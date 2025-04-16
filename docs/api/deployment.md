# Deployment API

The Deployment module provides comprehensive functionality for deploying Uno applications to various platforms using different deployment strategies. It offers a complete pipeline for automated deployment, including validation, testing, build, deployment, and verification phases.

## Overview

The Deployment module is designed around domain-driven principles with clear separation of concerns between entities, repositories, and services. It supports various deployment platforms (Kubernetes, AWS, Azure, etc.) and deployment strategies (blue-green, rolling, canary, etc.).

## Key Components

### Core Entities

- **DeploymentConfig**: Configuration for deploying an application, including settings for database, resources, network, security, monitoring, and testing
- **Pipeline**: A deployment pipeline consisting of stages and tasks
- **Stage**: A phase in the deployment pipeline (e.g., preparation, testing, deployment)
- **Task**: An individual unit of work in a deployment stage

### Repositories

The module provides repository interfaces with memory and database implementations:

- **DeploymentConfigRepository**: For storing and retrieving deployment configurations
- **PipelineRepository**: For managing deployment pipelines
- **DeploymentResultRepository**: For storing deployment results

### Services

The business logic is encapsulated in these service interfaces:

- **DeploymentConfigService**: For managing deployment configurations
- **PipelineService**: For creating and executing deployment pipelines
- **DeploymentService**: For deploying applications using configuration and pipelines

## Usage Examples

### Creating a Deployment Configuration

```python
from uno.deployment import (
    DeploymentConfigService, DeploymentEnvironment, DeploymentPlatform, 
    DeploymentStrategy
)

# Create a deployment configuration
config_service = inject.instance(DeploymentConfigService)
config_result = await config_service.create_config(
    app_name="my-app",
    app_version="1.0.0",
    environment=DeploymentEnvironment.DEV,
    platform=DeploymentPlatform.KUBERNETES,
    strategy=DeploymentStrategy.ROLLING,
    database_config={
        "host": "postgres-db",
        "port": 5432,
        "name": "myapp_db",
        "user": "myapp_user",
        "password_env_var": "DB_PASSWORD",
        "apply_migrations": True,
        "backup_before_deploy": True
    },
    resource_requirements={
        "cpu_min": "100m",
        "cpu_max": "500m",
        "memory_min": "256Mi",
        "memory_max": "512Mi",
        "replicas_min": 1,
        "replicas_max": 3,
        "auto_scaling": True,
        "auto_scaling_cpu_threshold": 80
    },
    network_config={
        "domain": "myapp.example.com",
        "use_https": True,
    },
    security_config={
        "enable_network_policy": True,
        "scan_images": True,
    },
    monitoring_config={
        "enable_logging": True,
        "enable_metrics": True,
        "log_level": "INFO",
    },
    testing_config={
        "run_unit_tests": True,
        "run_integration_tests": True,
    }
)

if config_result.is_success():
    config = config_result.value
    print(f"Created deployment config with ID: {config.id.value}")
else:
    print(f"Error creating config: {config_result.error.message}")
```

### Deploying an Application

```python
from uno.deployment import DeploymentService, DeploymentId

# Deploy an application using a deployment configuration
deployment_service = inject.instance(DeploymentService)
deployment_result = await deployment_service.deploy(
    config_id=DeploymentId(value="config-123"),
    description="Deploying version 1.0.0 to dev environment"
)

if deployment_result.is_success():
    result = deployment_result.value
    print(f"Deployment {'succeeded' if result.success else 'failed'}: {result.message}")
else:
    print(f"Error starting deployment: {deployment_result.error.message}")
```

### Creating and Executing a Pipeline Manually

