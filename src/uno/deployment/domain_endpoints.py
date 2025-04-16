"""
Domain endpoints for the Deployment module.

This module defines FastAPI endpoints for the Deployment module,
providing HTTP API access to deployment functionality.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Set

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field

from uno.core.di_fastapi import inject_dependency
from uno.core.result import Result, Success, Failure

from uno.deployment.entities import (
    DeploymentId, PipelineId, StageId, TaskId, StrategyId,
    DeploymentConfig, Pipeline, Stage, Task,
    DeploymentEnvironment, DeploymentPlatform, DeploymentStrategy,
    DeploymentStatus, StageStatus, TaskStatus,
    DeploymentResult,
    DatabaseConfig, ResourceRequirements, NetworkConfig, SecurityConfig,
    MonitoringConfig, TestingConfig
)
from uno.deployment.domain_services import (
    DeploymentConfigServiceProtocol,
    PipelineServiceProtocol,
    DeploymentServiceProtocol
)


# Pydantic models for API requests/responses

class DeploymentEnvironmentModel(str, Enum):
    """Deployment environment types for API."""
    DEV = "dev"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentPlatformModel(str, Enum):
    """Deployment platform types for API."""
    KUBERNETES = "kubernetes"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    HEROKU = "heroku"
    DIGITALOCEAN = "digitalocean"
    CUSTOM = "custom"


class DeploymentStrategyModel(str, Enum):
    """Deployment strategy types for API."""
    BLUE_GREEN = "blue-green"
    ROLLING = "rolling"
    CANARY = "canary"
    RECREATE = "recreate"


class DeploymentStatusModel(str, Enum):
    """Deployment status types for API."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    ROLLING_BACK = "rolling-back"
    ROLLED_BACK = "rolled-back"


class StageStatusModel(str, Enum):
    """Stage status types for API."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStatusModel(str, Enum):
    """Task status types for API."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class DatabaseConfigModel(BaseModel):
    """Database configuration for API."""
    host: str = Field(..., description="Database host")
    port: int = Field(5432, description="Database port")
    name: str = Field(..., description="Database name")
    user: str = Field(..., description="Database username")
    password_env_var: str = Field("DB_PASSWORD", description="Environment variable for database password")
    ssl_mode: Optional[str] = Field(None, description="SSL mode for database connection")
    connection_pool_min: int = Field(5, description="Minimum connection pool size")
    connection_pool_max: int = Field(20, description="Maximum connection pool size")
    apply_migrations: bool = Field(True, description="Apply migrations during deployment")
    backup_before_deploy: bool = Field(True, description="Backup database before deployment")


class ResourceRequirementsModel(BaseModel):
    """Resource requirements for API."""
    cpu_min: str = Field("100m", description="Minimum CPU requirement")
    cpu_max: str = Field("500m", description="Maximum CPU requirement")
    memory_min: str = Field("256Mi", description="Minimum memory requirement")
    memory_max: str = Field("512Mi", description="Maximum memory requirement")
    replicas_min: int = Field(1, description="Minimum number of replicas")
    replicas_max: int = Field(3, description="Maximum number of replicas")
    auto_scaling: bool = Field(True, description="Enable auto-scaling")
    auto_scaling_cpu_threshold: int = Field(80, description="CPU utilization threshold for auto-scaling")


class NetworkConfigModel(BaseModel):
    """Network configuration for API."""
    domain: Optional[str] = Field(None, description="Domain name")
    use_https: bool = Field(True, description="Use HTTPS")
    use_hsts: bool = Field(True, description="Use HTTP Strict Transport Security")
    ingress_annotations: Dict[str, str] = Field(default_factory=dict, description="Ingress annotations")
    cors_allowed_origins: List[str] = Field(default_factory=list, description="CORS allowed origins")
    rate_limiting: bool = Field(False, description="Enable rate limiting")
    rate_limit_requests: int = Field(100, description="Rate limit requests per minute")


class SecurityConfigModel(BaseModel):
    """Security configuration for API."""
    enable_network_policy: bool = Field(True, description="Enable network policy")
    pod_security_policy: str = Field("restricted", description="Pod security policy")
    scan_images: bool = Field(True, description="Scan container images for vulnerabilities")
    scan_dependencies: bool = Field(True, description="Scan dependencies for vulnerabilities")
    enable_secrets_encryption: bool = Field(True, description="Enable secrets encryption")
    secrets_provider: str = Field("vault", description="Secrets provider")


