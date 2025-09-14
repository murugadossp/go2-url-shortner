# Implementation Plan

- [x] 1. Set up project structure and core configuration
  - Create monorepo structure with apps/web, apps/api, and packages/shared directories
  - Initialize Next.js project with TypeScript and Tailwind CSS configuration
  - Initialize FastAPI project with Python dependencies and project structure
  - Set up shared types package with TypeScript interfaces
  - Configure environment files (.env.example) for both frontend and backend
  - _Requirements: 11.1, 11.2_

- [x] 2. Configure Firebase services and authentication
  - Set up Firebase project with Authentication, Firestore, and Storage
  - Configure Google OAuth provider in Firebase Authentication
  - Implement Firebase client SDK setup in Next.js frontend
  - Configure firebase-admin SDK in FastAPI backend with service account
  - Create Firestore security rules for links, users, and config collections
  - _Requirements: 6.1, 6.2, 6.5, 11.4_

- [x] 3. Implement core data models and validation
  - Create TypeScript interfaces for LinkDocument, ClickDocument, UserDocument in shared package
  - Implement Pydantic models for API request/response validation in FastAPI
  - Create Firestore document converters and serializers
  - Implement form validation schemas using Zod for frontend forms
  - Write unit tests for data model validation and serialization
  - _Requirements: 11.1, 11.2, 11.5_

- [x] 4. Build safety and validation service
  - Implement URL scheme validation (HTTP/HTTPS only) with comprehensive tests
  - Create domain blacklist system with configurable blacklist file
  - Implement adult/gambling content pattern detection with regex rules
  - Integrate Google Safe Browsing API v4 for malicious URL detection
  - Create SafetyService class with comprehensive validation pipeline
  - Write unit tests for all safety validation scenarios
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.7_

- [x] 5. Implement link creation and management system
  - Create POST /api/links/shorten endpoint with safety validation integration
  - Implement custom code collision detection and suggestion algorithm
  - Build plan-based custom code limit enforcement (5 for free, 100 for paid)
  - Create link storage system in Firestore with proper indexing
  - Implement password hashing for protected links
  - Write comprehensive tests for link creation scenarios including edge cases
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 7.6, 10.2, 10.3_

- [x] 6. Build URL redirection and click tracking system
  - Implement GET /{code} redirect handler with 302 responses
  - Create click logging system with IP hashing and user agent parsing
  - Integrate IP geolocation service for country/city/region tracking
  - Implement password protection flow for protected links
  - Handle expired and disabled link scenarios with appropriate error pages
  - Create click data storage in Firestore clicks subcollection
  - Write tests for redirect scenarios and click logging accuracy
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 7. Implement QR code generation and caching
  - Create QR code generation service using Python qrcode library
  - Implement GET /api/qr/{code} endpoint returning PNG images
  - Build Firebase Storage integration for QR code caching
  - Create cache-first QR serving strategy with fallback generation
  - Optimize QR code size and quality for different use cases
  - Write tests for QR generation and caching functionality
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 8. Build analytics and reporting system
  - Create analytics aggregation service for click data processing
  - Implement GET /api/stats/{code} endpoint with time-series data
  - Build geographic analytics with country/city breakdowns
  - Create referrer and device analytics with user agent parsing
  - Implement data export functionality in JSON and CSV formats
  - Design analytics dashboard with charts and geographic visualization
  - Write tests for analytics calculations and data aggregation
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 9. Implement domain configuration and management
  - Create GET /api/config/base-domains endpoint serving allowed domains
  - Implement contextual domain suggestion algorithm (YouTube → go2.video)
  - Build domain dropdown component with auto-preselection logic
  - Create admin interface for domain configuration management
  - Implement domain validation in link creation process
  - Write tests for domain suggestion logic and validation
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 10. Build user authentication and plan management
  - Implement Google OAuth login flow in Next.js frontend
  - Create user profile management with plan tracking
  - Build custom code usage tracking and limit enforcement
  - Implement plan upgrade prompts and limit notifications
  - Create user dashboard showing usage statistics and limits
  - Write tests for authentication flows and plan limit enforcement
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 11. Create frontend user interface components
  - Build LinkCreator component with URL input and domain dropdown
  - Implement real-time custom code availability checking
  - Create LinkDisplay component with copy functionality and QR preview
  - Build analytics dashboard with time-series charts and geographic maps
  - Implement responsive design with Tailwind CSS for mobile compatibility
  - Create loading states, error handling, and success notifications
  - Write component tests and accessibility compliance verification
  - _Requirements: 1.1, 1.2, 1.3, 1.6, 4.1, 4.2, 4.5_

