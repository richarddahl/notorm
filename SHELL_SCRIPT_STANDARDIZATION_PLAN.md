# Shell Script Standardization Plan

This document outlines the plan to standardize the shell scripts in the codebase to make them more maintainable and consistent.

## Current State

We have identified several issues with the current shell script organization:

1. **Duplication**: Scripts with similar functionality exist in multiple directories
2. **Inconsistent Location**: Scripts are scattered across the repository
3. **Proxy Pattern**: Many scripts in the root directory simply call other scripts in subdirectories
4. **Inconsistent Naming**: No standardized naming convention for scripts
5. **Mixed Responsibilities**: Docker setup, database initialization, and other operations mixed together

## Script Inventory

Current script locations:

1. Repository Root Scripts (proxy scripts):
   - `/scripts/install_pgvector.sh`
   - `/scripts/rebuild_docker.sh`
   - `/scripts/setup_docker.sh`
   - `/scripts/setup_test_env.sh`
   - `/scripts/convert_tests_to_pytest.sh` (development tool)

2. Docker Scripts:
   - `/docker/download_pgvector.sh`
   - `/docker/init-db.sh`
   - `/docker/init-extensions.sh`
   - `/docker/rebuild.sh`

3. Docker Scripts Subdirectory:
   - `/docker/scripts/download_pgvector.sh`
   - `/docker/scripts/init-db.sh`
   - `/docker/scripts/init-extensions.sh`
   - `/docker/scripts/install_pgvector.sh`
   - `/docker/scripts/rebuild.sh`
   - `/docker/scripts/setup_test_docker.sh`
   - `/docker/scripts/setup_with_docker.sh`

## Standardization Plan

### 1. Directory Structure

Create a clean, organized structure for scripts:

```
/scripts
├── docker/           # Docker-related scripts
│   ├── build.sh      # Build Docker images
│   ├── start.sh      # Start Docker containers
│   ├── stop.sh       # Stop Docker containers
│   ├── postgres/     # PostgreSQL specific scripts
│   │   ├── init.sh   # Initialize PostgreSQL
│   │   ├── backup.sh # Backup database
│   │   └── restore.sh # Restore database
│   └── test/         # Docker test environment scripts
│       └── setup.sh  # Set up test environment
├── db/               # Database scripts
│   ├── extensions/   # Database extension scripts
│   │   └── pgvector.sh # Install pgvector extension
│   └── migrations/   # Database migration scripts
├── dev/              # Development utility scripts
│   ├── lint.sh       # Run linting
│   └── test.sh       # Run tests
└── ci/               # CI/CD scripts
```

### 2. Standardized Naming

Adopt a consistent naming convention for all scripts:

- Use lowercase with hyphens for script names
- Use descriptive names that indicate purpose
- Group related scripts with common prefixes

### 3. Implementation Plan

1. **Create new structure**:
   - Set up the new directory structure
   - Create placeholder README.md files in each directory explaining its purpose

2. **Consolidate duplicates**:
   - Identify and eliminate duplicate scripts
   - Create a single canonical version of each script

3. **Standardize scripts**:
   - Add consistent headers with description, usage, and parameters
   - Add error handling and logging
   - Make scripts more robust with appropriate exit codes
   - Ensure consistent styling and formatting

4. **Replace proxy pattern**:
   - Eliminate proxy scripts by moving functionality to the main scripts
   - Use symlinks if necessary for backwards compatibility

5. **Python Conversion**:
   - Identify scripts that would benefit from being rewritten in Python
   - Create Python equivalents with improved functionality
   - Document Python alternatives for shell scripts

### 4. Script Template

Each script should follow this template:

```bash
#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: script-name.sh
# Description: Brief description of what the script does
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./script-name.sh [options]
# 
# Options:
#   -h, --help     Display this help message
#   -v, --verbose  Enable verbose output
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions if needed
source "${SCRIPT_DIR}/../common/functions.sh"

# Parse arguments
verbose=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -h, --help     Display this help message"
            echo "  -v, --verbose  Enable verbose output"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Function definitions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Main script logic
log "Starting script execution"

# ... script content ...

log "Script completed successfully"
exit 0
```

### 5. Documentation

Update documentation to reflect the new script organization:

1. Update `DOCKER_FIRST.md` to reference the new script locations
2. Update `README.md` to describe the script organization
3. Add a section to `docs/developer_guide.md` about available scripts and their usage

### 6. Migration Strategy

1. Begin by creating the new structure and placing new versions of scripts in it
2. Keep old scripts working during transition with symlinks
3. Update documentation to point to new script locations
4. Once all references to old scripts are updated, remove old scripts

### 7. Python Conversion Candidates (COMPLETED)

The following scripts have been converted to Python:

1. ✅ Database initialization (`init-db.sh`) → `src/scripts/db_init.py`
2. ✅ Test environment setup (`setup_test_docker.sh`) → `src/scripts/docker_utils.py`
3. ✅ Extension management (`init-extensions.sh`) → `src/scripts/postgres_extensions.py`
4. ✅ Docker rebuild utility (`rebuild.sh`) → `src/scripts/docker_rebuild.py`
5. ✅ Environment setup utility (`setup_with_docker.sh`) → `src/scripts/setup_environment.py`

All Python implementations include:
- Improved error handling with specific exception classes
- Command-line interfaces with argument parsing
- Type hints for better code safety
- Modular design with reusable functions
- Integration with hatch commands via `pyproject.toml`

### 8. Timeline

1. Phase 1: Create new structure and documentation (1 day)
2. Phase 2: Standardize and consolidate Docker scripts (1-2 days)
3. Phase 3: Standardize and consolidate database scripts (1-2 days)
4. Phase 4: Implement Python alternatives for key scripts (2-3 days)
5. Phase 5: Remove old scripts and update all references (1 day)

Total estimated time: 6-9 days

## Success Criteria

1. ✅ All shell scripts follow the standardized template
2. ✅ No duplicate scripts exist in the codebase
3. ✅ Scripts are organized in a logical directory structure
4. ✅ Documentation is updated to reflect the new organization
5. ✅ All scripts have proper error handling and help information
6. ✅ Complex operations are implemented in Python where appropriate

## Completion Status

The shell script standardization plan has been successfully implemented:

1. ✅ Created standardized directory structure for shell scripts
2. ✅ Implemented common functions library
3. ✅ Converted complex shell scripts to Python
4. ✅ Updated hatch configuration to use Python implementations
5. ✅ Removed old shell scripts and eliminated duplicates
6. ✅ Ensured all scripts have proper error handling and documentation

Next steps are focused on enhancing the Python utilities with:
- Unit tests for the Python implementations
- Comprehensive documentation
- Logging configuration
- Enhanced error handling and reporting