"""
Tests for the Deployment module domain repositories.

These tests verify the behavior of the domain repositories in the Deployment module,
ensuring they meet the business requirements and behave as expected.
"""

import os
import uuid
import pytest
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, cast
from unittest.mock import Mock, patch, AsyncMock

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
    InMemoryDeploymentConfigRepository,
    InMemoryPipelineRepository,
    InMemoryDeploymentResultRepository,
)


class TestInMemoryDeploymentConfigRepository:
    """Tests for the InMemoryDeploymentConfigRepository."""

    @pytest.fixture
    def repository(self):
        """Create an in-memory deployment config repository."""
        return InMemoryDeploymentConfigRepository()

    @pytest.fixture
    def config(self):
        """Create a sample deployment configuration."""
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        return DeploymentConfig(
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

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository, config):
        """Test saving a configuration and retrieving it by ID."""
        # Arrange & Act
        save_result = await repository.save(config)
        get_result = await repository.get_by_id(config.id)

        # Assert
        assert save_result.is_success() is True
        assert get_result.is_success() is True
        assert get_result.value == config

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository):
        """Test getting a non-existent configuration by ID."""
        # Arrange
        non_existent_id = DeploymentId(value=str(uuid.uuid4()))

        # Act
        result = await repository.get_by_id(non_existent_id)

        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_get_by_app_name(self, repository, config):
        """Test getting configurations by application name."""
        # Arrange
        await repository.save(config)

        # Create another config with the same app name but different environment
        config2 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name=config.app_name,
            app_version="1.1.0",
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
        await repository.save(config2)

        # Create another config with a different app name
        config3 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name="other-app",
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
        await repository.save(config3)

        # Act
        result = await repository.get_by_app_name(config.app_name)

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 2
        assert config.id in [c.id for c in result.value]
        assert config2.id in [c.id for c in result.value]
        assert config3.id not in [c.id for c in result.value]

    @pytest.mark.asyncio
    async def test_get_by_environment(self, repository, config):
        """Test getting configurations by environment."""
        # Arrange
        await repository.save(config)

        # Create another config with the same environment but different app name
        config2 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name="other-app",
            app_version="1.0.0",
            environment=config.environment,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        await repository.save(config2)

        # Create another config with a different environment
        config3 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name="test-app",
            app_version="1.0.0",
            environment=DeploymentEnvironment.PRODUCTION,
            platform=DeploymentPlatform.KUBERNETES,
            strategy=DeploymentStrategy.ROLLING,
            database=DatabaseConfig(host="localhost", name="testdb", user="testuser"),
            resources=ResourceRequirements(),
            network=NetworkConfig(),
            security=SecurityConfig(),
            monitoring=MonitoringConfig(),
            testing=TestingConfig()
        )
        await repository.save(config3)

        # Act
        result = await repository.get_by_environment(config.environment)

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 2
        assert config.id in [c.id for c in result.value]
        assert config2.id in [c.id for c in result.value]
        assert config3.id not in [c.id for c in result.value]

    @pytest.mark.asyncio
    async def test_list_all(self, repository, config):
        """Test listing all configurations."""
        # Arrange
        await repository.save(config)

        # Create another config
        config2 = DeploymentConfig(
            id=DeploymentId(value=str(uuid.uuid4())),
            app_name="other-app",
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
        await repository.save(config2)

        # Act
        result = await repository.list_all()

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 2
        assert config.id in [c.id for c in result.value]
        assert config2.id in [c.id for c in result.value]

    @pytest.mark.asyncio
    async def test_delete(self, repository, config):
        """Test deleting a configuration."""
        # Arrange
        await repository.save(config)

        # Act
        result = await repository.delete(config.id)
        get_result = await repository.get_by_id(config.id)

        # Assert
        assert result.is_success() is True
        assert result.value is True
        assert get_result.value is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository):
        """Test deleting a non-existent configuration."""
        # Arrange
        non_existent_id = DeploymentId(value=str(uuid.uuid4()))

        # Act
        result = await repository.delete(non_existent_id)

        # Assert
        assert result.is_success() is True
        assert result.value is False


