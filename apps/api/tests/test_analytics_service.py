"""
Tests for the analytics service.
Tests click logging, geolocation, statistics aggregation, and data export.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import json

from src.services.analytics_service import AnalyticsService, analytics_service
from src.models.analytics import ClickDocument, LocationData, LinkStats, GeographicStats


@pytest.fixture
def mock_firestore():
    """Mock Firestore database"""
    with patch('src.services.analytics_service.firebase_service') as mock_service:
        mock_db = MagicMock()
        mock_service.db = mock_db
        yield mock_db


class TestAnalyticsService:
    """Test analytics service functionality"""
    
    def test_ip_hashing(self):
        """Test IP address hashing for privacy"""
        service = AnalyticsService()
        
        ip = '192.168.1.100'
        hashed = service.hash_ip(ip)
        
        # Verify hash properties
        assert len(hashed) == 16  # Truncated to 16 chars
        assert hashed != ip  # Not plaintext
        assert service.hash_ip(ip) == hashed  # Consistent hashing
        
        # Different IPs should produce different hashes
        assert service.hash_ip('192.168.1.101') != hashed
    
    def test_user_agent_parsing_desktop(self):
        """Test parsing desktop user agent"""
        service = AnalyticsService()
        
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        result = service.parse_user_agent(ua)
        
        assert result['device_type'] == 'desktop'
        assert 'Chrome' in result['browser']
        assert 'Windows' in result['os']
    
    def test_user_agent_parsing_mobile(self):
        """Test parsing mobile user agent"""
        service = AnalyticsService()
        
        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
        result = service.parse_user_agent(ua)
        
        assert result['device_type'] == 'mobile'
        assert 'Mobile Safari' in result['browser']
        assert 'iOS' in result['os']
    
    def test_user_agent_parsing_tablet(self):
        """Test parsing tablet user agent"""
        service = AnalyticsService()
        
        ua = 'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
        result = service.parse_user_agent(ua)
        
        assert result['device_type'] == 'tablet'
        assert 'Mobile Safari' in result['browser']
        assert 'iOS' in result['os']
    
    def test_user_agent_parsing_invalid(self):
        """Test parsing invalid user agent returns unknown"""
        service = AnalyticsService()
        
        result = service.parse_user_agent('invalid-user-agent')
        
        assert result['device_type'] == 'unknown'
        assert result['browser'] in [None, 'Other']  # user-agents library may return 'Other' for invalid UA
        assert result['os'] in [None, 'Other']  # user-agents library may return 'Other' for invalid UA
    
    def test_private_ip_detection(self):
        """Test detection of private IP addresses"""
        service = AnalyticsService()
        
        # Test private IPs
        private_ips = [
            '127.0.0.1',      # Loopback
            '10.0.0.1',       # Private Class A
            '172.16.0.1',     # Private Class B
            '172.31.255.255', # Private Class B upper bound
            '192.168.1.1',    # Private Class C
            '::1',            # IPv6 loopback
            'fc00::1',        # IPv6 private
            'fe80::1',        # IPv6 link-local
        ]
        
        for ip in private_ips:
            assert service._is_private_ip(ip) == True, f"Failed for {ip}"
        
        # Test public IPs
        public_ips = [
            '8.8.8.8',        # Google DNS
            '1.1.1.1',        # Cloudflare DNS
            '208.67.222.222', # OpenDNS
        ]
        
        for ip in public_ips:
            assert service._is_private_ip(ip) == False, f"Failed for {ip}"
    
    @pytest.mark.asyncio
    @patch('src.services.analytics_service.requests.get')
    async def test_geolocation_success(self, mock_requests):
        """Test successful IP geolocation"""
        service = AnalyticsService()
        
        # Mock successful API response
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
        
        # Test geolocation
        location = await service.get_location_from_ip('8.8.8.8')
        
        assert location.country == 'United States'
        assert location.country_code == 'US'
        assert location.region == 'California'
        assert location.city == 'San Francisco'
        assert location.timezone == 'America/Los_Angeles'
        assert location.latitude == 37.7749
        assert location.longitude == -122.4194
    
    @patch('src.services.analytics_service.requests.get')
    async def test_geolocation_api_error(self, mock_requests):
        """Test geolocation API error handling"""
        service = AnalyticsService()
        
        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'error': True,
            'reason': 'RateLimited'
        }
        mock_requests.return_value = mock_response
        
        # Test geolocation with error
        location = await service.get_location_from_ip('8.8.8.8')
        
        # Should return empty location data
        assert location.country is None
        assert location.city is None
    
    @patch('src.services.analytics_service.requests.get')
    async def test_geolocation_network_error(self, mock_requests):
        """Test geolocation network error handling"""
        service = AnalyticsService()
        
        # Mock network error
        mock_requests.side_effect = Exception("Network error")
        
        # Test geolocation with network error
        location = await service.get_location_from_ip('8.8.8.8')
        
        # Should return empty location data
        assert location.country is None
        assert location.city is None
    
    async def test_geolocation_private_ip(self):
        """Test geolocation skips private IPs"""
        service = AnalyticsService()
        
        # Test with private IP
        location = await service.get_location_from_ip('192.168.1.1')
        
        # Should return empty location data without API call
        assert location.country is None
        assert location.city is None
    
    @patch('src.services.analytics_service.requests.get')
    async def test_click_logging(self, mock_requests, mock_firestore):
        """Test click logging functionality"""
        service = AnalyticsService()
        
        # Mock geolocation response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'country_name': 'United States',
            'country_code': 'US',
            'region': 'California',
            'city': 'San Francisco'
        }
        mock_requests.return_value = mock_response
        
        # Mock Firestore
        mock_clicks_ref = MagicMock()
        mock_firestore.collection.return_value.document.return_value.collection.return_value = mock_clicks_ref
        
        # Log click
        await service.log_click(
            code='test123',
            ip='8.8.8.8',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            referrer='https://google.com/search'
        )
        
        # Verify Firestore was called
        mock_clicks_ref.add.assert_called_once()
        
        # Verify click data structure
        call_args = mock_clicks_ref.add.call_args[0][0]
        assert 'ts' in call_args
        assert 'ip_hash' in call_args
        assert 'ua' in call_args
        assert 'referrer' in call_args
        assert 'location' in call_args
        assert 'device_type' in call_args
        assert 'browser' in call_args
        assert 'os' in call_args
    
    async def test_click_logging_error_handling(self, mock_firestore):
        """Test click logging handles errors gracefully"""
        service = AnalyticsService()
        
        # Mock Firestore error
        mock_firestore.collection.side_effect = Exception("Database error")
        
        # Should not raise exception
        await service.log_click(code='test123', ip='8.8.8.8')
    
    async def test_get_stats_empty(self, mock_firestore):
        """Test getting stats for link with no clicks"""
        service = AnalyticsService()
        
        # Mock empty clicks collection
        mock_query = MagicMock()
        mock_query.stream.return_value = []
        
        mock_firestore.collection.return_value.document.return_value.collection.return_value.where.return_value.order_by.return_value = mock_query
        
        # Get stats
        stats = await service.get_stats('empty123', '7d')
        
        assert stats.total_clicks == 0
        assert len(stats.clicks_by_day) == 7  # Should have 7 days with zeros for 7d period
        assert all(clicks == 0 for clicks in stats.clicks_by_day.values())  # All should be zero
        assert len(stats.top_referrers) == 0
        assert len(stats.top_devices) == 0
        assert stats.last_clicked is None
    
    async def test_get_stats_with_data(self, mock_firestore):
        """Test getting stats for link with click data"""
        service = AnalyticsService()
        
        # Mock click documents with enhanced data
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        
        mock_clicks = [
            {
                'ts': now.isoformat(),
                'referrer': 'https://google.com/search',
                'device_type': 'desktop',
                'browser': 'Chrome',
                'os': 'Windows',
                'location': {
                    'country': 'United States',
                    'city': 'San Francisco',
                    'region': 'California'
                }
            },
            {
                'ts': yesterday.isoformat(),
                'referrer': 'https://twitter.com',
                'device_type': 'mobile',
                'browser': 'Safari',
                'os': 'iOS',
                'location': {
                    'country': 'Canada',
                    'city': 'Toronto',
                    'region': 'Ontario'
                }
            },
            {
                'ts': now.isoformat(),
                'referrer': None,  # Direct traffic
                'device_type': 'desktop',
                'browser': 'Firefox',
                'os': 'macOS',
                'location': {
                    'country': 'United States',
                    'city': 'New York',
                    'region': 'New York'
                }
            },
            {
                'ts': two_days_ago.isoformat(),
                'referrer': 'https://www.facebook.com',
                'device_type': 'tablet',
                'browser': 'Safari',
                'os': 'iPadOS',
                'location': {
                    'country': 'United Kingdom',
                    'city': 'London',
                    'region': 'England'
                }
            }
        ]
        
        # Mock Firestore query
        mock_docs = []
        for click in mock_clicks:
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = click
            mock_docs.append(mock_doc)
        
        mock_query = MagicMock()
        mock_query.stream.return_value = mock_docs
        
        mock_firestore.collection.return_value.document.return_value.collection.return_value.where.return_value.order_by.return_value = mock_query
        
        # Get stats
        stats = await service.get_stats('test123', '7d')
        
        # Verify aggregated data
        assert stats.total_clicks == 4
        assert len(stats.clicks_by_day) >= 3  # At least 3 different days (including zeros)
        assert 'google.com' in stats.top_referrers
        assert 'twitter.com' in stats.top_referrers
        assert 'facebook.com' in stats.top_referrers
        assert 'Direct' in stats.top_referrers
        assert stats.top_devices['desktop'] == 2
        assert stats.top_devices['mobile'] == 1
        assert stats.top_devices['tablet'] == 1
        assert stats.geographic_stats.countries['United States'] == 2
        assert stats.geographic_stats.countries['Canada'] == 1
        assert stats.geographic_stats.countries['United Kingdom'] == 1
        assert stats.last_clicked is not None
        
        # Verify enhanced geographic data with city context
        assert 'San Francisco, United States' in stats.geographic_stats.cities
        assert 'Toronto, Canada' in stats.geographic_stats.cities
        assert 'New York, United States' in stats.geographic_stats.cities
        assert 'London, United Kingdom' in stats.geographic_stats.cities
    
    async def test_export_data_json(self, mock_firestore):
        """Test exporting data in JSON format"""
        service = AnalyticsService()
        
        # Mock stats
        with patch.object(service, 'get_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = LinkStats(
                total_clicks=42,
                clicks_by_day={'2023-12-01': 10, '2023-12-02': 32},
                top_referrers={'google.com': 25, 'direct': 17},
                top_devices={'desktop': 30, 'mobile': 12}
            )
            
            # Export data
            data = await service.export_data('test123', 'json', '30d')
            
            # Verify JSON format
            parsed = json.loads(data.decode('utf-8'))
            assert parsed['total_clicks'] == 42
            assert '2023-12-01' in parsed['clicks_by_day']
            assert 'google.com' in parsed['top_referrers']
    
    async def test_export_data_csv(self, mock_firestore):
        """Test exporting data in CSV format"""
        service = AnalyticsService()
        
        # Mock stats
        with patch.object(service, 'get_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = LinkStats(
                total_clicks=42,
                clicks_by_day={'2023-12-01': 10, '2023-12-02': 32},
                top_referrers={'google.com': 25, 'direct': 17},
                top_devices={'desktop': 30, 'mobile': 12}
            )
            
            # Export data
            data = await service.export_data('test123', 'csv', '30d')
            
            # Verify CSV format
            csv_content = data.decode('utf-8')
            assert 'Metric,Value' in csv_content
            assert 'Total Clicks,42' in csv_content
            assert 'Date,Clicks' in csv_content
            assert '2023-12-01,10' in csv_content
            assert 'Referrer,Clicks' in csv_content
            assert 'google.com,25' in csv_content
    
    async def test_export_data_invalid_format(self, mock_firestore):
        """Test exporting data with invalid format raises error"""
        service = AnalyticsService()
        
        with pytest.raises(ValueError, match="Unsupported format"):
            await service.export_data('test123', 'xml', '30d')
    
    async def test_stats_error_handling(self, mock_firestore):
        """Test stats retrieval handles errors gracefully"""
        service = AnalyticsService()
        
        # Mock Firestore error
        mock_firestore.collection.side_effect = Exception("Database error")
        
        # Should return empty stats instead of raising
        stats = await service.get_stats('error123', '7d')
        
        assert stats.total_clicks == 0
        assert len(stats.clicks_by_day) == 0
    
    async def test_get_aggregated_stats(self, mock_firestore):
        """Test aggregated statistics across multiple links"""
        service = AnalyticsService()
        
        # Mock individual stats for multiple links
        with patch.object(service, 'get_stats', new_callable=AsyncMock) as mock_get_stats:
            # Mock stats for link1
            stats1 = LinkStats(
                total_clicks=10,
                clicks_by_day={'2023-12-01': 5, '2023-12-02': 5},
                top_referrers={'google.com': 6, 'direct': 4},
                top_devices={'desktop': 7, 'mobile': 3},
                geographic_stats=GeographicStats(
                    countries={'United States': 8, 'Canada': 2},
                    cities={'New York, United States': 5, 'Toronto, Canada': 2},
                    regions={'New York, United States': 5, 'Ontario, Canada': 2}
                )
            )
            
            # Mock stats for link2
            stats2 = LinkStats(
                total_clicks=15,
                clicks_by_day={'2023-12-01': 8, '2023-12-03': 7},
                top_referrers={'twitter.com': 9, 'google.com': 6},
                top_devices={'mobile': 10, 'desktop': 5},
                geographic_stats=GeographicStats(
                    countries={'United Kingdom': 10, 'United States': 5},
                    cities={'London, United Kingdom': 8, 'Boston, United States': 3},
                    regions={'England, United Kingdom': 8, 'Massachusetts, United States': 3}
                )
            )
            
            mock_get_stats.side_effect = [stats1, stats2]
            
            # Get aggregated stats
            aggregated = await service.get_aggregated_stats(['link1', 'link2'], '7d')
            
            # Verify aggregation
            assert aggregated.total_clicks == 25  # 10 + 15
            assert aggregated.clicks_by_day['2023-12-01'] == 13  # 5 + 8
            assert aggregated.clicks_by_day['2023-12-02'] == 5   # 5 + 0
            assert aggregated.clicks_by_day['2023-12-03'] == 7   # 0 + 7
            
            # Verify referrer aggregation
            assert aggregated.top_referrers['google.com'] == 12  # 6 + 6
            assert aggregated.top_referrers['twitter.com'] == 9  # 0 + 9
            assert aggregated.top_referrers['direct'] == 4      # 4 + 0
            
            # Verify device aggregation
            assert aggregated.top_devices['desktop'] == 12  # 7 + 5
            assert aggregated.top_devices['mobile'] == 13   # 3 + 10
            
            # Verify geographic aggregation
            assert aggregated.geographic_stats.countries['United States'] == 13  # 8 + 5
            assert aggregated.geographic_stats.countries['United Kingdom'] == 10  # 0 + 10
            assert aggregated.geographic_stats.countries['Canada'] == 2          # 2 + 0
    
    async def test_time_series_data_structure(self, mock_firestore):
        """Test that time series data includes zeros for missing days"""
        service = AnalyticsService()
        
        # Mock click data for only one day in a 7-day period
        now = datetime.utcnow()
        mock_clicks = [
            {
                'ts': now.isoformat(),
                'referrer': 'https://google.com',
                'device_type': 'desktop',
                'location': {'country': 'United States'}
            }
        ]
        
        mock_docs = []
        for click in mock_clicks:
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = click
            mock_docs.append(mock_doc)
        
        mock_query = MagicMock()
        mock_query.stream.return_value = mock_docs
        
        mock_firestore.collection.return_value.document.return_value.collection.return_value.where.return_value.order_by.return_value = mock_query
        
        # Get 7-day stats
        stats = await service.get_stats('test123', '7d')
        
        # Should have 7 days of data (including zeros)
        assert len(stats.clicks_by_day) == 7
        
        # Today should have 1 click
        today = now.strftime('%Y-%m-%d')
        assert stats.clicks_by_day[today] == 1
        
        # Other days should have 0 clicks
        zero_days = [day for day, clicks in stats.clicks_by_day.items() if day != today]
        assert len(zero_days) == 6
        for day in zero_days:
            assert stats.clicks_by_day[day] == 0
    
    async def test_enhanced_csv_export(self, mock_firestore):
        """Test enhanced CSV export with detailed analytics"""
        service = AnalyticsService()
        
        # Mock comprehensive stats
        with patch.object(service, 'get_stats', new_callable=AsyncMock) as mock_stats:
            mock_stats.return_value = LinkStats(
                total_clicks=100,
                clicks_by_day={
                    '2023-12-01': 30,
                    '2023-12-02': 25,
                    '2023-12-03': 45
                },
                top_referrers={
                    'google.com': 40,
                    'twitter.com': 30,
                    'direct': 20,
                    'facebook.com': 10
                },
                top_devices={
                    'desktop': 60,
                    'mobile': 35,
                    'tablet': 5
                },
                last_clicked=datetime(2023, 12, 3, 15, 30, 0),
                geographic_stats=GeographicStats(
                    countries={'United States': 70, 'Canada': 20, 'United Kingdom': 10},
                    cities={'New York, United States': 40, 'Toronto, Canada': 15},
                    regions={'New York, United States': 40, 'Ontario, Canada': 15}
                )
            )
            
            # Export CSV
            csv_data = await service.export_data('test123', 'csv', '30d')
            csv_content = csv_data.decode('utf-8')
            
            # Verify CSV structure and content
            assert 'Analytics Summary' in csv_content
            assert 'Total Clicks,100' in csv_content
            assert 'Daily Clicks Time Series' in csv_content
            assert '2023-12-01,30' in csv_content
            assert '2023-12-02,25' in csv_content
            assert '2023-12-03,45' in csv_content
            assert 'Top Traffic Sources' in csv_content
            assert 'google.com,40,40.0%' in csv_content
            assert 'twitter.com,30,30.0%' in csv_content
            assert 'Device Analytics' in csv_content
            assert 'desktop,60,60.0%' in csv_content
            assert 'mobile,35,35.0%' in csv_content
            assert 'Geographic Analytics - Countries' in csv_content
            assert 'United States,70,70.0%' in csv_content
            assert 'Canada,20,20.0%' in csv_content


class TestGlobalAnalyticsService:
    """Test the global analytics service instance"""
    
    def test_global_service_instance(self):
        """Test global analytics service is properly initialized"""
        assert analytics_service is not None
        assert isinstance(analytics_service, AnalyticsService)
    
    def test_service_methods_available(self):
        """Test all required methods are available on global service"""
        required_methods = [
            'hash_ip',
            'parse_user_agent',
            'get_location_from_ip',
            'log_click',
            'get_stats',
            'export_data'
        ]
        
        for method in required_methods:
            assert hasattr(analytics_service, method)
            assert callable(getattr(analytics_service, method))


if __name__ == '__main__':
    pytest.main([__file__])