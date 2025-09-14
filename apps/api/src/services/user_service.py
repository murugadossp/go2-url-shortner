from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from google.cloud.firestore import Client
from ..models.user import UserDocument, UserProfileResponse, PlanType
from ..services.firebase_service import firebase_service
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.db: Client = firebase_service.db
        self.users_collection = self.db.collection('users')
        self.audit_collection = self.db.collection('audit_log')
        
        # Plan limits
        self.plan_limits = {
            'free': {'custom_codes': 5},
            'paid': {'custom_codes': 100}
        }
    
    async def get_or_create_user(self, user_token: Dict[str, Any]) -> UserDocument:
        """Get existing user or create new user from Firebase token"""
        uid = user_token['uid']
        email = user_token.get('email', '')
        display_name = user_token.get('name', email.split('@')[0] if email else 'User')
        
        user_ref = self.users_collection.document(uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            # Update last login
            user_data = user_doc.to_dict()
            user_ref.update({'last_login': datetime.utcnow()})
            user_data['last_login'] = datetime.utcnow()
            return UserDocument(**user_data)
        else:
            # Create new user
            now = datetime.utcnow()
            reset_date = now + timedelta(days=30)  # Monthly reset for custom codes
            
            # Check if this should be the first admin (bootstrap)
            import os
            first_admin_email = os.getenv('FIRST_ADMIN_EMAIL')
            is_first_admin = (first_admin_email and email.lower() == first_admin_email.lower())
            
            new_user = UserDocument(
                email=email,
                display_name=display_name,
                plan_type='paid' if is_first_admin else 'free',
                custom_codes_used=0,
                custom_codes_reset_date=reset_date,
                created_at=now,
                last_login=now,
                is_admin=is_first_admin
            )
            
            user_ref.set(new_user.model_dump())
            
            # Log the bootstrap action for first admin
            if is_first_admin:
                logger.info(f"Created first admin user: {email}")
                
                # Log the bootstrap action
                await self.log_admin_action(
                    admin_uid=uid,
                    action='bootstrap_first_admin',
                    details={'email': email, 'method': 'environment_variable'}
                )
            
            return new_user
    
    async def get_user_profile(self, uid: str) -> Optional[UserProfileResponse]:
        """Get user profile with calculated remaining limits"""
        user_ref = self.users_collection.document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return None
        
        user_data = user_doc.to_dict()
        user = UserDocument(**user_data)
        
        # Check if custom codes need to be reset (monthly)
        if datetime.utcnow() > user.custom_codes_reset_date:
            user.custom_codes_used = 0
            user.custom_codes_reset_date = datetime.utcnow() + timedelta(days=30)
            user_ref.update({
                'custom_codes_used': 0,
                'custom_codes_reset_date': user.custom_codes_reset_date
            })
        
        # Calculate remaining custom codes
        plan_limit = self.plan_limits[user.plan_type]['custom_codes']
        custom_codes_remaining = max(0, plan_limit - user.custom_codes_used)
        
        return UserProfileResponse(
            email=user.email,
            display_name=user.display_name,
            plan_type=user.plan_type,
            custom_codes_used=user.custom_codes_used,
            custom_codes_remaining=custom_codes_remaining,
            custom_codes_reset_date=user.custom_codes_reset_date,
            created_at=user.created_at,
            is_admin=user.is_admin
        )
    
    async def update_user_profile(self, uid: str, display_name: str) -> bool:
        """Update user profile"""
        try:
            user_ref = self.users_collection.document(uid)
            user_ref.update({'display_name': display_name})
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    async def increment_custom_code_usage(self, uid: str) -> bool:
        """Increment custom code usage for user"""
        try:
            user_ref = self.users_collection.document(uid)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                return False
            
            user_data = user_doc.to_dict()
            user = UserDocument(**user_data)
            
            # Check if reset is needed
            if datetime.utcnow() > user.custom_codes_reset_date:
                user_ref.update({
                    'custom_codes_used': 1,
                    'custom_codes_reset_date': datetime.utcnow() + timedelta(days=30)
                })
            else:
                user_ref.update({
                    'custom_codes_used': user.custom_codes_used + 1
                })
            
            return True
        except Exception as e:
            logger.error(f"Error incrementing custom code usage: {e}")
            return False
    
    async def can_create_custom_code(self, uid: str) -> bool:
        """Check if user can create another custom code"""
        user_profile = await self.get_user_profile(uid)
        if not user_profile:
            return False
        
        return user_profile.custom_codes_remaining > 0
    
    async def upgrade_user_plan(self, uid: str, plan_type: PlanType) -> bool:
        """Upgrade user plan (in real app, this would integrate with payment system)"""
        try:
            user_ref = self.users_collection.document(uid)
            user_ref.update({'plan_type': plan_type})
            return True
        except Exception as e:
            logger.error(f"Error upgrading user plan: {e}")
            return False
    
    async def get_user_usage_stats(self, uid: str) -> Dict[str, Any]:
        """Get user usage statistics"""
        user_profile = await self.get_user_profile(uid)
        if not user_profile:
            return {}
        
        # Get link count for user
        from google.cloud.firestore import FieldFilter
        links_query = self.db.collection('links').where(filter=FieldFilter('owner_uid', '==', uid))
        links = links_query.get()
        
        total_links = len(links)
        custom_code_links = sum(1 for link in links if link.to_dict().get('is_custom_code', False))
        
        # Calculate total clicks across all user's links
        total_clicks = 0
        for link in links:
            clicks_collection = link.reference.collection('clicks')
            clicks = clicks_collection.get()
            total_clicks += len(clicks)
        
        return {
            'total_links': total_links,
            'custom_code_links': custom_code_links,
            'total_clicks': total_clicks,
            'plan_type': user_profile.plan_type,
            'custom_codes_used': user_profile.custom_codes_used,
            'custom_codes_remaining': user_profile.custom_codes_remaining,
            'custom_codes_reset_date': user_profile.custom_codes_reset_date
        }
    
    # Admin methods
    async def list_all_users(self, limit: int = 100, offset: int = 0) -> List[UserProfileResponse]:
        """List all users with pagination (admin only)"""
        try:
            users_query = self.users_collection.limit(limit).offset(offset).order_by('created_at', direction='DESCENDING')
            users = users_query.get()
            
            user_profiles = []
            for user_doc in users:
                user_data = user_doc.to_dict()
                user = UserDocument(**user_data)
                
                # Check if custom codes need to be reset
                if datetime.utcnow() > user.custom_codes_reset_date:
                    user.custom_codes_used = 0
                    user.custom_codes_reset_date = datetime.utcnow() + timedelta(days=30)
                
                # Calculate remaining custom codes
                plan_limit = self.plan_limits[user.plan_type]['custom_codes']
                custom_codes_remaining = max(0, plan_limit - user.custom_codes_used)
                
                user_profiles.append(UserProfileResponse(
                    email=user.email,
                    display_name=user.display_name,
                    plan_type=user.plan_type,
                    custom_codes_used=user.custom_codes_used,
                    custom_codes_remaining=custom_codes_remaining,
                    custom_codes_reset_date=user.custom_codes_reset_date,
                    created_at=user.created_at,
                    is_admin=user.is_admin
                ))
            
            return user_profiles
        except Exception as e:
            logger.error(f"Error listing all users: {e}")
            return []
    
    async def set_admin_status(self, uid: str, is_admin: bool) -> bool:
        """Set admin status for a user"""
        try:
            user_ref = self.users_collection.document(uid)
            user_ref.update({'is_admin': is_admin})
            return True
        except Exception as e:
            logger.error(f"Error setting admin status: {e}")
            return False
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics with robust error handling"""
        stats = {
            'users': {
                'total': 0,
                'free': 0,
                'paid': 0,
                'admin': 0,
                'recent_signups': 0
            },
            'links': {
                'total': 0,
                'custom_codes': 0,
                'disabled': 0,
                'recent_created': 0
            },
            'engagement': {
                'total_clicks': 0,
                'avg_clicks_per_link': 0
            },
            'last_updated': datetime.utcnow().isoformat(),
            'errors': []
        }
        
        # Get user statistics
        try:
            users_query = self.users_collection
            all_users = users_query.get()
            
            stats['users']['total'] = len(all_users)
            stats['users']['free'] = sum(1 for user in all_users if user.to_dict().get('plan_type') == 'free')
            stats['users']['paid'] = stats['users']['total'] - stats['users']['free']
            stats['users']['admin'] = sum(1 for user in all_users if user.to_dict().get('is_admin', False))
            
            # Recent activity (last 7 days) with safe date comparison
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_signups = 0
            for user in all_users:
                user_data = user.to_dict()
                created_at = user_data.get('created_at')
                if created_at:
                    # Handle both datetime objects and ISO string formats
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            continue
                    elif hasattr(created_at, 'timestamp'):  # Firestore timestamp
                        created_at = created_at
                    
                    if isinstance(created_at, datetime) and created_at > seven_days_ago:
                        recent_signups += 1
            
            stats['users']['recent_signups'] = recent_signups
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            stats['errors'].append(f"User statistics unavailable: {str(e)}")
        
        # Get link statistics (simplified to avoid index issues)
        try:
            # Use simple queries that don't require composite indexes
            links_collection = self.db.collection('links')
            
            # Basic count
            all_links = links_collection.get()
            stats['links']['total'] = len(all_links)
            
            # Count different types
            custom_code_links = 0
            disabled_links = 0
            recent_links = 0
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            for link in all_links:
                link_data = link.to_dict()
                if link_data.get('is_custom_code', False):
                    custom_code_links += 1
                if link_data.get('disabled', False):
                    disabled_links += 1
                
                # Safe date comparison for recent links
                created_at = link_data.get('created_at')
                if created_at:
                    # Handle both datetime objects and ISO string formats
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            continue
                    elif hasattr(created_at, 'timestamp'):  # Firestore timestamp
                        created_at = created_at
                    
                    if isinstance(created_at, datetime) and created_at > seven_days_ago:
                        recent_links += 1
            
            stats['links']['custom_codes'] = custom_code_links
            stats['links']['disabled'] = disabled_links
            stats['links']['recent_created'] = recent_links
            
        except Exception as e:
            logger.error(f"Error getting link stats: {e}")
            stats['errors'].append(f"Link statistics unavailable: {str(e)}")
        
        # Get engagement statistics (with better error handling)
        try:
            total_clicks = 0
            links_with_clicks = 0
            
            # Sample a subset of links for click counting to avoid timeout
            links_collection = self.db.collection('links')
            sample_links = links_collection.limit(100).get()  # Sample first 100 links
            
            for link in sample_links:
                try:
                    clicks_collection = link.reference.collection('clicks')
                    clicks = clicks_collection.get()
                    click_count = len(clicks)
                    if click_count > 0:
                        total_clicks += click_count
                        links_with_clicks += 1
                except Exception as e:
                    # Skip this link if clicks can't be counted
                    logger.debug(f"Skipping click count for link {link.id}: {e}")
                    continue
            
            stats['engagement']['total_clicks'] = total_clicks
            if stats['links']['total'] > 0:
                # Estimate total clicks based on sample
                if len(sample_links) < stats['links']['total']:
                    # Extrapolate from sample
                    sample_ratio = len(sample_links) / stats['links']['total']
                    estimated_total_clicks = int(total_clicks / sample_ratio) if sample_ratio > 0 else 0
                    stats['engagement']['total_clicks'] = estimated_total_clicks
                    stats['engagement']['estimated'] = True
                
                stats['engagement']['avg_clicks_per_link'] = round(
                    stats['engagement']['total_clicks'] / max(stats['links']['total'], 1), 2
                )
            
        except Exception as e:
            logger.error(f"Error getting engagement stats: {e}")
            stats['errors'].append(f"Engagement statistics unavailable: {str(e)}")
        
        # Remove errors field if no errors occurred
        if not stats['errors']:
            del stats['errors']
        
        logger.info(f"System stats generated successfully with {len(stats.get('errors', []))} errors")
        return stats
    

# Global instance
user_service = UserService()
