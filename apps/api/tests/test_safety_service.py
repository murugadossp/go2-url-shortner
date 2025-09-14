"""
Unit tests for SafetyService.
Tests all safety validation scenarios including scheme validation,
blacklist checking, content pattern detection, and Safe Browsing integration.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.services.safety_service import SafetyService, SafetyError, SafetyResult


class TestSafetyService:
    """Test suite for SafetyService"""
    
    @pytest.fixture
    def temp_blacklist_file(self):
        """Create temporary blacklist file for testing"""
        blacklist_data = {
            "domains": ["malware.com", "phishing.net", "spam.org"],
            "keywords": ["scam", "fraud", "illegal"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(blacklist_data, f)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        os.unlink(temp_file)
    
    @pytest.fixture
    def safety_service(self, temp_blacklist_file):
        """Create SafetyService instance for testing"""
        return SafetyService(
            safe_browsing_api_key="test_api_key",
            blacklist_file_path=temp_blacklist_file
        )
    
    @pytest.fixture
    def safety_service_no_api(self, temp_blacklist_file):
        """Create SafetyService instance without Safe Browsing API"""
        return SafetyService(blacklist_file_path=temp_blacklist_file)


class TestURLSchemeValidation(TestSafetyService):
    """Test URL scheme validation"""
    
    def test_valid_http_url(self, safety_service):
        """Test that HTTP URLs are accepted"""
        result = safety_service._validate_url_scheme("http://example.com")
        assert result is True
    
    def test_valid_https_url(self, safety_service):
        """Test that HTTPS URLs are accepted"""
        result = safety_service._validate_url_scheme("https://example.com")
        assert result is True
    
    def test_invalid_javascript_scheme(self, safety_service):
        """Test that javascript: URLs are rejected"""
        result = safety_service._validate_url_scheme("javascript:alert('xss')")
        assert result is False
    
    def test_invalid_data_scheme(self, safety_service):
        """Test that data: URLs are rejected"""
        result = safety_service._validate_url_scheme("data:text/html,<script>alert('xss')</script>")
        assert result is False
    
    def test_invalid_file_scheme(self, safety_service):
        """Test that file: URLs are rejected"""
        result = safety_service._validate_url_scheme("file:///etc/passwd")
        assert result is False
    
    def test_invalid_ftp_scheme(self, safety_service):
        """Test that FTP URLs are rejected"""
        result = safety_service._validate_url_scheme("ftp://example.com/file.txt")
        assert result is False
    
    def test_malformed_url(self, safety_service):
        """Test that malformed URLs are rejected"""
        result = safety_service._validate_url_scheme("not-a-url")
        assert result is False
    
    def test_empty_url(self, safety_service):
        """Test that empty URLs are rejected"""
        result = safety_service._validate_url_scheme("")
        assert result is False


class TestBlacklistValidation(TestSafetyService):
    """Test domain and keyword blacklist validation"""
    
    def test_blacklisted_domain(self, safety_service):
        """Test that blacklisted domains are blocked"""
        result = safety_service._check_blacklist("https://malware.com/page")
        assert result is True
    
    def test_subdomain_of_blacklisted_domain(self, safety_service):
        """Test that subdomains of blacklisted domains are blocked"""
        result = safety_service._check_blacklist("https://sub.malware.com/page")
        assert result is True
    
    def test_blacklisted_keyword_in_url(self, safety_service):
        """Test that URLs with blacklisted keywords are blocked"""
        result = safety_service._check_blacklist("https://example.com/scam-page")
        assert result is True
    
    def test_blacklisted_keyword_in_domain(self, safety_service):
        """Test that domains with blacklisted keywords are blocked"""
        result = safety_service._check_blacklist("https://fraud-site.com/page")
        assert result is True
    
    def test_clean_url_not_blacklisted(self, safety_service):
        """Test that clean URLs are not blocked by blacklist"""
        result = safety_service._check_blacklist("https://google.com")
        assert result is False
    
    def test_case_insensitive_blacklist_check(self, safety_service):
        """Test that blacklist checking is case insensitive"""
        result = safety_service._check_blacklist("https://MALWARE.COM/page")
        assert result is True
    
    def test_blacklist_error_handling(self, safety_service):
        """Test that blacklist errors are handled gracefully"""
        # Test with invalid URL that has no scheme or netloc
        result = safety_service._check_blacklist(":::invalid-url:::")
        assert result is True  # Should fail safe and block


class TestContentPatternDetection(TestSafetyService):
    """Test adult/gambling content pattern detection"""
    
    def test_adult_content_pattern(self, safety_service):
        """Test that adult content patterns are detected"""
        result = safety_service._scan_content_patterns("https://example.com/porn-videos")
        assert result is True
    
    def test_gambling_content_pattern(self, safety_service):
        """Test that gambling content patterns are detected"""
        result = safety_service._scan_content_patterns("https://example.com/casino-games")
        assert result is True
    
    def test_pharmacy_content_pattern(self, safety_service):
        """Test that pharmacy content patterns are detected"""
        result = safety_service._scan_content_patterns("https://example.com/buy-viagra")
        assert result is True
    
    def test_escort_content_pattern(self, safety_service):
        """Test that escort content patterns are detected"""
        result = safety_service._scan_content_patterns("https://example.com/escort-services")
        assert result is True
    
    def test_clean_url_no_patterns(self, safety_service):
        """Test that clean URLs don't match content patterns"""
        result = safety_service._scan_content_patterns("https://google.com/search?q=python")
        assert result is False
    
    def test_case_insensitive_pattern_matching(self, safety_service):
        """Test that pattern matching is case insensitive"""
        result = safety_service._scan_content_patterns("https://example.com/CASINO-GAMES")
        assert result is True
    
    def test_pattern_in_domain(self, safety_service):
        """Test that patterns in domain are detected"""
        result = safety_service._scan_content_patterns("https://poker-site.com/games")
        assert result is True


