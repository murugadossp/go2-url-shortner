# Test Execution Guide

This guide provides step-by-step instructions for running all types of tests in the contextual URL shortener project.

## Quick Start

### Run All Tests (Recommended)
```bash
# From project root
./scripts/run-tests.sh
```

### Run All Tests with Coverage
```bash
./scripts/run-tests.sh --coverage-only
```

### Run Tests Excluding E2E (Faster)
```bash
./scripts/run-tests.sh --skip-e2e --skip-performance
```

## Prerequisites

Before running tests, ensure you have:

1. **Node.js** (v18 or higher)
2. **Python** (3.11 or higher)
3. **npm** package manager
4. **pip** Python package manager

### Install Dependencies

```bash
# Backend dependencies
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend dependencies
cd ../web
npm install

# Shared package dependencies
cd ../../packages/shared
npm install
```

## Individual Test Categories

### 1. Backend Tests

#### Unit Tests
```bash
cd apps/api
source venv/bin/activate
pytest
```

#### With Coverage
```bash
pytest --cov=src --cov-report=html --cov-report=term
```

#### Specific Test File
```bash
pytest tests/test_models.py -v
```

#### Parallel Execution
```bash
pytest -n auto
```

#### Integration Tests Only
```bash
pytest -m integration
```

#### Performance Tests
```bash
# Start API server first
uvicorn src.main:app --host 0.0.0.0 --port 8000 &

# Run load tests
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users=50 --spawn-rate=5 --run-time=60s --headless
```

### 2. Frontend Tests

#### Unit Tests
```bash
cd apps/web
npm test
```

#### Watch Mode
```bash
npm run test:watch
```

#### With Coverage
```bash
npm run test:coverage
```

#### Specific Test File
```bash
npm test -- Button.test.tsx
```

#### Update Snapshots
```bash
npm test -- --updateSnapshot
```

### 3. End-to-End Tests

#### Install Playwright (First Time)
```bash
cd apps/web
npx playwright install
```

#### Run All E2E Tests
```bash
npm run test:e2e
```

#### Run with UI Mode
```bash
npm run test:e2e:ui
```

#### Run Specific Browser
```bash
npx playwright test --project=chromium
```

#### Run Specific Test File
```bash
npx playwright test link-creation.spec.ts
```

#### Debug Mode
```bash
npx playwright test --debug
```

#### Generate Test Report
```bash
npx playwright show-report
```

### 4. Accessibility Tests

#### Run All Accessibility Tests
```bash
cd apps/web
npm run test:accessibility
```

#### Run Specific Accessibility Test
```bash
npx playwright test accessibility.spec.ts
```

### 5. Shared Package Tests

```bash
cd packages/shared
npm test
```

#### Watch Mode
```bash
npm run test:watch
```

## Advanced Test Execution

### Running Tests in CI/CD Mode

```bash
# Backend
cd apps/api
pytest --cov=src --cov-report=xml -n auto

# Frontend
cd apps/web
npm run test:coverage

# E2E
npm run test:e2e
```

### Custom Test Configurations

#### Backend Test Markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

#### Frontend Test Patterns
```bash
# Run tests matching pattern
npm test -- --testNamePattern="Button"

# Run tests in specific directory
npm test -- src/components/__tests__/

# Run tests with specific timeout
npm test -- --testTimeout=10000
```

#### E2E Test Options
```bash
# Run tests in headed mode
npx playwright test --headed

# Run tests with specific viewport
npx playwright test --config=playwright.config.ts

# Run tests with video recording
npx playwright test --video=on

# Run tests with trace
npx playwright test --trace=on
```

## Test Environment Setup

### Environment Variables

Create `.env.test` files for test-specific configuration:

#### Backend (.env.test)
```bash
ENVIRONMENT=test
FIREBASE_PROJECT_ID=test-project
DISABLE_AUTH=true
DISABLE_SAFETY_CHECKS=true
```

#### Frontend (.env.test.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_CONFIG={"projectId":"test-project"}
```

### Mock Services

#### Start Mock Backend for E2E Tests
```bash
cd apps/api
ENVIRONMENT=test uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Debugging Tests

### Backend Debugging

#### With pdb
```bash
pytest tests/test_models.py::test_specific_function --pdb
```

#### With logging
```bash
pytest tests/test_models.py --log-cli-level=DEBUG
```

#### Verbose output
```bash
pytest tests/test_models.py -v -s
```

### Frontend Debugging

#### Debug specific test
```bash
npm test -- --testNamePattern="Button renders" --verbose
```

