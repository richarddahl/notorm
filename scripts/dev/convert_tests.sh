#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: convert_tests.sh
# Description: Convert unittest-style tests to pytest style
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./convert_tests.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -f, --force      Force conversion even if target files exist
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false
force_conversion=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Convert unittest-style tests to pytest style" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output
  -f, --force      Force conversion even if target files exist"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -f|--force)
            force_conversion=true
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
log_section "Converting unittest tests to pytest"

# Create destination directory if it doesn't exist
mkdir -p "${PROJECT_ROOT}/tests/unit/database"

# Check for conftest.py
if [ ! -f "${PROJECT_ROOT}/tests/unit/database/conftest.py" ]; then
    log_error "conftest.py not found in tests/unit/database/. Create it first."
    exit 1
fi

# Copy the example test file we created if it doesn't exist
if [ -f "${PROJECT_ROOT}/tests/unit/database/test_db_merge.py" ] && [ "$force_conversion" != true ]; then
    log_info "File test_db_merge.py already exists in target directory. Skipping."
else
    if [ -f "${PROJECT_ROOT}/tests/unit_unittest/database/test_db_merge.py.new" ]; then
        cp "${PROJECT_ROOT}/tests/unit_unittest/database/test_db_merge.py.new" \
           "${PROJECT_ROOT}/tests/unit/database/test_db_merge.py"
        log_success "Copied test_db_merge.py to target directory."
    else
        log_warning "Could not find source file tests/unit_unittest/database/test_db_merge.py.new"
    fi
fi

# List all unittest-style test files to convert
UNITTEST_FILES=(
    "test_db_basic.py"
    "test_db_create.py"
    "test_db_filter.py"
    "test_db_get.py"
    "test_session_async.py"
    "test_session_mock.py"
)

# Echo conversion instructions
log_section "Conversion Instructions"

for file in "${UNITTEST_FILES[@]}"; do
    if [ "$file" == "test_db_merge.py" ]; then
        continue  # Skip the file we may have already converted
    fi
    
    log_info "Converting $file from unittest to pytest style:"
    echo "   - Replace 'unittest.IsolatedAsyncioTestCase' with '@pytest.mark.asyncio' decorator"
    echo "   - Convert 'setUp' method to pytest fixtures"
    echo "   - Replace assertion methods with pytest assertions"
    echo "   - Change class-based tests to function-based tests"
    echo "   - Use fixtures instead of self attributes"
    echo ""
    
    # Attempt auto-conversion if requested and source file exists
    source_file="${PROJECT_ROOT}/tests/unit_unittest/database/${file}"
    target_file="${PROJECT_ROOT}/tests/unit/database/${file}"
    
    if [ -f "$source_file" ]; then
        if [ -f "$target_file" ] && [ "$force_conversion" != true ]; then
            log_warning "Target file $target_file already exists. Use --force to overwrite."
        else
            log_info "Performing basic conversion for $file..."
            
            # Basic conversion using sed - this is a starting point,
            # manual editing will still be required
            cat "$source_file" | \
                sed 's/import unittest/import pytest/' | \
                sed 's/class Test\([a-zA-Z0-9]*\)(unittest.TestCase)/# Test\1/' | \
                sed 's/class Test\([a-zA-Z0-9]*\)(unittest.IsolatedAsyncioTestCase)/# Test\1/' | \
                sed 's/    def test_\([a-zA-Z0-9_]*\)(self)/\n@pytest.mark.asyncio\nasync def test_\1():/' | \
                sed 's/    def setUp(self):/\n@pytest.fixture\ndef test_setup():/' | \
                sed 's/        self.assertEqual(\(.*\), \(.*\))/    assert \1 == \2/' | \
                sed 's/        self.assertTrue(\(.*\))/    assert \1/' | \
                sed 's/        self.assertFalse(\(.*\))/    assert not \1/' | \
                sed 's/        self.assertIs(\(.*\), \(.*\))/    assert \1 is \2/' | \
                sed 's/        self.assertIsNot(\(.*\), \(.*\))/    assert \1 is not \2/' | \
                sed 's/        self.assertIn(\(.*\), \(.*\))/    assert \1 in \2/' | \
                sed 's/        self.assertNotIn(\(.*\), \(.*\))/    assert \1 not in \2/' | \
                sed 's/        self.assertIsInstance(\(.*\), \(.*\))/    assert isinstance(\1, \2)/' > "$target_file"
                
            log_info "Generated $target_file (requires manual editing)"
        fi
    else
        log_warning "Source file $source_file not found."
    fi
    
    echo "--------------------------------------------------------"
done

log_section "Next Steps"
log_info "1. Review and edit the converted files as needed"
log_info "2. Run tests to verify conversion:"
log_info "   python -m pytest tests/unit/database/ -v"
log_info ""
log_info "If all tests pass, you can delete the unittest-style files:"
log_info "rm -rf tests/unit_unittest"

exit 0