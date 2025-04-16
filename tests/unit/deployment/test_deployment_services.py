"""
Tests for the Deployment module domain services.

These tests verify the behavior of the domain services in the Deployment module,
ensuring they meet the business requirements and behave as expected.
"""

import logging
import uuid
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Optional, Any, cast
from datetime import datetime, UTC

from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode, ErrorDetails

from uno.deployment.entities import (
    DeploymentId, PipelineId, StageId, TaskId,
    DeploymentConfig, Pipeline, Stage, Task,
    DeploymentEnvironment, DeploymentPlatform, DeploymentStrategy,
    DeploymentStatus, StageStatus, TaskStatus,
    DatabaseConfig, ResourceRequirements, NetworkConfig, SecurityConfig,
    MonitoringConfig, TestingConfig,
    DeploymentResult
)
from uno.deployment.domain_repositories import (
    DeploymentConfigRepositoryProtocol,
    PipelineRepositoryProtocol,
    DeploymentResultRepositoryProtocol
)
from uno.deployment.domain_services import (
    DeploymentConfigService,
    PipelineService,
    DeploymentService
)


class TestDeploymentConfigService:
    """Tests for the DeploymentConfigService."""

    @pytest.fixture
    def mock_config_repository(self):
        """Create a mock deployment config repository."""
        repo = AsyncMock(spec=DeploymentConfigRepositoryProtocol)
        return repo

    @pytest.fixture
    def service(self, mock_config_repository):
        """Create a deployment config service with a mock repository."""
        return DeploymentConfigService(
            config_repository=mock_config_repository,
            logger=logging.getLogger("test")
        )

    @pytest.mark.asyncio
    async def test_get_config(self, service, mock_config_repository):
        """Test getting a deployment configuration by ID."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        config = DeploymentConfig(
            id=deployment_id,
            app_name="test-app",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        mock_config_repository.get_by_id.return_value = Success(config)

        # Act
        result = await service.get_config(deployment_id)

        # Assert
        assert result.is_success() is True
        assert result.value == config
        mock_config_repository.get_by_id.assert_called_once_with(deployment_id)

    @pytest.mark.asyncio
    async def test_get_configs_by_app_name(self, service, mock_config_repository):
        """Test getting deployment configurations by application name."""
        # Arrange
        app_name = "test-app"
        config1 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name=app_name,
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        config2 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name=app_name,
            app_version="1.0.0",
            environment=DeploymentEnvironment.STAGING,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        configs = [config1, config2]
        mock_config_repository.get_by_app_name.return_value = Success(configs)

        # Act
        result = await service.get_configs_by_app_name(app_name)

        # Assert
        assert result.is_success() is True
        assert result.value == configs
        mock_config_repository.get_by_app_name.assert_called_once_with(app_name)

    @pytest.mark.asyncio
    async def test_get_configs_by_environment(self, service, mock_config_repository):
        """Test getting deployment configurations by environment."""
        # Arrange
        environment = DeploymentEnvironment.DEV
        config1 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name="app1",
            app_version="1.0.0",
            environment=environment,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        config2 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name="app2",
            app_version="1.0.0",
            environment=environment,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        configs = [config1, config2]
        mock_config_repository.get_by_environment.return_value = Success(configs)

        # Act
        result = await service.get_configs_by_environment(environment)

        # Assert
        assert result.is_success() is True
        assert result.value == configs
        mock_config_repository.get_by_environment.assert_called_once_with(environment)

    @pytest.mark.asyncio
    async def test_list_configs(self, service, mock_config_repository):
        """Test listing all deployment configurations."""
        # Arrange
        config1 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name="app1",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        config2 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name="app2",
            app_version="1.0.0",
            environment=DeploymentEnvironment.STAGING,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        configs = [config1, config2]
        mock_config_repository.list_all.return_value = Success(configs)

        # Act
        result = await service.list_configs()

        # Assert
        assert result.is_success() is True
        assert result.value == configs
        mock_config_repository.list_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_config(self, service, mock_config_repository):
        """Test creating a deployment configuration."""
        # Arrange
        app_name = "test-app"
        app_version = "1.0.0"
        environment = DeploymentEnvironment.DEV
        platform = DeploymentPlatform.KUBERNETES
        strategy = DeploymentStrategy.ROLLING
        database_config = {
            "host": "localhost",
            "port": 5432,
            "name": "testdb",
            "user": "testuser"
        }
        resource_requirements = {
            "cpu_min": "100m",
            "cpu_max": "500m",
            "memory_min": "256Mi",
            "memory_max": "512Mi"
        }
        network_config = {
            "domain": "example.com",
            "use_https": True
        }
        security_config = {
            "enable_network_policy": True,
            "pod_security_policy": "restricted"
        }
        monitoring_config = {
            "enable_logging": True,
            "log_level": "INFO"
        }
        testing_config = {
            "run_unit_tests": True,
            "run_integration_tests": True
        }
        custom_settings = {"feature_flag": True}
        environment_variables = {"ENV": "dev"}
        secrets = ["api-key"]
        config_files = ["config.json"]
        
        # Mock the repository to return the saved config
        def mock_save(config):
            return Success(config)
        
        mock_config_repository.save.side_effect = mock_save

        # Act
        result = await service.create_config(
            app_name=app_name,
            app_version=app_version,
            environment=environment,
            platform=platform,
            strategy=strategy,
            database_config=database_config,
            resource_requirements=resource_requirements,
            network_config=network_config,
            security_config=security_config,
            monitoring_config=monitoring_config,
            testing_config=testing_config,
            custom_settings=custom_settings,
            environment_variables=environment_variables,
            secrets=secrets,
            config_files=config_files
        )

        # Assert
        assert result.is_success() is True
        assert isinstance(result.value, DeploymentConfig)
        assert result.value.app_name == app_name
        assert result.value.app_version == app_version
        assert result.value.environment == environment
        assert result.value.platform == platform
        assert result.value.strategy == strategy
        assert result.value.database.host == database_config["host"]
        assert result.value.resources.cpu_min == resource_requirements["cpu_min"]
        assert result.value.network.domain == network_config["domain"]
        assert result.value.security.pod_security_policy == security_config["pod_security_policy"]
        assert result.value.monitoring.log_level == monitoring_config["log_level"]
        assert result.value.testing.run_unit_tests == testing_config["run_unit_tests"]
        assert result.value.custom_settings == custom_settings
        assert result.value.environment_variables == environment_variables
        assert result.value.secrets == secrets
        assert result.value.config_files == config_files
        mock_config_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_config_failure(self, service, mock_config_repository):
        """Test failure when creating a deployment configuration."""
        # Arrange
        mock_config_repository.save.side_effect = Exception("Database error")

        # Act
        result = await service.create_config(
            app_name="test-app",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database_config={"host": "localhost", "name": "testdb", "user": "testuser"},
            resource_requirements={},
            network_config={},
            security_config={},
            monitoring_config={},
            testing_config={}
        )

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.APPLICATION_ERROR
        assert "Failed to create deployment configuration" in result.error.message
        mock_config_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_config(self, service, mock_config_repository):
        """Test updating a deployment configuration."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        config = DeploymentConfig(
            id=deployment_id,
            app_name="test-app",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        
        mock_config_repository.get_by_id.return_value = Success(config)
        mock_config_repository.save.return_value = Success(config)

        # Act
        result = await service.update_config(config)

        # Assert
        assert result.is_success() is True
        assert result.value == config
        mock_config_repository.get_by_id.assert_called_once_with(deployment_id)
        mock_config_repository.save.assert_called_once_with(config)

    @pytest.mark.asyncio
    async def test_update_config_not_found(self, service, mock_config_repository):
        """Test updating a non-existent deployment configuration."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        config = DeploymentConfig(
            id=deployment_id,
            app_name="test-app",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        
        mock_config_repository.get_by_id.return_value = Success(None)

        # Act
        result = await service.update_config(config)

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.NOT_FOUND
        assert f"Deployment configuration not found: {deployment_id.value}" in result.error.message
        mock_config_repository.get_by_id.assert_called_once_with(deployment_id)
        mock_config_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_config(self, service, mock_config_repository):
        """Test deleting a deployment configuration."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        mock_config_repository.delete.return_value = Success(True)

        # Act
        result = await service.delete_config(deployment_id)

        # Assert
        assert result.is_success() is True
        assert result.value is True
        mock_config_repository.delete.assert_called_once_with(deployment_id)

    @pytest.mark.asyncio
    async def test_create_environment_config(self, service, mock_config_repository):
        """Test creating a deployment configuration for a specific environment."""
        # Arrange
        base_config = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name="test-app",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        
        target_environment = DeploymentEnvironment.PRODUCTION

        # Mock the repository to return the saved config
        def mock_save(config):
            return Success(config)
        
        mock_config_repository.save.side_effect = mock_save

        # Act
        result = await service.create_environment_config(base_config, target_environment)

        # Assert
        assert result.is_success() is True
        assert isinstance(result.value, DeploymentConfig)
        assert result.value.id != base_config.id
        assert result.value.app_name == base_config.app_name
        assert result.value.app_version == base_config.app_version
        assert result.value.environment == target_environment
        # Production should change strategy to BLUE_GREEN
        assert result.value.strategy == DeploymentStrategy.BLUE_GREEN
        mock_config_repository.save.assert_called_once()


