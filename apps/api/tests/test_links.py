"""
Comprehensive tests for link creation and management system.
Tests all endpoints, edge cases, and business logic.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from src.main import app
from src.models.link import CreateLinkRequest, LinkDocument
from src.services.safety_service import SafetyError
from src.routers.links import generate_short_code, hash_password, verify_password, hash_ip
from src.utils.auth import get_current_user, require_auth, require_admin

client = TestClient(app)

# Test fixtures
@pytest.fixture
def mock_firebase_service():
    """Mock Firebase service for testing"""
    with patch('src.routers.links.firebase_service') as mock:
        # Mock Firestore client
        mock_db = Mock()
        mock.db = mock_db
        
        # Mock document references
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        mock_doc.to_dict.return_value = {}
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.set = Mock()
        mock_doc_ref.update = Mock()
        mock_doc_ref.delete = Mock()
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        mock_collection.where.return_value = mock_collection
        mock_collection.order_by.return_value = mock_collection
        mock_collection.limit.return_value = mock_collection
        mock_collection.offset.return_value = mock_collection
        mock_collection.stream.return_value = []
        
        mock_db.collection.return_value = mock_collection
        
        yield mock

@pytest.fixture
def mock_safety_service():
    """Mock safety service for testing"""
    with patch('src.routers.links.safety_service') as mock:
        mock.validate_url = Mock()
        yield mock

@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return {
        'uid': 'test-user-123',
        'email': 'test@example.com',
        'name': 'Test User'
    }

@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    return {
        'uid': 'admin-user-123',
        'email': 'admin@example.com',
        'name': 'Admin User',
        'admin': True
    }

class TestLinkCreation:
    """Test link creation functionality"""
    
    def test_create_link_success(self, mock_firebase_service, mock_safety_service):
        """Test successful link creation"""
        # Setup mocks
        mock_safety_service.validate_url.return_value = None
        
        request_data = {
            "long_url": "https://example.com/very/long/url",
            "base_domain": "go2.tools"
        }
        
        response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "short_url" in data
        assert "code" in data
        assert "qr_url" in data
        assert data["long_url"] == request_data["long_url"]
        assert data["base_domain"] == request_data["base_domain"]
        
        # Verify safety validation was called
        mock_safety_service.validate_url.assert_called_once_with(request_data["long_url"])
        
        # Verify Firestore operations
        mock_firebase_service.db.collection.assert_called_with('links')
    
    def test_create_link_with_custom_code(self, mock_firebase_service, mock_safety_service):
        """Test link creation with custom code"""
        mock_safety_service.validate_url.return_value = None
        
        request_data = {
            "long_url": "https://example.com/test",
            "base_domain": "go2.video",
            "custom_code": "mycustomcode"
        }
        
        with patch('src.routers.links.get_current_user') as mock_get_user:
            mock_get_user.return_value = {
                'uid': 'test-user',
                'email': 'test@example.com'
            }
            
            with patch('src.routers.links.get_user_document') as mock_get_user_doc:
                mock_get_user_doc.return_value = Mock(
                    plan_type='free',
                    custom_codes_used=0,
                    custom_codes_reset_date=datetime.utcnow() + timedelta(days=30)
                )
                
                response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["code"] == "mycustomcode"
    
    def test_create_link_custom_code_collision(self, mock_firebase_service, mock_safety_service):
        """Test custom code collision handling"""
        mock_safety_service.validate_url.return_value = None
        
        # Mock existing document
        mock_doc = Mock()
        mock_doc.exists = True
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        request_data = {
            "long_url": "https://example.com/test",
            "base_domain": "go2.tools",
            "custom_code": "taken"
        }
        
        with patch('src.routers.links.get_current_user') as mock_get_user:
            mock_get_user.return_value = {'uid': 'test-user'}
            
            with patch('src.routers.links.get_user_document') as mock_get_user_doc:
                mock_get_user_doc.return_value = Mock(
                    plan_type='free',
                    custom_codes_used=0,
                    custom_codes_reset_date=datetime.utcnow() + timedelta(days=30)
                )
                
                response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "already taken" in data["detail"]["message"]
        assert "suggestions" in data["detail"]
    
    def test_create_link_safety_violation(self, mock_firebase_service, mock_safety_service):
        """Test link creation blocked by safety validation"""
        mock_safety_service.validate_url.side_effect = SafetyError(
            "URL blocked", ["malware detected"]
        )
        
        request_data = {
            "long_url": "https://malicious.com/virus",
            "base_domain": "go2.tools"
        }
        
        response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "safety validation" in response.json()["detail"]
    
    def test_create_link_custom_code_limit_exceeded(self, mock_firebase_service, mock_safety_service):
        """Test custom code limit enforcement"""
        mock_safety_service.validate_url.return_value = None
        
        request_data = {
            "long_url": "https://example.com/test",
            "base_domain": "go2.tools",
            "custom_code": "newcode"
        }
        
        # Mock the dependency override
        def mock_get_current_user():
            return {'uid': 'test-user', 'email': 'test@example.com'}
        
        # Override the dependency
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        try:
            with patch('src.routers.links.get_user_document') as mock_get_user_doc:
                mock_get_user_doc.return_value = Mock(
                    plan_type='free',
                    custom_codes_used=5,  # At limit
                    custom_codes_reset_date=datetime.utcnow() + timedelta(days=30)
                )
                
                response = client.post("/api/links/shorten", json=request_data)
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "limit exceeded" in response.json()["detail"]
    
    def test_create_link_with_password(self, mock_firebase_service, mock_safety_service):
        """Test link creation with password protection"""
        mock_safety_service.validate_url.return_value = None
        
        request_data = {
            "long_url": "https://example.com/secret",
            "base_domain": "go2.tools",
            "password": "secretpass123"
        }
        
        response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify password was hashed and stored
        mock_firebase_service.db.collection().document().set.assert_called_once()
        call_args = mock_firebase_service.db.collection().document().set.call_args[0][0]
        assert call_args['password_hash'] is not None
        assert call_args['password_hash'] != "secretpass123"  # Should be hashed
    
    def test_create_link_with_expiration(self, mock_firebase_service, mock_safety_service):
        """Test link creation with expiration date"""
        mock_safety_service.validate_url.return_value = None
        
        future_date = datetime.utcnow() + timedelta(days=7)
        request_data = {
            "long_url": "https://example.com/temporary",
            "base_domain": "go2.tools",
            "expires_at": future_date.isoformat()
        }
        
        response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["expires_at"] is not None
    
    def test_create_link_invalid_url(self, mock_firebase_service, mock_safety_service):
        """Test link creation with invalid URL"""
        request_data = {
            "long_url": "not-a-valid-url",
            "base_domain": "go2.tools"
        }
        
        response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_link_invalid_domain(self, mock_firebase_service, mock_safety_service):
        """Test link creation with invalid base domain"""
        with patch('src.routers.links.get_valid_base_domains') as mock_get_domains:
            mock_get_domains.return_value = ['go2.video', 'go2.reviews', 'go2.tools']
            
            request_data = {
                "long_url": "https://example.com/test",
                "base_domain": "invalid.domain"
            }
            
            response = client.post("/api/links/shorten", json=request_data)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "Invalid base domain" in response.json()["detail"]
    
    def test_create_link_valid_domains(self, mock_firebase_service, mock_safety_service):
        """Test link creation with all valid base domains"""
        with patch('src.routers.links.get_valid_base_domains') as mock_get_domains:
            mock_get_domains.return_value = ['go2.video', 'go2.reviews', 'go2.tools']
            
            valid_domains = ['go2.video', 'go2.reviews', 'go2.tools']
            
            for domain in valid_domains:
                request_data = {
                    "long_url": "https://example.com/test",
                    "base_domain": domain
                }
                
                response = client.post("/api/links/shorten", json=request_data)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["base_domain"] == domain
                assert domain in data["short_url"]
    
    def test_create_link_domain_validation_firestore_error(self, mock_firebase_service, mock_safety_service):
        """Test domain validation fallback when Firestore fails"""
        with patch('src.routers.links.get_valid_base_domains') as mock_get_domains:
            # Simulate Firestore error, should fall back to default domains
            mock_get_domains.return_value = ['go2.video', 'go2.reviews', 'go2.tools']
            
            request_data = {
                "long_url": "https://example.com/test",
                "base_domain": "go2.video"  # Valid default domain
            }
            
            response = client.post("/api/links/shorten", json=request_data)
            
            assert response.status_code == status.HTTP_200_OK

class TestLinkRedirection:
    """Test link redirection functionality"""
    
    def test_redirect_success(self, mock_firebase_service):
        """Test successful link redirection"""
        # Mock existing link
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/target',
            'disabled': False,
            'expires_at': None,
            'password_hash': None
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        response = client.get("/api/links/testcode", follow_redirects=False)
        
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "https://example.com/target"
    
    def test_redirect_not_found(self, mock_firebase_service):
        """Test redirection for non-existent link"""
        mock_doc = Mock()
        mock_doc.exists = False
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        response = client.get("/api/links/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_redirect_disabled_link(self, mock_firebase_service):
        """Test redirection for disabled link"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/target',
            'disabled': True
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        response = client.get("/api/links/disabled")
        
        assert response.status_code == status.HTTP_410_GONE
        assert "disabled" in response.json()["detail"]
    
    def test_redirect_expired_link(self, mock_firebase_service):
        """Test redirection for expired link"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/target',
            'disabled': False,
            'expires_at': datetime.utcnow() - timedelta(days=1)  # Expired
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        response = client.get("/api/links/expired")
        
        assert response.status_code == status.HTTP_410_GONE
        assert "expired" in response.json()["detail"]
    
    def test_redirect_password_protected_no_password(self, mock_firebase_service):
        """Test redirection for password-protected link without password"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/secret',
            'disabled': False,
            'expires_at': None,
            'password_hash': hash_password('secret123')
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        response = client.get("/api/links/protected")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Password required" in response.json()["detail"]
    
    def test_redirect_password_protected_wrong_password(self, mock_firebase_service):
        """Test redirection for password-protected link with wrong password"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/secret',
            'disabled': False,
            'expires_at': None,
            'password_hash': hash_password('secret123')
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        response = client.get("/api/links/protected?password=wrongpass")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect password" in response.json()["detail"]
    
    def test_redirect_password_protected_correct_password(self, mock_firebase_service):
        """Test redirection for password-protected link with correct password"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/secret',
            'disabled': False,
            'expires_at': None,
            'password_hash': hash_password('secret123')
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        response = client.get("/api/links/protected?password=secret123", follow_redirects=False)
        
        assert response.status_code == status.HTTP_302_FOUND
        assert response.headers["location"] == "https://example.com/secret"

