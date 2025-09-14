# Go2 URL Shortener - Production Runbook

## Overview

This runbook provides operational procedures for maintaining the Go2 URL Shortener in production. It covers monitoring, troubleshooting, incident response, and routine maintenance tasks.

## System Architecture

```
Internet → Load Balancer → Cloud Run (Backend) → Firestore
                      ↓
                Firebase Hosting (Frontend)
```

### Key Components
- **Frontend**: Next.js app on Firebase Hosting
- **Backend**: FastAPI on Google Cloud Run (asia-south1)
- **Database**: Firestore
- **CDN**: Cloud CDN
- **Monitoring**: Cloud Monitoring + Logging

## Monitoring and Alerting

### Key Metrics to Monitor

#### System Health
- **Service Availability**: > 99.9%
- **Response Time**: 95th percentile < 1s
- **Error Rate**: < 1%
- **Instance Count**: Monitor scaling patterns

#### Business Metrics
- **Links Created**: Track daily/hourly creation rates
- **Redirects Served**: Monitor redirect success rate
- **QR Codes Generated**: Track QR code usage
- **Safety Violations**: Monitor blocked URLs

### Monitoring Dashboards

1. **System Overview**: https://console.cloud.google.com/monitoring/dashboards
2. **Cloud Run Metrics**: https://console.cloud.google.com/run/detail/asia-south1/go2-api
3. **Firebase Console**: https://console.firebase.google.com/project/go2-url-shortener

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error Rate | > 2% | > 5% | Check logs, investigate |
| Response Time | > 1.5s | > 3s | Check performance, scale |
| Availability | < 99.5% | < 99% | Immediate investigation |
| Instance Count | > 50 | > 80 | Check for traffic spike |

## Incident Response

### Severity Levels

#### P0 - Critical (Service Down)
- **Response Time**: 15 minutes
- **Examples**: Complete service outage, data loss
- **Actions**: Immediate escalation, all hands on deck

#### P1 - High (Major Impact)
- **Response Time**: 1 hour
- **Examples**: High error rates, significant performance degradation
- **Actions**: Investigate and resolve quickly

#### P2 - Medium (Minor Impact)
- **Response Time**: 4 hours
- **Examples**: Minor performance issues, non-critical feature failures
- **Actions**: Investigate during business hours

#### P3 - Low (Minimal Impact)
- **Response Time**: 24 hours
- **Examples**: Cosmetic issues, minor bugs
- **Actions**: Schedule for next maintenance window

### Incident Response Procedures

#### 1. Initial Response (First 15 minutes)
```bash
# Check overall system status
gcloud run services describe go2-api --region asia-south1

# Check recent logs for errors
gcloud logging read 'resource.type="cloud_run_revision" severity>=ERROR' --limit 20

# Check monitoring dashboard
# Visit: https://console.cloud.google.com/monitoring

# Test basic functionality
curl -f https://go2.video/health
curl -f https://go2.tools/health
curl -f https://go2.reviews/health
```

#### 2. Diagnosis (15-30 minutes)
```bash
# Check service metrics
gcloud monitoring metrics list --filter="metric.type:run.googleapis.com"

# Check recent deployments
gcloud run revisions list --service go2-api --region asia-south1

# Check load balancer status
gcloud compute backend-services get-health go2-backend --global

# Check SSL certificate status
gcloud compute ssl-certificates describe go2-ssl-cert --global
```

#### 3. Resolution Actions

##### Service Not Responding
```bash
# Check if service is running
gcloud run services describe go2-api --region asia-south1

# Restart service (creates new revision)
gcloud run deploy go2-api --image gcr.io/go2-url-shortener/go2-api:latest --region asia-south1

# Check logs for startup issues
gcloud logging read 'resource.type="cloud_run_revision" resource.labels.service_name="go2-api"' --limit 50
```

##### High Error Rate
```bash
# Check error logs
gcloud logging read 'resource.type="cloud_run_revision" severity>=ERROR' --limit 50

# Check for specific error patterns
gcloud logging read 'resource.type="cloud_run_revision" "500"' --limit 20

# Check Firestore connectivity
gcloud logging read 'resource.type="cloud_run_revision" "firestore"' --limit 20
```

##### Performance Issues
```bash
# Check instance scaling
gcloud run services describe go2-api --region asia-south1 --format="value(spec.template.metadata.annotations)"

# Scale up if needed
gcloud run services update go2-api --min-instances 2 --max-instances 200 --region asia-south1

# Check memory/CPU usage
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"
```

