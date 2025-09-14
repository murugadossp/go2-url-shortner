# Go2 URL Shortener - API Reference

## Overview

The Go2 URL Shortener API provides comprehensive URL shortening functionality with multi-domain support, analytics, QR code generation, and administrative features.

**Base URL**: `https://go2-api-asia-south1-run.app`

**Supported Domains**:
- `go2.video` - Video content (YouTube, Vimeo, etc.)
- `go2.tools` - Tools and utilities (GitHub, documentation, etc.)
- `go2.reviews` - Reviews and shopping (Amazon, Yelp, etc.)

## Authentication

### Firebase Authentication
Most endpoints require Firebase ID tokens for authentication:

```http
Authorization: Bearer <firebase_id_token>
```

### Admin Endpoints
Admin endpoints require users with `admin: true` custom claims.

## Links API

### Create Short Link

Create a new short link with optional customization.

```http
POST /api/links/shorten
Content-Type: application/json
Authorization: Bearer <token> (optional for anonymous links)
```

**Request Body:**
```json
{
  "long_url": "https://youtube.com/watch?v=example",
  "base_domain": "go2.video",
  "custom_code": "my-video",
  "password": "secret123",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

**Parameters:**
- `long_url` (required): The destination URL to shorten
- `base_domain` (required): Target domain (`go2.video`, `go2.tools`, `go2.reviews`)
- `custom_code` (optional): Custom short code (3-50 characters, alphanumeric + hyphens/underscores)
- `password` (optional): Password protection (4-100 characters)
- `expires_at` (optional): Expiration date (ISO 8601 format)

**Response:**
```json
{
  "short_url": "https://go2.video/my-video",
  "code": "my-video",
  "qr_url": "/api/qr/go2.video_my-video",
  "long_url": "https://youtube.com/watch?v=example",
  "base_domain": "go2.video",
  "expires_at": "2024-12-31T23:59:59Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid URL or parameters
- `403 Forbidden`: URL blocked by safety validation
- `409 Conflict`: Custom code already taken
- `422 Unprocessable Entity`: Invalid base domain

### Get Link Statistics

Retrieve analytics data for a short link.

```http
GET /api/links/stats/{code}?period={period}
Authorization: Bearer <token> (required for private links)
```

**Parameters:**
- `code` (path): The short code
- `period` (query): Time period (`7d`, `30d`, `all`)

**Response:**
```json
{
  "total_clicks": 150,
  "clicks_by_day": {
    "2024-01-01": 25,
    "2024-01-02": 30,
    "2024-01-03": 20
  },
  "clicks_by_hour": {
    "00": 5,
    "01": 3,
    "02": 1
  },
  "top_referrers": [
    {"referrer": "twitter.com", "count": 45},
    {"referrer": "facebook.com", "count": 30},
    {"referrer": "direct", "count": 25}
  ],
  "top_countries": [
    {"country": "United States", "count": 60, "percentage": 40.0},
    {"country": "India", "count": 40, "percentage": 26.7}
  ],
  "top_cities": [
    {"city": "New York", "count": 25},
    {"city": "Mumbai", "count": 20}
  ],
  "device_breakdown": {
    "mobile": 80,
    "desktop": 60,
    "tablet": 10
  },
  "browser_breakdown": {
    "Chrome": 90,
    "Safari": 35,
    "Firefox": 25
  },
  "os_breakdown": {
    "Android": 45,
    "iOS": 35,
    "Windows": 40
  },
  "last_clicked": "2024-01-03T15:30:00Z"
}
```

### Update Link

Update an existing link (owner or admin only).

```http
PUT /api/links/{code}
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "disabled": false,
  "expires_at": "2024-12-31T23:59:59Z",
  "password": "new-password"
}
```

**Parameters:**
- `disabled` (optional): Enable/disable the link
- `expires_at` (optional): Update expiration date
- `password` (optional): Update password protection

**Response:**
```json
{
  "message": "Link updated successfully"
}
```

### Delete Link

Delete a link (owner or admin only).

```http
DELETE /api/links/{code}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Link deleted successfully"
}
```

### Check Code Availability

Check if a custom code is available across all domains.

```http
GET /api/links/check-availability/{code}
```

**Response:**
```json
{
  "available": false,
  "suggestions": ["my-video-1", "my-video-2", "my-video-alt"],
  "message": "Code 'my-video' is already taken in domains: go2.video, go2.tools",
  "taken_domains": ["go2.video", "go2.tools"]
}
```

### Export Link Data

Export analytics data in various formats.

```http
GET /api/links/export/{code}?format={format}&period={period}
Authorization: Bearer <token>
```

**Parameters:**
- `format`: Export format (`json`, `csv`)
- `period`: Time period (`7d`, `30d`, `all`)

**Response:** File download with appropriate content-type headers.

### List User Links

Get paginated list of user's links.

```http
GET /api/links/?page={page}&limit={limit}&search={search}&domain={domain}
Authorization: Bearer <token>
```

**Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)
- `search` (optional): Search term for filtering
- `domain` (optional): Filter by domain

