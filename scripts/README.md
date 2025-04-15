# uno Scripts

This directory contains scripts used for development, deployment, and maintenance of the uno application.

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

## Script Categories

### Docker Scripts

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `docker/start.sh` | Starts Docker containers for development | `./scripts/docker/start.sh [options]` | Options: `-v` (verbose), `-c` (clean), `-d` (detached) |
| `docker/stop.sh` | Stops Docker containers | `./scripts/docker/stop.sh` | |
| `docker/test/setup.sh` | Sets up test Docker environment | `./scripts/docker/test/setup.sh` | |

### Development Scripts

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `dev/lint.sh` | Runs linting checks | `./scripts/dev/lint.sh` | |
| `dev/modeler.sh` | Launches the visual data modeler | `./scripts/dev/modeler.sh` | Requires virtual environment setup |
| `dev/convert_tests.sh` | Converts unittest tests to pytest | `./scripts/dev/convert_tests.sh` | Provides automated conversion |

### Database Scripts

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `db/extensions/pgvector.sh` | Sets up pgvector extension | `./scripts/db/extensions/pgvector.sh` | |
| `install_pgvector.sh` | Installs pgvector extension | `./scripts/install_pgvector.sh` | |

### CI/CD Scripts

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `ci/build.sh` | Builds the project for CI | `./scripts/ci/build.sh` | |
| `ci/test.sh` | Runs tests for CI | `./scripts/ci/test.sh` | |
| `ci/deploy.sh` | Deploys the project | `./scripts/ci/deploy.sh` | |
| `ci/verify.sh` | Verifies deployment | `./scripts/ci/verify.sh` | |
| `ci/benchmark_dashboard.sh` | Sets up benchmark dashboard | `./scripts/ci/benchmark_dashboard.sh` | |

### Benchmark Scripts

| Script | Purpose | Usage | Notes |
|--------|---------|-------|-------|
| `benchmarks/run_vector_benchmarks.sh` | Runs vector search benchmarks | `./scripts/benchmarks/run_vector_benchmarks.sh` | |

## Legacy Scripts

These scripts are being migrated to the new structure:

| Script | Purpose | Replacement | Notes |
|--------|---------|-------------|-------|
| `setup_docker.sh` | Sets up Docker environment for development | `docker/start.sh` | This script now redirects to the new location |
| `setup_test_env.sh` | Sets up Docker environment for testing | `docker/test/setup.sh` | This script now redirects to the new location |
| `rebuild_docker.sh` | Rebuilds Docker containers from scratch | `ci/build.sh` | This script now redirects to the new location |
| `install_pgvector.sh` | Installs pgvector extension locally | `db/extensions/pgvector.sh` | This script now redirects to the new location |
| `launch_modeler.sh` | Launches the visual data modeler | `dev/modeler.sh` | This script now redirects to the new location |
| `convert_tests_to_pytest.sh` | Converts unittest tests to pytest | `dev/convert_tests.sh` | This script now redirects to the new location |
| `setup-test.sh` | (Does not exist - mentioned in docs) | `setup_test_env.sh` | |

## Python Scripts

Python scripts are located in the `src/scripts/` directory and include tools for:
- Database management (createdb.py, dropdb.py)
- User management (createsuperuser.py)
- Environment setup (setup_environment.py)
- Testing and validation (validate_*.py)
- CLI tools (attributes_cli.py, reports_cli.py, values_cli.py)

## Usage

All scripts should include help information. Run any script with `-h` or `--help` to see usage instructions:

```
./scripts/script-name.sh --help
```

## Known Issues

- Some scripts are marked as legacy and redirect to newer versions
- Docker scripts assume Docker is installed and running
- Database scripts assume PostgreSQL is running in Docker
- Vector search scripts assume pgvector extension is installed
- Some scripts may have dependency issues in certain environments

## Naming Convention

Scripts follow these naming conventions:
- Use lowercase with hyphens for script names
- Use descriptive names that indicate purpose
- Group related scripts with common prefixes

## Common Functions

Scripts can import common functions from `scripts/common/functions.sh`.