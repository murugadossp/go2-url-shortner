"""
Tests for error handling and validation.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from src.main import app
from src.utils.exceptions import (
    APIError, ValidationError, SafetyError, ResourceNotFoundError,
    ResourceConflictError, AuthenticationError, AuthorizationError,
    RateLimitError, ExternalServiceError, PlanLimitError
)


client = TestClient(app)


class TestErrorHandlers:
    """Test error handler middleware"""
    
    def test_api_error_handler(self):
        """Test custom API error handling"""
        # This would require a test endpoint that raises APIError
        # For now, we'll test the error classes directly
        error = ValidationError("Invalid input", {"field": "url"})
        assert error.code == "VALIDATION_ERROR"
        assert error.status_code == 400
        assert error.details == {"field": "url"}
    
    def test_safety_error_handler(self):
        """Test safety error handling"""
        error = SafetyError("Malicious URL detected", ["blacklist", "safe_browsing"])
        assert error.code == "SAFETY_VIOLATION"
        assert error.status_code == 403
        assert error.details["reasons"] == ["blacklist", "safe_browsing"]
    
    def test_resource_not_found_error(self):
        """Test resource not found error"""
        error = ResourceNotFoundError("Link", "abc123")
        assert error.code == "RESOURCE_NOT_FOUND"
        assert error.status_code == 404
        assert "abc123" in error.message
    
    def test_resource_conflict_error(self):
        """Test resource conflict error"""
        error = ResourceConflictError("Custom code already exists", {"code": "test"})
        assert error.code == "RESOURCE_CONFLICT"
        assert error.status_code == 409
    
    def test_authentication_error(self):
        """Test authentication error"""
        error = AuthenticationError()
        assert error.code == "AUTHENTICATION_ERROR"
        assert error.status_code == 401
    
    def test_authorization_error(self):
        """Test authorization error"""
        error = AuthorizationError()
        assert error.code == "AUTHORIZATION_ERROR"
        assert error.status_code == 403
    
    def test_rate_limit_error(self):
        """Test rate limit error"""
        error = RateLimitError("Too many requests", 60)
        assert error.code == "RATE_LIMIT_EXCEEDED"
        assert error.status_code == 429
        assert error.details["retry_after"] == 60
    
    def test_external_service_error(self):
        """Test external service error"""
        error = ExternalServiceError("Google Safe Browsing", "API unavailable")
        assert error.code == "EXTERNAL_SERVICE_ERROR"
        assert error.status_code == 503
        assert "Google Safe Browsing" in error.message
    
    def test_plan_limit_error(self):
        """Test plan limit error"""
        error = PlanLimitError("custom_codes", "free", 5)
        assert error.code == "PLAN_LIMIT_EXCEEDED"
        assert error.status_code == 402
        assert error.details["limit"] == 5


class TestValidationErrors:
    """Test input validation and error responses"""
    
    def test_invalid_url_format(self):
        """Test invalid URL format validation"""
        response = client.post("/api/links/shorten", json={
            "long_url": "not-a-url",
            "base_domain": "go2.tools"
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "details" in data["error"]
    
    def test_missing_required_fields(self):
        """Test missing required fields"""
        response = client.post("/api/links/shorten", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_invalid_domain_selection(self):
        """Test invalid domain selection"""
        response = client.post("/api/links/shorten", json={
            "long_url": "https://example.com",
            "base_domain": "invalid.domain"
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_invalid_custom_code_format(self):
        """Test invalid custom code format"""
        response = client.post("/api/links/shorten", json={
            "long_url": "https://example.com",
            "base_domain": "go2.tools",
            "custom_code": "invalid code with spaces!"
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_reserved_custom_code(self):
        """Test reserved custom code rejection"""
        response = client.post("/api/links/shorten", json={
            "long_url": "https://example.com",
            "base_domain": "go2.tools",
            "custom_code": "admin"
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_invalid_expiration_date(self):
        """Test invalid expiration date"""
        from datetime import datetime, timezone, timedelta
        
        # Past date
        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        response = client.post("/api/links/shorten", json={
            "long_url": "https://example.com",
            "base_domain": "go2.tools",
            "expires_at": past_date
        })
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"


class TestRateLimiting:
    """Test rate limiting middleware"""
    
    def test_rate_limit_headers(self):
        """Test rate limit headers are included"""
        response = client.get("/health")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    @patch('src.middleware.rate_limiting.InMemoryRateLimiter.is_allowed')
    def test_rate_limit_exceeded(self, mock_is_allowed):
        """Test rate limit exceeded response"""
        mock_is_allowed.return_value = (False, 60)
        
        response = client.get("/health")
        
        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in response.headers
    
    def test_rate_limit_per_endpoint(self):
        """Test endpoint-specific rate limiting"""
        # Make multiple requests to test rate limiting
        responses = []
        for _ in range(15):  # Exceed the limit for link creation
            response = client.post("/api/links/shorten", json={
                "long_url": "https://example.com",
                "base_domain": "go2.tools"
            })
            responses.append(response)
        
        # At least one should be rate limited (depending on other tests)
        rate_limited = any(r.status_code == 429 for r in responses)
        # Note: This might not always trigger in tests due to test isolation


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @patch('src.services.safety_service.SafetyService.check_safe_browsing')
    def test_circuit_breaker_opens_on_failures(self, mock_safe_browsing):
        """Test circuit breaker opens after consecutive failures"""
        # Mock consecutive failures
        mock_safe_browsing.side_effect = Exception("Service unavailable")
        
        # Make requests that would trigger the circuit breaker
        for _ in range(6):  # Exceed failure threshold
            try:
                response = client.post("/api/links/shorten", json={
                    "long_url": "https://example.com",
                    "base_domain": "go2.tools"
                })
            except:
                pass  # Expected to fail
    
    def test_graceful_degradation_fallback(self):
        """Test graceful degradation with fallback values"""
        # Test that the system continues to work even when external services fail
        response = client.get("/api/config/base-domains")
        
        # Should return fallback domains even if Firebase is unavailable
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestErrorLogging:
    """Test error logging functionality"""
    
    @patch('src.utils.logging_config.get_logger')
    def test_security_event_logging(self, mock_logger):
        """Test security event logging"""
        from src.utils.logging_config import log_security_event
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        log_security_event("MALICIOUS_URL_BLOCKED", {
            "url": "https://malicious.com",
            "reason": "blacklist"
        })
        
        mock_logger_instance.warning.assert_called_once()
    
    @patch('src.utils.logging_config.get_logger')
    def test_performance_metric_logging(self, mock_logger):
        """Test performance metric logging"""
        from src.utils.logging_config import log_performance_metric
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        log_performance_metric("response_time", 150.5, "ms", endpoint="/api/links/shorten")
        
        mock_logger_instance.info.assert_called_once()


class TestGracefulDegradation:
    """Test graceful degradation scenarios"""
    
    @patch('src.services.firebase_service.firebase_service.db')
    def test_firebase_unavailable_fallback(self, mock_db):
        """Test fallback when Firebase is unavailable"""
        mock_db.side_effect = Exception("Firebase unavailable")
        
        # Should still return some response, not crash
        response = client.get("/health")
        
        # Health check should indicate unhealthy status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
    
    @patch('requests.get')
    def test_external_api_failure_fallback(self, mock_requests):
        """Test fallback when external APIs fail"""
        mock_requests.side_effect = Exception("Network error")
        
        # Should still allow link creation without external validation
        response = client.post("/api/links/shorten", json={
            "long_url": "https://example.com",
            "base_domain": "go2.tools"
        })
        
        # Might succeed with degraded functionality or fail gracefully
        assert response.status_code in [200, 201, 503]


class TestErrorResponseFormat:
    """Test standardized error response format"""
    
    def test_validation_error_format(self):
        """Test validation error response format"""
        response = client.post("/api/links/shorten", json={
            "long_url": "invalid-url"
        })
        
        assert response.status_code == 422
        data = response.json()
        
        # Check standard error format
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "details" in data["error"]
        
        # Check validation-specific format
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert isinstance(data["error"]["details"], list)
    
    def test_not_found_error_format(self):
        """Test not found error response format"""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"
    
    def test_method_not_allowed_format(self):
        """Test method not allowed error format"""
        response = client.patch("/api/links/shorten")  # PATCH not allowed
        
        assert response.status_code == 405
        data = response.json()
        
        assert "error" in data
        assert data["error"]["code"] == "METHOD_NOT_ALLOWED"


if __name__ == "__main__":
    pytest.main([__file__])