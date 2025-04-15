# uno Python Scripts

This directory contains Python scripts for managing and working with uno. These scripts handle tasks like database operations, validation, CLI interfaces, and development utilities.

## Table of Contents
- [Database Management](#database-management)
- [Testing and Validation](#testing-and-validation)
- [CLI Tools](#cli-tools)
- [Environment Setup](#environment-setup)
- [Development Utilities](#development-utilities)
- [Documentation](#documentation)
- [Known Issues](#known-issues)
- [Usage Examples](#usage-examples)

## Database Management

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `createdb.py` | Creates database with proper roles, schemas, and extensions | `python src/scripts/createdb.py` | Requires PostgreSQL running |
| `dropdb.py` | Drops database | `python src/scripts/dropdb.py` | Use with caution |
| `db_init.py` | Initializes database structures | `python src/scripts/db_init.py` | |
| `createsuperuser.py` | Creates superuser account | `python src/scripts/createsuperuser.py` | |
| `postgres_extensions.py` | Sets up PostgreSQL extensions | `python src/scripts/postgres_extensions.py` | |
| `eventstore.py` | Creates/manages event store | `python src/scripts/eventstore.py [command]` | Commands: create, purge, reset |
| `createquerypaths.py` | Sets up query paths for GraphQL | `python src/scripts/createquerypaths.py` | |

## Testing and Validation

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `validate_protocols.py` | Validates protocol implementations | `python src/scripts/validate_protocols.py` | |
| `validate_protocols_patched.py` | Validates protocol implementations with patches | `python src/scripts/validate_protocols_patched.py` | |
| `validate_errors.py` | Validates error handling | `python src/scripts/validate_errors.py` | |
| `validate_reports.py` | Validates report generation | `python src/scripts/validate_reports.py` | |
| `validate_workflows.py` | Validates workflow definitions | `python src/scripts/validate_workflows.py` | |
| `validate_clean_slate.py` | Validates clean state startup | `python src/scripts/validate_clean_slate.py` | |
| `validate_specific.py` | Validates specific components | `python src/scripts/validate_specific.py [component]` | |
| `test_merge_function.py` | Tests merge function | `python src/scripts/test_merge_function.py` | |

## CLI Tools

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `attributes_cli.py` | CLI for managing attributes | `python src/scripts/attributes_cli.py [command]` | |
| `values_cli.py` | CLI for managing values | `python src/scripts/values_cli.py [command]` | |
| `reports_cli.py` | CLI for managing reports | `python src/scripts/reports_cli.py [command]` | |

## Environment Setup

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `setup_environment.py` | Sets up development environment | `python src/scripts/setup_environment.py [options]` | |
| `docker_utils.py` | Utilities for Docker interactions | Not meant to be run directly | |
| `docker_rebuild.py` | Rebuilds Docker containers | `python src/scripts/docker_rebuild.py` | |

## Development Utilities

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `vector_demo.py` | Demonstrates vector search capabilities | `python src/scripts/vector_demo.py` | |
| `generate_docs.py` | Generates documentation | `python src/scripts/generate_docs.py [options]` | Has dependency issues |

## Known Issues

- `generate_docs.py` has dependency issues with missing module imports
- Some scripts assume the database is already set up and running
- Scripts may require specific environment variables to be set
- Error handling could be improved in some scripts
- Some scripts require Docker to be running

## Usage Examples

### Setting up a new development environment

```bash
# Set up Docker environment
cd /path/to/project/root
./scripts/docker/start.sh

# Initialize database
python src/scripts/createdb.py
python src/scripts/createsuperuser.py

# Validate setup
python src/scripts/validate_clean_slate.py
```

### Running vector search demo

```bash
# Ensure vector extensions are set up
./scripts/db/extensions/pgvector.sh

# Run the demo
python src/scripts/vector_demo.py
```

### Generating documentation (when fixed)

```bash
python src/scripts/generate_docs.py --output docs/api --formats markdown openapi
```

## Adding New Scripts

When adding new scripts:

1. Follow Python best practices and PEP 8 guidelines
2. Include comprehensive docstrings
3. Add type hints for all functions and variables
4. Document script in this README
5. Add appropriate error handling
6. Include help text accessible via --help flag
7. Follow existing naming conventions