"""
Tests for the analytics router.
Tests analytics endpoints, permissions, and data export functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import json

from src.main import app
from src.models.analytics import LinkStats, GeographicStats


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user"""
    return {
        'uid': 'test-user-123',
        'email': 'test@example.com',
        'admin': False
    }


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    return {
        'uid': 'admin-user-123',
        'email': 'admin@example.com',
        'admin': True
    }


@pytest.fixture
def mock_link_data():
    """Mock link document data"""
    return {
        'long_url': 'https://example.com',
        'base_domain': 'go2.tools',
        'owner_uid': 'test-user-123',
        'created_at': datetime.utcnow(),
        'disabled': False
    }


@pytest.fixture
def mock_analytics_stats():
    """Mock analytics statistics"""
    return LinkStats(
        total_clicks=42,
        clicks_by_day={
            '2023-12-01': 15,
            '2023-12-02': 20,
            '2023-12-03': 7
        },
        top_referrers={
            'google.com': 25,
            'twitter.com': 12,
            'direct': 5
        },
        top_devices={
            'desktop': 30,
            'mobile': 10,
            'tablet': 2
        },
        last_clicked=datetime(2023, 12, 3, 15, 30, 0),
        geographic_stats=GeographicStats(
            countries={'United States': 30, 'Canada': 8, 'United Kingdom': 4},
            cities={'New York, United States': 20, 'Toronto, Canada': 6},
            regions={'New York, United States': 20, 'Ontario, Canada': 6}
        )
    )


