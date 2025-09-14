"""
Daily report service for generating and sending analytics reports.
Handles report generation, HTML template rendering, and email delivery via SendGrid.
"""

import logging
import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from jinja2 import Template

from ..models.analytics import DailyReportResponse, GeographicStats
from ..services.firebase_service import firebase_service
from ..services.analytics_service import analytics_service

logger = logging.getLogger(__name__)


class DailyReportService:
    """Service for generating and sending daily analytics reports"""
    
    def __init__(self):
        self.db = firebase_service.db
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'reports@go2.tools')
        
    async def generate_daily_report(
        self,
        report_date: date,
        domain_filter: Optional[str] = None,
        user_uid: Optional[str] = None
    ) -> DailyReportResponse:
        """
        Generate comprehensive daily analytics report.
        
        Args:
            report_date: Date to generate report for
            domain_filter: Optional domain filter (e.g., 'go2.video')
            user_uid: Optional user ID to filter links by owner
            
        Returns:
            DailyReportResponse with aggregated analytics and HTML content
        """
        try:
            # Convert date to datetime range
            start_datetime = datetime.combine(report_date, datetime.min.time())
            end_datetime = datetime.combine(report_date, datetime.max.time())
            
            # Query links created on this date or with clicks on this date
            links_query = self.db.collection('links')
            
            # Apply user filter if specified
            if user_uid:
                links_query = links_query.where('owner_uid', '==', user_uid)
            
            # Apply domain filter if specified
            if domain_filter:
                links_query = links_query.where('base_domain', '==', domain_filter)
            
            # Get all links (we'll filter by date in clicks)
            links_docs = list(links_query.stream())
            
            # Initialize report data
            total_clicks = 0
            total_links = len(links_docs)
            link_performance = []
            all_countries = {}
            all_cities = {}
            all_regions = {}
            all_devices = {}
            all_referrers = {}
            
            # Process each link
            for link_doc in links_docs:
                link_data = link_doc.to_dict()
                code = link_doc.id
                
                # Query clicks for this specific date
                clicks_query = (
                    self.db.collection('links')
                    .document(code)
                    .collection('clicks')
                    .where('ts', '>=', start_datetime)
                    .where('ts', '<=', end_datetime)
                )
                
                clicks_docs = list(clicks_query.stream())
                daily_clicks = len(clicks_docs)
                
                if daily_clicks > 0:
                    total_clicks += daily_clicks
                    
                    # Add to link performance tracking
                    link_performance.append({
                        'code': code,
                        'long_url': link_data.get('long_url', ''),
                        'base_domain': link_data.get('base_domain', ''),
                        'clicks': daily_clicks,
                        'created_at': link_data.get('created_at'),
                        'owner_uid': link_data.get('owner_uid')
                    })
                    
                    # Aggregate analytics data
                    for click_doc in clicks_docs:
                        click_data = click_doc.to_dict()
                        
                        # Geographic data
                        location = click_data.get('location', {})
                        if location.get('country'):
                            country = location['country']
                            all_countries[country] = all_countries.get(country, 0) + 1
                            
                            if location.get('city'):
                                city = f"{location['city']}, {country}"
                                all_cities[city] = all_cities.get(city, 0) + 1
                            
                            if location.get('region'):
                                region = f"{location['region']}, {country}"
                                all_regions[region] = all_regions.get(region, 0) + 1
                        
                        # Device data
                        device = click_data.get('device_type', 'unknown')
                        all_devices[device] = all_devices.get(device, 0) + 1
                        
                        # Referrer data
                        referrer = click_data.get('referrer')
                        if referrer:
                            from urllib.parse import urlparse
                            try:
                                domain = urlparse(referrer).netloc
                                if domain.startswith('www.'):
                                    domain = domain[4:]
                                all_referrers[domain] = all_referrers.get(domain, 0) + 1
                            except:
                                all_referrers['Unknown'] = all_referrers.get('Unknown', 0) + 1
                        else:
                            all_referrers['Direct'] = all_referrers.get('Direct', 0) + 1
            
            # Sort and limit top performers
            top_links = sorted(link_performance, key=lambda x: x['clicks'], reverse=True)[:10]
            
            # Create geographic stats
            geographic_stats = GeographicStats(
                countries=dict(sorted(all_countries.items(), key=lambda x: x[1], reverse=True)[:10]),
                cities=dict(sorted(all_cities.items(), key=lambda x: x[1], reverse=True)[:10]),
                regions=dict(sorted(all_regions.items(), key=lambda x: x[1], reverse=True)[:10])
            )
            
            # Create device and referrer breakdowns
            device_breakdown = dict(sorted(all_devices.items(), key=lambda x: x[1], reverse=True)[:10])
            referrer_breakdown = dict(sorted(all_referrers.items(), key=lambda x: x[1], reverse=True)[:10])
            
            # Generate HTML content
            html_content = self._generate_html_report(
                report_date=report_date,
                total_clicks=total_clicks,
                total_links=total_links,
                top_links=top_links,
                geographic_stats=geographic_stats,
                device_breakdown=device_breakdown,
                referrer_breakdown=referrer_breakdown,
                domain_filter=domain_filter
            )
            
            return DailyReportResponse(
                date=datetime.combine(report_date, datetime.min.time()),
                total_clicks=total_clicks,
                total_links=total_links,
                top_links=top_links,
                geographic_breakdown=geographic_stats,
                device_breakdown=device_breakdown,
                referrer_breakdown=referrer_breakdown,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to generate daily report for {report_date}: {e}")
            raise
    
    def _generate_html_report(
        self,
        report_date: date,
        total_clicks: int,
        total_links: int,
        top_links: List[Dict[str, Any]],
        geographic_stats: GeographicStats,
        device_breakdown: Dict[str, int],
        referrer_breakdown: Dict[str, int],
        domain_filter: Optional[str] = None
    ) -> str:
        """Generate HTML content for the daily report"""
        
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Analytics Report - {{ report_date }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2.2em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid #667eea;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 0;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 5px 0 0 0;
        }
        .section {
            background: white;
            margin-bottom: 30px;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .section-header {
            background: #f8f9fa;
            padding: 20px 25px;
            border-bottom: 1px solid #e9ecef;
        }
        .section-header h2 {
            margin: 0;
            color: #495057;
            font-size: 1.3em;
        }
        .section-content {
            padding: 25px;
        }
        .top-links {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .link-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #f1f3f4;
        }
        .link-item:last-child {
            border-bottom: none;
        }
        .link-info {
            flex: 1;
        }
        .link-code {
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }
        .link-url {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
            word-break: break-all;
        }
        .link-domain {
            background: #e3f2fd;
            color: #1976d2;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-top: 5px;
            display: inline-block;
        }
        .click-count {
            background: #667eea;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
            min-width: 50px;
            text-align: center;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
        }
        .stat-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f1f3f4;
        }
        .stat-item:last-child {
            border-bottom: none;
        }
        .stat-name {
            font-weight: 500;
            color: #495057;
        }
        .stat-value {
            background: #f8f9fa;
            color: #495057;
            padding: 4px 12px;
            border-radius: 15px;
            font-weight: bold;
        }
        .no-data {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 40px 20px;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }
        .filter-info {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Daily Analytics Report</h1>
        <p>{{ report_date.strftime('%B %d, %Y') }}</p>
        {% if domain_filter %}
        <p>Filtered by domain: {{ domain_filter }}</p>
        {% endif %}
    </div>

    {% if domain_filter %}
    <div class="filter-info">
        <strong>Note:</strong> This report is filtered to show data for {{ domain_filter }} only.
    </div>
    {% endif %}

    <div class="summary">
        <div class="metric-card">
            <div class="metric-value">{{ "{:,}".format(total_clicks) }}</div>
            <div class="metric-label">Total Clicks</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{{ "{:,}".format(total_links) }}</div>
            <div class="metric-label">Active Links</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{{ "{:.1f}".format(total_clicks / total_links if total_links > 0 else 0) }}</div>
            <div class="metric-label">Avg Clicks/Link</div>
        </div>
    </div>

    {% if top_links %}
    <div class="section">
        <div class="section-header">
            <h2>🔥 Top Performing Links</h2>
        </div>
        <div class="section-content">
            <ul class="top-links">
                {% for link in top_links %}
                <li class="link-item">
                    <div class="link-info">
                        <div class="link-code">{{ link.base_domain }}/{{ link.code }}</div>
                        <div class="link-url">{{ link.long_url[:80] }}{% if link.long_url|length > 80 %}...{% endif %}</div>
                        <div class="link-domain">{{ link.base_domain }}</div>
                    </div>
                    <div class="click-count">{{ link.clicks }}</div>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>
    {% endif %}

    <div class="stats-grid">
        {% if geographic_stats.countries %}
        <div class="section">
            <div class="section-header">
                <h2>🌍 Geographic Breakdown</h2>
            </div>
            <div class="section-content">
                <ul class="stat-list">
                    {% for country, clicks in geographic_stats.countries.items() %}
                    <li class="stat-item">
                        <span class="stat-name">{{ country }}</span>
                        <span class="stat-value">{{ clicks }}</span>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        {% endif %}

        {% if device_breakdown %}
        <div class="section">
            <div class="section-header">
                <h2>📱 Device Breakdown</h2>
            </div>
            <div class="section-content">
                <ul class="stat-list">
                    {% for device, clicks in device_breakdown.items() %}
                    <li class="stat-item">
                        <span class="stat-name">{{ device.title() }}</span>
                        <span class="stat-value">{{ clicks }}</span>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        {% endif %}
    </div>

    {% if referrer_breakdown %}
    <div class="section">
        <div class="section-header">
            <h2>🔗 Traffic Sources</h2>
        </div>
        <div class="section-content">
            <ul class="stat-list">
                {% for referrer, clicks in referrer_breakdown.items() %}
                <li class="stat-item">
                    <span class="stat-name">{{ referrer }}</span>
                    <span class="stat-value">{{ clicks }}</span>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>
    {% endif %}

    {% if total_clicks == 0 %}
    <div class="section">
        <div class="section-content">
            <div class="no-data">
                📭 No clicks recorded for {{ report_date.strftime('%B %d, %Y') }}
                {% if domain_filter %}for {{ domain_filter }}{% endif %}
            </div>
        </div>
    </div>
    {% endif %}

    <div class="footer">
        <p>Generated on {{ datetime.now().strftime('%B %d, %Y at %I:%M %p UTC') }}</p>
        <p>Go2 URL Shortener Analytics</p>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(
            report_date=report_date,
            total_clicks=total_clicks,
            total_links=total_links,
            top_links=top_links,
            geographic_stats=geographic_stats,
            device_breakdown=device_breakdown,
            referrer_breakdown=referrer_breakdown,
            domain_filter=domain_filter,
            datetime=datetime
        )
    
    async def send_report_email(
        self,
        report: DailyReportResponse,
        recipients: List[str],
        user_name: str = "User"
    ) -> bool:
        """
        Send daily report via SendGrid email.
        
        Args:
            report: Generated daily report
            recipients: List of email addresses
            user_name: Name of the user for personalization
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.sendgrid_api_key:
            logger.warning("SendGrid API key not configured, skipping email")
            return False
        
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            # Create email content
            subject = f"Daily Analytics Report - {report.date.strftime('%B %d, %Y')}"
            
            # Create plain text version
            text_content = f"""
Daily Analytics Report - {report.date.strftime('%B %d, %Y')}

Summary:
- Total Clicks: {report.total_clicks:,}
- Active Links: {report.total_links:,}
- Average Clicks per Link: {report.total_clicks / report.total_links if report.total_links > 0 else 0:.1f}

Top Performing Links:
"""
            
            for i, link in enumerate(report.top_links[:5], 1):
                text_content += f"{i}. {link['base_domain']}/{link['code']} - {link['clicks']} clicks\n"
            
            if report.geographic_breakdown.countries:
                text_content += "\nTop Countries:\n"
                for country, clicks in list(report.geographic_breakdown.countries.items())[:5]:
                    text_content += f"- {country}: {clicks} clicks\n"
            
            text_content += f"\nGenerated on {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}\nGo2 URL Shortener Analytics"
            
            # Create email
            from_email = Email(self.from_email, "Go2 Analytics")
            to_emails = [To(email) for email in recipients]
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_emails,
                subject=subject,
                plain_text_content=Content("text/plain", text_content),
                html_content=Content("text/html", report.html_content)
            )
            
            # Send email
            response = sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Daily report email sent successfully to {recipients}")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send daily report email: {e}")
            return False
    
    async def test_email_configuration(
        self,
        test_recipient: str,
        user_name: str = "User"
    ) -> bool:
        """
        Test SendGrid email configuration by sending a test email.
        
        Args:
            test_recipient: Email address to send test to
            user_name: Name for personalization
            
        Returns:
            True if test email sent successfully, False otherwise
        """
        if not self.sendgrid_api_key:
            logger.warning("SendGrid API key not configured")
            return False
        
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            subject = "Go2 Analytics - Email Configuration Test"
            
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #667eea; color: white; padding: 20px; text-align: center; border-radius: 8px; }}
        .content {{ background: #f9f9f9; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .success {{ color: #28a745; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Email Configuration Test</h1>
        </div>
        <div class="content">
            <p>Hello {user_name},</p>
            <p class="success">✅ Your SendGrid email configuration is working correctly!</p>
            <p>This test email confirms that:</p>
            <ul>
                <li>SendGrid API key is valid</li>
                <li>Email delivery is functioning</li>
                <li>Daily reports will be delivered successfully</li>
            </ul>
            <p>You can now receive automated daily analytics reports.</p>
        </div>
        <div style="text-align: center; color: #666; font-size: 0.9em;">
            <p>Go2 URL Shortener Analytics</p>
        </div>
    </div>
</body>
</html>
            """
            
            text_content = f"""
Email Configuration Test

Hello {user_name},

✅ Your SendGrid email configuration is working correctly!

This test email confirms that:
- SendGrid API key is valid
- Email delivery is functioning  
- Daily reports will be delivered successfully

You can now receive automated daily analytics reports.

Go2 URL Shortener Analytics
            """
            
            from_email = Email(self.from_email, "Go2 Analytics")
            to_email = To(test_recipient)
            
            mail = Mail(
                from_email=from_email,
                to_emails=[to_email],
                subject=subject,
                plain_text_content=Content("text/plain", text_content),
                html_content=Content("text/html", html_content)
            )
            
            response = sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Test email sent successfully to {test_recipient}")
                return True
            else:
                logger.error(f"SendGrid test returned status {response.status_code}: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            return False


# Global daily report service instance
daily_report_service = DailyReportService()