class MonitoringConfigModel(BaseModel):
    """Monitoring configuration for API."""
    enable_logging: bool = Field(True, description="Enable logging")
    enable_metrics: bool = Field(True, description="Enable metrics collection")
    enable_tracing: bool = Field(True, description="Enable distributed tracing")
    log_level: str = Field("INFO", description="Log level")
    retention_days: int = Field(30, description="Log retention days")
    alerting: bool = Field(True, description="Enable alerting")
    alert_channels: List[str] = Field(default_factory=lambda: ["email"], description="Alert channels")


class TestingConfigModel(BaseModel):
    """Testing configuration for API."""
    run_unit_tests: bool = Field(True, description="Run unit tests")
    run_integration_tests: bool = Field(True, description="Run integration tests")
    run_performance_tests: bool = Field(False, description="Run performance tests (can be time-consuming)")
    run_security_tests: bool = Field(True, description="Run security tests")
    fail_on_test_failure: bool = Field(True, description="Fail deployment on test failure")
    test_coverage_threshold: int = Field(80, description="Test coverage threshold percentage")


class CreateConfigRequest(BaseModel):
    """Request to create a deployment configuration."""
    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application version")
    environment: DeploymentEnvironmentModel = Field(..., description="Deployment environment")
    platform: DeploymentPlatformModel = Field(..., description="Deployment platform")
    strategy: DeploymentStrategyModel = Field(..., description="Deployment strategy")
    database: DatabaseConfigModel = Field(..., description="Database configuration")
    resources: ResourceRequirementsModel = Field(..., description="Resource requirements")
    network: NetworkConfigModel = Field(..., description="Network configuration")
    security: SecurityConfigModel = Field(..., description="Security configuration")
    monitoring: MonitoringConfigModel = Field(..., description="Monitoring configuration")
    testing: TestingConfigModel = Field(..., description="Testing configuration")
    custom_settings: Optional[Dict[str, Any]] = Field(None, description="Custom settings")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    secrets: Optional[List[str]] = Field(None, description="Secret keys (values provided separately)")
    config_files: Optional[List[str]] = Field(None, description="Additional configuration files")


class CreateEnvironmentConfigRequest(BaseModel):
    """Request to create an environment-specific configuration."""
    environment: DeploymentEnvironmentModel = Field(..., description="Target environment")


class DeployRequest(BaseModel):
    """Request to deploy an application."""
    config_id: str = Field(..., description="Deployment configuration ID")
    description: Optional[str] = Field(None, description="Deployment description")


class RollbackRequest(BaseModel):
    """Request to roll back a deployment."""
    deployment_id: str = Field(..., description="Deployment ID")


class DeploymentConfigResponse(BaseModel):
    """Response model for a deployment configuration."""
    id: str = Field(..., description="Deployment configuration ID")
    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    platform: str = Field(..., description="Deployment platform")
    strategy: str = Field(..., description="Deployment strategy")
    database: DatabaseConfigModel = Field(..., description="Database configuration")
    resources: ResourceRequirementsModel = Field(..., description="Resource requirements")
    network: NetworkConfigModel = Field(..., description="Network configuration")
    security: SecurityConfigModel = Field(..., description="Security configuration")
    monitoring: MonitoringConfigModel = Field(..., description="Monitoring configuration")
    testing: TestingConfigModel = Field(..., description="Testing configuration")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom settings")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    secrets: List[str] = Field(default_factory=list, description="Secret keys")
    config_files: List[str] = Field(default_factory=list, description="Configuration files")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DeploymentResultResponse(BaseModel):
    """Response model for a deployment result."""
    id: str = Field(..., description="Deployment result ID")
    deployment_id: str = Field(..., description="Deployment ID")
    success: bool = Field(..., description="Whether the deployment was successful")
    message: str = Field(..., description="Deployment message")
    status: str = Field(..., description="Deployment status")
    details: Dict[str, Any] = Field(default_factory=dict, description="Deployment details")
    created_at: datetime = Field(..., description="Creation timestamp")