class TestPipelineService:
    """Tests for the PipelineService."""

    @pytest.fixture
    def mock_pipeline_repository(self):
        """Create a mock pipeline repository."""
        repo = AsyncMock(spec=PipelineRepositoryProtocol)
        return repo

    @pytest.fixture
    def service(self, mock_pipeline_repository):
        """Create a pipeline service with a mock repository."""
        return PipelineService(
            pipeline_repository=mock_pipeline_repository,
            logger=logging.getLogger("test")
        )

    @pytest.mark.asyncio
    async def test_get_pipeline(self, service, mock_pipeline_repository):
        """Test getting a pipeline by ID."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        mock_pipeline_repository.get_by_id.return_value = Success(pipeline)

        # Act
        result = await service.get_pipeline(pipeline_id)

        # Assert
        assert result.is_success() is True
        assert result.value == pipeline
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)

    @pytest.mark.asyncio
    async def test_get_pipelines_by_deployment_id(self, service, mock_pipeline_repository):
        """Test getting pipelines by deployment ID."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        pipeline1 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="pipeline1",
            description="Pipeline 1",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        pipeline2 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="pipeline2",
            description="Pipeline 2",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        pipelines = [pipeline1, pipeline2]
        mock_pipeline_repository.get_by_deployment_id.return_value = Success(pipelines)

        # Act
        result = await service.get_pipelines_by_deployment_id(deployment_id)

        # Assert
        assert result.is_success() is True
        assert result.value == pipelines
        mock_pipeline_repository.get_by_deployment_id.assert_called_once_with(deployment_id)

    @pytest.mark.asyncio
    async def test_get_pipelines_by_status(self, service, mock_pipeline_repository):
        """Test getting pipelines by status."""
        # Arrange
        status = DeploymentStatus.RUNNING
        pipeline1 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="pipeline1",
            description="Pipeline 1",
            stages=[],
            status=status
        )
        pipeline2 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="pipeline2",
            description="Pipeline 2",
            stages=[],
            status=status
        )
        pipelines = [pipeline1, pipeline2]
        mock_pipeline_repository.get_by_status.return_value = Success(pipelines)

        # Act
        result = await service.get_pipelines_by_status(status)

        # Assert
        assert result.is_success() is True
        assert result.value == pipelines
        mock_pipeline_repository.get_by_status.assert_called_once_with(status)

    @pytest.mark.asyncio
    async def test_get_active_pipelines(self, service, mock_pipeline_repository):
        """Test getting active pipelines."""
        # Arrange
        pipeline1 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="pipeline1",
            description="Pipeline 1",
            stages=[],
            status=DeploymentStatus.RUNNING
        )
        pipeline2 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="pipeline2",
            description="Pipeline 2",
            stages=[],
            status=DeploymentStatus.ROLLING_BACK
        )
        pipelines = [pipeline1, pipeline2]
        mock_pipeline_repository.get_active_pipelines.return_value = Success(pipelines)

        # Act
        result = await service.get_active_pipelines()

        # Assert
        assert result.is_success() is True
        assert result.value == pipelines
        mock_pipeline_repository.get_active_pipelines.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_pipelines(self, service, mock_pipeline_repository):
        """Test listing all pipelines."""
        # Arrange
        pipeline1 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="pipeline1",
            description="Pipeline 1",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        pipeline2 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="pipeline2",
            description="Pipeline 2",
            stages=[],
            status=DeploymentStatus.RUNNING
        )
        pipelines = [pipeline1, pipeline2]
        mock_pipeline_repository.list_all.return_value = Success(pipelines)

        # Act
        result = await service.list_pipelines()

        # Assert
        assert result.is_success() is True
        assert result.value == pipelines
        mock_pipeline_repository.list_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pipeline(self, service, mock_pipeline_repository):
        """Test creating a pipeline."""
        # Arrange
        name = "test-pipeline"
        description = "A test pipeline"
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        
        # Mock the repository to return the saved pipeline
        def mock_save(pipeline):
            return Success(pipeline)
        
        mock_pipeline_repository.save.side_effect = mock_save

        # Act
        result = await service.create_pipeline(name, description, deployment_id)

        # Assert
        assert result.is_success() is True
        assert isinstance(result.value, Pipeline)
        assert result.value.name == name
        assert result.value.description == description
        assert result.value.status == DeploymentStatus.PENDING
        assert result.value.get_context("deployment_id") == deployment_id.value
        mock_pipeline_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pipeline_failure(self, service, mock_pipeline_repository):
        """Test failure when creating a pipeline."""
        # Arrange
        mock_pipeline_repository.save.side_effect = Exception("Database error")

        # Act
        result = await service.create_pipeline(
            name="test-pipeline",
            description="A test pipeline",
            deployment_id=DeploymentId(value=str(uuid.uuid4()))
        )

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.APPLICATION_ERROR
        assert "Failed to create pipeline" in result.error.message
        mock_pipeline_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_stage(self, service, mock_pipeline_repository):
        """Test adding a stage to a pipeline."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        
        mock_pipeline_repository.get_by_id.return_value = Success(pipeline)
        mock_pipeline_repository.save.return_value = Success(pipeline)

        # Act
        result = await service.add_stage(
            pipeline_id=pipeline_id,
            name="test-stage",
            description="A test stage",
            fail_fast=True
        )

        # Assert
        assert result.is_success() is True
        assert isinstance(result.value, Stage)
        assert result.value.name == "test-stage"
        assert result.value.description == "A test stage"
        assert result.value.fail_fast is True
        assert result.value.status == StageStatus.PENDING
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_stage_pipeline_not_found(self, service, mock_pipeline_repository):
        """Test adding a stage to a non-existent pipeline."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        mock_pipeline_repository.get_by_id.return_value = Success(None)

        # Act
        result = await service.add_stage(
            pipeline_id=pipeline_id,
            name="test-stage",
            description="A test stage",
            fail_fast=True
        )

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.NOT_FOUND
        assert f"Pipeline not found: {pipeline_id.value}" in result.error.message
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_stage_invalid_pipeline_state(self, service, mock_pipeline_repository):
        """Test adding a stage to a pipeline in an invalid state."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[],
            status=DeploymentStatus.RUNNING  # Running state, not PENDING
        )
        
        mock_pipeline_repository.get_by_id.return_value = Success(pipeline)

        # Act
        result = await service.add_stage(
            pipeline_id=pipeline_id,
            name="test-stage",
            description="A test stage",
            fail_fast=True
        )

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.INVALID_OPERATION
        assert f"Cannot modify pipeline in status {DeploymentStatus.RUNNING.value}" in result.error.message
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_task(self, service, mock_pipeline_repository):
        """Test adding a task to a stage."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        stage_id = StageId(value=str(uuid.uuid4()))
        
        stage = Stage(
            id=stage_id,
            name="test-stage",
            description="A test stage",
            fail_fast=True,
            tasks=[]
        )
        
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[stage],
            status=DeploymentStatus.PENDING
        )
        
        mock_pipeline_repository.get_by_id.return_value = Success(pipeline)
        mock_pipeline_repository.save.return_value = Success(pipeline)

        # Act
        result = await service.add_task(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            name="test-task",
            description="A test task",
            skip_on_failure=False,
            timeout=300
        )

        # Assert
        assert result.is_success() is True
        assert isinstance(result.value, Task)
        assert result.value.name == "test-task"
        assert result.value.description == "A test task"
        assert result.value.skip_on_failure is False
        assert result.value.timeout == 300
        assert result.value.status == TaskStatus.PENDING
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_task_pipeline_not_found(self, service, mock_pipeline_repository):
        """Test adding a task to a non-existent pipeline."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        stage_id = StageId(value=str(uuid.uuid4()))
        
        mock_pipeline_repository.get_by_id.return_value = Success(None)

        # Act
        result = await service.add_task(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            name="test-task",
            description="A test task"
        )

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.NOT_FOUND
        assert f"Pipeline not found: {pipeline_id.value}" in result.error.message
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_task_stage_not_found(self, service, mock_pipeline_repository):
        """Test adding a task to a non-existent stage."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        stage_id = StageId(value=str(uuid.uuid4()))  # Stage ID not in pipeline
        
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[],  # Empty stages list
            status=DeploymentStatus.PENDING
        )
        
        mock_pipeline_repository.get_by_id.return_value = Success(pipeline)

        # Act
        result = await service.add_task(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            name="test-task",
            description="A test task"
        )

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.NOT_FOUND
        assert f"Stage not found: {stage_id.value}" in result.error.message
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_pipeline(self, service, mock_pipeline_repository):
        """Test starting a pipeline."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        
        mock_pipeline_repository.get_by_id.return_value = Success(pipeline)
        mock_pipeline_repository.save.return_value = Success(pipeline)

        # Act
        result = await service.start_pipeline(pipeline_id)

        # Assert
        assert result.is_success() is True
        assert result.value.status == DeploymentStatus.RUNNING
        assert result.value.started_at is not None
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_pipeline_not_found(self, service, mock_pipeline_repository):
        """Test starting a non-existent pipeline."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        mock_pipeline_repository.get_by_id.return_value = Success(None)

        # Act
        result = await service.start_pipeline(pipeline_id)

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.NOT_FOUND
        assert f"Pipeline not found: {pipeline_id.value}" in result.error.message
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_pipeline_invalid_state(self, service, mock_pipeline_repository):
        """Test starting a pipeline in an invalid state."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[],
            status=DeploymentStatus.RUNNING  # Already running
        )
        
        mock_pipeline_repository.get_by_id.return_value = Success(pipeline)

        # Act
        result = await service.start_pipeline(pipeline_id)

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.INVALID_OPERATION
        assert f"Cannot start pipeline in status {DeploymentStatus.RUNNING.value}" in result.error.message
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancel_pipeline(self, service, mock_pipeline_repository):
        """Test canceling a pipeline."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[],
            status=DeploymentStatus.RUNNING
        )
        
        mock_pipeline_repository.get_by_id.return_value = Success(pipeline)
        mock_pipeline_repository.save.return_value = Success(pipeline)

        # Act
        result = await service.cancel_pipeline(pipeline_id)

        # Assert
        assert result.is_success() is True
        assert result.value.status == DeploymentStatus.CANCELED
        assert result.value.completed_at is not None
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_status(self, service, mock_pipeline_repository):
        """Test updating the status of a task."""
        # Arrange
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        stage_id = StageId(value=str(uuid.uuid4()))
        task_id = TaskId(value=str(uuid.uuid4()))
        
        task = Task(
            id=task_id,
            name="test-task",
            description="A test task"
        )
        
        stage = Stage(
            id=stage_id,
            name="test-stage",
            description="A test stage",
            tasks=[task]
        )
        
        pipeline = Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[stage]
        )
        
        mock_pipeline_repository.get_by_id.return_value = Success(pipeline)
        mock_pipeline_repository.save.return_value = Success(pipeline)

        # Act
        result = await service.update_task_status(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            task_id=task_id,
            status=TaskStatus.RUNNING
        )

        # Assert
        assert result.is_success() is True
        assert result.value.status == TaskStatus.RUNNING
        assert result.value.started_at is not None
        mock_pipeline_repository.get_by_id.assert_called_once_with(pipeline_id)
        mock_pipeline_repository.save.assert_called_once()
        
        # Test with SUCCESS status and result
        success_result = {"output": "test output"}
        result = await service.update_task_status(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            task_id=task_id,
            status=TaskStatus.SUCCEEDED,
            result=success_result
        )
        
        assert result.is_success() is True
        assert result.value.status == TaskStatus.SUCCEEDED
        assert result.value.completed_at is not None
        assert result.value.result == success_result
        
        # Test with FAILED status and error
        error_message = "Task failed with error"
        result = await service.update_task_status(
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=error_message
        )
        
        assert result.is_success() is True
        assert result.value.status == TaskStatus.FAILED
        assert result.value.completed_at is not None
        assert result.value.error == error_message


