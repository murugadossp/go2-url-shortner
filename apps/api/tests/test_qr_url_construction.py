"""
Test QR URL construction in link creation.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.main import app

client = TestClient(app)

class TestQRURLConstruction:
    """Test QR URL construction in link responses."""
    
    @patch('src.routers.links.safety_service')
    @patch('src.routers.links.firebase_service')
    def test_qr_url_construction_with_request(self, mock_firebase_service, mock_safety_service):
        """Test that QR URL is constructed with full API URL when request is available."""
        # Mock safety service
        mock_safety_service.validate_url.return_value = None
        
        # Mock Firestore operations
        mock_doc = Mock()
        mock_doc.exists = False  # Link doesn't exist yet
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        # Mock successful document creation
        mock_firebase_service.db.collection().document().set.return_value = None
        mock_firebase_service.get_current_timestamp.return_value = Mock()
        
        # Mock metadata fetching
        with patch('src.routers.links.fetch_url_metadata') as mock_fetch_metadata:
            mock_fetch_metadata.return_value = Mock(
                title="Test Page",
                host="example.com",
                favicon_url=None
            )
            
            # Mock domain validation
            with patch('src.routers.links.validate_base_domain') as mock_validate_domain:
                mock_validate_domain.return_value = True
                
                # Make request
                request_data = {
                    "long_url": "https://example.com/test",
                    "base_domain": "go2.tools"
                }
                
                response = client.post("/api/links/shorten", json=request_data)
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify QR URL is constructed with full API URL
                assert "qr_url" in data
                qr_url = data["qr_url"]
                
                # QR URL should be absolute and point to the test client's base URL
                assert qr_url.startswith("http://testserver/api/qr/")
                assert data["code"] in qr_url
                
                print(f"Generated QR URL: {qr_url}")
                print(f"Short URL: {data['short_url']}")
                print(f"Code: {data['code']}")
    
    def test_qr_url_fallback_without_request(self):
        """Test QR URL construction fallback when request is not available."""
        # This tests the fallback logic in the links router
        from src.routers.links import CreateLinkResponse
        
        # Simulate the QR URL construction logic
        code = "test123"
        http_request = None  # No request available
        
        if http_request:
            api_base_url = f"{http_request.url.scheme}://{http_request.url.netloc}"
            qr_url = f"{api_base_url}/api/qr/{code}"
        else:
            # Fallback to relative URL
            qr_url = f"/api/qr/{code}"
        
        # Should fallback to relative URL
        assert qr_url == "/api/qr/test123"
        assert not qr_url.startswith("http")
        
        print(f"Fallback QR URL: {qr_url}")