"""
Integration tests for domain configuration and validation functionality.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from src.main import app
from src.utils.auth import require_admin


class TestDomainIntegration:
    """Integration tests for domain configuration system"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_domain_configuration_flow(self):
        """Test complete domain configuration flow"""
        # Mock admin user
        def mock_admin_user():
            return {'uid': 'admin123', 'admin': True}
        
        app.dependency_overrides[require_admin] = mock_admin_user
        
        try:
            with patch('src.routers.config.firebase_service') as mock_firebase:
                # Mock Firestore operations
                mock_doc = Mock()
                mock_doc.exists = True
                mock_doc.to_dict.return_value = {
                    'base_domains': ['go2.video', 'go2.reviews'],
                    'domain_suggestions': {'youtube.com': 'go2.video'},
                    'last_updated': '2024-01-01T00:00:00'
                }
                
                # Create a proper mock chain
                mock_collection = Mock()
                mock_document = Mock()
                mock_collection.document.return_value = mock_document
                mock_document.get.return_value = mock_doc
                mock_firebase.db.collection.return_value = mock_collection
                # For the update operation, use the same mock_document
                mock_ref = mock_document
                
                # 1. Get current config
                response = self.client.get("/api/config/admin/domains")
                assert response.status_code == status.HTTP_200_OK
                config_data = response.json()['data']
                assert len(config_data['base_domains']) == 2
                
                # 2. Update config
                new_config = {
                    'base_domains': ['go2.video', 'go2.tools'],
                    'domain_suggestions': {
                        'github.com': 'go2.tools',
                        'youtube.com': 'go2.video'
                    }
                }
                
                response = self.client.put("/api/config/admin/domains", json=new_config)
                assert response.status_code == status.HTTP_200_OK
                
                # Verify Firestore was called with correct data
                mock_ref.set.assert_called_once()
                call_args = mock_ref.set.call_args[0][0]
                assert call_args['base_domains'] == new_config['base_domains']
                assert call_args['domain_suggestions'] == new_config['domain_suggestions']
                
        finally:
            if require_admin in app.dependency_overrides:
                del app.dependency_overrides[require_admin]
    
    def test_public_config_endpoint_integration(self):
        """Test public config endpoint with different Firestore states"""
        # Test with custom config
        with patch('src.routers.config.firebase_service') as mock_firebase:
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                'base_domains': ['go2.video'],
                'domain_suggestions': {'youtube.com': 'go2.video'}
            }
            mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            response = self.client.get("/api/config/base-domains")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()['data']
            assert data['base_domains'] == ['go2.video']
            assert data['domain_suggestions']['youtube.com'] == 'go2.video'
    
    def test_link_creation_with_domain_validation(self):
        """Test link creation with domain validation"""
        with patch('src.routers.links.firebase_service') as mock_firebase, \
             patch('src.routers.links.safety_service') as mock_safety, \
             patch('src.routers.links.get_valid_base_domains') as mock_get_domains:
            
            # Mock safety service
            mock_safety.validate_url.return_value = None
            
            # Mock domain validation
            mock_get_domains.return_value = ['go2.video', 'go2.tools']
            
            # Mock Firestore operations
            mock_doc = Mock()
            mock_doc.exists = False
            mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
            mock_firebase.db.collection.return_value.document.return_value.set.return_value = None
            
            # Test valid domain
            request_data = {
                "long_url": "https://example.com/test",
                "base_domain": "go2.video"
            }
            
            response = self.client.post("/api/links/shorten", json=request_data)
            assert response.status_code == status.HTTP_200_OK
            
            # Test invalid domain
            request_data = {
                "long_url": "https://example.com/test",
                "base_domain": "go2.reviews"  # Not in allowed domains
            }
            
            response = self.client.post("/api/links/shorten", json=request_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "Invalid base domain" in response.json()["detail"]
    
    def test_domain_suggestion_algorithm(self):
        """Test domain suggestion algorithm with various URLs"""
        test_cases = [
            # (URL, expected_pattern_match, expected_domain)
            ('https://youtube.com/watch?v=123', 'youtube.com', 'go2.video'),
            ('https://www.youtube.com/channel/123', 'youtube.com', 'go2.video'),
            ('https://youtu.be/123', 'youtu.be', 'go2.video'),
            ('https://github.com/user/repo', 'github.com', 'go2.tools'),
            ('https://amazon.com/product/123', 'amazon.com', 'go2.reviews'),
        ]
        
        # Mock domain suggestions
        domain_suggestions = {
            'youtube.com': 'go2.video',
            'youtu.be': 'go2.video',
            'github.com': 'go2.tools',
            'amazon.com': 'go2.reviews'
        }
        
        for url, expected_pattern, expected_domain in test_cases:
            from urllib.parse import urlparse
            hostname = urlparse(url).hostname.lower()
            
            # Find matching pattern
            suggested_domain = None
            for pattern, domain in domain_suggestions.items():
                if pattern in hostname:
                    suggested_domain = domain
                    break
            
            assert suggested_domain == expected_domain, f"Failed for URL: {url}"
    
    def test_config_caching_headers(self):
        """Test that config endpoints return proper caching headers"""
        with patch('src.routers.config.firebase_service'):
            response = self.client.get("/api/config/base-domains")
            
            assert response.status_code == status.HTTP_200_OK
            assert 'Cache-Control' in response.headers
            assert 'ETag' in response.headers
            assert 'max-age=300' in response.headers['Cache-Control']
            assert 'public' in response.headers['Cache-Control']
    
    def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback behavior"""
        # Test Firestore error fallback
        with patch('src.routers.config.firebase_service') as mock_firebase:
            mock_firebase.db.collection.return_value.document.return_value.get.side_effect = Exception("DB Error")
            
            response = self.client.get("/api/config/base-domains")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert 'fallback' in data['message']
            assert len(data['data']['base_domains']) == 3  # Default domains
            
        # Test domain validation fallback
        with patch('src.routers.links.get_valid_base_domains') as mock_get_domains:
            mock_get_domains.return_value = ['go2.video', 'go2.reviews', 'go2.tools']  # Fallback domains
            
            from src.routers.links import validate_base_domain
            import asyncio
            
            # Should work with fallback domains
            assert asyncio.run(validate_base_domain('go2.video')) == True
            assert asyncio.run(validate_base_domain('invalid.domain')) == False