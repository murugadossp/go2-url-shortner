import os
import json
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from firebase_admin.exceptions import FirebaseError
import logging
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

class FirebaseService:
    """Service for Firebase Admin SDK operations"""
    
    def __init__(self):
        self._app = None
        self._db = None
        self._storage_bucket = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Always delete existing apps to ensure clean initialization
            if firebase_admin._apps:
                for app_name in list(firebase_admin._apps.keys()):
                    firebase_admin.delete_app(firebase_admin._apps[app_name])
                    logger.info(f"Deleted existing Firebase app: {app_name}")
            
            # Force fresh initialization
            # Initialize from service account key file or environment
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
            
            if service_account_path and os.path.exists(service_account_path):
                # Initialize with service account file
                cred = credentials.Certificate(service_account_path)
                self._app = firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
                })
                logger.info("Firebase initialized with service account file")
            else:
                # Initialize with environment variables (for production)
                service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
                if service_account_json:
                    service_account_info = json.loads(service_account_json)
                    cred = credentials.Certificate(service_account_info)
                    self._app = firebase_admin.initialize_app(cred, {
                        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
                    })
                    logger.info(f"Firebase initialized with service account JSON for project: {service_account_info.get('project_id')}")
                else:
                    # Initialize with default credentials (for local development)
                    self._app = firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
            
            # Initialize services
            self._db = firestore.client()
            if os.getenv('FIREBASE_STORAGE_BUCKET'):
                self._storage_bucket = storage.bucket()
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    @property
    def db(self) -> firestore.Client:
        """Get Firestore client"""
        if not self._db:
            raise RuntimeError("Firestore not initialized")
        return self._db
    
    @property
    def storage_bucket(self):
        """Get Storage bucket"""
        if not self._storage_bucket:
            raise RuntimeError("Storage bucket not initialized")
        return self._storage_bucket
    
    async def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return decoded token"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except FirebaseError as e:
            logger.error(f"Token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error verifying token: {e}")
            return None
    
    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user by UID"""
        try:
            user_record = auth.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'email_verified': user_record.email_verified,
                'disabled': user_record.disabled,
                'custom_claims': user_record.custom_claims or {}
            }
        except FirebaseError as e:
            logger.error(f"Failed to get user {uid}: {e}")
            return None
    
    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
        """Set custom claims for a user"""
        try:
            auth.set_custom_user_claims(uid, claims)
            return True
        except FirebaseError as e:
            logger.error(f"Failed to set custom claims for {uid}: {e}")
            return False

# Global Firebase service instance
firebase_service = FirebaseService()