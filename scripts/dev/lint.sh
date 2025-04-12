#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: lint.sh
# Description: Run linting tools on codebase
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./lint.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -f, --fix        Automatically fix issues where possible
#   -p, --path PATH  Path to lint (default: src)
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false
fix=false
path="src"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Run linting tools on codebase" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output
  -f, --fix        Automatically fix issues where possible
  -p, --path PATH  Path to lint (default: src)"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -f|--fix)
            fix=true
            shift
            ;;
        -p|--path)
            path="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Main script logic
log_section "Linting Python code"

# Check if required tools are installed
check_command "ruff" "Ruff linter is required. Install with: pip install ruff"
check_command "mypy" "MyPy type checker is required. Install with: pip install mypy"

# Set up arguments
ruff_args=("check" "$path")
mypy_args=("$path")

if [[ "$fix" == true ]]; then
    log_info "Running in fix mode"
    ruff_args=("check" "--fix" "$path")
fi

if [[ "$verbose" == true ]]; then
    log_info "Running in verbose mode"
    ruff_args+=("--verbose")
    mypy_args+=("--verbose")
fi

# Run Ruff linter
log_info "Running Ruff linter..."
cd "$PROJECT_ROOT"

if ! python -m ruff "${ruff_args[@]}"; then
    if [[ "$fix" == true ]]; then
        log_warning "Ruff found issues and attempted to fix them automatically."
    else
        log_error "Ruff found issues. Run with --fix to attempt automatic fixes."
        log_info "For detailed information, run with --verbose"
    fi
    has_errors=true
else
    log_success "Ruff found no issues."
fi

# Run MyPy type checking
log_info "Running MyPy type checker..."
cd "$PROJECT_ROOT"

if ! python -m mypy "${mypy_args[@]}"; then
    log_error "MyPy found type issues."
    log_info "For detailed information, run with --verbose"
    has_errors=true
else
    log_success "MyPy found no type issues."
fi

# Check for other quality issues
log_info "Checking for other code quality issues..."

# Check for print statements
print_statements=$(grep -r "print(" --include="*.py" "$path" | grep -v "# noqa" | wc -l)
if [[ $print_statements -gt 0 ]]; then
    log_warning "Found $print_statements print() statements in the codebase."
    log_info "Consider using proper logging instead."
    
    if [[ "$verbose" == true ]]; then
        log_info "Print statements found in:"
        grep -r "print(" --include="*.py" "$path" | grep -v "# noqa"
    fi
fi

# Check for TODO items
todo_items=$(grep -r "TODO" --include="*.py" "$path" | wc -l)
if [[ $todo_items -gt 0 ]]; then
    log_warning "Found $todo_items TODO items in the codebase."
    
    if [[ "$verbose" == true ]]; then
        log_info "TODO items found in:"
        grep -r "TODO" --include="*.py" "$path"
    fi
fi

# Summary
log_section "Linting Summary"

if [[ "$has_errors" == true ]]; then
    log_error "Linting found issues that need to be fixed."
    exit 1
else
    log_success "Linting completed successfully!"
    
    if [[ $print_statements -gt 0 || $todo_items -gt 0 ]]; then
        log_warning "Some minor issues were found (print statements, TODOs)."
    fi
    
    log_info "Code quality looks good!"
fi

exit 0