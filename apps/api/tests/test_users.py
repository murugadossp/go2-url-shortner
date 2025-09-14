import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from src.main import app
from src.models.user import UserProfileResponse, PlanType


class TestUsersRouter:
    
    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_token(self):
        """Mock Firebase user token"""
        return {
            'uid': 'test-user-123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
    
    @pytest.fixture
    def mock_user_profile(self):
        """Mock user profile response"""
        return UserProfileResponse(
            email='test@example.com',
            display_name='Test User',
            plan_type='free',
            custom_codes_used=2,
            custom_codes_remaining=3,
            custom_codes_reset_date=datetime.utcnow() + timedelta(days=20),
            created_at=datetime.utcnow() - timedelta(days=10),
            is_admin=False
        )
    
    @pytest.fixture
    def mock_usage_stats(self):
        """Mock usage statistics"""
        return {
            'total_links': 10,
            'custom_code_links': 2,
            'total_clicks': 150,
            'plan_type': 'free',
            'custom_codes_used': 2,
            'custom_codes_remaining': 3,
            'custom_codes_reset_date': (datetime.utcnow() + timedelta(days=20)).isoformat()
        }

    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_get_user_profile_success(self, mock_firebase, mock_user_service, client, mock_user_token, mock_user_profile):
        """Test successful user profile retrieval"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = mock_user_token
        
        # Mock user service
        mock_user_service.get_or_create_user = AsyncMock(return_value=Mock())
        mock_user_service.get_user_profile = AsyncMock(return_value=mock_user_profile)
        
        response = client.get(
            '/api/users/profile',
            headers={'Authorization': 'Bearer fake-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['email'] == 'test@example.com'
        assert data['plan_type'] == 'free'
        assert data['custom_codes_remaining'] == 3

    @patch('src.utils.auth.firebase_service')
    def test_get_user_profile_unauthorized(self, mock_firebase, client):
        """Test user profile retrieval without authentication"""
        response = client.get('/api/users/profile')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_get_user_profile_not_found(self, mock_firebase, mock_user_service, client, mock_user_token):
        """Test user profile retrieval for non-existent user"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = mock_user_token
        
        # Mock user service
        mock_user_service.get_or_create_user = AsyncMock(return_value=Mock())
        mock_user_service.get_user_profile = AsyncMock(return_value=None)
        
        response = client.get(
            '/api/users/profile',
            headers={'Authorization': 'Bearer fake-token'}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_update_user_profile_success(self, mock_firebase, mock_user_service, client, mock_user_token):
        """Test successful user profile update"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = mock_user_token
        
        # Mock user service
        mock_user_service.update_user_profile = AsyncMock(return_value=True)
        
        response = client.put(
            '/api/users/profile',
            headers={'Authorization': 'Bearer fake-token'},
            json={'display_name': 'Updated Name'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['message'] == 'Profile updated successfully'
        
        # Verify service was called with correct parameters
        mock_user_service.update_user_profile.assert_called_once_with('test-user-123', 'Updated Name')

    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_update_user_profile_failure(self, mock_firebase, mock_user_service, client, mock_user_token):
        """Test user profile update failure"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = mock_user_token
        
        # Mock user service failure
        mock_user_service.update_user_profile = AsyncMock(return_value=False)
        
        response = client.put(
            '/api/users/profile',
            headers={'Authorization': 'Bearer fake-token'},
            json={'display_name': 'Updated Name'}
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_get_user_usage_success(self, mock_firebase, mock_user_service, client, mock_user_token, mock_usage_stats):
        """Test successful user usage retrieval"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = mock_user_token
        
        # Mock user service
        mock_user_service.get_user_usage_stats = AsyncMock(return_value=mock_usage_stats)
        
        response = client.get(
            '/api/users/usage',
            headers={'Authorization': 'Bearer fake-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_links'] == 10
        assert data['custom_code_links'] == 2
        assert data['total_clicks'] == 150

    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_get_user_usage_not_found(self, mock_firebase, mock_user_service, client, mock_user_token):
        """Test user usage retrieval for non-existent user"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = mock_user_token
        
        # Mock user service
        mock_user_service.get_user_usage_stats = AsyncMock(return_value={})
        
        response = client.get(
            '/api/users/usage',
            headers={'Authorization': 'Bearer fake-token'}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_upgrade_plan_success(self, mock_firebase, mock_user_service, client, mock_user_token):
        """Test successful plan upgrade"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = mock_user_token
        
        # Mock user service
        mock_user_service.upgrade_user_plan = AsyncMock(return_value=True)
        
        response = client.post(
            '/api/users/upgrade',
            headers={'Authorization': 'Bearer fake-token'},
            json={'plan_type': 'paid'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'Plan upgraded to paid' in data['message']
        assert 'demo implementation' in data['note']
        
        # Verify service was called with correct parameters
        mock_user_service.upgrade_user_plan.assert_called_once_with('test-user-123', 'paid')

    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_upgrade_plan_failure(self, mock_firebase, mock_user_service, client, mock_user_token):
        """Test plan upgrade failure"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = mock_user_token
        
        # Mock user service failure
        mock_user_service.upgrade_user_plan = AsyncMock(return_value=False)
        
        response = client.post(
            '/api/users/upgrade',
            headers={'Authorization': 'Bearer fake-token'},
            json={'plan_type': 'paid'}
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_plan_limits(self, client):
        """Test getting plan limits (public endpoint)"""
        response = client.get('/api/users/limits')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'plans' in data
        assert 'free' in data['plans']
        assert 'paid' in data['plans']
        assert data['plans']['free']['custom_codes'] == 5
        assert data['plans']['paid']['custom_codes'] == 100

    def test_update_profile_validation(self, client):
        """Test profile update with invalid data"""
        response = client.put(
            '/api/users/profile',
            headers={'Authorization': 'Bearer fake-token'},
            json={'display_name': ''}  # Empty display name
        )
        
        # Should fail validation before reaching authentication
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_401_UNAUTHORIZED]

    def test_upgrade_plan_validation(self, client):
        """Test plan upgrade with invalid data"""
        response = client.post(
            '/api/users/upgrade',
            headers={'Authorization': 'Bearer fake-token'},
            json={'plan_type': 'invalid'}  # Invalid plan type
        )
        
        # Should fail validation before reaching authentication
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_401_UNAUTHORIZED]


class TestUserAuthenticationFlow:
    """Test authentication flow integration"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @patch('src.utils.auth.firebase_service')
    def test_authentication_required_endpoints(self, mock_firebase, client):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ('GET', '/api/users/profile'),
            ('PUT', '/api/users/profile'),
            ('GET', '/api/users/usage'),
            ('POST', '/api/users/upgrade'),
        ]
        
        for method, endpoint in protected_endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'PUT':
                response = client.put(endpoint, json={'display_name': 'Test'})
            elif method == 'POST':
                response = client.post(endpoint, json={'plan_type': 'paid'})
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('src.utils.auth.firebase_service')
    def test_invalid_token_handling(self, mock_firebase, client):
        """Test handling of invalid authentication tokens"""
        # Mock invalid token
        mock_firebase.verify_id_token.return_value = None
        
        response = client.get(
            '/api/users/profile',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_public_endpoints_no_auth(self, client):
        """Test that public endpoints don't require authentication"""
        response = client.get('/api/users/limits')
        assert response.status_code == status.HTTP_200_OK


class TestPlanLimitEnforcement:
    """Test plan limit enforcement in user operations"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_free_plan_limits_in_profile(self, mock_firebase, mock_user_service, client):
        """Test that free plan limits are correctly reflected in profile"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = {'uid': 'test-user', 'email': 'test@example.com'}
        
        # Mock user service with free plan at limit
        mock_profile = UserProfileResponse(
            email='test@example.com',
            display_name='Test User',
            plan_type='free',
            custom_codes_used=5,  # At limit
            custom_codes_remaining=0,
            custom_codes_reset_date=datetime.utcnow() + timedelta(days=20),
            created_at=datetime.utcnow() - timedelta(days=10),
            is_admin=False
        )
        
        mock_user_service.get_or_create_user = AsyncMock(return_value=Mock())
        mock_user_service.get_user_profile = AsyncMock(return_value=mock_profile)
        
        response = client.get(
            '/api/users/profile',
            headers={'Authorization': 'Bearer fake-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['custom_codes_remaining'] == 0
        assert data['plan_type'] == 'free'

    @patch('src.routers.users.user_service')
    @patch('src.utils.auth.firebase_service')
    def test_paid_plan_higher_limits(self, mock_firebase, mock_user_service, client):
        """Test that paid plan has higher limits"""
        # Mock authentication
        mock_firebase.verify_id_token.return_value = {'uid': 'test-user', 'email': 'test@example.com'}
        
        # Mock user service with paid plan
        mock_profile = UserProfileResponse(
            email='test@example.com',
            display_name='Test User',
            plan_type='paid',
            custom_codes_used=50,
            custom_codes_remaining=50,  # Higher limit
            custom_codes_reset_date=datetime.utcnow() + timedelta(days=20),
            created_at=datetime.utcnow() - timedelta(days=10),
            is_admin=False
        )
        
        mock_user_service.get_or_create_user = AsyncMock(return_value=Mock())
        mock_user_service.get_user_profile = AsyncMock(return_value=mock_profile)
        
        response = client.get(
            '/api/users/profile',
            headers={'Authorization': 'Bearer fake-token'}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['custom_codes_remaining'] == 50
        assert data['plan_type'] == 'paid'