##### SSL/DNS Issues
```bash
# Check SSL certificate
openssl s_client -connect go2.video:443 -servername go2.video

# Check DNS resolution
nslookup go2.video
dig go2.video

# Check load balancer
gcloud compute forwarding-rules describe go2-https-rule --global
```

## Routine Maintenance

### Daily Tasks

#### Health Checks (Automated)
```bash
#!/bin/bash
# Daily health check script

echo "=== Daily Health Check $(date) ==="

# Test all domains
for domain in go2.video go2.tools go2.reviews; do
    echo "Testing $domain..."
    if curl -f -s "https://$domain/health" > /dev/null; then
        echo "✅ $domain is healthy"
    else
        echo "❌ $domain is unhealthy"
        # Send alert
    fi
done

# Check error rates
echo "Checking error rates..."
gcloud logging read 'resource.type="cloud_run_revision" severity>=ERROR' --limit 1 --format="value(timestamp)"

# Check performance
echo "Checking performance metrics..."
# Add performance checks here

echo "=== Health Check Complete ==="
```

#### Log Review
```bash
# Check for unusual patterns
gcloud logging read 'resource.type="cloud_run_revision" severity>=WARNING' --limit 20

# Check safety violations
gcloud logging read 'resource.type="cloud_run_revision" "safety violation"' --limit 10

# Check authentication issues
gcloud logging read 'resource.type="cloud_run_revision" "authentication"' --limit 10
```

### Weekly Tasks

#### Performance Review
```bash
# Generate performance report
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision" --format="table(metric.type)"

# Check scaling patterns
gcloud run revisions list --service go2-api --region asia-south1 --limit 10

# Review cost metrics
gcloud billing budgets list
```

#### Security Review
```bash
# Check Cloud Armor logs
gcloud logging read 'resource.type="http_load_balancer" "blocked"' --limit 20

# Review access patterns
gcloud logging read 'resource.type="cloud_run_revision" "admin"' --limit 10

# Check for suspicious activity
gcloud logging read 'resource.type="cloud_run_revision" "rate limit"' --limit 10
```

### Monthly Tasks

#### Capacity Planning
```bash
# Review traffic trends
gcloud monitoring metrics list --filter="metric.type:run.googleapis.com/request_count"

# Check resource utilization
gcloud monitoring metrics list --filter="metric.type:run.googleapis.com/container/memory/utilizations"

# Plan for scaling needs
# Review and adjust min/max instances based on traffic patterns
```

#### Security Updates
```bash
# Update base Docker image
cd apps/api
# Update Dockerfile with latest Python image
docker build -t gcr.io/go2-url-shortener/go2-api:latest .
gcloud builds submit --tag gcr.io/go2-url-shortener/go2-api:latest

# Deploy updated image
gcloud run deploy go2-api --image gcr.io/go2-url-shortener/go2-api:latest --region asia-south1
```

