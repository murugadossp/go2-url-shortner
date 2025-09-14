# Firebase Setup Guide

This guide walks you through setting up Firebase for the Contextual URL Shortener project.

## Prerequisites

- Node.js and npm installed
- Python 3.9+ installed
- Firebase CLI installed (`npm install -g firebase-tools`)
- Google Cloud account

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter project name (e.g., "contextual-url-shortener")
4. Enable Google Analytics (optional)
5. Wait for project creation

## Step 2: Enable Firebase Services

### Authentication
1. In Firebase Console, go to Authentication > Sign-in method
2. Enable "Google" provider
3. Add your domain to authorized domains
4. Note down the Web SDK configuration

### Firestore Database
1. Go to Firestore Database
2. Click "Create database"
3. Choose "Start in test mode" (we'll deploy security rules later)
4. Select a location close to your users

### Storage
1. Go to Storage
2. Click "Get started"
3. Choose "Start in test mode"
4. Select the same location as Firestore

## Step 3: Configure Web App

1. In Firebase Console, go to Project Settings
2. Scroll down to "Your apps" section
3. Click "Add app" > Web app icon
4. Register app with a nickname
5. Copy the Firebase configuration object

## Step 4: Set Up Service Account

1. Go to Project Settings > Service accounts
2. Click "Generate new private key"
3. Download the JSON file
4. Save it as `firebase-service-account.json` in the `apps/api/` directory
5. **Important**: Add this file to `.gitignore` (already done)

## Step 5: Configure Environment Variables

### Frontend (.env.local in apps/web/)
```bash
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Backend (.env in apps/api/)
```bash
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
```

## Step 6: Deploy Security Rules

```bash
# Install Firebase CLI if not already installed
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in your project root
firebase init

# Select:
# - Firestore: Configure security rules and indexes files
# - Storage: Configure security rules file
# - Hosting: Configure files for Firebase Hosting and GitHub Action deploys

# Deploy rules
firebase deploy --only firestore:rules,storage:rules
```

## Step 7: Set Up Admin User

After your first user signs up through Google OAuth:

1. Go to Firebase Console > Authentication > Users
2. Find your user and copy the UID
3. Go to Firestore Database
4. Create a document in the `users` collection with your UID as the document ID
5. Add field: `is_admin: true`

Or use the Firebase CLI:

```bash
# Set custom claims for admin user
firebase auth:set-claims YOUR_USER_UID '{"admin": true}'
```

## Step 8: Test Configuration

1. Start the backend server:
   ```bash
   cd apps/api
   python -m uvicorn src.main:app --reload
   ```

2. Visit `http://localhost:8000/health` - should show Firebase as "connected"

3. Start the frontend:
   ```bash
   cd apps/web
   npm run dev
   ```

4. Visit `http://localhost:3000` and test Google sign-in

## Production Deployment

### Environment Variables for Production

Instead of using a service account file, use environment variables:

```bash
FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'
```

### Security Considerations

1. Never commit service account files to version control
2. Use environment variables for sensitive configuration
3. Regularly rotate service account keys
4. Monitor Firebase usage and set up billing alerts
5. Review and test security rules thoroughly

## Troubleshooting

### Common Issues

1. **"Firebase not initialized"**
   - Check that service account file exists and path is correct
   - Verify environment variables are loaded

2. **"Permission denied" errors**
   - Check Firestore security rules
   - Verify user authentication status
   - Ensure admin claims are set correctly

3. **CORS errors**
   - Add your domain to Firebase authorized domains
   - Check CORS configuration in FastAPI

4. **Token verification failed**
   - Ensure clocks are synchronized
   - Check that project ID matches in all configurations
   - Verify service account has proper permissions

### Useful Commands

```bash
# Check Firebase project status
firebase projects:list

# Test security rules locally
firebase emulators:start --only firestore

# View Firestore data
firebase firestore:get /links/test-code

# Set custom claims
firebase auth:set-claims USER_UID '{"admin": true}'
```