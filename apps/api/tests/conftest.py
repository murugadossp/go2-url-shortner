"""
Pytest configuration and shared fixtures
"""
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
from src.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_firestore():
    """Mock Firestore client"""
    with patch('src.services.firebase_service.get_firestore_client') as mock:
        mock_db = MagicMock()
        mock.return_value = mock_db
        yield mock_db

@pytest.fixture
def mock_firebase_auth():
    """Mock Firebase Auth verification"""
    with patch('src.services.firebase_service.verify_firebase_token') as mock:
        mock.return_value = {
            'uid': 'test-user-123',
            'email': 'test@example.com',
            'admin': False
        }
        yield mock

@pytest.fixture
def mock_admin_auth():
    """Mock Firebase Auth verification for admin"""
    with patch('src.services.firebase_service.verify_firebase_token') as mock:
        mock.return_value = {
            'uid': 'admin-user-123',
            'email': 'admin@example.com',
            'admin': True
        }
        yield mock

@pytest.fixture
def mock_safety_service():
    """Mock Safety Service"""
    with patch('src.services.safety_service.SafetyService.validate_url') as mock:
        mock.return_value = {'is_safe': True, 'reasons': []}
        yield mock

@pytest.fixture
def mock_qr_service():
    """Mock QR Service"""
    with patch('src.services.qr_service.QRService') as mock:
        mock_instance = MagicMock()
        mock_instance.generate_qr.return_value = b'fake-qr-data'
        mock_instance.get_cached_qr.return_value = None
        mock_instance.cache_qr.return_value = 'https://storage.googleapis.com/qr/test.png'
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_analytics_service():
    """Mock Analytics Service"""
    with patch('src.services.analytics_service.AnalyticsService') as mock:
        mock_instance = MagicMock()
        mock_instance.get_stats.return_value = {
            'total_clicks': 42,
            'clicks_by_day': [],
            'top_referrers': [],
            'top_devices': [],
            'geographic_data': []
        }
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_sendgrid():
    """Mock SendGrid email service"""
    with patch('sendgrid.SendGridAPIClient') as mock:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_client.send.return_value = mock_response
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Cleanup test data after each test"""
    yield
    # Cleanup logic would go here
    # In a real implementation, you might:
    # - Clear test collections in Firestore
    # - Reset mock states
    # - Clean up temporary files
    pass

class MockFirestoreDocument:
    """Mock Firestore document"""
    
    def __init__(self, data=None, exists=True):
        self._data = data or {}
        self.exists = exists
        self.id = 'mock-doc-id'
    
    def to_dict(self):
        return self._data
    
    def get(self):
        return self
    
    def set(self, data):
        self._data = data
    
    def update(self, data):
        self._data.update(data)
    
    def delete(self):
        self.exists = False
        self._data = {}

class MockFirestoreCollection:
    """Mock Firestore collection"""
    
    def __init__(self):
        self._documents = {}
    
    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = f'auto-generated-{len(self._documents)}'
        
        if doc_id not in self._documents:
            self._documents[doc_id] = MockFirestoreDocument()
        
        return self._documents[doc_id]
    
    def add(self, data):
        doc_id = f'auto-generated-{len(self._documents)}'
        doc = MockFirestoreDocument(data)
        self._documents[doc_id] = doc
        return doc, doc_id
    
    def stream(self):
        return [doc for doc in self._documents.values() if doc.exists]
    
    def where(self, field, op, value):
        # Simple mock implementation
        return self
    
    def order_by(self, field, direction=None):
        return self
    
    def limit(self, count):
        return self

@pytest.fixture
def mock_firestore_collection():
    """Mock Firestore collection with helper methods"""
    return MockFirestoreCollection()

@pytest.fixture
def setup_test_environment():
    """Setup test environment with all necessary mocks"""
    with patch.multiple(
        'src.services.firebase_service',
        get_firestore_client=MagicMock(),
        verify_firebase_token=MagicMock(return_value={
            'uid': 'test-user-123',
            'email': 'test@example.com'
        })
    ), patch.multiple(
        'src.services.safety_service',
        SafetyService=MagicMock()
    ), patch.multiple(
        'src.services.qr_service',
        QRService=MagicMock()
    ):
        yield

# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Generate large dataset for performance testing"""
    return {
        'links': [
            {
                'code': f'perf{i}',
                'long_url': f'https://example{i}.com',
                'base_domain': 'go2.tools',
                'owner_uid': f'user{i % 10}',  # 10 different users
                'created_at': '2024-01-01T00:00:00Z',
                'clicks': i * 5
            }
            for i in range(1000)
        ],
        'clicks': [
            {
                'code': f'perf{i % 100}',  # Distribute clicks across 100 links
                'timestamp': '2024-01-01T00:00:00Z',
                'country': 'US' if i % 2 == 0 else 'CA',
                'device': 'desktop' if i % 3 == 0 else 'mobile'
            }
            for i in range(10000)
        ]
    }