- [x] 12. Enhance frontend with modern glassmorphic design
  - Implement glassmorphic design system with backdrop blur and transparency effects
  - Create collapsible/expandable sections for optional features (password, expiry, custom code)
  - Add smooth animations and micro-interactions for better user experience
  - Implement gradient backgrounds and modern color schemes
  - Create floating card layouts with subtle shadows and glass effects
  - Add progressive disclosure for advanced options based on user interaction
  - Implement responsive design improvements with modern spacing and typography
  - _Requirements: 1.1, 1.2, 1.3, 1.6, 11.1, 11.2_

- [x] 13. Implement administrative interface and controls
  - Create admin authentication using Firebase custom claims
  - Build admin dashboard for link management and user oversight
  - Implement bulk operations for link management (disable, delete, edit expiry)
  - Create user management interface with plan assignment capabilities
  - Build system statistics and monitoring dashboard
  - Implement audit logging for administrative actions
  - Write tests for admin functionality and permission enforcement
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 14. Build daily reporting and hook system
  - Create send_daily_report hook with date and domain filtering
  - Implement click data aggregation for daily report generation
  - Build HTML email template rendering for analytics reports
  - Integrate SendGrid for email delivery when configured
  - Create manual report generation interface in analytics dashboard
  - Implement POST /api/hooks/send_daily_report endpoint
  - Write tests for report generation and email delivery
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 15. Implement comprehensive error handling and validation
  - Create standardized error response format across all API endpoints
  - Implement client-side error boundaries and user-friendly error messages
  - Build rate limiting middleware for API protection
  - Create input validation with detailed error messages for form fields
  - Implement graceful degradation for external service failures
  - Add comprehensive logging for debugging and monitoring
  - Write tests for error scenarios and edge cases
  - _Requirements: 7.7, 11.5_

- [ ] 16. Add testing suite and quality assurance
  - Write unit tests for all backend services and API endpoints
  - Create integration tests for complete user workflows
  - Implement frontend component tests with React Testing Library
  - Build end-to-end tests for critical user journeys using Playwright
  - Set up test data fixtures and cleanup procedures
  - Configure continuous integration pipeline with automated testing
  - Perform accessibility testing and compliance verification
  - _Requirements: All requirements validation through comprehensive testing_

- [x] 17. Implement advanced links management with search and sort functionality
  - Enhance GET /api/links/ endpoint to accept search, sort, and filter query parameters
  - Add search functionality across link codes, long URLs, and base domains using Firestore text matching
  - Implement multi-criteria sorting by creation date, click count, expiration date, and alphabetical order
  - Create additional Firestore composite indexes for new query patterns (clicks+created_at, expires_at+owner_uid)
  - Build responsive search bar component with debounced input and real-time results
  - Implement sort dropdown with intuitive options (Most Clicked, Newest, Oldest, A-Z, Expiring Soon)
  - Add filter chips for quick filtering by status (Active, Expired, Disabled) and link type (Custom, Generated)
  - Create pagination controls for large result sets with proper loading states
  - Implement result counter showing "X of Y links" with current search/filter context
  - Add "Clear All Filters" functionality to reset search and filter state
  - Optimize query performance with proper indexing and caching strategies
  - Write comprehensive tests for search, sort, and filter functionality
  - Test performance with large datasets to ensure scalability
  - _Requirements: Enhanced user experience for link management and organization_

- [ ] 18. Configure deployment and production setup
  - Set up production Firebase project with proper security rules
  - Configure environment variables and secrets management
  - Create Docker containers for FastAPI backend deployment
  - Set up Next.js production build with optimization
  - Configure CDN and caching strategies for performance
  - Implement monitoring and alerting for production systems
  - Create deployment documentation and runbooks
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
