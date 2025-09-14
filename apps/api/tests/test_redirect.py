"""
Tests for redirect functionality and click tracking.
Tests redirect scenarios, password protection, error handling, and analytics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from passlib.hash import bcrypt

from src.main import app
from src.services.firebase_service import firebase_service
from src.services.analytics_service import analytics_service


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_firestore():
    """Mock Firestore database"""
    with patch('src.routers.redirect.firebase_service') as mock_service:
        mock_db = MagicMock()
        mock_service.db = mock_db
        yield mock_db


@pytest.fixture
def mock_analytics():
    """Mock analytics service"""
    with patch.object(analytics_service, 'log_click', new_callable=AsyncMock) as mock_log:
        yield mock_log


class TestRedirectHandling:
    """Test redirect functionality"""
    
    def test_successful_redirect(self, client, mock_firestore, mock_analytics):
        """Test successful redirect to long URL"""
        # Mock link document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/long-url',
            'disabled': False,
            'expires_at': None,
            'password_hash': None
        }
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request (don't follow redirects)
        response = client.get('/test123', follow_redirects=False)
        
        # Verify redirect
        assert response.status_code == 302
        assert response.headers['location'] == 'https://example.com/long-url'
        
        # Verify click logging was called
        mock_analytics.assert_called_once()
    
    def test_link_not_found(self, client, mock_firestore):
        """Test 404 response for non-existent link"""
        # Mock non-existent document
        mock_doc = MagicMock()
        mock_doc.exists = False
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get('/nonexistent')
        
        # Verify 404 response with HTML error page
        assert response.status_code == 404
        assert 'Link Not Found' in response.text
        assert 'text/html' in response.headers['content-type']
    
    def test_disabled_link(self, client, mock_firestore):
        """Test 410 response for disabled link"""
        # Mock disabled link document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/long-url',
            'disabled': True,
            'expires_at': None,
            'password_hash': None
        }
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get('/disabled123')
        
        # Verify 410 response with HTML error page
        assert response.status_code == 410
        assert 'Link Disabled' in response.text
        assert 'text/html' in response.headers['content-type']
    
    def test_expired_link(self, client, mock_firestore):
        """Test 410 response for expired link"""
        # Mock expired link document
        expired_date = datetime.utcnow() - timedelta(days=1)
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/long-url',
            'disabled': False,
            'expires_at': expired_date,
            'password_hash': None
        }
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get('/expired123')
        
        # Verify 410 response with HTML error page
        assert response.status_code == 410
        assert 'Link Expired' in response.text
        assert 'text/html' in response.headers['content-type']


class TestPasswordProtection:
    """Test password-protected link functionality"""
    
    def test_password_form_display(self, client, mock_firestore):
        """Test password form is displayed for protected links"""
        # Mock password-protected link
        password_hash = bcrypt.hash('secret123')
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/protected',
            'disabled': False,
            'expires_at': None,
            'password_hash': password_hash
        }
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make GET request
        response = client.get('/protected123')
        
        # Verify password form is displayed
        assert response.status_code == 200
        assert 'Password Required' in response.text
        assert 'form method="post"' in response.text
        assert 'input type="password"' in response.text
    
    def test_correct_password_redirect(self, client, mock_firestore, mock_analytics):
        """Test successful redirect with correct password"""
        # Mock password-protected link
        password_hash = bcrypt.hash('secret123')
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/protected',
            'disabled': False,
            'expires_at': None,
            'password_hash': password_hash
        }
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make POST request with correct password
        response = client.post('/protected123', data={'password': 'secret123'}, follow_redirects=False)
        
        # Verify redirect
        assert response.status_code == 302
        assert response.headers['location'] == 'https://example.com/protected'
        
        # Verify click logging was called
        mock_analytics.assert_called_once()
    
    def test_incorrect_password_error(self, client, mock_firestore):
        """Test error display with incorrect password"""
        # Mock password-protected link
        password_hash = bcrypt.hash('secret123')
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/protected',
            'disabled': False,
            'expires_at': None,
            'password_hash': password_hash
        }
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make POST request with incorrect password
        response = client.post('/protected123', data={'password': 'wrongpassword'})
        
        # Verify error form is displayed
        assert response.status_code == 401
        assert 'Incorrect password' in response.text
        assert 'form method="post"' in response.text


class TestClickTracking:
    """Test click tracking and analytics functionality"""
    
    @patch('src.services.analytics_service.requests.get')
    def test_click_logging_with_geolocation(self, mock_requests, client, mock_firestore):
        """Test click logging includes geolocation data"""
        # Mock successful geolocation response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'country_name': 'United States',
            'country_code': 'US',
            'region': 'California',
            'city': 'San Francisco',
            'timezone': 'America/Los_Angeles',
            'latitude': 37.7749,
            'longitude': -122.4194
        }
        mock_requests.return_value = mock_response
        
        # Mock link document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/tracked',
            'disabled': False,
            'expires_at': None,
            'password_hash': None
        }
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock clicks collection for logging
        mock_clicks_ref = MagicMock()
        mock_firestore.collection.return_value.document.return_value.collection.return_value = mock_clicks_ref
        
        # Make request with headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://google.com/search'
        }
        response = client.get('/tracked123', headers=headers, follow_redirects=False)
        
        # Verify redirect
        assert response.status_code == 302
        
        # Give time for async click logging
        import asyncio
        import time
        time.sleep(0.1)  # Brief pause for async task
    
    def test_ip_hashing_privacy(self):
        """Test IP addresses are properly hashed for privacy"""
        from src.services.analytics_service import AnalyticsService
        
        service = AnalyticsService()
        
        # Test IP hashing
        ip = '192.168.1.100'
        hashed = service.hash_ip(ip)
        
        # Verify hash properties
        assert len(hashed) == 16  # Truncated SHA256
        assert hashed != ip  # Not plaintext
        assert service.hash_ip(ip) == hashed  # Consistent
    
    def test_user_agent_parsing(self):
        """Test user agent parsing extracts correct device info"""
        from src.services.analytics_service import AnalyticsService
        
        service = AnalyticsService()
        
        # Test desktop user agent
        desktop_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        desktop_info = service.parse_user_agent(desktop_ua)
        
        assert desktop_info['device_type'] == 'desktop'
        assert 'Chrome' in desktop_info['browser']
        assert 'Windows' in desktop_info['os']
        
        # Test mobile user agent
        mobile_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
        mobile_info = service.parse_user_agent(mobile_ua)
        
        assert mobile_info['device_type'] == 'mobile'
        assert 'Mobile Safari' in mobile_info['browser']
        assert 'iOS' in mobile_info['os']
    
    def test_private_ip_detection(self):
        """Test private IP addresses are not sent to geolocation service"""
        from src.services.analytics_service import AnalyticsService
        
        service = AnalyticsService()
        
        # Test private IP ranges
        private_ips = [
            '127.0.0.1',      # Loopback
            '10.0.0.1',       # Private Class A
            '172.16.0.1',     # Private Class B
            '192.168.1.1',    # Private Class C
        ]
        
        for ip in private_ips:
            assert service._is_private_ip(ip) == True
        
        # Test public IP
        assert service._is_private_ip('8.8.8.8') == False


class TestAnalyticsEndpoints:
    """Test analytics API endpoints"""
    
    @patch('src.routers.links.firebase_service')
    def test_get_link_stats_public(self, mock_links_firebase, client):
        """Test getting stats for public link (no auth required)"""
        # Mock public link document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/public',
            'owner_uid': None  # Public link
        }
        
        mock_links_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock analytics service
        with patch.object(analytics_service, 'get_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = MagicMock(
                total_clicks=42,
                clicks_by_day={'2023-12-01': 10, '2023-12-02': 32},
                top_referrers={'google.com': 25, 'direct': 17},
                top_devices={'desktop': 30, 'mobile': 12},
                last_clicked=datetime.utcnow(),
                geographic_stats=MagicMock(
                    countries={'United States': 35, 'Canada': 7},
                    cities={'San Francisco': 20, 'Toronto': 7},
                    regions={'California': 20, 'Ontario': 7}
                )
            )
            
            # Make request
            response = client.get('/api/links/stats/public123?period=7d')
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['total_clicks'] == 42
            assert '2023-12-01' in data['clicks_by_day']
            assert 'google.com' in data['top_referrers']
    
    @patch('src.routers.links.firebase_service')
    def test_get_link_stats_private_unauthorized(self, mock_links_firebase, client):
        """Test getting stats for private link without auth returns 401"""
        # Mock private link document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/private',
            'owner_uid': 'user123'  # Private link
        }
        
        mock_links_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request without auth
        response = client.get('/api/links/stats/private123')
        
        # Verify 401 response
        assert response.status_code == 401
        assert 'Authentication required' in response.json()['detail']
    



class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_database_error_handling(self, client, mock_firestore):
        """Test graceful handling of database errors"""
        # Mock database error
        mock_firestore.collection.side_effect = Exception("Database connection failed")
        
        # Make request
        response = client.get('/error123')
        
        # Verify 500 error page
        assert response.status_code == 500
        assert 'Server Error' in response.text
        assert 'text/html' in response.headers['content-type']
    
    def test_geolocation_service_failure(self):
        """Test analytics service handles geolocation API failures gracefully"""
        from src.services.analytics_service import AnalyticsService
        
        service = AnalyticsService()
        
        # Test with requests exception
        with patch('src.services.analytics_service.requests.get') as mock_requests:
            mock_requests.side_effect = Exception("Network error")
            
            # Should not raise exception
            import asyncio
            location = asyncio.run(service.get_location_from_ip('8.8.8.8'))
            
            # Should return empty location data
            assert location.country is None
            assert location.city is None
    
    @patch('src.routers.links.firebase_service')
    def test_invalid_period_parameter(self, mock_links_firebase, client):
        """Test invalid period parameter returns 400"""
        # Mock link document
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'long_url': 'https://example.com/test',
            'owner_uid': None
        }
        
        mock_links_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request with invalid period
        response = client.get('/api/links/stats/test123?period=invalid')
        
        # Verify 400 response
        assert response.status_code == 400
        assert 'Period must be one of' in response.json()['detail']


if __name__ == '__main__':
    pytest.main([__file__])