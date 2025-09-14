"""
Tests for config router endpoints and domain management functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from src.main import app
from src.models.config import DomainConfigRequest
from src.utils.auth import require_admin


class TestConfigEndpoints:
    """Test config router endpoints"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_get_base_domains_success(self):
        """Test successful retrieval of base domains"""
        with patch('src.routers.config.firebase_service') as mock_firebase:
            # Mock Firestore document
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                'base_domains': ['go2.video', 'go2.reviews', 'go2.tools'],
                'domain_suggestions': {
                    'youtube.com': 'go2.video',
                    'amazon.com': 'go2.reviews'
                }
            }
            mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            response = self.client.get("/api/config/base-domains")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert 'data' in data
            assert 'base_domains' in data['data']
            assert 'domain_suggestions' in data['data']
            assert len(data['data']['base_domains']) == 3
            assert 'go2.video' in data['data']['base_domains']
    
    def test_get_base_domains_fallback(self):
        """Test fallback when Firestore document doesn't exist"""
        with patch('src.routers.config.firebase_service') as mock_firebase:
            # Mock Firestore document not existing
            mock_doc = Mock()
            mock_doc.exists = False
            mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            response = self.client.get("/api/config/base-domains")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert 'data' in data
            assert len(data['data']['base_domains']) == 3
            assert 'youtube.com' in data['data']['domain_suggestions']
    
    def test_get_base_domains_error_fallback(self):
        """Test fallback when Firestore throws an error"""
        with patch('src.routers.config.firebase_service') as mock_firebase:
            # Mock Firestore error
            mock_firebase.db.collection.return_value.document.return_value.get.side_effect = Exception("Firestore error")
            
            response = self.client.get("/api/config/base-domains")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert 'fallback' in data['message']
            assert len(data['data']['base_domains']) == 3
    
    def test_get_base_domains_caching_headers(self):
        """Test that proper caching headers are set"""
        with patch('src.routers.config.firebase_service'):
            response = self.client.get("/api/config/base-domains")
            
            assert response.status_code == status.HTTP_200_OK
            assert 'Cache-Control' in response.headers
            assert 'ETag' in response.headers
            assert 'max-age=300' in response.headers['Cache-Control']


class TestAdminConfigEndpoints:
    """Test admin config endpoints"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_get_admin_domain_config_success(self):
        """Test successful retrieval of admin domain config"""
        # Mock admin user dependency
        def mock_admin_user():
            return {'uid': 'admin123', 'admin': True}
        
        app.dependency_overrides[require_admin] = mock_admin_user
        
        try:
            with patch('src.routers.config.firebase_service') as mock_firebase:
                # Mock Firestore document
                mock_doc = Mock()
                mock_doc.exists = True
                mock_doc.to_dict.return_value = {
                    'base_domains': ['go2.video', 'go2.reviews'],
                    'domain_suggestions': {'youtube.com': 'go2.video'},
                    'last_updated': '2024-01-01T00:00:00'
                }
                mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
                
                response = self.client.get("/api/config/admin/domains")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert 'data' in data
                assert len(data['data']['base_domains']) == 2
                assert data['data']['last_updated'] == '2024-01-01T00:00:00'
        finally:
            # Clean up dependency override
            if require_admin in app.dependency_overrides:
                del app.dependency_overrides[require_admin]
    
    def test_get_admin_domain_config_default(self):
        """Test default config when document doesn't exist"""
        def mock_admin_user():
            return {'uid': 'admin123', 'admin': True}
        
        app.dependency_overrides[require_admin] = mock_admin_user
        
        try:
            with patch('src.routers.config.firebase_service') as mock_firebase:
                # Mock Firestore document not existing
                mock_doc = Mock()
                mock_doc.exists = False
                mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
                
                response = self.client.get("/api/config/admin/domains")
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data['data']['base_domains']) == 3
                assert data['data']['last_updated'] is None
        finally:
            if require_admin in app.dependency_overrides:
                del app.dependency_overrides[require_admin]
    
    def test_update_domain_config_success(self):
        """Test successful domain config update"""
        def mock_admin_user():
            return {'uid': 'admin123', 'admin': True}
        
        app.dependency_overrides[require_admin] = mock_admin_user
        
        try:
            with patch('src.routers.config.firebase_service') as mock_firebase:
                # Mock Firestore set operation
                mock_ref = Mock()
                mock_firebase.db.collection.return_value.document.return_value = mock_ref
                
                request_data = {
                    'base_domains': ['go2.video', 'go2.reviews'],
                    'domain_suggestions': {
                        'youtube.com': 'go2.video',
                        'amazon.com': 'go2.reviews'
                    }
                }
                
                response = self.client.put("/api/config/admin/domains", json=request_data)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert 'updated successfully' in data['message']
                
                # Verify Firestore was called
                mock_ref.set.assert_called_once()
                call_args = mock_ref.set.call_args[0][0]
                assert call_args['base_domains'] == request_data['base_domains']
                assert call_args['domain_suggestions'] == request_data['domain_suggestions']
        finally:
            if require_admin in app.dependency_overrides:
                del app.dependency_overrides[require_admin]
    
    def test_update_domain_config_invalid_domain(self):
        """Test update with invalid domain"""
        def mock_admin_user():
            return {'uid': 'admin123', 'admin': True}
        
        app.dependency_overrides[require_admin] = mock_admin_user
        
        try:
            request_data = {
                'base_domains': ['invalid.domain', 'go2.video'],
                'domain_suggestions': {}
            }
            
            response = self.client.put("/api/config/admin/domains", json=request_data)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            # Pydantic validation error format
            response_data = response.json()
            assert 'detail' in response_data
            assert isinstance(response_data['detail'], list)
            assert any('go2.video' in str(error) for error in response_data['detail'])
        finally:
            if require_admin in app.dependency_overrides:
                del app.dependency_overrides[require_admin]
    
    def test_update_domain_config_invalid_suggestion(self):
        """Test update with invalid domain suggestion"""
        def mock_admin_user():
            return {'uid': 'admin123', 'admin': True}
        
        app.dependency_overrides[require_admin] = mock_admin_user
        
        try:
            request_data = {
                'base_domains': ['go2.video', 'go2.reviews'],
                'domain_suggestions': {
                    'youtube.com': 'invalid.domain'
                }
            }
            
            response = self.client.put("/api/config/admin/domains", json=request_data)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            # Pydantic validation error format
            response_data = response.json()
            assert 'detail' in response_data
            assert isinstance(response_data['detail'], list)
            assert any('go2.video' in str(error) for error in response_data['detail'])
        finally:
            if require_admin in app.dependency_overrides:
                del app.dependency_overrides[require_admin]


