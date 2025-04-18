# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Dependency injection provider for DTO module components.

This module provides dependency injection container and provider for the DTO
module components, following the patterns from uno.dependencies.
"""

import logging
from typing import Optional, Dict, Any

from uno.dependencies.modern_provider import Provider, ProviderProtocol

from uno.dto.domain_repositories import (
    SchemaDefinitionRepositoryProtocol,
    SchemaConfigurationRepositoryProtocol,
    InMemorySchemaDefinitionRepository,
    InMemorySchemaConfigurationRepository,
    FileSchemaDefinitionRepository,
    FileSchemaConfigurationRepository,
)

from uno.dto.domain_services import (
    SchemaManagerServiceProtocol,
    SchemaValidationServiceProtocol,
    SchemaTransformationServiceProtocol,
    SchemaManagerService,
    SchemaValidationService,
    SchemaTransformationService,
)


class SchemaProvider(ProviderProtocol):
    """Provider for the DTOschema components."""
    
    def __init__(
        self,
        schema_repository: Optional[SchemaDefinitionRepositoryProtocol] = None,
        config_repository: Optional[SchemaConfigurationRepositoryProtocol] = None,
        manager_service: Optional[SchemaManagerServiceProtocol] = None,
        validation_service: Optional[SchemaValidationServiceProtocol] = None,
        transformation_service: Optional[SchemaTransformationServiceProtocol] = None,
        logger: Optional[logging.Logger] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the provider.
        
        Args:
            schema_repository: Optional schema repository implementation
            config_repository: Optional config repository implementation
            manager_service: Optional manager service implementation
            validation_service: Optional validation service implementation
            transformation_service: Optional transformation service implementation
            logger: Optional logger instance
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize repositories
        self.schema_repository = schema_repository
        self.config_repository = config_repository
        
        # Initialize services
        self.manager_service = manager_service
        self.validation_service = validation_service
        self.transformation_service = transformation_service
        
    def register(self, provider: Provider) -> None:
        """
        Register components with the provider.
        
        Args:
            provider: The provider to register with
        """
        # Initialize repositories if not provided
        if not self.schema_repository:
            if "schema_dir" in self.config:
                self.schema_repository = FileSchemaDefinitionRepository(
                    self.config["schema_dir"]
                )
            else:
                self.schema_repository = InMemorySchemaDefinitionRepository()
                
        if not self.config_repository:
            if "config_dir" in self.config:
                self.config_repository = FileSchemaConfigurationRepository(
                    self.config["config_dir"]
                )
            else:
                self.config_repository = InMemorySchemaConfigurationRepository()
                
        # Initialize services if not provided
        if not self.manager_service:
            self.manager_service = SchemaManagerService(
                self.schema_repository,
                self.config_repository,
                self.logger
            )
            
        if not self.validation_service:
            self.validation_service = SchemaValidationService(self.logger)
            
        if not self.transformation_service:
            self.transformation_service = SchemaTransformationService(self.logger)
            
        # Register all components with the provider
        provider.register(SchemaDefinitionRepositoryProtocol, lambda: self.schema_repository)
        provider.register(SchemaConfigurationRepositoryProtocol, lambda: self.config_repository)
        provider.register(SchemaManagerServiceProtocol, lambda: self.manager_service)
        provider.register(SchemaValidationServiceProtocol, lambda: self.validation_service)
        provider.register(SchemaTransformationServiceProtocol, lambda: self.transformation_service)


class TestingSchemaProvider(SchemaProvider):
    """Provider for testing the DTO schema components."""
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the testing provider.
        
        Args:
            logger: Optional logger instance
            config: Optional configuration dictionary
        """
        # Use in-memory repositories for testing
        schema_repository = InMemorySchemaDefinitionRepository()
        config_repository = InMemorySchemaConfigurationRepository()
        
        # Initialize services
        manager_service = SchemaManagerService(
            schema_repository,
            config_repository,
            logger
        )
        validation_service = SchemaValidationService(logger)
        transformation_service = SchemaTransformationService(logger)
        
        super().__init__(
            schema_repository=schema_repository,
            config_repository=config_repository,
            manager_service=manager_service,
            validation_service=validation_service,
            transformation_service=transformation_service,
            logger=logger,
            config=config
        )