class TestSafeBrowsingIntegration(TestSafetyService):
    """Test Google Safe Browsing API integration"""
    
    @patch('src.services.safety_service.discovery.build')
    def test_safe_browsing_malware_detection(self, mock_build, temp_blacklist_file):
        """Test that Safe Browsing detects malware URLs"""
        # Mock Safe Browsing client
        mock_client = Mock()
        mock_threat_matches = Mock()
        mock_find = Mock()
        
        mock_find.execute.return_value = {
            'matches': [{'threatType': 'MALWARE', 'platformType': 'ANY_PLATFORM'}]
        }
        mock_threat_matches.find.return_value = mock_find
        mock_client.threatMatches.return_value = mock_threat_matches
        mock_build.return_value = mock_client
        
        safety_service = SafetyService(
            safe_browsing_api_key="test_key",
            blacklist_file_path=temp_blacklist_file
        )
        
        result = safety_service._check_safe_browsing("https://malware-site.com")
        assert result is True
    
    @patch('src.services.safety_service.discovery.build')
    def test_safe_browsing_clean_url(self, mock_build, temp_blacklist_file):
        """Test that Safe Browsing allows clean URLs"""
        # Mock Safe Browsing client
        mock_client = Mock()
        mock_threat_matches = Mock()
        mock_find = Mock()
        
        mock_find.execute.return_value = {}  # No matches
        mock_threat_matches.find.return_value = mock_find
        mock_client.threatMatches.return_value = mock_threat_matches
        mock_build.return_value = mock_client
        
        safety_service = SafetyService(
            safe_browsing_api_key="test_key",
            blacklist_file_path=temp_blacklist_file
        )
        
        result = safety_service._check_safe_browsing("https://google.com")
        assert result is False
    
    def test_safe_browsing_no_api_key(self, safety_service_no_api):
        """Test that Safe Browsing is skipped when no API key provided"""
        result = safety_service_no_api._check_safe_browsing("https://example.com")
        assert result is False
    
    @patch('src.services.safety_service.discovery.build')
    def test_safe_browsing_api_error_handling(self, mock_build, temp_blacklist_file):
        """Test that Safe Browsing API errors are handled gracefully"""
        from googleapiclient.errors import HttpError
        
        # Mock Safe Browsing client that raises error
        mock_client = Mock()
        mock_threat_matches = Mock()
        mock_find = Mock()
        
        mock_find.execute.side_effect = HttpError(
            resp=Mock(status=400), content=b'API Error'
        )
        mock_threat_matches.find.return_value = mock_find
        mock_client.threatMatches.return_value = mock_threat_matches
        mock_build.return_value = mock_client
        
        safety_service = SafetyService(
            safe_browsing_api_key="test_key",
            blacklist_file_path=temp_blacklist_file
        )
        
        result = safety_service._check_safe_browsing("https://example.com")
        assert result is False  # Should not block on API errors


