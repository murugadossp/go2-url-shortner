"""
Unit tests for Firestore document converters.
Tests conversion between Pydantic models and Firestore documents.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from src.utils.firestore_converters import (
    FirestoreConverter, LinkConverter, UserConverter, ClickConverter,
    ConfigConverter, BatchConverter, serialize_for_json, deserialize_from_json,
    validate_and_convert
)
from src.models.link import LinkDocument, LinkMetadata
from src.models.user import UserDocument
from src.models.analytics import ClickDocument, LocationData
from src.models.config import ConfigDocument, SafetySettings, PlanLimits


class TestFirestoreConverter:
    """Test cases for base FirestoreConverter"""
    
    def test_to_firestore_dict_with_datetime(self):
        """Test conversion of model with datetime to Firestore dict"""
        now = datetime.now()
        link = LinkDocument(
            long_url="https://example.com",
            base_domain="go2.video",
            created_at=now
        )
        
        firestore_dict = FirestoreConverter.to_firestore_dict(link)
        
        assert str(firestore_dict["long_url"]) == "https://example.com/"
        assert firestore_dict["base_domain"] == "go2.video"
        assert firestore_dict["created_at"] == now.isoformat()  # Now serialized as ISO string
        assert firestore_dict["disabled"] is False
    
    def test_to_firestore_dict_nested_objects(self):
        """Test conversion with nested objects"""
        now = datetime.now()
        metadata = LinkMetadata(title="Test", host="example.com")
        link = LinkDocument(
            long_url="https://example.com",
            base_domain="go2.video",
            created_at=now,
            metadata=metadata
        )
        
        firestore_dict = FirestoreConverter.to_firestore_dict(link)
        
        assert firestore_dict["metadata"]["title"] == "Test"
        assert firestore_dict["metadata"]["host"] == "example.com"
    
    def test_from_firestore_dict(self):
        """Test conversion from Firestore dict to model"""
        now = datetime.now()
        firestore_data = {
            "long_url": "https://example.com",
            "base_domain": "go2.video",
            "created_at": now,
            "disabled": False,
            "owner_uid": None,
            "password_hash": None,
            "expires_at": None,
            "created_by_ip": None,
            "metadata": {"title": "Test"},
            "plan_type": "free",
            "is_custom_code": False
        }
        
        link = FirestoreConverter.from_firestore_dict(firestore_data, LinkDocument)
        
        assert str(link.long_url) == "https://example.com/"
        assert link.base_domain == "go2.video"
        assert link.created_at == now
        assert link.metadata.title == "Test"
    
    def test_from_document_snapshot_exists(self):
        """Test conversion from existing DocumentSnapshot"""
        now = datetime.now()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "long_url": "https://example.com",
            "base_domain": "go2.video",
            "created_at": now,
            "disabled": False,
            "owner_uid": None,
            "password_hash": None,
            "expires_at": None,
            "created_by_ip": None,
            "metadata": {},
            "plan_type": "free",
            "is_custom_code": False
        }
        
        link = FirestoreConverter.from_document_snapshot(mock_doc, LinkDocument)
        
        assert link is not None
        assert str(link.long_url) == "https://example.com/"
        assert link.base_domain == "go2.video"
    
    def test_from_document_snapshot_not_exists(self):
        """Test conversion from non-existing DocumentSnapshot"""
        mock_doc = Mock()
        mock_doc.exists = False
        
        result = FirestoreConverter.from_document_snapshot(mock_doc, LinkDocument)
        
        assert result is None


class TestLinkConverter:
    """Test cases for LinkConverter"""
    
    def test_to_firestore(self):
        """Test LinkDocument to Firestore conversion"""
        now = datetime.now()
        metadata = LinkMetadata(title="Test Title")
        link = LinkDocument(
            long_url="https://example.com",
            base_domain="go2.video",
            created_at=now,
            metadata=metadata,
            owner_uid="user123"
        )
        
        firestore_dict = LinkConverter.to_firestore(link)
        
        assert str(firestore_dict["long_url"]) == "https://example.com/"
        assert firestore_dict["owner_uid"] == "user123"
        assert firestore_dict["metadata"]["title"] == "Test Title"
    
    def test_from_firestore(self):
        """Test Firestore to LinkDocument conversion"""
        now = datetime.now()
        firestore_data = {
            "long_url": "https://example.com",
            "base_domain": "go2.reviews",
            "created_at": now,
            "disabled": False,
            "owner_uid": "user123",
            "password_hash": None,
            "expires_at": None,
            "created_by_ip": None,
            "metadata": {"title": "Test"},
            "plan_type": "paid",
            "is_custom_code": True
        }
        
        link = LinkConverter.from_firestore(firestore_data)
        
        assert str(link.long_url) == "https://example.com/"
        assert link.base_domain == "go2.reviews"
        assert link.owner_uid == "user123"
        assert link.plan_type == "paid"
        assert link.is_custom_code is True
    
    def test_from_firestore_missing_metadata(self):
        """Test conversion when metadata is missing"""
        now = datetime.now()
        firestore_data = {
            "long_url": "https://example.com",
            "base_domain": "go2.tools",
            "created_at": now,
            "disabled": False,
            "owner_uid": None,
            "password_hash": None,
            "expires_at": None,
            "created_by_ip": None,
            # metadata missing
            "plan_type": "free",
            "is_custom_code": False
        }
        
        link = LinkConverter.from_firestore(firestore_data)
        
        assert link.metadata.title is None
        assert link.metadata.host is None


class TestUserConverter:
    """Test cases for UserConverter"""
    
    def test_to_firestore(self):
        """Test UserDocument to Firestore conversion"""
        now = datetime.now()
        user = UserDocument(
            email="test@example.com",
            display_name="Test User",
            plan_type="paid",
            custom_codes_used=10,
            custom_codes_reset_date=now,
            created_at=now,
            last_login=now,
            is_admin=True
        )
        
        firestore_dict = UserConverter.to_firestore(user)
        
        assert firestore_dict["email"] == "test@example.com"
        assert firestore_dict["plan_type"] == "paid"
        assert firestore_dict["custom_codes_used"] == 10
        assert firestore_dict["is_admin"] is True
    
    def test_from_firestore(self):
        """Test Firestore to UserDocument conversion"""
        now = datetime.now()
        firestore_data = {
            "email": "test@example.com",
            "display_name": "Test User",
            "plan_type": "free",
            "custom_codes_used": 3,
            "custom_codes_reset_date": now,
            "created_at": now,
            "last_login": now,
            "is_admin": False
        }
        
        user = UserConverter.from_firestore(firestore_data)
        
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.plan_type == "free"
        assert user.custom_codes_used == 3


class TestClickConverter:
    """Test cases for ClickConverter"""
    
    def test_to_firestore(self):
        """Test ClickDocument to Firestore conversion"""
        now = datetime.now()
        location = LocationData(
            country="United States",
            country_code="US",
            city="San Francisco"
        )
        click = ClickDocument(
            ts=now,
            ip_hash="hashed_ip",
            ua="Mozilla/5.0...",
            location=location,
            device_type="desktop"
        )
        
        firestore_dict = ClickConverter.to_firestore(click)
        
        assert firestore_dict["ts"] == now.isoformat()
        assert firestore_dict["device_type"] == "desktop"
        assert firestore_dict["location"]["country"] == "United States"
        assert firestore_dict["location"]["country_code"] == "US"
    
    def test_from_firestore_missing_location(self):
        """Test conversion when location is missing"""
        now = datetime.now()
        firestore_data = {
            "ts": now,
            "ip_hash": "hashed_ip",
            "ua": "Mozilla/5.0...",
            "referrer": None,
            # location missing
            "device_type": "mobile",
            "browser": "Chrome",
            "os": "iOS"
        }
        
        click = ClickConverter.from_firestore(firestore_data)
        
        assert click.location.country is None
        assert click.device_type == "mobile"


class TestConfigConverter:
    """Test cases for ConfigConverter"""
    
    def test_to_firestore(self):
        """Test ConfigDocument to Firestore conversion"""
        safety_settings = SafetySettings(
            enable_safe_browsing=True,
            blacklist_domains=["spam.com"],
            blacklist_keywords=["spam"]
        )
        plan_limits = PlanLimits(
            free={"custom_codes": 5},
            paid={"custom_codes": 100}
        )
        config = ConfigDocument(
            base_domains=["go2.video", "go2.reviews"],
            domain_suggestions={"youtube.com": "go2.video"},
            safety_settings=safety_settings,
            plan_limits=plan_limits
        )
        
        firestore_dict = ConfigConverter.to_firestore(config)
        
        assert len(firestore_dict["base_domains"]) == 2
        assert firestore_dict["domain_suggestions"]["youtube.com"] == "go2.video"
        assert firestore_dict["safety_settings"]["enable_safe_browsing"] is True
        assert firestore_dict["plan_limits"]["free"]["custom_codes"] == 5
    
    def test_from_firestore_missing_nested_objects(self):
        """Test conversion when nested objects are missing"""
        firestore_data = {
            "base_domains": ["go2.video"]
            # safety_settings, plan_limits, domain_suggestions missing
        }
        
        config = ConfigConverter.from_firestore(firestore_data)
        
        assert len(config.base_domains) == 1
        assert config.safety_settings.enable_safe_browsing is True  # Default
        assert config.plan_limits.free["custom_codes"] == 5  # Default
        assert len(config.domain_suggestions) == 0  # Default


class TestBatchConverter:
    """Test cases for BatchConverter"""
    
    def test_links_from_snapshots(self):
        """Test batch conversion of link snapshots"""
        now = datetime.now()
        
        # Mock snapshots
        mock_doc1 = Mock()
        mock_doc1.exists = True
        mock_doc1.to_dict.return_value = {
            "long_url": "https://example1.com",
            "base_domain": "go2.video",
            "created_at": now,
            "disabled": False,
            "owner_uid": None,
            "password_hash": None,
            "expires_at": None,
            "created_by_ip": None,
            "metadata": {},
            "plan_type": "free",
            "is_custom_code": False
        }
        
        mock_doc2 = Mock()
        mock_doc2.exists = True
        mock_doc2.to_dict.return_value = {
            "long_url": "https://example2.com",
            "base_domain": "go2.reviews",
            "created_at": now,
            "disabled": False,
            "owner_uid": None,
            "password_hash": None,
            "expires_at": None,
            "created_by_ip": None,
            "metadata": {},
            "plan_type": "free",
            "is_custom_code": False
        }
        
        mock_doc3 = Mock()
        mock_doc3.exists = False  # This one doesn't exist
        
        docs = [mock_doc1, mock_doc2, mock_doc3]
        links = BatchConverter.links_from_snapshots(docs)
        
        assert len(links) == 2  # Only existing docs converted
        assert str(links[0].long_url) == "https://example1.com/"
        assert str(links[1].long_url) == "https://example2.com/"


class TestUtilityFunctions:
    """Test cases for utility functions"""
    
    def test_serialize_for_json(self):
        """Test JSON serialization utility"""
        now = datetime.now()
        link = LinkDocument(
            long_url="https://example.com",
            base_domain="go2.video",
            created_at=now
        )
        
        json_data = serialize_for_json(link)
        
        assert str(json_data["long_url"]) == "https://example.com/"
        assert json_data["base_domain"] == "go2.video"
        assert isinstance(json_data["created_at"], str)  # Now serialized as ISO string
    
    def test_deserialize_from_json(self):
        """Test JSON deserialization utility"""
        now = datetime.now()
        json_data = {
            "long_url": "https://example.com",
            "base_domain": "go2.video",
            "created_at": now,
            "disabled": False,
            "owner_uid": None,
            "password_hash": None,
            "expires_at": None,
            "created_by_ip": None,
            "metadata": {},
            "plan_type": "free",
            "is_custom_code": False
        }
        
        link = deserialize_from_json(json_data, LinkDocument)
        
        assert str(link.long_url) == "https://example.com/"
        assert link.base_domain == "go2.video"
        assert link.created_at == now
    
    def test_validate_and_convert_valid(self):
        """Test validation and conversion with valid data"""
        now = datetime.now()
        data = {
            "long_url": "https://example.com",
            "base_domain": "go2.video",
            "created_at": now,
            "disabled": False,
            "owner_uid": None,
            "password_hash": None,
            "expires_at": None,
            "created_by_ip": None,
            "metadata": {},
            "plan_type": "free",
            "is_custom_code": False
        }
        
        link = validate_and_convert(data, LinkDocument)
        
        assert str(link.long_url) == "https://example.com/"
        assert link.base_domain == "go2.video"
    
    def test_validate_and_convert_invalid(self):
        """Test validation and conversion with invalid data"""
        invalid_data = {
            "long_url": "not-a-url",  # Invalid URL
            "base_domain": "invalid-domain"  # Invalid domain
        }
        
        with pytest.raises(ValueError) as exc_info:
            validate_and_convert(invalid_data, LinkDocument)
        
        assert "Invalid data for LinkDocument" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])