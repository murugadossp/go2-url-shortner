from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..services.firebase_service import firebase_service
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user from Firebase ID token.
    Returns None if no token provided (for anonymous access).
    Raises HTTPException if token is invalid.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        decoded_token = await firebase_service.verify_id_token(token)
        
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return decoded_token
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Require authentication - raises HTTPException if no valid token provided.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user = await get_current_user(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    return user

async def require_admin(
    user: Dict[str, Any] = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Require admin privileges - raises HTTPException if user is not admin.
    Checks Firestore users collection for is_admin status.
    """
    from ..services.firebase_service import firebase_service
    
    uid = user.get('uid')
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    # Check Firestore users collection for admin status
    try:
        user_ref = firebase_service.db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        logger.info(f"Checking admin status for user {uid}")
        
        if not user_doc.exists:
            logger.warning(f"User document not found for {uid}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required - user not found"
            )
        
        user_data = user_doc.to_dict()
        is_admin = user_data.get('is_admin', False)
        
        logger.info(f"User {uid} admin status: {is_admin}")
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required - not admin"
            )
        
        logger.info(f"Admin access granted for user {uid}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking admin status for {uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify admin privileges"
        )

def get_user_id(user: Optional[Dict[str, Any]]) -> Optional[str]:
    """Extract user ID from decoded token"""
    return user.get('uid') if user else None

async def is_admin(user: Optional[Dict[str, Any]]) -> bool:
    """Check if user has admin privileges by checking Firestore"""
    if not user:
        return False
    
    from ..services.firebase_service import firebase_service
    
    uid = user.get('uid')
    if not uid:
        return False
    
    try:
        user_ref = firebase_service.db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return False
        
        user_data = user_doc.to_dict()
        return user_data.get('is_admin', False)
        
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False