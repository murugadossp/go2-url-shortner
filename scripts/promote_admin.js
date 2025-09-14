const admin = require('firebase-admin');

// Initialize Firebase Admin (make sure you have credentials configured)
if (!admin.apps.length) {
  admin.initializeApp();
}

async function promoteUserToAdmin(email) {
  try {
    // Get user by email
    const userRecord = await admin.auth().getUserByEmail(email);
    console.log(`Found user: ${email} (UID: ${userRecord.uid})`);
    
    // Set custom claims
    await admin.auth().setCustomUserClaims(userRecord.uid, { admin: true });
    console.log('✅ Set Firebase custom claims');
    
    // Update Firestore document
    const db = admin.firestore();
    const userRef = db.collection('users').doc(userRecord.uid);
    const userDoc = await userRef.get();
    
    if (userDoc.exists) {
      await userRef.update({ is_admin: true });
      console.log('✅ Updated existing user document');
    } else {
      // Create user document if it doesn't exist
      const userData = {
        email: email,
        display_name: userRecord.displayName || email.split('@')[0],
        plan_type: 'paid', // Give admin paid plan
        custom_codes_used: 0,
        custom_codes_reset_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
        created_at: new Date(),
        last_login: new Date(),
        is_admin: true
      };
      
      await userRef.set(userData);
      console.log('✅ Created new admin user document');
    }
    
    // Log the action
    await db.collection('audit_log').add({
      admin_uid: userRecord.uid,
      action: 'create_first_admin',
      details: { email: email, created_by: 'manual_script' },
      timestamp: new Date()
    });
    
    console.log(`🎉 Successfully promoted ${email} to admin!`);
    console.log(`   UID: ${userRecord.uid}`);
    console.log(`   The user can now access /admin in the web app`);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    if (error.code === 'auth/user-not-found') {
      console.log(`   User ${email} not found. Please ensure they have signed up first.`);
    }
  }
}

// Run the promotion
const email = process.argv[2];
if (!email) {
  console.log('Usage: node promote_admin.js <email>');
  console.log('Example: node promote_admin.js murugadossp@gmail.com');
  process.exit(1);
}

promoteUserToAdmin(email);