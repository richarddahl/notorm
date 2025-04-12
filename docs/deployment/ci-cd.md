# CI/CD Integration

The Uno Deployment Pipeline provides templates and utilities for integrating with various CI/CD platforms. This document describes the supported platforms and how to use them effectively.

## GitHub Actions

The pipeline includes a GitHub Actions workflow template for building, testing, and deploying Uno applications.

### Workflow Features

- **Triggered by**: Pushes to main branch, pull requests to main branch, or manual dispatch
- **Environment Support**: Dev, test, staging, production environments
- **Testing**: Unit tests, integration tests, coverage reporting
- **Security**: Security scanning with Bandit and Safety
- **Docker**: Building and pushing Docker images to GitHub Container Registry
- **Deployment**: Deploying to different environments

### Example Workflow

The workflow template is located at `src/uno/deployment/templates/github_actions.yml`. Here's an overview of the key components:

```yaml
name: Uno CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - test
          - staging
          - production

jobs:
  build-and-test:
    # Build and run tests
    ...

  security-scan:
    # Run security scans
    ...

  build-docker:
    # Build and push Docker image
    ...

  deploy:
    # Deploy to environment
    ...
```

### Usage

1. Copy the workflow template to your repository's `.github/workflows` directory:

```bash
mkdir -p .github/workflows
cp src/uno/deployment/templates/github_actions.yml .github/workflows/uno-ci-cd.yml
```

2. Customize the workflow as needed:
   - Adjust environment variables
   - Configure deployment options
   - Add or remove specific jobs or steps

3. Push the workflow to your repository.

4. Trigger the workflow:
   - Automatically: Push to main branch or open a pull request
   - Manually: Use the "Run workflow" button in the GitHub Actions UI

### Environment Secrets

The workflow requires the following GitHub Secrets:

- `GITHUB_TOKEN`: Automatically provided by GitHub
- `KUBECONFIG`: Base64-encoded Kubernetes configuration (for Kubernetes deployments)
- `DB_PASSWORD`: Database password for deployment environments

## GitLab CI

The pipeline also supports GitLab CI/CD with a template for building, testing, and deploying Uno applications.

### Pipeline Features

- **Stages**: Build, test, scan, deploy
- **Environment Support**: Dev, test, staging, production environments
- **Testing**: Unit tests, integration tests, coverage reporting
- **Security**: Security scanning with Bandit and Safety
- **Docker**: Building and pushing Docker images to GitLab Container Registry
- **Deployment**: Deploying to different environments

### Template Location

The GitLab CI template is available at `src/uno/deployment/templates/gitlab_ci.yml`.

## Jenkins

For organizations using Jenkins, the pipeline includes a Jenkinsfile template for creating a CI/CD pipeline.

### Pipeline Features

- **Stages**: Checkout, build, test, security, deploy
- **Environment Support**: Dev, test, staging, production environments
- **Testing**: Unit tests, integration tests, coverage reporting
- **Security**: Security scanning with Bandit and Safety
- **Docker**: Building and pushing Docker images
- **Deployment**: Deploying to different environments

### Template Location

The Jenkins pipeline template is available at `src/uno/deployment/templates/Jenkinsfile`.

## CircleCI

The pipeline also includes a CircleCI configuration template for organizations using CircleCI.

### Configuration Features

- **Jobs**: Build, test, security, deploy
- **Workflows**: Build-test-deploy for different environments
- **Environment Support**: Dev, test, staging, production environments
- **Testing**: Unit tests, integration tests, coverage reporting
- **Security**: Security scanning with Bandit and Safety
- **Docker**: Building and pushing Docker images
- **Deployment**: Deploying to different environments

### Template Location

The CircleCI configuration template is available at `src/uno/deployment/templates/circle_ci.yml`.

## Custom CI/CD Integration

For custom CI/CD platforms, you can use the Uno deployment scripts directly:

```bash
# Install the package
pip install -e .

# Run deployment
python -m uno.deployment.scripts.deploy \
  --app-name my-app \
  --environment prod \
  --platform kubernetes \
  --config-file ./deployment/config.yaml
```

## Best Practices

### Environment Isolation

Use different environments (dev, test, staging, production) to isolate deployments:

```yaml
deployment:
  dev:
    url: https://dev.example.com
    replicas: 1
  test:
    url: https://test.example.com
    replicas: 1
  staging:
    url: https://staging.example.com
    replicas: 2
  production:
    url: https://example.com
    replicas: 3
```

### Branch Strategy

A typical branch strategy with CI/CD integration:

- **Feature Branches**: Deploy to dev environment
- **Development Branch**: Deploy to test environment
- **Release Branches**: Deploy to staging environment
- **Main Branch**: Deploy to production environment

### Automated Testing

Include comprehensive testing in your CI/CD pipeline:

1. **Unit Tests**: Fast tests that verify individual components
2. **Integration Tests**: Tests that verify interactions between components
3. **Security Tests**: Scan code and dependencies for vulnerabilities
4. **Performance Tests**: Verify application performance under load

### Deployment Approval

For production deployments, consider adding an approval step:

```yaml
deploy-production:
  stage: deploy
  environment: production
  when: manual  # Requires manual approval
  only:
    - main
```

### Rollback Strategy

Implement a rollback strategy in case of deployment failures:

1. **Automatic Rollback**: Automatically rollback if health checks fail
2. **Manual Rollback**: Provide a manual rollback option for quick recovery
3. **Version Rollback**: Ability to deploy a specific previous version

Example rollback command:

```bash
python -m uno.deployment.scripts.deploy \
  --app-name my-app \
  --environment prod \
  --platform kubernetes \
  --image-tag v1.0.0 \  # Previous version
  --config-file ./deployment/config.yaml
```