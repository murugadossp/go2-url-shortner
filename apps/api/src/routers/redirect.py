"""
Redirect router for handling short URL redirects.
Handles /{code} redirects with click tracking, password protection, and error handling.
Uses composite document IDs to support same codes across different domains.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from passlib.hash import bcrypt

from ..services.firebase_service import firebase_service
from ..services.analytics_service import analytics_service
from ..utils.domain_utils import get_base_domain_from_request, get_composite_document_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["redirect"])


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.verify(password, hashed)


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request headers"""
    # Check for forwarded headers first (for reverse proxies)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fall back to direct connection IP
    if request.client:
        return request.client.host
    
    return None





def get_password_form_html(code: str, error: Optional[str] = None) -> str:
    """Generate HTML form for password-protected links"""
    error_html = f'<div class="error">{error}</div>' if error else ''
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Required - Go2 URL Shortener</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 400px;
                margin: 100px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
                font-size: 24px;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            label {{
                display: block;
                margin-bottom: 5px;
                color: #555;
                font-weight: 500;
            }}
            input[type="password"] {{
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
                box-sizing: border-box;
            }}
            button {{
                background-color: #007bff;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
            }}
            button:hover {{
                background-color: #0056b3;
            }}
            .error {{
                color: #dc3545;
                margin-bottom: 15px;
                padding: 10px;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
            }}
            .info {{
                color: #6c757d;
                font-size: 14px;
                margin-top: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔒 Password Required</h1>
            {error_html}
            <p>This link is password protected. Please enter the password to continue.</p>
            
            <form method="post" action="/{code}">
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required autofocus>
                </div>
                <button type="submit">Access Link</button>
            </form>
            
            <div class="info">
                Powered by <strong>Go2 URL Shortener</strong>
            </div>
        </div>
    </body>
    </html>
    """


def get_error_page_html(title: str, message: str, status_code: int) -> str:
    """Generate HTML error page"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Go2 URL Shortener</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 500px;
                margin: 100px auto;
                padding: 20px;
                background-color: #f5f5f5;
                text-align: center;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .status-code {{
                font-size: 72px;
                font-weight: bold;
                color: #dc3545;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
                font-size: 28px;
            }}
            p {{
                color: #666;
                font-size: 16px;
                line-height: 1.5;
                margin-bottom: 30px;
            }}
            .home-link {{
                display: inline-block;
                background-color: #007bff;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: 500;
            }}
            .home-link:hover {{
                background-color: #0056b3;
            }}
            .info {{
                color: #6c757d;
                font-size: 14px;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status-code">{status_code}</div>
            <h1>{title}</h1>
            <p>{message}</p>
            <a href="/" class="home-link">Go to Homepage</a>
            <div class="info">
                Powered by <strong>Go2 URL Shortener</strong>
            </div>
        </div>
    </body>
    </html>
    """


@router.get("/{code}")
async def redirect_to_long_url(code: str, request: Request):
    """
    Handle GET requests to /{code} - redirect to original URL or show password form.
    Implements click tracking, password protection, and error handling.
    Uses composite document IDs to support same codes across different domains.
    """
    try:
        # Extract domain from request host header and create composite document ID
        host = request.headers.get('host', '')
        base_domain = get_base_domain_from_host(host)
        document_id = get_composite_document_id(base_domain, code)
        
        logger.info(f"Redirect request: {host}/{code} -> document_id: {document_id}")
        
        # Get link document using composite ID
        link_ref = firebase_service.db.collection('links').document(document_id)
        link_doc = link_ref.get()
        
        if not link_doc.exists:
            logger.warning(f"Link not found: {document_id}")
            return HTMLResponse(
                content=get_error_page_html(
                    "Link Not Found",
                    "The short link you're looking for doesn't exist or may have been deleted.",
                    404
                ),
                status_code=404
            )
        
        link_data = link_doc.to_dict()
        
        # Check if link is disabled
        if link_data.get('disabled', False):
            logger.info(f"Link disabled: {document_id}")
            return HTMLResponse(
                content=get_error_page_html(
                    "Link Disabled",
                    "This link has been disabled by the owner or administrator.",
                    410
                ),
                status_code=410
            )
        
        # Check if link is expired
        expires_at = link_data.get('expires_at')
        if expires_at and datetime.utcnow() > expires_at:
            logger.info(f"Link expired: {document_id}")
            return HTMLResponse(
                content=get_error_page_html(
                    "Link Expired",
                    "This link has expired and is no longer available.",
                    410
                ),
                status_code=410
            )
        
        # Check password protection
        password_hash = link_data.get('password_hash')
        if password_hash:
            # Show password form for GET requests
            return HTMLResponse(
                content=get_password_form_html(code),
                status_code=200
            )
        
        # Log click data (async, don't wait)
        client_ip = get_client_ip(request)
        user_agent = request.headers.get('User-Agent')
        referrer = request.headers.get('Referer')
        
        # Fire and forget click logging (use composite document_id)
        import asyncio
        asyncio.create_task(analytics_service.log_click(
            code=document_id,  # Use composite ID for analytics
            ip=client_ip,
            user_agent=user_agent,
            referrer=referrer
        ))
        
        logger.info(f"Redirecting {document_id} to {link_data['long_url']}")
        
        # Redirect to original URL
        return RedirectResponse(
            url=link_data['long_url'],
            status_code=status.HTTP_302_FOUND
        )
        
    except Exception as e:
        logger.error(f"Error redirecting {code}: {e}")
        return HTMLResponse(
            content=get_error_page_html(
                "Server Error",
                "An unexpected error occurred while processing your request. Please try again later.",
                500
            ),
            status_code=500
        )


@router.post("/{code}")
async def redirect_with_password(code: str, request: Request, password: str = Form(...)):
    """
    Handle POST requests to /{code} - verify password and redirect.
    Used for password-protected links.
    Uses composite document IDs to support same codes across different domains.
    """
    try:
        # Extract domain from request host header and create composite document ID
        host = request.headers.get('host', '')
        base_domain = get_base_domain_from_host(host)
        document_id = get_composite_document_id(base_domain, code)
        
        logger.info(f"Password redirect request: {host}/{code} -> document_id: {document_id}")
        
        # Get link document using composite ID
        link_ref = firebase_service.db.collection('links').document(document_id)
        link_doc = link_ref.get()
        
        if not link_doc.exists:
            logger.warning(f"Link not found: {document_id}")
            return HTMLResponse(
                content=get_error_page_html(
                    "Link Not Found",
                    "The short link you're looking for doesn't exist or may have been deleted.",
                    404
                ),
                status_code=404
            )
        
        link_data = link_doc.to_dict()
        
        # Check if link is disabled
        if link_data.get('disabled', False):
            logger.info(f"Link disabled: {document_id}")
            return HTMLResponse(
                content=get_error_page_html(
                    "Link Disabled",
                    "This link has been disabled by the owner or administrator.",
                    410
                ),
                status_code=410
            )
        
        # Check if link is expired
        expires_at = link_data.get('expires_at')
        if expires_at and datetime.utcnow() > expires_at:
            logger.info(f"Link expired: {document_id}")
            return HTMLResponse(
                content=get_error_page_html(
                    "Link Expired",
                    "This link has expired and is no longer available.",
                    410
                ),
                status_code=410
            )
        
        # Verify password
        password_hash = link_data.get('password_hash')
        if not password_hash:
            # Link is not password protected, redirect directly
            pass
        elif not verify_password(password, password_hash):
            # Wrong password, show form with error
            logger.warning(f"Wrong password for {document_id}")
            return HTMLResponse(
                content=get_password_form_html(code, "Incorrect password. Please try again."),
                status_code=401
            )
        
        # Log click data (async, don't wait)
        client_ip = get_client_ip(request)
        user_agent = request.headers.get('User-Agent')
        referrer = request.headers.get('Referer')
        
        # Fire and forget click logging (use composite document_id)
        import asyncio
        asyncio.create_task(analytics_service.log_click(
            code=document_id,  # Use composite ID for analytics
            ip=client_ip,
            user_agent=user_agent,
            referrer=referrer
        ))
        
        logger.info(f"Password verified, redirecting {document_id} to {link_data['long_url']}")
        
        # Redirect to original URL
        return RedirectResponse(
            url=link_data['long_url'],
            status_code=status.HTTP_302_FOUND
        )
        
    except Exception as e:
        logger.error(f"Error redirecting {code} with password: {e}")
        return HTMLResponse(
            content=get_error_page_html(
                "Server Error",
                "An unexpected error occurred while processing your request. Please try again later.",
                500
            ),
            status_code=500
        )