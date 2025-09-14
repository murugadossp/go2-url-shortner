"""
Integration tests for complete user workflows
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

@pytest.mark.asyncio
class TestCompleteUserWorkflows:
    """Test complete user workflows from start to finish"""

    async def test_complete_link_creation_and_analytics_workflow(self, client: AsyncClient):
        """Test the complete workflow: create link -> click link -> view analytics"""
        
        # Mock Firebase services
        with patch('src.services.firebase_service.get_firestore_client') as mock_firestore, \
             patch('src.services.firebase_service.verify_firebase_token') as mock_verify, \
             patch('src.services.safety_service.SafetyService.validate_url') as mock_safety, \
             patch('src.services.qr_service.QRService.generate_qr') as mock_qr:
            
            # Setup mocks
            mock_db = MagicMock()
            mock_firestore.return_value = mock_db
            mock_verify.return_value = {
                'uid': 'test-user-123',
                'email': 'test@example.com'
            }
            mock_safety.return_value = {'is_safe': True, 'reasons': []}
            mock_qr.return_value = b'fake-qr-data'
            
            # Mock Firestore operations
            mock_doc_ref = MagicMock()
            mock_collection = MagicMock()
            mock_collection.document.return_value = mock_doc_ref
            mock_db.collection.return_value = mock_collection
            
            # Mock document get for collision check
            mock_doc_ref.get.return_value.exists = False
            
            # Step 1: Create a link
            link_data = {
                'long_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'base_domain': 'go2.video',
                'custom_code': 'rickroll'
            }
            
            response = await client.post(
                '/api/links/shorten',
                json=link_data,
                headers={'Authorization': 'Bearer fake-token'}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result['code'] == 'rickroll'
            assert result['short_url'] == 'https://go2.video/rickroll'
            
            # Verify Firestore set was called
            mock_doc_ref.set.assert_called_once()
            
            # Step 2: Simulate clicking the link (redirect)
            # Mock the link document exists for redirect
            mock_link_doc = MagicMock()
            mock_link_doc.exists = True
            mock_link_doc.to_dict.return_value = {
                'long_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'base_domain': 'go2.video',
                'owner_uid': 'test-user-123',
                'disabled': False,
                'expires_at': None,
                'password_hash': None,
                'created_at': datetime.now()
            }
            mock_doc_ref.get.return_value = mock_link_doc
            
            # Mock clicks subcollection
            mock_clicks_collection = MagicMock()
            mock_doc_ref.collection.return_value = mock_clicks_collection
            
            redirect_response = await client.get('/rickroll')
            assert redirect_response.status_code == 302
            assert redirect_response.headers['location'] == 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            
            # Verify click was logged
            mock_clicks_collection.add.assert_called_once()
            
            # Step 3: View analytics
            # Mock analytics data
            mock_clicks_query = MagicMock()
            mock_clicks_collection.stream.return_value = [
                MagicMock(to_dict=lambda: {
                    'ts': datetime.now(),
                    'location': {'country': 'US', 'city': 'New York'},
                    'device_type': 'desktop',
                    'referrer': 'google.com'
                })
            ]
            mock_clicks_collection.where.return_value = mock_clicks_query
            mock_clicks_query.stream.return_value = mock_clicks_collection.stream.return_value
            
            analytics_response = await client.get(
                '/api/stats/rickroll',
                headers={'Authorization': 'Bearer fake-token'}
            )
            
            assert analytics_response.status_code == 200
            analytics_data = analytics_response.json()
            assert 'total_clicks' in analytics_data
            assert 'clicks_by_day' in analytics_data

    async def test_password_protected_link_workflow(self, client: AsyncClient):
        """Test creating and accessing a password-protected link"""
        
        with patch('src.services.firebase_service.get_firestore_client') as mock_firestore, \
             patch('src.services.firebase_service.verify_firebase_token') as mock_verify, \
             patch('src.services.safety_service.SafetyService.validate_url') as mock_safety, \
             patch('passlib.context.CryptContext.hash') as mock_hash, \
             patch('passlib.context.CryptContext.verify') as mock_verify_password:
            
            # Setup mocks
            mock_db = MagicMock()
            mock_firestore.return_value = mock_db
            mock_verify.return_value = {
                'uid': 'test-user-123',
                'email': 'test@example.com'
            }
            mock_safety.return_value = {'is_safe': True, 'reasons': []}
            mock_hash.return_value = 'hashed_password'
            mock_verify_password.return_value = True
            
            # Mock Firestore operations
            mock_doc_ref = MagicMock()
            mock_collection = MagicMock()
            mock_collection.document.return_value = mock_doc_ref
            mock_db.collection.return_value = mock_collection
            mock_doc_ref.get.return_value.exists = False
            
            # Step 1: Create password-protected link
            link_data = {
                'long_url': 'https://secret-document.com',
                'base_domain': 'go2.tools',
                'password': 'secretpass123'
            }
            
            response = await client.post(
                '/api/links/shorten',
                json=link_data,
                headers={'Authorization': 'Bearer fake-token'}
            )
            
            assert response.status_code == 200
            result = response.json()
            code = result['code']
            
            # Step 2: Try to access without password (should show password form)
            mock_link_doc = MagicMock()
            mock_link_doc.exists = True
            mock_link_doc.to_dict.return_value = {
                'long_url': 'https://secret-document.com',
                'base_domain': 'go2.tools',
                'owner_uid': 'test-user-123',
                'disabled': False,
                'expires_at': None,
                'password_hash': 'hashed_password',
                'created_at': datetime.now()
            }
            mock_doc_ref.get.return_value = mock_link_doc
            
            redirect_response = await client.get(f'/{code}')
            assert redirect_response.status_code == 200  # Should show password form
            
            # Step 3: Access with correct password
            password_response = await client.post(
                f'/{code}',
                data={'password': 'secretpass123'}
            )
            assert password_response.status_code == 302
            assert password_response.headers['location'] == 'https://secret-document.com'

    async def test_admin_workflow(self, client: AsyncClient):
        """Test admin operations workflow"""
        
        with patch('src.services.firebase_service.get_firestore_client') as mock_firestore, \
             patch('src.services.firebase_service.verify_firebase_token') as mock_verify:
            
            # Setup admin user
            mock_db = MagicMock()
            mock_firestore.return_value = mock_db
            mock_verify.return_value = {
                'uid': 'admin-user-123',
                'email': 'admin@example.com',
                'admin': True
            }
            
            # Mock Firestore operations for admin queries
            mock_collection = MagicMock()
            mock_db.collection.return_value = mock_collection
            
            # Mock links query
            mock_links_query = MagicMock()
            mock_collection.stream.return_value = [
                MagicMock(id='link1', to_dict=lambda: {
                    'long_url': 'https://example1.com',
                    'owner_uid': 'user1',
                    'disabled': False,
                    'created_at': datetime.now()
                }),
                MagicMock(id='link2', to_dict=lambda: {
                    'long_url': 'https://example2.com',
                    'owner_uid': 'user2',
                    'disabled': False,
                    'created_at': datetime.now()
                })
            ]
            
            # Step 1: Get all links (admin view)
            response = await client.get(
                '/api/admin/links',
                headers={'Authorization': 'Bearer admin-token'}
            )
            
            assert response.status_code == 200
            links = response.json()
            assert len(links) >= 0  # Should return links list
            
            # Step 2: Disable a link
            mock_doc_ref = MagicMock()
            mock_collection.document.return_value = mock_doc_ref
            
            disable_response = await client.put(
                '/api/admin/links/link1',
                json={'disabled': True},
                headers={'Authorization': 'Bearer admin-token'}
            )
            
            assert disable_response.status_code == 200
            mock_doc_ref.update.assert_called_once()

    async def test_daily_report_workflow(self, client: AsyncClient):
        """Test daily report generation workflow"""
        
        with patch('src.services.firebase_service.get_firestore_client') as mock_firestore, \
             patch('src.services.daily_report_service.DailyReportService.generate_report') as mock_report, \
             patch('sendgrid.SendGridAPIClient.send') as mock_sendgrid:
            
            mock_db = MagicMock()
            mock_firestore.return_value = mock_db
            
            # Mock report data
            mock_report.return_value = {
                'date': '2024-01-01',
                'total_clicks': 150,
                'total_links': 25,
                'top_links': [
                    {'code': 'abc123', 'clicks': 50, 'url': 'https://example.com'}
                ],
                'geographic_breakdown': [
                    {'country': 'US', 'clicks': 100}
                ]
            }
            
            # Mock SendGrid success
            mock_sendgrid.return_value.status_code = 202
            
            # Generate daily report
            response = await client.post(
                '/api/hooks/send_daily_report',
                json={
                    'date': '2024-01-01',
                    'domain': 'go2.video',
                    'email': 'reports@example.com'
                }
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result['success'] is True
            
            # Verify report was generated and email sent
            mock_report.assert_called_once()
            mock_sendgrid.assert_called_once()

    async def test_safety_validation_workflow(self, client: AsyncClient):
        """Test safety validation preventing malicious links"""
        
        with patch('src.services.firebase_service.get_firestore_client') as mock_firestore, \
             patch('src.services.firebase_service.verify_firebase_token') as mock_verify, \
             patch('src.services.safety_service.SafetyService.validate_url') as mock_safety:
            
            mock_db = MagicMock()
            mock_firestore.return_value = mock_db
            mock_verify.return_value = {
                'uid': 'test-user-123',
                'email': 'test@example.com'
            }
            
            # Mock safety service to reject URL
            mock_safety.return_value = {
                'is_safe': False,
                'reasons': ['Domain is blacklisted', 'Contains adult content']
            }
            
            # Try to create link with unsafe URL
            link_data = {
                'long_url': 'https://malicious-site.com/phishing',
                'base_domain': 'go2.tools'
            }
            
            response = await client.post(
                '/api/links/shorten',
                json=link_data,
                headers={'Authorization': 'Bearer fake-token'}
            )
            
            assert response.status_code == 403
            error = response.json()
            assert error['error']['code'] == 'SAFETY_VIOLATION'
            assert 'blacklisted' in error['error']['message'].lower()

    async def test_plan_limits_workflow(self, client: AsyncClient):
        """Test plan limits enforcement workflow"""
        
        with patch('src.services.firebase_service.get_firestore_client') as mock_firestore, \
             patch('src.services.firebase_service.verify_firebase_token') as mock_verify, \
             patch('src.services.safety_service.SafetyService.validate_url') as mock_safety, \
             patch('src.services.user_service.UserService.get_user_custom_code_usage') as mock_usage:
            
            mock_db = MagicMock()
            mock_firestore.return_value = mock_db
            mock_verify.return_value = {
                'uid': 'free-user-123',
                'email': 'free@example.com'
            }
            mock_safety.return_value = {'is_safe': True, 'reasons': []}
            
            # Mock user has reached free plan limit (5 custom codes)
            mock_usage.return_value = 5
            
            # Try to create 6th custom code link
            link_data = {
                'long_url': 'https://example.com',
                'base_domain': 'go2.tools',
                'custom_code': 'sixth-code'
            }
            
            response = await client.post(
                '/api/links/shorten',
                json=link_data,
                headers={'Authorization': 'Bearer fake-token'}
            )
            
            assert response.status_code == 403
            error = response.json()
            assert error['error']['code'] == 'PLAN_LIMIT_EXCEEDED'

    async def test_qr_code_workflow(self, client: AsyncClient):
        """Test QR code generation and caching workflow"""
        
        with patch('src.services.firebase_service.get_firestore_client') as mock_firestore, \
             patch('src.services.qr_service.QRService.get_cached_qr') as mock_cached, \
             patch('src.services.qr_service.QRService.generate_qr') as mock_generate, \
             patch('src.services.qr_service.QRService.cache_qr') as mock_cache:
            
            mock_db = MagicMock()
            mock_firestore.return_value = mock_db
            
            # Mock link exists
            mock_doc_ref = MagicMock()
            mock_collection = MagicMock()
            mock_collection.document.return_value = mock_doc_ref
            mock_db.collection.return_value = mock_collection
            
            mock_link_doc = MagicMock()
            mock_link_doc.exists = True
            mock_doc_ref.get.return_value = mock_link_doc
            
            # Test cache miss -> generate -> cache
            mock_cached.return_value = None  # Cache miss
            mock_generate.return_value = b'fake-qr-png-data'
            
            response = await client.get('/api/qr/test123')
            
            assert response.status_code == 200
            assert response.headers['content-type'] == 'image/png'
            
            # Verify QR was generated and cached
            mock_generate.assert_called_once()
            mock_cache.assert_called_once()
            
            # Test cache hit
            mock_cached.return_value = 'https://storage.googleapis.com/qr/test123.png'
            
            response2 = await client.get('/api/qr/test123')
            assert response2.status_code == 302  # Redirect to cached version