# Go2 URL Shortener - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Go2 URL Shortener to production using Firebase Hosting (frontend) and Google Cloud Run (backend) in the asia-south1 region.

## Prerequisites

### Required Tools
```bash
# Install Google Cloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Install Firebase CLI
npm install -g firebase-tools

# Install Docker
# Follow instructions at https://docs.docker.com/get-docker/

# Verify installations
gcloud --version
firebase --version
docker --version
```

### Required Accounts & Permissions
- Google Cloud Platform account with billing enabled
- Firebase project owner permissions
- Domain registrar access for go2.video, go2.tools, go2.reviews
- SendGrid account (optional, for email reports)
- Google Safe Browsing API key (optional, for URL safety)

## Step 1: Google Cloud Project Setup

```bash
# Set project ID
export PROJECT_ID="go2-url-shortener"
export REGION="asia-south1"

# Create project (if not exists)
gcloud projects create $PROJECT_ID --name="Go2 URL Shortener"

# Set current project
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
gcloud config set compute/region $REGION

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable dns.googleapis.com
gcloud services enable certificatemanager.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

## Step 2: Secret Management Setup

```bash
# Create secrets for sensitive data
gcloud secrets create firebase-service-account \
    --data-file=apps/api/go2-url-shortner-firebase-adminsdk-fbsvc-5e27a7f632.json

# Create other secrets (replace with actual values)
echo "your-safe-browsing-api-key" | gcloud secrets create safe-browsing-api-key --data-file=-
echo "your-sendgrid-api-key" | gcloud secrets create sendgrid-api-key --data-file=-

# Create service account for Cloud Run
gcloud iam service-accounts create go2-api-sa \
    --display-name "Go2 API Service Account"

# Grant secret access permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:go2-api-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role "roles/secretmanager.secretAccessor"

# Grant Firestore access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member "serviceAccount:go2-api-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role "roles/datastore.user"
```

## Step 3: Build and Deploy Backend to Cloud Run

```bash
# Navigate to API directory
cd apps/api

# Build Docker image
gcloud builds submit --tag gcr.io/$PROJECT_ID/go2-api:latest

# Deploy to Cloud Run
gcloud run deploy go2-api \
    --image gcr.io/$PROJECT_ID/go2-api:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account go2-api-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 100 \
    --concurrency 1000 \
    --timeout 300 \
    --set-env-vars ENVIRONMENT=production,FIREBASE_PROJECT_ID=$PROJECT_ID \
    --set-secrets FIREBASE_SERVICE_ACCOUNT_JSON=firebase-service-account:latest \
    --set-secrets GOOGLE_SAFE_BROWSING_API_KEY=safe-browsing-api-key:latest \
    --set-secrets SENDGRID_API_KEY=sendgrid-api-key:latest

# Get the service URL
export CLOUD_RUN_URL=$(gcloud run services describe go2-api --region $REGION --format 'value(status.url)')
echo "Cloud Run URL: $CLOUD_RUN_URL"
```

## Step 4: Set Up Load Balancer and SSL

```bash
# Reserve static IP
gcloud compute addresses create go2-ip --global

# Get the IP address
export STATIC_IP=$(gcloud compute addresses describe go2-ip --global --format="value(address)")
echo "Static IP: $STATIC_IP"

# Create Network Endpoint Group for Cloud Run
gcloud compute network-endpoint-groups create go2-neg \
    --region=$REGION \
    --network-endpoint-type=serverless \
    --cloud-run-service=go2-api

# Create backend service
gcloud compute backend-services create go2-backend \
    --global \
    --load-balancing-scheme=EXTERNAL_MANAGED

# Add Cloud Run NEG to backend service
gcloud compute backend-services add-backend go2-backend \
    --global \
    --network-endpoint-group=go2-neg \
    --network-endpoint-group-region=$REGION

# Enable Cloud CDN
gcloud compute backend-services update go2-backend \
    --enable-cdn \
    --cache-mode CACHE_ALL_STATIC \
    --default-ttl 3600 \
    --max-ttl 86400 \
    --global

# Create managed SSL certificate
gcloud compute ssl-certificates create go2-ssl-cert \
    --domains=go2.video,go2.tools,go2.reviews,www.go2.video,www.go2.tools,www.go2.reviews \
    --global

# Create URL map
gcloud compute url-maps create go2-url-map \
    --default-service go2-backend

# Create HTTPS proxy
gcloud compute target-https-proxies create go2-https-proxy \
    --ssl-certificates go2-ssl-cert \
    --url-map go2-url-map

# Create HTTPS forwarding rule
gcloud compute forwarding-rules create go2-https-rule \
    --global \
    --target-https-proxy go2-https-proxy \
    --address go2-ip \
    --ports 443

# Create HTTP to HTTPS redirect
gcloud compute url-maps create go2-http-redirect \
    --default-url-redirect-response-code=301 \
    --default-url-redirect-https-redirect

gcloud compute target-http-proxies create go2-http-proxy \
    --url-map go2-http-redirect

gcloud compute forwarding-rules create go2-http-rule \
    --global \
    --target-http-proxy go2-http-proxy \
    --address go2-ip \
    --ports 80
```

## Step 5: Configure DNS

Update your DNS records at your domain registrar:

```
Domain: go2.video
Type: A
Name: @
Value: [STATIC_IP from above]
TTL: 300

Domain: go2.video
Type: A
Name: www
Value: [STATIC_IP from above]
TTL: 300

# Repeat for go2.tools and go2.reviews
```

## Step 6: Build and Deploy Frontend to Firebase Hosting

```bash
# Navigate to web directory
cd ../../apps/web

# Update environment variables
cp .env.production .env.local