#### Run with Node debugger
```bash
node --inspect-brk node_modules/.bin/jest --runInBand
```

### E2E Debugging

#### Debug mode with browser
```bash
npx playwright test --debug
```

#### Step through test
```bash
npx playwright test --debug --headed
```

#### Generate trace
```bash
npx playwright test --trace=on
npx playwright show-trace trace.zip
```

## Test Reports and Coverage

### View Coverage Reports

#### Backend Coverage
```bash
cd apps/api
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

#### Frontend Coverage
```bash
cd apps/web
npm run test:coverage
open coverage/lcov-report/index.html
```

### Test Reports Location

After running tests, reports are generated in:
- `apps/api/htmlcov/` - Backend coverage
- `apps/web/coverage/` - Frontend coverage
- `apps/web/playwright-report/` - E2E test results
- `reports/` - Consolidated reports (when using run-tests.sh)

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

### Local CI Simulation

```bash
# Simulate CI environment
CI=true ./scripts/run-tests.sh
```

## Performance Testing

### Load Testing Setup

```bash
cd apps/api
source venv/bin/activate
pip install locust

# Start API server
uvicorn src.main:app --host 0.0.0.0 --port 8000 &

# Run load test
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Load Test Options

```bash
# Headless mode with specific parameters
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users=100 --spawn-rate=10 --run-time=300s --headless

# Generate HTML report
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users=50 --spawn-rate=5 --run-time=60s --headless \
       --html=performance-report.html
```

## Troubleshooting

### Common Issues

#### Backend Tests

**Issue**: Import errors
```bash
# Solution: Ensure PYTHONPATH is set
export PYTHONPATH=.
pytest
```

**Issue**: Database connection errors
```bash
# Solution: Use test environment
ENVIRONMENT=test pytest
```

#### Frontend Tests

**Issue**: Module not found errors
```bash
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue**: React/DOM testing issues
```bash
# Solution: Check jest.setup.js configuration
npm test -- --no-cache
```

#### E2E Tests

**Issue**: Browser not found
```bash
# Solution: Reinstall Playwright browsers
npx playwright install
```

**Issue**: Server not responding
```bash
# Solution: Ensure backend is running
curl http://localhost:8000/health
```

### Test Data Cleanup

#### Reset Test Database
```bash
# Backend cleanup (if using real database)
python scripts/cleanup_test_data.py
```

#### Clear Test Cache
```bash
# Backend
cd apps/api
rm -rf .pytest_cache __pycache__

# Frontend
cd apps/web
npm test -- --clearCache
```

## Best Practices

### Before Running Tests

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Install/update dependencies**
   ```bash
   cd apps/api && pip install -r requirements.txt
   cd ../web && npm install
   cd ../../packages/shared && npm install
   ```

3. **Check environment**
   ```bash
   python --version  # Should be 3.11+
   node --version    # Should be 18+
   ```

### During Development

1. **Run relevant tests frequently**
   ```bash
   # When working on backend
   cd apps/api && pytest tests/test_specific_module.py

   # When working on frontend
   cd apps/web && npm test -- ComponentName.test.tsx
   ```

2. **Use watch modes**
   ```bash
   # Backend
   pytest-watch

   # Frontend
   npm run test:watch
   ```

3. **Run full test suite before commits**
   ```bash
   ./scripts/run-tests.sh --skip-performance
   ```

### Test Writing

1. **Follow naming conventions**
   - Backend: `test_function_name_scenario`
   - Frontend: `should do something when condition`

2. **Use descriptive test names**
   ```python
   def test_create_link_with_custom_code_succeeds():
   ```

3. **Keep tests isolated and independent**

4. **Use appropriate fixtures and mocks**

## Quick Reference

### Most Common Commands

```bash
# Run all tests quickly
./scripts/run-tests.sh --skip-e2e --skip-performance

# Backend unit tests
cd apps/api && pytest

# Frontend unit tests
cd apps/web && npm test

# E2E tests
cd apps/web && npm run test:e2e

# Coverage reports
cd apps/api && pytest --cov=src --cov-report=html
cd apps/web && npm run test:coverage

# Performance tests
cd apps/api && locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Test Script Options

```bash
./scripts/run-tests.sh --help

Options:
  --skip-e2e          Skip end-to-end tests
  --skip-performance  Skip performance tests
  --coverage-only     Only run tests with coverage reporting
  --verbose           Enable verbose output
  --parallel          Run tests in parallel where possible
  --help              Show help message
```

For more detailed information, see [TESTING.md](./TESTING.md).