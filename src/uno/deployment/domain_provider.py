"""
Domain provider for the Deployment module.

This module configures dependency injection for the Deployment module,
providing factory functions for repositories and services.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Any, Dict, List, Union

import inject

from uno.dependencies.interfaces import ProviderProtocol
from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode, ErrorDetails

from uno.deployment.entities import (
    DeploymentId, PipelineId, StageId, TaskId, StrategyId,
    DeploymentConfig, Pipeline, Stage, Task,
    DeploymentEnvironment, DeploymentPlatform, DeploymentStrategy,
    DeploymentStatus, StageStatus, TaskStatus,
    DeploymentResult
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


class DeploymentProvider(ProviderProtocol):
    """
    Provider for deployment dependencies.
    
    This class configures dependency injection for the Deployment module,
    providing factory functions for repositories and services.
    """
    
    def __init__(
        self,
        config_file_path: Optional[Union[str, Path]] = None,
        use_in_memory: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the provider.
        
        Args:
            config_file_path: Optional path to deployment config files
            use_in_memory: Whether to use in-memory repositories
            logger: Optional logger instance
        """
        self.config_file_path = Path(config_file_path) if config_file_path else None
        self.use_in_memory = use_in_memory
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def configure(self, binder: inject.Binder) -> None:
        """
        Configure dependency injection bindings.
        
        Args:
            binder: The inject binder
        """
        # Bind repository implementations
        if self.use_in_memory:
            # Use in-memory repositories
            binder.bind_to_provider(
                DeploymentConfigRepositoryProtocol,
                self._provide_in_memory_config_repository
            )
            binder.bind_to_provider(
                PipelineRepositoryProtocol,
                self._provide_in_memory_pipeline_repository
            )
            binder.bind_to_provider(
                DeploymentResultRepositoryProtocol,
                self._provide_in_memory_result_repository
            )
        else:
            # Use file system repositories
            binder.bind_to_provider(
                DeploymentConfigRepositoryProtocol,
                self._provide_file_system_config_repository
            )
            # There are no file system implementations for pipeline and result repositories yet
            binder.bind_to_provider(
                PipelineRepositoryProtocol,
                self._provide_in_memory_pipeline_repository
            )
            binder.bind_to_provider(
                DeploymentResultRepositoryProtocol,
                self._provide_in_memory_result_repository
            )
        
        # Bind service implementations
        binder.bind_to_provider(
            DeploymentConfigServiceProtocol,
            self._provide_config_service
        )
        binder.bind_to_provider(
            PipelineServiceProtocol,
            self._provide_pipeline_service
        )
        binder.bind_to_provider(
            DeploymentServiceProtocol,
            self._provide_deployment_service
        )
    
    def _provide_in_memory_config_repository(self) -> DeploymentConfigRepositoryProtocol:
        """
        Provide an in-memory deployment configuration repository.
        
        Returns:
            An in-memory deployment configuration repository
        """
        return InMemoryDeploymentConfigRepository(logger=self.logger)
    
    def _provide_in_memory_pipeline_repository(self) -> PipelineRepositoryProtocol:
        """
        Provide an in-memory pipeline repository.
        
        Returns:
            An in-memory pipeline repository
        """
        return InMemoryPipelineRepository(logger=self.logger)
    
    def _provide_in_memory_result_repository(self) -> DeploymentResultRepositoryProtocol:
        """
        Provide an in-memory deployment result repository.
        
        Returns:
            An in-memory deployment result repository
        """
        return InMemoryDeploymentResultRepository(logger=self.logger)
    
    def _provide_file_system_config_repository(self) -> DeploymentConfigRepositoryProtocol:
        """
        Provide a file system deployment configuration repository.
        
        Returns:
            A file system deployment configuration repository
        """
        if not self.config_file_path:
            # Default to a "deployments" directory in the current working directory
            base_dir = Path.cwd() / "deployments"
        else:
            base_dir = self.config_file_path
        
        return FileSystemDeploymentConfigRepository(base_dir=base_dir, logger=self.logger)
    
    def _provide_config_service(self) -> DeploymentConfigServiceProtocol:
        """
        Provide a deployment configuration service.
        
        Returns:
            A deployment configuration service
        """
        config_repository = inject.instance(DeploymentConfigRepositoryProtocol)
        return DeploymentConfigService(config_repository=config_repository, logger=self.logger)
    
    def _provide_pipeline_service(self) -> PipelineServiceProtocol:
        """
        Provide a pipeline service.
        
        Returns:
            A pipeline service
        """
        pipeline_repository = inject.instance(PipelineRepositoryProtocol)
        return PipelineService(pipeline_repository=pipeline_repository, logger=self.logger)
    
    def _provide_deployment_service(self) -> DeploymentServiceProtocol:
        """
        Provide a deployment service.
        
        Returns:
            A deployment service
        """
        config_service = inject.instance(DeploymentConfigServiceProtocol)
        pipeline_service = inject.instance(PipelineServiceProtocol)
        result_repository = inject.instance(DeploymentResultRepositoryProtocol)
        
        return DeploymentService(
            config_service=config_service,
            pipeline_service=pipeline_service,
            result_repository=result_repository,
            logger=self.logger
        )