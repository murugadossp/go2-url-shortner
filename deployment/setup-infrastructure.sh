#!/bin/bash

# Go2 URL Shortener - Infrastructure Setup Script
# This script sets up the initial infrastructure for the Go2 URL Shortener

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

# Check if user is authenticated
check_auth() {
    log_info "Checking authentication..."
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    log_success "Authentication check passed"
}

# Create or select project
setup_project() {
    log_info "Setting up Google Cloud project..."
    
    # Check if project exists
    if gcloud projects describe $PROJECT_ID &>/dev/null; then
        log_info "Project $PROJECT_ID already exists"
    else
        log_info "Creating project $PROJECT_ID..."
        gcloud projects create $PROJECT_ID --name="Go2 URL Shortener"
    fi
    
    # Set current project
    gcloud config set project $PROJECT_ID
    gcloud config set run/region $REGION
    gcloud config set compute/region $REGION
    
    log_success "Project setup completed"
}

# Enable required APIs
enable_apis() {
    log_info "Enabling required Google Cloud APIs..."
    
    APIS=(
        "run.googleapis.com"
        "cloudbuild.googleapis.com"
        "compute.googleapis.com"
        "dns.googleapis.com"
        "certificatemanager.googleapis.com"
        "secretmanager.googleapis.com"
        "monitoring.googleapis.com"
        "logging.googleapis.com"
        "firebase.googleapis.com"
        "firestore.googleapis.com"
        "storage.googleapis.com"
    )
    
    for api in "${APIS[@]}"; do
        log_info "Enabling $api..."
        gcloud services enable $api
    done
    
    log_success "All APIs enabled"
}

# Create service account
create_service_account() {
    log_info "Creating service account..."
    
    # Create service account
    if gcloud iam service-accounts describe go2-api-sa@$PROJECT_ID.iam.gserviceaccount.com &>/dev/null; then
        log_info "Service account already exists"
    else
        gcloud iam service-accounts create go2-api-sa \
            --display-name "Go2 API Service Account" \
            --description "Service account for Go2 URL Shortener API"
    fi
    
    # Grant necessary permissions
    log_info "Granting permissions to service account..."
    
    ROLES=(
        "roles/secretmanager.secretAccessor"
        "roles/datastore.user"
        "roles/storage.objectViewer"
        "roles/monitoring.metricWriter"
        "roles/logging.logWriter"
    )
    
    for role in "${ROLES[@]}"; do
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member "serviceAccount:go2-api-sa@$PROJECT_ID.iam.gserviceaccount.com" \
            --role "$role"
    done
    
    log_success "Service account created and configured"
}

# Setup secrets
setup_secrets() {
    log_info "Setting up Secret Manager..."
    
    # Check if Firebase service account key exists
    if [ -f "apps/api/go2-url-shortner-firebase-adminsdk-fbsvc-5e27a7f632.json" ]; then
        log_info "Creating Firebase service account secret..."
        gcloud secrets create firebase-service-account \
            --data-file=apps/api/go2-url-shortner-firebase-adminsdk-fbsvc-5e27a7f632.json \
            --replication-policy="automatic" || log_warning "Firebase secret may already exist"
    else
        log_warning "Firebase service account key not found. Please add it manually later."
    fi
    
    # Create placeholder secrets for API keys
    log_info "Creating placeholder secrets for API keys..."
    
    echo "placeholder-key" | gcloud secrets create safe-browsing-api-key \
        --data-file=- \
        --replication-policy="automatic" || log_warning "Safe browsing secret may already exist"
    
    echo "placeholder-key" | gcloud secrets create sendgrid-api-key \
        --data-file=- \
        --replication-policy="automatic" || log_warning "SendGrid secret may already exist"
    
    log_success "Secrets setup completed"
    log_warning "Remember to update the placeholder API keys with real values!"
}

# Reserve static IP
reserve_static_ip() {
    log_info "Reserving static IP address..."
    
    if gcloud compute addresses describe go2-ip --global &>/dev/null; then
        log_info "Static IP already exists"
    else
        gcloud compute addresses create go2-ip --global
    fi
    
    STATIC_IP=$(gcloud compute addresses describe go2-ip --global --format="value(address)")
    log_success "Static IP reserved: $STATIC_IP"
    
    log_info "Please update your DNS records to point to: $STATIC_IP"
    log_info "DNS Records needed:"
    for domain in go2.video go2.tools go2.reviews; do
        echo "  $domain A $STATIC_IP"
        echo "  www.$domain A $STATIC_IP"
    done
}

# Create SSL certificate
create_ssl_certificate() {
    log_info "Creating managed SSL certificate..."
    
    if gcloud compute ssl-certificates describe go2-ssl-cert --global &>/dev/null; then
        log_info "SSL certificate already exists"
    else
        gcloud compute ssl-certificates create go2-ssl-cert \
            --domains=go2.video,go2.tools,go2.reviews,www.go2.video,www.go2.tools,www.go2.reviews \
            --global
    fi
    
    log_success "SSL certificate created"
    log_warning "SSL certificate provisioning can take up to 60 minutes"
}

