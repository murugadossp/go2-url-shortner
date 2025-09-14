#!/bin/bash

# Comprehensive test runner script for the contextual URL shortener
# This script runs all tests in the correct order and generates reports

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run tests with error handling
run_test() {
    local test_name="$1"
    local test_command="$2"
    local test_dir="$3"
    
    print_status "Running $test_name..."
    
    if [ -n "$test_dir" ]; then
        cd "$test_dir"
    fi
    
    if eval "$test_command"; then
        print_success "$test_name passed"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Initialize variables
SKIP_E2E=false
SKIP_PERFORMANCE=false
COVERAGE_ONLY=false
VERBOSE=false
PARALLEL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-e2e)
            SKIP_E2E=true
            shift
            ;;
        --skip-performance)
            SKIP_PERFORMANCE=true
            shift
            ;;
        --coverage-only)
            COVERAGE_ONLY=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --skip-e2e          Skip end-to-end tests"
            echo "  --skip-performance  Skip performance tests"
            echo "  --coverage-only     Only run tests with coverage reporting"
            echo "  --verbose           Enable verbose output"
            echo "  --parallel          Run tests in parallel where possible"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists node; then
    print_error "Node.js is not installed"
    exit 1
fi

if ! command_exists python3; then
    print_error "Python 3 is not installed"
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed"
    exit 1
fi

if ! command_exists pip; then
    print_error "pip is not installed"
    exit 1
fi

print_success "Prerequisites check passed"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Initialize test results
BACKEND_TESTS_PASSED=false
FRONTEND_TESTS_PASSED=false
SHARED_TESTS_PASSED=false
E2E_TESTS_PASSED=false
ACCESSIBILITY_TESTS_PASSED=false
PERFORMANCE_TESTS_PASSED=false

# Create reports directory
mkdir -p reports

print_status "Starting comprehensive test suite..."

# 1. Backend Tests
print_status "=== Backend Tests ==="
cd "$PROJECT_ROOT/apps/api"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt >/dev/null 2>&1

if [ "$COVERAGE_ONLY" = true ]; then
    if run_test "Backend Unit Tests with Coverage" "pytest --cov=src --cov-report=xml --cov-report=html --cov-report=term" ""; then
        BACKEND_TESTS_PASSED=true
        cp coverage.xml "$PROJECT_ROOT/reports/backend-coverage.xml"
        cp -r htmlcov "$PROJECT_ROOT/reports/backend-coverage-html"
    fi
else
    if [ "$PARALLEL" = true ]; then
        if run_test "Backend Unit Tests (Parallel)" "pytest -n auto" ""; then
            BACKEND_TESTS_PASSED=true
        fi
    else
        if run_test "Backend Unit Tests" "pytest" ""; then
            BACKEND_TESTS_PASSED=true
        fi
    fi
fi

deactivate

# 2. Shared Package Tests
print_status "=== Shared Package Tests ==="
cd "$PROJECT_ROOT/packages/shared"

npm ci >/dev/null 2>&1
if run_test "Shared Package Tests" "npm test" ""; then
    SHARED_TESTS_PASSED=true
fi

# 3. Frontend Tests
print_status "=== Frontend Tests ==="
cd "$PROJECT_ROOT/apps/web"

npm ci >/dev/null 2>&1

if [ "$COVERAGE_ONLY" = true ]; then
    if run_test "Frontend Unit Tests with Coverage" "npm run test:coverage" ""; then
        FRONTEND_TESTS_PASSED=true
        cp -r coverage "$PROJECT_ROOT/reports/frontend-coverage"
    fi
else
    if run_test "Frontend Unit Tests" "npm test -- --watchAll=false" ""; then
        FRONTEND_TESTS_PASSED=true
    fi
fi

# 4. End-to-End Tests
if [ "$SKIP_E2E" = false ]; then
    print_status "=== End-to-End Tests ==="
    
    # Install Playwright if not already installed
    if [ ! -d "node_modules/@playwright" ]; then
        print_status "Installing Playwright..."
        npx playwright install >/dev/null 2>&1
    fi
    
    # Start backend server for E2E tests
    print_status "Starting backend server for E2E tests..."
    cd "$PROJECT_ROOT/apps/api"
    source venv/bin/activate
    
    # Start server in background
    PYTHONPATH=. uvicorn src.main:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    
    # Wait for server to start
    sleep 5
    
    # Check if server is running
    if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_warning "Backend server not responding, starting without backend"
    fi
    
    cd "$PROJECT_ROOT/apps/web"
    
    if run_test "End-to-End Tests" "npx playwright test" ""; then
        E2E_TESTS_PASSED=true
        cp -r playwright-report "$PROJECT_ROOT/reports/e2e-report" 2>/dev/null || true
    fi
    
    # Stop backend server
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    deactivate
else
    print_warning "Skipping E2E tests (--skip-e2e flag used)"
    E2E_TESTS_PASSED=true
