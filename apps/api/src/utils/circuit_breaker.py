"""
Circuit breaker pattern for external service resilience.
"""
import time
import logging
from typing import Callable, Any, Optional, Dict
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: int = 30  # Request timeout in seconds


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_requests: int = 0
    total_failures: int = 0


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.stats = CircuitBreakerStats()
        self._lock = False  # Simple lock for thread safety
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self._lock:
            # Simple spinlock - in production, use proper async locks
            while self._lock:
                await asyncio.sleep(0.001)
        
        self._lock = True
        try:
            # Check if circuit should be opened
            self._update_state()
            
            if self.stats.state == CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker {self.name} is OPEN, rejecting request",
                    extra={
                        "circuit_breaker": self.name,
                        "state": self.stats.state.value,
                        "failure_count": self.stats.failure_count
                    }
                )
                raise CircuitBreakerError(f"Circuit breaker {self.name} is open")
            
            # Execute the function
            self.stats.total_requests += 1
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                self._record_success()
                return result
                
            except Exception as e:
                self._record_failure()
                raise
                
        finally:
            self._lock = False
    
    def _update_state(self):
        """Update circuit breaker state based on current conditions"""
        now = time.time()
        
        if self.stats.state == CircuitState.OPEN:
            # Check if we should try half-open
            if (self.stats.last_failure_time and 
                now - self.stats.last_failure_time >= self.config.recovery_timeout):
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.success_count = 0
                logger.info(
                    f"Circuit breaker {self.name} transitioning to HALF_OPEN",
                    extra={"circuit_breaker": self.name, "state": "half_open"}
                )
        
        elif self.stats.state == CircuitState.HALF_OPEN:
            # Check if we should close (enough successes)
            if self.stats.success_count >= self.config.success_threshold:
                self.stats.state = CircuitState.CLOSED
                self.stats.failure_count = 0
                logger.info(
                    f"Circuit breaker {self.name} transitioning to CLOSED",
                    extra={"circuit_breaker": self.name, "state": "closed"}
                )
    
    def _record_success(self):
        """Record a successful operation"""
        self.stats.last_success_time = time.time()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.success_count += 1
        elif self.stats.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.stats.failure_count = 0
    
    def _record_failure(self):
        """Record a failed operation"""
        self.stats.last_failure_time = time.time()
        self.stats.failure_count += 1
        self.stats.total_failures += 1
        
        # Check if we should open the circuit
        if (self.stats.state in [CircuitState.CLOSED, CircuitState.HALF_OPEN] and
            self.stats.failure_count >= self.config.failure_threshold):
            self.stats.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker {self.name} transitioning to OPEN",
                extra={
                    "circuit_breaker": self.name,
                    "state": "open",
                    "failure_count": self.stats.failure_count,
                    "threshold": self.config.failure_threshold
                }
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "total_failures": self.stats.total_failures,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    def reset(self):
        """Reset circuit breaker to closed state"""
        self.stats = CircuitBreakerStats()
        logger.info(
            f"Circuit breaker {self.name} manually reset",
            extra={"circuit_breaker": self.name, "state": "closed"}
        )


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get or create a circuit breaker"""
    if name not in _circuit_breakers:
        config = config or CircuitBreakerConfig()
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Decorator for circuit breaker protection"""
    cb = get_circuit_breaker(name, config)
    return cb


# Import asyncio at the end to avoid circular imports
import asyncio


# Fallback strategies
class FallbackStrategy:
    """Base class for fallback strategies"""
    
    async def execute(self, *args, **kwargs) -> Any:
        raise NotImplementedError


class CachedFallback(FallbackStrategy):
    """Fallback to cached data"""
    
    def __init__(self, cache_key: str, default_value: Any = None):
        self.cache_key = cache_key
        self.default_value = default_value
    
    async def execute(self, *args, **kwargs) -> Any:
        # In a real implementation, this would check a cache (Redis, etc.)
        logger.info(f"Using cached fallback for {self.cache_key}")
        return self.default_value


class DefaultValueFallback(FallbackStrategy):
    """Fallback to a default value"""
    
    def __init__(self, default_value: Any):
        self.default_value = default_value
    
    async def execute(self, *args, **kwargs) -> Any:
        logger.info(f"Using default value fallback: {self.default_value}")
        return self.default_value


class GracefulDegradation:
    """Wrapper for graceful degradation with fallback strategies"""
    
    def __init__(self, name: str, fallback: FallbackStrategy, circuit_config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.fallback = fallback
        self.circuit_breaker = get_circuit_breaker(name, circuit_config)
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with graceful degradation"""
        try:
            return await self.circuit_breaker.call(func, *args, **kwargs)
        except (CircuitBreakerError, Exception) as e:
            logger.warning(
                f"Service {self.name} failed, using fallback",
                extra={
                    "service": self.name,
                    "error": str(e),
                    "fallback_used": True
                }
            )
            return await self.fallback.execute(*args, **kwargs)