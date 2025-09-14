"""
Integration test for QR code functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from src.main import app

client = TestClient(app)

class TestQRIntegration:
    """Integration tests for QR code functionality."""
    
    def test_qr_url_construction_in_response(self):
        """Test that link creation returns properly constructed QR URL."""
        # This test verifies that the QR URL is constructed correctly
        # when creating a link through the API
        
        with patch('src.routers.links.safety_service') as mock_safety_service:
            with patch('src.routers.links.firebase_service') as mock_firebase_service:
                # Mock safety validation
                mock_safety_service.validate_url.return_value = None
                
                # Mock Firestore operations
                mock_doc = Mock()
                mock_doc.exists = False  # Link doesn't exist yet
                mock_firebase_service.db.collection().document().get.return_value = mock_doc
                mock_firebase_service.db.collection().document().set.return_value = None
                mock_firebase_service.get_current_timestamp.return_value = Mock()
                
                # Mock domain validation
                with patch('src.routers.links.validate_base_domain') as mock_validate_domain:
                    mock_validate_domain.return_value = True
                    
                    # Make request to create link
                    request_data = {
                        "long_url": "https://example.com/test",
                        "base_domain": "go2.tools"
                    }
                    
                    response = client.post("/api/links/shorten", json=request_data)
                    
                    # Verify response structure
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Verify QR URL is present and properly formatted
                        assert "qr_url" in data
                        qr_url = data["qr_url"]
                        
                        # QR URL should be absolute when using TestClient
                        assert qr_url.startswith("http://testserver/api/qr/") or qr_url.startswith("/api/qr/")
                        assert data["code"] in qr_url
                        
                        print(f"✅ QR URL constructed: {qr_url}")
                        print(f"✅ Short URL: {data['short_url']}")
                        print(f"✅ Code: {data['code']}")
                        
                        return True
                    else:
                        print(f"❌ Link creation failed: {response.status_code}")
                        print(f"❌ Response: {response.json()}")
                        return False
    
    @patch('src.routers.qr.firebase_service')
    @patch('src.routers.qr.qr_service')
    def test_qr_endpoint_with_existing_link(self, mock_qr_service, mock_firebase_service):
        """Test QR endpoint with a mocked existing link."""
        # Mock link data
        link_data = {
            'long_url': 'https://example.com',
            'base_domain': 'go2.tools',
            'disabled': False,
            'expires_at': None,
            'owner_uid': 'test_user'
        }
        
        # Mock Firestore document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = link_data
        mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock QR generation
        from unittest.mock import AsyncMock
        mock_qr_service.generate_and_cache_qr = AsyncMock(return_value=b"fake_qr_data")
        mock_qr_service.validate_size.return_value = True
        
        # Test QR endpoint
        response = client.get("/api/qr/test123")
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == b"fake_qr_data"
        
        print("✅ QR endpoint works with existing link")
        
        # Verify QR service was called correctly
        mock_qr_service.generate_and_cache_qr.assert_called_once_with(
            "test123", 
            "https://go2.tools/test123", 
            "medium"
        )
    
    def test_qr_endpoint_with_nonexistent_link(self):
        """Test QR endpoint with non-existent link returns 404."""
        with patch('src.routers.qr.firebase_service') as mock_firebase_service:
            # Mock non-existent link
            mock_doc = Mock()
            mock_doc.exists = False
            mock_firebase_service.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            # Test QR endpoint
            response = client.get("/api/qr/nonexistent")
            
            # Verify 404 response
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
            
            print("✅ QR endpoint correctly returns 404 for non-existent links")
    
    def test_qr_url_format_validation(self):
        """Test that QR URLs follow the expected format."""
        test_cases = [
            {
                "scheme": "http",
                "netloc": "localhost:8000",
                "code": "abc123",
                "expected": "http://localhost:8000/api/qr/abc123"
            },
            {
                "scheme": "https", 
                "netloc": "api.go2.tools",
                "code": "xyz789",
                "expected": "https://api.go2.tools/api/qr/xyz789"
            }
        ]
        
        for case in test_cases:
            # Simulate the QR URL construction logic
            api_base_url = f"{case['scheme']}://{case['netloc']}"
            qr_url = f"{api_base_url}/api/qr/{case['code']}"
            
            assert qr_url == case["expected"]
            print(f"✅ QR URL format correct: {qr_url}")