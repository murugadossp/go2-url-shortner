# Contextual URL Shortener

A production-ready contextual URL shortener with safety measures, analytics, and QR code generation.

## Project Structure

```
go2/
├── apps/
│   ├── web/              # Next.js frontend
│   └── api/              # FastAPI backend
├── packages/
│   └── shared/           # Shared TypeScript types
└── README.md
```

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.9+
- **Database**: Firebase Firestore
- **Authentication**: Firebase Auth
- **Storage**: Firebase Storage

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.9+
- npm or yarn

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm run install:all
   ```

3. Set up environment variables:
   ```bash
   cp apps/web/.env.example apps/web/.env.local
   cp apps/api/.env.example apps/api/.env
   ```

4. Configure Firebase:
   - Create a Firebase project
   - Enable Authentication, Firestore, and Storage
   - Download service account key for backend
   - Update environment variables

### Development

Start all services:
```bash
npm run dev
```

Or start individually:
```bash
# Frontend (http://localhost:3000)
npm run dev:web

# Backend (http://localhost:8000)
npm run dev:api

# Shared types (watch mode)
npm run dev:shared
```

### Building

```bash
npm run build
```

### Testing

#### Quick Test Execution

```bash
# Run all tests
./scripts/run-tests.sh

# Run tests with coverage
./scripts/run-tests.sh --coverage-only

# Skip slow tests (E2E and performance)
./scripts/run-tests.sh --skip-e2e --skip-performance
```

#### Individual Test Categories

```bash
# Backend tests
cd apps/api && pytest

# Frontend tests  
cd apps/web && npm test

# E2E tests
cd apps/web && npm run test:e2e

# Accessibility tests
cd apps/web && npm run test:accessibility

# Performance tests
cd apps/api && locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

For detailed testing instructions, see [TEST_EXECUTION_GUIDE.md](./TEST_EXECUTION_GUIDE.md)

## Features

- ✅ Contextual domain selection (go2.video, go2.reviews, go2.tools)
- ✅ Custom short codes with collision detection
- ✅ QR code generation and caching
- ✅ Click tracking and analytics
- ✅ User authentication and plan management
- ✅ Safety validation and abuse prevention
- ✅ Administrative interface
- ✅ Daily reporting system

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.