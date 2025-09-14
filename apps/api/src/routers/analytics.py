"""
Analytics router for advanced analytics endpoints.
Provides detailed analytics, aggregations, and reporting functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import Response

from ..models.analytics import (
    LinkStats, AnalyticsExportRequest, GeographicStats,
    DailyReportRequest, DailyReportResponse
)
from ..models.api import ErrorResponse
from ..services.analytics_service import analytics_service
from ..services.firebase_service import firebase_service
from ..utils.auth import get_current_user, require_auth, require_admin, get_user_id
from google.cloud.firestore import FieldFilter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/stats/{code}", response_model=LinkStats)
async def get_link_analytics(
    code: str,
    period: str = Query('7d', pattern='^(7d|30d|all)$'),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Get comprehensive analytics statistics for a link.
    Supports time-series data, geographic breakdowns, and device analytics.
    """
    try:
        # Get link document to check permissions
        link_ref = firebase_service.db.collection('links').document(code)
        link_doc = link_ref.get()
        
        if not link_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        link_data = link_doc.to_dict()
        
        # Check permissions for private links
        owner_uid = link_data.get('owner_uid')
        if owner_uid:  # Private link
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required to view private link statistics"
                )
            
            is_owner = get_user_id(current_user) == owner_uid
            is_admin = current_user.get('admin', False)
            
            if not (is_owner or is_admin):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
        
        # Get comprehensive statistics
        stats = await analytics_service.get_stats(code, period)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics for {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.get("/geographic/{code}", response_model=GeographicStats)
async def get_geographic_analytics(
    code: str,
    period: str = Query('30d', pattern='^(7d|30d|all)$'),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Get detailed geographic analytics for a link.
    Includes country, region, and city breakdowns.
    """
    try:
        # Check permissions (same as main analytics)
        link_ref = firebase_service.db.collection('links').document(code)
        link_doc = link_ref.get()
        
        if not link_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        link_data = link_doc.to_dict()
        owner_uid = link_data.get('owner_uid')
        
        if owner_uid and current_user:
            is_owner = get_user_id(current_user) == owner_uid
            is_admin = current_user.get('admin', False)
            
            if not (is_owner or is_admin):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied"
                )
        elif owner_uid and not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get full stats and return geographic portion
        stats = await analytics_service.get_stats(code, period)
        return stats.geographic_stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting geographic analytics for {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve geographic analytics"
        )


@router.get("/export/{code}")
async def export_analytics_data(
    code: str,
    format: str = Query('json', pattern='^(json|csv)$'),
    period: str = Query('30d', pattern='^(7d|30d|all)$'),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Export comprehensive analytics data in JSON or CSV format.
    Requires owner or admin access.
    """
    try:
        # Get link document to check permissions
        link_ref = firebase_service.db.collection('links').document(code)
        link_doc = link_ref.get()
        
        if not link_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        
        link_data = link_doc.to_dict()
        
        # Check permissions (owner or admin only for exports)
        owner_uid = link_data.get('owner_uid')
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        is_owner = get_user_id(current_user) == owner_uid
        is_admin = current_user.get('admin', False)
        
        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        # Export data
        try:
            data = await analytics_service.export_data(code, format, period)
            if not data:
                # Handle case where export returns empty data
                if format == 'json':
                    data = b'{"total_clicks": 0, "message": "No analytics data available for this link"}'
                else:  # csv
                    data = b'Message,No analytics data available for this link\nTotal Clicks,0\n'
        except Exception as export_error:
            logger.error(f"Analytics export failed for {code}: {export_error}")
            # Return a meaningful error response instead of letting it bubble up as 500
            if format == 'json':
                data = b'{"error": "Failed to export analytics data", "total_clicks": 0}'
            else:  # csv
                data = b'Error,Failed to export analytics data\nTotal Clicks,0\n'
        
        # Set appropriate content type and filename
        content_type = 'application/json' if format == 'json' else 'text/csv'
        filename = f"{code}_analytics_{period}.{format}"
        
        return Response(
            content=data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting analytics for {code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analytics data"
        )


@router.get("/summary")
async def get_user_analytics_summary(
    current_user: Dict[str, Any] = Depends(require_auth),
    period: str = Query('30d', pattern='^(7d|30d|all)$')
):
    """
    Get analytics summary for all user's links.
    Provides aggregated statistics across all owned links.
    """
    try:
        uid = get_user_id(current_user)
        
        # Get user's links
        links_ref = firebase_service.db.collection('links')
        query = links_ref.where(filter=FieldFilter('owner_uid', '==', uid))
        
        total_clicks = 0
        total_links = 0
        countries = {}
        devices = {}
        referrers = {}
        
        for doc in query.stream():
            total_links += 1
            try:
                stats = await analytics_service.get_stats(doc.id, period)
                total_clicks += stats.total_clicks
                
                # Aggregate geographic data
                for country, count in stats.geographic_stats.countries.items():
                    countries[country] = countries.get(country, 0) + count
                
                # Aggregate device data
                for device, count in stats.top_devices.items():
                    devices[device] = devices.get(device, 0) + count
                
                # Aggregate referrer data
                for referrer, count in stats.top_referrers.items():
                    referrers[referrer] = referrers.get(referrer, 0) + count
                    
            except Exception as e:
                logger.warning(f"Failed to get stats for link {doc.id}: {e}")
                continue
        
        return {
            "total_links": total_links,
            "total_clicks": total_clicks,
            "period": period,
            "top_countries": dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_devices": dict(sorted(devices.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_referrers": dict(sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:10])
        }
        
    except Exception as e:
        logger.error(f"Error getting user analytics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics summary"
        )


@router.get("/admin/overview")
async def get_admin_analytics_overview(
    current_user: Dict[str, Any] = Depends(require_admin),
    period: str = Query('30d', pattern='^(7d|30d|all)$')
):
    """
    Get system-wide analytics overview (admin only).
    Provides aggregated statistics across all links in the system.
    """
    try:
        # Calculate date range
        now = datetime.utcnow()
        if period == '7d':
            start_date = now - timedelta(days=7)
        elif period == '30d':
            start_date = now - timedelta(days=30)
        else:  # 'all'
            start_date = datetime(2020, 1, 1)
        
        # Get all links
        links_ref = firebase_service.db.collection('links')
        
        total_links = 0
        total_clicks = 0
        active_links = 0  # Links with clicks in period
        countries = {}
        devices = {}
        referrers = {}
        daily_clicks = {}
        
        for doc in links_ref.stream():
            total_links += 1
            try:
                stats = await analytics_service.get_stats(doc.id, period)
                if stats.total_clicks > 0:
                    active_links += 1
                    total_clicks += stats.total_clicks
                    
                    # Aggregate data
                    for country, count in stats.geographic_stats.countries.items():
                        countries[country] = countries.get(country, 0) + count
                    
                    for device, count in stats.top_devices.items():
                        devices[device] = devices.get(device, 0) + count
                    
                    for referrer, count in stats.top_referrers.items():
                        referrers[referrer] = referrers.get(referrer, 0) + count
                    
                    for date, count in stats.clicks_by_day.items():
                        daily_clicks[date] = daily_clicks.get(date, 0) + count
                        
            except Exception as e:
                logger.warning(f"Failed to get stats for link {doc.id}: {e}")
                continue
        
        return {
            "period": period,
            "total_links": total_links,
            "active_links": active_links,
            "total_clicks": total_clicks,
            "clicks_by_day": daily_clicks,
            "top_countries": dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_devices": dict(sorted(devices.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_referrers": dict(sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:10])
        }
        
    except Exception as e:
        logger.error(f"Error getting admin analytics overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin analytics overview"
        )


@router.post("/admin/daily-report", response_model=DailyReportResponse)
async def generate_daily_report(
    request: DailyReportRequest,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Generate a daily analytics report (admin only).
    Aggregates click data for a specific date with optional domain filtering.
    """
    try:
        report_date = request.date.date()
        
        # Query links with optional domain filter
        links_ref = firebase_service.db.collection('links')
        if request.domain_filter:
            query = links_ref.where(filter=FieldFilter('base_domain', '==', request.domain_filter))
        else:
            query = links_ref
        
        total_clicks = 0
        total_links = 0
        top_links = []
        countries = {}
        devices = {}
        referrers = {}
        
        for doc in query.stream():
            link_data = doc.to_dict()
            total_links += 1
            
            # Get clicks for the specific date
            clicks_ref = doc.reference.collection('clicks')
            start_datetime = datetime.combine(report_date, datetime.min.time())
            end_datetime = datetime.combine(report_date, datetime.max.time())
            
            date_query = clicks_ref.where(
                filter=FieldFilter('ts', '>=', start_datetime)
            ).where(
                filter=FieldFilter('ts', '<=', end_datetime)
            )
            
            link_clicks = 0
            for click_doc in date_query.stream():
                click_data = click_doc.to_dict()
                link_clicks += 1
                total_clicks += 1
                
                # Aggregate data
                location = click_data.get('location', {})
                if location.get('country'):
                    countries[location['country']] = countries.get(location['country'], 0) + 1
                
                device = click_data.get('device_type', 'unknown')
                devices[device] = devices.get(device, 0) + 1
                
                referrer = click_data.get('referrer')
                if referrer:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(referrer).netloc
                        referrers[domain] = referrers.get(domain, 0) + 1
                    except:
                        referrers['Unknown'] = referrers.get('Unknown', 0) + 1
                else:
                    referrers['Direct'] = referrers.get('Direct', 0) + 1
            
            if link_clicks > 0:
                top_links.append({
                    'code': doc.id,
                    'long_url': link_data.get('long_url', ''),
                    'base_domain': link_data.get('base_domain', ''),
                    'clicks': link_clicks
                })
        
        # Sort top links by clicks
        top_links.sort(key=lambda x: x['clicks'], reverse=True)
        top_links = top_links[:10]  # Top 10 links
        
        # Create geographic stats
        geographic_stats = GeographicStats(
            countries=dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]),
            cities={},  # Not aggregated in daily report
            regions={}  # Not aggregated in daily report
        )
        
        return DailyReportResponse(
            date=request.date,
            total_clicks=total_clicks,
            total_links=total_links,
            top_links=top_links,
            geographic_breakdown=geographic_stats,
            device_breakdown=dict(sorted(devices.items(), key=lambda x: x[1], reverse=True)[:10]),
            referrer_breakdown=dict(sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:10])
        )
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate daily report"
        )