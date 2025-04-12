#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: stop.sh
# Description: Stop Docker containers for Uno development
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./stop.sh [options]
# 
# Options:
#   -h, --help     Display this help message
#   -v, --verbose  Enable verbose output
#   -r, --remove   Remove containers after stopping them
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false
remove=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Stop Docker containers for Uno development" "  -h, --help     Display this help message
  -v, --verbose  Enable verbose output
  -r, --remove   Remove containers after stopping them"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -r|--remove)
            remove=true
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
log_section "Stopping Uno Development Environment"

# Check if Docker is running
if ! docker_is_running; then
    exit 1
fi

# Change to docker directory
cd "$PROJECT_ROOT/docker"

# Stop containers
if $remove; then
    log_info "Stopping and removing containers..."
    docker-compose down
else
    log_info "Stopping containers..."
    docker-compose stop
fi

log_success "Docker environment stopped successfully!"
exit 0