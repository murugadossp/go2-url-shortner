# Testing Guide

This document provides comprehensive information about the testing suite for the contextual URL shortener project.

## Quick Start Guides

- **[Test Execution Guide](./TEST_EXECUTION_GUIDE.md)** - Step-by-step instructions for running tests
- **[Test Cheat Sheet](./TEST_CHEAT_SHEET.md)** - Quick reference for common test commands
- **[CI/CD Pipeline](./.github/workflows/ci.yml)** - Automated testing configuration

## Overview

Our testing strategy includes:
- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test complete workflows and API interactions
- **End-to-End Tests**: Test user journeys in a real browser
- **Accessibility Tests**: Ensure WCAG compliance
- **Performance Tests**: Load testing and performance monitoring
- **Security Tests**: Vulnerability scanning and security validation

## Test Structure

```
├── apps/
│   ├── api/
│   │   ├── tests/
│   │   │   ├── fixtures/           # Test data and fixtures
│   │   │   ├── performance/        # Load testing with Locust
│   │   │   ├── test_*.py          # Unit and integration tests
│   │   │   └── conftest.py        # Pytest configuration
│   │   └── pytest.ini             # Pytest settings
│   └── web/
│       ├── e2e/                   # End-to-end tests
│       │   ├── fixtures/          # E2E test data
│       │   └── *.spec.ts         # Playwright tests
│       ├── src/
│       │   └── **/__tests__/      # Component tests
│       ├── jest.config.js         # Jest configuration
│       ├── jest.setup.js          # Jest setup
│       └── playwright.config.ts   # Playwright configuration
└── packages/
    └── shared/
        └── src/
            └── **/__tests__/      # Shared package tests
```

## Running Tests

### Backend Tests

```bash
# Navigate to API directory
cd apps/api

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_links.py

# Run tests in parallel
pytest -n auto

# Run integration tests only
pytest -m integration

# Run performance tests
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

### Frontend Tests

```bash
# Navigate to web directory
cd apps/web

# Run unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run accessibility tests
npm run test:accessibility

# Run all tests
npm run test:all
```

### Shared Package Tests

```bash
# Navigate to shared package
cd packages/shared

# Run tests
npm test

