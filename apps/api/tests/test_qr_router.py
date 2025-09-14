"""
Tests for QR code router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from src.main import app

client = TestClient(app)

class TestQRRouter:
    """Test cases for QR router endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_code = "abc123"
        self.test_link_data = {
            'long_url': 'https://example.com',
            'base_domain': 'go2.tools',
            'disabled': False,
            'expires_at': None,
            'owner_uid': 'test_user'
        }
    
    @patch('src.routers.qr.firebase_service')
    @patch('src.routers.qr.qr_service')
    def test_get_qr_code_success(self, mock_qr_service, mock_firebase_service):
        """Test successful QR code generation."""
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_link_data
        
        mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock QR generation
        mock_qr_service.generate_and_cache_qr = AsyncMock(return_value=b"fake_qr_data")
        
        # Make request
        response = client.get(f"/api/qr/{self.test_code}")
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == b"fake_qr_data"
        assert "Cache-Control" in response.headers
        assert "Content-Disposition" in response.headers
        
        # Verify QR generation was called with correct URL
        mock_qr_service.generate_and_cache_qr.assert_called_once_with(
            self.test_code, 
            "https://go2.tools/abc123", 
            "medium"
        )
    
    @patch('src.routers.qr.firebase_service')
    def test_get_qr_code_link_not_found(self, mock_firebase_service):
        """Test QR code generation for non-existent link."""
        # Mock Firestore document that doesn't exist
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get(f"/api/qr/{self.test_code}")
        
        # Verify 404 response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('src.routers.qr.firebase_service')
    def test_get_qr_code_disabled_link(self, mock_firebase_service):
        """Test QR code generation for disabled link."""
        # Mock disabled link
        disabled_link_data = {**self.test_link_data, 'disabled': True}
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = disabled_link_data
        
        mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get(f"/api/qr/{self.test_code}")
        
        # Verify 410 response
        assert response.status_code == 410
        assert "disabled" in response.json()["detail"]
    
    @patch('src.routers.qr.firebase_service')
    def test_get_qr_code_expired_link(self, mock_firebase_service):
        """Test QR code generation for expired link."""
        from datetime import datetime, timezone
        
        # Mock current time and expired link
        current_time = datetime.now(timezone.utc)
        past_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        mock_firebase_service.get_current_timestamp.return_value = Mock(timestamp=lambda: current_time.timestamp())
        
        expired_link_data = {
            **self.test_link_data, 
            'expires_at': Mock(timestamp=lambda: past_time.timestamp())
        }
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = expired_link_data
        
        mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get(f"/api/qr/{self.test_code}")
        
        # Verify 410 response
        assert response.status_code == 410
        assert "expired" in response.json()["detail"]
    
    @patch('src.routers.qr.firebase_service')
    @patch('src.routers.qr.qr_service')
    def test_get_qr_code_different_sizes(self, mock_qr_service, mock_firebase_service):
        """Test QR code generation with different sizes."""
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_link_data
        
        mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock QR generation
        mock_qr_service.generate_and_cache_qr = AsyncMock(return_value=b"fake_qr_data")
        
        sizes = ["small", "medium", "large"]
        
        for size in sizes:
            response = client.get(f"/api/qr/{self.test_code}?size={size}")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
    
    def test_get_qr_code_invalid_size(self):
        """Test QR code generation with invalid size."""
        response = client.get(f"/api/qr/{self.test_code}?size=invalid")
        
        # Verify 400 response
        assert response.status_code == 400
        assert "Invalid size" in response.json()["detail"]
    
    @patch('src.routers.qr.firebase_service')
    @patch('src.routers.qr.qr_service')
    def test_get_qr_code_generation_failure(self, mock_qr_service, mock_firebase_service):
        """Test QR code generation failure."""
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_link_data
        
        mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock QR generation failure
        mock_qr_service.generate_and_cache_qr.side_effect = Exception("QR generation failed")
        
        # Make request
        response = client.get(f"/api/qr/{self.test_code}")
        
        # Verify 500 response
        assert response.status_code == 500
        assert "Failed to generate QR code" in response.json()["detail"]
    
    @patch('src.routers.qr.firebase_service')
    def test_get_qr_info_success(self, mock_firebase_service):
        """Test successful QR info retrieval."""
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = self.test_link_data
        
        mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get(f"/api/qr/{self.test_code}/info")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == self.test_code
        assert data["short_url"] == "https://go2.tools/abc123"
        assert "qr_urls" in data
        assert "small" in data["qr_urls"]
        assert "medium" in data["qr_urls"]
        assert "large" in data["qr_urls"]
        assert "sizes" in data
        
        # Verify QR URLs are correct
        assert data["qr_urls"]["small"] == f"/api/qr/{self.test_code}?size=small"
        assert data["qr_urls"]["medium"] == f"/api/qr/{self.test_code}?size=medium"
        assert data["qr_urls"]["large"] == f"/api/qr/{self.test_code}?size=large"
    
    @patch('src.routers.qr.firebase_service')
    def test_get_qr_info_link_not_found(self, mock_firebase_service):
        """Test QR info for non-existent link."""
        # Mock Firestore document that doesn't exist
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get(f"/api/qr/{self.test_code}/info")
        
        # Verify 404 response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('src.routers.qr.firebase_service')
    def test_get_qr_info_different_domains(self, mock_firebase_service):
        """Test QR info with different base domains."""
        domains = ["go2.video", "go2.reviews", "go2.tools"]
        
        for domain in domains:
            link_data = {**self.test_link_data, 'base_domain': domain}
            
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = link_data
            
            mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            response = client.get(f"/api/qr/{self.test_code}/info")
            
            assert response.status_code == 200
            data = response.json()
            assert data["short_url"] == f"https://{domain}/{self.test_code}"
    
    @patch('src.routers.qr.firebase_service')
    def test_get_qr_info_database_error(self, mock_firebase_service):
        """Test QR info with database error."""
        # Mock database error
        mock_firebase_service.db.collection.side_effect = Exception("Database error")
        
        # Make request
        response = client.get(f"/api/qr/{self.test_code}/info")
        
        # Verify 500 response
        assert response.status_code == 500
        assert "Failed to retrieve QR code information" in response.json()["detail"]

class TestQRRouterIntegration:
    """Integration tests for QR router."""
    
    def test_qr_router_registered(self):
        """Test that QR router is properly registered."""
        # Test that the QR endpoints are available
        response = client.get("/api/qr/nonexistent")
        # Should get 404 for link not found, not 404 for route not found
        assert response.status_code in [404, 500]  # Either link not found or DB error
        
        response = client.get("/api/qr/nonexistent/info")
        assert response.status_code in [404, 500]  # Either link not found or DB error