# CI/CD Scripts

This directory contains scripts used for Continuous Integration and Continuous Deployment (CI/CD) workflows.

## Scripts

- `deploy.sh` - Handles deployment of the application to various environments
- `build.sh` - Builds the application and container images
- `test.sh` - Runs tests in CI environment
- `verify.sh` - Verifies deployment health

## Usage

The scripts in this directory are primarily intended to be used by CI/CD systems like GitHub Actions, GitLab CI, or Jenkins. However, they can also be used locally for testing the CI/CD workflow.

Example:

```bash
# Build the application
./scripts/ci/build.sh

# Run tests
./scripts/ci/test.sh

# Deploy to development environment
./scripts/ci/deploy.sh --env dev
```

## Common Parameters

Most scripts support the following parameters:

- `-h, --help` - Show help message
- `-v, --verbose` - Enable verbose output
- `-e, --env ENV` - Specify environment (dev, test, staging, prod)

See individual script documentation for script-specific parameters.

## Environment Variables

The CI scripts may use the following environment variables:

- `CI_ENVIRONMENT` - The environment to deploy to (dev, test, staging, prod)
- `CI_REGISTRY` - Docker registry URL
- `CI_REGISTRY_USER` - Docker registry username
- `CI_REGISTRY_PASSWORD` - Docker registry password
- `KUBE_CONFIG` - Kubernetes configuration for deployments