# Update the API URL in .env.local
echo "NEXT_PUBLIC_API_URL=$CLOUD_RUN_URL" >> .env.local

# Install dependencies and build
npm ci
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting

# Update firebase.json to point to your Cloud Run service
# (This was already done in the firebase.json update above)
```

## Step 7: Set Up Monitoring and Alerting

```bash
# Create log-based metrics
gcloud logging metrics create link_created \
    --description="Count of links created" \
    --log-filter='resource.type="cloud_run_revision" "link created successfully"'

gcloud logging metrics create redirect_served \
    --description="Count of redirects served" \
    --log-filter='resource.type="cloud_run_revision" "redirect successful"'

gcloud logging metrics create safety_violations \
    --description="Count of safety violations" \
    --log-filter='resource.type="cloud_run_revision" "safety violation"'

# Create alerting policies (example for high error rate)
gcloud alpha monitoring policies create --policy-from-file=deployment/monitoring-setup.yaml
```

## Step 8: Security Configuration

```bash
# Create Cloud Armor security policy
gcloud compute security-policies create go2-security-policy \
    --description "Security policy for Go2 API"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
    --security-policy go2-security-policy \
    --expression "true" \
    --action "rate-based-ban" \
    --rate-limit-threshold-count 100 \
    --rate-limit-threshold-interval-sec 60 \
    --ban-duration-sec 600

# Apply to backend service
gcloud compute backend-services update go2-backend \
    --security-policy go2-security-policy \
    --global
```

## Step 9: Verification and Testing

```bash
# Test health endpoints
curl -f https://go2.video/health
curl -f https://go2.tools/health
curl -f https://go2.reviews/health

# Test SSL certificates
openssl s_client -connect go2.video:443 -servername go2.video < /dev/null

# Create a test link
curl -X POST https://go2.video/api/links/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "long_url": "https://example.com",
    "base_domain": "go2.video"
  }'

# Test redirect (replace SHORT_CODE with actual code from above)
curl -I https://go2.video/SHORT_CODE
```

## Step 10: Performance Optimization

```bash
# Update Cloud Run service with optimized settings
gcloud run services update go2-api \
    --cpu 2 \
    --memory 2Gi \
    --concurrency 1000 \
    --min-instances 1 \
    --max-instances 100 \
    --execution-environment gen2 \
    --region $REGION

# Verify CDN is working
curl -I https://go2.video/static/some-asset.js
# Look for "cache-control" and "x-cache" headers
```

## Maintenance and Updates

### Deploying Updates

```bash
# Backend updates
cd apps/api
gcloud builds submit --tag gcr.io/$PROJECT_ID/go2-api:latest
gcloud run deploy go2-api \
    --image gcr.io/$PROJECT_ID/go2-api:latest \
    --region $REGION

# Frontend updates
cd apps/web
npm run build
firebase deploy --only hosting
```

### Monitoring

- **Cloud Console**: https://console.cloud.google.com/run/detail/asia-south1/go2-api
- **Firebase Console**: https://console.firebase.google.com/project/go2-url-shortener
- **Monitoring Dashboard**: https://console.cloud.google.com/monitoring

### Backup Strategy

```bash
# Firestore is automatically backed up
# For additional backups, export data:
gcloud firestore export gs://your-backup-bucket/$(date +%Y%m%d)
```

### Rollback Procedure

```bash
# List revisions
gcloud run revisions list --service go2-api --region $REGION

# Rollback to previous revision
gcloud run services update-traffic go2-api \
    --to-revisions PREVIOUS_REVISION=100 \
    --region $REGION
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Not Ready**
   ```bash
   # Check certificate status (may take 10-60 minutes)
   gcloud compute ssl-certificates describe go2-ssl-cert --global
   ```

2. **DNS Not Resolving**
   ```bash
   # Check DNS propagation
   nslookup go2.video
   dig go2.video
   ```

3. **Cloud Run Service Errors**
   ```bash
   # Check logs
   gcloud logging read 'resource.type="cloud_run_revision" resource.labels.service_name="go2-api"' --limit 50
   ```

4. **Load Balancer Issues**
   ```bash
   # Check backend health
   gcloud compute backend-services get-health go2-backend --global
   ```

### Support Contacts

- **Technical Issues**: Check Cloud Run logs and monitoring dashboard
- **DNS Issues**: Contact your domain registrar
- **Firebase Issues**: Check Firebase console and documentation

## Cost Optimization

### Current Setup Costs (Estimated)

- **Cloud Run**: ~$20-50/month (depending on traffic)
- **Load Balancer**: ~$18/month
- **Cloud CDN**: ~$0.08/GB
- **SSL Certificates**: Free (Google-managed)
- **Firebase Hosting**: Free tier (up to 10GB)

### Optimization Tips

1. **Use minimum instances**: Set min-instances to 0 for cost savings
2. **Enable CPU throttling**: Reduces costs during idle periods
3. **Optimize images**: Use multi-stage Docker builds
4. **Monitor usage**: Set up billing alerts

## Security Checklist

- ✅ HTTPS enforced on all domains
- ✅ Security headers configured
- ✅ Rate limiting enabled
- ✅ Secrets stored in Secret Manager
- ✅ Non-root user in Docker container
- ✅ Firestore security rules configured
- ✅ Cloud Armor protection enabled
- ✅ Regular security updates scheduled

## Compliance and Governance

- **Data Retention**: Configure Firestore TTL for expired links
- **Audit Logging**: Enable Cloud Audit Logs
- **Access Control**: Use IAM roles and service accounts
- **Monitoring**: Set up alerting for security events

---

**Deployment Complete!** Your Go2 URL Shortener is now running in production across all three domains with proper monitoring, security, and performance optimizations.