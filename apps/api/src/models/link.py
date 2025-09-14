from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict, field_serializer
import re

# Type aliases for better readability
BaseDomain = Literal['go2.video', 'go2.reviews', 'go2.tools']
PlanType = Literal['free', 'paid']
DeviceType = Literal['mobile', 'desktop', 'tablet', 'unknown']


class LinkMetadata(BaseModel):
    """Metadata for a link"""
    title: Optional[str] = None
    host: Optional[str] = None
    favicon_url: Optional[HttpUrl] = None


class LinkDocument(BaseModel):
    """Firestore document model for links"""
    long_url: HttpUrl
    base_domain: BaseDomain
    owner_uid: Optional[str] = None
    password_hash: Optional[str] = None
    expires_at: Optional[datetime] = None
    disabled: bool = False
    created_at: datetime
    created_by_ip: Optional[str] = None
    metadata: LinkMetadata = Field(default_factory=LinkMetadata)
    plan_type: PlanType = 'free'
    is_custom_code: bool = False

    @field_serializer('created_at', 'expires_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class CreateLinkRequest(BaseModel):
    """Request model for creating a new link"""
    long_url: HttpUrl
    base_domain: BaseDomain
    custom_code: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=4, max_length=100)
    expires_at: Optional[datetime] = None

    @field_validator('custom_code')
    @classmethod
    def validate_custom_code(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Custom code can only contain letters, numbers, hyphens, and underscores')
        return v

    @field_validator('expires_at')
    @classmethod
    def validate_expires_at(cls, v):
        if v is not None:
            # Handle both timezone-aware and timezone-naive datetimes
            from datetime import timezone
            now = datetime.now(timezone.utc)
            
            # Convert input to UTC if it has timezone info
            if v.tzinfo is not None:
                v_utc = v.astimezone(timezone.utc)
            else:
                # If input is timezone-naive, assume it's UTC
                v_utc = v.replace(tzinfo=timezone.utc)
            
            if v_utc <= now:
                raise ValueError('Expiration date must be in the future')
        return v


class CreateLinkResponse(BaseModel):
    """Response model for link creation"""
    short_url: str
    code: str
    qr_url: str
    long_url: str
    base_domain: BaseDomain
    expires_at: Optional[datetime] = None

    @field_serializer('expires_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class UpdateLinkRequest(BaseModel):
    """Request model for updating a link"""
    disabled: Optional[bool] = None
    expires_at: Optional[datetime] = None
    password: Optional[str] = Field(None, min_length=4, max_length=100)

    @field_validator('expires_at')
    @classmethod
    def validate_expires_at(cls, v):
        if v is not None:
            # Handle both timezone-aware and timezone-naive datetimes
            from datetime import timezone
            now = datetime.now(timezone.utc)
            
            # Convert input to UTC if it has timezone info
            if v.tzinfo is not None:
                v_utc = v.astimezone(timezone.utc)
            else:
                # If input is timezone-naive, assume it's UTC
                v_utc = v.replace(tzinfo=timezone.utc)
            
            if v_utc <= now:
                raise ValueError('Expiration date must be in the future')
        return v


class LinkStatsRequest(BaseModel):
    """Request model for link statistics"""
    period: Literal['7d', '30d', 'all'] = '7d'


class LinkListResponse(BaseModel):
    """Response model for link listing"""
    code: str
    long_url: str
    base_domain: BaseDomain
    created_at: datetime
    disabled: bool
    expires_at: Optional[datetime] = None
    total_clicks: int = 0
    owner_uid: Optional[str] = None
    is_custom_code: bool = False

    @field_serializer('created_at', 'expires_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None