```python
from uno.deployment import PipelineService, DeploymentId, PipelineId, StageId

# Create a deployment pipeline
pipeline_service = inject.instance(PipelineService)
pipeline_result = await pipeline_service.create_pipeline(
    name="my-app-dev-pipeline",
    description="Deployment pipeline for my-app to dev environment",
    deployment_id=DeploymentId(value="config-123")
)

pipeline = pipeline_result.value
pipeline_id = pipeline.id

# Add a preparation stage
prep_stage_result = await pipeline_service.add_stage(
    pipeline_id=pipeline_id,
    name="preparation",
    description="Prepare for deployment",
    fail_fast=True
)
prep_stage = prep_stage_result.value

# Add tasks to the preparation stage
await pipeline_service.add_task(
    pipeline_id=pipeline_id,
    stage_id=prep_stage.id,
    name="validate-config",
    description="Validate deployment configuration"
)

# Add more stages and tasks...

# Execute the pipeline
execution_result = await pipeline_service.execute_pipeline(pipeline_id)
if execution_result.is_success():
    executed_pipeline = execution_result.value
    print(f"Pipeline status: {executed_pipeline.status.value}")
else:
    print(f"Error executing pipeline: {execution_result.error.message}")
```

### Rolling Back a Deployment

```python
from uno.deployment import DeploymentService, DeploymentId

# Roll back a deployment
deployment_service = inject.instance(DeploymentService)
rollback_result = await deployment_service.rollback(
    deployment_id=DeploymentId(value="deployment-123")
)

if rollback_result.is_success():
    result = rollback_result.value
    print(f"Rollback {'succeeded' if result.success else 'failed'}: {result.message}")
else:
    print(f"Error rolling back deployment: {rollback_result.error.message}")
```

## HTTP API Examples

The Deployment module provides HTTP API endpoints for interacting with deployments from external systems.

### Creating a Deployment Configuration

```http
POST /api/deployments/configs HTTP/1.1
Content-Type: application/json

{
  "app_name": "my-app",
  "app_version": "1.0.0",
  "environment": "dev",
  "platform": "kubernetes",
  "strategy": "rolling",
  "database": {
    "host": "postgres-db",
    "port": 5432,
    "name": "myapp_db",
    "user": "myapp_user",
    "password_env_var": "DB_PASSWORD",
    "apply_migrations": true,
    "backup_before_deploy": true
  },
  "resources": {
    "cpu_min": "100m",
    "cpu_max": "500m",
    "memory_min": "256Mi",
    "memory_max": "512Mi",
    "replicas_min": 1,
    "replicas_max": 3,
    "auto_scaling": true,
    "auto_scaling_cpu_threshold": 80
  },
  "network": {
    "domain": "myapp.example.com",
    "use_https": true
  },
  "security": {
    "enable_network_policy": true,
    "scan_images": true
  },
  "monitoring": {
    "enable_logging": true,
    "enable_metrics": true,
    "log_level": "INFO"
  },
  "testing": {
    "run_unit_tests": true,
    "run_integration_tests": true
  }
}
```

### Deploying an Application

```http
POST /api/deployments/deploy HTTP/1.1
Content-Type: application/json

{
  "config_id": "config-123",
  "description": "Deploying version 1.0.0 to dev environment"
}
```

### Rolling Back a Deployment

```http
POST /api/deployments/rollback HTTP/1.1
Content-Type: application/json

{
  "deployment_id": "deployment-123"
}
```

### Getting Deployment Status

```http
GET /api/deployments/status/deployment-123 HTTP/1.1
```

## Environment-Specific Configurations

The Deployment module automatically adjusts configurations based on the target environment:

- **Development** (DEV)
  - Simple deployment strategy (recreate)
  - Minimal resource requirements
  - Basic security features
  - Only unit tests run

- **Testing** (TEST)
  - Rolling deployment strategy
  - Basic resource requirements
  - Unit and integration tests

- **Staging** (STAGING)
  - Blue-green deployment strategy
  - Moderate resource requirements
  - Enhanced security features
  - Comprehensive testing

- **Production** (PRODUCTION)
  - Blue-green or canary deployment strategy
  - Higher resource requirements
  - Enhanced security features
  - Comprehensive testing including performance tests