class TestDomainSuggestionLogic:
    """Test domain suggestion algorithm"""
    
    def test_youtube_suggestions(self):
        """Test YouTube domain suggestions"""
        test_cases = [
            ('https://youtube.com/watch?v=123', 'go2.video'),
            ('https://youtu.be/123', 'go2.video'),
            ('https://www.youtube.com/channel/123', 'go2.video'),
        ]
        
        # Mock the domain suggestions from config
        domain_suggestions = {
            'youtube.com': 'go2.video',
            'youtu.be': 'go2.video'
        }
        
        for url, expected_domain in test_cases:
            from urllib.parse import urlparse
            hostname = urlparse(url).hostname.lower()
            
            suggested = None
            for pattern, domain in domain_suggestions.items():
                if pattern in hostname:
                    suggested = domain
                    break
            
            assert suggested == expected_domain, f"Failed for URL: {url}"
    
    def test_review_site_suggestions(self):
        """Test review site domain suggestions"""
        test_cases = [
            ('https://amazon.com/product/123', 'go2.reviews'),
            ('https://yelp.com/biz/restaurant', 'go2.reviews'),
            ('https://tripadvisor.com/hotel/123', 'go2.reviews'),
        ]
        
        domain_suggestions = {
            'amazon.com': 'go2.reviews',
            'yelp.com': 'go2.reviews',
            'tripadvisor.com': 'go2.reviews'
        }
        
        for url, expected_domain in test_cases:
            from urllib.parse import urlparse
            hostname = urlparse(url).hostname.lower()
            
            suggested = None
            for pattern, domain in domain_suggestions.items():
                if pattern in hostname:
                    suggested = domain
                    break
            
            assert suggested == expected_domain, f"Failed for URL: {url}"
    
    def test_tools_suggestions(self):
        """Test tools domain suggestions"""
        test_cases = [
            ('https://github.com/user/repo', 'go2.tools'),
            ('https://stackoverflow.com/questions/123', 'go2.tools'),
            ('https://docs.google.com/document/123', 'go2.tools'),
        ]
        
        domain_suggestions = {
            'github.com': 'go2.tools',
            'stackoverflow.com': 'go2.tools',
            'docs.google.com': 'go2.tools'
        }
        
        for url, expected_domain in test_cases:
            from urllib.parse import urlparse
            hostname = urlparse(url).hostname.lower()
            
            suggested = None
            for pattern, domain in domain_suggestions.items():
                if pattern in hostname:
                    suggested = domain
                    break
            
            assert suggested == expected_domain, f"Failed for URL: {url}"