**Response:**
```json
{
  "links": [
    {
      "code": "my-video",
      "long_url": "https://youtube.com/watch?v=example",
      "base_domain": "go2.video",
      "created_at": "2024-01-01T12:00:00Z",
      "disabled": false,
      "expires_at": null,
      "total_clicks": 150,
      "owner_uid": "user123",
      "is_custom_code": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

## QR Code API

### Generate QR Code

Generate or retrieve cached QR code for a short link.

```http
GET /api/qr/{document_id}?size={size}
```

**Parameters:**
- `document_id` (path): Composite document ID (e.g., `go2.video_abc123`)
- `size` (query): QR code size (`small`, `medium`, `large`)

**Response:** PNG image with caching headers

**Headers:**
```
Content-Type: image/png
Cache-Control: public, max-age=31536000
Content-Disposition: inline; filename=qr_go2.video_abc123_medium.png
```

### Get QR Code Information

Get information about available QR code sizes and URLs.

```http
GET /api/qr/{document_id}/info
```

**Response:**
```json
{
  "code": "abc123",
  "short_url": "https://go2.video/abc123",
  "qr_urls": {
    "small": "/api/qr/go2.video_abc123?size=small",
    "medium": "/api/qr/go2.video_abc123?size=medium",
    "large": "/api/qr/go2.video_abc123?size=large"
  },
  "sizes": {
    "small": {
      "description": "Compact QR code for small spaces",
      "dimensions": "~200x200px"
    },
    "medium": {
      "description": "Standard QR code for general use",
      "dimensions": "~250x250px"
    },
    "large": {
      "description": "Large QR code for print materials",
      "dimensions": "~300x300px"
    }
  }
}
```

## Redirect API

### Handle Redirect

Handle short link redirects with analytics tracking.

```http
GET /{code}
Host: go2.video
```

**Flow:**
1. Extract domain from `Host` header
2. Create composite document ID
3. Look up link in Firestore
4. Check password protection and expiration
5. Log analytics (async)
6. Return redirect response

**Responses:**
- `302 Found`: Successful redirect to destination URL
- `200 OK`: Password form for protected links
- `404 Not Found`: Link doesn't exist
- `410 Gone`: Link is disabled or expired

### Password-Protected Links

For password-protected links, a form is displayed:

```http
POST /{code}
Content-Type: application/x-www-form-urlencoded
Host: go2.video

password=user-entered-password
```

**Responses:**
- `302 Found`: Correct password, redirect to destination
- `401 Unauthorized`: Incorrect password, show form with error

## Configuration API

### Get Base Domains

Get list of available base domains.

```http
GET /api/config/base-domains
```

**Response:**
```json
{
  "base_domains": ["go2.video", "go2.tools", "go2.reviews"],
  "domain_suggestions": {
    "youtube.com": "go2.video",
    "vimeo.com": "go2.video",
    "github.com": "go2.tools",
    "amazon.com": "go2.reviews"
  }
}
```

### Get Plan Information

Get information about available plans and limits.

```http
GET /api/config/plans
```

**Response:**
```json
{
  "plans": {
    "free": {
      "name": "Free",
      "custom_codes": 5,
      "features": ["Basic analytics", "QR codes"]
    },
    "paid": {
      "name": "Pro",
      "custom_codes": 100,
      "features": ["Advanced analytics", "Custom domains", "API access"]
    }
  }
}
```

## Admin API

### Bulk Operations

#### Bulk Disable Links

```http
POST /api/links/admin/bulk-disable
Content-Type: application/json
Authorization: Bearer <admin_token>

