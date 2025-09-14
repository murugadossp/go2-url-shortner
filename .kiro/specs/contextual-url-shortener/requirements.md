# Requirements Document

## Introduction

This document outlines the requirements for a production-ready contextual URL shortener that allows users to create short links with contextual base domains (go2.video, go2.reviews, go2.tools), generate QR codes, and track basic analytics. The system includes safety measures, user authentication, and administrative capabilities built on a modern tech stack with Next.js frontend and FastAPI backend.

## Requirements

### Requirement 1: Core URL Shortening

**User Story:** As a user, I want to paste a long URL and create a short link with a contextual domain, so that I can share memorable, branded short URLs.

#### Acceptance Criteria

1. WHEN a user submits a valid HTTP/HTTPS URL THEN the system SHALL create a short link with the selected base domain
2. WHEN a user selects a base domain from dropdown (go2.video, go2.reviews, go2.tools) THEN the system SHALL use that domain for the short URL
3. WHEN a user provides an optional custom code THEN the system SHALL use that code if available, otherwise inform the user of the collision and suggest alternatives
4. WHEN a free plan user attempts to create more than 5 custom codes THEN the system SHALL enforce the limit and suggest upgrading to paid plan
5. WHEN a paid plan user attempts to create more than 100 custom codes per month THEN the system SHALL enforce the monthly limit
6. WHEN a user sets an optional password THEN the system SHALL require password entry before redirecting
7. WHEN a user sets an expiration date THEN the system SHALL disable the link after that date
8. WHEN short link creation succeeds THEN the system SHALL return the short URL, code, and QR code URL

### Requirement 2: URL Redirection and Click Tracking

**User Story:** As a user, I want my short links to redirect visitors to the original URL while tracking basic analytics, so that I can measure engagement.

#### Acceptance Criteria

1. WHEN a visitor accesses a short URL THEN the system SHALL redirect with HTTP 302 to the original URL
2. WHEN a redirect occurs THEN the system SHALL log click data (timestamp, user agent, referrer, country)
3. WHEN a link is password-protected THEN the system SHALL prompt for password before redirecting
4. WHEN a link is expired or disabled THEN the system SHALL show an appropriate error page
5. IF a link does not exist THEN the system SHALL return a 404 error

### Requirement 3: QR Code Generation

**User Story:** As a user, I want to generate QR codes for my short links, so that I can share them in print or mobile contexts.

#### Acceptance Criteria

1. WHEN a user requests a QR code for a short link THEN the system SHALL generate a PNG QR code
2. WHEN QR code is requested via API THEN the system SHALL return the PNG image directly
3. IF Firebase Storage is configured THEN the system SHALL cache QR codes to reduce generation overhead
4. WHEN QR code generation fails THEN the system SHALL return an appropriate error response

### Requirement 4: Basic Analytics

**User Story:** As a user, I want to view basic analytics for my short links, so that I can understand how they're being used.

#### Acceptance Criteria

1. WHEN a user requests link statistics THEN the system SHALL show total clicks, clicks by day (7/30 days), top referrers, top devices, and last clicked timestamp
2. WHEN displaying analytics THEN the system SHALL aggregate data from the clicks collection
3. WHEN no clicks exist THEN the system SHALL show zero values with appropriate messaging
4. WHEN analytics are requested for non-existent links THEN the system SHALL return 404
5. WHEN displaying analytics THEN the system SHALL provide exportable data in common formats (JSON, CSV)

### Requirement 5: Domain Configuration

**User Story:** As a system administrator, I want to configure available base domains, so that users can select from approved contextual domains.

#### Acceptance Criteria

1. WHEN the frontend loads THEN the system SHALL fetch available domains from the backend configuration
2. WHEN a user creates a link THEN the system SHALL validate the selected domain against the allowed list
3. WHEN possible, the system SHALL auto-preselect domain based on URL context (YouTube → go2.video)
4. WHEN domain configuration changes THEN the system SHALL update without requiring application restart

