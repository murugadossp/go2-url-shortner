from fastapi import APIRouter, Response, Depends, HTTPException, status
from typing import List, Dict, Any
from ..models.api import SuccessResponse
from ..models.link import BaseDomain
from ..models.config import ConfigDocument, DomainConfigRequest
from ..services.firebase_service import firebase_service
from ..utils.auth import require_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("/base-domains")
async def get_base_domains(response: Response) -> SuccessResponse:
    """Get available base domains and their configurations"""
    
    # Set caching headers - this data rarely changes
    response.headers["Cache-Control"] = "public, max-age=300, s-maxage=300"  # 5 minutes
    response.headers["ETag"] = '"base-domains-v2"'
    
    try:
        # Try to get configuration from Firestore
        config_ref = firebase_service.db.collection('config').document('settings')
        config_doc = config_ref.get()
        
        if config_doc.exists:
            config_data = config_doc.to_dict()
            base_domains = config_data.get('base_domains', ["go2.video", "go2.reviews", "go2.tools"])
            domain_suggestions = config_data.get('domain_suggestions', {})
        else:
            # Fallback to default configuration
            base_domains = ["go2.video", "go2.reviews", "go2.tools"]
            domain_suggestions = {
                "youtube.com": "go2.video",
                "youtu.be": "go2.video",
                "vimeo.com": "go2.video",
                "twitch.tv": "go2.video",
                "amazon.com": "go2.reviews",
                "ebay.com": "go2.reviews",
                "etsy.com": "go2.reviews",
                "yelp.com": "go2.reviews",
                "tripadvisor.com": "go2.reviews",
                "github.com": "go2.tools",
                "stackoverflow.com": "go2.tools",
                "docs.google.com": "go2.tools",
                "notion.so": "go2.tools",
            }
        
        return SuccessResponse(
            data={
                "base_domains": base_domains,
                "domain_suggestions": domain_suggestions
            },
            message="Base domains retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting base domains: {e}")
        # Fallback to hardcoded defaults on error
        return SuccessResponse(
            data={
                "base_domains": ["go2.video", "go2.reviews", "go2.tools"],
                "domain_suggestions": {
                    "youtube.com": "go2.video",
                    "youtu.be": "go2.video",
                    "vimeo.com": "go2.video",
                    "twitch.tv": "go2.video",
                    "amazon.com": "go2.reviews",
                    "ebay.com": "go2.reviews",
                    "etsy.com": "go2.reviews",
                    "yelp.com": "go2.reviews",
                    "tripadvisor.com": "go2.reviews",
                    "github.com": "go2.tools",
                    "stackoverflow.com": "go2.tools",
                    "docs.google.com": "go2.tools",
                    "notion.so": "go2.tools",
                }
            },
            message="Base domains retrieved successfully (fallback)"
        )

@router.get("/health")
async def config_health() -> SuccessResponse:
    """Health check for config service"""
    return SuccessResponse(
        data={"status": "healthy"},
        message="Config service is operational"
    )


@router.get("/admin/domains")
async def get_admin_domain_config(
    current_user: Dict[str, Any] = Depends(require_admin)
) -> SuccessResponse:
    """Get domain configuration for admin interface"""
    try:
        # Get configuration from Firestore
        config_ref = firebase_service.db.collection('config').document('settings')
        config_doc = config_ref.get()
        
        if config_doc.exists:
            config_data = config_doc.to_dict()
            return SuccessResponse(
                data={
                    "base_domains": config_data.get('base_domains', ['go2.video', 'go2.reviews', 'go2.tools']),
                    "domain_suggestions": config_data.get('domain_suggestions', {}),
                    "last_updated": config_data.get('last_updated')
                },
                message="Domain configuration retrieved successfully"
            )
        else:
            # Return default configuration
            return SuccessResponse(
                data={
                    "base_domains": ['go2.video', 'go2.reviews', 'go2.tools'],
                    "domain_suggestions": {},
                    "last_updated": None
                },
                message="Default domain configuration returned"
            )
    except Exception as e:
        logger.error(f"Error getting admin domain config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve domain configuration"
        )


@router.put("/admin/domains")
async def update_domain_config(
    request: DomainConfigRequest,
    current_user: Dict[str, Any] = Depends(require_admin)
) -> SuccessResponse:
    """Update domain configuration (admin only)"""
    try:
        from datetime import datetime
        
        # Validate that all domains are valid BaseDomain values
        valid_domains = ['go2.video', 'go2.reviews', 'go2.tools']
        for domain in request.base_domains:
            if domain not in valid_domains:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid domain '{domain}'. Valid domains: {', '.join(valid_domains)}"
                )
        
        # Validate domain suggestions
        for pattern, suggested_domain in request.domain_suggestions.items():
            if suggested_domain not in valid_domains:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid suggested domain '{suggested_domain}' for pattern '{pattern}'"
                )
        
        # Update configuration in Firestore
        config_ref = firebase_service.db.collection('config').document('settings')
        config_data = {
            'base_domains': request.base_domains,
            'domain_suggestions': request.domain_suggestions,
            'last_updated': datetime.utcnow().isoformat(),
            'updated_by': current_user.get('uid')
        }
        
        # Merge with existing config to preserve other settings
        config_ref.set(config_data, merge=True)
        
        return SuccessResponse(
            data=config_data,
            message="Domain configuration updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating domain config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update domain configuration"
        )