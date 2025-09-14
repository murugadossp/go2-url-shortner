"""
Test data fixtures for backend tests
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
import pytest

class TestDataFixtures:
    """Centralized test data fixtures"""
    
    @staticmethod
    def get_test_user(user_type: str = 'regular') -> Dict[str, Any]:
        """Get test user data"""
        users = {
            'regular': {
                'uid': 'test-user-123',
                'email': 'test@example.com',
                'display_name': 'Test User',
                'plan_type': 'free',
                'custom_codes_used': 2,
                'custom_codes_reset_date': datetime.now(),
                'created_at': datetime.now() - timedelta(days=30),
                'last_login': datetime.now(),
                'is_admin': False
            },
            'admin': {
                'uid': 'admin-user-123',
                'email': 'admin@example.com',
                'display_name': 'Admin User',
                'plan_type': 'paid',
                'custom_codes_used': 15,
                'custom_codes_reset_date': datetime.now(),
                'created_at': datetime.now() - timedelta(days=90),
                'last_login': datetime.now(),
                'is_admin': True
            },
            'paid': {
                'uid': 'paid-user-123',
                'email': 'paid@example.com',
                'display_name': 'Paid User',
                'plan_type': 'paid',
                'custom_codes_used': 25,
                'custom_codes_reset_date': datetime.now(),
                'created_at': datetime.now() - timedelta(days=60),
                'last_login': datetime.now(),
                'is_admin': False
            }
        }
        return users.get(user_type, users['regular'])
    
    @staticmethod
    def get_test_link(link_type: str = 'basic') -> Dict[str, Any]:
        """Get test link data"""
        base_link = {
            'long_url': 'https://www.example.com',
            'base_domain': 'go2.tools',
            'owner_uid': 'test-user-123',
            'disabled': False,
            'created_at': datetime.now(),
            'created_by_ip': '192.168.1.1',
            'metadata': {
                'title': 'Example Site',
                'host': 'example.com'
            },
            'plan_type': 'free',
            'is_custom_code': False
        }
        
        links = {
            'basic': {
                **base_link,
                'code': 'abc123',
                'password_hash': None,
                'expires_at': None
            },
            'custom': {
                **base_link,
                'code': 'mycustom',
                'password_hash': None,
                'expires_at': None,
                'is_custom_code': True
            },
            'password_protected': {
                **base_link,
                'code': 'secure123',
                'password_hash': '$2b$12$hashed_password_here',
                'expires_at': None
            },
            'expired': {
                **base_link,
                'code': 'expired123',
                'password_hash': None,
                'expires_at': datetime.now() - timedelta(days=1)
            },
            'disabled': {
                **base_link,
                'code': 'disabled123',
                'password_hash': None,
                'expires_at': None,
                'disabled': True
            }
        }
        return links.get(link_type, links['basic'])
    
    @staticmethod
    def get_test_click_data() -> List[Dict[str, Any]]:
        """Get test click analytics data"""
        return [
            {
                'ts': datetime.now() - timedelta(hours=1),
                'ip_hash': 'hashed_ip_1',
                'ua': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'referrer': 'https://google.com',
                'location': {
                    'country': 'United States',
                    'country_code': 'US',
                    'region': 'California',
                    'city': 'San Francisco',
                    'timezone': 'America/Los_Angeles',
                    'latitude': 37.7749,
                    'longitude': -122.4194
                },
                'device_type': 'desktop',
                'browser': 'Chrome',
                'os': 'Windows'
            },
            {
                'ts': datetime.now() - timedelta(hours=2),
                'ip_hash': 'hashed_ip_2',
                'ua': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)',
                'referrer': 'https://twitter.com',
                'location': {
                    'country': 'Canada',
                    'country_code': 'CA',
                    'region': 'Ontario',
                    'city': 'Toronto',
                    'timezone': 'America/Toronto',
                    'latitude': 43.6532,
                    'longitude': -79.3832
                },
                'device_type': 'mobile',
                'browser': 'Safari',
                'os': 'iOS'
            },
            {
                'ts': datetime.now() - timedelta(hours=3),
                'ip_hash': 'hashed_ip_3',
                'ua': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'referrer': None,  # Direct traffic
                'location': {
                    'country': 'United Kingdom',
                    'country_code': 'GB',
                    'region': 'England',
                    'city': 'London',
                    'timezone': 'Europe/London',
                    'latitude': 51.5074,
                    'longitude': -0.1278
                },
                'device_type': 'desktop',
                'browser': 'Safari',
                'os': 'macOS'
            }
        ]
    
    @staticmethod
    def get_test_urls() -> Dict[str, str]:
        """Get test URLs for validation"""
        return {
            'valid': {
                'youtube': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'github': 'https://github.com/microsoft/playwright',
                'google': 'https://www.google.com',
                'amazon': 'https://www.amazon.com/product/123'
            },
            'invalid': {
                'no_protocol': 'www.example.com',
                'javascript': 'javascript:alert("xss")',
                'malformed': 'not-a-url',
                'empty': '',
                'ftp': 'ftp://files.example.com/file.zip'
            },
            'unsafe': {
                'blacklisted': 'https://malicious-site.com',
                'adult_content': 'https://adult-site.xxx',
                'gambling': 'https://casino-site.com/slots'
            }
        }
    
    @staticmethod
    def get_test_config() -> Dict[str, Any]:
        """Get test configuration data"""
        return {
            'base_domains': ['go2.video', 'go2.reviews', 'go2.tools'],
            'domain_suggestions': {
                'youtube.com': 'go2.video',
                'youtu.be': 'go2.video',
                'vimeo.com': 'go2.video',
                'amazon.com': 'go2.reviews',
                'yelp.com': 'go2.reviews',
                'github.com': 'go2.tools',
                'stackoverflow.com': 'go2.tools'
            },
            'safety_settings': {
                'enable_safe_browsing': True,
                'blacklist_domains': ['malicious-site.com', 'spam-site.net'],
                'blacklist_keywords': ['casino', 'gambling', 'adult', 'xxx']
            },
            'plan_limits': {
                'free': {'custom_codes': 5},
                'paid': {'custom_codes': 100}
            }
        }
    
    @staticmethod
    def get_mock_firebase_token(user_type: str = 'regular') -> Dict[str, Any]:
        """Get mock Firebase token claims"""
        user_data = TestDataFixtures.get_test_user(user_type)
        return {
            'uid': user_data['uid'],
            'email': user_data['email'],
            'admin': user_data.get('is_admin', False),
            'iat': int(datetime.now().timestamp()),
            'exp': int((datetime.now() + timedelta(hours=1)).timestamp())
        }

@pytest.fixture
def test_user():
    """Fixture for regular test user"""
    return TestDataFixtures.get_test_user('regular')

@pytest.fixture
def admin_user():
    """Fixture for admin test user"""
    return TestDataFixtures.get_test_user('admin')

@pytest.fixture
def paid_user():
    """Fixture for paid test user"""
    return TestDataFixtures.get_test_user('paid')

@pytest.fixture
def test_link():
    """Fixture for basic test link"""
    return TestDataFixtures.get_test_link('basic')

@pytest.fixture
def custom_link():
    """Fixture for custom code test link"""
    return TestDataFixtures.get_test_link('custom')

@pytest.fixture
def protected_link():
    """Fixture for password-protected test link"""
    return TestDataFixtures.get_test_link('password_protected')

@pytest.fixture
def expired_link():
    """Fixture for expired test link"""
    return TestDataFixtures.get_test_link('expired')

@pytest.fixture
def test_clicks():
    """Fixture for test click data"""
    return TestDataFixtures.get_test_click_data()

@pytest.fixture
def test_urls():
    """Fixture for test URLs"""
    return TestDataFixtures.get_test_urls()

@pytest.fixture
def test_config():
    """Fixture for test configuration"""
    return TestDataFixtures.get_test_config()

@pytest.fixture
def mock_firebase_token():
    """Fixture for mock Firebase token"""
    return TestDataFixtures.get_mock_firebase_token('regular')

@pytest.fixture
def mock_admin_token():
    """Fixture for mock admin Firebase token"""
    return TestDataFixtures.get_mock_firebase_token('admin')