#!/bin/bash

# Go2 URL Shortener - Production Deployment Script
# This script automates the deployment of both frontend and backend to production

set -e  # Exit on any error

# Configuration
PROJECT_ID="go2-url-shortener"
REGION="asia-south1"
SERVICE_NAME="go2-api"
DOMAINS="go2.video,go2.tools,go2.reviews"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed and authenticated
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if firebase CLI is installed
    if ! command -v firebase &> /dev/null; then
        log_error "Firebase CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    # Set project
    gcloud config set project $PROJECT_ID
    gcloud config set run/region $REGION
    
    log_success "Prerequisites check passed"
}

# Deploy backend to Cloud Run
deploy_backend() {
    log_info "Deploying backend to Cloud Run..."
    
    cd apps/api
    
    # Build and submit to Cloud Build
    log_info "Building Docker image..."
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:latest
    
    # Deploy to Cloud Run
    log_info "Deploying to Cloud Run..."
    gcloud run deploy $SERVICE_NAME \
        --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
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
        --set-env-vars ENVIRONMENT=production,FIREBASE_PROJECT_ID=$PROJECT_ID,CORS_ORIGINS=https://$DOMAINS \
        --set-secrets FIREBASE_SERVICE_ACCOUNT_JSON=firebase-service-account:latest \
        --set-secrets GOOGLE_SAFE_BROWSING_API_KEY=safe-browsing-api-key:latest \
        --set-secrets SENDGRID_API_KEY=sendgrid-api-key:latest \
        --quiet
    
    # Get service URL
    CLOUD_RUN_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    log_success "Backend deployed successfully to: $CLOUD_RUN_URL"
    
    cd ../..
}

# Test backend deployment
test_backend() {
    log_info "Testing backend deployment..."
    
    # Get Cloud Run URL
    CLOUD_RUN_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    
    # Test health endpoint
    if curl -f -s "$CLOUD_RUN_URL/health" > /dev/null; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        exit 1
    fi
    
    # Test API endpoint
    if curl -f -s "$CLOUD_RUN_URL/api/config/base-domains" > /dev/null; then
        log_success "Backend API test passed"
    else
        log_error "Backend API test failed"
        exit 1
    fi
}

# Deploy frontend to Firebase Hosting
deploy_frontend() {
    log_info "Deploying frontend to Firebase Hosting..."
    
    cd apps/web
    
    # Install dependencies
    log_info "Installing dependencies..."
    npm ci
    
    # Build the application
    log_info "Building Next.js application..."
    npm run build
    
    # Deploy to Firebase Hosting
    log_info "Deploying to Firebase Hosting..."
    firebase deploy --only hosting --non-interactive
    
    log_success "Frontend deployed successfully"
    
    cd ../..
}

# Test frontend deployment
test_frontend() {
    log_info "Testing frontend deployment..."
    
    # Test each domain
    for domain in go2.video go2.tools go2.reviews; do
        log_info "Testing https://$domain..."
        
        # Test with timeout
        if timeout 10 curl -f -s "https://$domain" > /dev/null; then
            log_success "$domain is accessible"
        else
            log_warning "$domain may not be ready yet (DNS propagation can take time)"
        fi
    done
}

# Update load balancer configuration
update_load_balancer() {
    log_info "Updating load balancer configuration..."
    
    # Get Cloud Run URL
    CLOUD_RUN_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    
    # Update backend service if needed
    # This is typically done once during initial setup
    log_info "Load balancer configuration is managed separately"
    log_info "Cloud Run URL: $CLOUD_RUN_URL"
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Test link creation
    log_info "Testing link creation..."
    RESPONSE=$(curl -s -X POST "https://go2.video/api/links/shorten" \
        -H "Content-Type: application/json" \
        -d '{
            "long_url": "https://example.com",
            "base_domain": "go2.video"
        }')
    
    if echo "$RESPONSE" | grep -q "short_url"; then
        log_success "Link creation test passed"
        
        # Extract short code and test redirect
        SHORT_CODE=$(echo "$RESPONSE" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
        if [ -n "$SHORT_CODE" ]; then
            log_info "Testing redirect for code: $SHORT_CODE"
            if curl -I -s "https://go2.video/$SHORT_CODE" | grep -q "302"; then
                log_success "Redirect test passed"
            else
                log_warning "Redirect test failed"
            fi
        fi
    else
        log_warning "Link creation test failed"
    fi
}

# Main deployment function
main() {
    log_info "Starting Go2 URL Shortener deployment..."
    log_info "Project: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "Domains: $DOMAINS"
    
    # Check prerequisites
    check_prerequisites
    
    # Deploy backend
    deploy_backend
    
    # Test backend
    test_backend
    
    # Deploy frontend
    deploy_frontend
    
    # Test frontend
    test_frontend
    
    # Update load balancer (informational)
    update_load_balancer
    
    # Run smoke tests
    run_smoke_tests
    
    log_success "Deployment completed successfully!"
    log_info "Your Go2 URL Shortener is now live at:"
    log_info "  - https://go2.video"
    log_info "  - https://go2.tools"
    log_info "  - https://go2.reviews"
    
    log_info "Monitor your deployment at:"
    log_info "  - Cloud Run: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME"
    log_info "  - Firebase: https://console.firebase.google.com/project/$PROJECT_ID"
    log_info "  - Monitoring: https://console.cloud.google.com/monitoring"
}

# Handle script arguments
case "${1:-}" in
    "backend")
        check_prerequisites
        deploy_backend
        test_backend
        ;;
    "frontend")
        check_prerequisites
        deploy_frontend
        test_frontend
        ;;
    "test")
        run_smoke_tests
        ;;
    *)
        main
        ;;
esac