class TestComprehensiveValidation(TestSafetyService):
    """Test comprehensive URL validation"""
    
    def test_safe_url_passes_all_checks(self, safety_service_no_api):
        """Test that safe URLs pass all validation checks"""
        result = safety_service_no_api.validate_url("https://google.com")
        assert result.is_safe is True
        assert len(result.reasons) == 0
        assert len(result.blocked_by) == 0
    
    def test_invalid_scheme_fails_validation(self, safety_service_no_api):
        """Test that invalid schemes fail validation"""
        with pytest.raises(SafetyError) as exc_info:
            safety_service_no_api.validate_url("javascript:alert('xss')")
        
        assert "Invalid URL scheme" in exc_info.value.message
        assert any("scheme" in reason.lower() for reason in exc_info.value.reasons)
    
    def test_blacklisted_domain_fails_validation(self, safety_service_no_api):
        """Test that blacklisted domains fail validation"""
        with pytest.raises(SafetyError) as exc_info:
            safety_service_no_api.validate_url("https://malware.com/page")
        
        assert "blacklisted domain" in exc_info.value.message
        assert any("blacklisted" in reason for reason in exc_info.value.reasons)
    
    def test_adult_content_fails_validation(self, safety_service_no_api):
        """Test that adult content fails validation"""
        with pytest.raises(SafetyError) as exc_info:
            safety_service_no_api.validate_url("https://example.com/porn-site")
        
        assert "adult/gambling content" in exc_info.value.message
        assert any("content" in reason for reason in exc_info.value.reasons)
    
    def test_multiple_violations_reported(self, safety_service_no_api):
        """Test that multiple violations are all reported"""
        with pytest.raises(SafetyError) as exc_info:
            safety_service_no_api.validate_url("javascript:malware.com/scam-porn")
        
        # Should catch scheme violation, blacklist violation, and content pattern
        assert len(exc_info.value.reasons) >= 2
    
    @patch('src.services.safety_service.discovery.build')
    def test_safe_browsing_integration_in_full_validation(self, mock_build, temp_blacklist_file):
        """Test Safe Browsing integration in full validation pipeline"""
        # Mock Safe Browsing client
        mock_client = Mock()
        mock_threat_matches = Mock()
        mock_find = Mock()
        
        mock_find.execute.return_value = {
            'matches': [{'threatType': 'SOCIAL_ENGINEERING'}]
        }
        mock_threat_matches.find.return_value = mock_find
        mock_client.threatMatches.return_value = mock_threat_matches
        mock_build.return_value = mock_client
        
        safety_service = SafetyService(
            safe_browsing_api_key="test_key",
            blacklist_file_path=temp_blacklist_file
        )
        
        with pytest.raises(SafetyError) as exc_info:
            safety_service.validate_url("https://phishing-site.com")
        
        assert "Safe Browsing" in exc_info.value.message


