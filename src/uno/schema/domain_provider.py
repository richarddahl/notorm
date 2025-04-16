# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain provider for the Schema module.

This module provides dependency injection configuration for the Schema module,
registering repositories and services.
"""

import logging
from pathlib import Path
from typing import Optional, Type

import inject

from uno.core.errors.result import Result, Success, Failure, ErrorDetails
from uno.schema.domain_repositories import (
    SchemaDefinitionRepositoryProtocol,
    SchemaConfigurationRepositoryProtocol,
    InMemorySchemaDefinitionRepository,
    InMemorySchemaConfigurationRepository,
    FileSchemaDefinitionRepository,
    FileSchemaConfigurationRepository
)
from uno.schema.domain_services import (
    SchemaManagerServiceProtocol,
    SchemaValidationServiceProtocol,
    SchemaTransformationServiceProtocol,
    SchemaManagerService,
    SchemaValidationService,
    SchemaTransformationService
)


class SchemaProvider:
    """Dependency provider for the Schema module."""
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        use_file_storage: bool = False,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the schema provider.
        
        Args:
            storage_path: Optional path for file-based storage
            use_file_storage: Whether to use file-based storage instead of in-memory
            logger: Optional logger
        """
        self.storage_path = storage_path
        self.use_file_storage = use_file_storage
        self.logger = logger or logging.getLogger(__name__)
        
        # Create storage path if using file storage and path provided
        if use_file_storage and storage_path:
            storage_path.mkdir(parents=True, exist_ok=True)
    
    def configure(self) -> None:
        """Configure dependency injection for the Schema module."""
        def config(binder: inject.Binder) -> None:
            # Bind repositories
            if self.use_file_storage and self.storage_path:
                self.logger.info("Using file-based storage for Schema module")
                binder.bind(
                    SchemaDefinitionRepositoryProtocol,
                    FileSchemaDefinitionRepository(self.storage_path)
                )
                binder.bind(
                    SchemaConfigurationRepositoryProtocol,
                    FileSchemaConfigurationRepository(self.storage_path)
                )
            else:
                self.logger.info("Using in-memory storage for Schema module")
                binder.bind(
                    SchemaDefinitionRepositoryProtocol,
                    InMemorySchemaDefinitionRepository()
                )
                binder.bind(
                    SchemaConfigurationRepositoryProtocol,
                    InMemorySchemaConfigurationRepository()
                )
            
            # Bind services
            binder.bind(
                SchemaManagerServiceProtocol,
                SchemaManagerService(
                    schema_repository=inject.instance(SchemaDefinitionRepositoryProtocol),
                    config_repository=inject.instance(SchemaConfigurationRepositoryProtocol),
                    logger=self.logger
                )
            )
            binder.bind(
                SchemaValidationServiceProtocol,
                SchemaValidationService(
                    schema_repository=inject.instance(SchemaDefinitionRepositoryProtocol),
                    logger=self.logger
                )
            )
            binder.bind(
                SchemaTransformationServiceProtocol,
                SchemaTransformationService(
                    schema_repository=inject.instance(SchemaDefinitionRepositoryProtocol),
                    logger=self.logger
                )
            )
        
        inject.configure(config)
    
    def register_standard_configurations(self) -> Result[None, ErrorDetails]:
        """
        Register standard schema configurations.
        
        Returns:
            Result indicating success or failure
        """
        schema_manager = inject.instance(SchemaManagerServiceProtocol)
        return schema_manager.register_standard_configurations()
    
    @staticmethod
    def get_schema_manager() -> SchemaManagerServiceProtocol:
        """
        Get the schema manager service instance.
        
        Returns:
            The schema manager service instance
        """
        return inject.instance(SchemaManagerServiceProtocol)
    
    @staticmethod
    def get_schema_validation() -> SchemaValidationServiceProtocol:
        """
        Get the schema validation service instance.
        
        Returns:
            The schema validation service instance
        """
        return inject.instance(SchemaValidationServiceProtocol)
    
    @staticmethod
    def get_schema_transformation() -> SchemaTransformationServiceProtocol:
        """
        Get the schema transformation service instance.
        
        Returns:
            The schema transformation service instance
        """
        return inject.instance(SchemaTransformationServiceProtocol)


class TestingSchemaProvider:
    """Testing provider for the Schema module."""
    
    @staticmethod
    def configure_with_mocks(
        schema_def_repository: Optional[SchemaDefinitionRepositoryProtocol] = None,
        schema_config_repository: Optional[SchemaConfigurationRepositoryProtocol] = None,
        schema_manager: Optional[SchemaManagerServiceProtocol] = None,
        schema_validation: Optional[SchemaValidationServiceProtocol] = None,
        schema_transformation: Optional[SchemaTransformationServiceProtocol] = None
    ) -> None:
        """
        Configure the Schema module with mock implementations for testing.
        
        Args:
            schema_def_repository: Optional mock schema definition repository
            schema_config_repository: Optional mock schema configuration repository
            schema_manager: Optional mock schema manager service
            schema_validation: Optional mock schema validation service
            schema_transformation: Optional mock schema transformation service
        """
        def config(binder: inject.Binder) -> None:
            # Bind repositories
            if schema_def_repository:
                binder.bind(SchemaDefinitionRepositoryProtocol, schema_def_repository)
            else:
                binder.bind(SchemaDefinitionRepositoryProtocol, InMemorySchemaDefinitionRepository())
            
            if schema_config_repository:
                binder.bind(SchemaConfigurationRepositoryProtocol, schema_config_repository)
            else:
                binder.bind(SchemaConfigurationRepositoryProtocol, InMemorySchemaConfigurationRepository())
            
            # Bind services
            if schema_manager:
                binder.bind(SchemaManagerServiceProtocol, schema_manager)
            else:
                binder.bind(
                    SchemaManagerServiceProtocol,
                    SchemaManagerService(
                        schema_repository=inject.instance(SchemaDefinitionRepositoryProtocol),
                        config_repository=inject.instance(SchemaConfigurationRepositoryProtocol)
                    )
                )
            
            if schema_validation:
                binder.bind(SchemaValidationServiceProtocol, schema_validation)
            else:
                binder.bind(
                    SchemaValidationServiceProtocol,
                    SchemaValidationService(
                        schema_repository=inject.instance(SchemaDefinitionRepositoryProtocol)
                    )
                )
            
            if schema_transformation:
                binder.bind(SchemaTransformationServiceProtocol, schema_transformation)
            else:
                binder.bind(
                    SchemaTransformationServiceProtocol,
                    SchemaTransformationService(
                        schema_repository=inject.instance(SchemaDefinitionRepositoryProtocol)
                    )
                )
        
        inject.configure(config)
    
    @staticmethod
    def cleanup() -> None:
        """Clean up the testing configuration."""
        inject.clear()