"""
Rate limiting middleware for API protection.
"""
import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.exceptions import RateLimitError, ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window algorithm"""
    
    def __init__(self):
        # Store request timestamps for each client
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.last_cleanup = time.time()
    
    def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Client identifier (IP, user ID, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > 60:  # Cleanup every minute
            self._cleanup_old_entries(now - window * 2)
            self.last_cleanup = now
        
        # Get request history for this key
        request_times = self.requests[key]
        
        # Remove requests outside the window
        while request_times and request_times[0] <= now - window:
            request_times.popleft()
        
        # Check if limit is exceeded
        if len(request_times) >= limit:
            # Calculate retry after time
            oldest_request = request_times[0]
            retry_after = int(oldest_request + window - now) + 1
            return False, retry_after
        
        # Add current request
        request_times.append(now)
        return True, None
    
    def _cleanup_old_entries(self, cutoff_time: float):
        """Remove old entries to prevent memory leaks"""
        keys_to_remove = []
        for key, request_times in self.requests.items():
            # Remove old requests
            while request_times and request_times[0] <= cutoff_time:
                request_times.popleft()
            
            # Remove empty entries
            if not request_times:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.requests[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, rate_limiter: Optional[InMemoryRateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or InMemoryRateLimiter()
        
        # Rate limit configurations
        self.rate_limits = {
            # Global limits per IP
            "global": {"limit": 100, "window": 60},  # 100 requests per minute
            
            # Endpoint-specific limits
            "/api/links/shorten": {"limit": 10, "window": 60},  # 10 link creations per minute
            "/api/qr/": {"limit": 30, "window": 60},  # 30 QR generations per minute
            "/health": {"limit": 10, "window": 10},  # 10 health checks per 10 seconds
            
            # Authentication endpoints
            "/api/users/": {"limit": 20, "window": 60},  # 20 user operations per minute
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limiting(request):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check global rate limit
        is_allowed, retry_after = self._check_rate_limit(
            client_id, 
            "global", 
            self.rate_limits["global"]
        )
        
        if not is_allowed:
            return self._create_rate_limit_response(retry_after)
        
        # Check endpoint-specific rate limit
        endpoint_limit = self._get_endpoint_limit(request.url.path)
        if endpoint_limit:
            endpoint_key = f"{client_id}:{request.url.path}"
            is_allowed, retry_after = self._check_rate_limit(
                endpoint_key,
                request.url.path,
                endpoint_limit
            )
            
            if not is_allowed:
                return self._create_rate_limit_response(retry_after)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, client_id)
        
        return response
    
    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Check if rate limiting should be skipped for this request"""
        # Skip for static files, health checks in development, etc.
        skip_paths = ["/docs", "/redoc", "/openapi.json"]
        return any(request.url.path.startswith(path) for path in skip_paths)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from auth token first
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in case of multiple proxies
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def _get_endpoint_limit(self, path: str) -> Optional[Dict]:
        """Get rate limit configuration for specific endpoint"""
        for endpoint_pattern, limit_config in self.rate_limits.items():
            if endpoint_pattern != "global" and path.startswith(endpoint_pattern):
                return limit_config
        return None
    
    def _check_rate_limit(self, key: str, endpoint: str, config: Dict) -> Tuple[bool, Optional[int]]:
        """Check rate limit for given key and endpoint"""
        is_allowed, retry_after = self.rate_limiter.is_allowed(
            key, 
            config["limit"], 
            config["window"]
        )
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {key} on {endpoint}",
                extra={
                    "client_key": key,
                    "endpoint": endpoint,
                    "limit": config["limit"],
                    "window": config["window"],
                    "retry_after": retry_after
                }
            )
        
        return is_allowed, retry_after
    
    def _create_rate_limit_response(self, retry_after: Optional[int]) -> JSONResponse:
        """Create rate limit exceeded response"""
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="RATE_LIMIT_EXCEEDED",
                    message="Rate limit exceeded. Please try again later.",
                    details={"retry_after": retry_after}
                )
            ).model_dump(),
            headers={"Retry-After": str(retry_after)} if retry_after else {}
        )
    
    def _add_rate_limit_headers(self, response: Response, client_id: str):
        """Add rate limit information to response headers"""
        # Get current usage for global limit
        global_config = self.rate_limits["global"]
        request_times = self.rate_limiter.requests.get(client_id, deque())
        
        # Count requests in current window
        now = time.time()
        current_requests = sum(
            1 for req_time in request_times 
            if req_time > now - global_config["window"]
        )
        
        response.headers["X-RateLimit-Limit"] = str(global_config["limit"])
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, global_config["limit"] - current_requests)
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(now + global_config["window"])
        )