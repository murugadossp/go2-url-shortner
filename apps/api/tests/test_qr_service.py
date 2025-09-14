"""
Tests for QR code generation and caching service.
"""

import pytest
import io
from PIL import Image
from unittest.mock import Mock, patch, AsyncMock
from src.services.qr_service import QRService, qr_service

class TestQRService:
    """Test cases for QR code service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.qr_service = QRService()
        self.test_url = "https://go2.tools/abc123"
        self.test_code = "abc123"
    
    def test_generate_qr_code_success(self):
        """Test successful QR code generation."""
        # Generate QR code
        qr_data = self.qr_service.generate_qr_code(self.test_url)
        
        # Verify it's valid PNG data
        assert isinstance(qr_data, bytes)
        assert len(qr_data) > 0
        
        # Verify it's a valid PNG image
        img = Image.open(io.BytesIO(qr_data))
        assert img.format == 'PNG'
        assert img.size[0] > 0 and img.size[1] > 0
    
    def test_generate_qr_code_different_sizes(self):
        """Test QR code generation with different sizes."""
        sizes = ["small", "medium", "large"]
        
        for size in sizes:
            qr_data = self.qr_service.generate_qr_code(self.test_url, size)
            
            # Verify valid PNG
            assert isinstance(qr_data, bytes)
            img = Image.open(io.BytesIO(qr_data))
            assert img.format == 'PNG'
    
    def test_generate_qr_code_invalid_size(self):
        """Test QR code generation with invalid size defaults to medium."""
        qr_data = self.qr_service.generate_qr_code(self.test_url, "invalid")
        
        # Should still generate (defaults to medium)
        assert isinstance(qr_data, bytes)
        img = Image.open(io.BytesIO(qr_data))
        assert img.format == 'PNG'
    
    def test_generate_qr_code_empty_url(self):
        """Test QR code generation with empty URL."""
        # QR code library can handle empty strings, so this should work
        qr_data = self.qr_service.generate_qr_code("")
        assert isinstance(qr_data, bytes)
        assert len(qr_data) > 0
    
    def test_validate_size(self):
        """Test size validation."""
        assert self.qr_service.validate_size("small") is True
        assert self.qr_service.validate_size("medium") is True
        assert self.qr_service.validate_size("large") is True
        assert self.qr_service.validate_size("invalid") is False
        assert self.qr_service.validate_size("") is False
    
    def test_get_cache_path(self):
        """Test cache path generation."""
        path = self.qr_service.get_cache_path("abc123", "medium")
        assert path == "qr-codes/abc123_medium.png"
        
        path = self.qr_service.get_cache_path("xyz789", "large")
        assert path == "qr-codes/xyz789_large.png"
    
    @pytest.mark.asyncio
    async def test_get_cached_qr_no_bucket(self):
        """Test cached QR retrieval when no bucket is available."""
        service = QRService()
        service.bucket = None
        
        result = await service.get_cached_qr("abc123")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_qr_no_bucket(self):
        """Test QR caching when no bucket is available."""
        service = QRService()
        service.bucket = None
        
        result = await service.cache_qr("abc123", b"fake_data")
        assert result is False
    
    @pytest.mark.asyncio
    @patch('firebase_admin.storage.bucket')
    async def test_get_cached_qr_exists(self, mock_bucket_class):
        """Test cached QR retrieval when QR exists."""
        # Mock bucket and blob
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b"cached_qr_data"
        
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket_class.return_value = mock_bucket
        
        service = QRService()
        service.bucket = mock_bucket
        
        result = await service.get_cached_qr("abc123", "medium")
        
        assert result == b"cached_qr_data"
        mock_bucket.blob.assert_called_with("qr-codes/abc123_medium.png")
        mock_blob.exists.assert_called_once()
        mock_blob.download_as_bytes.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('firebase_admin.storage.bucket')
    async def test_get_cached_qr_not_exists(self, mock_bucket_class):
        """Test cached QR retrieval when QR doesn't exist."""
        # Mock bucket and blob
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket_class.return_value = mock_bucket
        
        service = QRService()
        service.bucket = mock_bucket
        
        result = await service.get_cached_qr("abc123", "medium")
        
        assert result is None
        mock_blob.exists.assert_called_once()
        mock_blob.download_as_bytes.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('firebase_admin.storage.bucket')
    async def test_cache_qr_success(self, mock_bucket_class):
        """Test successful QR caching."""
        # Mock bucket and blob
        mock_blob = Mock()
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket_class.return_value = mock_bucket
        
        service = QRService()
        service.bucket = mock_bucket
        
        result = await service.cache_qr("abc123", b"qr_data", "medium")
        
        assert result is True
        mock_bucket.blob.assert_called_with("qr-codes/abc123_medium.png")
        mock_blob.upload_from_string.assert_called_with(
            b"qr_data",
            content_type='image/png'
        )
        mock_blob.patch.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('firebase_admin.storage.bucket')
    async def test_cache_qr_failure(self, mock_bucket_class):
        """Test QR caching failure."""
        # Mock bucket and blob that raises exception
        mock_blob = Mock()
        mock_blob.upload_from_string.side_effect = Exception("Upload failed")
        
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket_class.return_value = mock_bucket
        
        service = QRService()
        service.bucket = mock_bucket
        
        result = await service.cache_qr("abc123", b"qr_data", "medium")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_generate_and_cache_qr_cache_hit(self):
        """Test generate_and_cache_qr with cache hit."""
        service = QRService()
        
        # Mock get_cached_qr to return cached data
        service.get_cached_qr = AsyncMock(return_value=b"cached_qr_data")
        
        result = await service.generate_and_cache_qr("abc123", self.test_url, "medium")
        
        assert result == b"cached_qr_data"
        service.get_cached_qr.assert_called_once_with("abc123", "medium")
    
    @pytest.mark.asyncio
    async def test_generate_and_cache_qr_cache_miss(self):
        """Test generate_and_cache_qr with cache miss."""
        service = QRService()
        
        # Mock methods
        service.get_cached_qr = AsyncMock(return_value=None)
        service.cache_qr = AsyncMock(return_value=True)
        
        # Mock generate_qr_code
        with patch.object(service, 'generate_qr_code') as mock_generate:
            mock_generate.return_value = b"new_qr_data"
            
            result = await service.generate_and_cache_qr("abc123", self.test_url, "medium")
            
            assert result == b"new_qr_data"
            service.get_cached_qr.assert_called_once_with("abc123", "medium")
            mock_generate.assert_called_once_with(self.test_url, "medium")
            service.cache_qr.assert_called_once_with("abc123", b"new_qr_data", "medium")
    
    @pytest.mark.asyncio
    async def test_generate_and_cache_qr_cache_failure(self):
        """Test generate_and_cache_qr when caching fails."""
        service = QRService()
        
        # Mock methods
        service.get_cached_qr = AsyncMock(return_value=None)
        service.cache_qr = AsyncMock(side_effect=Exception("Cache failed"))
        
        # Mock generate_qr_code
        with patch.object(service, 'generate_qr_code') as mock_generate:
            mock_generate.return_value = b"new_qr_data"
            
            # Should still return the generated QR even if caching fails
            result = await service.generate_and_cache_qr("abc123", self.test_url, "medium")
            
            assert result == b"new_qr_data"

class TestQRServiceIntegration:
    """Integration tests for QR service."""
    
    def test_qr_service_singleton(self):
        """Test that qr_service is properly initialized."""
        assert qr_service is not None
        assert isinstance(qr_service, QRService)
    
    def test_end_to_end_qr_generation(self):
        """Test end-to-end QR generation without caching."""
        url = "https://go2.tools/test123"
        
        # Generate QR code
        qr_data = qr_service.generate_qr_code(url)
        
        # Verify it's a valid PNG
        assert isinstance(qr_data, bytes)
        img = Image.open(io.BytesIO(qr_data))
        assert img.format == 'PNG'
        
        # Verify reasonable size
        assert len(qr_data) > 200  # Should be at least 200 bytes for a QR code
        assert len(qr_data) < 100000  # Should be less than 100KB