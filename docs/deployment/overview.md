# Deployment Pipeline

The uno Deployment Pipeline provides a comprehensive solution for deploying uno applications to various environments and platforms. It supports different deployment strategies, automated testing, and configuration management.

## Key Components

The deployment pipeline consists of the following key components:

1. **Deployment Configuration**: Central configuration for deployment settings, environment variables, and platform-specific options.
2. **Deployment Manager**: Core component that orchestrates the deployment process.
3. **Deployment Pipeline**: Structured pipeline with stages and tasks for executing the deployment.
4. **Deployment Strategies**: Various deployment strategies including blue-green, rolling, and canary deployments.
5. **CI/CD Templates**: Pre-configured templates for popular CI/CD platforms.

## Deployment Strategies

### Blue-Green Deployment

Blue-green deployment is a technique that reduces downtime and risk by running two identical production environments, "Blue" and "Green". At any time, only one of the environments is live, serving all production traffic. The other environment is idle.

**Key Benefits:**
- Zero downtime deployments
- Instant rollback capability
- Testing in production-like environment

**Implementation:**
1. Deploy the new version to the idle environment
2. Run tests and health checks
3. Switch traffic from the active environment to the new one
4. Keep the previous environment for rollback if needed

### Rolling Deployment

Rolling deployment updates instances of the application incrementally, typically one at a time or in small batches. This approach allows for continuous availability but can lead to having multiple versions running simultaneously.

**Key Benefits:**
- Reduced resource requirements
- Continuous availability
- Gradual rollout

**Implementation:**
1. Deploy to a subset of instances
2. Run health checks
3. Continue to the next batch when health checks pass
4. Repeat until all instances are updated

### Canary Deployment

Canary deployment is a technique to reduce risk by slowly rolling out changes to a small subset of users before making them available to everyone.

**Key Benefits:**
- Early detection of issues
- Reduced risk
- Controlled exposure

**Implementation:**
1. Deploy the new version to a small percentage of instances
2. Monitor metrics and errors
3. Gradually increase traffic to the new version
4. Roll back if issues are detected

## CI/CD Integration

The uno Deployment Pipeline integrates with popular CI/CD platforms:

### GitHub Actions

The pipeline provides a GitHub Actions workflow template that includes:
- Building and testing the application
- Security scanning
- Building and pushing Docker images
- Deploying to different environments

### Kubernetes Deployment

For Kubernetes deployments, the pipeline provides:
- Template-based Kubernetes manifest generation
- Support for various Kubernetes resources (Deployments, Services, Ingress, etc.)
- Health check and readiness probe configuration
- Horizontal Pod Autoscaling

### Docker Compose

For simpler deployments or local development, the pipeline provides a Docker Compose template that includes:
- Application service
- PostgreSQL database
- Redis cache
- Nginx web server

## Usage

### Basic Deployment

```bash
python -m uno.deployment.scripts.deploy \
  --app-name my-app \
  --environment prod \
  --platform kubernetes \
  --config-file ./deployment/config.yaml
```

### Blue-Green Deployment

```bash
python -m uno.deployment.scripts.blue_green \
  --app-name my-app \
  --namespace my-namespace \
  --image-tag v1.0.0 \
  --health-check-url http://my-app-{env}.example.com/health
```

### Configuration

Create a deployment configuration file:

```yaml
app_name: my-app
app_version: 1.0.0
environment: prod
platform: kubernetes

database:
  host: postgres
  port: 5432
  name: myapp_db
  user: myapp_user
  password_env_var: DB_PASSWORD

resources:
  replicas_min: 2
  replicas_max: 5
  cpu_min: 250m
  cpu_max: 1000m
  memory_min: 512Mi
  memory_max: 1Gi

network:
  domain: myapp.example.com
  use_https: true

strategy: blue-green

testing:
  run_unit_tests: true
  run_integration_tests: true
  run_performance_tests: true
  run_security_tests: true
```

## Extending the Pipeline

The uno Deployment Pipeline is designed to be extensible. You can:

1. Create custom deployment strategies by extending the `DeploymentStrategy` base class
2. Add new tasks to the pipeline by modifying the `DeploymentManager._create_pipeline` method
3. Create templates for additional platforms
4. Implement platform-specific deployment logic