#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: test.sh
# Description: Run tests in CI environment
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./test.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -t, --type TYPE  Test type (unit, integration, all) (default: all)
#   -c, --coverage   Generate test coverage report
#   -x, --xml        Generate JUnit XML report for CI systems
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false
test_type="all"
coverage=false
xml_report=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Run tests in CI environment" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output
  -t, --type TYPE  Test type (unit, integration, all) (default: all)
  -c, --coverage   Generate test coverage report
  -x, --xml        Generate JUnit XML report for CI systems"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -t|--type)
            test_type="$2"
            shift 2
            ;;
        -c|--coverage)
            coverage=true
            shift
            ;;
        -x|--xml)
            xml_report=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Validate test type
if [[ "$test_type" != "unit" && "$test_type" != "integration" && "$test_type" != "all" ]]; then
    log_error "Invalid test type: $test_type. Must be one of: unit, integration, all"
    exit 1
fi

# Main script logic
log_section "Running $test_type tests"

# Set up test environment
export ENV=test

# Ensure test database is available
if [[ "$test_type" == "integration" || "$test_type" == "all" ]]; then
    log_info "Setting up test database..."
    "${PROJECT_ROOT}/scripts/docker/test/setup.sh"
    docker_wait_for_postgres "pg16_uno" 30
fi

# Build pytest arguments
pytest_args=()

# Add verbosity
if [[ "$verbose" == true ]]; then
    pytest_args+=("-v")
fi

# Add coverage
if [[ "$coverage" == true ]]; then
    pytest_args+=("--cov=src/uno")
    pytest_args+=("--cov-report=term")
    pytest_args+=("--cov-report=html:coverage_report")
fi

# Add XML report
if [[ "$xml_report" == true ]]; then
    pytest_args+=("--junitxml=test-results.xml")
fi

# Run tests based on type
case "$test_type" in
    unit)
        log_info "Running unit tests..."
        
        # Run the tests
        cd "$PROJECT_ROOT"
        python -m pytest tests/unit/ "${pytest_args[@]}"
        ;;
    integration)
        log_info "Running integration tests..."
        
        # Run the tests
        cd "$PROJECT_ROOT"
        python -m pytest tests/integration/ "${pytest_args[@]}" --run-integration
        ;;
    all)
        log_info "Running all tests..."
        
        # Run the tests
        cd "$PROJECT_ROOT"
        python -m pytest "${pytest_args[@]}" --run-integration
        ;;
esac

# Run vector tests if pgvector is available
if docker exec pg16_uno psql -U postgres -d uno_test -c "SELECT 1 FROM pg_extension WHERE extname = 'vector'" -t | grep -q 1; then
    log_info "Running vector search tests..."
    cd "$PROJECT_ROOT"
    python -m pytest tests/unit/domain/vector/ "${pytest_args[@]}" --run-pgvector
    
    if [[ "$test_type" == "integration" || "$test_type" == "all" ]]; then
        python -m pytest tests/integration/test_vector_search.py "${pytest_args[@]}" --run-pgvector --run-integration
    fi
else
    log_warning "pgvector extension not found, skipping vector search tests"
fi

# Generate coverage report if requested
if [[ "$coverage" == true ]]; then
    log_info "Generating coverage report..."
    
    if command -v coverage &> /dev/null; then
        # Generate coverage badge
        coverage_percent=$(coverage report | grep TOTAL | awk '{print $NF}' | tr -d '%')
        log_info "Test coverage: ${coverage_percent}%"
        
        # Create badge file
        cat > "${PROJECT_ROOT}/coverage_badge.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="106" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="106" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h63v20H0z"/>
    <path fill="#4c1" d="M63 0h43v20H63z"/>
    <path fill="url(#b)" d="M0 0h106v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="31.5" y="15" fill="#010101" fill-opacity=".3">coverage</text>
    <text x="31.5" y="14">coverage</text>
    <text x="83.5" y="15" fill="#010101" fill-opacity=".3">${coverage_percent}%</text>
    <text x="83.5" y="14">${coverage_percent}%</text>
  </g>
</svg>
EOF
        
        log_info "Coverage badge created at ${PROJECT_ROOT}/coverage_badge.svg"
    else
        log_warning "Coverage command not found. Install 'coverage' package to generate badges."
    fi
fi

log_success "All tests completed successfully!"

log_section "Next Steps"
log_info "1. Review test results"
if [[ "$coverage" == true ]]; then
    log_info "2. Check coverage report in ./coverage_report/index.html"
fi
log_info "3. Deploy with: ./scripts/ci/deploy.sh"

exit 0