#### Backup Verification
```bash
# Verify Firestore backups
gcloud firestore operations list

# Test backup restoration (in staging environment)
# gcloud firestore import gs://backup-bucket/backup-folder
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: "Service Unavailable" Error
**Symptoms**: Users getting 503 errors
**Diagnosis**:
```bash
gcloud run services describe go2-api --region asia-south1
gcloud logging read 'resource.type="cloud_run_revision" "503"' --limit 10
```
**Solutions**:
1. Check if service is running
2. Verify resource limits (CPU/Memory)
3. Check for cold start issues
4. Scale up instances if needed

#### Issue: High Latency
**Symptoms**: Slow response times
**Diagnosis**:
```bash
gcloud monitoring metrics list --filter="metric.type:run.googleapis.com/request_latencies"
gcloud logging read 'resource.type="cloud_run_revision" "slow"' --limit 10
```
**Solutions**:
1. Check database query performance
2. Verify CDN cache hit rates
3. Scale up CPU/Memory
4. Optimize application code

#### Issue: SSL Certificate Problems
**Symptoms**: SSL warnings or errors
**Diagnosis**:
```bash
gcloud compute ssl-certificates describe go2-ssl-cert --global
openssl s_client -connect go2.video:443 -servername go2.video
```
**Solutions**:
1. Wait for certificate provisioning (can take up to 60 minutes)
2. Verify domain ownership
3. Check DNS configuration
4. Recreate certificate if needed

#### Issue: High Error Rate
**Symptoms**: Increased 4xx/5xx errors
**Diagnosis**:
```bash
gcloud logging read 'resource.type="cloud_run_revision" severity>=ERROR' --limit 20
gcloud monitoring metrics list --filter="metric.type:run.googleapis.com/request_count"
```
**Solutions**:
1. Check application logs for specific errors
2. Verify external API connectivity (Firebase, SendGrid)
3. Check for malformed requests
4. Review recent code changes

### Emergency Procedures

#### Complete Service Outage
1. **Immediate Actions** (0-5 minutes):
   - Check Cloud Status: https://status.cloud.google.com/
   - Verify load balancer status
   - Check DNS resolution

2. **Diagnosis** (5-15 minutes):
   - Check Cloud Run service status
   - Review recent deployments
   - Check Firestore connectivity

3. **Recovery** (15-30 minutes):
   - Rollback to previous working revision if needed
   - Scale up resources if capacity issue
   - Contact Google Cloud Support if platform issue

#### Data Corruption/Loss
1. **Immediate Actions**:
   - Stop all write operations
   - Assess scope of corruption
   - Notify stakeholders

2. **Recovery**:
   - Restore from Firestore backup
   - Verify data integrity
   - Resume operations gradually

## Deployment Procedures

### Standard Deployment
```bash
# Backend deployment
cd apps/api
gcloud builds submit --tag gcr.io/go2-url-shortener/go2-api:latest
gcloud run deploy go2-api --image gcr.io/go2-url-shortener/go2-api:latest --region asia-south1

# Frontend deployment
cd apps/web
npm run build
firebase deploy --only hosting
```

### Emergency Rollback
```bash
# List recent revisions
gcloud run revisions list --service go2-api --region asia-south1

# Rollback to previous revision
gcloud run services update-traffic go2-api --to-revisions PREVIOUS_REVISION=100 --region asia-south1

# Verify rollback
curl -f https://go2.video/health
```

### Blue-Green Deployment
```bash
# Deploy to new revision without traffic
gcloud run deploy go2-api-staging --image gcr.io/go2-url-shortener/go2-api:latest --region asia-south1 --no-traffic

# Test new revision
curl -f https://go2-api-staging-xyz.a.run.app/health

# Gradually shift traffic
gcloud run services update-traffic go2-api --to-revisions go2-api-staging=10,go2-api=90 --region asia-south1

# Monitor and complete migration
gcloud run services update-traffic go2-api --to-revisions go2-api-staging=100 --region asia-south1
```

## Performance Tuning

### Optimization Checklist
- [ ] CDN cache hit rate > 80%
- [ ] Average response time < 500ms
- [ ] Cold start time < 2s
- [ ] Memory utilization < 80%
- [ ] CPU utilization < 70%

### Scaling Configuration
```bash
# Optimize for traffic patterns
gcloud run services update go2-api \
    --min-instances 1 \
    --max-instances 100 \
    --concurrency 1000 \
    --cpu 2 \
    --memory 2Gi \
    --region asia-south1
```

## Security Procedures

### Security Incident Response
1. **Identify**: Monitor for security alerts
2. **Contain**: Block malicious traffic via Cloud Armor
3. **Eradicate**: Remove threats and patch vulnerabilities
4. **Recover**: Restore normal operations
5. **Learn**: Update security measures

### Regular Security Tasks
```bash
# Review Cloud Armor logs
gcloud logging read 'resource.type="http_load_balancer" jsonPayload.enforcedSecurityPolicy.name="go2-security-policy"'

# Check for brute force attempts
gcloud logging read 'resource.type="cloud_run_revision" "rate limit exceeded"'

# Review admin access
gcloud logging read 'resource.type="cloud_run_revision" "admin access"'
```

## Contact Information

### Escalation Path
1. **On-call Engineer**: [Your contact info]
2. **Technical Lead**: [Technical lead contact]
3. **Google Cloud Support**: [Support case URL]

### External Dependencies
- **Domain Registrar**: [Contact info for DNS issues]
- **SendGrid Support**: [For email delivery issues]
- **Firebase Support**: [For hosting/database issues]

---

**Remember**: Always test procedures in staging before applying to production. Keep this runbook updated with any changes to the system architecture or procedures.