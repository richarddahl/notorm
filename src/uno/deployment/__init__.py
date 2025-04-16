"""
Uno Deployment Framework.

This module provides a comprehensive deployment pipeline for Uno applications,
including CI/CD integration, blue-green deployment support, and deployment
templates for various platforms.
"""

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
    DeploymentResultRepositoryProtocol,
    InMemoryDeploymentConfigRepository,
    InMemoryPipelineRepository,
    InMemoryDeploymentResultRepository,
    FileSystemDeploymentConfigRepository
)

from uno.deployment.domain_services import (
    DeploymentConfigServiceProtocol,
    PipelineServiceProtocol,
    DeploymentServiceProtocol,
    DeploymentConfigService,
    PipelineService,
    DeploymentService
)

from uno.deployment.domain_provider import DeploymentProvider
from uno.deployment.domain_endpoints import create_deployment_endpoints

# Legacy imports for backward compatibility
# These will be removed in a future version
from uno.deployment.manager import DeploymentManager
from uno.deployment.pipeline import Pipeline as LegacyPipeline, Stage as LegacyStage, Task as LegacyTask

__version__ = "0.2.0"

__all__ = [
    # Entities
    "DeploymentId", "PipelineId", "StageId", "TaskId", "StrategyId",
    "DeploymentConfig", "Pipeline", "Stage", "Task",
    "DeploymentEnvironment", "DeploymentPlatform", "DeploymentStrategy",
    "DeploymentStatus", "StageStatus", "TaskStatus",
    "DeploymentResult",
    "DatabaseConfig", "ResourceRequirements", "NetworkConfig", "SecurityConfig",
    "MonitoringConfig", "TestingConfig",
    
    # Repositories
    "DeploymentConfigRepositoryProtocol",
    "PipelineRepositoryProtocol",
    "DeploymentResultRepositoryProtocol",
    "InMemoryDeploymentConfigRepository",
    "InMemoryPipelineRepository",
    "InMemoryDeploymentResultRepository",
    "FileSystemDeploymentConfigRepository",
    
    # Services
    "DeploymentConfigServiceProtocol",
    "PipelineServiceProtocol",
    "DeploymentServiceProtocol",
    "DeploymentConfigService",
    "PipelineService",
    "DeploymentService",
    
    # Provider
    "DeploymentProvider",
    
    # Endpoints
    "create_deployment_endpoints",
    
    # Legacy
    "DeploymentManager",
    "LegacyPipeline",
    "LegacyStage",
    "LegacyTask"
]