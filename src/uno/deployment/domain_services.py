"""
Domain services for the Deployment module.

This module defines the service interfaces and implementations for the Deployment module,
providing business logic for deployment management.
"""

import logging
import os
import time
import asyncio
import subprocess
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone, UTC
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union, Tuple, Protocol, Generic, Type, TypeVar, cast, Callable

import yaml

from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode, ErrorDetails

from uno.deployment.entities import (
    DeploymentId, PipelineId, StageId, TaskId, StrategyId,
    DeploymentConfig, Pipeline, Stage, Task,
    DeploymentEnvironment, DeploymentPlatform, DeploymentStrategy,
    DeploymentStatus, StageStatus, TaskStatus,
    DeploymentResult,
    DatabaseConfig, ResourceRequirements, NetworkConfig, SecurityConfig,
    MonitoringConfig, TestingConfig
)
from uno.deployment.domain_repositories import (
    DeploymentConfigRepositoryProtocol,
    PipelineRepositoryProtocol,
    DeploymentResultRepositoryProtocol
)

# Type variables
T = TypeVar('T')


# Service protocols

class DeploymentConfigServiceProtocol(Protocol):
    """Protocol for deployment configuration services."""
    
    async def get_config(self, id: DeploymentId) -> Result[Optional[DeploymentConfig]]:
        """
        Get a deployment configuration by ID.
        
        Args:
            id: The deployment configuration ID
            
        Returns:
            Result containing the deployment configuration if found, None otherwise
        """
        ...
    
    async def get_configs_by_app_name(self, app_name: str) -> Result[List[DeploymentConfig]]:
        """
        Get deployment configurations by application name.
        
        Args:
            app_name: The application name
            
        Returns:
            Result containing the list of deployment configurations
        """
        ...
    
    async def get_configs_by_environment(self, environment: DeploymentEnvironment) -> Result[List[DeploymentConfig]]:
        """
        Get deployment configurations by environment.
        
        Args:
            environment: The environment
            
        Returns:
            Result containing the list of deployment configurations
        """
        ...
    
    async def list_configs(self) -> Result[List[DeploymentConfig]]:
        """
        List all deployment configurations.
        
        Returns:
            Result containing the list of all deployment configurations
        """
        ...
    
    async def create_config(
        self,
        app_name: str,
        app_version: str,
        environment: DeploymentEnvironment,
        platform: DeploymentPlatform,
        strategy: DeploymentStrategy,
        database_config: Dict[str, Any],
        resource_requirements: Dict[str, Any],
        network_config: Dict[str, Any],
        security_config: Dict[str, Any],
        monitoring_config: Dict[str, Any],
        testing_config: Dict[str, Any],
        custom_settings: Optional[Dict[str, Any]] = None,
        environment_variables: Optional[Dict[str, str]] = None,
        secrets: Optional[List[str]] = None,
        config_files: Optional[List[str]] = None
    ) -> Result[DeploymentConfig]:
        """
        Create a new deployment configuration.
        
        Args:
            app_name: Application name
            app_version: Application version
            environment: Deployment environment
            platform: Deployment platform
            strategy: Deployment strategy
            database_config: Database configuration
            resource_requirements: Resource requirements
            network_config: Network configuration
            security_config: Security configuration
            monitoring_config: Monitoring configuration
            testing_config: Testing configuration
            custom_settings: Optional custom settings
            environment_variables: Optional environment variables
            secrets: Optional secret keys
            config_files: Optional configuration files
            
        Returns:
            Result containing the created deployment configuration
        """
        ...
    
    async def update_config(self, config: DeploymentConfig) -> Result[DeploymentConfig]:
        """
        Update a deployment configuration.
        
        Args:
            config: The deployment configuration to update
            
        Returns:
            Result containing the updated deployment configuration
        """
        ...
    
    async def delete_config(self, id: DeploymentId) -> Result[bool]:
        """
        Delete a deployment configuration.
        
        Args:
            id: The deployment configuration ID
            
        Returns:
            Result containing True if the configuration was deleted, False otherwise
        """
        ...
    
    async def create_environment_config(
        self, config: DeploymentConfig, environment: DeploymentEnvironment
    ) -> Result[DeploymentConfig]:
        """
        Create a deployment configuration for a specific environment based on an existing configuration.
        
        Args:
            config: The base deployment configuration
            environment: The target environment
            
        Returns:
            Result containing the created deployment configuration
        """
        ...