class TestAnalyticsRouter:
    """Test analytics router endpoints"""
    
    def test_get_link_analytics_success(self, client, mock_auth_user, mock_link_data, mock_analytics_stats):
        """Test successful analytics retrieval"""
        from src.routers.analytics import get_current_user, firebase_service, analytics_service
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_auth_user
        
        with patch.object(firebase_service, 'db') as mock_db, \
             patch.object(analytics_service, 'get_stats', new_callable=AsyncMock) as mock_get_stats:
            
            # Mock Firestore
            mock_doc = MagicMock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = mock_link_data
            mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            # Mock analytics service
            mock_get_stats.return_value = mock_analytics_stats
            
            # Make request
            response = client.get('/api/analytics/stats/test123?period=7d')
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data['total_clicks'] == 42
            assert '2023-12-01' in data['clicks_by_day']
            assert 'google.com' in data['top_referrers']
            assert 'desktop' in data['top_devices']
            assert 'United States' in data['geographic_stats']['countries']
        
        # Clean up
        app.dependency_overrides.clear()
    
    @patch('src.routers.analytics.firebase_service')
    @patch('src.routers.analytics.get_current_user')
    def test_get_link_analytics_not_found(self, mock_get_user, mock_firebase, client, mock_auth_user):
        """Test analytics for non-existent link"""
        # Mock authentication
        mock_get_user.return_value = mock_auth_user
        
        # Mock Firestore - link not found
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get('/api/analytics/stats/nonexistent?period=7d')
        
        # Verify 404 response
        assert response.status_code == 404
        assert 'Link not found' in response.json()['detail']
    
    @patch('src.routers.analytics.firebase_service')
    @patch('src.routers.analytics.get_current_user')
    def test_get_link_analytics_permission_denied(self, mock_get_user, mock_firebase, client, mock_auth_user, mock_link_data):
        """Test analytics access denied for non-owner"""
        # Mock authentication
        mock_get_user.return_value = mock_auth_user
        
        # Mock Firestore - different owner
        different_owner_data = mock_link_data.copy()
        different_owner_data['owner_uid'] = 'different-user-456'
        
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = different_owner_data
        mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Make request
        response = client.get('/api/analytics/stats/test123?period=7d')
        
        # Verify 403 response
        assert response.status_code == 403
        assert 'Permission denied' in response.json()['detail']
    
    @patch('src.routers.analytics.firebase_service')
    @patch('src.routers.analytics.analytics_service')
    @patch('src.routers.analytics.get_current_user')
    def test_get_link_analytics_admin_access(self, mock_get_user, mock_analytics, mock_firebase, client, mock_admin_user, mock_link_data, mock_analytics_stats):
        """Test admin can access any link analytics"""
        # Mock authentication as admin
        mock_get_user.return_value = mock_admin_user
        
        # Mock Firestore - different owner
        different_owner_data = mock_link_data.copy()
        different_owner_data['owner_uid'] = 'different-user-456'
        
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = different_owner_data
        mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock analytics service
        mock_analytics.get_stats = AsyncMock(return_value=mock_analytics_stats)
        
        # Make request
        response = client.get('/api/analytics/stats/test123?period=7d')
        
        # Verify success
        assert response.status_code == 200
        data = response.json()
        assert data['total_clicks'] == 42
    
    def test_get_link_analytics_invalid_period(self, client):
        """Test analytics with invalid period parameter"""
        response = client.get('/api/analytics/stats/test123?period=invalid')
        
        # Should return 422 for invalid query parameter
        assert response.status_code == 422
    
    @patch('src.routers.analytics.firebase_service')
    @patch('src.routers.analytics.analytics_service')
    @patch('src.routers.analytics.get_current_user')
    def test_get_geographic_analytics(self, mock_get_user, mock_analytics, mock_firebase, client, mock_auth_user, mock_link_data, mock_analytics_stats):
        """Test geographic analytics endpoint"""
        # Mock authentication
        mock_get_user.return_value = mock_auth_user
        
        # Mock Firestore
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = mock_link_data
        mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock analytics service
        mock_analytics.get_stats = AsyncMock(return_value=mock_analytics_stats)
        
        # Make request
        response = client.get('/api/analytics/geographic/test123?period=30d')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert 'countries' in data
        assert 'cities' in data
        assert 'regions' in data
        assert 'United States' in data['countries']
        assert data['countries']['United States'] == 30
    
    @patch('src.routers.analytics.firebase_service')
    @patch('src.routers.analytics.analytics_service')
    @patch('src.routers.analytics.get_current_user')
    def test_export_analytics_data_json(self, mock_get_user, mock_analytics, mock_firebase, client, mock_auth_user, mock_link_data):
        """Test analytics data export in JSON format"""
        # Mock authentication
        mock_get_user.return_value = mock_auth_user
        
        # Mock Firestore
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = mock_link_data
        mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock analytics service export
        export_data = json.dumps({'total_clicks': 42, 'period': '30d'}).encode('utf-8')
        mock_analytics.export_data = AsyncMock(return_value=export_data)
        
        # Make request
        response = client.get('/api/analytics/export/test123?format=json&period=30d')
        
        # Verify response
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/json'
        assert 'attachment; filename=test123_analytics_30d.json' in response.headers['content-disposition']
        
        # Verify exported data
        exported_data = json.loads(response.content)
        assert exported_data['total_clicks'] == 42
        assert exported_data['period'] == '30d'
    
    @patch('src.routers.analytics.firebase_service')
    @patch('src.routers.analytics.analytics_service')
    @patch('src.routers.analytics.get_current_user')
    def test_export_analytics_data_csv(self, mock_get_user, mock_analytics, mock_firebase, client, mock_auth_user, mock_link_data):
        """Test analytics data export in CSV format"""
        # Mock authentication
        mock_get_user.return_value = mock_auth_user
        
        # Mock Firestore
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = mock_link_data
        mock_firebase.db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock analytics service export
        csv_data = "Metric,Value\nTotal Clicks,42\nPeriod,30d".encode('utf-8')
        mock_analytics.export_data = AsyncMock(return_value=csv_data)
        
        # Make request
        response = client.get('/api/analytics/export/test123?format=csv&period=30d')
        
        # Verify response
        assert response.status_code == 200
        assert response.headers['content-type'] == 'text/csv'
        assert 'attachment; filename=test123_analytics_30d.csv' in response.headers['content-disposition']
        
        # Verify CSV content
        csv_content = response.content.decode('utf-8')
        assert 'Total Clicks,42' in csv_content
        assert 'Period,30d' in csv_content
    
    @patch('src.routers.analytics.firebase_service')
    @patch('src.routers.analytics.analytics_service')
    @patch('src.routers.analytics.require_auth')
    @patch('src.routers.analytics.get_user_id')
    def test_get_user_analytics_summary(self, mock_get_user_id, mock_require_auth, mock_analytics, mock_firebase, client, mock_auth_user):
        """Test user analytics summary endpoint"""
        # Mock authentication
        mock_require_auth.return_value = mock_auth_user
        mock_get_user_id.return_value = 'test-user-123'
        
        # Mock Firestore query for user's links
        mock_doc1 = MagicMock()
        mock_doc1.id = 'link1'
        mock_doc2 = MagicMock()
        mock_doc2.id = 'link2'
        
        mock_query = MagicMock()
        mock_query.stream.return_value = [mock_doc1, mock_doc2]
        mock_firebase.db.collection.return_value.where.return_value = mock_query
        
        # Mock analytics service for each link
        stats1 = LinkStats(total_clicks=20, top_devices={'desktop': 15, 'mobile': 5})
        stats2 = LinkStats(total_clicks=30, top_devices={'mobile': 20, 'desktop': 10})
        
        mock_analytics.get_stats = AsyncMock(side_effect=[stats1, stats2])
        
        # Make request
        response = client.get('/api/analytics/summary?period=30d')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['total_links'] == 2
        assert data['total_clicks'] == 50  # 20 + 30
        assert data['period'] == '30d'
        assert 'top_devices' in data
        assert data['top_devices']['desktop'] == 25  # 15 + 10
        assert data['top_devices']['mobile'] == 25   # 5 + 20
    
    @patch('src.routers.analytics.firebase_service')
    @patch('src.routers.analytics.analytics_service')
    @patch('src.routers.analytics.require_admin')
    @patch('src.routers.analytics.get_user_id')
    def test_get_admin_analytics_overview(self, mock_get_user_id, mock_require_admin, mock_analytics, mock_firebase, client, mock_admin_user):
        """Test admin analytics overview endpoint"""
        # Mock authentication
        mock_require_admin.return_value = mock_admin_user
        mock_get_user_id.return_value = 'admin-user-123'
        
        # Mock Firestore query for all links
        mock_doc1 = MagicMock()
        mock_doc1.id = 'link1'
        mock_doc2 = MagicMock()
        mock_doc2.id = 'link2'
        mock_doc3 = MagicMock()
        mock_doc3.id = 'link3'
        
        mock_firebase.db.collection.return_value.stream.return_value = [mock_doc1, mock_doc2, mock_doc3]
        
        # Mock analytics service - some links have clicks, some don't
        stats1 = LinkStats(total_clicks=25, clicks_by_day={'2023-12-01': 15, '2023-12-02': 10})
        stats2 = LinkStats(total_clicks=0)  # No clicks
        stats3 = LinkStats(total_clicks=35, clicks_by_day={'2023-12-01': 20, '2023-12-03': 15})
        
        mock_analytics.get_stats = AsyncMock(side_effect=[stats1, stats2, stats3])
        
        # Make request
        response = client.get('/api/analytics/admin/overview?period=7d')
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['total_links'] == 3
        assert data['active_links'] == 2  # Only links with clicks
        assert data['total_clicks'] == 60  # 25 + 0 + 35
        assert data['period'] == '7d'
        assert 'clicks_by_day' in data
        assert data['clicks_by_day']['2023-12-01'] == 35  # 15 + 0 + 20
        assert data['clicks_by_day']['2023-12-02'] == 10  # 10 + 0 + 0
        assert data['clicks_by_day']['2023-12-03'] == 15  # 0 + 0 + 15
    
    def test_get_admin_analytics_overview_requires_admin(self, client):
        """Test admin overview requires admin privileges"""
        response = client.get('/api/analytics/admin/overview')
        
        # Should require authentication
        assert response.status_code in [401, 403]
    
    @patch('src.routers.analytics.firebase_service')
    @patch('src.routers.analytics.require_admin')
    @patch('src.routers.analytics.get_user_id')
    def test_generate_daily_report(self, mock_get_user_id, mock_require_admin, mock_firebase, client, mock_admin_user):
        """Test daily report generation"""
        # Mock authentication
        mock_require_admin.return_value = mock_admin_user
        mock_get_user_id.return_value = 'admin-user-123'
        
        # Mock Firestore query for links
        mock_doc = MagicMock()
        mock_doc.reference.collection.return_value.where.return_value.where.return_value = MagicMock()
        mock_doc.reference.collection.return_value.where.return_value.where.return_value.stream.return_value = []
        
        mock_link_data = {
            'long_url': 'https://example.com',
            'base_domain': 'go2.tools'
        }
        mock_doc.to_dict.return_value = mock_link_data
        
        mock_firebase.db.collection.return_value.stream.return_value = [mock_doc]
        
        # Make request
        report_data = {
            'date': '2023-12-01T00:00:00Z',
            'domain_filter': None
        }
        
        response = client.post('/api/analytics/admin/daily-report', json=report_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert 'date' in data
        assert 'total_clicks' in data
        assert 'total_links' in data
        assert 'top_links' in data
        assert 'geographic_breakdown' in data
        assert 'device_breakdown' in data
        assert 'referrer_breakdown' in data


if __name__ == '__main__':
    pytest.main([__file__])