"""
Tests for daily report service functionality.
Tests report generation, HTML template rendering, and email delivery.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from src.services.daily_report_service import DailyReportService
from src.models.analytics import DailyReportResponse, GeographicStats


class TestDailyReportService:
    """Test cases for DailyReportService"""
    
    @pytest.fixture
    def service(self):
        """Create a DailyReportService instance for testing"""
        return DailyReportService()
    
    @pytest.fixture
    def mock_firestore_data(self):
        """Mock Firestore data for testing"""
        return {
            'links': [
                {
                    'id': 'test1',
                    'data': {
                        'long_url': 'https://example.com/page1',
                        'base_domain': 'go2.video',
                        'owner_uid': 'user123',
                        'created_at': datetime.utcnow()
                    }
                },
                {
                    'id': 'test2', 
                    'data': {
                        'long_url': 'https://example.com/page2',
                        'base_domain': 'go2.tools',
                        'owner_uid': 'user123',
                        'created_at': datetime.utcnow()
                    }
                }
            ],
            'clicks': {
                'test1': [
                    {
                        'ts': datetime.utcnow(),
                        'ip_hash': 'hash123',
                        'ua': 'Mozilla/5.0',
                        'referrer': 'https://google.com',
                        'location': {
                            'country': 'United States',
                            'country_code': 'US',
                            'city': 'New York',
                            'region': 'New York'
                        },
                        'device_type': 'desktop',
                        'browser': 'Chrome',
                        'os': 'Windows'
                    },
                    {
                        'ts': datetime.utcnow(),
                        'ip_hash': 'hash456',
                        'ua': 'Mozilla/5.0',
                        'referrer': None,
                        'location': {
                            'country': 'Canada',
                            'country_code': 'CA',
                            'city': 'Toronto',
                            'region': 'Ontario'
                        },
                        'device_type': 'mobile',
                        'browser': 'Safari',
                        'os': 'iOS'
                    }
                ],
                'test2': [
                    {
                        'ts': datetime.utcnow(),
                        'ip_hash': 'hash789',
                        'ua': 'Mozilla/5.0',
                        'referrer': 'https://twitter.com',
                        'location': {
                            'country': 'United Kingdom',
                            'country_code': 'GB',
                            'city': 'London',
                            'region': 'England'
                        },
                        'device_type': 'tablet',
                        'browser': 'Firefox',
                        'os': 'Android'
                    }
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_generate_daily_report_success(self, service, mock_firestore_data):
        """Test successful daily report generation"""
        report_date = date.today() - timedelta(days=1)
        
        # Mock Firestore queries
        with patch.object(service.db, 'collection') as mock_collection:
            # Mock links collection query
            mock_links_query = Mock()
            mock_links_docs = []
            
            for link in mock_firestore_data['links']:
                mock_doc = Mock()
                mock_doc.id = link['id']
                mock_doc.to_dict.return_value = link['data']
                mock_links_docs.append(mock_doc)
            
            mock_links_query.stream.return_value = mock_links_docs
            mock_links_query.where.return_value = mock_links_query  # Chain where calls
            mock_collection.return_value = mock_links_query
            
            # Mock clicks subcollection queries
            def mock_document_collection_chain(*args):
                if len(args) == 1:  # collection('links')
                    return mock_links_query
                elif len(args) == 2:  # document(code)
                    mock_doc_ref = Mock()
                    mock_clicks_collection = Mock()
                    
                    # Return appropriate clicks for each link
                    code = args[1] if isinstance(args[1], str) else args[0]
                    clicks_data = mock_firestore_data['clicks'].get(code, [])
                    
                    mock_clicks_docs = []
                    for click in clicks_data:
                        mock_click_doc = Mock()
                        mock_click_doc.to_dict.return_value = click
                        mock_clicks_docs.append(mock_click_doc)
                    
                    mock_clicks_query = Mock()
                    mock_clicks_query.stream.return_value = mock_clicks_docs
                    mock_clicks_query.where.return_value = mock_clicks_query
                    
                    mock_clicks_collection.where.return_value = mock_clicks_query
                    mock_doc_ref.collection.return_value = mock_clicks_collection
                    return mock_doc_ref
            
            # Setup the chain: collection().document().collection()
            mock_collection.return_value.document.side_effect = lambda code: mock_document_collection_chain('links', code)
            
            # Generate report
            report = await service.generate_daily_report(
                report_date=report_date,
                user_uid='user123'
            )
            
            # Verify report structure
            assert isinstance(report, DailyReportResponse)
            assert report.date.date() == report_date
            assert report.total_clicks == 3  # Total clicks from mock data
            assert report.total_links == 2   # Total links from mock data
            assert len(report.top_links) <= 10
            assert report.html_content is not None
            assert len(report.html_content) > 0
            
            # Verify geographic stats
            assert 'United States' in report.geographic_breakdown.countries
            assert 'Canada' in report.geographic_breakdown.countries
            assert 'United Kingdom' in report.geographic_breakdown.countries
            
            # Verify device breakdown
            assert 'desktop' in report.device_breakdown
            assert 'mobile' in report.device_breakdown
            assert 'tablet' in report.device_breakdown
    
    @pytest.mark.asyncio
    async def test_generate_daily_report_with_domain_filter(self, service, mock_firestore_data):
        """Test daily report generation with domain filter"""
        report_date = date.today() - timedelta(days=1)
        
        with patch.object(service.db, 'collection') as mock_collection:
            # Mock filtered links query
            mock_links_query = Mock()
            
            # Only return links matching the domain filter
            filtered_links = [link for link in mock_firestore_data['links'] 
                            if link['data']['base_domain'] == 'go2.video']
            
            mock_links_docs = []
            for link in filtered_links:
                mock_doc = Mock()
                mock_doc.id = link['id']
                mock_doc.to_dict.return_value = link['data']
                mock_links_docs.append(mock_doc)
            
            mock_links_query.stream.return_value = mock_links_docs
            mock_links_query.where.return_value = mock_links_query
            mock_collection.return_value = mock_links_query
            
            # Mock clicks for filtered links
            def mock_document_collection_chain(*args):
                if len(args) == 2:  # document(code)
                    mock_doc_ref = Mock()
                    mock_clicks_collection = Mock()
                    
                    code = args[1] if isinstance(args[1], str) else args[0]
                    clicks_data = mock_firestore_data['clicks'].get(code, [])
                    
                    mock_clicks_docs = []
                    for click in clicks_data:
                        mock_click_doc = Mock()
                        mock_click_doc.to_dict.return_value = click
                        mock_clicks_docs.append(mock_click_doc)
                    
                    mock_clicks_query = Mock()
                    mock_clicks_query.stream.return_value = mock_clicks_docs
                    mock_clicks_query.where.return_value = mock_clicks_query
                    
                    mock_clicks_collection.where.return_value = mock_clicks_query
                    mock_doc_ref.collection.return_value = mock_clicks_collection
                    return mock_doc_ref
            
            mock_collection.return_value.document.side_effect = lambda code: mock_document_collection_chain('links', code)
            
            # Generate filtered report
            report = await service.generate_daily_report(
                report_date=report_date,
                domain_filter='go2.video',
                user_uid='user123'
            )
            
            # Verify filtering worked
            assert report.total_links == 1  # Only one go2.video link
            assert report.total_clicks == 2  # Only clicks for test1
    
    @pytest.mark.asyncio
    async def test_generate_daily_report_no_data(self, service):
        """Test daily report generation with no data"""
        report_date = date.today() - timedelta(days=1)
        
        with patch.object(service.db, 'collection') as mock_collection:
            # Mock empty results
            mock_links_query = Mock()
            mock_links_query.stream.return_value = []
            mock_links_query.where.return_value = mock_links_query  # Chain where calls
            mock_collection.return_value = mock_links_query
            
            report = await service.generate_daily_report(
                report_date=report_date,
                user_uid='user123'
            )
            
            # Verify empty report
            assert report.total_clicks == 0
            assert report.total_links == 0
            assert len(report.top_links) == 0
            assert report.html_content is not None  # Should still generate HTML
    
    def test_generate_html_report(self, service):
        """Test HTML report generation"""
        report_date = date.today() - timedelta(days=1)
        
        # Mock data
        top_links = [
            {
                'code': 'test1',
                'long_url': 'https://example.com/page1',
                'base_domain': 'go2.video',
                'clicks': 10
            }
        ]
        
        geographic_stats = GeographicStats(
            countries={'United States': 5, 'Canada': 3},
            cities={'New York, United States': 3, 'Toronto, Canada': 2},
            regions={'New York, United States': 3, 'Ontario, Canada': 2}
        )
        
        device_breakdown = {'desktop': 6, 'mobile': 4}
        referrer_breakdown = {'google.com': 5, 'Direct': 5}
        
        html_content = service._generate_html_report(
            report_date=report_date,
            total_clicks=10,
            total_links=1,
            top_links=top_links,
            geographic_stats=geographic_stats,
            device_breakdown=device_breakdown,
            referrer_breakdown=referrer_breakdown
        )
        
        # Verify HTML content
        assert isinstance(html_content, str)
        assert len(html_content) > 0
        assert '<!DOCTYPE html>' in html_content
        assert 'Daily Analytics Report' in html_content
        assert 'test1' in html_content
        assert 'go2.video' in html_content
        assert 'United States' in html_content
        assert 'Desktop' in html_content or 'desktop' in html_content
        assert 'google.com' in html_content
    
    def test_generate_html_report_with_domain_filter(self, service):
        """Test HTML report generation with domain filter"""
        report_date = date.today() - timedelta(days=1)
        
        html_content = service._generate_html_report(
            report_date=report_date,
            total_clicks=5,
            total_links=1,
            top_links=[],
            geographic_stats=GeographicStats(),
            device_breakdown={},
            referrer_breakdown={},
            domain_filter='go2.video'
        )
        
        # Verify domain filter is mentioned
        assert 'go2.video' in html_content
        assert 'Filtered by domain' in html_content or 'filtered to show data for' in html_content
    
    @pytest.mark.asyncio
    async def test_send_report_email_success(self, service):
        """Test successful email sending"""
        # Mock SendGrid
        with patch('sendgrid.SendGridAPIClient') as mock_sg_client:
            mock_sg = Mock()
            mock_response = Mock()
            mock_response.status_code = 202
            mock_sg.send.return_value = mock_response
            mock_sg_client.return_value = mock_sg
            
            # Mock environment variable
            with patch.dict('os.environ', {'SENDGRID_API_KEY': 'test_key'}):
                service.sendgrid_api_key = 'test_key'
                
                # Create test report
                report = DailyReportResponse(
                    date=datetime.utcnow(),
                    total_clicks=10,
                    total_links=2,
                    top_links=[],
                    geographic_breakdown=GeographicStats(),
                    device_breakdown={},
                    referrer_breakdown={},
                    html_content='<html><body>Test Report</body></html>'
                )
                
                result = await service.send_report_email(
                    report=report,
                    recipients=['test@example.com'],
                    user_name='Test User'
                )
                
                assert result is True
                mock_sg.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_report_email_no_api_key(self, service):
        """Test email sending without API key"""
        service.sendgrid_api_key = None
        
        report = DailyReportResponse(
            date=datetime.utcnow(),
            total_clicks=0,
            total_links=0,
            top_links=[],
            geographic_breakdown=GeographicStats(),
            device_breakdown={},
            referrer_breakdown={},
            html_content='<html><body>Test</body></html>'
        )
        
        result = await service.send_report_email(
            report=report,
            recipients=['test@example.com']
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_send_report_email_sendgrid_error(self, service):
        """Test email sending with SendGrid error"""
        with patch('sendgrid.SendGridAPIClient') as mock_sg_client:
            mock_sg = Mock()
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.body = 'Bad Request'
            mock_sg.send.return_value = mock_response
            mock_sg_client.return_value = mock_sg
            
            with patch.dict('os.environ', {'SENDGRID_API_KEY': 'test_key'}):
                service.sendgrid_api_key = 'test_key'
                
                report = DailyReportResponse(
                    date=datetime.utcnow(),
                    total_clicks=0,
                    total_links=0,
                    top_links=[],
                    geographic_breakdown=GeographicStats(),
                    device_breakdown={},
                    referrer_breakdown={},
                    html_content='<html><body>Test</body></html>'
                )
                
                result = await service.send_report_email(
                    report=report,
                    recipients=['test@example.com']
                )
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_test_email_configuration_success(self, service):
        """Test successful email configuration test"""
        with patch('sendgrid.SendGridAPIClient') as mock_sg_client:
            mock_sg = Mock()
            mock_response = Mock()
            mock_response.status_code = 202
            mock_sg.send.return_value = mock_response
            mock_sg_client.return_value = mock_sg
            
            with patch.dict('os.environ', {'SENDGRID_API_KEY': 'test_key'}):
                service.sendgrid_api_key = 'test_key'
                
                result = await service.test_email_configuration(
                    test_recipient='test@example.com',
                    user_name='Test User'
                )
                
                assert result is True
                mock_sg.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_test_email_configuration_no_api_key(self, service):
        """Test email configuration test without API key"""
        service.sendgrid_api_key = None
        
        result = await service.test_email_configuration(
            test_recipient='test@example.com'
        )
        
        assert result is False
    
    def test_html_template_rendering_edge_cases(self, service):
        """Test HTML template with edge cases"""
        report_date = date.today()
        
        # Test with empty data
        html_content = service._generate_html_report(
            report_date=report_date,
            total_clicks=0,
            total_links=0,
            top_links=[],
            geographic_stats=GeographicStats(),
            device_breakdown={},
            referrer_breakdown={}
        )
        
        assert 'No clicks recorded' in html_content or '0' in html_content
        
        # Test with very long URLs
        long_url_links = [
            {
                'code': 'test',
                'long_url': 'https://example.com/' + 'a' * 200,  # Very long URL
                'base_domain': 'go2.tools',
                'clicks': 1
            }
        ]
        
        html_content = service._generate_html_report(
            report_date=report_date,
            total_clicks=1,
            total_links=1,
            top_links=long_url_links,
            geographic_stats=GeographicStats(),
            device_breakdown={},
            referrer_breakdown={}
        )
        
        # Should truncate long URLs
        assert '...' in html_content or len(html_content) < 50000  # Reasonable size limit
    
    @pytest.mark.asyncio
    async def test_generate_report_error_handling(self, service):
        """Test error handling in report generation"""
        report_date = date.today() - timedelta(days=1)
        
        # Mock Firestore to raise an exception
        with patch.object(service.db, 'collection') as mock_collection:
            mock_collection.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception) as exc_info:
                await service.generate_daily_report(
                    report_date=report_date,
                    user_uid='user123'
                )
            
            assert "Database connection failed" in str(exc_info.value)