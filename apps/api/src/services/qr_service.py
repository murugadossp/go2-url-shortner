"""
QR Code generation and caching service.
Handles QR code generation with Firebase Storage caching.
"""

import qrcode
from PIL import Image, ImageDraw
import io
import logging
from typing import Optional, Tuple
from firebase_admin import storage
from .firebase_service import firebase_service

logger = logging.getLogger(__name__)

class QRService:
    """Service for generating and caching QR codes."""
    
    def __init__(self):
        self.bucket = None
        try:
            # Initialize Firebase Storage bucket
            self.bucket = storage.bucket()
            logger.info("Firebase Storage initialized for QR caching")
        except Exception as e:
            logger.warning(f"Firebase Storage not available for QR caching: {e}")
    
    def generate_qr_code(self, url: str, size: str = "medium") -> bytes:
        """
        Generate QR code for the given URL.
        
        Args:
            url: The URL to encode in the QR code
            size: Size preset - "small", "medium", "large"
            
        Returns:
            PNG image data as bytes
        """
        try:
            # Size configurations
            size_configs = {
                "small": {"box_size": 8, "border": 2},
                "medium": {"box_size": 10, "border": 4}, 
                "large": {"box_size": 12, "border": 6}
            }
            
            config = size_configs.get(size, size_configs["medium"])
            
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,  # Controls the size of the QR Code
                error_correction=qrcode.constants.ERROR_CORRECT_M,  # ~15% error correction
                box_size=config["box_size"],
                border=config["border"],
            )
            
            # Add data and optimize
            qr.add_data(url)
            qr.make(fit=True)
            
            # Create image with white background and black foreground
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to PNG bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG', optimize=True)
            img_buffer.seek(0)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate QR code for URL {url}: {e}")
            raise Exception(f"QR code generation failed: {str(e)}")
    
    def get_cache_path(self, code: str, size: str = "medium") -> str:
        """Get the Firebase Storage path for a QR code."""
        return f"qr-codes/{code}_{size}.png"
    
    async def get_cached_qr(self, code: str, size: str = "medium") -> Optional[bytes]:
        """
        Retrieve cached QR code from Firebase Storage.
        
        Args:
            code: The short link code
            size: Size preset
            
        Returns:
            PNG image data as bytes if cached, None otherwise
        """
        if not self.bucket:
            return None
            
        try:
            cache_path = self.get_cache_path(code, size)
            blob = self.bucket.blob(cache_path)
            
            if blob.exists():
                logger.info(f"QR code cache hit for {code} (size: {size})")
                return blob.download_as_bytes()
            else:
                logger.debug(f"QR code cache miss for {code} (size: {size})")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached QR code for {code}: {e}")
            return None
    
    async def cache_qr(self, code: str, qr_data: bytes, size: str = "medium") -> bool:
        """
        Cache QR code in Firebase Storage.
        
        Args:
            code: The short link code
            qr_data: PNG image data as bytes
            size: Size preset
            
        Returns:
            True if successfully cached, False otherwise
        """
        if not self.bucket:
            return False
            
        try:
            cache_path = self.get_cache_path(code, size)
            blob = self.bucket.blob(cache_path)
            
            # Upload with appropriate content type and caching headers
            blob.upload_from_string(
                qr_data,
                content_type='image/png'
            )
            
            # Set cache control headers (cache for 1 year since QR codes don't change)
            blob.cache_control = 'public, max-age=31536000'
            blob.patch()
            
            logger.info(f"QR code cached for {code} (size: {size})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache QR code for {code}: {e}")
            return False
    
    async def generate_and_cache_qr(self, code: str, url: str, size: str = "medium") -> bytes:
        """
        Generate QR code and cache it. Cache-first strategy with fallback generation.
        
        Args:
            code: The short link code
            url: The full URL to encode
            size: Size preset
            
        Returns:
            PNG image data as bytes
        """
        # Try to get from cache first
        cached_qr = await self.get_cached_qr(code, size)
        if cached_qr:
            return cached_qr
        
        # Generate new QR code
        qr_data = self.generate_qr_code(url, size)
        
        # Cache the generated QR code (fire and forget)
        try:
            await self.cache_qr(code, qr_data, size)
        except Exception as e:
            logger.warning(f"Failed to cache QR code for {code}: {e}")
            # Continue anyway, we still have the generated QR code
        
        return qr_data
    
    def validate_size(self, size: str) -> bool:
        """Validate if the size parameter is supported."""
        return size in ["small", "medium", "large"]

# Global QR service instance
qr_service = QRService()