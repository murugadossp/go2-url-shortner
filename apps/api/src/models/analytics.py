from datetime import datetime
from typing import Optional, Dict, Literal, Any
from pydantic import BaseModel, Field, ConfigDict, field_serializer

DeviceType = Literal['mobile', 'desktop', 'tablet', 'unknown']


class LocationData(BaseModel):
    """Geographic location data"""
    country: Optional[str] = None
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class ClickDocument(BaseModel):
    """Firestore document model for clicks"""
    ts: datetime
    ip_hash: Optional[str] = None
    ua: Optional[str] = None
    referrer: Optional[str] = None
    location: LocationData = Field(default_factory=LocationData)
    device_type: DeviceType = 'unknown'
    browser: Optional[str] = None
    os: Optional[str] = None

    @field_serializer('ts')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class GeographicStats(BaseModel):
    """Geographic statistics for analytics"""
    countries: Dict[str, int] = Field(default_factory=dict)
    cities: Dict[str, int] = Field(default_factory=dict)
    regions: Dict[str, int] = Field(default_factory=dict)


class LinkStats(BaseModel):
    """Link statistics response model"""
    total_clicks: int = 0
    clicks_by_day: Dict[str, int] = Field(default_factory=dict)
    top_referrers: Dict[str, int] = Field(default_factory=dict)
    top_devices: Dict[str, int] = Field(default_factory=dict)
    last_clicked: Optional[datetime] = None
    geographic_stats: GeographicStats = Field(default_factory=GeographicStats)

    @field_serializer('last_clicked')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class AnalyticsExportRequest(BaseModel):
    """Request model for analytics data export"""
    format: Literal['json', 'csv'] = 'json'
    period: Literal['7d', '30d', 'all'] = '30d'


class DailyReportRequest(BaseModel):
    """Request model for daily report generation"""
    date: datetime
    domain_filter: Optional[str] = None
    email_recipients: Optional[list[str]] = None

    @field_serializer('date')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class DailyReportResponse(BaseModel):
    """Response model for daily report"""
    date: datetime
    total_clicks: int
    total_links: int
    top_links: list[Dict[str, Any]] = Field(default_factory=list)
    geographic_breakdown: GeographicStats = Field(default_factory=GeographicStats)
    device_breakdown: Dict[str, int] = Field(default_factory=dict)
    referrer_breakdown: Dict[str, int] = Field(default_factory=dict)
    html_content: Optional[str] = None

    @field_serializer('date')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()