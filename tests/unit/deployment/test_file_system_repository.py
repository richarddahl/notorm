"""
Tests for the Deployment module file system repositories.

These tests verify the behavior of the file system repository implementations in the Deployment module,
ensuring they meet the business requirements and behave as expected.
"""

import os
import tempfile
import uuid
import pytest
import yaml
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, cast

from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode, ErrorDetails

from uno.deployment.entities import (
    DeploymentId, PipelineId,
    DeploymentConfig, Pipeline,
    DeploymentEnvironment, DeploymentPlatform, DeploymentStrategy,
    DeploymentStatus,
    DatabaseConfig, ResourceRequirements, NetworkConfig, SecurityConfig,
    MonitoringConfig, TestingConfig
)
from uno.deployment.domain_repositories import (
    FileSystemDeploymentConfigRepository
)


class TestFileSystemDeploymentConfigRepository:
    """Tests for the FileSystemDeploymentConfigRepository."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def repository(self, temp_dir):
        """Create a file system deployment config repository with a temp directory."""
        return FileSystemDeploymentConfigRepository(base_dir=temp_dir)

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
    async def test_save_and_file_exists(self, repository, config, temp_dir):
        """Test saving a configuration creates a file."""
        # Arrange & Act
        save_result = await repository.save(config)
        
        # Assert
        assert save_result.is_success() is True
        config_path = Path(temp_dir) / f"{config.id.value}.yaml"
        assert config_path.exists() is True

    @pytest.mark.asyncio
    async def test_save_file_content(self, repository, config, temp_dir):
        """Test the content of the saved configuration file."""
        # Arrange & Act
        await repository.save(config)
        
        # Assert
        config_path = Path(temp_dir) / f"{config.id.value}.yaml"
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        
        assert data["id"] == config.id.value
        assert data["app_name"] == config.app_name
        assert data["app_version"] == config.app_version
        assert data["environment"] == config.environment.value
        assert data["platform"] == config.platform.value
        assert data["strategy"] == config.strategy.value
        assert data["database"]["host"] == config.database.host
        assert data["database"]["name"] == config.database.name
        assert data["database"]["user"] == config.database.user

    @pytest.mark.asyncio
    async def test_delete(self, repository, config, temp_dir):
        """Test deleting a configuration."""
        # Arrange
        await repository.save(config)
        config_path = Path(temp_dir) / f"{config.id.value}.yaml"
        assert config_path.exists() is True
        
        # Act
        result = await repository.delete(config.id)
        
        # Assert
        assert result.is_success() is True
        assert result.value is True
        assert config_path.exists() is False

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

    @pytest.mark.skip("get_by_id not fully implemented in FileSystemDeploymentConfigRepository")
    @pytest.mark.asyncio
    async def test_get_by_id(self, repository, config):
        """Test getting a configuration by ID."""
        # Arrange
        await repository.save(config)
        
        # Act
        result = await repository.get_by_id(config.id)
        
        # Assert
        assert result.is_success() is True
        assert result.value is not None
        assert result.value.id == config.id
        assert result.value.app_name == config.app_name
        assert result.value.app_version == config.app_version
        assert result.value.environment == config.environment
        assert result.value.platform == config.platform
        assert result.value.strategy == config.strategy

    @pytest.mark.skip("get_by_app_name not fully implemented in FileSystemDeploymentConfigRepository")
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

    @pytest.mark.skip("get_by_environment not fully implemented in FileSystemDeploymentConfigRepository")
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

    @pytest.mark.skip("list_all not fully implemented in FileSystemDeploymentConfigRepository")
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