"""
Integration tests for hooks functionality.
Tests the daily report generation and email sending without full FastAPI setup.
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from src.services.daily_report_service import DailyReportService
from src.models.analytics import DailyReportResponse, GeographicStats


class TestHooksIntegration:
    """Integration test cases for hooks functionality"""
    
    @pytest.fixture
    def service(self):
        """Create a DailyReportService instance for testing"""
        return DailyReportService()
    
    @pytest.mark.asyncio
    async def test_end_to_end_report_generation(self, service):
        """Test end-to-end report generation workflow"""
        report_date = date.today() - timedelta(days=1)
        
        # Mock Firestore data
        mock_links_data = [
            {
                'id': 'abc123',
                'data': {
                    'long_url': 'https://youtube.com/watch?v=example',
                    'base_domain': 'go2.video',
                    'owner_uid': 'user123',
                    'created_at': datetime.utcnow()
                }
            }
        ]
        
        mock_clicks_data = [
            {
                'ts': datetime.utcnow(),
                'ip_hash': 'hash123',
                'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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
            }
        ]
        
        with patch.object(service.db, 'collection') as mock_collection:
            # Mock links query
            mock_links_query = Mock()
            mock_links_docs = []
            
            for link in mock_links_data:
                mock_doc = Mock()
                mock_doc.id = link['id']
                mock_doc.to_dict.return_value = link['data']
                mock_links_docs.append(mock_doc)
            
            mock_links_query.stream.return_value = mock_links_docs
            mock_links_query.where.return_value = mock_links_query
            mock_collection.return_value = mock_links_query
            
            # Mock clicks query
            def mock_document_collection_chain(code):
                mock_doc_ref = Mock()
                mock_clicks_collection = Mock()
                
                mock_clicks_docs = []
                for click in mock_clicks_data:
                    mock_click_doc = Mock()
                    mock_click_doc.to_dict.return_value = click
                    mock_clicks_docs.append(mock_click_doc)
                
                mock_clicks_query = Mock()
                mock_clicks_query.stream.return_value = mock_clicks_docs
                mock_clicks_query.where.return_value = mock_clicks_query
                
                mock_clicks_collection.where.return_value = mock_clicks_query
                mock_doc_ref.collection.return_value = mock_clicks_collection
                return mock_doc_ref
            
            mock_collection.return_value.document.side_effect = mock_document_collection_chain
            
            # Generate report
            report = await service.generate_daily_report(
                report_date=report_date,
                user_uid='user123'
            )
            
            # Verify report structure
            assert isinstance(report, DailyReportResponse)
            assert report.total_clicks == 1
            assert report.total_links == 1
            assert len(report.top_links) == 1
            assert report.top_links[0]['code'] == 'abc123'
            assert report.top_links[0]['base_domain'] == 'go2.video'
            assert report.html_content is not None
            assert len(report.html_content) > 1000  # Should be substantial HTML
            
            # Verify geographic data
            assert 'United States' in report.geographic_breakdown.countries
            assert report.geographic_breakdown.countries['United States'] == 1
            
            # Verify device data
            assert 'desktop' in report.device_breakdown
            assert report.device_breakdown['desktop'] == 1
            
            # Verify referrer data
            assert 'google.com' in report.referrer_breakdown
            assert report.referrer_breakdown['google.com'] == 1
    
    @pytest.mark.asyncio
    async def test_email_workflow_with_sendgrid(self, service):
        """Test complete email workflow with SendGrid"""
        # Create a test report
        report = DailyReportResponse(
            date=datetime.utcnow(),
            total_clicks=50,
            total_links=10,
            top_links=[
                {
                    'code': 'popular1',
                    'long_url': 'https://example.com/popular-page',
                    'base_domain': 'go2.tools',
                    'clicks': 25
                },
                {
                    'code': 'popular2',
                    'long_url': 'https://youtube.com/watch?v=viral',
                    'base_domain': 'go2.video',
                    'clicks': 15
                }
            ],
            geographic_breakdown=GeographicStats(
                countries={'United States': 30, 'Canada': 15, 'United Kingdom': 5},
                cities={'New York, United States': 20, 'Toronto, Canada': 10, 'London, United Kingdom': 5},
                regions={'New York, United States': 20, 'Ontario, Canada': 10, 'England, United Kingdom': 5}
            ),
            device_breakdown={'desktop': 30, 'mobile': 15, 'tablet': 5},
            referrer_breakdown={'google.com': 25, 'Direct': 20, 'twitter.com': 5},
            html_content='<html><body><h1>Test Report</h1></body></html>'
        )
        
        # Test successful email sending
        with patch('sendgrid.SendGridAPIClient') as mock_sg_client:
            mock_sg = Mock()
            mock_response = Mock()
            mock_response.status_code = 202
            mock_sg.send.return_value = mock_response
            mock_sg_client.return_value = mock_sg
            
            with patch.dict('os.environ', {'SENDGRID_API_KEY': 'test_key'}):
                service.sendgrid_api_key = 'test_key'
                
                result = await service.send_report_email(
                    report=report,
                    recipients=['user@example.com', 'admin@example.com'],
                    user_name='Test User'
                )
                
                assert result is True
                
                # Verify SendGrid was called
                mock_sg.send.assert_called_once()
                
                # Verify email content structure
                call_args = mock_sg.send.call_args[0][0]  # Get the Mail object
                # Just verify that send was called with a Mail object
                assert call_args is not None
    
    @pytest.mark.asyncio
    async def test_report_with_domain_filtering(self, service):
        """Test report generation with domain filtering"""
        report_date = date.today() - timedelta(days=1)
        
        # Mock mixed domain data
        mock_links_data = [
            {
                'id': 'video1',
                'data': {
                    'long_url': 'https://youtube.com/watch?v=example1',
                    'base_domain': 'go2.video',
                    'owner_uid': 'user123',
                    'created_at': datetime.utcnow()
                }
            },
            {
                'id': 'tool1',
                'data': {
                    'long_url': 'https://github.com/example/repo',
                    'base_domain': 'go2.tools',
                    'owner_uid': 'user123',
                    'created_at': datetime.utcnow()
                }
            }
        ]
        
        with patch.object(service.db, 'collection') as mock_collection:
            # Mock filtered query (only go2.video links)
            mock_links_query = Mock()
            filtered_links = [link for link in mock_links_data if link['data']['base_domain'] == 'go2.video']
            
            mock_links_docs = []
            for link in filtered_links:
                mock_doc = Mock()
                mock_doc.id = link['id']
                mock_doc.to_dict.return_value = link['data']
                mock_links_docs.append(mock_doc)
            
            mock_links_query.stream.return_value = mock_links_docs
            mock_links_query.where.return_value = mock_links_query
            mock_collection.return_value = mock_links_query
            
            # Mock clicks for video1 only
            def mock_document_collection_chain(code):
                mock_doc_ref = Mock()
                mock_clicks_collection = Mock()
                
                if code == 'video1':
                    mock_clicks_docs = [Mock()]
                    mock_clicks_docs[0].to_dict.return_value = {
                        'ts': datetime.utcnow(),
                        'location': {'country': 'Canada'},
                        'device_type': 'mobile',
                        'referrer': 'https://twitter.com'
                    }
                else:
                    mock_clicks_docs = []
                
                mock_clicks_query = Mock()
                mock_clicks_query.stream.return_value = mock_clicks_docs
                mock_clicks_query.where.return_value = mock_clicks_query
                
                mock_clicks_collection.where.return_value = mock_clicks_query
                mock_doc_ref.collection.return_value = mock_clicks_collection
                return mock_doc_ref
            
            mock_collection.return_value.document.side_effect = mock_document_collection_chain
            
            # Generate filtered report
            report = await service.generate_daily_report(
                report_date=report_date,
                domain_filter='go2.video',
                user_uid='user123'
            )
            
            # Verify filtering worked
            assert report.total_links == 1  # Only go2.video link
            assert report.total_clicks == 1  # Only clicks for video1
            assert len(report.top_links) == 1
            assert report.top_links[0]['base_domain'] == 'go2.video'
            
            # Verify HTML mentions the filter
            assert 'go2.video' in report.html_content
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, service):
        """Test error handling in various scenarios"""
        report_date = date.today() - timedelta(days=1)
        
        # Test database connection error
        with patch.object(service.db, 'collection') as mock_collection:
            mock_collection.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception) as exc_info:
                await service.generate_daily_report(
                    report_date=report_date,
                    user_uid='user123'
                )
            
            assert "Database connection failed" in str(exc_info.value)
        
        # Test email sending with invalid API key
        report = DailyReportResponse(
            date=datetime.utcnow(),
            total_clicks=0,
            total_links=0,
            top_links=[],
            geographic_breakdown=GeographicStats(),
            device_breakdown={},
            referrer_breakdown={},
            html_content='<html><body>Empty Report</body></html>'
        )
        
        # Test with no API key
        service.sendgrid_api_key = None
        result = await service.send_report_email(
            report=report,
            recipients=['test@example.com']
        )
        assert result is False
        
        # Test with SendGrid error
        with patch('sendgrid.SendGridAPIClient') as mock_sg_client:
            mock_sg = Mock()
            mock_sg.send.side_effect = Exception("SendGrid API error")
            mock_sg_client.return_value = mock_sg
            
            service.sendgrid_api_key = 'test_key'
            result = await service.send_report_email(
                report=report,
                recipients=['test@example.com']
            )
            assert result is False
    
    def test_html_template_comprehensive(self, service):
        """Test HTML template with comprehensive data"""
        report_date = date.today() - timedelta(days=1)
        
        # Create comprehensive test data
        top_links = [
            {
                'code': 'viral1',
                'long_url': 'https://youtube.com/watch?v=viral-video-with-very-long-title-that-should-be-truncated',
                'base_domain': 'go2.video',
                'clicks': 1000
            },
            {
                'code': 'tool1',
                'long_url': 'https://github.com/popular/repository',
                'base_domain': 'go2.tools',
                'clicks': 500
            },
            {
                'code': 'review1',
                'long_url': 'https://amazon.com/product/reviews',
                'base_domain': 'go2.reviews',
                'clicks': 250
            }
        ]
        
        geographic_stats = GeographicStats(
            countries={
                'United States': 800,
                'Canada': 300,
                'United Kingdom': 200,
                'Germany': 150,
                'France': 100,
                'Australia': 75,
                'Japan': 50,
                'Brazil': 40,
                'India': 30,
                'Mexico': 25
            },
            cities={
                'New York, United States': 300,
                'Toronto, Canada': 200,
                'London, United Kingdom': 150,
                'Berlin, Germany': 100,
                'Paris, France': 80
            },
            regions={
                'New York, United States': 300,
                'Ontario, Canada': 200,
                'England, United Kingdom': 150,
                'Berlin, Germany': 100,
                'Île-de-France, France': 80
            }
        )
        
        device_breakdown = {
            'desktop': 900,
            'mobile': 700,
            'tablet': 150,
            'unknown': 20
        }
        
        referrer_breakdown = {
            'google.com': 600,
            'Direct': 400,
            'twitter.com': 300,
            'facebook.com': 200,
            'reddit.com': 150,
            'linkedin.com': 100,
            'youtube.com': 75,
            'github.com': 50,
            'stackoverflow.com': 25,
            'Unknown': 20
        }
        
        html_content = service._generate_html_report(
            report_date=report_date,
            total_clicks=1770,
            total_links=3,
            top_links=top_links,
            geographic_stats=geographic_stats,
            device_breakdown=device_breakdown,
            referrer_breakdown=referrer_breakdown
        )
        
        # Verify comprehensive HTML structure
        assert isinstance(html_content, str)
        assert len(html_content) > 5000  # Should be substantial
        assert '<!DOCTYPE html>' in html_content
        assert 'Daily Analytics Report' in html_content
        
        # Verify all top links are included
        assert 'viral1' in html_content
        assert 'go2.video' in html_content
        assert 'go2.tools' in html_content
        assert 'go2.reviews' in html_content
        
        # Verify geographic data
        assert 'United States' in html_content
        assert 'Canada' in html_content
        assert 'United Kingdom' in html_content
        
        # Verify device data (capitalized in template)
        assert 'Desktop' in html_content or 'desktop' in html_content
        assert 'Mobile' in html_content or 'mobile' in html_content
        
        # Verify referrer data
        assert 'google.com' in html_content
        assert 'Direct' in html_content
        assert 'twitter.com' in html_content
        
        # Verify metrics
        assert '1,770' in html_content or '1770' in html_content  # Total clicks
        assert '590' in html_content  # Average clicks per link (1770/3)
        
        # Verify URL truncation for long URLs
        assert '...' in html_content  # Long URL should be truncated
        
        # Verify proper HTML structure
        assert '<html' in html_content
        assert '</html>' in html_content
        assert '<head>' in html_content
        assert '<body>' in html_content
        assert 'charset="UTF-8"' in html_content