"""
Service implementations for schema management.

This module provides services that implement business logic
for schema management through dependency injection.
"""

import logging
from typing import Dict, Type, Optional, List, Any

from pydantic import BaseModel

from uno.dependencies.interfaces import UnoConfigProtocol
from uno.schema.schema import UnoSchema, UnoSchemaConfig


class SchemaManagerService:
    """
    Service for managing UnoObj schemas.
    
    This service provides a centralized way to create and manage
    schemas for UnoObj models, with proper dependency injection
    and configuration.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        schema_configs: Optional[Dict[str, UnoSchemaConfig]] = None
    ):
        """
        Initialize the schema manager service.
        
        Args:
            logger: Optional logger
            schema_configs: Optional initial schema configurations
        """
        self.logger = logger or logging.getLogger(__name__)
        self.schema_configs = schema_configs or {}
        self.schemas: Dict[str, Type[UnoSchema]] = {}
    
    def add_schema_config(self, name: str, config: UnoSchemaConfig) -> None:
        """
        Add a schema configuration.
        
        Args:
            name: The name of the schema configuration
            config: The schema configuration to add
        """
        self.logger.debug(f"Adding schema config: {name}")
        self.schema_configs[name] = config
    
    def create_schema(
        self, 
        schema_name: str, 
        model: Type[BaseModel]
    ) -> Type[UnoSchema]:
        """
        Create a schema for a model.
        
        Args:
            schema_name: The name of the schema to create
            model: The model to create a schema for
            
        Returns:
            The created schema class
            
        Raises:
            ValueError: If the schema configuration is not found
        """
        if schema_name not in self.schema_configs:
            error_msg = f"Schema configuration {schema_name} not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.debug(f"Creating schema: {schema_name} for model: {model.__name__}")
        schema_config = self.schema_configs[schema_name]
        schema = schema_config.create_schema(
            schema_name=schema_name,
            model=model
        )
        
        self.schemas[schema_name] = schema
        return schema
    
    def create_all_schemas(self, model: Type[BaseModel]) -> Dict[str, Type[UnoSchema]]:
        """
        Create all schemas for a model.
        
        Args:
            model: The model to create schemas for
            
        Returns:
            A dictionary of schema names to schema classes
        """
        self.logger.debug(f"Creating all schemas for model: {model.__name__}")
        for schema_name in self.schema_configs:
            self.create_schema(schema_name, model)
        return self.schemas
    
    def get_schema(self, schema_name: str) -> Optional[Type[UnoSchema]]:
        """
        Get a schema by name.
        
        Args:
            schema_name: The name of the schema to get
            
        Returns:
            The schema if found, None otherwise
        """
        return self.schemas.get(schema_name)
    
    def register_standard_configs(self) -> None:
        """
        Register standard schema configurations.
        
        This method sets up the common schema configurations used
        throughout the application.
        """
        self.logger.debug("Registering standard schema configurations")
        
        # Create schema for storing data in the database with all fields
        self.add_schema_config("data", UnoSchemaConfig())
        
        # Create schema for API responses with all fields
        self.add_schema_config("api", UnoSchemaConfig())
        
        # Create schema for form editing
        self.add_schema_config("edit", UnoSchemaConfig(
            exclude_fields={"created_at", "updated_at", "version"}
        ))
        
        # Create schema for viewing
        self.add_schema_config("view", UnoSchemaConfig(
            exclude_fields={"private_fields", "password", "secret_key"}
        ))
        
        # Create schema for list views with minimal fields
        self.add_schema_config("list", UnoSchemaConfig(
            include_only=True,
            include_fields={"id", "name", "display_name", "created_at"}
        ))
    
    def create_standard_schemas(self, model: Type[BaseModel]) -> Dict[str, Type[UnoSchema]]:
        """
        Create standard schemas for a model.
        
        This method ensures that standard configurations are registered
        and then creates all schemas for the model.
        
        Args:
            model: The model to create schemas for
            
        Returns:
            A dictionary of schema names to schema classes
        """
        # Make sure standard configs are registered
        if not self.schema_configs:
            self.register_standard_configs()
        
        # Create all schemas
        return self.create_all_schemas(model)