class PipelineServiceProtocol(Protocol):
    """Protocol for deployment pipeline services."""
    
    async def get_pipeline(self, id: PipelineId) -> Result[Optional[Pipeline]]:
        """
        Get a pipeline by ID.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the pipeline if found, None otherwise
        """
        ...
    
    async def get_pipelines_by_deployment_id(self, deployment_id: DeploymentId) -> Result[List[Pipeline]]:
        """
        Get pipelines by deployment ID.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Result containing the list of pipelines
        """
        ...
    
    async def get_pipelines_by_status(self, status: DeploymentStatus) -> Result[List[Pipeline]]:
        """
        Get pipelines by status.
        
        Args:
            status: The pipeline status
            
        Returns:
            Result containing the list of pipelines
        """
        ...
    
    async def get_active_pipelines(self) -> Result[List[Pipeline]]:
        """
        Get active (running, rolling back) pipelines.
        
        Returns:
            Result containing the list of active pipelines
        """
        ...
    
    async def list_pipelines(self) -> Result[List[Pipeline]]:
        """
        List all pipelines.
        
        Returns:
            Result containing the list of all pipelines
        """
        ...
    
    async def create_pipeline(
        self,
        name: str,
        description: str,
        deployment_id: DeploymentId
    ) -> Result[Pipeline]:
        """
        Create a new pipeline.
        
        Args:
            name: Pipeline name
            description: Pipeline description
            deployment_id: The deployment ID this pipeline is associated with
            
        Returns:
            Result containing the created pipeline
        """
        ...
    
    async def add_stage(
        self,
        pipeline_id: PipelineId,
        name: str,
        description: str,
        fail_fast: bool = True
    ) -> Result[Stage]:
        """
        Add a stage to a pipeline.
        
        Args:
            pipeline_id: The pipeline ID
            name: Stage name
            description: Stage description
            fail_fast: Whether to fail fast on task failure
            
        Returns:
            Result containing the added stage
        """
        ...
    
    async def add_task(
        self,
        pipeline_id: PipelineId,
        stage_id: StageId,
        name: str,
        description: str,
        skip_on_failure: bool = False,
        timeout: Optional[int] = None,
        dependencies: Optional[List[TaskId]] = None
    ) -> Result[Task]:
        """
        Add a task to a stage.
        
        Args:
            pipeline_id: The pipeline ID
            stage_id: The stage ID
            name: Task name
            description: Task description
            skip_on_failure: Whether dependent tasks should be skipped if this task fails
            timeout: Optional timeout in seconds
            dependencies: Optional list of task dependencies
            
        Returns:
            Result containing the added task
        """
        ...
    
    async def start_pipeline(self, id: PipelineId) -> Result[Pipeline]:
        """
        Start a pipeline.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the updated pipeline
        """
        ...
    
    async def cancel_pipeline(self, id: PipelineId) -> Result[Pipeline]:
        """
        Cancel a pipeline.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the updated pipeline
        """
        ...
    
    async def rollback_pipeline(self, id: PipelineId) -> Result[Pipeline]:
        """
        Roll back a pipeline.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the updated pipeline
        """
        ...
    
    async def update_task_status(
        self,
        pipeline_id: PipelineId,
        stage_id: StageId,
        task_id: TaskId,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Result[Task]:
        """
        Update the status of a task.
        
        Args:
            pipeline_id: The pipeline ID
            stage_id: The stage ID
            task_id: The task ID
            status: The new task status
            result: Optional task result data
            error: Optional error message if task failed
            
        Returns:
            Result containing the updated task
        """
        ...
    
    async def execute_pipeline(self, id: PipelineId) -> Result[Pipeline]:
        """
        Execute a pipeline.
        
        This method will run the pipeline from start to finish,
        executing all stages and tasks in the appropriate order.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the executed pipeline
        """
        ...


class DeploymentServiceProtocol(Protocol):
    """Protocol for deployment services."""
    
    async def deploy(
        self,
        config_id: DeploymentId,
        description: Optional[str] = None
    ) -> Result[DeploymentResult]:
        """
        Deploy an application using the specified configuration.
        
        Args:
            config_id: The deployment configuration ID
            description: Optional deployment description
            
        Returns:
            Result containing the deployment result
        """
        ...
    
    async def rollback(
        self,
        deployment_id: DeploymentId
    ) -> Result[DeploymentResult]:
        """
        Roll back a deployment.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Result containing the rollback result
        """
        ...
    
    async def get_deployment_status(
        self,
        deployment_id: DeploymentId
    ) -> Result[DeploymentStatus]:
        """
        Get the status of a deployment.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Result containing the deployment status
        """
        ...
    
    async def get_deployment_result(
        self,
        deployment_id: DeploymentId
    ) -> Result[Optional[DeploymentResult]]:
        """
        Get the result of a deployment.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Result containing the deployment result if available, None otherwise
        """
        ...
    
    async def list_deployments(
        self,
        app_name: Optional[str] = None,
        environment: Optional[DeploymentEnvironment] = None,
        status: Optional[DeploymentStatus] = None
    ) -> Result[List[DeploymentResult]]:
        """
        List deployments.
        
        Args:
            app_name: Optional application name to filter by
            environment: Optional environment to filter by
            status: Optional status to filter by
            
        Returns:
            Result containing the list of deployment results
        """
        ...


# Service implementations

class DeploymentConfigService(DeploymentConfigServiceProtocol):
    """
    Implementation of the deployment configuration service.
    
    This service provides business logic for managing deployment configurations.
    """
    
    def __init__(
        self,
        config_repository: DeploymentConfigRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            config_repository: Repository for deployment configurations
            logger: Optional logger instance
        """
        self.config_repository = config_repository
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_config(self, id: DeploymentId) -> Result[Optional[DeploymentConfig]]:
        """
        Get a deployment configuration by ID.
        
        Args:
            id: The deployment configuration ID
            
        Returns:
            Result containing the deployment configuration if found, None otherwise
        """
        return await self.config_repository.get_by_id(id)
    
    async def get_configs_by_app_name(self, app_name: str) -> Result[List[DeploymentConfig]]:
        """
        Get deployment configurations by application name.
        
        Args:
            app_name: The application name
            
        Returns:
            Result containing the list of deployment configurations
        """
        return await self.config_repository.get_by_app_name(app_name)
    
    async def get_configs_by_environment(self, environment: DeploymentEnvironment) -> Result[List[DeploymentConfig]]:
        """
        Get deployment configurations by environment.
        
        Args:
            environment: The environment
            
        Returns:
            Result containing the list of deployment configurations
        """
        return await self.config_repository.get_by_environment(environment)
    
    async def list_configs(self) -> Result[List[DeploymentConfig]]:
        """
        List all deployment configurations.
        
        Returns:
            Result containing the list of all deployment configurations
        """
        return await self.config_repository.list_all()
    
    async def create_config(
        self,
        app_name: str,
        app_version: str,
        environment: DeploymentEnvironment,
        platform: DeploymentPlatform,
        strategy: DeploymentStrategy,
        database_config: Dict[str, Any],
        resource_requirements: Dict[str, Any],
        network_config: Dict[str, Any],
        security_config: Dict[str, Any],
        monitoring_config: Dict[str, Any],
        testing_config: Dict[str, Any],
        custom_settings: Optional[Dict[str, Any]] = None,
        environment_variables: Optional[Dict[str, str]] = None,
        secrets: Optional[List[str]] = None,
        config_files: Optional[List[str]] = None
    ) -> Result[DeploymentConfig]:
        """
        Create a new deployment configuration.
        
        Args:
            app_name: Application name
            app_version: Application version
            environment: Deployment environment
            platform: Deployment platform
            strategy: Deployment strategy
            database_config: Database configuration
            resource_requirements: Resource requirements
            network_config: Network configuration
            security_config: Security configuration
            monitoring_config: Monitoring configuration
            testing_config: Testing configuration
            custom_settings: Optional custom settings
            environment_variables: Optional environment variables
            secrets: Optional secret keys
            config_files: Optional configuration files
            
        Returns:
            Result containing the created deployment configuration
        """
        try:
            # Create the database configuration
            db_config = DatabaseConfig(
                id=str(uuid.uuid4()),
                host=database_config.get("host", "localhost"),
                port=database_config.get("port", 5432),
                name=database_config.get("name", app_name),
                user=database_config.get("user", app_name),
                password_env_var=database_config.get("password_env_var", "DB_PASSWORD"),
                ssl_mode=database_config.get("ssl_mode"),
                connection_pool_min=database_config.get("connection_pool_min", 5),
                connection_pool_max=database_config.get("connection_pool_max", 20),
                apply_migrations=database_config.get("apply_migrations", True),
                backup_before_deploy=database_config.get("backup_before_deploy", True)
            )
            
            # Create the resource requirements
            resources = ResourceRequirements(
                id=str(uuid.uuid4()),
                cpu_min=resource_requirements.get("cpu_min", "100m"),
                cpu_max=resource_requirements.get("cpu_max", "500m"),
                memory_min=resource_requirements.get("memory_min", "256Mi"),
                memory_max=resource_requirements.get("memory_max", "512Mi"),
                replicas_min=resource_requirements.get("replicas_min", 1),
                replicas_max=resource_requirements.get("replicas_max", 3),
                auto_scaling=resource_requirements.get("auto_scaling", True),
                auto_scaling_cpu_threshold=resource_requirements.get("auto_scaling_cpu_threshold", 80)
            )
            
            # Create the network configuration
            network = NetworkConfig(
                id=str(uuid.uuid4()),
                domain=network_config.get("domain"),
                use_https=network_config.get("use_https", True),
                use_hsts=network_config.get("use_hsts", True),
                ingress_annotations=network_config.get("ingress_annotations", {}),
                cors_allowed_origins=network_config.get("cors_allowed_origins", []),
                rate_limiting=network_config.get("rate_limiting", False),
                rate_limit_requests=network_config.get("rate_limit_requests", 100)
            )
            
            # Create the security configuration
            security = SecurityConfig(
                id=str(uuid.uuid4()),
                enable_network_policy=security_config.get("enable_network_policy", True),
                pod_security_policy=security_config.get("pod_security_policy", "restricted"),
                scan_images=security_config.get("scan_images", True),
                scan_dependencies=security_config.get("scan_dependencies", True),
                enable_secrets_encryption=security_config.get("enable_secrets_encryption", True),
                secrets_provider=security_config.get("secrets_provider", "vault")
            )
            
            # Create the monitoring configuration
            monitoring = MonitoringConfig(
                id=str(uuid.uuid4()),
                enable_logging=monitoring_config.get("enable_logging", True),
                enable_metrics=monitoring_config.get("enable_metrics", True),
                enable_tracing=monitoring_config.get("enable_tracing", True),
                log_level=monitoring_config.get("log_level", "INFO"),
                retention_days=monitoring_config.get("retention_days", 30),
                alerting=monitoring_config.get("alerting", True),
                alert_channels=monitoring_config.get("alert_channels", ["email"])
            )
            
            # Create the testing configuration
            testing = TestingConfig(
                id=str(uuid.uuid4()),
                run_unit_tests=testing_config.get("run_unit_tests", True),
                run_integration_tests=testing_config.get("run_integration_tests", True),
                run_performance_tests=testing_config.get("run_performance_tests", False),
                run_security_tests=testing_config.get("run_security_tests", True),
                fail_on_test_failure=testing_config.get("fail_on_test_failure", True),
                test_coverage_threshold=testing_config.get("test_coverage_threshold", 80)
            )
            
            # Create the deployment configuration
            config = DeploymentConfig(
                id=DeploymentId(value=str(uuid.uuid4())),
                app_name=app_name,
                app_version=app_version,
                environment=environment,
                platform=platform,
                strategy=strategy,
                database=db_config,
                resources=resources,
                network=network,
                security=security,
                monitoring=monitoring,
                testing=testing,
                custom_settings=custom_settings or {},
                environment_variables=environment_variables or {},
                secrets=secrets or [],
                config_files=config_files or []
            )
            
            # Save the configuration
            return await self.config_repository.save(config)
        except Exception as e:
            self.logger.error(f"Error creating deployment configuration: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to create deployment configuration: {str(e)}",
                    context={
                        "app_name": app_name,
                        "environment": environment.value
                    }
                )
            )
    
    async def update_config(self, config: DeploymentConfig) -> Result[DeploymentConfig]:
        """
        Update a deployment configuration.
        
        Args:
            config: The deployment configuration to update
            
        Returns:
            Result containing the updated deployment configuration
        """
        # Check if the configuration exists
        config_result = await self.config_repository.get_by_id(config.id)
        if not config_result.is_success():
            return config_result
        
        if config_result.value is None:
            return Failure(
                ErrorCode.NOT_FOUND,
                ErrorDetails(
                    message=f"Deployment configuration not found: {config.id.value}",
                    context={"id": config.id.value}
                )
            )
        
        # Update the configuration
        config.updated_at = datetime.now(UTC)
        return await self.config_repository.save(config)
    
    async def delete_config(self, id: DeploymentId) -> Result[bool]:
        """
        Delete a deployment configuration.
        
        Args:
            id: The deployment configuration ID
            
        Returns:
            Result containing True if the configuration was deleted, False otherwise
        """
        return await self.config_repository.delete(id)
    
    async def create_environment_config(
        self, config: DeploymentConfig, environment: DeploymentEnvironment
    ) -> Result[DeploymentConfig]:
        """
        Create a deployment configuration for a specific environment based on an existing configuration.
        
        Args:
            config: The base deployment configuration
            environment: The target environment
            
        Returns:
            Result containing the created deployment configuration
        """
        try:
            # Create a new configuration for the target environment
            new_config = config.for_environment(environment)
            
            # Save the new configuration
            return await self.config_repository.save(new_config)
        except Exception as e:
            self.logger.error(f"Error creating environment configuration: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to create environment configuration: {str(e)}",
                    context={
                        "base_config_id": config.id.value,
                        "environment": environment.value
                    }
                )
            )


class PipelineService(PipelineServiceProtocol):
    """
    Implementation of the deployment pipeline service.
    
    This service provides business logic for managing deployment pipelines.
    """
    
    def __init__(
        self,
        pipeline_repository: PipelineRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            pipeline_repository: Repository for deployment pipelines
            logger: Optional logger instance
        """
        self.pipeline_repository = pipeline_repository
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._task_handlers: Dict[str, Callable[[Dict[str, Any]], bool]] = {}
    
    async def get_pipeline(self, id: PipelineId) -> Result[Optional[Pipeline]]:
        """
        Get a pipeline by ID.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the pipeline if found, None otherwise
        """
        return await self.pipeline_repository.get_by_id(id)
    
    async def get_pipelines_by_deployment_id(self, deployment_id: DeploymentId) -> Result[List[Pipeline]]:
        """
        Get pipelines by deployment ID.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Result containing the list of pipelines
        """
        return await self.pipeline_repository.get_by_deployment_id(deployment_id)
    
    async def get_pipelines_by_status(self, status: DeploymentStatus) -> Result[List[Pipeline]]:
        """
        Get pipelines by status.
        
        Args:
            status: The pipeline status
            
        Returns:
            Result containing the list of pipelines
        """
        return await self.pipeline_repository.get_by_status(status)
    
    async def get_active_pipelines(self) -> Result[List[Pipeline]]:
        """
        Get active (running, rolling back) pipelines.
        
        Returns:
            Result containing the list of active pipelines
        """
        return await self.pipeline_repository.get_active_pipelines()
    
    async def list_pipelines(self) -> Result[List[Pipeline]]:
        """
        List all pipelines.
        
        Returns:
            Result containing the list of all pipelines
        """
        return await self.pipeline_repository.list_all()
    
    async def create_pipeline(
        self,
        name: str,
        description: str,
        deployment_id: DeploymentId
    ) -> Result[Pipeline]:
        """
        Create a new pipeline.
        
        Args:
            name: Pipeline name
            description: Pipeline description
            deployment_id: The deployment ID this pipeline is associated with
            
        Returns:
            Result containing the created pipeline
        """
        try:
            # Create the pipeline
            pipeline = Pipeline(
                id=PipelineId(value=str(uuid.uuid4())),
                name=name,
                description=description,
                stages=[],
                status=DeploymentStatus.PENDING,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            
            # Add deployment ID to context
            pipeline.add_context("deployment_id", deployment_id.value)
            
            # Save the pipeline
            return await self.pipeline_repository.save(pipeline)
        except Exception as e:
            self.logger.error(f"Error creating pipeline: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to create pipeline: {str(e)}",
                    context={
                        "name": name,
                        "deployment_id": deployment_id.value
                    }
                )
            )
    
    async def add_stage(
        self,
        pipeline_id: PipelineId,
        name: str,
        description: str,
        fail_fast: bool = True
    ) -> Result[Stage]:
        """
        Add a stage to a pipeline.
        
        Args:
            pipeline_id: The pipeline ID
            name: Stage name
            description: Stage description
            fail_fast: Whether to fail fast on task failure
            
        Returns:
            Result containing the added stage
        """
        try:
            # Get the pipeline
            pipeline_result = await self.pipeline_repository.get_by_id(pipeline_id)
            if not pipeline_result.is_success():
                return Failure(
                    pipeline_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get pipeline: {pipeline_result.error.message}",
                        context={"id": pipeline_id.value}
                    )
                )
            
            pipeline = pipeline_result.value
            if pipeline is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Pipeline not found: {pipeline_id.value}",
                        context={"id": pipeline_id.value}
                    )
                )
            
            # Check if pipeline is in a valid state for modification
            if pipeline.status != DeploymentStatus.PENDING:
                return Failure(
                    ErrorCode.INVALID_OPERATION,
                    ErrorDetails(
                        message=f"Cannot modify pipeline in status {pipeline.status.value}",
                        context={"id": pipeline_id.value, "status": pipeline.status.value}
                    )
                )
            
            # Create the stage
            stage = Stage(
                id=StageId(value=str(uuid.uuid4())),
                name=name,
                description=description,
                status=StageStatus.PENDING,
                fail_fast=fail_fast,
                tasks=[],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            
            # Add the stage to the pipeline
            pipeline.add_stage(stage)
            pipeline.updated_at = datetime.now(UTC)
            
            # Save the pipeline
            save_result = await self.pipeline_repository.save(pipeline)
            if not save_result.is_success():
                return Failure(
                    save_result.error.code,
                    ErrorDetails(
                        message=f"Failed to save pipeline: {save_result.error.message}",
                        context={"id": pipeline_id.value}
                    )
                )
            
            return Success(stage)
        except Exception as e:
            self.logger.error(f"Error adding stage to pipeline {pipeline_id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to add stage to pipeline: {str(e)}",
                    context={
                        "pipeline_id": pipeline_id.value,
                        "name": name
                    }
                )
            )
    
    async def add_task(
        self,
        pipeline_id: PipelineId,
        stage_id: StageId,
        name: str,
        description: str,
        skip_on_failure: bool = False,
        timeout: Optional[int] = None,
        dependencies: Optional[List[TaskId]] = None
    ) -> Result[Task]:
        """
        Add a task to a stage.
        
        Args:
            pipeline_id: The pipeline ID
            stage_id: The stage ID
            name: Task name
            description: Task description
            skip_on_failure: Whether dependent tasks should be skipped if this task fails
            timeout: Optional timeout in seconds
            dependencies: Optional list of task dependencies
            
        Returns:
            Result containing the added task
        """
        try:
            # Get the pipeline
            pipeline_result = await self.pipeline_repository.get_by_id(pipeline_id)
            if not pipeline_result.is_success():
                return Failure(
                    pipeline_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get pipeline: {pipeline_result.error.message}",
                        context={"id": pipeline_id.value}
                    )
                )
            
            pipeline = pipeline_result.value
            if pipeline is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Pipeline not found: {pipeline_id.value}",
                        context={"id": pipeline_id.value}
                    )
                )
            
            # Check if pipeline is in a valid state for modification
            if pipeline.status != DeploymentStatus.PENDING:
                return Failure(
                    ErrorCode.INVALID_OPERATION,
                    ErrorDetails(
                        message=f"Cannot modify pipeline in status {pipeline.status.value}",
                        context={"id": pipeline_id.value, "status": pipeline.status.value}
                    )
                )
            
            # Find the stage
            stage = None
            for s in pipeline.stages:
                if s.id == stage_id:
                    stage = s
                    break
            
            if stage is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Stage not found: {stage_id.value}",
                        context={"pipeline_id": pipeline_id.value, "stage_id": stage_id.value}
                    )
                )
            
            # Create the task
            task = Task(
                id=TaskId(value=str(uuid.uuid4())),
                name=name,
                description=description,
                status=TaskStatus.PENDING,
                dependencies=dependencies or [],
                skip_on_failure=skip_on_failure,
                timeout=timeout,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            
            # Add the task to the stage
            stage.add_task(task)
            stage.updated_at = datetime.now(UTC)
            pipeline.updated_at = datetime.now(UTC)
            
            # Save the pipeline
            save_result = await self.pipeline_repository.save(pipeline)
            if not save_result.is_success():
                return Failure(
                    save_result.error.code,
                    ErrorDetails(
                        message=f"Failed to save pipeline: {save_result.error.message}",
                        context={"id": pipeline_id.value}
                    )
                )
            
            return Success(task)
        except Exception as e:
            self.logger.error(f"Error adding task to stage {stage_id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to add task to stage: {str(e)}",
                    context={
                        "pipeline_id": pipeline_id.value,
                        "stage_id": stage_id.value,
                        "name": name
                    }
                )
            )
    
    async def start_pipeline(self, id: PipelineId) -> Result[Pipeline]:
        """
        Start a pipeline.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the updated pipeline
        """
        try:
            # Get the pipeline
            pipeline_result = await self.pipeline_repository.get_by_id(id)
            if not pipeline_result.is_success():
                return Failure(
                    pipeline_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get pipeline: {pipeline_result.error.message}",
                        context={"id": id.value}
                    )
                )
            
            pipeline = pipeline_result.value
            if pipeline is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Pipeline not found: {id.value}",
                        context={"id": id.value}
                    )
                )
            
            # Check if pipeline is in a valid state to start
            if pipeline.status != DeploymentStatus.PENDING:
                return Failure(
                    ErrorCode.INVALID_OPERATION,
                    ErrorDetails(
                        message=f"Cannot start pipeline in status {pipeline.status.value}",
                        context={"id": id.value, "status": pipeline.status.value}
                    )
                )
            
            # Start the pipeline
            pipeline.start()
            
            # Save the pipeline
            return await self.pipeline_repository.save(pipeline)
        except Exception as e:
            self.logger.error(f"Error starting pipeline {id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to start pipeline: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def cancel_pipeline(self, id: PipelineId) -> Result[Pipeline]:
        """
        Cancel a pipeline.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the updated pipeline
        """
        try:
            # Get the pipeline
            pipeline_result = await self.pipeline_repository.get_by_id(id)
            if not pipeline_result.is_success():
                return Failure(
                    pipeline_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get pipeline: {pipeline_result.error.message}",
                        context={"id": id.value}
                    )
                )
            
            pipeline = pipeline_result.value
            if pipeline is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Pipeline not found: {id.value}",
                        context={"id": id.value}
                    )
                )
            
            # Check if pipeline is in a valid state to cancel
            if pipeline.status not in [DeploymentStatus.PENDING, DeploymentStatus.RUNNING]:
                return Failure(
                    ErrorCode.INVALID_OPERATION,
                    ErrorDetails(
                        message=f"Cannot cancel pipeline in status {pipeline.status.value}",
                        context={"id": id.value, "status": pipeline.status.value}
                    )
                )
            
            # Cancel the pipeline
            pipeline.cancel()
            
            # Save the pipeline
            return await self.pipeline_repository.save(pipeline)
        except Exception as e:
            self.logger.error(f"Error canceling pipeline {id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to cancel pipeline: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def rollback_pipeline(self, id: PipelineId) -> Result[Pipeline]:
        """
        Roll back a pipeline.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the updated pipeline
        """
        try:
            # Get the pipeline
            pipeline_result = await self.pipeline_repository.get_by_id(id)
            if not pipeline_result.is_success():
                return Failure(
                    pipeline_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get pipeline: {pipeline_result.error.message}",
                        context={"id": id.value}
                    )
                )
            
            pipeline = pipeline_result.value
            if pipeline is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Pipeline not found: {id.value}",
                        context={"id": id.value}
                    )
                )
            
            # Check if pipeline is in a valid state to roll back
            if pipeline.status not in [DeploymentStatus.SUCCEEDED, DeploymentStatus.FAILED]:
                return Failure(
                    ErrorCode.INVALID_OPERATION,
                    ErrorDetails(
                        message=f"Cannot roll back pipeline in status {pipeline.status.value}",
                        context={"id": id.value, "status": pipeline.status.value}
                    )
                )
            
            # Start the rollback
            pipeline.start_rollback()
            
            # Save the pipeline
            save_result = await self.pipeline_repository.save(pipeline)
            if not save_result.is_success():
                return save_result
            
            # Create a new rollback pipeline (not implemented here)
            # This would create a new pipeline with rollback tasks
            
            # Complete the rollback
            pipeline.complete_rollback()
            
            # Save the pipeline again
            return await self.pipeline_repository.save(pipeline)
        except Exception as e:
            self.logger.error(f"Error rolling back pipeline {id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to roll back pipeline: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def update_task_status(
        self,
        pipeline_id: PipelineId,
        stage_id: StageId,
        task_id: TaskId,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Result[Task]:
        """
        Update the status of a task.
        
        Args:
            pipeline_id: The pipeline ID
            stage_id: The stage ID
            task_id: The task ID
            status: The new task status
            result: Optional task result data
            error: Optional error message if task failed
            
        Returns:
            Result containing the updated task
        """
        try:
            # Get the pipeline
            pipeline_result = await self.pipeline_repository.get_by_id(pipeline_id)
            if not pipeline_result.is_success():
                return Failure(
                    pipeline_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get pipeline: {pipeline_result.error.message}",
                        context={"id": pipeline_id.value}
                    )
                )
            
            pipeline = pipeline_result.value
            if pipeline is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Pipeline not found: {pipeline_id.value}",
                        context={"id": pipeline_id.value}
                    )
                )
            
            # Find the stage
            stage = None
            for s in pipeline.stages:
                if s.id == stage_id:
                    stage = s
                    break
            
            if stage is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Stage not found: {stage_id.value}",
                        context={"pipeline_id": pipeline_id.value, "stage_id": stage_id.value}
                    )
                )
            
            # Find the task
            task = None
            for t in stage.tasks:
                if t.id == task_id:
                    task = t
                    break
            
            if task is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Task not found: {task_id.value}",
                        context={
                            "pipeline_id": pipeline_id.value,
                            "stage_id": stage_id.value,
                            "task_id": task_id.value
                        }
                    )
                )
            
            # Update the task status
            if status == TaskStatus.RUNNING:
                task.start()
            elif status == TaskStatus.SUCCEEDED:
                task.succeed(result)
            elif status == TaskStatus.FAILED:
                task.fail(error or "Unknown error")
            elif status == TaskStatus.SKIPPED:
                task.skip()
            
            # Update the pipeline
            pipeline.updated_at = datetime.now(UTC)
            
            # Save the pipeline
            save_result = await self.pipeline_repository.save(pipeline)
            if not save_result.is_success():
                return Failure(
                    save_result.error.code,
                    ErrorDetails(
                        message=f"Failed to save pipeline: {save_result.error.message}",
                        context={"id": pipeline_id.value}
                    )
                )
            
            return Success(task)
        except Exception as e:
            self.logger.error(f"Error updating task status: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to update task status: {str(e)}",
                    context={
                        "pipeline_id": pipeline_id.value,
                        "stage_id": stage_id.value,
                        "task_id": task_id.value,
                        "status": status.value
                    }
                )
            )
    
    async def execute_pipeline(self, id: PipelineId) -> Result[Pipeline]:
        """
        Execute a pipeline.
        
        This method will run the pipeline from start to finish,
        executing all stages and tasks in the appropriate order.
        
        Args:
            id: The pipeline ID
            
        Returns:
            Result containing the executed pipeline
        """
        try:
            # Start the pipeline
            start_result = await self.start_pipeline(id)
            if not start_result.is_success():
                return start_result
            
            pipeline = start_result.value
            
            # Execute each stage
            for stage in pipeline.stages:
                # Start the stage
                stage.start()
                pipeline.updated_at = datetime.now(UTC)
                await self.pipeline_repository.save(pipeline)
                
                # Execute each task in the stage
                stage_success = True
                for task in stage.tasks:
                    # Check if all dependencies are met
                    dependencies_met = True
                    for dep_id in task.dependencies:
                        # Find the dependency task
                        dep_task = None
                        for s in pipeline.stages:
                            for t in s.tasks:
                                if t.id == dep_id:
                                    dep_task = t
                                    break
                            if dep_task:
                                break
                        
                        if dep_task is None or dep_task.status != TaskStatus.SUCCEEDED:
                            dependencies_met = False
                            break
                    
                    if not dependencies_met:
                        # Skip this task
                        task.skip()
                        pipeline.updated_at = datetime.now(UTC)
                        await self.pipeline_repository.save(pipeline)
                        continue
                    
                    # Start the task
                    task.start()
                    pipeline.updated_at = datetime.now(UTC)
                    await self.pipeline_repository.save(pipeline)
                    
                    # Execute the task
                    task_success = False
                    error_message = "Task execution not implemented"
                    
                    # Look up the task handler
                    if task.name in self._task_handlers:
                        try:
                            handler = self._task_handlers[task.name]
                            task_success = handler(pipeline.context)
                            if not task_success:
                                error_message = "Task handler returned failure"
                        except Exception as e:
                            error_message = str(e)
                    
                    # Update the task status
                    if task_success:
                        task.succeed()
                    else:
                        task.fail(error_message)
                        stage_success = False
                        if stage.fail_fast:
                            break
                    
                    pipeline.updated_at = datetime.now(UTC)
                    await self.pipeline_repository.save(pipeline)
                
                # Update the stage status
                if stage_success:
                    stage.succeed()
                else:
                    stage.fail()
                    # If a stage fails, the pipeline fails
                    pipeline.fail()
                    pipeline.updated_at = datetime.now(UTC)
                    await self.pipeline_repository.save(pipeline)
                    return Success(pipeline)
                
                pipeline.updated_at = datetime.now(UTC)
                await self.pipeline_repository.save(pipeline)
            
            # All stages succeeded, so the pipeline succeeded
            pipeline.succeed()
            pipeline.updated_at = datetime.now(UTC)
            return await self.pipeline_repository.save(pipeline)
        except Exception as e:
            self.logger.error(f"Error executing pipeline {id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to execute pipeline: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    def register_task_handler(self, task_name: str, handler: Callable[[Dict[str, Any]], bool]) -> None:
        """
        Register a handler for a task.
        
        Args:
            task_name: The name of the task
            handler: The handler function for the task
        """
        self._task_handlers[task_name] = handler


class DeploymentService(DeploymentServiceProtocol):
    """
    Implementation of the deployment service.
    
    This service provides business logic for deploying applications.
    """
    
    def __init__(
        self,
        config_service: DeploymentConfigServiceProtocol,
        pipeline_service: PipelineServiceProtocol,
        result_repository: DeploymentResultRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            config_service: Service for deployment configurations
            pipeline_service: Service for deployment pipelines
            result_repository: Repository for deployment results
            logger: Optional logger instance
        """
        self.config_service = config_service
        self.pipeline_service = pipeline_service
        self.result_repository = result_repository
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def deploy(
        self,
        config_id: DeploymentId,
        description: Optional[str] = None
    ) -> Result[DeploymentResult]:
        """
        Deploy an application using the specified configuration.
        
        Args:
            config_id: The deployment configuration ID
            description: Optional deployment description
            
        Returns:
            Result containing the deployment result
        """
        try:
            # Get the deployment configuration
            config_result = await self.config_service.get_config(config_id)
            if not config_result.is_success():
                return Failure(
                    config_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get deployment configuration: {config_result.error.message}",
                        context={"id": config_id.value}
                    )
                )
            
            config = config_result.value
            if config is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"Deployment configuration not found: {config_id.value}",
                        context={"id": config_id.value}
                    )
                )
            
            # Create a pipeline for this deployment
            pipeline_name = f"{config.app_name}-{config.environment.value}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
            pipeline_desc = description or f"Deployment pipeline for {config.app_name} to {config.environment.value}"
            
            pipeline_result = await self.pipeline_service.create_pipeline(
                name=pipeline_name,
                description=pipeline_desc,
                deployment_id=config_id
            )
            
            if not pipeline_result.is_success():
                return Failure(
                    pipeline_result.error.code,
                    ErrorDetails(
                        message=f"Failed to create pipeline: {pipeline_result.error.message}",
                        context={"config_id": config_id.value}
                    )
                )
            
            pipeline = pipeline_result.value
            
            # Add stages and tasks to the pipeline based on the configuration
            # This is a simplified example - in a real implementation, you would
            # add stages and tasks based on the configuration details
            
            # Preparation stage
            prep_stage_result = await self.pipeline_service.add_stage(
                pipeline_id=pipeline.id,
                name="preparation",
                description="Prepare for deployment",
                fail_fast=True
            )
            
            if not prep_stage_result.is_success():
                return Failure(
                    prep_stage_result.error.code,
                    ErrorDetails(
                        message=f"Failed to add preparation stage: {prep_stage_result.error.message}",
                        context={"pipeline_id": pipeline.id.value}
                    )
                )
            
            prep_stage = prep_stage_result.value
            
            # Add tasks to preparation stage
            await self.pipeline_service.add_task(
                pipeline_id=pipeline.id,
                stage_id=prep_stage.id,
                name="validate-config",
                description="Validate deployment configuration"
            )
            
            await self.pipeline_service.add_task(
                pipeline_id=pipeline.id,
                stage_id=prep_stage.id,
                name="check-dependencies",
                description="Check deployment dependencies"
            )
            
            # Testing stage (if enabled)
            if (config.testing.run_unit_tests or 
                config.testing.run_integration_tests or
                config.testing.run_performance_tests or
                config.testing.run_security_tests):
                
                test_stage_result = await self.pipeline_service.add_stage(
                    pipeline_id=pipeline.id,
                    name="testing",
                    description="Run tests before deployment",
                    fail_fast=config.testing.fail_on_test_failure
                )
                
                if not test_stage_result.is_success():
                    return Failure(
                        test_stage_result.error.code,
                        ErrorDetails(
                            message=f"Failed to add testing stage: {test_stage_result.error.message}",
                            context={"pipeline_id": pipeline.id.value}
                        )
                    )
                
                test_stage = test_stage_result.value
                
                # Add tasks to testing stage
                if config.testing.run_unit_tests:
                    await self.pipeline_service.add_task(
                        pipeline_id=pipeline.id,
                        stage_id=test_stage.id,
                        name="run-unit-tests",
                        description="Run unit tests"
                    )
                
                if config.testing.run_integration_tests:
                    await self.pipeline_service.add_task(
                        pipeline_id=pipeline.id,
                        stage_id=test_stage.id,
                        name="run-integration-tests",
                        description="Run integration tests"
                    )
                
                if config.testing.run_performance_tests:
                    await self.pipeline_service.add_task(
                        pipeline_id=pipeline.id,
                        stage_id=test_stage.id,
                        name="run-performance-tests",
                        description="Run performance tests"
                    )
                
                if config.testing.run_security_tests:
                    await self.pipeline_service.add_task(
                        pipeline_id=pipeline.id,
                        stage_id=test_stage.id,
                        name="run-security-tests",
                        description="Run security tests"
                    )
            
            # Build stage
            build_stage_result = await self.pipeline_service.add_stage(
                pipeline_id=pipeline.id,
                name="build",
                description="Build application artifacts",
                fail_fast=True
            )
            
            if not build_stage_result.is_success():
                return Failure(
                    build_stage_result.error.code,
                    ErrorDetails(
                        message=f"Failed to add build stage: {build_stage_result.error.message}",
                        context={"pipeline_id": pipeline.id.value}
                    )
                )
            
            build_stage = build_stage_result.value
            
            # Add tasks to build stage
            await self.pipeline_service.add_task(
                pipeline_id=pipeline.id,
                stage_id=build_stage.id,
                name="build-application",
                description="Build application"
            )
            
            if config.platform == DeploymentPlatform.KUBERNETES:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=build_stage.id,
                    name="build-container",
                    description="Build container image"
                )
            
            # Deployment stage
            deploy_stage_result = await self.pipeline_service.add_stage(
                pipeline_id=pipeline.id,
                name="deployment",
                description=f"Deploy to {config.environment.value} environment",
                fail_fast=True
            )
            
            if not deploy_stage_result.is_success():
                return Failure(
                    deploy_stage_result.error.code,
                    ErrorDetails(
                        message=f"Failed to add deployment stage: {deploy_stage_result.error.message}",
                        context={"pipeline_id": pipeline.id.value}
                    )
                )
            
            deploy_stage = deploy_stage_result.value
            
            # Add tasks to deployment stage
            if config.database.backup_before_deploy:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="backup-database",
                    description="Backup database before deployment"
                )
            
            # Add platform-specific deployment tasks
            if config.platform == DeploymentPlatform.KUBERNETES:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="apply-kubernetes-config",
                    description="Apply Kubernetes configuration"
                )
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="deploy-to-kubernetes",
                    description="Deploy to Kubernetes"
                )
            elif config.platform == DeploymentPlatform.AWS:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="deploy-to-aws",
                    description="Deploy to AWS"
                )
            elif config.platform == DeploymentPlatform.AZURE:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="deploy-to-azure",
                    description="Deploy to Azure"
                )
            elif config.platform == DeploymentPlatform.GCP:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="deploy-to-gcp",
                    description="Deploy to Google Cloud Platform"
                )
            elif config.platform == DeploymentPlatform.HEROKU:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="deploy-to-heroku",
                    description="Deploy to Heroku"
                )
            elif config.platform == DeploymentPlatform.DIGITALOCEAN:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="deploy-to-digitalocean",
                    description="Deploy to DigitalOcean"
                )
            elif config.platform == DeploymentPlatform.CUSTOM:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="deploy-custom",
                    description="Deploy using custom method"
                )
            
            # Database migrations (if enabled)
            if config.database.apply_migrations:
                await self.pipeline_service.add_task(
                    pipeline_id=pipeline.id,
                    stage_id=deploy_stage.id,
                    name="apply-migrations",
                    description="Apply database migrations"
                )
            
            # Verification stage
            verify_stage_result = await self.pipeline_service.add_stage(
                pipeline_id=pipeline.id,
                name="verification",
                description="Verify deployment",
                fail_fast=False
            )
            
            if not verify_stage_result.is_success():
                return Failure(
                    verify_stage_result.error.code,
                    ErrorDetails(
                        message=f"Failed to add verification stage: {verify_stage_result.error.message}",
                        context={"pipeline_id": pipeline.id.value}
                    )
                )
            
            verify_stage = verify_stage_result.value
            
            # Add tasks to verification stage
            await self.pipeline_service.add_task(
                pipeline_id=pipeline.id,
                stage_id=verify_stage.id,
                name="verify-deployment",
                description="Verify deployment"
            )
            
            await self.pipeline_service.add_task(
                pipeline_id=pipeline.id,
                stage_id=verify_stage.id,
                name="health-check",
                description="Run health checks"
            )
            
            # Execute the pipeline
            pipeline_result = await self.pipeline_service.execute_pipeline(pipeline.id)
            if not pipeline_result.is_success():
                return Failure(
                    pipeline_result.error.code,
                    ErrorDetails(
                        message=f"Failed to execute pipeline: {pipeline_result.error.message}",
                        context={"pipeline_id": pipeline.id.value}
                    )
                )
            
            pipeline = pipeline_result.value
            
            # Create a deployment result
            deployment_result = DeploymentResult(
                deployment_id=config_id,
                success=pipeline.status == DeploymentStatus.SUCCEEDED,
                message=f"Deployment {'succeeded' if pipeline.status == DeploymentStatus.SUCCEEDED else 'failed'}",
                status=pipeline.status,
                details={
                    "pipeline_id": pipeline.id.value,
                    "duration": pipeline.duration,
                    "success_percentage": pipeline.success_percentage
                }
            )
            
            # Save the deployment result
            save_result = await self.result_repository.save(deployment_result)
            if not save_result.is_success():
                return Failure(
                    save_result.error.code,
                    ErrorDetails(
                        message=f"Failed to save deployment result: {save_result.error.message}",
                        context={"deployment_id": config_id.value}
                    )
                )
            
            return Success(save_result.value)
        except Exception as e:
            self.logger.error(f"Error deploying {config_id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to deploy: {str(e)}",
                    context={"config_id": config_id.value}
                )
            )
    
    async def rollback(
        self,
        deployment_id: DeploymentId
    ) -> Result[DeploymentResult]:
        """
        Roll back a deployment.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Result containing the rollback result
        """
        try:
            # Get the latest deployment result
            result_result = await self.result_repository.get_latest_by_deployment_id(deployment_id)
            if not result_result.is_success():
                return Failure(
                    result_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get deployment result: {result_result.error.message}",
                        context={"deployment_id": deployment_id.value}
                    )
                )
            
            deployment_result = result_result.value
            if deployment_result is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"No deployment result found for deployment {deployment_id.value}",
                        context={"deployment_id": deployment_id.value}
                    )
                )
            
            # Get the pipeline used for the deployment
            pipelines_result = await self.pipeline_service.get_pipelines_by_deployment_id(deployment_id)
            if not pipelines_result.is_success():
                return Failure(
                    pipelines_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get pipelines: {pipelines_result.error.message}",
                        context={"deployment_id": deployment_id.value}
                    )
                )
            
            pipelines = pipelines_result.value
            if not pipelines:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"No pipelines found for deployment {deployment_id.value}",
                        context={"deployment_id": deployment_id.value}
                    )
                )
            
            # Get the original deployment pipeline
            # Assuming the first pipeline is the main deployment pipeline
            pipeline = pipelines[0]
            
            # Roll back the pipeline
            rollback_result = await self.pipeline_service.rollback_pipeline(pipeline.id)
            if not rollback_result.is_success():
                return Failure(
                    rollback_result.error.code,
                    ErrorDetails(
                        message=f"Failed to roll back pipeline: {rollback_result.error.message}",
                        context={"pipeline_id": pipeline.id.value}
                    )
                )
            
            # Create a rollback result
            rollback_deployment_result = DeploymentResult(
                deployment_id=deployment_id,
                success=True,
                message="Deployment rolled back successfully",
                status=DeploymentStatus.ROLLED_BACK,
                details={
                    "pipeline_id": pipeline.id.value,
                    "original_deployment_result_id": deployment_result.id
                }
            )
            
            # Save the rollback result
            save_result = await self.result_repository.save(rollback_deployment_result)
            if not save_result.is_success():
                return Failure(
                    save_result.error.code,
                    ErrorDetails(
                        message=f"Failed to save rollback result: {save_result.error.message}",
                        context={"deployment_id": deployment_id.value}
                    )
                )
            
            return Success(save_result.value)
        except Exception as e:
            self.logger.error(f"Error rolling back deployment {deployment_id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to roll back deployment: {str(e)}",
                    context={"deployment_id": deployment_id.value}
                )
            )
    
    async def get_deployment_status(
        self,
        deployment_id: DeploymentId
    ) -> Result[DeploymentStatus]:
        """
        Get the status of a deployment.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Result containing the deployment status
        """
        try:
            # Get the latest deployment result
            result_result = await self.result_repository.get_latest_by_deployment_id(deployment_id)
            if not result_result.is_success():
                return Failure(
                    result_result.error.code,
                    ErrorDetails(
                        message=f"Failed to get deployment result: {result_result.error.message}",
                        context={"deployment_id": deployment_id.value}
                    )
                )
            
            deployment_result = result_result.value
            if deployment_result is None:
                return Failure(
                    ErrorCode.NOT_FOUND,
                    ErrorDetails(
                        message=f"No deployment result found for deployment {deployment_id.value}",
                        context={"deployment_id": deployment_id.value}
                    )
                )
            
            return Success(deployment_result.status)
        except Exception as e:
            self.logger.error(f"Error getting deployment status {deployment_id.value}: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to get deployment status: {str(e)}",
                    context={"deployment_id": deployment_id.value}
                )
            )
    
    async def get_deployment_result(
        self,
        deployment_id: DeploymentId
    ) -> Result[Optional[DeploymentResult]]:
        """
        Get the result of a deployment.
        
        Args:
            deployment_id: The deployment ID
            
        Returns:
            Result containing the deployment result if available, None otherwise
        """
        return await self.result_repository.get_latest_by_deployment_id(deployment_id)
    
    async def list_deployments(
        self,
        app_name: Optional[str] = None,
        environment: Optional[DeploymentEnvironment] = None,
        status: Optional[DeploymentStatus] = None
    ) -> Result[List[DeploymentResult]]:
        """
        List deployments.
        
        Args:
            app_name: Optional application name to filter by
            environment: Optional environment to filter by
            status: Optional status to filter by
            
        Returns:
            Result containing the list of deployment results
        """
        try:
            # Get all deployment results
            results_result = await self.result_repository.list_all()
            if not results_result.is_success():
                return results_result
            
            results = results_result.value
            
            # Apply filters
            filtered_results = results
            
            if app_name or environment:
                # Need to get the deployment configurations to filter by app_name or environment
                configs_result = await self.config_service.list_configs()
                if not configs_result.is_success():
                    return Failure(
                        configs_result.error.code,
                        ErrorDetails(
                            message=f"Failed to get deployment configurations: {configs_result.error.message}"
                        )
                    )
                
                configs = configs_result.value
                config_map = {config.id.value: config for config in configs}
                
                filtered_results = [
                    result for result in filtered_results
                    if result.deployment_id.value in config_map
                    and (not app_name or config_map[result.deployment_id.value].app_name == app_name)
                    and (not environment or config_map[result.deployment_id.value].environment == environment)
                ]
            
            if status:
                filtered_results = [
                    result for result in filtered_results
                    if result.status == status
                ]
            
            return Success(filtered_results)
        except Exception as e:
            self.logger.error(f"Error listing deployments: {str(e)}")
            return Failure(
                ErrorCode.APPLICATION_ERROR,
                ErrorDetails(
                    message=f"Failed to list deployments: {str(e)}"
                )
            )