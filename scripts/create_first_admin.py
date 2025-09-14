#!/usr/bin/env python3
"""
Script to create the first admin user.
Run this once to bootstrap the admin system.
"""

import os
import sys
import asyncio
from firebase_admin import auth, firestore
from firebase_admin.exceptions import FirebaseError

# Add the API source to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api', 'src'))

from services.firebase_service import firebase_service
from services.user_service import user_service

async def create_first_admin(email: str):
    """Create the first admin user by email"""
    try:
        # Get user by email from Firebase Auth
        user_record = auth.get_user_by_email(email)
        uid = user_record.uid
        
        print(f"Found user: {email} (UID: {uid})")
        
        # Set Firebase custom claims
        auth.set_custom_user_claims(uid, {'admin': True})
        print("✅ Set Firebase custom claims")
        
        # Update Firestore user document
        user_ref = firebase_service.db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            # Update existing user
            user_ref.update({'is_admin': True})
            print("✅ Updated existing user document")
        else:
            # Create user document if it doesn't exist
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            
            user_data = {
                'email': email,
                'display_name': user_record.display_name or email.split('@')[0],
                'plan_type': 'paid',  # Give admin paid plan
                'custom_codes_used': 0,
                'custom_codes_reset_date': now + timedelta(days=30),
                'created_at': now,
                'last_login': now,
                'is_admin': True
            }
            
            user_ref.set(user_data)
            print("✅ Created new admin user document")
        
        # Log the admin creation
        await user_service.log_admin_action(
            admin_uid=uid,
            action='create_first_admin',
            details={'email': email, 'created_by': 'bootstrap_script'}
        )
        
        print(f"🎉 Successfully created admin user: {email}")
        print(f"   UID: {uid}")
        print(f"   The user can now access /admin in the web app")
        
    except FirebaseError as e:
        print(f"❌ Firebase error: {e}")
        if "USER_NOT_FOUND" in str(e):
            print(f"   User {email} not found. Please ensure they have signed up first.")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python create_first_admin.py <admin_email>")
        print("Example: python create_first_admin.py admin@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    
    print(f"Creating first admin user: {email}")
    print("Make sure this user has already signed up to the application!")
    
    confirm = input("Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    asyncio.run(create_first_admin(email))

if __name__ == "__main__":
    main()