# Run tests in watch mode
npm run test:watch
```

## Test Categories

### 1. Unit Tests

**Backend Unit Tests** (`apps/api/tests/test_*.py`)
- Service layer functions
- Utility functions
- Data model validation
- Individual API endpoints

**Frontend Unit Tests** (`apps/web/src/**/__tests__/*.test.tsx`)
- React component rendering
- Hook behavior
- Utility functions
- Form validation

**Example Backend Unit Test:**
```python
def test_safety_service_validates_url():
    safety_service = SafetyService()
    result = safety_service.validate_url('https://example.com')
    assert result['is_safe'] is True
```

**Example Frontend Unit Test:**
```typescript
test('LinkCreator renders correctly', () => {
  render(<LinkCreator />);
  expect(screen.getByLabelText(/url/i)).toBeInTheDocument();
});
```

### 2. Integration Tests

**Backend Integration Tests** (`apps/api/tests/test_integration_*.py`)
- Complete API workflows
- Database interactions
- External service integrations
- Authentication flows

**Example Integration Test:**
```python
async def test_complete_link_creation_workflow(client):
    # Create link
    response = await client.post('/api/links/shorten', json={
        'long_url': 'https://example.com',
        'base_domain': 'go2.tools'
    })
    assert response.status_code == 200
    
    # Access link
    code = response.json()['code']
    redirect_response = await client.get(f'/{code}')
    assert redirect_response.status_code == 302
```

### 3. End-to-End Tests

**E2E Tests** (`apps/web/e2e/*.spec.ts`)
- Complete user journeys
- Cross-browser testing
- Mobile responsiveness
- Real user interactions

**Example E2E Test:**
```typescript
test('should create and access short link', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="url-input"]', 'https://example.com');
  await page.click('[data-testid="create-button"]');
  
  const shortUrl = await page.textContent('[data-testid="short-url"]');
  expect(shortUrl).toContain('go2.');
});
```

### 4. Accessibility Tests

**Accessibility Tests** (`apps/web/e2e/accessibility.spec.ts`)
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader compatibility
- Color contrast validation

**Example Accessibility Test:**
```typescript
test('should not have accessibility violations', async ({ page }) => {
  await page.goto('/');
  const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
  expect(accessibilityScanResults.violations).toEqual([]);
});
```

### 5. Performance Tests

**Load Tests** (`apps/api/tests/performance/locustfile.py`)
- Concurrent user simulation
- API endpoint performance
- Database query optimization
- Rate limiting validation

**Example Performance Test:**
```python
class URLShortenerUser(HttpUser):
    @task(5)
    def create_short_link(self):
        payload = {
            'long_url': 'https://example.com',
            'base_domain': 'go2.tools'
        }
        self.client.post('/api/links/shorten', json=payload)
```

## Test Data and Fixtures

### Backend Fixtures

Located in `apps/api/tests/fixtures/test_data.py`:
- User data (regular, admin, paid users)
- Link data (basic, custom, protected, expired)
- Click analytics data
- Configuration data

### Frontend Fixtures

Located in `apps/web/e2e/fixtures/`:
- Test URLs (valid, invalid, unsafe)
- Mock user data
- Mock analytics data
- Authentication setup

### Using Fixtures

**Backend:**
```python
def test_with_user_fixture(test_user):
    assert test_user['email'] == 'test@example.com'
    assert test_user['plan_type'] == 'free'
```

**Frontend:**
```typescript
import { testUrls } from './fixtures/test-data';

test('validates URL', () => {
  // Use testUrls.valid.youtube
});
```

## Mocking and Test Doubles

### Backend Mocking

```python
@patch('src.services.firebase_service.get_firestore_client')
def test_with_mock_firestore(mock_firestore):
    mock_db = MagicMock()
    mock_firestore.return_value = mock_db
    # Test implementation
```

### Frontend Mocking

```typescript
jest.mock('@/lib/api', () => ({
  apiClient: {
    post: jest.fn().mockResolvedValue({ data: { code: 'abc123' } }),
  },
}));
```

## Continuous Integration

Our CI pipeline runs:
1. **Backend Tests**: Unit and integration tests with coverage
2. **Frontend Tests**: Component tests with coverage
3. **E2E Tests**: Cross-browser testing
4. **Accessibility Tests**: WCAG compliance validation
5. **Performance Tests**: Load testing (on main branch)
6. **Security Scanning**: Vulnerability detection
7. **Code Quality**: Linting and type checking

### CI Configuration

See `.github/workflows/ci.yml` for the complete CI/CD pipeline.

## Test Coverage

### Coverage Requirements
- **Backend**: Minimum 80% line coverage
- **Frontend**: Minimum 75% line coverage
- **Critical paths**: 100% coverage required

### Viewing Coverage Reports

**Backend:**
```bash
cd apps/api
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

**Frontend:**
```bash
cd apps/web
npm run test:coverage
open coverage/lcov-report/index.html
```

## Best Practices

### Writing Tests

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **Use Descriptive Names**: Test names should describe the scenario
3. **Test One Thing**: Each test should verify one specific behavior
4. **Use Fixtures**: Reuse test data through fixtures
5. **Mock External Dependencies**: Don't rely on external services
6. **Test Edge Cases**: Include error conditions and boundary cases

### Test Organization

1. **Group Related Tests**: Use describe blocks or test classes
2. **Use Setup/Teardown**: Clean up after tests
3. **Parallel Execution**: Write tests that can run in parallel
4. **Fast Feedback**: Unit tests should run quickly

### Data Management

1. **Isolated Tests**: Each test should be independent
2. **Clean State**: Reset data between tests
3. **Realistic Data**: Use data that resembles production
4. **Minimal Data**: Only create data needed for the test

## Debugging Tests

### Backend Debugging

```bash
# Run single test with verbose output
pytest tests/test_links.py::test_create_link -v -s

# Debug with pdb
pytest tests/test_links.py::test_create_link --pdb

# Run with logging
pytest tests/test_links.py --log-cli-level=DEBUG
```

### Frontend Debugging

```bash
# Run tests in debug mode
npm test -- --detectOpenHandles

# Run specific test
npm test -- LinkCreator.test.tsx

# Debug E2E tests
npx playwright test --debug
```

## Performance Testing

### Load Testing with Locust

```bash
# Start API server
cd apps/api
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Run load test
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users=50 --spawn-rate=5 --run-time=60s
```

### Performance Metrics

Monitor:
- Response times (p50, p95, p99)
- Throughput (requests per second)
- Error rates
- Resource utilization

## Security Testing

### Automated Security Scanning

```bash
# Run Trivy vulnerability scanner
trivy fs .

# Check for secrets
git-secrets --scan
```

### Manual Security Testing

- Input validation testing
- Authentication bypass attempts
- Authorization testing
- SQL injection testing
- XSS testing

## Accessibility Testing

### Automated Testing

```bash
# Run accessibility tests
npm run test:accessibility
```

### Manual Testing

- Keyboard navigation
- Screen reader testing
- Color contrast validation
- Focus management
- ARIA attributes

## Troubleshooting

### Common Issues

1. **Flaky Tests**: Use proper waits and stable selectors
2. **Slow Tests**: Mock external dependencies
3. **Test Isolation**: Ensure tests don't depend on each other
4. **Environment Issues**: Use consistent test environments

### Getting Help

1. Check test logs for error details
2. Run tests individually to isolate issues
3. Use debugging tools (pdb, browser dev tools)
4. Review test documentation and examples

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Add appropriate test coverage
4. Update test documentation
5. Consider accessibility and performance implications

For more information, see the main README.md file.