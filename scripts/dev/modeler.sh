#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: modeler.sh
# Description: Launch the Uno visual data modeler
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./modeler.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Launch the Uno visual data modeler" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        *)
            # Pass remaining arguments to the modeler
            break
            ;;
    esac
done

# Main script logic
log_section "Launching Uno Data Modeler"

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "${PROJECT_ROOT}/venv" ]; then
        log_info "Activating virtual environment..."
        source "${PROJECT_ROOT}/venv/bin/activate"
    else
        log_warning "No virtual environment found at ${PROJECT_ROOT}/venv"
        log_info "Dependencies may be missing."
        
        # Check if hatch is available
        if command -v hatch &> /dev/null; then
            log_info "Hatch found, using it to run modeler..."
            cd "${PROJECT_ROOT}"
            hatch run dev:modeler "$@"
            exit $?
        fi
    fi
fi

# Launch the modeler
log_info "Starting modeler..."
cd "${PROJECT_ROOT}"

if $verbose; then
    python -m uno.devtools.cli.main modeler start "$@"
else
    python -m uno.devtools.cli.main modeler start "$@" 2>/dev/null
fi

log_success "Modeler started successfully"
exit 0