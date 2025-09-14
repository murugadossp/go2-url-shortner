"""
Integration tests for SafetyService configuration and factory.
"""

import pytest
import os
import tempfile
import json
from unittest.mock import patch

from src.services.safety_config import create_safety_service, get_safety_service
from src.services.safety_service import SafetyService


class TestSafetyServiceIntegration:
    """Test SafetyService integration and configuration"""
    
    def test_create_safety_service_with_env_vars(self):
        """Test creating SafetyService with environment variables"""
        with patch.dict(os.environ, {
            'GOOGLE_SAFE_BROWSING_API_KEY': 'test_api_key',
            'DOMAIN_BLACKLIST_FILE': 'test_blacklist.json'
        }):
            service = create_safety_service()
            assert isinstance(service, SafetyService)
            assert service.safe_browsing_api_key == 'test_api_key'
            assert service.blacklist_file_path == 'test_blacklist.json'
    
    def test_create_safety_service_without_env_vars(self):
        """Test creating SafetyService without environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            service = create_safety_service()
            assert isinstance(service, SafetyService)
            assert service.safe_browsing_api_key is None
            assert service.blacklist_file_path == 'config/domain_blacklist.json'
    
    def test_get_safety_service_singleton(self):
        """Test that get_safety_service returns the same instance"""
        # Clear any existing instance
        import src.services.safety_config
        src.services.safety_config._safety_service = None
        
        service1 = get_safety_service()
        service2 = get_safety_service()
        
        assert service1 is service2
        assert isinstance(service1, SafetyService)
    
    def test_safety_service_with_real_blacklist(self):
        """Test SafetyService with actual blacklist file"""
        # Create temporary blacklist file
        blacklist_data = {
            "domains": ["test-malware.com", "test-phishing.net"],
            "keywords": ["test-scam", "test-fraud"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(blacklist_data, f)
            temp_file = f.name
        
        try:
            with patch.dict(os.environ, {
                'DOMAIN_BLACKLIST_FILE': temp_file
            }):
                service = create_safety_service()
                
                # Test that blacklist is loaded
                stats = service.get_blacklist_stats()
                assert stats['domains'] >= 2
                assert stats['keywords'] >= 2
                
                # Test blacklist functionality
                assert service._check_blacklist("https://test-malware.com/page") is True
                assert service._check_blacklist("https://example.com/test-scam") is True
                assert service._check_blacklist("https://google.com") is False
                
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__])