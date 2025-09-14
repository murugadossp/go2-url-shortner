from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from ..models.user import UserProfileResponse, UpdateUserRequest, PlanUpgradeRequest
from ..services.user_service import user_service
from ..utils.auth import require_auth, require_admin, get_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """Get current user's profile with usage statistics"""
    uid = get_user_id(current_user)
    
    # Ensure user exists in database
    await user_service.get_or_create_user(current_user)
    
    profile = await user_service.get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return profile

@router.put("/profile")
async def update_user_profile(
    request: UpdateUserRequest,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """Update user profile"""
    uid = get_user_id(current_user)
    
    success = await user_service.update_user_profile(uid, request.display_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    return {"message": "Profile updated successfully"}

@router.get("/usage")
async def get_user_usage(
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """Get detailed user usage statistics"""
    uid = get_user_id(current_user)
    
    usage_stats = await user_service.get_user_usage_stats(uid)
    if not usage_stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return usage_stats

@router.post("/upgrade")
async def upgrade_plan(
    request: PlanUpgradeRequest,
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """Upgrade user plan (demo implementation - would integrate with payment system)"""
    uid = get_user_id(current_user)
    
    # In a real implementation, this would:
    # 1. Validate payment information
    # 2. Process payment through Stripe/PayPal
    # 3. Only upgrade on successful payment
    
    success = await user_service.upgrade_user_plan(uid, request.plan_type)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade plan"
        )
    
    return {
        "message": f"Plan upgraded to {request.plan_type}",
        "note": "This is a demo implementation. In production, payment processing would be required."
    }

@router.get("/limits")
async def get_plan_limits():
    """Get plan limits information"""
    return {
        "plans": {
            "free": {
                "custom_codes": 5,
                "features": ["Basic URL shortening", "QR codes", "Basic analytics"]
            },
            "paid": {
                "custom_codes": 100,
                "features": [
                    "All free features",
                    "100 custom codes per month",
                    "Advanced analytics",
                    "Priority support"
                ]
            }
        }
    }

@router.get("/admin/check")
async def check_admin_status(
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Simple endpoint to check if user has admin privileges"""
    return {
        "is_admin": True,
        "user_id": current_user.get('uid'),
        "message": "Admin access confirmed"
    }

@router.post("/ensure-user")
async def ensure_user_exists(
    current_user: Dict[str, Any] = Depends(require_auth)
):
    """Ensure user document exists in Firestore"""
    try:
        user_doc = await user_service.get_or_create_user(current_user)
        return {
            "message": "User document ensured",
            "user_id": current_user.get('uid'),
            "is_admin": user_doc.is_admin
        }
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ensure user document"
        )

# Admin routes
@router.get("/admin/all", response_model=List[UserProfileResponse])
async def list_all_users(
    current_user: Dict[str, Any] = Depends(require_admin),
    limit: int = 100,
    offset: int = 0
):
    """List all users (admin only)"""
    try:
        users = await user_service.list_all_users(limit=limit, offset=offset)
        return users
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/admin/{uid}", response_model=UserProfileResponse)
async def get_user_by_id(
    uid: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Get user by ID (admin only)"""
    profile = await user_service.get_user_profile(uid)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return profile

@router.put("/admin/{uid}/plan")
async def admin_update_user_plan(
    uid: str,
    request: PlanUpgradeRequest,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Update user plan (admin only)"""
    success = await user_service.upgrade_user_plan(uid, request.plan_type)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user plan"
        )
    
    
    return {"message": f"User plan updated to {request.plan_type}"}

@router.put("/admin/{uid}/admin-status")
async def toggle_admin_status(
    uid: str,
    is_admin: bool,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Toggle user admin status (admin only)"""
    success = await user_service.set_admin_status(uid, is_admin)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin status"
        )
    
    
    return {"message": f"Admin status {'granted' if is_admin else 'revoked'}"}

@router.get("/admin/stats/overview")
async def get_admin_stats(
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Get system overview statistics (admin only)"""
    try:
        stats = await user_service.get_system_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )
