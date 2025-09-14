"""
Configuration and factory for SafetyService.
Handles environment-based configuration and service initialization.
"""

import os
from typing import Optional
from .safety_service import SafetyService


def create_safety_service() -> SafetyService:
    """
    Create and configure SafetyService instance based on environment variables.
    
    Environment variables:
    - GOOGLE_SAFE_BROWSING_API_KEY: Google Safe Browsing API key
    - DOMAIN_BLACKLIST_FILE: Path to domain blacklist JSON file
    
    Returns:
        Configured SafetyService instance
    """
    safe_browsing_api_key = os.getenv('GOOGLE_SAFE_BROWSING_API_KEY')
    blacklist_file_path = os.getenv('DOMAIN_BLACKLIST_FILE', 'config/domain_blacklist.json')
    
    return SafetyService(
        safe_browsing_api_key=safe_browsing_api_key,
        blacklist_file_path=blacklist_file_path
    )


# Global safety service instance
_safety_service: Optional[SafetyService] = None


def get_safety_service() -> SafetyService:
    """
    Get the global SafetyService instance (singleton pattern).
    
    Returns:
        SafetyService instance
    """
    global _safety_service
    if _safety_service is None:
        _safety_service = create_safety_service()
    return _safety_service