class TestDeploymentService:
    """Tests for the DeploymentService."""

    @pytest.fixture
    def mock_config_service(self):
        """Create a mock deployment config service."""
        service = AsyncMock(spec=DeploymentConfigService)
        return service

    @pytest.fixture
    def mock_pipeline_service(self):
        """Create a mock pipeline service."""
        service = AsyncMock(spec=PipelineService)
        return service

    @pytest.fixture
    def mock_result_repository(self):
        """Create a mock deployment result repository."""
        repo = AsyncMock(spec=DeploymentResultRepositoryProtocol)
        return repo

    @pytest.fixture
    def service(self, mock_config_service, mock_pipeline_service, mock_result_repository):
        """Create a deployment service with mock dependencies."""
        return DeploymentService(
            config_service=mock_config_service,
            pipeline_service=mock_pipeline_service,
            result_repository=mock_result_repository,
            logger=logging.getLogger("test")
        )

    @pytest.mark.asyncio
    async def test_deploy(self, service, mock_config_service, mock_pipeline_service, mock_result_repository):
        """Test deploying an application."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        config = DeploymentConfig(
            id=deployment_id,
            app_name="test-app",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        
        mock_config_service.get_config.return_value = Success(config)
        
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        pipeline = Pipeline(
            id=pipeline_id,
            name=f"{config.app_name}-{config.environment.value}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            description="Deployment pipeline",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        
        mock_pipeline_service.create_pipeline.return_value = Success(pipeline)
        
        # Mock stage creation
        stage_id = StageId(value=str(uuid.uuid4()))
        stage = Stage(
            id=stage_id,
            name="test-stage",
            description="A test stage",
            tasks=[]
        )
        mock_pipeline_service.add_stage.return_value = Success(stage)
        
        # Mock task creation
        task_id = TaskId(value=str(uuid.uuid4()))
        task = Task(
            id=task_id,
            name="test-task",
            description="A test task"
        )
        mock_pipeline_service.add_task.return_value = Success(task)
        
        # Mock pipeline execution
        mock_pipeline_service.execute_pipeline.return_value = Success(pipeline)
        
        # Mock result creation
        deployment_result = DeploymentResult(
            deployment_id=deployment_id,
            success=True,
            message="Deployment succeeded",
            status=DeploymentStatus.SUCCEEDED,
            details={}
        )
        mock_result_repository.save.return_value = Success(deployment_result)

        # Act
        result = await service.deploy(deployment_id, "Test deployment")

        # Assert
        assert result.is_success() is True
        assert isinstance(result.value, DeploymentResult)
        mock_config_service.get_config.assert_called_once_with(deployment_id)
        mock_pipeline_service.create_pipeline.assert_called_once()
        mock_pipeline_service.execute_pipeline.assert_called_once()
        mock_result_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_deploy_config_not_found(self, service, mock_config_service):
        """Test deploying with a non-existent configuration."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        mock_config_service.get_config.return_value = Success(None)

        # Act
        result = await service.deploy(deployment_id)

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.NOT_FOUND
        assert f"Deployment configuration not found: {deployment_id.value}" in result.error.message
        mock_config_service.get_config.assert_called_once_with(deployment_id)

    @pytest.mark.asyncio
    async def test_get_deployment_status(self, service, mock_result_repository):
        """Test getting deployment status."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        deployment_result = DeploymentResult(
            deployment_id=deployment_id,
            success=True,
            message="Deployment succeeded",
            status=DeploymentStatus.SUCCEEDED,
            details={}
        )
        mock_result_repository.get_latest_by_deployment_id.return_value = Success(deployment_result)

        # Act
        result = await service.get_deployment_status(deployment_id)

        # Assert
        assert result.is_success() is True
        assert result.value == DeploymentStatus.SUCCEEDED
        mock_result_repository.get_latest_by_deployment_id.assert_called_once_with(deployment_id)

    @pytest.mark.asyncio
    async def test_get_deployment_status_not_found(self, service, mock_result_repository):
        """Test getting status of a non-existent deployment."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        mock_result_repository.get_latest_by_deployment_id.return_value = Success(None)

        # Act
        result = await service.get_deployment_status(deployment_id)

        # Assert
        assert result.is_success() is False
        assert result.error.code == ErrorCode.NOT_FOUND
        assert f"No deployment result found for deployment {deployment_id.value}" in result.error.message
        mock_result_repository.get_latest_by_deployment_id.assert_called_once_with(deployment_id)

    @pytest.mark.asyncio
    async def test_get_deployment_result(self, service, mock_result_repository):
        """Test getting deployment result."""
        # Arrange
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        deployment_result = DeploymentResult(
            deployment_id=deployment_id,
            success=True,
            message="Deployment succeeded",
            status=DeploymentStatus.SUCCEEDED,
            details={}
        )
        mock_result_repository.get_latest_by_deployment_id.return_value = Success(deployment_result)

        # Act
        result = await service.get_deployment_result(deployment_id)

        # Assert
        assert result.is_success() is True
        assert result.value == deployment_result
        mock_result_repository.get_latest_by_deployment_id.assert_called_once_with(deployment_id)

    @pytest.mark.asyncio
    async def test_list_deployments(self, service, mock_result_repository, mock_config_service):
        """Test listing deployments."""
        # Arrange
        deployment_id1 = DeploymentId(value=str(uuid.uuid4()))
        deployment_id2 = DeploymentId(value=str(uuid.uuid4()))
        
        deployment_result1 = DeploymentResult(
            deployment_id=deployment_id1,
            success=True,
            message="Deployment succeeded",
            status=DeploymentStatus.SUCCEEDED,
            details={}
        )
        
        deployment_result2 = DeploymentResult(
            deployment_id=deployment_id2,
            success=False,
            message="Deployment failed",
            status=DeploymentStatus.FAILED,
            details={}
        )
        
        results = [deployment_result1, deployment_result2]
        mock_result_repository.list_all.return_value = Success(results)

        # Act
        result = await service.list_deployments()

        # Assert
        assert result.is_success() is True
        assert result.value == results
        mock_result_repository.list_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_deployments_with_filters(self, service, mock_result_repository, mock_config_service):
        """Test listing deployments with filters."""
        # Arrange
        deployment_id1 = DeploymentId(value=str(uuid.uuid4()))
        deployment_id2 = DeploymentId(value=str(uuid.uuid4()))
        
        deployment_result1 = DeploymentResult(
            deployment_id=deployment_id1,
            success=True,
            message="Deployment succeeded",
            status=DeploymentStatus.SUCCEEDED,
            details={}
        )
        
        deployment_result2 = DeploymentResult(
            deployment_id=deployment_id2,
            success=False,
            message="Deployment failed",
            status=DeploymentStatus.FAILED,
            details={}
        )
        
        results = [deployment_result1, deployment_result2]
        mock_result_repository.list_all.return_value = Success(results)
        
        # Mock configurations for filtering
        config1 = DeploymentConfig(
            id=deployment_id1,
            app_name="app1",
            app_version="1.0.0",
            environment=DeploymentEnvironment.DEV,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        
        config2 = DeploymentConfig(
            id=deployment_id2,
            app_name="app2",
            app_version="1.0.0",
            environment=DeploymentEnvironment.STAGING,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        
        configs = [config1, config2]
        mock_config_service.list_configs.return_value = Success(configs)

        # Act - filter by app_name
        app_name = "app1"
        result = await service.list_deployments(app_name=app_name)

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 1
        assert result.value[0].deployment_id == deployment_id1
        mock_result_repository.list_all.assert_called_once()
        mock_config_service.list_configs.assert_called_once()
        
        # Reset mocks
        mock_result_repository.list_all.reset_mock()
        mock_config_service.list_configs.reset_mock()
        mock_result_repository.list_all.return_value = Success(results)
        mock_config_service.list_configs.return_value = Success(configs)
        
        # Act - filter by environment
        environment = DeploymentEnvironment.STAGING
        result = await service.list_deployments(environment=environment)
        
        # Assert
        assert result.is_success() is True
        assert len(result.value) == 1
        assert result.value[0].deployment_id == deployment_id2
        mock_result_repository.list_all.assert_called_once()
        mock_config_service.list_configs.assert_called_once()
        
        # Reset mocks
        mock_result_repository.list_all.reset_mock()
        mock_config_service.list_configs.reset_mock()
        mock_result_repository.list_all.return_value = Success(results)
        
        # Act - filter by status
        status = DeploymentStatus.SUCCEEDED
        result = await service.list_deployments(status=status)
        
        # Assert
        assert result.is_success() is True
        assert len(result.value) == 1
        assert result.value[0].status == DeploymentStatus.SUCCEEDED
        mock_result_repository.list_all.assert_called_once()
        mock_config_service.list_configs.assert_not_called()  # No need to fetch configs for status filtering