from typing import Any, Optional, Generic, TypeVar, List, Dict
from pydantic import BaseModel, Field, validator
from datetime import datetime

T = TypeVar('T')


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: 'ErrorDetail'


class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str
    message: str
    details: Optional[Any] = None


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response model"""
    data: T
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = "healthy"
    timestamp: str
    version: str = "1.0.0"


class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    error: 'ValidationErrorDetail'


class ValidationErrorDetail(BaseModel):
    """Validation error detail model"""
    code: str = "VALIDATION_ERROR"
    message: str = "Invalid input data"
    details: List[Dict[str, Any]] = []


class FieldValidationError(BaseModel):
    """Individual field validation error"""
    field: str
    message: str
    type: str
    input: Optional[Any] = None


class RateLimitInfo(BaseModel):
    """Rate limit information"""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None


# Enhanced validation models
class URLValidationRequest(BaseModel):
    """Request model for URL validation"""
    url: str = Field(..., min_length=1, max_length=2048, description="URL to validate")
    
    @validator('url')
    def validate_url_format(cls, v):
        import re
        from urllib.parse import urlparse
        
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        
        # Basic URL format validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError("Invalid URL format. Must be a valid HTTP or HTTPS URL")
        
        # Parse URL to check components
        try:
            parsed = urlparse(v)
            if not parsed.netloc:
                raise ValueError("URL must have a valid domain")
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("URL must use HTTP or HTTPS protocol")
        except Exception:
            raise ValueError("Invalid URL format")
        
        return v.strip()


class CustomCodeValidationRequest(BaseModel):
    """Request model for custom code validation"""
    code: str = Field(..., min_length=1, max_length=50, description="Custom code to validate")
    
    @validator('code')
    def validate_custom_code(cls, v):
        import re
        
        if not v or not v.strip():
            raise ValueError("Custom code cannot be empty")
        
        # Allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Custom code can only contain letters, numbers, hyphens, and underscores")
        
        # Reserved codes
        reserved_codes = {
            'api', 'admin', 'www', 'app', 'dashboard', 'login', 'logout', 
            'signup', 'register', 'health', 'status', 'docs', 'redoc',
            'qr', 'stats', 'analytics', 'config', 'settings'
        }
        
        if v.lower() in reserved_codes:
            raise ValueError(f"'{v}' is a reserved code and cannot be used")
        
        return v.strip()


class PasswordValidationRequest(BaseModel):
    """Request model for password validation"""
    password: str = Field(..., min_length=1, max_length=128, description="Password to validate")
    
    @validator('password')
    def validate_password(cls, v):
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
        
        if len(v) < 4:
            raise ValueError("Password must be at least 4 characters long")
        
        if len(v) > 128:
            raise ValueError("Password cannot be longer than 128 characters")
        
        return v


class ExpirationValidationRequest(BaseModel):
    """Request model for expiration date validation"""
    expires_at: datetime = Field(..., description="Expiration date and time")
    
    @validator('expires_at')
    def validate_expiration(cls, v):
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        
        if v <= now:
            raise ValueError("Expiration date must be in the future")
        
        # Maximum expiration: 10 years from now
        max_expiration = now.replace(year=now.year + 10)
        if v > max_expiration:
            raise ValueError("Expiration date cannot be more than 10 years in the future")
        
        return v


class DomainValidationRequest(BaseModel):
    """Request model for domain validation"""
    domain: str = Field(..., min_length=1, max_length=253, description="Domain to validate")
    
    @validator('domain')
    def validate_domain(cls, v):
        import re
        
        if not v or not v.strip():
            raise ValueError("Domain cannot be empty")
        
        # Basic domain format validation
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        
        if not domain_pattern.match(v):
            raise ValueError("Invalid domain format")
        
        return v.strip().lower()


# Update forward references
ErrorResponse.model_rebuild()
ValidationErrorResponse.model_rebuild()