class TestBlacklistManagement(TestSafetyService):
    """Test blacklist management functionality"""
    
    def test_add_domains_to_blacklist(self, safety_service):
        """Test adding domains to blacklist"""
        initial_count = len(safety_service._blacklist_domains)
        safety_service.add_to_blacklist(domains=["new-malware.com", "another-bad.site"])
        
        assert len(safety_service._blacklist_domains) == initial_count + 2
        assert "new-malware.com" in safety_service._blacklist_domains
        assert "another-bad.site" in safety_service._blacklist_domains
    
    def test_add_keywords_to_blacklist(self, safety_service):
        """Test adding keywords to blacklist"""
        initial_count = len(safety_service._blacklist_keywords)
        safety_service.add_to_blacklist(keywords=["newbadword", "anotherbadword"])
        
        assert len(safety_service._blacklist_keywords) == initial_count + 2
        assert "newbadword" in safety_service._blacklist_keywords
        assert "anotherbadword" in safety_service._blacklist_keywords
    
    def test_remove_domains_from_blacklist(self, safety_service):
        """Test removing domains from blacklist"""
        # First add a domain
        safety_service.add_to_blacklist(domains=["temp-domain.com"])
        assert "temp-domain.com" in safety_service._blacklist_domains
        
        # Then remove it
        safety_service.remove_from_blacklist(domains=["temp-domain.com"])
        assert "temp-domain.com" not in safety_service._blacklist_domains
    
    def test_remove_keywords_from_blacklist(self, safety_service):
        """Test removing keywords from blacklist"""
        # First add a keyword
        safety_service.add_to_blacklist(keywords=["tempkeyword"])
        assert "tempkeyword" in safety_service._blacklist_keywords
        
        # Then remove it
        safety_service.remove_from_blacklist(keywords=["tempkeyword"])
        assert "tempkeyword" not in safety_service._blacklist_keywords
    
    def test_get_blacklist_stats(self, safety_service):
        """Test getting blacklist statistics"""
        stats = safety_service.get_blacklist_stats()
        
        assert "domains" in stats
        assert "keywords" in stats
        assert isinstance(stats["domains"], int)
        assert isinstance(stats["keywords"], int)
        assert stats["domains"] > 0
        assert stats["keywords"] > 0


class TestBlacklistFileHandling(TestSafetyService):
    """Test blacklist file loading and creation"""
    
    def test_missing_blacklist_file_creates_default(self):
        """Test that missing blacklist file triggers default creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            blacklist_path = os.path.join(temp_dir, "test_blacklist.json")
            
            # Create service with non-existent blacklist file
            safety_service = SafetyService(blacklist_file_path=blacklist_path)
            
            # Should have created default blacklist
            assert os.path.exists(blacklist_path)
            assert len(safety_service._blacklist_domains) > 0
            assert len(safety_service._blacklist_keywords) > 0
    
    def test_invalid_blacklist_file_uses_defaults(self):
        """Test that invalid blacklist file falls back to defaults"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            safety_service = SafetyService(blacklist_file_path=temp_file)
            
            # Should have fallback blacklist
            assert len(safety_service._blacklist_domains) > 0
            assert len(safety_service._blacklist_keywords) > 0
            
        finally:
            os.unlink(temp_file)


class TestEdgeCases(TestSafetyService):
    """Test edge cases and error conditions"""
    
    def test_empty_url_validation(self, safety_service_no_api):
        """Test validation of empty URL"""
        with pytest.raises(SafetyError):
            safety_service_no_api.validate_url("")
    
    def test_none_url_validation(self, safety_service_no_api):
        """Test validation of None URL"""
        with pytest.raises(Exception):  # Should raise some exception
            safety_service_no_api.validate_url(None)
    
    def test_very_long_url_validation(self, safety_service_no_api):
        """Test validation of very long URL"""
        long_url = "https://example.com/" + "a" * 10000
        # Should not crash, may pass or fail based on content
        try:
            result = safety_service_no_api.validate_url(long_url)
            assert isinstance(result, SafetyResult)
        except SafetyError:
            pass  # May fail validation, that's ok
    
    def test_unicode_url_validation(self, safety_service_no_api):
        """Test validation of URL with unicode characters"""
        unicode_url = "https://example.com/测试页面"
        # Should handle unicode gracefully
        try:
            result = safety_service_no_api.validate_url(unicode_url)
            assert isinstance(result, SafetyResult)
        except SafetyError:
            pass  # May fail validation, that's ok


if __name__ == "__main__":
    pytest.main([__file__])