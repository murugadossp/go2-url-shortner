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

app = FastAPI(
    title="Contextual URL Shortener API",
    description="A production-ready contextual URL shortener with safety measures and analytics",
    version="1.0.0"
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",  # Alternative localhost
        "https://go2.video",
        "https://go2.tools", 
        "https://go2.reviews",
        # Add your frontend domain if different
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)