#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: start.sh
# Description: Start Docker containers for Uno development
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./start.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -c, --clean      Remove existing PostgreSQL data volumes before starting
#   -d, --detached   Run containers in detached mode (background)
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false
clean_data=false
detached=true
container_name="pg16_uno"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Start Docker containers for Uno development" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output
  -c, --clean      Remove existing PostgreSQL data volumes before starting
  -d, --detached   Run containers in detached mode (background)"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -c|--clean)
            clean_data=true
            shift
            ;;
        -d|--detached)
            detached=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Main script logic
log_section "Starting Uno Development Environment"

# Check if Docker is running
if ! docker_is_running; then
    exit 1
fi

# Change to docker directory
cd "$PROJECT_ROOT/docker"

# First ensure any existing containers are stopped
log_info "Stopping any existing containers..."
docker-compose down 2>/dev/null || true

# Check if we should clean data
if $clean_data; then
    log_info "Cleaning PostgreSQL data volumes..."
    docker-compose down -v
    log_success "Data volumes cleared."
elif confirm "Do you want to clear existing PostgreSQL data?" "n"; then
    log_info "Cleaning PostgreSQL data volumes..."
    docker-compose down -v
    log_success "Data volumes cleared."
fi

# Build and start the containers
log_info "Building Docker image..."
docker-compose build

log_info "Starting containers..."
if $detached; then
    docker-compose up -d
else
    docker-compose up
fi

# Wait for PostgreSQL to start properly
if $detached; then
    log_info "Waiting for PostgreSQL to be ready..."
    if ! docker_wait_for_postgres "$container_name" 15; then
        exit 1
    fi
    
    log_section "Environment Ready"
    log_info "PostgreSQL is now running in Docker"
    log_info "  Host: localhost"
    log_info "  Port: 5432"
    log_info "  Database: uno_dev"
    log_info "  User: postgres"
    log_info "  Password: postgreSQLR0ck%"
fi

log_success "Docker environment started successfully!"
exit 0