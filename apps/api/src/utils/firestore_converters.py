"""
Firestore document converters and serializers for data models.
Handles conversion between Pydantic models and Firestore documents.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar
from google.cloud.firestore import DocumentSnapshot
from pydantic import BaseModel

from ..models.link import LinkDocument, LinkMetadata
from ..models.user import UserDocument
from ..models.analytics import ClickDocument, LocationData
from ..models.config import ConfigDocument, SafetySettings, PlanLimits

T = TypeVar('T', bound=BaseModel)


class FirestoreConverter:
    """Base class for Firestore document conversion"""
    
    @staticmethod
    def to_firestore_dict(model: BaseModel) -> Dict[str, Any]:
        """Convert Pydantic model to Firestore-compatible dictionary"""
        data = model.model_dump()
        
        # Convert datetime objects to Firestore timestamps
        def convert_datetime(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj  # Firestore handles datetime objects natively
            else:
                return obj
        
        return convert_datetime(data)
    
    @staticmethod
    def from_firestore_dict(data: Dict[str, Any], model_class: Type[T]) -> T:
        """Convert Firestore dictionary to Pydantic model"""
        # Convert Firestore timestamps to datetime objects
        def convert_timestamp(obj):
            if isinstance(obj, dict):
                return {k: convert_timestamp(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_timestamp(item) for item in obj]
            elif hasattr(obj, 'timestamp'):  # Firestore timestamp
                return datetime.fromtimestamp(obj.timestamp())
            else:
                return obj
        
        converted_data = convert_timestamp(data)
        return model_class(**converted_data)
    
    @staticmethod
    def from_document_snapshot(doc: DocumentSnapshot, model_class: Type[T]) -> Optional[T]:
        """Convert Firestore DocumentSnapshot to Pydantic model"""
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        return FirestoreConverter.from_firestore_dict(data, model_class)


class LinkConverter(FirestoreConverter):
    """Converter for Link documents"""
    
    @staticmethod
    def to_firestore(link: LinkDocument) -> Dict[str, Any]:
        """Convert LinkDocument to Firestore dictionary"""
        return FirestoreConverter.to_firestore_dict(link)
    
    @staticmethod
    def from_firestore(data: Dict[str, Any]) -> LinkDocument:
        """Convert Firestore dictionary to LinkDocument"""
        # Ensure metadata is properly structured
        if 'metadata' not in data:
            data['metadata'] = {}
        
        return FirestoreConverter.from_firestore_dict(data, LinkDocument)
    
    @staticmethod
    def from_snapshot(doc: DocumentSnapshot) -> Optional[LinkDocument]:
        """Convert DocumentSnapshot to LinkDocument"""
        return FirestoreConverter.from_document_snapshot(doc, LinkDocument)


class UserConverter(FirestoreConverter):
    """Converter for User documents"""
    
    @staticmethod
    def to_firestore(user: UserDocument) -> Dict[str, Any]:
        """Convert UserDocument to Firestore dictionary"""
        return FirestoreConverter.to_firestore_dict(user)
    
    @staticmethod
    def from_firestore(data: Dict[str, Any]) -> UserDocument:
        """Convert Firestore dictionary to UserDocument"""
        return FirestoreConverter.from_firestore_dict(data, UserDocument)
    
    @staticmethod
    def from_snapshot(doc: DocumentSnapshot) -> Optional[UserDocument]:
        """Convert DocumentSnapshot to UserDocument"""
        return FirestoreConverter.from_document_snapshot(doc, UserDocument)


class ClickConverter(FirestoreConverter):
    """Converter for Click documents"""
    
    @staticmethod
    def to_firestore(click: ClickDocument) -> Dict[str, Any]:
        """Convert ClickDocument to Firestore dictionary"""
        return FirestoreConverter.to_firestore_dict(click)
    
    @staticmethod
    def from_firestore(data: Dict[str, Any]) -> ClickDocument:
        """Convert Firestore dictionary to ClickDocument"""
        # Ensure location is properly structured
        if 'location' not in data:
            data['location'] = {}
        
        return FirestoreConverter.from_firestore_dict(data, ClickDocument)
    
    @staticmethod
    def from_snapshot(doc: DocumentSnapshot) -> Optional[ClickDocument]:
        """Convert DocumentSnapshot to ClickDocument"""
        return FirestoreConverter.from_document_snapshot(doc, ClickDocument)


class ConfigConverter(FirestoreConverter):
    """Converter for Config documents"""
    
    @staticmethod
    def to_firestore(config: ConfigDocument) -> Dict[str, Any]:
        """Convert ConfigDocument to Firestore dictionary"""
        return FirestoreConverter.to_firestore_dict(config)
    
    @staticmethod
    def from_firestore(data: Dict[str, Any]) -> ConfigDocument:
        """Convert Firestore dictionary to ConfigDocument"""
        # Ensure nested objects are properly structured
        if 'safety_settings' not in data:
            data['safety_settings'] = {}
        if 'plan_limits' not in data:
            data['plan_limits'] = {"free": {"custom_codes": 5}, "paid": {"custom_codes": 100}}
        if 'domain_suggestions' not in data:
            data['domain_suggestions'] = {}
        
        return FirestoreConverter.from_firestore_dict(data, ConfigDocument)
    
    @staticmethod
    def from_snapshot(doc: DocumentSnapshot) -> Optional[ConfigDocument]:
        """Convert DocumentSnapshot to ConfigDocument"""
        return FirestoreConverter.from_document_snapshot(doc, ConfigDocument)


class BatchConverter:
    """Utility for batch conversions"""
    
    @staticmethod
    def links_from_snapshots(docs: list[DocumentSnapshot]) -> list[LinkDocument]:
        """Convert multiple DocumentSnapshots to LinkDocuments"""
        links = []
        for doc in docs:
            link = LinkConverter.from_snapshot(doc)
            if link:
                links.append(link)
        return links
    
    @staticmethod
    def clicks_from_snapshots(docs: list[DocumentSnapshot]) -> list[ClickDocument]:
        """Convert multiple DocumentSnapshots to ClickDocuments"""
        clicks = []
        for doc in docs:
            click = ClickConverter.from_snapshot(doc)
            if click:
                clicks.append(click)
        return clicks
    
    @staticmethod
    def users_from_snapshots(docs: list[DocumentSnapshot]) -> list[UserDocument]:
        """Convert multiple DocumentSnapshots to UserDocuments"""
        users = []
        for doc in docs:
            user = UserConverter.from_snapshot(doc)
            if user:
                users.append(user)
        return users


# Utility functions for common operations
def serialize_for_json(model: BaseModel) -> Dict[str, Any]:
    """Serialize Pydantic model for JSON response"""
    return model.model_dump()


def deserialize_from_json(data: Dict[str, Any], model_class: Type[T]) -> T:
    """Deserialize JSON data to Pydantic model"""
    return model_class(**data)


def validate_and_convert(data: Dict[str, Any], model_class: Type[T]) -> T:
    """Validate and convert dictionary data to Pydantic model"""
    try:
        return model_class(**data)
    except Exception as e:
        raise ValueError(f"Invalid data for {model_class.__name__}: {str(e)}")