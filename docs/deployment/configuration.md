# Deployment Configuration

The Uno Deployment Pipeline uses a flexible configuration system to manage deployment settings across different environments and platforms. This document describes the configuration options and how to use them effectively.

## Configuration Structure

The deployment configuration is represented by the `DeploymentConfig` class, which contains the following main sections:

- **Basic Information**: Application name, version, environment, platform
- **Database Configuration**: Database connection settings and migration options
- **Resource Requirements**: CPU, memory, and scaling settings
- **Network Configuration**: Domain, HTTPS, CORS, and rate limiting settings
- **Security Configuration**: Network policies, secrets, and scanning options
- **Monitoring Configuration**: Logging, metrics, tracing, and alerting settings
- **Deployment Strategy**: Strategy type (blue-green, rolling, canary, recreate)
- **Testing Configuration**: Test types to run during deployment
- **Custom Settings**: Additional platform-specific or application-specific settings

## Configuration Example

Here's a complete example of a deployment configuration file:

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
  ssl_mode: require
  connection_pool_min: 5
  connection_pool_max: 20
  apply_migrations: true
  backup_before_deploy: true

resources:
  cpu_min: 250m
  cpu_max: 1000m
  memory_min: 512Mi
  memory_max: 1Gi
  replicas_min: 2
  replicas_max: 5
  auto_scaling: true
  auto_scaling_cpu_threshold: 80

network:
  domain: myapp.example.com
  use_https: true
  use_hsts: true
  ingress_annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: 10m
  cors_allowed_origins:
    - https://example.com
    - https://api.example.com
  rate_limiting: true
  rate_limit_requests: 100

security:
  enable_network_policy: true
  pod_security_policy: restricted
  scan_images: true
  scan_dependencies: true
  enable_secrets_encryption: true
  secrets_provider: vault

monitoring:
  enable_logging: true
  enable_metrics: true
  enable_tracing: true
  log_level: INFO
  retention_days: 30
  alerting: true
  alert_channels:
    - email
    - slack

strategy: blue-green

testing:
  run_unit_tests: true
  run_integration_tests: true
  run_performance_tests: true
  run_security_tests: true
  fail_on_test_failure: true
  test_coverage_threshold: 80

environment_variables:
  NODE_ENV: production
  LOG_FORMAT: json
  FEATURE_FLAG_NEW_UI: "true"

secrets:
  - DB_PASSWORD
  - API_KEY
  - JWT_SECRET

custom_settings:
  kubernetes:
    service_account: my-app-sa
    namespace: my-app-prod
    node_selector:
      disk-type: ssd
```

## Environment-Specific Configuration

The `DeploymentConfig` class provides a method to create environment-specific configurations:

```python
# Load the base configuration
config = DeploymentConfig.from_yaml("deployment/base.yaml")

# Create environment-specific configurations
dev_config = config.for_environment(DeploymentEnvironment.DEV)
test_config = config.for_environment(DeploymentEnvironment.TEST)
staging_config = config.for_environment(DeploymentEnvironment.STAGING)
prod_config = config.for_environment(DeploymentEnvironment.PRODUCTION)

# Save the environment-specific configurations
dev_config.to_yaml("deployment/dev.yaml")
test_config.to_yaml("deployment/test.yaml")
staging_config.to_yaml("deployment/staging.yaml")
prod_config.to_yaml("deployment/prod.yaml")
```

Each environment automatically adjusts certain settings to appropriate values:

### Production
- Strategy: Blue-Green or Canary
- Replicas: 2-5
- Resources: Higher CPU and memory
- Security: Enhanced security features
- Testing: All test types enabled

### Staging
- Strategy: Blue-Green
- Replicas: 1-3
- Security: Most security features enabled
- Testing: Unit and integration tests

### Test
- Strategy: Rolling
- Replicas: 1
- Security: Basic security features
- Testing: Only unit tests

### Development
- Strategy: Recreate
- Replicas: 1
- Auto-scaling: Disabled
- Security: Minimal security features
- Testing: Only unit tests

## Configuration Validation

The configuration is validated using Pydantic's validation system. Validators are implemented for certain fields to ensure consistency:

- **Environment Variables**: Automatically adds environment-specific variables
- **Deployment Strategy**: Enforces appropriate strategies for production

## Configuration Loading

Configuration can be loaded from YAML files:

```python
from uno.deployment.config import DeploymentConfig

# Load from a YAML file
config = DeploymentConfig.from_yaml("deployment/prod.yaml")

# Save to a YAML file
config.to_yaml("deployment/prod-updated.yaml")
```

## Command-Line Configuration

When using the deployment scripts, configuration can be specified via command-line arguments:

```bash
python -m uno.deployment.scripts.deploy \
  --app-name my-app \
  --app-version 1.0.0 \
  --environment prod \
  --platform kubernetes \
  --config-file deployment/prod.yaml \
  --image-tag v1.0.0 \
  --skip-tests \
  --dry-run
```

Command-line arguments override values from the configuration file.

## Environment Variable Configuration

Configuration can also be influenced by environment variables:

```bash
export APP_NAME=my-app
export APP_VERSION=1.0.0
export ENV=prod
export PLATFORM=kubernetes
export IMAGE_TAG=v1.0.0
export SKIP_TESTS=true

python -m uno.deployment.scripts.deploy --config-file deployment/prod.yaml
```

## Configuration Hierarchy

The configuration is resolved in the following order (with later sources overriding earlier ones):

1. Default values in the `DeploymentConfig` class
2. Configuration file specified with `--config-file`
3. Environment variables
4. Command-line arguments

This allows for flexible configuration management while ensuring consistent defaults.