class TestInMemoryPipelineRepository:
    """Tests for the InMemoryPipelineRepository."""

    @pytest.fixture
    def repository(self):
        """Create an in-memory pipeline repository."""
        return InMemoryPipelineRepository()

    @pytest.fixture
    def pipeline(self):
        """Create a sample pipeline."""
        pipeline_id = PipelineId(value=str(uuid.uuid4()))
        return Pipeline(
            id=pipeline_id,
            name="test-pipeline",
            description="A test pipeline",
            stages=[],
            status=DeploymentStatus.PENDING
        )

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository, pipeline):
        """Test saving a pipeline and retrieving it by ID."""
        # Arrange & Act
        save_result = await repository.save(pipeline)
        get_result = await repository.get_by_id(pipeline.id)

        # Assert
        assert save_result.is_success() is True
        assert get_result.is_success() is True
        assert get_result.value == pipeline

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository):
        """Test getting a non-existent pipeline by ID."""
        # Arrange
        non_existent_id = PipelineId(value=str(uuid.uuid4()))

        # Act
        result = await repository.get_by_id(non_existent_id)

        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_get_by_deployment_id(self, repository, pipeline):
        """Test getting pipelines by deployment ID."""
        # Arrange
        deployment_id = str(uuid.uuid4())
        pipeline.add_context("deployment_id", deployment_id)
        await repository.save(pipeline)

        # Create another pipeline with the same deployment ID
        pipeline2 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="test-pipeline-2",
            description="Another test pipeline",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        pipeline2.add_context("deployment_id", deployment_id)
        await repository.save(pipeline2)

        # Create another pipeline with a different deployment ID
        pipeline3 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="test-pipeline-3",
            description="Yet another test pipeline",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        pipeline3.add_context("deployment_id", str(uuid.uuid4()))
        await repository.save(pipeline3)

        # Act
        result = await repository.get_by_deployment_id(DeploymentId(value=deployment_id))

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 2
        assert pipeline.id in [p.id for p in result.value]
        assert pipeline2.id in [p.id for p in result.value]
        assert pipeline3.id not in [p.id for p in result.value]

    @pytest.mark.asyncio
    async def test_get_by_status(self, repository, pipeline):
        """Test getting pipelines by status."""
        # Arrange
        status = DeploymentStatus.RUNNING
        pipeline.status = status
        await repository.save(pipeline)

        # Create another pipeline with the same status
        pipeline2 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="test-pipeline-2",
            description="Another test pipeline",
            stages=[],
            status=status
        )
        await repository.save(pipeline2)

        # Create another pipeline with a different status
        pipeline3 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="test-pipeline-3",
            description="Yet another test pipeline",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        await repository.save(pipeline3)

        # Act
        result = await repository.get_by_status(status)

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 2
        assert pipeline.id in [p.id for p in result.value]
        assert pipeline2.id in [p.id for p in result.value]
        assert pipeline3.id not in [p.id for p in result.value]

    @pytest.mark.asyncio
    async def test_get_active_pipelines(self, repository, pipeline):
        """Test getting active pipelines."""
        # Arrange
        pipeline.status = DeploymentStatus.RUNNING
        await repository.save(pipeline)

        # Create another active pipeline
        pipeline2 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="test-pipeline-2",
            description="Another test pipeline",
            stages=[],
            status=DeploymentStatus.ROLLING_BACK
        )
        await repository.save(pipeline2)

        # Create an inactive pipeline
        pipeline3 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="test-pipeline-3",
            description="Yet another test pipeline",
            stages=[],
            status=DeploymentStatus.SUCCEEDED
        )
        await repository.save(pipeline3)

        # Act
        result = await repository.get_active_pipelines()

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 2
        assert pipeline.id in [p.id for p in result.value]
        assert pipeline2.id in [p.id for p in result.value]
        assert pipeline3.id not in [p.id for p in result.value]

    @pytest.mark.asyncio
    async def test_list_all(self, repository, pipeline):
        """Test listing all pipelines."""
        # Arrange
        await repository.save(pipeline)

        # Create another pipeline
        pipeline2 = Pipeline(
            id=PipelineId(value=str(uuid.uuid4())),
            name="test-pipeline-2",
            description="Another test pipeline",
            stages=[],
            status=DeploymentStatus.PENDING
        )
        await repository.save(pipeline2)

        # Act
        result = await repository.list_all()

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 2
        assert pipeline.id in [p.id for p in result.value]
        assert pipeline2.id in [p.id for p in result.value]

    @pytest.mark.asyncio
    async def test_delete(self, repository, pipeline):
        """Test deleting a pipeline."""
        # Arrange
        deployment_id = str(uuid.uuid4())
        pipeline.add_context("deployment_id", deployment_id)
        await repository.save(pipeline)

        # Act
        result = await repository.delete(pipeline.id)
        get_result = await repository.get_by_id(pipeline.id)
        deployment_result = await repository.get_by_deployment_id(DeploymentId(value=deployment_id))

        # Assert
        assert result.is_success() is True
        assert result.value is True
        assert get_result.value is None
        assert len(deployment_result.value) == 0

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository):
        """Test deleting a non-existent pipeline."""
        # Arrange
        non_existent_id = PipelineId(value=str(uuid.uuid4()))

        # Act
        result = await repository.delete(non_existent_id)

        # Assert
        assert result.is_success() is True
        assert result.value is False


