"""
Domain utilities for handling multi-domain URL shortener functionality.
Provides functions for domain mapping and composite document ID creation.
"""

from typing import Optional
from fastapi import Request


def get_base_domain_from_host(host: str) -> str:
    """
    Extract base domain from request host header.
    
    Args:
        host: The host header value (e.g., 'go2.video', 'www.go2.tools')
        
    Returns:
        The base domain (go2.video, go2.tools, or go2.reviews)
    """
    host = host.lower().strip()
    
    # Map host to base domain
    domain_mapping = {
        'go2.video': 'go2.video',
        'go2.tools': 'go2.tools', 
        'go2.reviews': 'go2.reviews',
        'www.go2.video': 'go2.video',
        'www.go2.tools': 'go2.tools',
        'www.go2.reviews': 'go2.reviews',
        # Development/testing domains
        'localhost': 'go2.tools',
        '127.0.0.1': 'go2.tools',
        'localhost:3000': 'go2.tools',
        'localhost:8000': 'go2.tools',
    }
    
    return domain_mapping.get(host, 'go2.tools')  # Default fallback


def get_base_domain_from_request(request: Request) -> str:
    """
    Extract base domain from FastAPI request object.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        The base domain (go2.video, go2.tools, or go2.reviews)
    """
    host = request.headers.get('host', '')
    return get_base_domain_from_host(host)


def get_composite_document_id(base_domain: str, code: str) -> str:
    """
    Create composite document ID from domain and code.
    
    Args:
        base_domain: The base domain (go2.video, go2.tools, go2.reviews)
        code: The short code (e.g., 'abc123')
        
    Returns:
        Composite document ID (e.g., 'go2.video_abc123')
    """
    return f"{base_domain}_{code}"


def extract_code_from_document_id(document_id: str) -> tuple[str, str]:
    """
    Extract base domain and code from composite document ID.
    
    Args:
        document_id: Composite document ID (e.g., 'go2.video_abc123')
        
    Returns:
        Tuple of (base_domain, code)
    """
    if '_' not in document_id:
        # Legacy document ID, assume go2.tools
        return 'go2.tools', document_id
    
    parts = document_id.split('_', 1)
    return parts[0], parts[1]


def is_valid_base_domain(domain: str) -> bool:
    """
    Check if a domain is a valid base domain.
    
    Args:
        domain: Domain to check
        
    Returns:
        True if valid base domain, False otherwise
    """
    valid_domains = {'go2.video', 'go2.tools', 'go2.reviews'}
    return domain in valid_domains


def get_short_url(base_domain: str, code: str) -> str:
    """
    Create full short URL from base domain and code.
    
    Args:
        base_domain: The base domain
        code: The short code
        
    Returns:
        Full short URL (e.g., 'https://go2.video/abc123')
    """
    return f"https://{base_domain}/{code}"