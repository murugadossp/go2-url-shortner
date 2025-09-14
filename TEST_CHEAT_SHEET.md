# Test Execution Cheat Sheet

Quick reference for running tests in the contextual URL shortener project.

## 🚀 Quick Commands

### All Tests
```bash
./scripts/run-tests.sh                    # Run everything
./scripts/run-tests.sh --coverage-only   # With coverage
./scripts/run-tests.sh --skip-e2e        # Skip E2E tests
```

### Backend Tests
```bash
cd apps/api
pytest                                    # All tests
pytest --cov=src --cov-report=html      # With coverage
pytest tests/test_models.py             # Specific file
pytest -n auto                          # Parallel
```

### Frontend Tests
```bash
cd apps/web
npm test                                 # All tests
npm run test:coverage                   # With coverage
npm run test:watch                      # Watch mode
npm test -- Button.test.tsx            # Specific file
```

### E2E Tests
```bash
cd apps/web
npm run test:e2e                        # All E2E tests
npm run test:e2e:ui                     # With UI
npx playwright test --debug             # Debug mode
npx playwright test link-creation.spec.ts # Specific test
```

### Accessibility Tests
```bash
cd apps/web
npm run test:accessibility              # All accessibility tests
npx playwright test accessibility.spec.ts # Specific test
```

### Performance Tests
```bash
cd apps/api
# Start server first: uvicorn src.main:app --port 8000 &
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users=50 --spawn-rate=5 --run-time=60s --headless
```

## 🔧 Setup Commands

### First Time Setup
```bash
# Backend
cd apps/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd apps/web
npm install
npx playwright install

# Shared
cd packages/shared
npm install
```

### Environment Setup
```bash
# Backend test environment
export ENVIRONMENT=test
export FIREBASE_PROJECT_ID=test-project

# Frontend test environment
export NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🐛 Debug Commands

### Backend Debug
```bash
pytest tests/test_file.py::test_function --pdb    # Python debugger
pytest tests/test_file.py --log-cli-level=DEBUG   # Debug logging
pytest tests/test_file.py -v -s                   # Verbose output
```

### Frontend Debug
```bash
npm test -- --testNamePattern="test name" --verbose
node --inspect-brk node_modules/.bin/jest --runInBand
```

### E2E Debug
```bash
npx playwright test --debug                       # Debug mode
npx playwright test --headed                      # Show browser
npx playwright test --trace=on                    # Generate trace
```

## 📊 Coverage Commands

### View Coverage
```bash
# Backend
cd apps/api
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Frontend
cd apps/web
npm run test:coverage
open coverage/lcov-report/index.html
```

## 🔍 Test Filtering

### Backend Filters
```bash
pytest -m unit                          # Unit tests only
pytest -m integration                   # Integration tests only
pytest -m "not slow"                    # Skip slow tests
pytest -k "test_create"                 # Tests matching pattern
```

### Frontend Filters
```bash
npm test -- --testPathPattern=Button    # Files matching pattern
npm test -- --testNamePattern="render"  # Tests matching pattern
```

### E2E Filters
```bash
npx playwright test --project=chromium  # Specific browser
npx playwright test --grep="login"      # Tests matching pattern
```

## 🚨 Common Issues & Fixes

### Backend Issues
```bash
# Import errors
export PYTHONPATH=.

# Database connection
ENVIRONMENT=test pytest

# Clear cache
rm -rf .pytest_cache __pycache__
```

### Frontend Issues
```bash
# Module not found
rm -rf node_modules package-lock.json && npm install

# Clear Jest cache
npm test -- --clearCache
```

### E2E Issues
```bash
# Browser not found
npx playwright install

# Server not responding
curl http://localhost:8000/health
```

## 📈 Performance Testing

### Load Test Options
```bash
# Basic load test
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Custom parameters
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users=100 --spawn-rate=10 --run-time=300s --headless

# Generate report
locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
       --users=50 --spawn-rate=5 --run-time=60s --headless \
       --html=performance-report.html
```

## 📝 Test Writing Quick Tips

### Backend Test Structure
```python
def test_function_name_scenario():
    # Arrange
    setup_data()
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected
```

### Frontend Test Structure
```typescript
test('should do something when condition', () => {
  // Arrange
  render(<Component />);
  
  // Act
  fireEvent.click(screen.getByRole('button'));
  
  // Assert
  expect(screen.getByText('result')).toBeInTheDocument();
});
```

### E2E Test Structure
```typescript
test('user journey description', async ({ page }) => {
  // Navigate
  await page.goto('/');
  
  // Interact
  await page.fill('input', 'value');
  await page.click('button');
  
  // Assert
  await expect(page.locator('result')).toBeVisible();
});
```

## 🔗 Quick Links

- [Detailed Testing Guide](./TESTING.md)
- [Full Execution Guide](./TEST_EXECUTION_GUIDE.md)
- [CI/CD Pipeline](./.github/workflows/ci.yml)
- [Test Runner Script](./scripts/run-tests.sh)