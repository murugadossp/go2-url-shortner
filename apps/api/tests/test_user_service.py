import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.services.user_service import UserService, user_service
from src.models.user import UserDocument, UserProfileResponse


class TestUserService:
    
    @pytest.fixture
    def mock_db(self):
        """Mock Firestore database"""
        db = Mock()
        collection = Mock()
        document = Mock()
        
        db.collection.return_value = collection
        collection.document.return_value = document
        
        return db, collection, document
    
    @pytest.fixture
    def user_service_instance(self, mock_db):
        """Create UserService instance with mocked database"""
        db, collection, document = mock_db
        service = UserService()
        service.db = db
        service.users_collection = collection
        return service, db, collection, document
    
    @pytest.fixture
    def sample_user_token(self):
        """Sample Firebase user token"""
        return {
            'uid': 'test-user-123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
    
    @pytest.fixture
    def sample_user_document(self):
        """Sample user document data"""
        now = datetime.utcnow()
        return {
            'email': 'test@example.com',
            'display_name': 'Test User',
            'plan_type': 'free',
            'custom_codes_used': 2,
            'custom_codes_reset_date': now + timedelta(days=20),
            'created_at': now - timedelta(days=10),
            'last_login': now,
            'is_admin': False
        }

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing(self, user_service_instance, sample_user_token, sample_user_document):
        """Test getting existing user"""
        service, db, collection, document = user_service_instance
        
        # Mock existing user document
        doc_mock = Mock()
        doc_mock.exists = True
        doc_mock.to_dict.return_value = sample_user_document
        document.get.return_value = doc_mock
        
        result = await service.get_or_create_user(sample_user_token)
        
        # Verify user document was retrieved
        collection.document.assert_called_with('test-user-123')
        document.get.assert_called_once()
        document.update.assert_called_once()  # Last login update
        
        assert result.email == 'test@example.com'
        assert result.display_name == 'Test User'
        assert result.plan_type == 'free'

    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self, user_service_instance, sample_user_token):
        """Test creating new user"""
        service, db, collection, document = user_service_instance
        
        # Mock non-existing user document
        doc_mock = Mock()
        doc_mock.exists = False
        document.get.return_value = doc_mock
        
        result = await service.get_or_create_user(sample_user_token)
        
        # Verify new user document was created
        collection.document.assert_called_with('test-user-123')
        document.get.assert_called_once()
        document.set.assert_called_once()
        
        assert result.email == 'test@example.com'
        assert result.display_name == 'Test User'
        assert result.plan_type == 'free'
        assert result.custom_codes_used == 0

    @pytest.mark.asyncio
    async def test_get_user_profile_with_reset(self, user_service_instance, sample_user_document):
        """Test getting user profile with custom code reset"""
        service, db, collection, document = user_service_instance
        
        # Mock user document with expired reset date
        expired_data = sample_user_document.copy()
        expired_data['custom_codes_reset_date'] = datetime.utcnow() - timedelta(days=1)
        expired_data['custom_codes_used'] = 5
        
        doc_mock = Mock()
        doc_mock.exists = True
        doc_mock.to_dict.return_value = expired_data
        document.get.return_value = doc_mock
        
        result = await service.get_user_profile('test-user-123')
        
        # Verify reset was triggered
        document.update.assert_called_once()
        update_call = document.update.call_args[0][0]
        assert update_call['custom_codes_used'] == 0
        assert 'custom_codes_reset_date' in update_call
        
        assert result.custom_codes_used == 0
        assert result.custom_codes_remaining == 5  # Free plan limit

    @pytest.mark.asyncio
    async def test_can_create_custom_code_free_plan(self, user_service_instance, sample_user_document):
        """Test custom code limit check for free plan"""
        service, db, collection, document = user_service_instance
        
        # Test with usage under limit
        doc_mock = Mock()
        doc_mock.exists = True
        doc_mock.to_dict.return_value = sample_user_document
        document.get.return_value = doc_mock
        
        result = await service.can_create_custom_code('test-user-123')
        assert result is True
        
        # Test with usage at limit
        limit_data = sample_user_document.copy()
        limit_data['custom_codes_used'] = 5
        doc_mock.to_dict.return_value = limit_data
        
        result = await service.can_create_custom_code('test-user-123')
        assert result is False

    @pytest.mark.asyncio
    async def test_can_create_custom_code_paid_plan(self, user_service_instance, sample_user_document):
        """Test custom code limit check for paid plan"""
        service, db, collection, document = user_service_instance
        
        # Test paid plan with higher usage
        paid_data = sample_user_document.copy()
        paid_data['plan_type'] = 'paid'
        paid_data['custom_codes_used'] = 50
        
        doc_mock = Mock()
        doc_mock.exists = True
        doc_mock.to_dict.return_value = paid_data
        document.get.return_value = doc_mock
        
        result = await service.can_create_custom_code('test-user-123')
        assert result is True  # Still under paid limit of 100

    @pytest.mark.asyncio
    async def test_increment_custom_code_usage(self, user_service_instance, sample_user_document):
        """Test incrementing custom code usage"""
        service, db, collection, document = user_service_instance
        
        doc_mock = Mock()
        doc_mock.exists = True
        doc_mock.to_dict.return_value = sample_user_document
        document.get.return_value = doc_mock
        
        result = await service.increment_custom_code_usage('test-user-123')
        
        assert result is True
        document.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_custom_code_usage_with_reset(self, user_service_instance, sample_user_document):
        """Test incrementing custom code usage when reset is needed"""
        service, db, collection, document = user_service_instance
        
        # Mock user document with expired reset date
        expired_data = sample_user_document.copy()
        expired_data['custom_codes_reset_date'] = datetime.utcnow() - timedelta(days=1)
        
        doc_mock = Mock()
        doc_mock.exists = True
        doc_mock.to_dict.return_value = expired_data
        document.get.return_value = doc_mock
        
        result = await service.increment_custom_code_usage('test-user-123')
        
        assert result is True
        document.update.assert_called_once()
        update_call = document.update.call_args[0][0]
        assert update_call['custom_codes_used'] == 1  # Reset to 1 (incremented)

    @pytest.mark.asyncio
    async def test_upgrade_user_plan(self, user_service_instance):
        """Test upgrading user plan"""
        service, db, collection, document = user_service_instance
        
        result = await service.upgrade_user_plan('test-user-123', 'paid')
        
        assert result is True
        document.update.assert_called_once_with({'plan_type': 'paid'})

    @pytest.mark.asyncio
    async def test_get_user_usage_stats(self, user_service_instance, sample_user_document):
        """Test getting user usage statistics"""
        service, db, collection, document = user_service_instance
        
        # Mock user profile
        doc_mock = Mock()
        doc_mock.exists = True
        doc_mock.to_dict.return_value = sample_user_document
        document.get.return_value = doc_mock
        
        # Mock links collection query
        links_query = Mock()
        links_collection = Mock()
        service.db.collection.return_value = links_collection
        links_collection.where.return_value = links_query
        
        # Mock link documents
        link_docs = []
        for i in range(3):
            link_doc = Mock()
            link_doc.to_dict.return_value = {
                'is_custom_code': i < 2  # First 2 are custom codes
            }
            # Mock clicks subcollection
            clicks_collection = Mock()
            link_doc.reference.collection.return_value = clicks_collection
            clicks_collection.get.return_value = [Mock()] * (i + 1)  # Different click counts
            link_docs.append(link_doc)
        
        links_query.get.return_value = link_docs
        
        result = await service.get_user_usage_stats('test-user-123')
        
        assert result['total_links'] == 3
        assert result['custom_code_links'] == 2
        assert result['total_clicks'] == 6  # 1 + 2 + 3
        assert result['plan_type'] == 'free'
        assert result['custom_codes_used'] == 2
        assert result['custom_codes_remaining'] == 3  # 5 - 2

    @pytest.mark.asyncio
    async def test_update_user_profile(self, user_service_instance):
        """Test updating user profile"""
        service, db, collection, document = user_service_instance
        
        result = await service.update_user_profile('test-user-123', 'New Display Name')
        
        assert result is True
        document.update.assert_called_once_with({'display_name': 'New Display Name'})

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, user_service_instance):
        """Test getting profile for non-existent user"""
        service, db, collection, document = user_service_instance
        
        doc_mock = Mock()
        doc_mock.exists = False
        document.get.return_value = doc_mock
        
        result = await service.get_user_profile('non-existent-user')
        
        assert result is None


class TestUserServiceIntegration:
    """Integration tests for user service"""
    
    def test_plan_limits_configuration(self):
        """Test that plan limits are correctly configured"""
        service = UserService()
        
        assert service.plan_limits['free']['custom_codes'] == 5
        assert service.plan_limits['paid']['custom_codes'] == 100
    
    def test_global_user_service_instance(self):
        """Test that global user service instance is available"""
        assert user_service is not None
        assert isinstance(user_service, UserService)