#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: verify.sh
# Description: Verify deployed application health
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./verify.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -e, --env ENV    Specify environment (dev, test, staging, prod)
#   -u, --url URL    Specify base URL to check (default: auto-detect)
#   -t, --timeout SEC Timeout in seconds for health checks (default: 60)
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false
environment="dev"
base_url=""
timeout=60

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Verify deployed application health" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output
  -e, --env ENV    Specify environment (dev, test, staging, prod)
  -u, --url URL    Specify base URL to check (default: auto-detect)
  -t, --timeout SEC Timeout in seconds for health checks (default: 60)"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -e|--env)
            environment="$2"
            shift 2
            ;;
        -u|--url)
            base_url="$2"
            shift 2
            ;;
        -t|--timeout)
            timeout="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$environment" != "dev" && "$environment" != "test" && "$environment" != "staging" && "$environment" != "prod" ]]; then
    log_error "Invalid environment: $environment. Must be one of: dev, test, staging, prod"
    exit 1
fi

# Main script logic
log_section "Verifying $environment deployment"

# Determine base URL if not provided
if [[ -z "$base_url" ]]; then
    case "$environment" in
        dev)
            base_url="http://localhost:8000"
            ;;
        test)
            base_url="http://localhost:8001"
            ;;
        staging)
            base_url="https://staging.example.com"
            ;;
        prod)
            base_url="https://example.com"
            ;;
    esac
    log_info "Using auto-detected base URL: $base_url"
fi

# Check if curl is available
if ! command -v curl &> /dev/null; then
    log_error "curl is required for health checks but is not installed."
    exit 1
fi

# Function to check endpoint
check_endpoint() {
    local endpoint="$1"
    local expected_status="${2:-200}"
    local description="${3:-Endpoint check}"
    local url="${base_url}${endpoint}"
    
    log_info "Checking ${description}: ${url}"
    
    local start_time=$(date +%s)
    local max_time=$((start_time + timeout))
    
    while [[ $(date +%s) -lt $max_time ]]; do
        if [[ "$verbose" == true ]]; then
            response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
        else
            response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        fi
        
        if [[ "$response" == "$expected_status" ]]; then
            log_success "${description} is healthy (${response})"
            return 0
        fi
        
        log_warning "${description} returned ${response}, expected ${expected_status}. Retrying..."
        sleep 5
    done
    
    log_error "${description} failed after ${timeout} seconds. Last status: ${response}"
    return 1
}

# Run various health checks
errors=0

# Check main API health endpoint
if ! check_endpoint "/api/health" 200 "API Health"; then
    errors=$((errors+1))
fi

# Check docs endpoint
if ! check_endpoint "/docs" 200 "API Documentation"; then
    errors=$((errors+1))
fi

# Check database status via API
if ! check_endpoint "/api/health/db" 200 "Database Health"; then
    errors=$((errors+1))
fi

# Additional checks for staging/prod
if [[ "$environment" == "staging" || "$environment" == "prod" ]]; then
    # Check metrics endpoint
    if ! check_endpoint "/metrics" 200 "Metrics"; then
        errors=$((errors+1))
    fi
    
    # Check that robots.txt exists
    if ! check_endpoint "/robots.txt" 200 "Robots.txt"; then
        errors=$((errors+1))
    fi
fi

# Generate detailed report if verbose
if [[ "$verbose" == true ]]; then
    log_info "Generating detailed health report..."
    
    # Get health JSON for more details
    health_json=$(curl -s "${base_url}/api/health")
    echo "$health_json" | python -m json.tool
    
    # Check response times
    response_time=$(curl -s -w "%{time_total}" -o /dev/null "${base_url}/api/health")
    log_info "API Health response time: ${response_time} seconds"
    
    # Check resource usage if in local environment
    if [[ "$environment" == "dev" || "$environment" == "test" ]]; then
        if docker_container_running "pg16_uno"; then
            log_info "PostgreSQL container stats:"
            docker stats --no-stream pg16_uno
        fi
    fi
fi

# Final verification result
if [[ $errors -eq 0 ]]; then
    log_section "Verification Result: SUCCESS"
    log_success "All checks passed. The application is healthy."
    exit 0
else
    log_section "Verification Result: FAILURE"
    log_error "${errors} checks failed. Application health verification failed."
    exit 1
fi