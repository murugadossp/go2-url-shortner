"""
Links router for URL shortening and management.
Handles link creation, retrieval, updates, and deletion with safety validation.
"""

import os
import secrets
import string
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import RedirectResponse
from passlib.hash import bcrypt

from ..models.link import (
    CreateLinkRequest, CreateLinkResponse, UpdateLinkRequest, 
    LinkDocument, LinkMetadata, LinkListResponse, LinkStatsRequest
)
from ..models.api import ErrorResponse, ErrorDetail
from ..models.user import UserDocument, PlanType
from ..models.analytics import LinkStats, AnalyticsExportRequest
from ..services.firebase_service import firebase_service
from ..services.safety_service import SafetyService, SafetyError
from ..services.analytics_service import analytics_service
from ..services.user_service import user_service
from ..utils.auth import get_current_user, require_auth, require_admin, get_user_id
from ..utils.domain_utils import get_base_domain_from_request, get_composite_document_id, get_short_url, is_valid_base_domain
from google.cloud import firestore
from google.cloud.firestore import FieldFilter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/links", tags=["links"])

# Initialize safety service
safety_service = SafetyService(
    safe_browsing_api_key=os.getenv('GOOGLE_SAFE_BROWSING_API_KEY'),
    blacklist_file_path="config/domain_blacklist.json"
)

# Plan limits
PLAN_LIMITS = {
    'free': {'custom_codes': 5},
    'paid': {'custom_codes': 100}
}

async def get_valid_base_domains() -> List[str]:
    """Get valid base domains from Firestore configuration"""
    try:
        config_ref = firebase_service.db.collection('config').document('settings')
        config_doc = config_ref.get()
        
        if config_doc.exists:
            config_data = config_doc.to_dict()
            return config_data.get('base_domains', ['go2.video', 'go2.reviews', 'go2.tools'])
        else:
            return ['go2.video', 'go2.reviews', 'go2.tools']
    except Exception as e:
        logger.error(f"Error getting valid base domains: {e}")
        return ['go2.video', 'go2.reviews', 'go2.tools']

async def validate_base_domain(domain: str) -> bool:
    """Validate that the base domain is allowed"""
    valid_domains = await get_valid_base_domains()
    return domain in valid_domains

def generate_short_code(length: int = 6) -> str:
    """Generate a random short code"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.verify(password, hashed)

def hash_ip(ip: str) -> str:
    """Hash IP address for privacy"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]

async def get_user_document(uid: str) -> Optional[UserDocument]:
    """Get user document from Firestore"""
    try:
        user_ref = firebase_service.db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            return UserDocument(**user_doc.to_dict())
        return None
    except Exception as e:
        logger.error(f"Error getting user document: {e}")
        return None

async def create_user_document(uid: str, email: str, display_name: str) -> UserDocument:
    """Create a new user document in Firestore"""
    now = datetime.utcnow()
    user_data = UserDocument(
        email=email,
        display_name=display_name,
        plan_type='free',
        custom_codes_used=0,
        custom_codes_reset_date=now + timedelta(days=30),
        created_at=now,
        last_login=now,
        is_admin=False
    )
    
    try:
        user_ref = firebase_service.db.collection('users').document(uid)
        user_ref.set(user_data.model_dump())
        return user_data
    except Exception as e:
        logger.error(f"Error creating user document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user profile"
        )

async def check_custom_code_limit(user: Optional[Dict[str, Any]], is_custom_code: bool) -> None:
    """Check if user has exceeded custom code limits"""
    if not is_custom_code or not user:
        return
    
    uid = get_user_id(user)
    
    # Ensure user exists in database
    await user_service.get_or_create_user(user)
    
    # Check if user can create custom code
    can_create = await user_service.can_create_custom_code(uid)
    if not can_create:
        user_profile = await user_service.get_user_profile(uid)
        plan_limit = user_service.plan_limits[user_profile.plan_type]['custom_codes']
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Custom code limit exceeded. {user_profile.plan_type.title()} plan allows {plan_limit} custom codes per month."
        )