# Setup load balancer
setup_load_balancer() {
    log_info "Setting up load balancer..."
    
    # Create Network Endpoint Group (will be updated after first deployment)
    if gcloud compute network-endpoint-groups describe go2-neg --region=$REGION &>/dev/null; then
        log_info "Network Endpoint Group already exists"
    else
        log_info "NEG will be created during first deployment"
    fi
    
    # Create backend service
    if gcloud compute backend-services describe go2-backend --global &>/dev/null; then
        log_info "Backend service already exists"
    else
        gcloud compute backend-services create go2-backend \
            --global \
            --load-balancing-scheme=EXTERNAL_MANAGED
        
        # Enable Cloud CDN
        gcloud compute backend-services update go2-backend \
            --enable-cdn \
            --cache-mode CACHE_ALL_STATIC \
            --default-ttl 3600 \
            --max-ttl 86400 \
            --global
    fi
    
    # Create URL map
    if gcloud compute url-maps describe go2-url-map --global &>/dev/null; then
        log_info "URL map already exists"
    else
        gcloud compute url-maps create go2-url-map \
            --default-service go2-backend
    fi
    
    # Create HTTPS proxy
    if gcloud compute target-https-proxies describe go2-https-proxy --global &>/dev/null; then
        log_info "HTTPS proxy already exists"
    else
        gcloud compute target-https-proxies create go2-https-proxy \
            --ssl-certificates go2-ssl-cert \
            --url-map go2-url-map
    fi
    
    # Create HTTPS forwarding rule
    if gcloud compute forwarding-rules describe go2-https-rule --global &>/dev/null; then
        log_info "HTTPS forwarding rule already exists"
    else
        gcloud compute forwarding-rules create go2-https-rule \
            --global \
            --target-https-proxy go2-https-proxy \
            --address go2-ip \
            --ports 443
    fi
    
    # Create HTTP to HTTPS redirect
    if gcloud compute url-maps describe go2-http-redirect --global &>/dev/null; then
        log_info "HTTP redirect already exists"
    else
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
    fi
    
    log_success "Load balancer setup completed"
}

# Setup Cloud Armor security policy
setup_security_policy() {
    log_info "Setting up Cloud Armor security policy..."
    
    if gcloud compute security-policies describe go2-security-policy --global &>/dev/null; then
        log_info "Security policy already exists"
    else
        # Create security policy
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
    fi
    
    log_success "Security policy setup completed"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Create log-based metrics
    METRICS=(
        "link_created:Count of links created:resource.type=\"cloud_run_revision\" \"link created successfully\""
        "redirect_served:Count of redirects served:resource.type=\"cloud_run_revision\" \"redirect successful\""
        "safety_violations:Count of safety violations:resource.type=\"cloud_run_revision\" \"safety violation\""
        "qr_generated:Count of QR codes generated:resource.type=\"cloud_run_revision\" \"QR code generated\""
    )
    
    for metric in "${METRICS[@]}"; do
        IFS=':' read -r name description filter <<< "$metric"
        
        if gcloud logging metrics describe "$name" &>/dev/null; then
            log_info "Metric $name already exists"
        else
            gcloud logging metrics create "$name" \
                --description="$description" \
                --log-filter="$filter"
        fi
    done
    
    log_success "Monitoring setup completed"
}

# Initialize Firebase project
setup_firebase() {
    log_info "Setting up Firebase project..."
    
    # Check if Firebase project exists
    if firebase projects:list | grep -q "$PROJECT_ID"; then
        log_info "Firebase project already configured"
    else
        log_info "Please run 'firebase init' to configure Firebase for this project"
        log_info "Select Hosting and Firestore when prompted"
    fi
    
    log_success "Firebase setup completed"
}

# Main setup function
main() {
    log_info "Starting Go2 URL Shortener infrastructure setup..."
    log_info "Project: $PROJECT_ID"
    log_info "Region: $REGION"
    log_info "Domains: $DOMAINS"
    
    # Check authentication
    check_auth
    
    # Setup project
    setup_project
    
    # Enable APIs
    enable_apis
    
    # Create service account
    create_service_account
    
    # Setup secrets
    setup_secrets
    
    # Reserve static IP
    reserve_static_ip
    
    # Create SSL certificate
    create_ssl_certificate
    
    # Setup load balancer
    setup_load_balancer
    
    # Setup security policy
    setup_security_policy
    
    # Setup monitoring
    setup_monitoring
    
    # Setup Firebase
    setup_firebase
    
    log_success "Infrastructure setup completed!"
    
    log_info "Next steps:"
    log_info "1. Update DNS records to point to the static IP"
    log_info "2. Update API keys in Secret Manager"
    log_info "3. Run './deployment/deploy.sh' to deploy the application"
    log_info "4. Wait for SSL certificate provisioning (up to 60 minutes)"
    
    log_info "Important URLs:"
    log_info "  - Cloud Console: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
    log_info "  - Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
    log_info "  - Load Balancer: https://console.cloud.google.com/net-services/loadbalancing/list/loadBalancers?project=$PROJECT_ID"
    log_info "  - Monitoring: https://console.cloud.google.com/monitoring?project=$PROJECT_ID"
}

# Run main function
main