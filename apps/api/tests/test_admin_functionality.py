"""
Tests for admin functionality including user management, link management, and audit logging.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.main import app
from src.services.user_service import user_service
from src.services.firebase_service import firebase_service


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_admin_user():
    return {
        'uid': 'admin123',
        'email': 'admin@example.com',
        'name': 'Admin User',
        'admin': True
    }


@pytest.fixture
def mock_regular_user():
    return {
        'uid': 'user123',
        'email': 'user@example.com',
        'name': 'Regular User',
        'admin': False
    }


@pytest.fixture
def mock_firebase_token():
    with patch('src.utils.auth.firebase_service.verify_id_token') as mock_verify:
        yield mock_verify


class TestAdminAuthentication:
    """Test admin authentication and authorization"""
    
    def test_admin_required_decorator_allows_admin(self, client, mock_firebase_token, mock_admin_user):
        """Test that admin-only endpoints allow admin users"""
        mock_firebase_token.return_value = mock_admin_user
        
        with patch('src.services.user_service.user_service.get_system_stats') as mock_stats:
            mock_stats.return_value = {
                'users': {'total': 10, 'free': 8, 'paid': 2, 'admin': 1, 'recent_signups': 2},
                'links': {'total': 50, 'custom_codes': 10, 'disabled': 2, 'recent_created': 5},
                'engagement': {'total_clicks': 1000, 'avg_clicks_per_link': 20.0},
                'last_updated': datetime.utcnow().isoformat()
            }
            
            response = client.get(
                "/api/users/admin/stats/overview",
                headers={"Authorization": "Bearer valid_admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert 'users' in data
            assert 'links' in data
            assert 'engagement' in data
    
    def test_admin_required_decorator_blocks_regular_user(self, client, mock_firebase_token, mock_regular_user):
        """Test that admin-only endpoints block regular users"""
        mock_firebase_token.return_value = mock_regular_user
        
        response = client.get(
            "/api/users/admin/stats/overview",
            headers={"Authorization": "Bearer valid_user_token"}
        )
        
        assert response.status_code == 403
        assert "Admin privileges required" in response.json()['detail']
    
    def test_admin_required_decorator_blocks_unauthenticated(self, client):
        """Test that admin-only endpoints block unauthenticated requests"""
        response = client.get("/api/users/admin/stats/overview")
        
        assert response.status_code == 401


class TestAdminUserManagement:
    """Test admin user management functionality"""
    
    def test_list_all_users(self, client, mock_firebase_token, mock_admin_user):
        """Test listing all users"""
        mock_firebase_token.return_value = mock_admin_user
        
        mock_users = [
            {
                'email': 'user1@example.com',
                'display_name': 'User One',
                'plan_type': 'free',
                'custom_codes_used': 2,
                'custom_codes_remaining': 3,
                'custom_codes_reset_date': datetime.utcnow() + timedelta(days=20),
                'created_at': datetime.utcnow() - timedelta(days=10),
                'is_admin': False
            },
            {
                'email': 'user2@example.com',
                'display_name': 'User Two',
                'plan_type': 'paid',
                'custom_codes_used': 15,
                'custom_codes_remaining': 85,
                'custom_codes_reset_date': datetime.utcnow() + timedelta(days=25),
                'created_at': datetime.utcnow() - timedelta(days=5),
                'is_admin': False
            }
        ]
        
        with patch('src.services.user_service.user_service.list_all_users') as mock_list:
            mock_list.return_value = mock_users
            
            response = client.get(
                "/api/users/admin/all",
                headers={"Authorization": "Bearer valid_admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]['email'] == 'user1@example.com'
            assert data[1]['plan_type'] == 'paid'
    
    def test_get_user_by_id(self, client, mock_firebase_token, mock_admin_user):
        """Test getting user by ID"""
        mock_firebase_token.return_value = mock_admin_user
        
        mock_user = {
            'email': 'user@example.com',
            'display_name': 'Test User',
            'plan_type': 'free',
            'custom_codes_used': 1,
            'custom_codes_remaining': 4,
            'custom_codes_reset_date': datetime.utcnow() + timedelta(days=20),
            'created_at': datetime.utcnow() - timedelta(days=5),
            'is_admin': False
        }
        
        with patch('src.services.user_service.user_service.get_user_profile') as mock_get:
            mock_get.return_value = mock_user
            
            response = client.get(
                "/api/users/admin/user123",
                headers={"Authorization": "Bearer valid_admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['email'] == 'user@example.com'
            assert data['plan_type'] == 'free'
    
    def test_update_user_plan(self, client, mock_firebase_token, mock_admin_user):
        """Test updating user plan"""
        mock_firebase_token.return_value = mock_admin_user
        
        with patch('src.services.user_service.user_service.upgrade_user_plan') as mock_upgrade, \
             patch('src.services.user_service.user_service.log_admin_action') as mock_log:
            mock_upgrade.return_value = True
            
            response = client.put(
                "/api/users/admin/user123/plan",
                headers={"Authorization": "Bearer valid_admin_token"},
                json={"plan_type": "paid"}
            )
            
            assert response.status_code == 200
            assert "User plan updated to paid" in response.json()['message']
            mock_upgrade.assert_called_once_with('user123', 'paid')
            mock_log.assert_called_once()
    
    def test_toggle_admin_status(self, client, mock_firebase_token, mock_admin_user):
        """Test toggling admin status"""
        mock_firebase_token.return_value = mock_admin_user
        
        with patch('src.services.user_service.user_service.set_admin_status') as mock_set, \
             patch('src.services.user_service.user_service.log_admin_action') as mock_log:
            mock_set.return_value = True
            
            response = client.put(
                "/api/users/admin/user123/admin-status",
                headers={"Authorization": "Bearer valid_admin_token"},
                params={"is_admin": True}
            )
            
            assert response.status_code == 200
            assert "Admin status granted" in response.json()['message']
            mock_set.assert_called_once_with('user123', True)
            mock_log.assert_called_once()


class TestAdminLinkManagement:
    """Test admin link management functionality"""
    
    def test_bulk_disable_links(self, client, mock_firebase_token, mock_admin_user):
        """Test bulk disabling links"""
        mock_firebase_token.return_value = mock_admin_user
        
        with patch('src.services.firebase_service.firebase_service.db') as mock_db, \
             patch('src.services.user_service.user_service.log_admin_action') as mock_log:
            
            # Mock Firestore operations
            mock_collection = Mock()
            mock_db.collection.return_value = mock_collection
            
            mock_doc_ref = Mock()
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc_ref.get.return_value = mock_doc
            mock_collection.document.return_value = mock_doc_ref
            
            codes = ['abc123', 'def456', 'ghi789']
            
            response = client.post(
                "/api/links/admin/bulk-disable",
                headers={"Authorization": "Bearer valid_admin_token"},
                json=codes
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['disabled_count'] == 3
            assert len(data['errors']) == 0
            mock_log.assert_called_once()
    
    def test_bulk_delete_links(self, client, mock_firebase_token, mock_admin_user):
        """Test bulk deleting links"""
        mock_firebase_token.return_value = mock_admin_user
        
        with patch('src.services.firebase_service.firebase_service.db') as mock_db, \
             patch('src.services.user_service.user_service.log_admin_action') as mock_log:
            
            # Mock Firestore operations
            mock_collection = Mock()
            mock_db.collection.return_value = mock_collection
            
            mock_doc_ref = Mock()
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc_ref.get.return_value = mock_doc
            
            # Mock clicks subcollection
            mock_clicks_collection = Mock()
            mock_doc_ref.collection.return_value = mock_clicks_collection
            mock_clicks_collection.get.return_value = []  # No clicks
            
            mock_collection.document.return_value = mock_doc_ref
            
            codes = ['abc123', 'def456']
            
            response = client.post(
                "/api/links/admin/bulk-delete",
                headers={"Authorization": "Bearer valid_admin_token"},
                json=codes
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['deleted_count'] == 2
            assert len(data['errors']) == 0
            mock_log.assert_called_once()
    
    def test_bulk_update_expiry(self, client, mock_firebase_token, mock_admin_user):
        """Test bulk updating link expiry"""
        mock_firebase_token.return_value = mock_admin_user
        
        with patch('src.services.firebase_service.firebase_service.db') as mock_db, \
             patch('src.services.user_service.user_service.log_admin_action') as mock_log:
            
            # Mock Firestore operations
            mock_collection = Mock()
            mock_db.collection.return_value = mock_collection
            
            mock_doc_ref = Mock()
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc_ref.get.return_value = mock_doc
            mock_collection.document.return_value = mock_doc_ref
            
            codes = ['abc123', 'def456']
            expiry_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
            
            response = client.post(
                "/api/links/admin/bulk-update-expiry",
                headers={"Authorization": "Bearer valid_admin_token"},
                json={
                    "codes": codes,
                    "expires_at": expiry_date
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['updated_count'] == 2
            assert len(data['errors']) == 0
            mock_log.assert_called_once()


class TestAdminAuditLog:
    """Test admin audit logging functionality"""
    
    def test_get_audit_log(self, client, mock_firebase_token, mock_admin_user):
        """Test retrieving audit log"""
        mock_firebase_token.return_value = mock_admin_user
        
        mock_entries = [
            {
                'id': 'entry1',
                'admin_uid': 'admin123',
                'action': 'update_user_plan',
                'target_uid': 'user123',
                'details': {'new_plan': 'paid'},
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': '192.168.1.1'
            },
            {
                'id': 'entry2',
                'admin_uid': 'admin123',
                'action': 'bulk_disable_links',
                'details': {'codes': ['abc123', 'def456'], 'disabled_count': 2, 'errors': []},
                'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                'ip_address': '192.168.1.1'
            }
        ]
        
        with patch('src.services.user_service.user_service.get_audit_log') as mock_get:
            mock_get.return_value = mock_entries
            
            response = client.get(
                "/api/users/admin/audit-log",
                headers={"Authorization": "Bearer valid_admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]['action'] == 'update_user_plan'
            assert data[1]['action'] == 'bulk_disable_links'
    
    def test_log_admin_action(self):
        """Test logging admin actions"""
        with patch('src.services.firebase_service.firebase_service.db') as mock_db:
            mock_collection = Mock()
            mock_db.collection.return_value = mock_collection
            
            # Test the log_admin_action method directly
            import asyncio
            
            async def test_log():
                await user_service.log_admin_action(
                    admin_uid='admin123',
                    action='test_action',
                    target_uid='user123',
                    details={'test': 'data'}
                )
            
            asyncio.run(test_log())
            
            mock_collection.add.assert_called_once()
            call_args = mock_collection.add.call_args[0][0]
            assert call_args['admin_uid'] == 'admin123'
            assert call_args['action'] == 'test_action'
            assert call_args['target_uid'] == 'user123'
            assert call_args['details'] == {'test': 'data'}


class TestAdminSystemStats:
    """Test admin system statistics functionality"""
    
    def test_get_system_stats(self, client, mock_firebase_token, mock_admin_user):
        """Test getting system statistics"""
        mock_firebase_token.return_value = mock_admin_user
        
        mock_stats = {
            'users': {
                'total': 100,
                'free': 80,
                'paid': 20,
                'admin': 3,
                'recent_signups': 15
            },
            'links': {
                'total': 500,
                'custom_codes': 75,
                'disabled': 10,
                'recent_created': 50
            },
            'engagement': {
                'total_clicks': 10000,
                'avg_clicks_per_link': 20.0
            },
            'last_updated': datetime.utcnow().isoformat()
        }
        
        with patch('src.services.user_service.user_service.get_system_stats') as mock_get:
            mock_get.return_value = mock_stats
            
            response = client.get(
                "/api/users/admin/stats/overview",
                headers={"Authorization": "Bearer valid_admin_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['users']['total'] == 100
            assert data['links']['total'] == 500
            assert data['engagement']['total_clicks'] == 10000
            assert 'last_updated' in data


class TestAdminErrorHandling:
    """Test error handling in admin functionality"""
    
    def test_admin_action_with_service_error(self, client, mock_firebase_token, mock_admin_user):
        """Test admin action when service fails"""
        mock_firebase_token.return_value = mock_admin_user
        
        with patch('src.services.user_service.user_service.upgrade_user_plan') as mock_upgrade:
            mock_upgrade.return_value = False  # Service failure
            
            response = client.put(
                "/api/users/admin/user123/plan",
                headers={"Authorization": "Bearer valid_admin_token"},
                json={"plan_type": "paid"}
            )
            
            assert response.status_code == 500
            assert "Failed to update user plan" in response.json()['detail']
    
    def test_bulk_operation_with_partial_failures(self, client, mock_firebase_token, mock_admin_user):
        """Test bulk operation with some failures"""
        mock_firebase_token.return_value = mock_admin_user
        
        with patch('src.services.firebase_service.firebase_service.db') as mock_db, \
             patch('src.services.user_service.user_service.log_admin_action') as mock_log:
            
            # Mock Firestore operations with mixed results
            mock_collection = Mock()
            mock_db.collection.return_value = mock_collection
            
            def mock_document(code):
                mock_doc_ref = Mock()
                mock_doc = Mock()
                # First link exists, second doesn't
                mock_doc.exists = code == 'abc123'
                mock_doc_ref.get.return_value = mock_doc
                return mock_doc_ref
            
            mock_collection.document.side_effect = mock_document
            
            codes = ['abc123', 'nonexistent']
            
            response = client.post(
                "/api/links/admin/bulk-disable",
                headers={"Authorization": "Bearer valid_admin_token"},
                json=codes
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['disabled_count'] == 1
            assert len(data['errors']) == 1
            assert 'nonexistent' in data['errors'][0]


if __name__ == "__main__":
    pytest.main([__file__])