async def increment_custom_code_usage(uid: str) -> None:
    """Increment user's custom code usage count"""
    await user_service.increment_custom_code_usage(uid)

async def check_code_collision(code: str, base_domain: str) -> bool:
    """Check if a short code already exists for the given domain"""
    try:
        document_id = get_composite_document_id(base_domain, code)
        link_ref = firebase_service.db.collection('links').document(document_id)
        return link_ref.get().exists
    except Exception as e:
        logger.error(f"Error checking code collision for {base_domain}_{code}: {e}")
        return True  # Fail safe - assume collision


async def find_link_across_domains(code: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Find a link by code across all domains.
    Returns (link_data, domain) tuple or (None, None) if not found.
    """
    domains = ['go2.video', 'go2.tools', 'go2.reviews']
    
    for domain in domains:
        try:
            document_id = get_composite_document_id(domain, code)
            link_ref = firebase_service.db.collection('links').document(document_id)
            link_doc = link_ref.get()
            
            if link_doc.exists:
                link_data = link_doc.to_dict()
                link_data['_document_id'] = document_id  # Include document ID for updates
                return link_data, domain
        except Exception as e:
            logger.error(f"Error searching for {code} in domain {domain}: {e}")
            continue
    
    return None, None


async def get_link_document_ref(code: str) -> tuple[Optional[Any], Optional[str], Optional[str]]:
    """
    Get Firestore document reference for a link by code.
    Returns (document_ref, domain, document_id) tuple or (None, None, None) if not found.
    """
    domains = ['go2.video', 'go2.tools', 'go2.reviews']
    
    for domain in domains:
        try:
            document_id = get_composite_document_id(domain, code)
            link_ref = firebase_service.db.collection('links').document(document_id)
            
            if link_ref.get().exists:
                return link_ref, domain, document_id
        except Exception as e:
            logger.error(f"Error getting document ref for {code} in domain {domain}: {e}")
            continue
    
    return None, None, None

def suggest_alternative_codes(base_code: str, count: int = 3) -> List[str]:
    """Suggest alternative codes when collision occurs"""
    suggestions = []
    
    # Try adding numbers
    for i in range(1, count + 1):
        suggestions.append(f"{base_code}{i}")
    
    # Try adding random suffix
    for _ in range(count):
        suffix = ''.join(secrets.choice(string.digits) for _ in range(2))
        suggestions.append(f"{base_code}{suffix}")
    
    return suggestions[:count]

def extract_metadata(url: str) -> LinkMetadata:
    """Extract metadata from URL"""
    try:
        parsed = urlparse(url)
        return LinkMetadata(
            host=parsed.netloc,
            title=None,  # Could be enhanced with web scraping
            favicon_url=None  # Could be enhanced with favicon detection
        )
    except Exception:
        return LinkMetadata()

@router.post("/shorten", response_model=CreateLinkResponse)
async def create_short_link(
    request: CreateLinkRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    http_request: Request = None
):
    """
    Create a new short link with comprehensive safety validation.
    
    - Validates URL safety using multiple checks
    - Handles custom code collisions with suggestions
    - Enforces plan-based custom code limits
    - Supports password protection and expiration
    """
    try:
        # 1. Validate base domain
        if not await validate_base_domain(request.base_domain):
            valid_domains = await get_valid_base_domains()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid base domain '{request.base_domain}'. Allowed domains: {', '.join(valid_domains)}"
            )
        
        # 2. Safety validation
        try:
            safety_service.validate_url(str(request.long_url))
        except SafetyError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"URL blocked by safety validation: {e.message}"
            )
        
        # 3. Determine if custom code is being used
        is_custom_code = request.custom_code is not None
        
        # 4. Check custom code limits for authenticated users
        await check_custom_code_limit(current_user, is_custom_code)
        
        # 5. Generate or validate short code
        if is_custom_code:
            code = request.custom_code
            if await check_code_collision(code, request.base_domain):
                suggestions = suggest_alternative_codes(code)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": f"Custom code '{code}' is already taken for domain '{request.base_domain}'",
                        "suggestions": suggestions
                    }
                )
        else:
            # Generate unique random code
            max_attempts = 10
            for _ in range(max_attempts):
                code = generate_short_code()
                if not await check_code_collision(code, request.base_domain):
                    break
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate unique short code"
                )
        
        # 6. Hash password if provided
        password_hash = None
        if request.password:
            password_hash = hash_password(request.password)
        
        # 7. Get client IP for tracking
        client_ip = None
        if http_request:
            client_ip = http_request.client.host
            if client_ip:
                client_ip = hash_ip(client_ip)
        
        # 8. Extract metadata
        metadata = extract_metadata(str(request.long_url))
        
        # 9. Determine plan type
        plan_type = 'free'
        if current_user:
            user_doc = await get_user_document(get_user_id(current_user))
            if user_doc:
                plan_type = user_doc.plan_type
        
        # 10. Create link document
        now = datetime.utcnow()
        link_doc = LinkDocument(
            long_url=request.long_url,
            base_domain=request.base_domain,
            owner_uid=get_user_id(current_user),
            password_hash=password_hash,
            expires_at=request.expires_at,
            disabled=False,
            created_at=now,
            created_by_ip=client_ip,
            metadata=metadata,
            plan_type=plan_type,
            is_custom_code=is_custom_code
        )
        
        # 11. Save to Firestore using composite document ID
        link_data = link_doc.model_dump()
        link_data['long_url'] = str(link_data['long_url'])  # Convert HttpUrl to string
        
        # Use composite document ID: {domain}_{code}
        document_id = get_composite_document_id(request.base_domain, code)
        link_ref = firebase_service.db.collection('links').document(document_id)
        link_ref.set(link_data)
        
        # 12. Increment custom code usage if applicable
        if is_custom_code and current_user:
            await increment_custom_code_usage(get_user_id(current_user))
        
        # 13. Build response
        short_url = get_short_url(request.base_domain, code)
        
        # Construct full QR URL using the composite document ID
        if http_request:
            api_base_url = f"{http_request.url.scheme}://{http_request.url.netloc}"
            qr_url = f"{api_base_url}/api/qr/{document_id}"
        else:
            # Fallback to relative URL
            qr_url = f"/api/qr/{document_id}"
        
        return CreateLinkResponse(
            short_url=short_url,
            code=code,
            qr_url=qr_url,
            long_url=str(request.long_url),
            base_domain=request.base_domain,
            expires_at=request.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating short link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create short link"
        )



@router.put("/{code}")
async def update_link(
    code: str,
    request: UpdateLinkRequest,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Update an existing link (owner or admin only).
    Supports updating disabled status, expiration, and password.
    """
    try:
        # Find link across all domains
        link_data, domain = await find_link_across_domains(code)
        
        if not link_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        # Get document reference for updates
        document_id = link_data['_document_id']
        link_ref = firebase_service.db.collection('links').document(document_id)
        
        # Check permissions (owner or admin)
        is_owner = link_data.get('owner_uid') == get_user_id(current_user)
        is_admin = current_user.get('admin', False)
        
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        # Build update data
        update_data = {}
        
        if request.disabled is not None:
            update_data['disabled'] = request.disabled
        
        if request.expires_at is not None:
            update_data['expires_at'] = request.expires_at
        
        if request.password is not None:
            update_data['password_hash'] = hash_password(request.password)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # Update document
        link_ref.update(update_data)
        
        return {"message": "Link updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating link {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update link"
        )

@router.delete("/{code}")
async def delete_link(
    code: str,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Delete a link (owner or admin only).
    """
    try:
        # Find link across all domains
        link_data, domain = await find_link_across_domains(code)
        
        if not link_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        # Get document reference for deletion
        document_id = link_data['_document_id']
        link_ref = firebase_service.db.collection('links').document(document_id)
        
        # Check permissions (owner or admin)
        is_owner = link_data.get('owner_uid') == get_user_id(current_user)
        is_admin = current_user.get('admin', False)
        
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        # Delete document and subcollections
        link_ref.delete()
        
        # TODO: Delete clicks subcollection (will be handled in analytics task)
        
        return {"message": "Link deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting link {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete link"
        )

@router.get("/", response_model=List[LinkListResponse])
async def list_user_links(
    current_user: Dict[str, Any] = Depends(require_auth),
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    sort_by: str = 'created_at',
    order: str = 'desc',
    filter_status: Optional[str] = None,
    filter_type: Optional[str] = None
):
    """
    List links for the authenticated user with search, sort, and filter capabilities.
    
    Parameters:
    - search: Search text to match against code, long_url, or base_domain
    - sort_by: Field to sort by ('created_at', 'clicks', 'expires_at', 'code')
    - order: Sort order ('asc' or 'desc')
    - filter_status: Filter by status ('active', 'expired', 'disabled')
    - filter_type: Filter by type ('custom', 'generated')
    """
    try:
        uid = get_user_id(current_user)
        
        # Start with base query
        links_ref = firebase_service.db.collection('links')
        query = links_ref.where(filter=FieldFilter('owner_uid', '==', uid))
        
        # Apply status filter
        if filter_status == 'disabled':
            query = query.where(filter=FieldFilter('disabled', '==', True))
        elif filter_status == 'active':
            query = query.where(filter=FieldFilter('disabled', '==', False))
        
        # Apply type filter
        if filter_type == 'custom':
            query = query.where(filter=FieldFilter('is_custom_code', '==', True))
        elif filter_type == 'generated':
            query = query.where(filter=FieldFilter('is_custom_code', '==', False))
        
        # For sorting that requires database queries, apply appropriate order_by
        # For in-memory sorting (clicks, code), we'll fetch with default order and sort after
        if sort_by in ['created_at']:
            sort_direction = firestore.Query.DESCENDING if order == 'desc' else firestore.Query.ASCENDING
            query = query.order_by('created_at', direction=sort_direction)
        elif sort_by == 'expires_at':
            # For expires_at sorting, we need to handle this in-memory since not all links have expiry
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
        else:
            # For clicks and code sorting, fetch with default created_at order and sort in-memory
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Fetch documents
        docs = list(query.stream())
        
        # Convert to LinkListResponse objects and get analytics
        links = []
        for doc in docs:
            link_data = doc.to_dict()
            
            # Get click count from analytics service
            try:
                stats = await analytics_service.get_stats(doc.id, 'all')
                total_clicks = stats.total_clicks
            except Exception as e:
                logger.warning(f"Failed to get click count for {doc.id}: {e}")
                total_clicks = 0
            
            link = LinkListResponse(
                code=doc.id,
                long_url=link_data['long_url'],
                base_domain=link_data['base_domain'],
                created_at=link_data['created_at'],
                disabled=link_data.get('disabled', False),
                expires_at=link_data.get('expires_at'),
                total_clicks=total_clicks,
                owner_uid=link_data.get('owner_uid'),
                is_custom_code=link_data.get('is_custom_code', False)
            )
            
            links.append(link)
        
        # Apply search filter in-memory (since Firestore doesn't support full-text search well)
        if search:
            search_lower = search.lower()
            links = [
                link for link in links 
                if (search_lower in link.code.lower() or 
                    search_lower in link.long_url.lower() or 
                    search_lower in link.base_domain.lower())
            ]
        
        # Apply in-memory sorting for fields that can't be handled by Firestore
        if sort_by == 'clicks':
            reverse_sort = order == 'desc'
            links.sort(key=lambda x: x.total_clicks, reverse=reverse_sort)
        elif sort_by == 'code':
            reverse_sort = order == 'desc'
            links.sort(key=lambda x: x.code.lower(), reverse=reverse_sort)
        elif sort_by == 'expires_at':
            # Sort by expiration date, handling None values (put them at the end)
            reverse_sort = order == 'desc'
            def expires_sort_key(link):
                if not link.expires_at:
                    # Put links without expiry at the end
                    return datetime.max if not reverse_sort else datetime.min
                try:
                    return datetime.fromisoformat(link.expires_at.replace('Z', '+00:00'))
                except:
                    return datetime.max if not reverse_sort else datetime.min
            links.sort(key=expires_sort_key, reverse=reverse_sort)
        
        # Apply expired filter in-memory (since it requires date comparison)
        if filter_status == 'expired':
            now = datetime.utcnow()
            links = [
                link for link in links 
                if link.expires_at and datetime.fromisoformat(link.expires_at.replace('Z', '+00:00')) < now
            ]
        
        return links
        
    except Exception as e:
        logger.error(f"Error listing user links: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve links"
        )

@router.get("/admin/all", response_model=List[LinkListResponse])
async def list_all_links(
    current_user: Dict[str, Any] = Depends(require_admin),
    limit: int = 100,
    offset: int = 0
):
    """
    List all links (admin only).
    """
    try:
        # Query all links
        links_ref = firebase_service.db.collection('links')
        query = links_ref.order_by('created_at', direction=firestore.Query.DESCENDING)
        query = query.limit(limit).offset(offset)
        
        links = []
        for doc in query.stream():
            link_data = doc.to_dict()
            
            # Get click count from analytics service
            try:
                stats = await analytics_service.get_stats(doc.id, 'all')
                total_clicks = stats.total_clicks
            except Exception as e:
                logger.warning(f"Failed to get click count for {doc.id}: {e}")
                total_clicks = 0
            
            links.append(LinkListResponse(
                code=doc.id,
                long_url=link_data['long_url'],
                base_domain=link_data['base_domain'],
                created_at=link_data['created_at'],
                disabled=link_data.get('disabled', False),
                expires_at=link_data.get('expires_at'),
                total_clicks=total_clicks,
                owner_uid=link_data.get('owner_uid'),
                is_custom_code=link_data.get('is_custom_code', False)
            ))
        
        return links
        
    except Exception as e:
        logger.error(f"Error listing all links: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve links"
        )

@router.post("/admin/bulk-disable")
async def bulk_disable_links(
    codes: List[str],
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Bulk disable links (admin only).
    """
    try:
        disabled_count = 0
        errors = []
        
        for code in codes:
            try:
                link_ref = firebase_service.db.collection('links').document(code)
                link_doc = link_ref.get()
                
                if link_doc.exists:
                    link_ref.update({'disabled': True})
                    disabled_count += 1
                else:
                    errors.append(f"Link {code} not found")
            except Exception as e:
                errors.append(f"Failed to disable {code}: {str(e)}")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_uid=get_user_id(current_user),
            action="bulk_disable_links",
            details={"codes": codes, "disabled_count": disabled_count, "errors": errors}
        )
        
        return {
            "message": f"Disabled {disabled_count} links",
            "disabled_count": disabled_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk disable: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable links"
        )

@router.post("/admin/bulk-delete")
async def bulk_delete_links(
    codes: List[str],
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Bulk delete links (admin only).
    """
    try:
        deleted_count = 0
        errors = []
        
        for code in codes:
            try:
                link_ref = firebase_service.db.collection('links').document(code)
                link_doc = link_ref.get()
                
                if link_doc.exists:
                    # Delete clicks subcollection first
                    clicks_collection = link_ref.collection('clicks')
                    clicks = clicks_collection.get()
                    for click in clicks:
                        click.reference.delete()
                    
                    # Delete the link document
                    link_ref.delete()
                    deleted_count += 1
                else:
                    errors.append(f"Link {code} not found")
            except Exception as e:
                errors.append(f"Failed to delete {code}: {str(e)}")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_uid=get_user_id(current_user),
            action="bulk_delete_links",
            details={"codes": codes, "deleted_count": deleted_count, "errors": errors}
        )
        
        return {
            "message": f"Deleted {deleted_count} links",
            "deleted_count": deleted_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete links"
        )

@router.post("/admin/bulk-update-expiry")
async def bulk_update_expiry(
    codes: List[str],
    expires_at: Optional[datetime] = None,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Bulk update link expiration (admin only).
    """
    try:
        updated_count = 0
        errors = []
        
        for code in codes:
            try:
                link_ref = firebase_service.db.collection('links').document(code)
                link_doc = link_ref.get()
                
                if link_doc.exists:
                    link_ref.update({'expires_at': expires_at})
                    updated_count += 1
                else:
                    errors.append(f"Link {code} not found")
            except Exception as e:
                errors.append(f"Failed to update {code}: {str(e)}")
        
        # Log admin action
        await user_service.log_admin_action(
            admin_uid=get_user_id(current_user),
            action="bulk_update_expiry",
            details={"codes": codes, "expires_at": expires_at.isoformat() if expires_at else None, "updated_count": updated_count, "errors": errors}
        )
        
        return {
            "message": f"Updated expiry for {updated_count} links",
            "updated_count": updated_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in bulk update expiry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update link expiry"
        )


@router.get("/stats/{code}", response_model=LinkStats)
async def get_link_stats(
    code: str,
    period: str = '7d',
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Get analytics statistics for a link.
    Public links can be viewed by anyone, private links require owner or admin access.
    """
    try:
        # Find link across all domains
        link_data, domain = await find_link_across_domains(code)
        
        if not link_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        # Use the composite document ID for analytics
        document_id = link_data['_document_id']
        
        # Check permissions for private links
        owner_uid = link_data.get('owner_uid')
        if owner_uid:  # Private link
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to view private link statistics"
                )
            
            is_owner = get_user_id(current_user) == owner_uid
            is_admin = current_user.get('admin', False)
            
            if not (is_owner or is_admin):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
        
        # Validate period parameter
        if period not in ['7d', '30d', 'all']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Period must be one of: 7d, 30d, all"
            )
        
        # Get statistics using composite document ID
        stats = await analytics_service.get_stats(document_id, period)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/check-availability/{code}")
async def check_code_availability(code: str):
    """
    Check if a custom code is available for use.
    Returns availability status and suggestions if taken.
    """
    try:
        # Check if code exists across all domains
        domains = ['go2.video', 'go2.tools', 'go2.reviews']
        taken_domains = []
        
        for domain in domains:
            if await check_code_collision(code, domain):
                taken_domains.append(domain)
        
        if taken_domains:
            # Generate suggestions
            suggestions = suggest_alternative_codes(code, 3)
            return {
                "available": False,
                "suggestions": suggestions,
                "message": f"Code '{code}' is already taken in domains: {', '.join(taken_domains)}",
                "taken_domains": taken_domains
            }
        else:
            return {
                "available": True,
                "suggestions": [],
                "message": f"Code '{code}' is available in all domains"
            }
            
    except Exception as e:
        logger.error(f"Error checking code availability for {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check code availability"
        )

@router.get("/export/{code}")
async def export_link_data(
    code: str,
    format: str = 'json',
    period: str = '30d',
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Export analytics data for a link in JSON or CSV format.
    Requires owner or admin access.
    """
    try:
        # Get link document to check permissions
        link_ref = firebase_service.db.collection('links').document(code)
        link_doc = link_ref.get()
        
        if not link_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        link_data = link_doc.to_dict()
        
        # Check permissions (owner or admin only for exports)
        owner_uid = link_data.get('owner_uid')
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        is_owner = get_user_id(current_user) == owner_uid
        is_admin = current_user.get('admin', False)
        
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        # Validate parameters
        if format not in ['json', 'csv']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format must be 'json' or 'csv'"
            )
        
        if period not in ['7d', '30d', 'all']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Period must be one of: 7d, 30d, all"
            )
        
        # Export data
        data = await analytics_service.export_data(code, format, period)
        
        # Set appropriate content type and filename
        content_type = 'application/json' if format == 'json' else 'text/csv'
        filename = f"{code}_analytics_{period}.{format}"
        
        from fastapi.responses import Response
        return Response(
            content=data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting data for {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data"
        )