class TaskResponse(BaseModel):
    """Response model for a deployment task."""
    id: str = Field(..., description="Task ID")
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Task description")
    status: str = Field(..., description="Task status")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    skip_on_failure: bool = Field(False, description="Whether dependent tasks should be skipped if this task fails")
    timeout: Optional[int] = Field(None, description="Task timeout in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if task failed")


class StageResponse(BaseModel):
    """Response model for a deployment stage."""
    id: str = Field(..., description="Stage ID")
    name: str = Field(..., description="Stage name")
    description: str = Field(..., description="Stage description")
    status: str = Field(..., description="Stage status")
    fail_fast: bool = Field(True, description="Whether to fail fast on task failure")
    tasks: List[TaskResponse] = Field(default_factory=list, description="Stage tasks")
    dependencies: List[str] = Field(default_factory=list, description="Stage dependencies")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class PipelineResponse(BaseModel):
    """Response model for a deployment pipeline."""
    id: str = Field(..., description="Pipeline ID")
    name: str = Field(..., description="Pipeline name")
    description: str = Field(..., description="Pipeline description")
    stages: List[StageResponse] = Field(default_factory=list, description="Pipeline stages")
    status: str = Field(..., description="Pipeline status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    context: Dict[str, Any] = Field(default_factory=dict, description="Pipeline context")


# Domain-to-API model converters

def domain_config_to_api(config: DeploymentConfig) -> DeploymentConfigResponse:
    """
    Convert a domain deployment configuration to an API response model.
    
    Args:
        config: The domain deployment configuration
        
    Returns:
        API response model
    """
    return DeploymentConfigResponse(
        id=config.id.value,
        app_name=config.app_name,
        app_version=config.app_version,
        environment=config.environment.value,
        platform=config.platform.value,
        strategy=config.strategy.value,
        database=DatabaseConfigModel(
            host=config.database.host,
            port=config.database.port,
            name=config.database.name,
            user=config.database.user,
            password_env_var=config.database.password_env_var,
            ssl_mode=config.database.ssl_mode,
            connection_pool_min=config.database.connection_pool_min,
            connection_pool_max=config.database.connection_pool_max,
            apply_migrations=config.database.apply_migrations,
            backup_before_deploy=config.database.backup_before_deploy
        ),
        resources=ResourceRequirementsModel(
            cpu_min=config.resources.cpu_min,
            cpu_max=config.resources.cpu_max,
            memory_min=config.resources.memory_min,
            memory_max=config.resources.memory_max,
            replicas_min=config.resources.replicas_min,
            replicas_max=config.resources.replicas_max,
            auto_scaling=config.resources.auto_scaling,
            auto_scaling_cpu_threshold=config.resources.auto_scaling_cpu_threshold
        ),
        network=NetworkConfigModel(
            domain=config.network.domain,
            use_https=config.network.use_https,
            use_hsts=config.network.use_hsts,
            ingress_annotations=config.network.ingress_annotations,
            cors_allowed_origins=config.network.cors_allowed_origins,
            rate_limiting=config.network.rate_limiting,
            rate_limit_requests=config.network.rate_limit_requests
        ),
        security=SecurityConfigModel(
            enable_network_policy=config.security.enable_network_policy,
            pod_security_policy=config.security.pod_security_policy,
            scan_images=config.security.scan_images,
            scan_dependencies=config.security.scan_dependencies,
            enable_secrets_encryption=config.security.enable_secrets_encryption,
            secrets_provider=config.security.secrets_provider
        ),
        monitoring=MonitoringConfigModel(
            enable_logging=config.monitoring.enable_logging,
            enable_metrics=config.monitoring.enable_metrics,
            enable_tracing=config.monitoring.enable_tracing,
            log_level=config.monitoring.log_level,
            retention_days=config.monitoring.retention_days,
            alerting=config.monitoring.alerting,
            alert_channels=config.monitoring.alert_channels
        ),
        testing=TestingConfigModel(
            run_unit_tests=config.testing.run_unit_tests,
            run_integration_tests=config.testing.run_integration_tests,
            run_performance_tests=config.testing.run_performance_tests,
            run_security_tests=config.testing.run_security_tests,
            fail_on_test_failure=config.testing.fail_on_test_failure,
            test_coverage_threshold=config.testing.test_coverage_threshold
        ),
        custom_settings=config.custom_settings,
        environment_variables=config.environment_variables,
        secrets=config.secrets,
        config_files=config.config_files,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


def domain_result_to_api(result: DeploymentResult) -> DeploymentResultResponse:
    """
    Convert a domain deployment result to an API response model.
    
    Args:
        result: The domain deployment result
        
    Returns:
        API response model
    """
    return DeploymentResultResponse(
        id=result.id,
        deployment_id=result.deployment_id.value,
        success=result.success,
        message=result.message,
        status=result.status.value,
        details=result.details,
        created_at=result.created_at
    )


def domain_task_to_api(task: Task) -> TaskResponse:
    """
    Convert a domain task to an API response model.
    
    Args:
        task: The domain task
        
    Returns:
        API response model
    """
    return TaskResponse(
        id=task.id.value,
        name=task.name,
        description=task.description,
        status=task.status.value,
        dependencies=[dep.value for dep in task.dependencies],
        skip_on_failure=task.skip_on_failure,
        timeout=task.timeout,
        created_at=task.created_at,
        updated_at=task.updated_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        result=task.result,
        error=task.error
    )


def domain_stage_to_api(stage: Stage) -> StageResponse:
    """
    Convert a domain stage to an API response model.
    
    Args:
        stage: The domain stage
        
    Returns:
        API response model
    """
    return StageResponse(
        id=stage.id.value,
        name=stage.name,
        description=stage.description,
        status=stage.status.value,
        fail_fast=stage.fail_fast,
        tasks=[domain_task_to_api(task) for task in stage.tasks],
        dependencies=[dep.value for dep in stage.dependencies],
        created_at=stage.created_at,
        updated_at=stage.updated_at,
        started_at=stage.started_at,
        completed_at=stage.completed_at
    )


def domain_pipeline_to_api(pipeline: Pipeline) -> PipelineResponse:
    """
    Convert a domain pipeline to an API response model.
    
    Args:
        pipeline: The domain pipeline
        
    Returns:
        API response model
    """
    return PipelineResponse(
        id=pipeline.id.value,
        name=pipeline.name,
        description=pipeline.description,
        stages=[domain_stage_to_api(stage) for stage in pipeline.stages],
        status=pipeline.status.value,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
        started_at=pipeline.started_at,
        completed_at=pipeline.completed_at,
        context=pipeline.context
    )


# Create the API router

def create_deployment_router() -> APIRouter:
    """
    Create the FastAPI router for the Deployment module.
    
    Returns:
        FastAPI router
    """
    router = APIRouter(prefix="/api/deployments", tags=["Deployments"])
    
    # Helper function to handle service results
    def handle_result(result: Result[Any], not_found_message: str = "Item not found") -> Any:
        """
        Handle a service result, raising appropriate HTTP exceptions.
        
        Args:
            result: The service result
            not_found_message: Message to use for not found errors
            
        Returns:
            The result value if successful
            
        Raises:
            HTTPException: If the result is a failure
        """
        if not result.is_success():
            if result.error.code.value == "not_found":
                raise HTTPException(status_code=404, detail=not_found_message)
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {result.error.message}"
            )
        return result.value
    
    # Deployment configuration endpoints
    
    @router.get("/configs", response_model=List[DeploymentConfigResponse])
    async def list_configs(
        app_name: Optional[str] = Query(None, description="Filter by application name"),
        environment: Optional[DeploymentEnvironmentModel] = Query(None, description="Filter by environment"),
        config_service: DeploymentConfigServiceProtocol = Depends(inject_dependency(DeploymentConfigServiceProtocol))
    ) -> List[DeploymentConfigResponse]:
        """List deployment configurations."""
        if app_name:
            result = await config_service.get_configs_by_app_name(app_name)
            configs = handle_result(result, f"No configurations found for app {app_name}")
        elif environment:
            domain_env = DeploymentEnvironment(environment.value)
            result = await config_service.get_configs_by_environment(domain_env)
            configs = handle_result(result, f"No configurations found for environment {environment.value}")
        else:
            result = await config_service.list_configs()
            configs = handle_result(result, "No configurations found")
        
        return [domain_config_to_api(config) for config in configs]
    
    @router.get("/configs/{id}", response_model=DeploymentConfigResponse)
    async def get_config(
        id: str = Path(..., description="Deployment configuration ID"),
        config_service: DeploymentConfigServiceProtocol = Depends(inject_dependency(DeploymentConfigServiceProtocol))
    ) -> DeploymentConfigResponse:
        """Get a deployment configuration by ID."""
        result = await config_service.get_config(DeploymentId(value=id))
        config = handle_result(result, f"Configuration with ID {id} not found")
        
        if config is None:
            raise HTTPException(status_code=404, detail=f"Configuration with ID {id} not found")
            
        return domain_config_to_api(config)
    
    @router.post("/configs", response_model=DeploymentConfigResponse, status_code=201)
    async def create_config(
        request: CreateConfigRequest = Body(..., description="Deployment configuration to create"),
        config_service: DeploymentConfigServiceProtocol = Depends(inject_dependency(DeploymentConfigServiceProtocol))
    ) -> DeploymentConfigResponse:
        """Create a new deployment configuration."""
        result = await config_service.create_config(
            app_name=request.app_name,
            app_version=request.app_version,
            environment=DeploymentEnvironment(request.environment.value),
            platform=DeploymentPlatform(request.platform.value),
            strategy=DeploymentStrategy(request.strategy.value),
            database_config=request.database.dict(),
            resource_requirements=request.resources.dict(),
            network_config=request.network.dict(),
            security_config=request.security.dict(),
            monitoring_config=request.monitoring.dict(),
            testing_config=request.testing.dict(),
            custom_settings=request.custom_settings,
            environment_variables=request.environment_variables,
            secrets=request.secrets,
            config_files=request.config_files
        )
        
        config = handle_result(result, "Failed to create configuration")
        return domain_config_to_api(config)
    
    @router.post("/configs/{id}/environments", response_model=DeploymentConfigResponse, status_code=201)
    async def create_environment_config(
        id: str = Path(..., description="Base configuration ID"),
        request: CreateEnvironmentConfigRequest = Body(..., description="Environment to create configuration for"),
        config_service: DeploymentConfigServiceProtocol = Depends(inject_dependency(DeploymentConfigServiceProtocol))
    ) -> DeploymentConfigResponse:
        """Create a configuration for a specific environment based on an existing configuration."""
        # Get the base configuration
        get_result = await config_service.get_config(DeploymentId(value=id))
        base_config = handle_result(get_result, f"Base configuration with ID {id} not found")
        
        if base_config is None:
            raise HTTPException(status_code=404, detail=f"Base configuration with ID {id} not found")
        
        # Create the environment-specific configuration
        result = await config_service.create_environment_config(
            config=base_config,
            environment=DeploymentEnvironment(request.environment.value)
        )
        
        config = handle_result(result, "Failed to create environment configuration")
        return domain_config_to_api(config)
    
    @router.delete("/configs/{id}", status_code=204)
    async def delete_config(
        id: str = Path(..., description="Deployment configuration ID"),
        config_service: DeploymentConfigServiceProtocol = Depends(inject_dependency(DeploymentConfigServiceProtocol))
    ) -> None:
        """Delete a deployment configuration."""
        result = await config_service.delete_config(DeploymentId(value=id))
        handle_result(result, f"Configuration with ID {id} not found")
    
    # Deployment endpoints
    
    @router.post("/deploy", response_model=DeploymentResultResponse, status_code=202)
    async def deploy(
        request: DeployRequest = Body(..., description="Deployment request"),
        deployment_service: DeploymentServiceProtocol = Depends(inject_dependency(DeploymentServiceProtocol))
    ) -> DeploymentResultResponse:
        """Deploy an application using the specified configuration."""
        result = await deployment_service.deploy(
            config_id=DeploymentId(value=request.config_id),
            description=request.description
        )
        
        deployment_result = handle_result(result, f"Failed to deploy with configuration {request.config_id}")
        return domain_result_to_api(deployment_result)
    
    @router.post("/rollback", response_model=DeploymentResultResponse, status_code=202)
    async def rollback(
        request: RollbackRequest = Body(..., description="Rollback request"),
        deployment_service: DeploymentServiceProtocol = Depends(inject_dependency(DeploymentServiceProtocol))
    ) -> DeploymentResultResponse:
        """Roll back a deployment."""
        result = await deployment_service.rollback(
            deployment_id=DeploymentId(value=request.deployment_id)
        )
        
        rollback_result = handle_result(result, f"Failed to roll back deployment {request.deployment_id}")
        return domain_result_to_api(rollback_result)
    
    @router.get("/status/{id}", response_model=str)
    async def get_deployment_status(
        id: str = Path(..., description="Deployment ID"),
        deployment_service: DeploymentServiceProtocol = Depends(inject_dependency(DeploymentServiceProtocol))
    ) -> str:
        """Get the status of a deployment."""
        result = await deployment_service.get_deployment_status(DeploymentId(value=id))
        status = handle_result(result, f"Deployment with ID {id} not found")
        return status.value
    
    @router.get("/results/{id}", response_model=DeploymentResultResponse)
    async def get_deployment_result(
        id: str = Path(..., description="Deployment ID"),
        deployment_service: DeploymentServiceProtocol = Depends(inject_dependency(DeploymentServiceProtocol))
    ) -> DeploymentResultResponse:
        """Get the result of a deployment."""
        result = await deployment_service.get_deployment_result(DeploymentId(value=id))
        deployment_result = handle_result(result, f"Deployment result for ID {id} not found")
        
        if deployment_result is None:
            raise HTTPException(status_code=404, detail=f"Deployment result for ID {id} not found")
            
        return domain_result_to_api(deployment_result)
    
    @router.get("/results", response_model=List[DeploymentResultResponse])
    async def list_deployment_results(
        app_name: Optional[str] = Query(None, description="Filter by application name"),
        environment: Optional[DeploymentEnvironmentModel] = Query(None, description="Filter by environment"),
        status: Optional[DeploymentStatusModel] = Query(None, description="Filter by status"),
        deployment_service: DeploymentServiceProtocol = Depends(inject_dependency(DeploymentServiceProtocol))
    ) -> List[DeploymentResultResponse]:
        """List deployment results."""
        domain_env = DeploymentEnvironment(environment.value) if environment else None
        domain_status = DeploymentStatus(status.value) if status else None
        
        result = await deployment_service.list_deployments(
            app_name=app_name,
            environment=domain_env,
            status=domain_status
        )
        
        deployment_results = handle_result(result, "No deployment results found")
        return [domain_result_to_api(r) for r in deployment_results]
    
    # Pipeline endpoints
    
    @router.get("/pipelines/{id}", response_model=PipelineResponse)
    async def get_pipeline(
        id: str = Path(..., description="Pipeline ID"),
        pipeline_service: PipelineServiceProtocol = Depends(inject_dependency(PipelineServiceProtocol))
    ) -> PipelineResponse:
        """Get a pipeline by ID."""
        result = await pipeline_service.get_pipeline(PipelineId(value=id))
        pipeline = handle_result(result, f"Pipeline with ID {id} not found")
        
        if pipeline is None:
            raise HTTPException(status_code=404, detail=f"Pipeline with ID {id} not found")
            
        return domain_pipeline_to_api(pipeline)
    
    @router.get("/deployments/{id}/pipelines", response_model=List[PipelineResponse])
    async def get_pipelines_by_deployment(
        id: str = Path(..., description="Deployment ID"),
        pipeline_service: PipelineServiceProtocol = Depends(inject_dependency(PipelineServiceProtocol))
    ) -> List[PipelineResponse]:
        """Get pipelines for a deployment."""
        result = await pipeline_service.get_pipelines_by_deployment_id(DeploymentId(value=id))
        pipelines = handle_result(result, f"No pipelines found for deployment {id}")
        return [domain_pipeline_to_api(pipeline) for pipeline in pipelines]
    
    @router.post("/pipelines/{id}/cancel", status_code=204)
    async def cancel_pipeline(
        id: str = Path(..., description="Pipeline ID"),
        pipeline_service: PipelineServiceProtocol = Depends(inject_dependency(PipelineServiceProtocol))
    ) -> None:
        """Cancel a pipeline."""
        result = await pipeline_service.cancel_pipeline(PipelineId(value=id))
        handle_result(result, f"Failed to cancel pipeline {id}")
    
    # Additional endpoints would be added here
    
    return router


def create_deployment_endpoints(app: APIRouter) -> None:
    """
    Create FastAPI endpoints for the Deployment module.
    
    Args:
        app: The FastAPI router to attach endpoints to
    """
    app.include_router(create_deployment_router())