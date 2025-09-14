# Go2 URL Shortener - Production Deployment Checklist

## Pre-Deployment Checklist

### ✅ Infrastructure Setup

#### Google Cloud Project
- [ ] Create Google Cloud project: `go2-url-shortener`
- [ ] Enable billing on the project
- [ ] Set default region to `asia-south1`
- [ ] Enable required APIs:
  - [ ] Cloud Run API
  - [ ] Cloud Build API
  - [ ] Compute Engine API
  - [ ] Cloud DNS API
  - [ ] Certificate Manager API
  - [ ] Secret Manager API
  - [ ] Cloud Monitoring API
  - [ ] Cloud Logging API

#### Domain Configuration
- [ ] Verify ownership of domains:
  - [ ] go2.video
  - [ ] go2.tools
  - [ ] go2.reviews
- [ ] Configure DNS records to point to static IP
- [ ] Set up SSL certificates for all domains
- [ ] Configure www redirects

#### Firebase Setup
- [ ] Create Firebase project (link to Google Cloud project)
- [ ] Enable Firestore in native mode
- [ ] Enable Firebase Authentication
- [ ] Enable Firebase Hosting
- [ ] Configure Firebase Storage
- [ ] Set up security rules

### ✅ Environment Configuration

#### Secret Management
- [ ] Create Firebase service account key
- [ ] Store service account in Secret Manager: `firebase-service-account`
- [ ] Obtain Google Safe Browsing API key
- [ ] Store Safe Browsing key in Secret Manager: `safe-browsing-api-key`
- [ ] Obtain SendGrid API key (optional)
- [ ] Store SendGrid key in Secret Manager: `sendgrid-api-key`

#### Service Account Setup
- [ ] Create Cloud Run service account: `go2-api-sa`
- [ ] Grant necessary permissions:
  - [ ] `roles/secretmanager.secretAccessor`
  - [ ] `roles/datastore.user`
  - [ ] `roles/storage.objectViewer`
  - [ ] `roles/monitoring.metricWriter`
  - [ ] `roles/logging.logWriter`

#### Environment Files
- [ ] Configure `apps/api/.env.production`
- [ ] Configure `apps/web/.env.production`
- [ ] Verify all required environment variables are set

### ✅ Code Preparation

#### Backend Preparation
- [ ] Update `apps/api/src/main.py` for production
- [ ] Verify Dockerfile is optimized
- [ ] Check requirements.txt includes all dependencies
- [ ] Ensure composite document ID system is implemented
- [ ] Verify domain utilities are properly integrated

#### Frontend Preparation
- [ ] Update `apps/web/next.config.ts` for production
- [ ] Configure static export settings
- [ ] Verify environment variables are properly used
- [ ] Check Firebase configuration

#### Configuration Files
- [ ] Update `firebase.json` with correct rewrites
- [ ] Verify Firestore security rules
- [ ] Check storage rules
- [ ] Validate deployment configurations

## Deployment Steps

### 1. Infrastructure Deployment

#### Run Infrastructure Setup
```bash
# Make script executable
chmod +x deployment/setup-infrastructure.sh

# Run infrastructure setup
./deployment/setup-infrastructure.sh
```

**Verify:**
- [ ] Static IP reserved: `go2-ip`
- [ ] SSL certificate created: `go2-ssl-cert`
- [ ] Load balancer configured
- [ ] Security policy applied
- [ ] Monitoring metrics created

#### DNS Configuration
```bash
# Get static IP
STATIC_IP=$(gcloud compute addresses describe go2-ip --global --format="value(address)")
echo "Configure DNS records to point to: $STATIC_IP"
```

**Configure at domain registrar:**
- [ ] `go2.video A $STATIC_IP`
- [ ] `www.go2.video A $STATIC_IP`
- [ ] `go2.tools A $STATIC_IP`
- [ ] `www.go2.tools A $STATIC_IP`
- [ ] `go2.reviews A $STATIC_IP`
- [ ] `www.go2.reviews A $STATIC_IP`

### 2. Backend Deployment

#### Deploy to Cloud Run
```bash
# Run deployment script
chmod +x deployment/deploy.sh
./deployment/deploy.sh backend
```

**Verify:**
- [ ] Docker image built successfully
- [ ] Cloud Run service deployed
- [ ] Service account configured
- [ ] Environment variables set
- [ ] Secrets mounted correctly

