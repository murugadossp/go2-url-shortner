"""
Safety service for URL validation and content filtering.
Implements Google Safe Browsing API integration and domain blacklisting.
"""

import os
import json
import logging
from typing import List, Optional
from urllib.parse import urlparse
import requests

logger = logging.getLogger(__name__)

class SafetyError(Exception):
    """Exception raised when URL fails safety validation"""
    def __init__(self, message: str, reason: str = "unknown"):
        self.message = message
        self.reason = reason
        super().__init__(self.message)

class SafetyService:
    """Service for validating URL safety using multiple checks"""
    
    def __init__(self, safe_browsing_api_key: Optional[str] = None, blacklist_file_path: Optional[str] = None):
        self.safe_browsing_api_key = safe_browsing_api_key
        self.blacklist_file_path = blacklist_file_path
        self.domain_blacklist = self._load_domain_blacklist()
        
    def _load_domain_blacklist(self) -> List[str]:
        """Load domain blacklist from file"""
        if not self.blacklist_file_path or not os.path.exists(self.blacklist_file_path):
            # Default blacklist of known malicious domains
            return [
                'malware.com',
                'phishing.com',
                'spam.com',
                # Add more as needed
            ]
        
        try:
            with open(self.blacklist_file_path, 'r') as f:
                data = json.load(f)
                return data.get('domains', [])
        except Exception as e:
            logger.warning(f"Failed to load blacklist file: {e}")
            return []
    
    def _check_domain_blacklist(self, url: str) -> None:
        """Check if URL domain is in blacklist"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix for comparison
            if domain.startswith('www.'):
                domain = domain[4:]
            
            if domain in self.domain_blacklist:
                raise SafetyError(f"Domain {domain} is blacklisted", "blacklisted_domain")
                
        except SafetyError:
            raise
        except Exception as e:
            logger.warning(f"Error checking domain blacklist: {e}")
    
    def _check_safe_browsing(self, url: str) -> None:
        """Check URL against Google Safe Browsing API"""
        if not self.safe_browsing_api_key:
            logger.info("Safe Browsing API key not configured, skipping check")
            return
        
        try:
            api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self.safe_browsing_api_key}"
            
            payload = {
                "client": {
                    "clientId": "contextual-url-shortener",
                    "clientVersion": "1.0.0"
                },
                "threatInfo": {
                    "threatTypes": [
                        "MALWARE",
                        "SOCIAL_ENGINEERING",
                        "UNWANTED_SOFTWARE",
                        "POTENTIALLY_HARMFUL_APPLICATION"
                    ],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}]
                }
            }
            
            response = requests.post(api_url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('matches'):
                threat_type = result['matches'][0].get('threatType', 'UNKNOWN')
                raise SafetyError(f"URL flagged by Safe Browsing: {threat_type}", "safe_browsing")
                
        except SafetyError:
            raise
        except Exception as e:
            logger.warning(f"Error checking Safe Browsing API: {e}")
    
    def _check_url_format(self, url: str) -> None:
        """Basic URL format validation"""
        try:
            parsed = urlparse(url)
            
            # Check for valid scheme
            if parsed.scheme not in ['http', 'https']:
                raise SafetyError("URL must use HTTP or HTTPS protocol", "invalid_scheme")
            
            # Check for valid domain
            if not parsed.netloc:
                raise SafetyError("URL must have a valid domain", "invalid_domain")
            
            # Check for suspicious patterns
            suspicious_patterns = [
                'javascript:',
                'data:',
                'file:',
                'ftp:',
            ]
            
            url_lower = url.lower()
            for pattern in suspicious_patterns:
                if pattern in url_lower:
                    raise SafetyError(f"URL contains suspicious pattern: {pattern}", "suspicious_pattern")
                    
        except SafetyError:
            raise
        except Exception as e:
            raise SafetyError(f"Invalid URL format: {e}", "format_error")
    
    def validate_url(self, url: str) -> None:
        """
        Validate URL safety using multiple checks.
        Raises SafetyError if URL fails any validation.
        """
        logger.info(f"Validating URL safety: {url}")
        
        # 1. Basic format validation
        self._check_url_format(url)
        
        # 2. Domain blacklist check
        self._check_domain_blacklist(url)
        
        # 3. Google Safe Browsing check
        self._check_safe_browsing(url)
        
        logger.info(f"URL passed safety validation: {url}")
    
    def is_safe(self, url: str) -> bool:
        """
        Check if URL is safe (non-throwing version).
        Returns True if safe, False if unsafe.
        """
        try:
            self.validate_url(url)
            return True
        except SafetyError:
            return False
        except Exception as e:
            logger.error(f"Unexpected error in safety check: {e}")
            return False  # Fail safe