### Requirement 6: User Authentication

**User Story:** As a user, I want to create an account and log in, so that I can manage my short links and access advanced features.

#### Acceptance Criteria

1. WHEN a user signs up THEN the system SHALL create an account using Firebase Authentication
2. WHEN a user logs in THEN the system SHALL support Google OAuth authentication
3. WHEN a user is authenticated THEN the system SHALL associate created links with their user ID
4. WHEN a user is not logged in THEN the system SHALL still allow anonymous link creation for demo purposes
5. WHEN making authenticated API calls THEN the system SHALL verify Firebase ID tokens

### Requirement 7: Safety and Abuse Prevention

**User Story:** As a system administrator, I want to prevent malicious or inappropriate URLs from being shortened, so that the service maintains a good reputation.

#### Acceptance Criteria

1. WHEN a URL is submitted THEN the system SHALL perform all safety checks before creating the short link
2. WHEN a URL has non-HTTP/HTTPS schemes THEN the system SHALL reject creation (javascript:, data:, etc.)
3. WHEN a URL contains blacklisted domains or keywords THEN the system SHALL reject the creation request
4. WHEN a URL matches adult/gambling patterns THEN the system SHALL block creation with appropriate error message
5. WHEN Google Safe Browsing is enabled THEN the system SHALL check URLs against the Safe Browsing API and block flagged URLs before creation
6. WHEN a custom code conflicts with existing codes THEN the system SHALL return a collision error with suggested alternatives
7. WHEN any safety check fails THEN the system SHALL return descriptive error messages and not create the link

### Requirement 8: Administrative Interface

**User Story:** As an administrator, I want to manage links and users, so that I can maintain system integrity and handle abuse reports.

#### Acceptance Criteria

1. WHEN an admin accesses the admin panel THEN the system SHALL verify admin privileges via Firebase custom claims
2. WHEN an admin views the link list THEN the system SHALL display all links with owner, creation date, and status
3. WHEN an admin disables a link THEN the system SHALL prevent future redirects and show disabled message
4. WHEN an admin edits link expiration THEN the system SHALL update the expires_at field
5. WHEN admin actions are performed THEN the system SHALL log the changes for audit purposes

### Requirement 9: Daily Reporting Hook

**User Story:** As a user, I want to receive daily analytics reports, so that I can track my links' performance over time.

#### Acceptance Criteria

1. WHEN a daily report is requested THEN the system SHALL aggregate clicks for the specified date
2. WHEN generating reports THEN the system SHALL include totals, top referrers, top devices, and per-link breakdowns
3. IF SendGrid is configured THEN the system SHALL send email reports
4. WHEN email is not configured THEN the system SHALL return HTML report data for display
5. WHEN report generation fails THEN the system SHALL return appropriate error messages

### Requirement 10: Plan Management and Billing

**User Story:** As a user, I want to have different service tiers (free and paid), so that I can access features appropriate to my usage level.

#### Acceptance Criteria

1. WHEN a user signs up THEN the system SHALL assign them to the free plan by default
2. WHEN a free plan user creates custom codes THEN the system SHALL track usage and enforce 5 custom code limit
3. WHEN a paid plan user creates custom codes THEN the system SHALL track monthly usage and enforce 100 per month limit
4. WHEN plan limits are reached THEN the system SHALL display upgrade prompts for free users or limit notifications for paid users
5. WHEN a user upgrades their plan THEN the system SHALL update their limits immediately

### Requirement 11: Data Storage and Security

**User Story:** As a system operator, I want secure and scalable data storage, so that user data is protected and the system can grow.

#### Acceptance Criteria

1. WHEN storing link data THEN the system SHALL use Firestore with proper document structure
2. WHEN storing passwords THEN the system SHALL hash passwords and never store plaintext
3. WHEN logging clicks THEN the system SHALL hash IP addresses for privacy
4. WHEN users access data THEN the system SHALL enforce Firestore security rules
5. WHEN handling expired links THEN the system SHALL check expiration at redirect time