#### Test Backend
```bash
# Get Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe go2-api --region asia-south1 --format 'value(status.url)')

# Test health endpoint
curl -f "$CLOUD_RUN_URL/health"

# Test API endpoint
curl -f "$CLOUD_RUN_URL/api/config/base-domains"
```

**Expected responses:**
- [ ] Health check returns `{"status": "healthy"}`
- [ ] Config endpoint returns domain list
- [ ] No error logs in Cloud Run

### 3. Frontend Deployment

#### Deploy to Firebase Hosting
```bash
# Run frontend deployment
./deployment/deploy.sh frontend
```

**Verify:**
- [ ] Next.js build completed successfully
- [ ] Static files uploaded to Firebase Hosting
- [ ] Rewrites configured correctly
- [ ] Security headers applied

#### Test Frontend
```bash
# Test each domain
for domain in go2.video go2.tools go2.reviews; do
  echo "Testing https://$domain..."
  curl -I "https://$domain"
done
```

**Expected responses:**
- [ ] All domains return 200 OK
- [ ] Security headers present
- [ ] Redirects work correctly

### 4. End-to-End Testing

#### Functional Testing
```bash
# Create test link
RESPONSE=$(curl -s -X POST "https://go2.video/api/links/shorten" \
  -H "Content-Type: application/json" \
  -d '{
    "long_url": "https://example.com",
    "base_domain": "go2.video",
    "custom_code": "deployment-test"
  }')

echo "Link creation response: $RESPONSE"

# Test redirect
curl -I "https://go2.video/deployment-test"
```

**Verify:**
- [ ] Link creation succeeds
- [ ] Short URL is correct format
- [ ] QR URL is generated
- [ ] Redirect works (302 to example.com)
- [ ] Analytics are logged

#### Multi-Domain Testing
```bash
# Test same code on different domains
curl -X POST "https://go2.tools/api/links/shorten" \
  -H "Content-Type: application/json" \
  -d '{
    "long_url": "https://github.com/test",
    "base_domain": "go2.tools",
    "custom_code": "deployment-test"
  }'

# Should succeed (no collision)
curl -I "https://go2.tools/deployment-test"
```

**Verify:**
- [ ] Same code works on different domains
- [ ] Each redirects to correct destination
- [ ] No collision errors

#### QR Code Testing
```bash
# Test QR code generation
curl -I "https://go2.video/api/qr/go2.video_deployment-test"
```

**Verify:**
- [ ] QR code returns PNG image
- [ ] Correct caching headers
- [ ] Image displays properly

### 5. SSL Certificate Verification

#### Check Certificate Status
```bash
# Check certificate provisioning
gcloud compute ssl-certificates describe go2-ssl-cert --global

# Test SSL on each domain
for domain in go2.video go2.tools go2.reviews; do
  echo "Testing SSL for $domain..."
  openssl s_client -connect "$domain:443" -servername "$domain" < /dev/null
done
```

**Verify:**
- [ ] Certificate status is `ACTIVE`
- [ ] All domains have valid certificates
- [ ] No SSL warnings in browser
- [ ] HTTPS redirect works

### 6. Performance Testing

#### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test redirect performance
ab -n 1000 -c 10 https://go2.video/deployment-test

# Test API performance
ab -n 100 -c 5 https://go2.video/api/config/base-domains
```

**Performance Targets:**
- [ ] Redirect response time < 500ms
- [ ] API response time < 1s
- [ ] 99% success rate under load
- [ ] No memory leaks or errors

#### CDN Testing
```bash
# Test CDN cache headers
curl -I "https://go2.video/static/some-asset.js"
```

**Verify:**
- [ ] Cache-Control headers present
- [ ] X-Cache headers indicate CDN hit
- [ ] Static assets load quickly

## Post-Deployment Verification

### ✅ Monitoring Setup

#### Check Dashboards
- [ ] Cloud Run metrics dashboard
- [ ] Firebase Hosting metrics
- [ ] Custom business metrics
- [ ] Error rate monitoring

#### Verify Alerting
- [ ] High error rate alerts configured
- [ ] High latency alerts configured
- [ ] Low availability alerts configured
- [ ] Custom metric alerts working

#### Test Notifications
```bash
# Trigger test alert (if possible)
# Verify notification channels work
```

### ✅ Security Verification

#### Security Headers
```bash
# Check security headers
curl -I "https://go2.video" | grep -E "(X-|Content-Security|Strict-Transport)"
```

**Required headers:**
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-Frame-Options: DENY`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] `Content-Security-Policy` configured

