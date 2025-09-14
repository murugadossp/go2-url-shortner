"""
Logging configuration for the API.
"""
import logging
import logging.config
import os
import sys
from typing import Dict, Any
from datetime import datetime


def _serialize_for_json(obj):
    """Custom serializer for JSON that handles bytes and other non-serializable types"""
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8')
        except UnicodeDecodeError:
            return obj.hex()
    elif isinstance(obj, dict):
        return {_serialize_for_json(k): _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return str(obj)
    else:
        return str(obj)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'lineno', 'funcName', 'created', 
                'msecs', 'relativeCreated', 'thread', 'threadName', 
                'processName', 'process', 'getMessage', 'exc_info', 
                'exc_text', 'stack_info'
            }:
                # Serialize the value to handle bytes and other non-JSON types
                extra_fields[str(key)] = _serialize_for_json(value)
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        # Format as JSON-like string for easy parsing
        import json
        try:
            return json.dumps(log_entry, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # Fallback to string representation if JSON serialization fails
            return f"LOG_SERIALIZATION_ERROR: {str(e)} - {str(log_entry)}"


def setup_logging(log_level: str = None, log_format: str = None) -> None:
    """
    Setup logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Logging format ('structured' or 'simple')
    """
    # Get configuration from environment
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = log_format or os.getenv("LOG_FORMAT", "structured").lower()
    
    # Validate log level
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    # Configure formatters
    formatters = {
        "structured": {
            "()": StructuredFormatter,
        },
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    }
    
    # Configure handlers
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": log_format,
            "level": log_level
        }
    }
    
    # Add file handler if log file is specified
    log_file = os.getenv("LOG_FILE")
    if log_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": log_format,
            "level": log_level
        }
    
    # Configure root logger
    root_handlers = ["console"]
    if log_file:
        root_handlers.append("file")
    
    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "root": {
            "level": log_level,
            "handlers": root_handlers
        },
        "loggers": {
            # Application loggers
            "apps.api": {
                "level": log_level,
                "propagate": True
            },
            
            # Third-party loggers
            "uvicorn": {
                "level": "INFO",
                "propagate": True
            },
            "uvicorn.access": {
                "level": "INFO",
                "propagate": True
            },
            "fastapi": {
                "level": "INFO", 
                "propagate": True
            },
            
            # Reduce noise from verbose libraries
            "google": {
                "level": "WARNING",
                "propagate": True
            },
            "urllib3": {
                "level": "WARNING",
                "propagate": True
            },
            "requests": {
                "level": "WARNING",
                "propagate": True
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "log_level": log_level,
            "log_format": log_format,
            "log_file": log_file
        }
    )


class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests and responses"""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("apps.api.requests")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract request info
        # Convert headers from bytes tuples to string dict
        headers = {}
        for name, value in scope.get("headers", []):
            try:
                headers[name.decode('latin1')] = value.decode('latin1')
            except (UnicodeDecodeError, AttributeError):
                headers[str(name)] = str(value)
        
        request_info = {
            "method": scope["method"],
            "path": scope["path"],
            "query_string": scope["query_string"].decode() if scope["query_string"] else "",
            "headers": headers,
            "client": scope.get("client"),
        }
        
        # Start timing
        import time
        start_time = time.time()
        
        # Log request
        self.logger.info(
            f"{request_info['method']} {request_info['path']}",
            extra={
                "event": "request_start",
                "request": request_info
            }
        )
        
        # Capture response
        response_info = {"status_code": None, "headers": {}}
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_info["status_code"] = message["status"]
                # Convert response headers from bytes tuples to string dict
                response_headers = {}
                for name, value in message.get("headers", []):
                    try:
                        response_headers[name.decode('latin1')] = value.decode('latin1')
                    except (UnicodeDecodeError, AttributeError):
                        response_headers[str(name)] = str(value)
                response_info["headers"] = response_headers
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
            
            # Log successful response
            duration = time.time() - start_time
            self.logger.info(
                f"{request_info['method']} {request_info['path']} - {response_info['status_code']}",
                extra={
                    "event": "request_complete",
                    "request": request_info,
                    "response": response_info,
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
        except Exception as e:
            # Log error response
            duration = time.time() - start_time
            self.logger.error(
                f"{request_info['method']} {request_info['path']} - ERROR",
                extra={
                    "event": "request_error",
                    "request": request_info,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2)
                },
                exc_info=True
            )
            raise


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(f"apps.api.{name}")


# Security-focused logging helpers
def log_security_event(event_type: str, details: Dict[str, Any], level: str = "WARNING"):
    """Log security-related events"""
    logger = get_logger("security")
    log_method = getattr(logger, level.lower())
    
    log_method(
        f"Security event: {event_type}",
        extra={
            "event_type": event_type,
            "security_event": True,
            **details
        }
    )


def log_performance_metric(metric_name: str, value: float, unit: str = "ms", **kwargs):
    """Log performance metrics"""
    logger = get_logger("performance")
    
    logger.info(
        f"Performance metric: {metric_name}",
        extra={
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "performance_metric": True,
            **kwargs
        }
    )