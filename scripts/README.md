# Uno Scripts

This directory contains scripts used for development, deployment, and maintenance of the Uno application.

> **Note:** We are currently reorganizing these scripts. If you're looking for the original scripts, they're still available but will be migrated to the new structure soon.

## Directory Structure

- `docker/`: Scripts for Docker container management
  - `postgres/`: PostgreSQL specific Docker scripts
  - `test/`: Docker test environment scripts
- `db/`: Database management scripts
  - `extensions/`: Database extension installation scripts
  - `migrations/`: Database migration scripts
- `dev/`: Development utility scripts
- `ci/`: Continuous Integration scripts
- `common/`: Common functions and utilities used by other scripts

## Legacy Scripts

These scripts are being migrated to the new structure:

- `setup_docker.sh` - Sets up Docker environment for development
- `setup_test_env.sh` - Sets up Docker environment for testing
- `rebuild_docker.sh` - Rebuilds Docker containers from scratch
- `install_pgvector.sh` - Installs pgvector extension locally

## Usage

All scripts should include help information. Run any script with `-h` or `--help` to see usage instructions:

```
./scripts/script-name.sh --help
```

## Naming Convention

Scripts follow these naming conventions:
- Use lowercase with hyphens for script names
- Use descriptive names that indicate purpose
- Group related scripts with common prefixes

## Common Functions

Scripts can import common functions from `scripts/common/functions.sh`.