#### Access Control
- [ ] Anonymous link creation works
- [ ] Authenticated features require login
- [ ] Admin features require admin role
- [ ] Rate limiting is active

#### Data Protection
- [ ] IP addresses are hashed
- [ ] Passwords are hashed
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced everywhere

### ✅ Backup and Recovery

#### Verify Backups
- [ ] Firestore automatic backups enabled
- [ ] Manual backup/export tested
- [ ] Recovery procedures documented
- [ ] Backup retention configured

#### Test Recovery
```bash
# Test Firestore export (in staging)
gcloud firestore export gs://test-backup-bucket/test-export
```

### ✅ Documentation Updates

#### Update Documentation
- [ ] API endpoints documented
- [ ] Deployment procedures updated
- [ ] Troubleshooting guide current
- [ ] Monitoring runbook complete

#### Team Communication
- [ ] Deployment announcement sent
- [ ] Access credentials shared securely
- [ ] Support procedures communicated
- [ ] Escalation contacts updated

## Go-Live Checklist

### Final Pre-Launch Checks
- [ ] All tests passing
- [ ] Performance meets requirements
- [ ] Security scan completed
- [ ] Monitoring active
- [ ] Backup verified
- [ ] Team notified

### Launch Activities
- [ ] DNS propagation verified (24-48 hours)
- [ ] SSL certificates active
- [ ] All domains accessible
- [ ] Redirects working correctly
- [ ] Analytics tracking properly

### Post-Launch Monitoring (First 24 Hours)
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify user feedback
- [ ] Watch for any issues
- [ ] Document any problems

## Rollback Procedures

### Emergency Rollback
If critical issues are discovered:

```bash
# Rollback Cloud Run deployment
gcloud run revisions list --service go2-api --region asia-south1
gcloud run services update-traffic go2-api \
  --to-revisions PREVIOUS_REVISION=100 \
  --region asia-south1

# Rollback Firebase Hosting (if needed)
firebase hosting:clone SOURCE_SITE_ID:SOURCE_CHANNEL_ID TARGET_SITE_ID:live
```

### Rollback Checklist
- [ ] Identify rollback trigger
- [ ] Execute rollback procedure
- [ ] Verify rollback successful
- [ ] Communicate status to team
- [ ] Document incident
- [ ] Plan fix for next deployment

## Success Criteria

### Technical Success
- [ ] All domains accessible via HTTPS
- [ ] Link creation and redirect working
- [ ] Multi-domain support functional
- [ ] Analytics tracking properly
- [ ] QR codes generating correctly
- [ ] Admin functions operational

### Performance Success
- [ ] Redirect latency < 500ms
- [ ] API response time < 1s
- [ ] 99.9% uptime achieved
- [ ] CDN cache hit rate > 80%
- [ ] No memory leaks or errors

### Security Success
- [ ] All security headers present
- [ ] HTTPS enforced everywhere
- [ ] Authentication working
- [ ] Rate limiting active
- [ ] Data properly encrypted

### Business Success
- [ ] All three domains operational
- [ ] Contextual suggestions working
- [ ] User experience smooth
- [ ] Analytics providing insights
- [ ] Support procedures ready

---

## Deployment Sign-off

### Technical Lead Approval
- [ ] Code review completed
- [ ] Architecture approved
- [ ] Security review passed
- [ ] Performance testing completed

**Signed:** _________________ **Date:** _________

### Operations Approval
- [ ] Infrastructure ready
- [ ] Monitoring configured
- [ ] Backup procedures tested
- [ ] Support documentation complete

**Signed:** _________________ **Date:** _________

### Business Approval
- [ ] User acceptance testing passed
- [ ] Business requirements met
- [ ] Go-live plan approved
- [ ] Support team trained

**Signed:** _________________ **Date:** _________

---

**Deployment Status:** ⏳ **READY FOR PRODUCTION**

**Next Steps:** Execute deployment plan and monitor for 24-48 hours post-launch.