["code1", "code2", "code3"]
```

**Response:**
```json
{
  "disabled_count": 2,
  "errors": ["code3: Link not found"]
}
```

#### Bulk Delete Links

```http
POST /api/links/admin/bulk-delete
Content-Type: application/json
Authorization: Bearer <admin_token>

["code1", "code2", "code3"]
```

#### Bulk Update Expiry

```http
POST /api/links/admin/bulk-update-expiry
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "codes": ["code1", "code2"],
  "expires_at": "2024-12-31T23:59:59Z"
}
```

### Get All Links

Get paginated list of all links (admin only).

```http
GET /api/links/admin/all?page={page}&limit={limit}&search={search}
Authorization: Bearer <admin_token>
```

## Hooks API

### Daily Report

Generate daily analytics report.

```http
POST /api/hooks/send_daily_report
Content-Type: application/json
Authorization: Bearer <token>

{
  "date": "2024-01-01",
  "email": "user@example.com",
  "domain_filter": "go2.video"
}
```

**Response:**
```json
{
  "report_generated": true,
  "email_sent": true,
  "total_clicks": 1250,
  "total_links": 45,
  "top_link": {
    "code": "popular-video",
    "clicks": 150
  }
}
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "long_url",
      "issue": "Invalid URL format"
    }
  }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Invalid request data |
| 401 | `AUTHENTICATION_REQUIRED` | Missing or invalid token |
| 403 | `PERMISSION_DENIED` | Insufficient permissions |
| 403 | `SAFETY_VIOLATION` | URL blocked by safety checks |
| 404 | `RESOURCE_NOT_FOUND` | Link or resource not found |
| 409 | `CODE_COLLISION` | Custom code already taken |
| 410 | `RESOURCE_GONE` | Link disabled or expired |
| 422 | `UNPROCESSABLE_ENTITY` | Invalid domain or parameters |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |

## Rate Limiting

### Default Limits
- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Admin users**: 5000 requests per hour

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Webhooks

### Click Event Webhook

Configure webhooks to receive real-time click notifications.

**Webhook Payload:**
```json
{
  "event": "click",
  "timestamp": "2024-01-01T12:00:00Z",
  "link": {
    "code": "abc123",
    "base_domain": "go2.video",
    "long_url": "https://youtube.com/watch?v=example"
  },
  "click": {
    "country": "United States",
    "city": "New York",
    "device_type": "mobile",
    "browser": "Chrome",
    "referrer": "twitter.com"
  }
}
```

## SDKs and Libraries

### JavaScript/TypeScript
```bash
npm install @go2/url-shortener-sdk
```

```typescript
import { Go2Client } from '@go2/url-shortener-sdk';

const client = new Go2Client({
  apiKey: 'your-api-key',
  baseUrl: 'https://go2-api-asia-south1-run.app'
});

const link = await client.createLink({
  longUrl: 'https://example.com',
  baseDomain: 'go2.tools',
  customCode: 'my-link'
});
```

### Python
```bash
pip install go2-url-shortener
```

```python
from go2 import Go2Client

client = Go2Client(api_key='your-api-key')

link = client.create_link(
    long_url='https://example.com',
    base_domain='go2.tools',
    custom_code='my-link'
)
```

## Testing

### Test Environment
- **Base URL**: `https://go2-api-test-asia-south1-run.app`
- **Test Domains**: `test.go2.video`, `test.go2.tools`, `test.go2.reviews`

### Example Test Requests

```bash
# Create test link
curl -X POST https://go2-api-test-asia-south1-run.app/api/links/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "long_url": "https://example.com",
    "base_domain": "go2.tools",
    "custom_code": "test-link"
  }'

# Test redirect
curl -I https://test.go2.tools/test-link

# Get analytics
curl https://go2-api-test-asia-south1-run.app/api/links/stats/test-link
```

---

## Support

For API support and questions:
- **Documentation**: [Multi-Domain Architecture Guide](MULTI_DOMAIN_ARCHITECTURE.md)
- **Issues**: Create GitHub issue with API request/response details
- **Status Page**: Monitor API health and uptime

**API Version**: v1.0.0  
**Last Updated**: January 2024