fi

# 5. Accessibility Tests
print_status "=== Accessibility Tests ==="
cd "$PROJECT_ROOT/apps/web"

if run_test "Accessibility Tests" "npx playwright test accessibility.spec.ts" ""; then
    ACCESSIBILITY_TESTS_PASSED=true
fi

# 6. Performance Tests
if [ "$SKIP_PERFORMANCE" = false ]; then
    print_status "=== Performance Tests ==="
    cd "$PROJECT_ROOT/apps/api"
    source venv/bin/activate
    
    # Install locust if not already installed
    pip install locust >/dev/null 2>&1
    
    # Start server for performance tests
    PYTHONPATH=. uvicorn src.main:app --host 0.0.0.0 --port 8001 &
    PERF_BACKEND_PID=$!
    
    sleep 5
    
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        if run_test "Performance Tests" "locust -f tests/performance/locustfile.py --host=http://localhost:8001 --users=10 --spawn-rate=2 --run-time=30s --headless --html=performance-report.html" ""; then
            PERFORMANCE_TESTS_PASSED=true
            cp performance-report.html "$PROJECT_ROOT/reports/performance-report.html" 2>/dev/null || true
        fi
    else
        print_warning "Could not start backend for performance tests"
    fi
    
    # Stop performance test server
    if [ -n "$PERF_BACKEND_PID" ]; then
        kill $PERF_BACKEND_PID 2>/dev/null || true
    fi
    
    deactivate
else
    print_warning "Skipping performance tests (--skip-performance flag used)"
    PERFORMANCE_TESTS_PASSED=true
fi

# Generate summary report
print_status "=== Test Summary ==="

echo "Test Results:" > "$PROJECT_ROOT/reports/test-summary.txt"
echo "=============" >> "$PROJECT_ROOT/reports/test-summary.txt"
echo "" >> "$PROJECT_ROOT/reports/test-summary.txt"

# Function to add result to summary
add_result() {
    local test_name="$1"
    local passed="$2"
    
    if [ "$passed" = true ]; then
        echo "✅ $test_name: PASSED" >> "$PROJECT_ROOT/reports/test-summary.txt"
        print_success "$test_name: PASSED"
    else
        echo "❌ $test_name: FAILED" >> "$PROJECT_ROOT/reports/test-summary.txt"
        print_error "$test_name: FAILED"
    fi
}

add_result "Backend Tests" $BACKEND_TESTS_PASSED
add_result "Frontend Tests" $FRONTEND_TESTS_PASSED
add_result "Shared Package Tests" $SHARED_TESTS_PASSED
add_result "End-to-End Tests" $E2E_TESTS_PASSED
add_result "Accessibility Tests" $ACCESSIBILITY_TESTS_PASSED
add_result "Performance Tests" $PERFORMANCE_TESTS_PASSED

echo "" >> "$PROJECT_ROOT/reports/test-summary.txt"
echo "Generated: $(date)" >> "$PROJECT_ROOT/reports/test-summary.txt"

# Check overall success
if [ "$BACKEND_TESTS_PASSED" = true ] && 
   [ "$FRONTEND_TESTS_PASSED" = true ] && 
   [ "$SHARED_TESTS_PASSED" = true ] && 
   [ "$E2E_TESTS_PASSED" = true ] && 
   [ "$ACCESSIBILITY_TESTS_PASSED" = true ] && 
   [ "$PERFORMANCE_TESTS_PASSED" = true ]; then
    
    print_success "All tests passed! 🎉"
    echo "✅ ALL TESTS PASSED" >> "$PROJECT_ROOT/reports/test-summary.txt"
    exit 0
else
    print_error "Some tests failed. Check the summary above."
    echo "❌ SOME TESTS FAILED" >> "$PROJECT_ROOT/reports/test-summary.txt"
    exit 1
fi