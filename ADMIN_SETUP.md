# Admin Setup Guide

This guide explains how to identify yourself as an admin and manage admin privileges in the URL shortener system.

## How Admin Status Works

The system uses a **dual-layer approach** for admin identification:

1. **Firebase Custom Claims**: `{ admin: true }` in the user's ID token
2. **Firestore Database**: `is_admin: true` in the user document

Both must be set for full admin functionality.

## Methods to Become Admin

### Method 1: Bootstrap First Admin (Recommended for Initial Setup)

#### Option A: Environment Variable
1. Set the `FIRST_ADMIN_EMAIL` environment variable in your `.env` file:
   ```bash
   FIRST_ADMIN_EMAIL=your-email@example.com
   ```

2. Sign up normally through the web interface with that exact email
3. The system will automatically grant admin privileges on first login

#### Option B: Bootstrap Script
1. First, sign up normally through the web interface
2. Run the bootstrap script:
   ```bash
   cd scripts
   python create_first_admin.py your-email@example.com
   ```

### Method 2: Promoted by Existing Admin

Once you have at least one admin, they can promote other users:

1. Admin logs into the web interface
2. Navigate to `/admin` 
3. Go to the "Users" tab
4. Find the user to promote
5. Click "Make Admin" button

**Note**: Admins cannot revoke their own admin status (safety feature).

### Method 3: Direct Firebase Console (Advanced)

If you have Firebase Console access:

1. Go to Firebase Console → Authentication → Users
2. Find the user and click on them
3. Go to "Custom claims" tab
4. Add: `{"admin": true}`
5. Also update the Firestore `users` collection document to set `is_admin: true`

## Verifying Admin Status

### Frontend Check
```typescript
const { user } = useAuth();
const isAdmin = user?.customClaims?.admin === true;
```

### Backend Check
The system checks both:
- Firebase ID token custom claims: `user.get('admin', False)`
- Firestore user document: `user_doc.is_admin`

## Admin Capabilities

Once you have admin status, you can:

### Access Admin Dashboard
- Navigate to `/admin` in the web interface
- View system statistics and metrics

### User Management
- View all users
- Upgrade/downgrade user plans
- Grant/revoke admin privileges
- View user usage statistics

### Link Management
- View all links in the system
- Bulk disable links
- Bulk delete links
- Bulk update link expiry dates
- View link ownership and statistics

### System Monitoring
- View system-wide statistics
- Monitor user activity
- Track link creation and usage

### Audit Trail
- View all administrative actions
- See who performed what actions and when
- Track system changes

## Security Features

### Permission Enforcement
- All admin routes require valid admin token
- Frontend components check admin status
- Backend validates both custom claims and database records

### Audit Logging
- All admin actions are logged with timestamps
- Includes admin UID, action type, and details
- Searchable audit trail

### Self-Protection
- Admins cannot revoke their own admin status
- Prevents accidental lockout scenarios

## Troubleshooting

### "Access Denied" Error
1. Verify you have admin custom claims: Check Firebase Console
2. Verify database record: Check Firestore `users` collection
3. Try logging out and back in to refresh token
4. Check browser console for authentication errors

### Admin Interface Not Loading
1. Ensure you're accessing `/admin` URL
2. Check that admin components are properly imported
3. Verify API endpoints are responding (check Network tab)

### Cannot Promote Other Users
1. Verify your own admin status first
2. Check that target user exists in the system
3. Ensure target user has signed up at least once
4. Check browser console for API errors

## API Endpoints

### Admin User Management
- `GET /api/users/admin/all` - List all users
- `GET /api/users/admin/{uid}` - Get user by ID  
- `PUT /api/users/admin/{uid}/plan` - Update user plan
- `PUT /api/users/admin/{uid}/admin-status` - Toggle admin status
- `GET /api/users/admin/stats/overview` - System statistics
- `GET /api/users/admin/audit-log` - Audit log

### Admin Link Management
- `GET /api/links/admin/all` - List all links
- `POST /api/links/admin/bulk-disable` - Bulk disable links
- `POST /api/links/admin/bulk-delete` - Bulk delete links  
- `POST /api/links/admin/bulk-update-expiry` - Bulk update expiry

All admin endpoints require `Authorization: Bearer <firebase_id_token>` header with admin custom claims.

## Best Practices

1. **Always have multiple admins** - Don't rely on a single admin account
2. **Use strong authentication** - Enable 2FA on admin Firebase accounts
3. **Monitor audit logs** - Regularly review administrative actions
4. **Principle of least privilege** - Only grant admin to users who need it
5. **Regular access reviews** - Periodically review who has admin access

## Development vs Production

### Development
- Use environment variable method for quick setup
- Bootstrap script is fine for testing

### Production  
- Use Firebase Console method for initial admin
- Have multiple admins for redundancy
- Enable Firebase security rules
- Monitor audit logs regularly
- Use proper authentication flows