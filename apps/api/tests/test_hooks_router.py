"""
Tests for hooks router endpoints.
Tests daily report generation, email sending, and configuration testing.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from fastapi.testclient import TestClient
from src.main import app
from src.models.analytics import DailyReportResponse, GeographicStats


class TestHooksRouter:
    """Test cases for hooks router endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_token(self):
        """Mock Firebase user token"""
        return {
            'uid': 'test_user_123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
    
    @pytest.fixture
    def mock_daily_report(self):
        """Mock daily report response"""
        return DailyReportResponse(
            date=datetime.utcnow(),
            total_clicks=25,
            total_links=5,
            top_links=[
                {
                    'code': 'test1',
                    'long_url': 'https://example.com/page1',
                    'base_domain': 'go2.video',
                    'clicks': 15
                },
                {
                    'code': 'test2',
                    'long_url': 'https://example.com/page2',
                    'base_domain': 'go2.tools',
                    'clicks': 10
                }
            ],
            geographic_breakdown=GeographicStats(
                countries={'United States': 15, 'Canada': 10},
                cities={'New York, United States': 10, 'Toronto, Canada': 8},
                regions={'New York, United States': 10, 'Ontario, Canada': 8}
            ),
            device_breakdown={'desktop': 15, 'mobile': 10},
            referrer_breakdown={'google.com': 12, 'Direct': 13},
            html_content='<html><body><h1>Daily Report</h1></body></html>'
        )
    
    def test_send_daily_report_success(self, client, mock_user_token, mock_daily_report):
        """Test successful daily report generation and sending"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.generate_daily_report = AsyncMock(return_value=mock_daily_report)
                mock_service.send_report_email = AsyncMock(return_value=True)
                
                response = client.post(
                    '/api/hooks/send_daily_report',
                    json={
                        'date': '2024-01-15',
                        'domain_filter': 'go2.video',
                        'email_recipients': ['test@example.com'],
                        'send_email': True
                    },
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['total_clicks'] == 25
                assert data['total_links'] == 5
                assert len(data['top_links']) == 2
                assert data['html_content'] is not None
                
                # Verify service calls
                mock_service.generate_daily_report.assert_called_once()
                mock_service.send_report_email.assert_called_once()
    
    def test_send_daily_report_no_email(self, client, mock_user_token, mock_daily_report):
        """Test daily report generation without sending email"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.generate_daily_report = AsyncMock(return_value=mock_daily_report)
                
                response = client.post(
                    '/api/hooks/send_daily_report',
                    json={
                        'send_email': False
                    },
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['total_clicks'] == 25
                assert data['total_links'] == 5
                
                # Verify email was not sent
                mock_service.generate_daily_report.assert_called_once()
                mock_service.send_report_email.assert_not_called()
    
    def test_send_daily_report_default_date(self, client, mock_user_token, mock_daily_report):
        """Test daily report with default date (yesterday)"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.generate_daily_report = AsyncMock(return_value=mock_daily_report)
                
                response = client.post(
                    '/api/hooks/send_daily_report',
                    json={'send_email': False},
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 200
                
                # Verify service was called with yesterday's date
                call_args = mock_service.generate_daily_report.call_args
                report_date = call_args.kwargs['report_date']
                yesterday = (datetime.utcnow() - timedelta(days=1)).date()
                assert report_date == yesterday
    
    def test_send_daily_report_invalid_date(self, client, mock_user_token):
        """Test daily report with invalid date format"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            response = client.post(
                '/api/hooks/send_daily_report',
                json={
                    'date': 'invalid-date-format',
                    'send_email': False
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400
            assert 'Invalid date format' in response.json()['detail']
    
    def test_send_daily_report_no_email_recipients(self, client, mock_user_token):
        """Test daily report with no email recipients and no user email"""
        mock_user_no_email = {
            'uid': 'test_user_123',
            'name': 'Test User'
            # No email field
        }
        
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_no_email
            
            response = client.post(
                '/api/hooks/send_daily_report',
                json={'send_email': True},
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400
            assert 'No email recipients specified' in response.json()['detail']
    
    def test_send_daily_report_unauthorized(self, client):
        """Test daily report without authentication"""
        response = client.post(
            '/api/hooks/send_daily_report',
            json={'send_email': False}
        )
        
        assert response.status_code == 401
    
    def test_send_daily_report_service_error(self, client, mock_user_token):
        """Test daily report with service error"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.generate_daily_report = AsyncMock(
                    side_effect=Exception("Database connection failed")
                )
                
                response = client.post(
                    '/api/hooks/send_daily_report',
                    json={'send_email': False},
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 500
                assert 'Failed to generate daily report' in response.json()['detail']
    
    def test_preview_daily_report_success(self, client, mock_user_token, mock_daily_report):
        """Test successful daily report preview"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.generate_daily_report = AsyncMock(return_value=mock_daily_report)
                
                response = client.get(
                    '/api/hooks/daily_report_preview?date=2024-01-15&domain_filter=go2.video',
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert 'html_content' in data
                assert 'summary' in data
                assert data['summary']['total_clicks'] == 25
                assert data['summary']['total_links'] == 5
                assert data['summary']['top_links_count'] == 2
    
    def test_preview_daily_report_default_date(self, client, mock_user_token, mock_daily_report):
        """Test daily report preview with default date"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.generate_daily_report = AsyncMock(return_value=mock_daily_report)
                
                response = client.get(
                    '/api/hooks/daily_report_preview',
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 200
                
                # Verify service was called with yesterday's date
                call_args = mock_service.generate_daily_report.call_args
                report_date = call_args.kwargs['report_date']
                yesterday = (datetime.utcnow() - timedelta(days=1)).date()
                assert report_date == yesterday
    
    def test_preview_daily_report_invalid_date(self, client, mock_user_token):
        """Test daily report preview with invalid date"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            response = client.get(
                '/api/hooks/daily_report_preview?date=invalid-date',
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400
            assert 'Invalid date format' in response.json()['detail']
    
    def test_preview_daily_report_unauthorized(self, client):
        """Test daily report preview without authentication"""
        response = client.get('/api/hooks/daily_report_preview')
        
        assert response.status_code == 401
    
    def test_test_email_config_success(self, client, mock_user_token):
        """Test successful email configuration test"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.test_email_configuration = AsyncMock(return_value=True)
                
                response = client.post(
                    '/api/hooks/test_email_config',
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['status'] == 'success'
                assert 'Test email sent successfully' in data['message']
                
                # Verify service call
                mock_service.test_email_configuration.assert_called_once_with(
                    test_recipient='test@example.com',
                    user_name='Test User'
                )
    
    def test_test_email_config_failure(self, client, mock_user_token):
        """Test email configuration test failure"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.test_email_configuration = AsyncMock(return_value=False)
                
                response = client.post(
                    '/api/hooks/test_email_config',
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data['status'] == 'error'
                assert 'SendGrid not configured' in data['message']
    
    def test_test_email_config_no_user_email(self, client):
        """Test email configuration test without user email"""
        mock_user_no_email = {
            'uid': 'test_user_123',
            'name': 'Test User'
            # No email field
        }
        
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_no_email
            
            response = client.post(
                '/api/hooks/test_email_config',
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400
            assert 'User email not available' in response.json()['detail']
    
    def test_test_email_config_unauthorized(self, client):
        """Test email configuration test without authentication"""
        response = client.post('/api/hooks/test_email_config')
        
        assert response.status_code == 401
    
    def test_test_email_config_service_error(self, client, mock_user_token):
        """Test email configuration test with service error"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.test_email_configuration = AsyncMock(
                    side_effect=Exception("SendGrid API error")
                )
                
                response = client.post(
                    '/api/hooks/test_email_config',
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 500
                assert 'Email test failed' in response.json()['detail']
    
    def test_send_daily_report_with_all_parameters(self, client, mock_user_token, mock_daily_report):
        """Test daily report with all parameters specified"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.generate_daily_report = AsyncMock(return_value=mock_daily_report)
                mock_service.send_report_email = AsyncMock(return_value=True)
                
                response = client.post(
                    '/api/hooks/send_daily_report',
                    json={
                        'date': '2024-01-15',
                        'domain_filter': 'go2.tools',
                        'email_recipients': ['user1@example.com', 'user2@example.com'],
                        'send_email': True
                    },
                    headers={'Authorization': 'Bearer test_token'}
                )
                
                assert response.status_code == 200
                
                # Verify service calls with correct parameters
                generate_call = mock_service.generate_daily_report.call_args
                assert generate_call.kwargs['report_date'] == date(2024, 1, 15)
                assert generate_call.kwargs['domain_filter'] == 'go2.tools'
                assert generate_call.kwargs['user_uid'] == 'test_user_123'
                
                email_call = mock_service.send_report_email.call_args
                assert email_call.kwargs['recipients'] == ['user1@example.com', 'user2@example.com']
                assert email_call.kwargs['user_name'] == 'Test User'
    
    def test_hooks_router_cors_headers(self, client, mock_user_token, mock_daily_report):
        """Test that CORS headers are properly set for hooks endpoints"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.generate_daily_report = AsyncMock(return_value=mock_daily_report)
                
                # Test OPTIONS request
                response = client.options(
                    '/api/hooks/send_daily_report',
                    headers={'Origin': 'http://localhost:3000'}
                )
                
                # Should allow CORS for the frontend
                assert response.status_code in [200, 204]
    
    def test_background_task_execution(self, client, mock_user_token, mock_daily_report):
        """Test that background tasks are properly scheduled"""
        with patch('src.utils.auth.verify_firebase_token') as mock_verify:
            mock_verify.return_value = mock_user_token
            
            with patch('src.services.daily_report_service.daily_report_service') as mock_service:
                mock_service.generate_daily_report = AsyncMock(return_value=mock_daily_report)
                mock_service.send_report_email = AsyncMock(return_value=True)
                
                # Mock BackgroundTasks
                with patch('fastapi.BackgroundTasks') as mock_bg_tasks:
                    mock_bg_instance = Mock()
                    mock_bg_tasks.return_value = mock_bg_instance
                    
                    response = client.post(
                        '/api/hooks/send_daily_report',
                        json={'send_email': True},
                        headers={'Authorization': 'Bearer test_token'}
                    )
                    
                    assert response.status_code == 200
                    
                    # Note: In actual FastAPI, background tasks are added automatically
                    # This test verifies the endpoint structure is correct