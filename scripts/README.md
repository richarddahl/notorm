# Uno Scripts

This directory contains utility scripts for the Uno framework.

## Docker Scripts

- `setup_docker.sh` - Sets up Docker environment for development
- `setup_test_env.sh` - Sets up Docker environment for testing
- `rebuild_docker.sh` - Rebuilds Docker containers from scratch
- `install_pgvector.sh` - Installs pgvector extension locally

## Usage

All scripts are executable from the project root:

```bash
# Set up development environment
./scripts/setup_docker.sh

# Set up test environment
./scripts/setup_test_env.sh

# Rebuild Docker containers
./scripts/rebuild_docker.sh

# Install pgvector locally
./scripts/install_pgvector.sh
```

## Implementation Details

The scripts in this directory are thin wrappers around the actual implementation scripts located in the `docker/scripts/` directory. This approach allows for:

1. A consistent user interface from the project root
2. Proper organization of implementation details
3. Clear separation between user-facing scripts and internal Docker scripts