class TestInMemoryDeploymentResultRepository:
    """Tests for the InMemoryDeploymentResultRepository."""

    @pytest.fixture
    def repository(self):
        """Create an in-memory deployment result repository."""
        return InMemoryDeploymentResultRepository()

    @pytest.fixture
    def deployment_result(self):
        """Create a sample deployment result."""
        deployment_id = DeploymentId(value=str(uuid.uuid4()))
        return DeploymentResult(
            deployment_id=deployment_id,
            success=True,
            message="Deployment succeeded",
            status=DeploymentStatus.SUCCEEDED,
            details={"duration": 120}
        )

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository, deployment_result):
        """Test saving a deployment result and retrieving it by ID."""
        # Arrange & Act
        save_result = await repository.save(deployment_result)
        get_result = await repository.get_by_id(deployment_result.id)

        # Assert
        assert save_result.is_success() is True
        assert get_result.is_success() is True
        assert get_result.value == deployment_result

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository):
        """Test getting a non-existent deployment result by ID."""
        # Arrange
        non_existent_id = str(uuid.uuid4())

        # Act
        result = await repository.get_by_id(non_existent_id)

        # Assert
        assert result.is_success() is True
        assert result.value is None

    @pytest.mark.asyncio
    async def test_get_by_deployment_id(self, repository, deployment_result):
        """Test getting deployment results by deployment ID."""
        # Arrange
        await repository.save(deployment_result)

        # Create another result for the same deployment
        result2 = DeploymentResult(
            deployment_id=deployment_result.deployment_id,
            success=False,
            message="Deployment failed",
            status=DeploymentStatus.FAILED,
            details={"error": "Connection timeout"}
        )
        await repository.save(result2)

        # Create a result for a different deployment
        different_deployment_id = DeploymentId(value=str(uuid.uuid4()))
        result3 = DeploymentResult(
            deployment_id=different_deployment_id,
            success=True,
            message="Deployment succeeded",
            status=DeploymentStatus.SUCCEEDED,
            details={}
        )
        await repository.save(result3)

        # Act
        result = await repository.get_by_deployment_id(deployment_result.deployment_id)

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 2
        assert deployment_result.id in [r.id for r in result.value]
        assert result2.id in [r.id for r in result.value]
        assert result3.id not in [r.id for r in result.value]

    @pytest.mark.asyncio
    async def test_get_latest_by_deployment_id(self, repository, deployment_result):
        """Test getting the latest deployment result by deployment ID."""
        # Arrange
        await repository.save(deployment_result)

        # Create a newer result for the same deployment
        newer_result = DeploymentResult(
            deployment_id=deployment_result.deployment_id,
            success=False,
            message="Deployment failed",
            status=DeploymentStatus.FAILED,
            details={"error": "Connection timeout"}
        )
        
        # Manually set created_at to a later time
        # Note: This is simplified for testing purposes; in reality, the newer result
        # would naturally have a later creation time
        newer_result.created_at = datetime.now(UTC)
        
        await repository.save(newer_result)

        # Act
        result = await repository.get_latest_by_deployment_id(deployment_result.deployment_id)

        # Assert
        assert result.is_success() is True
        assert result.value.id == newer_result.id

    @pytest.mark.asyncio
    async def test_list_all(self, repository, deployment_result):
        """Test listing all deployment results."""
        # Arrange
        await repository.save(deployment_result)

        # Create another result
        result2 = DeploymentResult(
            deployment_id=DeploymentId(value=str(uuid.uuid4())),
            success=False,
            message="Deployment failed",
            status=DeploymentStatus.FAILED,
            details={"error": "Connection timeout"}
        )
        await repository.save(result2)

        # Act
        result = await repository.list_all()

        # Assert
        assert result.is_success() is True
        assert len(result.value) == 2
        assert deployment_result.id in [r.id for r in result.value]
        assert result2.id in [r.id for r in result.value]

    @pytest.mark.asyncio
    async def test_delete(self, repository, deployment_result):
        """Test deleting a deployment result."""
        # Arrange
        await repository.save(deployment_result)

        # Act
        result = await repository.delete(deployment_result.id)
        get_result = await repository.get_by_id(deployment_result.id)
        deployment_results = await repository.get_by_deployment_id(deployment_result.deployment_id)

        # Assert
        assert result.is_success() is True
        assert result.value is True
        assert get_result.value is None
        assert len(deployment_results.value) == 0

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository):
        """Test deleting a non-existent deployment result."""
        # Arrange
        non_existent_id = str(uuid.uuid4())

        # Act
        result = await repository.delete(non_existent_id)

        # Assert
        assert result.is_success() is True
        assert result.value is False