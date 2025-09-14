"""
Custom exception classes and error handling utilities for the API.
"""
from typing import Any, Optional, Dict, List
from fastapi import HTTPException, status
from pydantic import BaseModel


class APIError(Exception):
    """Base API error class"""
    def __init__(
        self, 
        code: str, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Any] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ValidationError(APIError):
    """Validation error for input data"""
    def __init__(self, message: str = "Invalid input data", details: Optional[Any] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class SafetyError(APIError):
    """Safety violation error"""
    def __init__(self, message: str, reasons: Optional[List[str]] = None):
        super().__init__(
            code="SAFETY_VIOLATION",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details={"reasons": reasons or []}
        )


class ResourceNotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} '{identifier}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier}
        )


class ResourceConflictError(APIError):
    """Resource conflict error"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            code="RESOURCE_CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class AuthenticationError(APIError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(APIError):
    """Authorization error"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            code="AUTHORIZATION_ERROR",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class RateLimitError(APIError):
    """Rate limit exceeded error"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after}
        )


class ExternalServiceError(APIError):
    """External service error"""
    def __init__(self, service: str, message: str = "External service unavailable"):
        super().__init__(
            code="EXTERNAL_SERVICE_ERROR",
            message=f"{service}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service}
        )


class PlanLimitError(APIError):
    """Plan limit exceeded error"""
    def __init__(self, limit_type: str, current_plan: str, limit: int):
        super().__init__(
            code="PLAN_LIMIT_EXCEEDED",
            message=f"{limit_type} limit exceeded for {current_plan} plan",
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            details={
                "limit_type": limit_type,
                "current_plan": current_plan,
                "limit": limit
            }
        )


# Error response models
class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: ErrorDetail


class ValidationErrorDetail(BaseModel):
    """Validation error detail with field-specific errors"""
    code: str = "VALIDATION_ERROR"
    message: str = "Invalid input data"
    details: List[Dict[str, Any]] = []


class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    error: ValidationErrorDetail