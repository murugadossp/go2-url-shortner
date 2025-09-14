"""
Analytics service for click tracking and geolocation.
Handles click logging, IP geolocation, and analytics data aggregation.
"""

import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import requests
import user_agents

from ..models.analytics import ClickDocument, LocationData, LinkStats, GeographicStats
from ..services.firebase_service import firebase_service
from google.cloud import firestore

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for handling click analytics and geolocation"""
    
    def __init__(self, ip_geolocation_api_key: Optional[str] = None):
        self.ip_geolocation_api_key = ip_geolocation_api_key
        self.db = firebase_service.db
    
    def hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy compliance"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    def parse_user_agent(self, user_agent: str) -> Dict[str, Optional[str]]:
        """Parse user agent string to extract device, browser, and OS info"""
        try:
            ua = user_agents.parse(user_agent)
            
            # Determine device type
            if ua.is_mobile:
                device_type = 'mobile'
            elif ua.is_tablet:
                device_type = 'tablet'
            elif ua.is_pc:
                device_type = 'desktop'
            else:
                device_type = 'unknown'
            
            return {
                'device_type': device_type,
                'browser': ua.browser.family if ua.browser.family else None,
                'os': ua.os.family if ua.os.family else None
            }
        except Exception as e:
            logger.warning(f"Failed to parse user agent: {e}")
            return {
                'device_type': 'unknown',
                'browser': None,
                'os': None
            }
    
    async def get_location_from_ip(self, ip: str) -> LocationData:
        """Get geographic location from IP address using ipapi.co"""
        try:
            # Skip private/local IPs
            if self._is_private_ip(ip):
                return LocationData()
            
            # Use ipapi.co free service (1000 requests/month)
            response = requests.get(
                f"https://ipapi.co/{ip}/json/",
                timeout=5,
                headers={'User-Agent': 'Go2 URL Shortener/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle rate limiting or errors
                if 'error' in data:
                    logger.warning(f"IP geolocation error: {data.get('reason', 'Unknown error')}")
                    return LocationData()
                
                return LocationData(
                    country=data.get('country_name'),
                    country_code=data.get('country_code'),
                    region=data.get('region'),
                    city=data.get('city'),
                    timezone=data.get('timezone'),
                    latitude=data.get('latitude'),
                    longitude=data.get('longitude')
                )
            else:
                logger.warning(f"IP geolocation API returned status {response.status_code}")
                return LocationData()
                
        except requests.RequestException as e:
            logger.warning(f"Failed to get location for IP {ip}: {e}")
            return LocationData()
        except Exception as e:
            logger.error(f"Unexpected error in IP geolocation: {e}")
            return LocationData()
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP address is private/local"""
        private_patterns = [
            r'^127\.',           # Loopback
            r'^10\.',            # Private Class A
            r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # Private Class B
            r'^192\.168\.',      # Private Class C
            r'^::1$',            # IPv6 loopback
            r'^fc00:',           # IPv6 private
            r'^fe80:',           # IPv6 link-local
        ]
        
        for pattern in private_patterns:
            if re.match(pattern, ip):
                return True
        return False
    
    async def log_click(
        self,
        code: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> None:
        """Log a click event with analytics data"""
        try:
            # Hash IP for privacy
            ip_hash = self.hash_ip(ip) if ip else None
            
            # Parse user agent
            ua_data = self.parse_user_agent(user_agent) if user_agent else {
                'device_type': 'unknown',
                'browser': None,
                'os': None
            }
            
            # Get location data
            location = await self.get_location_from_ip(ip) if ip else LocationData()
            
            # Create click document
            click_doc = ClickDocument(
                ts=datetime.utcnow(),
                ip_hash=ip_hash,
                ua=user_agent,
                referrer=referrer,
                location=location,
                device_type=ua_data['device_type'],
                browser=ua_data['browser'],
                os=ua_data['os']
            )
            
            # Save to Firestore clicks subcollection
            clicks_ref = self.db.collection('links').document(code).collection('clicks')
            clicks_ref.add(click_doc.model_dump())
            
            logger.info(f"Logged click for {code} from {location.country or 'Unknown'}")
            
        except Exception as e:
            logger.error(f"Failed to log click for {code}: {e}")
            # Don't raise exception - click logging shouldn't break redirects
    
    async def get_stats(self, code: str, period: str = '7d') -> LinkStats:
        """Get analytics statistics for a link with enhanced time-series data"""
        try:
            # Calculate date range
            now = datetime.utcnow()
            if period == '7d':
                start_date = now - timedelta(days=7)
            elif period == '30d':
                start_date = now - timedelta(days=30)
            else:  # 'all'
                start_date = datetime(2020, 1, 1)  # Far in the past
            
            # Query clicks
            from google.cloud.firestore import FieldFilter
            clicks_ref = self.db.collection('links').document(code).collection('clicks')
            query = clicks_ref.where(filter=FieldFilter('ts', '>=', start_date)).order_by('ts')
            
            clicks = []
            for doc in query.stream():
                clicks.append(doc.to_dict())
            
            # Initialize stats with proper time-series structure
            stats = LinkStats()
            stats.total_clicks = len(clicks)
            
            # Initialize clicks_by_day with zeros for the entire period
            if period != 'all':
                days = 7 if period == '7d' else 30
                for i in range(days):
                    date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
                    stats.clicks_by_day[date] = 0
            
            if not clicks:
                return stats
            
            # Process clicks
            referrers = {}
            devices = {}
            browsers = {}
            operating_systems = {}
            countries = {}
            cities = {}
            regions = {}
            last_clicked = None
            hourly_distribution = {}  # Track clicks by hour of day
            
            for click in clicks:
                # Parse timestamp
                ts = click.get('ts')
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                
                if not last_clicked or ts > last_clicked:
                    last_clicked = ts
                
                # Group by day (overwrite zero if we have actual data)
                day_key = ts.strftime('%Y-%m-%d')
                stats.clicks_by_day[day_key] = stats.clicks_by_day.get(day_key, 0) + 1
                
                # Track hourly distribution
                hour_key = ts.strftime('%H')
                hourly_distribution[hour_key] = hourly_distribution.get(hour_key, 0) + 1
                
                # Count referrers with better parsing
                referrer = click.get('referrer')
                if referrer:
                    try:
                        domain = urlparse(referrer).netloc
                        # Clean up common referrer domains
                        if domain.startswith('www.'):
                            domain = domain[4:]
                        referrers[domain] = referrers.get(domain, 0) + 1
                    except:
                        referrers['Unknown'] = referrers.get('Unknown', 0) + 1
                else:
                    referrers['Direct'] = referrers.get('Direct', 0) + 1
                
                # Count devices, browsers, and OS separately
                device = click.get('device_type', 'unknown')
                devices[device] = devices.get(device, 0) + 1
                
                browser = click.get('browser')
                if browser:
                    browsers[browser] = browsers.get(browser, 0) + 1
                
                os = click.get('os')
                if os:
                    operating_systems[os] = operating_systems.get(os, 0) + 1
                
                # Count geographic data with better handling
                location = click.get('location', {})
                if location.get('country'):
                    country = location['country']
                    countries[country] = countries.get(country, 0) + 1
                    
                    # Also track city with country context for better analytics
                    if location.get('city'):
                        city = f"{location['city']}, {country}"
                        cities[city] = cities.get(city, 0) + 1
                    
                    if location.get('region'):
                        region = f"{location['region']}, {country}"
                        regions[region] = regions.get(region, 0) + 1
            
            # Sort and limit top items with enhanced data
            stats.top_referrers = dict(sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:10])
            stats.top_devices = dict(sorted(devices.items(), key=lambda x: x[1], reverse=True)[:10])
            stats.last_clicked = last_clicked
            
            # Add enhanced analytics data
            stats.geographic_stats = GeographicStats(
                countries=dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)[:15]),
                cities=dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:15]),
                regions=dict(sorted(regions.items(), key=lambda x: x[1], reverse=True)[:15])
            )
            
            # Store additional analytics in a custom field (if needed for frontend)
            if hasattr(stats, 'additional_stats'):
                stats.additional_stats = {
                    'top_browsers': dict(sorted(browsers.items(), key=lambda x: x[1], reverse=True)[:10]),
                    'top_operating_systems': dict(sorted(operating_systems.items(), key=lambda x: x[1], reverse=True)[:10]),
                    'hourly_distribution': hourly_distribution
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats for {code}: {e}")
            return LinkStats()  # Return empty stats on error
    
    async def get_aggregated_stats(self, codes: List[str], period: str = '30d') -> LinkStats:
        """Get aggregated analytics statistics for multiple links"""
        try:
            aggregated_stats = LinkStats()
            all_clicks_by_day = {}
            all_referrers = {}
            all_devices = {}
            all_countries = {}
            all_cities = {}
            all_regions = {}
            latest_click = None
            
            for code in codes:
                try:
                    stats = await self.get_stats(code, period)
                    aggregated_stats.total_clicks += stats.total_clicks
                    
                    # Aggregate daily clicks
                    for date, clicks in stats.clicks_by_day.items():
                        all_clicks_by_day[date] = all_clicks_by_day.get(date, 0) + clicks
                    
                    # Aggregate referrers
                    for referrer, count in stats.top_referrers.items():
                        all_referrers[referrer] = all_referrers.get(referrer, 0) + count
                    
                    # Aggregate devices
                    for device, count in stats.top_devices.items():
                        all_devices[device] = all_devices.get(device, 0) + count
                    
                    # Aggregate geographic data
                    for country, count in stats.geographic_stats.countries.items():
                        all_countries[country] = all_countries.get(country, 0) + count
                    
                    for city, count in stats.geographic_stats.cities.items():
                        all_cities[city] = all_cities.get(city, 0) + count
                    
                    for region, count in stats.geographic_stats.regions.items():
                        all_regions[region] = all_regions.get(region, 0) + count
                    
                    # Track latest click
                    if stats.last_clicked and (not latest_click or stats.last_clicked > latest_click):
                        latest_click = stats.last_clicked
                        
                except Exception as e:
                    logger.warning(f"Failed to get stats for link {code}: {e}")
                    continue
            
            # Set aggregated data
            aggregated_stats.clicks_by_day = all_clicks_by_day
            aggregated_stats.top_referrers = dict(sorted(all_referrers.items(), key=lambda x: x[1], reverse=True)[:10])
            aggregated_stats.top_devices = dict(sorted(all_devices.items(), key=lambda x: x[1], reverse=True)[:10])
            aggregated_stats.last_clicked = latest_click
            
            aggregated_stats.geographic_stats = GeographicStats(
                countries=dict(sorted(all_countries.items(), key=lambda x: x[1], reverse=True)[:15]),
                cities=dict(sorted(all_cities.items(), key=lambda x: x[1], reverse=True)[:15]),
                regions=dict(sorted(all_regions.items(), key=lambda x: x[1], reverse=True)[:15])
            )
            
            return aggregated_stats
            
        except Exception as e:
            logger.error(f"Failed to get aggregated stats: {e}")
            return LinkStats()

    async def export_data(self, code: str, format: str = 'json', period: str = '30d') -> bytes:
        """Export analytics data in specified format"""
        try:
            stats = await self.get_stats(code, period)
            
            if format == 'json':
                import json
                return json.dumps(stats.model_dump(), indent=2, default=str).encode('utf-8')
            
            elif format == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write summary metrics
                writer.writerow(['Analytics Summary'])
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Total Clicks', stats.total_clicks])
                writer.writerow(['Last Clicked', stats.last_clicked.isoformat() if stats.last_clicked else 'Never'])
                writer.writerow(['Period', period])
                writer.writerow(['Export Date', datetime.utcnow().isoformat()])
                
                # Daily clicks time series
                writer.writerow([])
                writer.writerow(['Daily Clicks Time Series'])
                writer.writerow(['Date', 'Clicks'])
                # Sort dates for proper time series
                sorted_dates = sorted(stats.clicks_by_day.items())
                for date, clicks in sorted_dates:
                    writer.writerow([date, clicks])
                
                # Top referrers with percentages
                writer.writerow([])
                writer.writerow(['Top Traffic Sources'])
                writer.writerow(['Referrer', 'Clicks', 'Percentage'])
                for referrer, clicks in stats.top_referrers.items():
                    percentage = round((clicks / stats.total_clicks) * 100, 2) if stats.total_clicks > 0 else 0
                    writer.writerow([referrer, clicks, f"{percentage}%"])
                
                # Device analytics
                writer.writerow([])
                writer.writerow(['Device Analytics'])
                writer.writerow(['Device Type', 'Clicks', 'Percentage'])
                for device, clicks in stats.top_devices.items():
                    percentage = round((clicks / stats.total_clicks) * 100, 2) if stats.total_clicks > 0 else 0
                    writer.writerow([device, clicks, f"{percentage}%"])
                
                # Geographic analytics - Countries
                writer.writerow([])
                writer.writerow(['Geographic Analytics - Countries'])
                writer.writerow(['Country', 'Clicks', 'Percentage'])
                for country, clicks in stats.geographic_stats.countries.items():
                    percentage = round((clicks / stats.total_clicks) * 100, 2) if stats.total_clicks > 0 else 0
                    writer.writerow([country, clicks, f"{percentage}%"])
                
                # Geographic analytics - Cities
                if stats.geographic_stats.cities:
                    writer.writerow([])
                    writer.writerow(['Geographic Analytics - Cities'])
                    writer.writerow(['City', 'Clicks', 'Percentage'])
                    for city, clicks in stats.geographic_stats.cities.items():
                        percentage = round((clicks / stats.total_clicks) * 100, 2) if stats.total_clicks > 0 else 0
                        writer.writerow([city, clicks, f"{percentage}%"])
                
                # Geographic analytics - Regions
                if stats.geographic_stats.regions:
                    writer.writerow([])
                    writer.writerow(['Geographic Analytics - Regions'])
                    writer.writerow(['Region', 'Clicks', 'Percentage'])
                    for region, clicks in stats.geographic_stats.regions.items():
                        percentage = round((clicks / stats.total_clicks) * 100, 2) if stats.total_clicks > 0 else 0
                        writer.writerow([region, clicks, f"{percentage}%"])
                
                return output.getvalue().encode('utf-8')
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export data for {code}: {e}")
            raise


# Global analytics service instance
analytics_service = AnalyticsService()