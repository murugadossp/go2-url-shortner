"""
QR Code generation router.
Handles QR code generation and serving for short links.
"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
import io
import logging
from ..services.qr_service import qr_service
from ..services.firebase_service import firebase_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/qr", tags=["qr"])

@router.get("/{code}")
async def get_qr_code(
    code: str,
    size: str = Query("medium", description="QR code size: small, medium, or large")
):
    """
    Generate or retrieve cached QR code for a short link.
    
    Args:
        code: The short link code
        size: QR code size preset (small, medium, large)
        
    Returns:
        PNG image of the QR code
    """
    try:
        # Validate size parameter
        if not qr_service.validate_size(size):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid size '{size}'. Must be one of: small, medium, large"
            )
        
        # Check if the link exists
        link_doc = firebase_service.db.collection('links').document(code).get()
        if not link_doc.exists:
            logger.warning(f"QR code requested for non-existent link: {code}")
            raise HTTPException(
                status_code=404,
                detail=f"Short link '{code}' not found. Please ensure the link exists before requesting its QR code."
            )
        
        link_data = link_doc.to_dict()
        
        # Check if link is disabled
        if link_data.get('disabled', False):
            raise HTTPException(
                status_code=410,
                detail="This link has been disabled"
            )
        
        # Check if link is expired
        expires_at = link_data.get('expires_at')
        if expires_at and expires_at.timestamp() < firebase_service.get_current_timestamp().timestamp():
            raise HTTPException(
                status_code=410,
                detail="This link has expired"
            )
        
        # Construct the full short URL
        base_domain = link_data.get('base_domain', 'go2.tools')
        short_url = f"https://{base_domain}/{code}"
        
        # Generate or retrieve cached QR code
        qr_data = await qr_service.generate_and_cache_qr(code, short_url, size)
        
        # Return the QR code as PNG image
        return Response(
            content=qr_data,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
                "Content-Disposition": f"inline; filename=qr_{code}_{size}.png"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Failed to generate QR code for {code}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate QR code"
        )

@router.get("/{code}/info")
async def get_qr_info(code: str):
    """
    Get information about available QR code sizes and URLs.
    
    Args:
        code: The short link code
        
    Returns:
        QR code information and available sizes
    """
    try:
        # Check if the link exists
        link_doc = firebase_service.db.collection('links').document(code).get()
        if not link_doc.exists:
            raise HTTPException(
                status_code=404,
                detail=f"Short link '{code}' not found"
            )
        
        link_data = link_doc.to_dict()
        base_domain = link_data.get('base_domain', 'go2.tools')
        short_url = f"https://{base_domain}/{code}"
        
        # Generate URLs for different sizes
        base_qr_url = f"/api/qr/{code}"
        
        return {
            "code": code,
            "short_url": short_url,
            "qr_urls": {
                "small": f"{base_qr_url}?size=small",
                "medium": f"{base_qr_url}?size=medium", 
                "large": f"{base_qr_url}?size=large"
            },
            "sizes": {
                "small": {"description": "Compact QR code for small spaces", "dimensions": "~200x200px"},
                "medium": {"description": "Standard QR code for general use", "dimensions": "~250x250px"},
                "large": {"description": "Large QR code for print materials", "dimensions": "~300x300px"}
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get QR info for {code}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve QR code information"
        )