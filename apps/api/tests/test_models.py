"""
Unit tests for Pydantic data models.
Tests validation, serialization, and deserialization of all models.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.models.link import (
    LinkDocument, LinkMetadata, CreateLinkRequest, CreateLinkResponse,
    UpdateLinkRequest, LinkStatsRequest, LinkListResponse
)
from src.models.user import (
    UserDocument, UserProfileResponse, UpdateUserRequest, PlanUpgradeRequest
)
from src.models.analytics import (
    ClickDocument, LocationData, GeographicStats, LinkStats,
    AnalyticsExportRequest, DailyReportRequest, DailyReportResponse
)
from src.models.config import (
    ConfigDocument, SafetySettings, PlanLimits, BaseDomainsResponse,
    UpdateConfigRequest
)
from src.models.api import (
    ErrorResponse, ErrorDetail, SuccessResponse, HealthCheckResponse,
    ValidationErrorResponse, ValidationErrorDetail
)


class TestLinkModels:
    """Test cases for link-related models"""
    
    def test_link_metadata_valid(self):
        """Test valid LinkMetadata creation"""
        metadata = LinkMetadata(
            title="Test Title",
            host="example.com",
            favicon_url="https://example.com/favicon.ico"
        )
        assert metadata.title == "Test Title"
        assert metadata.host == "example.com"
        assert str(metadata.favicon_url) == "https://example.com/favicon.ico"
    
    def test_link_metadata_optional_fields(self):
        """Test LinkMetadata with optional fields"""
        metadata = LinkMetadata()
        assert metadata.title is None
        assert metadata.host is None
        assert metadata.favicon_url is None
    
    def test_link_document_valid(self):
        """Test valid LinkDocument creation"""
        now = datetime.now()
        link = LinkDocument(
            long_url="https://example.com/very/long/url",
            base_domain="go2.video",
            owner_uid="user123",
            password_hash="hashed_password",
            expires_at=now + timedelta(days=30),
            disabled=False,
            created_at=now,
            created_by_ip="192.168.1.1",
            metadata=LinkMetadata(title="Test"),
            plan_type="free",
            is_custom_code=True
        )
        assert "https://example.com/very/long/url" in str(link.long_url)
        assert link.base_domain == "go2.video"
        assert link.owner_uid == "user123"
        assert link.plan_type == "free"
        assert link.is_custom_code is True
    
    def test_link_document_defaults(self):
        """Test LinkDocument with default values"""
        now = datetime.now()
        link = LinkDocument(
            long_url="https://example.com",
            base_domain="go2.tools",
            created_at=now
        )
        assert link.disabled is False
        assert link.plan_type == "free"
        assert link.is_custom_code is False
        assert link.owner_uid is None
    
    def test_create_link_request_valid(self):
        """Test valid CreateLinkRequest"""
        future_date = datetime.now() + timedelta(days=30)
        request = CreateLinkRequest(
            long_url="https://example.com",
            base_domain="go2.reviews",
            custom_code="my-code",
            password="secret123",
            expires_at=future_date
        )
        assert str(request.long_url) == "https://example.com/"
        assert request.base_domain == "go2.reviews"
        assert request.custom_code == "my-code"
    
    def test_create_link_request_invalid_url(self):
        """Test CreateLinkRequest with invalid URL"""
        with pytest.raises(ValidationError) as exc_info:
            CreateLinkRequest(
                long_url="not-a-url",
                base_domain="go2.video"
            )
        assert "url" in str(exc_info.value).lower()
    
    def test_create_link_request_invalid_custom_code(self):
        """Test CreateLinkRequest with invalid custom code"""
        with pytest.raises(ValidationError) as exc_info:
            CreateLinkRequest(
                long_url="https://example.com",
                base_domain="go2.video",
                custom_code="ab"  # Too short
            )
        assert "at least 3" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            CreateLinkRequest(
                long_url="https://example.com",
                base_domain="go2.video",
                custom_code="invalid@code"  # Invalid characters
            )
        assert "letters, numbers, hyphens, and underscores" in str(exc_info.value)
    
    def test_create_link_request_past_expiry(self):
        """Test CreateLinkRequest with past expiration date"""
        past_date = datetime.now() - timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            CreateLinkRequest(
                long_url="https://example.com",
                base_domain="go2.video",
                expires_at=past_date
            )
        assert "future" in str(exc_info.value)
    
    def test_create_link_response_serialization(self):
        """Test CreateLinkResponse JSON serialization"""
        future_date = datetime.now() + timedelta(days=30)
        response = CreateLinkResponse(
            short_url="https://go2.video/abc123",
            code="abc123",
            qr_url="https://api.example.com/qr/abc123",
            long_url="https://example.com",
            base_domain="go2.video",
            expires_at=future_date
        )
        json_data = response.model_dump()
        assert json_data["short_url"] == "https://go2.video/abc123"
        assert json_data["code"] == "abc123"
        assert isinstance(json_data["expires_at"], str)  # Now serialized as ISO string


class TestUserModels:
    """Test cases for user-related models"""
    
    def test_user_document_valid(self):
        """Test valid UserDocument creation"""
        now = datetime.now()
        user = UserDocument(
            email="test@example.com",
            display_name="Test User",
            plan_type="paid",
            custom_codes_used=5,
            custom_codes_reset_date=now,
            created_at=now,
            last_login=now,
            is_admin=True
        )
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.plan_type == "paid"
        assert user.custom_codes_used == 5
        assert user.is_admin is True
    
    def test_user_document_defaults(self):
        """Test UserDocument with default values"""
        now = datetime.now()
        user = UserDocument(
            email="test@example.com",
            display_name="Test User",
            custom_codes_reset_date=now,
            created_at=now,
            last_login=now
        )
        assert user.plan_type == "free"
        assert user.custom_codes_used == 0
        assert user.is_admin is False
    
    def test_user_document_invalid_email(self):
        """Test UserDocument with invalid email"""
        now = datetime.now()
        with pytest.raises(ValidationError) as exc_info:
            UserDocument(
                email="invalid-email",
                display_name="Test User",
                custom_codes_reset_date=now,
                created_at=now,
                last_login=now
            )
        assert "email" in str(exc_info.value).lower()
    
    def test_user_document_empty_display_name(self):
        """Test UserDocument with empty display name"""
        now = datetime.now()
        with pytest.raises(ValidationError) as exc_info:
            UserDocument(
                email="test@example.com",
                display_name="",
                custom_codes_reset_date=now,
                created_at=now,
                last_login=now
            )
        assert "at least 1" in str(exc_info.value)
    
    def test_user_profile_response(self):
        """Test UserProfileResponse model"""
        now = datetime.now()
        profile = UserProfileResponse(
            email="test@example.com",
            display_name="Test User",
            plan_type="free",
            custom_codes_used=3,
            custom_codes_remaining=2,
            custom_codes_reset_date=now,
            created_at=now,
            is_admin=False
        )
        assert profile.custom_codes_remaining == 2
        assert profile.plan_type == "free"


class TestAnalyticsModels:
    """Test cases for analytics-related models"""
    
    def test_location_data_valid(self):
        """Test valid LocationData creation"""
        location = LocationData(
            country="United States",
            country_code="US",
            region="California",
            city="San Francisco",
            timezone="America/Los_Angeles",
            latitude=37.7749,
            longitude=-122.4194
        )
        assert location.country == "United States"
        assert location.country_code == "US"
        assert location.latitude == 37.7749
        assert location.longitude == -122.4194
    
    def test_location_data_invalid_coordinates(self):
        """Test LocationData with invalid coordinates"""
        with pytest.raises(ValidationError):
            LocationData(latitude=91.0)  # Invalid latitude
        
        with pytest.raises(ValidationError):
            LocationData(longitude=181.0)  # Invalid longitude
    
    def test_location_data_invalid_country_code(self):
        """Test LocationData with invalid country code"""
        with pytest.raises(ValidationError):
            LocationData(country_code="USA")  # Should be 2 characters
    
    def test_click_document_valid(self):
        """Test valid ClickDocument creation"""
        now = datetime.now()
        location = LocationData(country="US", country_code="US")
        click = ClickDocument(
            ts=now,
            ip_hash="hashed_ip",
            ua="Mozilla/5.0...",
            referrer="https://google.com",
            location=location,
            device_type="desktop",
            browser="Chrome",
            os="Windows"
        )
        assert click.ts == now
        assert click.device_type == "desktop"
        assert click.location.country == "US"
    
    def test_click_document_defaults(self):
        """Test ClickDocument with default values"""
        now = datetime.now()
        click = ClickDocument(ts=now)
        assert click.device_type == "unknown"
        assert click.location.country is None
        assert click.ip_hash is None
    
    def test_link_stats_defaults(self):
        """Test LinkStats with default values"""
        stats = LinkStats()
        assert stats.total_clicks == 0
        assert len(stats.clicks_by_day) == 0
        assert len(stats.top_referrers) == 0
        assert stats.last_clicked is None
    
    def test_daily_report_request_valid(self):
        """Test valid DailyReportRequest"""
        today = datetime.now().date()
        request = DailyReportRequest(
            date=datetime.combine(today, datetime.min.time()),
            domain_filter="go2.video",
            email_recipients=["admin@example.com", "user@example.com"]
        )
        assert request.domain_filter == "go2.video"
        assert len(request.email_recipients) == 2


class TestConfigModels:
    """Test cases for configuration models"""
    
    def test_safety_settings_defaults(self):
        """Test SafetySettings with default values"""
        settings = SafetySettings()
        assert settings.enable_safe_browsing is True
        assert len(settings.blacklist_domains) == 0
        assert len(settings.blacklist_keywords) == 0
    
    def test_plan_limits_defaults(self):
        """Test PlanLimits with default values"""
        limits = PlanLimits()
        assert limits.free["custom_codes"] == 5
        assert limits.paid["custom_codes"] == 100
    
    def test_config_document_defaults(self):
        """Test ConfigDocument with default values"""
        config = ConfigDocument()
        assert len(config.base_domains) == 3
        assert "go2.video" in config.base_domains
        assert "go2.reviews" in config.base_domains
        assert "go2.tools" in config.base_domains
        assert config.safety_settings.enable_safe_browsing is True
        assert config.plan_limits.free["custom_codes"] == 5
    
    def test_base_domains_response(self):
        """Test BaseDomainsResponse model"""
        response = BaseDomainsResponse(
            domains=["go2.video", "go2.reviews"],
            suggestions={"youtube.com": "go2.video"}
        )
        assert len(response.domains) == 2
        assert response.suggestions["youtube.com"] == "go2.video"


class TestApiModels:
    """Test cases for API response models"""
    
    def test_error_response(self):
        """Test ErrorResponse model"""
        error = ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid input",
                details={"field": "long_url", "issue": "Invalid URL"}
            )
        )
        assert error.error.code == "VALIDATION_ERROR"
        assert error.error.message == "Invalid input"
        assert error.error.details["field"] == "long_url"
    
    def test_success_response(self):
        """Test SuccessResponse model"""
        response = SuccessResponse(
            data={"result": "success"},
            message="Operation completed"
        )
        assert response.data["result"] == "success"
        assert response.message == "Operation completed"
    
    def test_health_check_response(self):
        """Test HealthCheckResponse model"""
        health = HealthCheckResponse(
            status="healthy",
            timestamp="2024-01-01T00:00:00Z"
        )
        assert health.status == "healthy"
        assert health.version == "1.0.0"
    
    def test_validation_error_response(self):
        """Test ValidationErrorResponse model"""
        error = ValidationErrorResponse(
            error=ValidationErrorDetail(
                details=[
                    {"field": "long_url", "message": "Invalid URL"},
                    {"field": "custom_code", "message": "Too short"}
                ]
            )
        )
        assert error.error.code == "VALIDATION_ERROR"
        assert len(error.error.details) == 2


if __name__ == "__main__":
    pytest.main([__file__])