from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging first
from .utils.logging_config import setup_logging, RequestLoggingMiddleware
setup_logging()

import logging
logger = logging.getLogger(__name__)

# Initialize Firebase service (this will set up the connection)
from .services.firebase_service import firebase_service

# Determine if we're in production
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production'

app = FastAPI(
    title="Go2 URL Shortener API",
    description="Production-ready contextual URL shortener with analytics and safety measures",
    version="1.0.0",
    # Disable docs in production for security
    docs_url="/docs" if not IS_PRODUCTION else None,
    redoc_url="/redoc" if not IS_PRODUCTION else None,
    openapi_url="/openapi.json" if not IS_PRODUCTION else None,
)

# Setup error handlers
from .utils.error_handlers import setup_error_handlers
setup_error_handlers(app)

# Add rate limiting middleware
from .middleware.rate_limiting import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Define health endpoints before routers to avoid conflicts with catch-all routes
@app.get("/")
async def root():
    return {"message": "Contextual URL Shortener API"}

@app.get("/health")
async def health_check():
    """Health check endpoint that also verifies Firebase connection"""
    try:
        # Test Firebase connection
        firebase_service.db.collection('config').limit(1).get()
        return {
            "status": "healthy",
            "firebase": "connected",
            "timestamp": os.getenv("TIMESTAMP", "unknown")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "firebase": "disconnected",
            "error": str(e)
        }

# Import and register routers
from .routers import links, redirect, config, users, qr, analytics, hooks
app.include_router(links.router)
app.include_router(redirect.router)
app.include_router(config.router)
app.include_router(users.router)
app.include_router(qr.router)
app.include_router(analytics.router)
app.include_router(hooks.router)

# Configure CORS based on environment
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
if not IS_PRODUCTION:
    # Add development origins
    cors_origins.extend([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting Go2 URL Shortener API in {ENVIRONMENT} mode")
    logger.info(f"CORS origins: {cors_origins}")
    
    # Verify Firebase connection on startup
    try:
        firebase_service.db.collection('config').limit(1).get()
        logger.info("Firebase connection verified")
    except Exception as e:
        logger.error(f"Firebase connection failed: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Go2 URL Shortener API")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info" if IS_PRODUCTION else "debug"
    )