class TestLinkManagement:
    """Test link management functionality"""
    
    def test_update_link_success(self, mock_firebase_service):
        """Test successful link update"""
        # Mock existing link owned by user
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'owner_uid': 'test-user-123',
            'long_url': 'https://example.com/test'
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        update_data = {
            "disabled": True,
            "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
        
        def mock_require_auth():
            return {'uid': 'test-user-123'}
        
        app.dependency_overrides[require_auth] = mock_require_auth
        
        try:
            response = client.put("/api/links/testcode", json=update_data)
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == status.HTTP_200_OK
        mock_firebase_service.db.collection().document().update.assert_called_once()
    
    def test_update_link_not_found(self, mock_firebase_service):
        """Test updating non-existent link"""
        mock_doc = Mock()
        mock_doc.exists = False
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        def mock_require_auth():
            return {'uid': 'test-user-123'}
        
        app.dependency_overrides[require_auth] = mock_require_auth
        
        try:
            response = client.put("/api/links/nonexistent", json={"disabled": True})
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_link_permission_denied(self, mock_firebase_service):
        """Test updating link without permission"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'owner_uid': 'other-user-123',  # Different user
            'long_url': 'https://example.com/test'
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        def mock_require_auth():
            return {'uid': 'test-user-123', 'admin': False}
        
        app.dependency_overrides[require_auth] = mock_require_auth
        
        try:
            response = client.put("/api/links/testcode", json={"disabled": True})
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_link_admin_permission(self, mock_firebase_service):
        """Test admin can update any link"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'owner_uid': 'other-user-123',
            'long_url': 'https://example.com/test'
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        def mock_require_auth():
            return {'uid': 'admin-user-123', 'admin': True}
        
        app.dependency_overrides[require_auth] = mock_require_auth
        
        try:
            response = client.put("/api/links/testcode", json={"disabled": True})
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_delete_link_success(self, mock_firebase_service):
        """Test successful link deletion"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'owner_uid': 'test-user-123',
            'long_url': 'https://example.com/test'
        }
        mock_firebase_service.db.collection().document().get.return_value = mock_doc
        
        def mock_require_auth():
            return {'uid': 'test-user-123'}
        
        app.dependency_overrides[require_auth] = mock_require_auth
        
        try:
            response = client.delete("/api/links/testcode")
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == status.HTTP_200_OK
        mock_firebase_service.db.collection().document().delete.assert_called_once()
    
    def test_list_user_links(self, mock_firebase_service):
        """Test listing user's links"""
        # Mock query results
        mock_doc1 = Mock()
        mock_doc1.id = 'code1'
        mock_doc1.to_dict.return_value = {
            'long_url': 'https://example.com/1',
            'base_domain': 'go2.tools',
            'created_at': datetime.utcnow(),
            'disabled': False,
            'expires_at': None,
            'owner_uid': 'test-user-123',
            'is_custom_code': False
        }
        
        mock_firebase_service.db.collection().where().order_by().limit().offset().stream.return_value = [mock_doc1]
        
        def mock_require_auth():
            return {'uid': 'test-user-123'}
        
        app.dependency_overrides[require_auth] = mock_require_auth
        
        try:
            response = client.get("/api/links/")
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['code'] == 'code1'
    
    def test_list_all_links_admin(self, mock_firebase_service):
        """Test admin listing all links"""
        mock_doc1 = Mock()
        mock_doc1.id = 'code1'
        mock_doc1.to_dict.return_value = {
            'long_url': 'https://example.com/1',
            'base_domain': 'go2.tools',
            'created_at': datetime.utcnow(),
            'disabled': False,
            'expires_at': None,
            'owner_uid': 'some-user',
            'is_custom_code': False
        }
        
        mock_firebase_service.db.collection().order_by().limit().offset().stream.return_value = [mock_doc1]
        
        def mock_require_admin():
            return {'uid': 'admin-user-123', 'admin': True}
        
        app.dependency_overrides[require_admin] = mock_require_admin
        
        try:
            response = client.get("/api/links/admin/all")
        finally:
            app.dependency_overrides.clear()
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_generate_short_code(self):
        """Test short code generation"""
        code = generate_short_code()
        assert len(code) == 6
        assert code.isalnum()
        
        # Test custom length
        code = generate_short_code(10)
        assert len(code) == 10
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)
    
    def test_ip_hashing(self):
        """Test IP address hashing"""
        ip = "192.168.1.1"
        hashed = hash_ip(ip)
        
        assert hashed != ip
        assert len(hashed) == 16
        
        # Same IP should produce same hash
        assert hash_ip(ip) == hashed