## Supported Deployment Platforms

The module supports the following deployment platforms:

- **Kubernetes** - For container orchestration
- **AWS** - Amazon Web Services
- **Azure** - Microsoft Azure
- **GCP** - Google Cloud Platform
- **Heroku** - Heroku platform
- **DigitalOcean** - DigitalOcean platform
- **Custom** - For custom deployment methods

## Supported Deployment Strategies

The module supports the following deployment strategies:

- **Blue-Green** - Deploy new version alongside old version and switch traffic
- **Rolling** - Gradually update instances one at a time or in small batches
- **Canary** - Deploy new version to a small subset of instances/users first
- **Recreate** - Take down old version and deploy new version (with downtime)

## Working with Pipelines

### Pipeline Stages

A deployment pipeline typically consists of the following stages:

1. **Preparation** - Validate configuration and check dependencies
2. **Testing** - Run unit, integration, performance, and security tests
3. **Build** - Build application artifacts and container images
4. **Deployment** - Deploy to the target environment
5. **Verification** - Verify deployment and run health checks

### Tasks

Each stage contains tasks to be executed in order. Tasks can have dependencies on other tasks, and can be configured to skip dependent tasks on failure.

## Configuration Reference

### Database Configuration

| Property             | Type    | Description                             |
|----------------------|---------|-----------------------------------------|
| host                 | string  | Database host                           |
| port                 | integer | Database port                           |
| name                 | string  | Database name                           |
| user                 | string  | Database username                       |
| password_env_var     | string  | Environment variable for DB password    |
| ssl_mode             | string  | SSL mode for database connection        |
| connection_pool_min  | integer | Minimum connection pool size            |
| connection_pool_max  | integer | Maximum connection pool size            |
| apply_migrations     | boolean | Apply migrations during deployment      |
| backup_before_deploy | boolean | Backup database before deployment       |

### Resource Requirements

| Property                 | Type    | Description                          |
|--------------------------|---------|--------------------------------------|
| cpu_min                  | string  | Minimum CPU requirement              |
| cpu_max                  | string  | Maximum CPU requirement              |
| memory_min               | string  | Minimum memory requirement           |
| memory_max               | string  | Maximum memory requirement           |
| replicas_min             | integer | Minimum number of replicas           |
| replicas_max             | integer | Maximum number of replicas           |
| auto_scaling             | boolean | Enable auto-scaling                  |
| auto_scaling_cpu_threshold | integer | CPU threshold for auto-scaling    |

## Integration with Other Modules

The Deployment module integrates with:

- **Domain Core** - For base entities and value objects
- **Database** - For storing deployment configurations and results
- **Core** - For error handling and result pattern

## Best Practices

1. **Use environment-specific configurations**: Create separate configurations for development, testing, staging, and production environments.

2. **Enable appropriate testing**: Enable the appropriate level of testing for each environment.

3. **Backup before deployment**: Always backup the database before deployment, especially in production.

4. **Use blue-green or canary deployment for production**: These strategies minimize downtime and risk.

5. **Define custom settings for specific requirements**: Use the custom_settings field to define platform-specific settings.

6. **Monitor deployments**: Enable logging, metrics, and alerting to monitor deployments.

7. **Roll back failed deployments**: Use the rollback functionality to quickly recover from failed deployments.

## Error Handling

All services in the Deployment module use the Result pattern for consistent error handling. This means that methods return a Result object that contains either a success value or an error with details.

```python
result = await deployment_service.deploy(config_id=DeploymentId(value="config-123"))
if result.is_success():
    # Handle success
    deployment_result = result.value
else:
    # Handle error
    error = result.error
    print(f"Error code: {error.code.value}")
    print(f"Error message: {error.message}")
    print(f"Error context: {error.context}")
```

## API Reference

See the [UnoObj API Documentation](../api/overview.md) for detailed information on the base classes and interfaces.