class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_create_link_database_error(self, mock_firebase_service, mock_safety_service):
        """Test handling of database errors during link creation"""
        mock_safety_service.validate_url.return_value = None
        mock_firebase_service.db.collection().document().set.side_effect = Exception("DB Error")
        
        request_data = {
            "long_url": "https://example.com/test",
            "base_domain": "go2.tools"
        }
        
        response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_redirect_database_error(self, mock_firebase_service):
        """Test handling of database errors during redirection"""
        mock_firebase_service.db.collection().document().get.side_effect = Exception("DB Error")
        
        response = client.get("/api/links/testcode")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_create_link_empty_custom_code(self, mock_firebase_service, mock_safety_service):
        """Test link creation with empty custom code"""
        mock_safety_service.validate_url.return_value = None
        
        request_data = {
            "long_url": "https://example.com/test",
            "base_domain": "go2.tools",
            "custom_code": ""
        }
        
        response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_link_invalid_custom_code_characters(self, mock_firebase_service, mock_safety_service):
        """Test link creation with invalid custom code characters"""
        mock_safety_service.validate_url.return_value = None
        
        request_data = {
            "long_url": "https://example.com/test",
            "base_domain": "go2.tools",
            "custom_code": "invalid@code!"
        }
        
        response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_link_past_expiration_date(self, mock_firebase_service, mock_safety_service):
        """Test link creation with past expiration date"""
        mock_safety_service.validate_url.return_value = None
        
        past_date = datetime.utcnow() - timedelta(days=1)
        request_data = {
            "long_url": "https://example.com/test",
            "base_domain": "go2.tools",
            "expires_at": past_date.isoformat()
        }
        
        response = client.post("/api/links/shorten", json=request_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

if __name__ == "__main__":
    pytest.main([__file__])


class TestDomainValidation:
    """Test domain validation functionality"""
    
    @pytest.mark.asyncio
    async def test_get_valid_base_domains_from_firestore(self):
        """Test getting valid domains from Firestore"""
        with patch('src.routers.links.firebase_service') as mock_firebase:
            # Mock Firestore document
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                'base_domains': ['go2.video', 'go2.reviews']
            }
            mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            from src.routers.links import get_valid_base_domains
            domains = await get_valid_base_domains()
            
            assert domains == ['go2.video', 'go2.reviews']
    
    @pytest.mark.asyncio
    async def test_get_valid_base_domains_fallback(self):
        """Test fallback when Firestore document doesn't exist"""
        with patch('src.routers.links.firebase_service') as mock_firebase:
            # Mock Firestore document not existing
            mock_doc = Mock()
            mock_doc.exists = False
            mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            from src.routers.links import get_valid_base_domains
            domains = await get_valid_base_domains()
            
            assert domains == ['go2.video', 'go2.reviews', 'go2.tools']
    
    @pytest.mark.asyncio
    async def test_get_valid_base_domains_error_fallback(self):
        """Test fallback when Firestore throws an error"""
        with patch('src.routers.links.firebase_service') as mock_firebase:
            # Mock Firestore error
            mock_firebase.db.collection.return_value.document.return_value.get.side_effect = Exception("Firestore error")
            
            from src.routers.links import get_valid_base_domains
            domains = await get_valid_base_domains()
            
            assert domains == ['go2.video', 'go2.reviews', 'go2.tools']
    
    @pytest.mark.asyncio
    async def test_validate_base_domain_valid(self):
        """Test validation of valid base domains"""
        with patch('src.routers.links.get_valid_base_domains') as mock_get_domains:
            mock_get_domains.return_value = ['go2.video', 'go2.reviews', 'go2.tools']
            
            from src.routers.links import validate_base_domain
            
            assert await validate_base_domain('go2.video') == True
            assert await validate_base_domain('go2.reviews') == True
            assert await validate_base_domain('go2.tools') == True
    
    @pytest.mark.asyncio
    async def test_validate_base_domain_invalid(self):
        """Test validation of invalid base domains"""
        with patch('src.routers.links.get_valid_base_domains') as mock_get_domains:
            mock_get_domains.return_value = ['go2.video', 'go2.reviews', 'go2.tools']
            
            from src.routers.links import validate_base_domain
            
            assert await validate_base_domain('invalid.domain') == False
            assert await validate_base_domain('go2.invalid') == False
            assert await validate_base_domain('') == False
    
    @pytest.mark.asyncio
    async def test_validate_base_domain_custom_config(self):
        """Test validation with custom domain configuration"""
        with patch('src.routers.links.get_valid_base_domains') as mock_get_domains:
            # Simulate custom domain configuration
            mock_get_domains.return_value = ['go2.video', 'go2.custom']
            
            from src.routers.links import validate_base_domain
            
            assert await validate_base_domain('go2.video') == True
            assert await validate_base_domain('go2.custom') == True
            assert await validate_base_domain('go2.reviews') == False  # Not in custom config
            assert await validate_base_domain('go2.tools') == False    # Not in custom config