"""
Schema management services for the Domain-Driven Design approach.

This module provides schema management services that integrate with the dependency
injection system and support domain entities, SQLAlchemy models, and
DTOs (data transfer objects).
"""

import logging
from typing import Dict, Type, Optional, List, Any

from pydantic import BaseModel

from uno.dependencies.interfaces import UnoConfigProtocol
from uno.schema.schema import UnoSchema, UnoSchemaConfig


class SchemaManagerService:
    """
    Service for managing schemas in the Domain-Driven Design approach.
    
    This service:
    - Creates and manages schema transformations for domain entities
    - Generates DTO (Data Transfer Object) schemas for API endpoints
    - Produces paginated list schemas for collections
    - Supports both Pydantic models and SQLAlchemy models
    - Integrates with FastAPI for request validation and response serialization
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
        
    def get_list_schema(self, model: Type[Any]) -> Type[UnoSchema]:
        """
        Get or create a schema for paginated lists of the given model.
        
        This is particularly useful for API responses that return collections of items.
        The resulting schema includes pagination metadata fields.
        
        Args:
            model: The model to create a list schema for (entity, DTO or SQLAlchemy model)
            
        Returns:
            A schema class for paginated lists of the given model
        """
        from typing import List as ListType, Optional as OptionalType
        from pydantic import create_model, Field
        
        # Use a consistent naming convention for list schemas
        model_name = getattr(model, "__name__", str(model))
        schema_name = f"{model_name}ListSchema"
        
        # Check if we already have this list schema
        if schema_name in self.schemas:
            return self.schemas[schema_name]
            
        # Create the list schema
        list_schema = create_model(
            schema_name,
            __base__=UnoSchema,
            items=(ListType[model], ...),
            total=(int, ...),
            page=(int, Field(default=1, description="Current page number")),
            page_size=(int, Field(default=25, description="Number of items per page")),
            pages=(int, Field(default=1, description="Total number of pages")),
            has_next=(bool, Field(default=False, description="Whether there are more pages")),
            has_prev=(bool, Field(default=False, description="Whether there are previous pages"))
        )
        
        # Register the schema
        self.schemas[schema_name] = list_schema
        return list_schema
    
    def register_standard_configs(self) -> None:
        """
        Register standard schema configurations.
        
        This method sets up the common schema configurations used
        throughout the application for both domain entities and DTOs.
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
            include_fields={"id", "name", "display_name", "created_at"}
        ))
    
    def create_standard_schemas(self, model: Type[BaseModel]) -> Dict[str, Type[UnoSchema]]:
        """
        Create standard schemas for a model.
        
        This method ensures that standard configurations are registered
        and then creates all schemas for the model.
        
        Args:
            model: The model to create schemas for (domain entity or DTO)
            
        Returns:
            A dictionary of schema names to schema classes
        """
        # Make sure standard configs are registered
        if not self.schema_configs:
            self.register_standard_configs()
        
        # Create all schemas
        return self.create_all_schemas(model)
        
    def create_dto_from_model(
        self, 
        model_type: Type[Any], 
        dto_name: str,
        include_fields: Optional[set[str]] = None,
        exclude_fields: Optional[set[str]] = None,
        make_optional: bool = False
    ) -> Type[BaseModel]:
        """
        Create a DTO (Data Transfer Object) from a domain entity or SQLAlchemy model.
        
        This is useful for creating request and response models for API endpoints.
        
        Args:
            model_type: The domain entity or SQLAlchemy model class
            dto_name: Name for the generated DTO
            include_fields: Fields to include (if None, includes all except excluded fields)
            exclude_fields: Fields to exclude (only used if include_fields is None)
            make_optional: Whether to make all fields optional (useful for update DTOs)
            
        Returns:
            A Pydantic model class representing the DTO
        """
        from typing import get_type_hints, Optional as OptionalType
        from pydantic import create_model
        
        self.logger.debug(f"Creating DTO {dto_name} from {model_type.__name__}")
        
        # Get model fields
        if hasattr(model_type, 'model_fields'):
            # For Pydantic models
            field_names = model_type.model_fields.keys()
            field_types = {name: field.annotation for name, field in model_type.model_fields.items()}
        else:
            # For domain entities or SQLAlchemy models
            field_types = get_type_hints(model_type)
            field_names = field_types.keys()
        
        # Filter fields based on include/exclude parameters
        filtered_fields = {}
        for field_name in field_names:
            # Skip private fields, methods, and class variables
            if field_name.startswith('_') or field_name not in field_types:
                continue
                
            # Apply include/exclude filters
            if include_fields is not None and field_name not in include_fields:
                continue
            if exclude_fields is not None and field_name in exclude_fields:
                continue
            
            field_type = field_types[field_name]
                
            # Add the field
            if make_optional:
                filtered_fields[field_name] = (OptionalType[field_type], None)
            else:
                filtered_fields[field_name] = (field_type, ...)
        
        # Create and return the DTO
        return create_model(dto_name, **filtered_fields)
        
    def create_api_schemas(
        self,
        entity_type: Type[Any]
    ) -> Dict[str, Type[BaseModel]]:
        """
        Create a complete set of API schemas for a domain entity.
        
        This creates standard schemas for create, update, detail view, and list endpoints.
        
        Args:
            entity_type: The domain entity class
            
        Returns:
            A dictionary with 'detail', 'create', 'update', and 'list' schemas
        """
        entity_name = entity_type.__name__
        self.logger.debug(f"Creating API schemas for {entity_name}")
        
        # Create detail schema (includes all fields)
        detail_schema = self.create_dto_from_model(
            model_type=entity_type,
            dto_name=f"{entity_name}DetailDTO",
            exclude_fields={'events', 'child_entities'} if hasattr(entity_type, 'events') else None,
        )
        
        # Create schema for creation (no id required)
        create_schema = self.create_dto_from_model(
            model_type=entity_type,
            dto_name=f"{entity_name}CreateDTO",
            exclude_fields={'id', 'created_at', 'updated_at', 'version', 'events', 'child_entities'},
        )
        
        # Create schema for updates (all fields optional except id)
        update_schema = self.create_dto_from_model(
            model_type=entity_type,
            dto_name=f"{entity_name}UpdateDTO",
            exclude_fields={'id', 'created_at', 'updated_at', 'version', 'events', 'child_entities'},
            make_optional=True
        )
        
        # Create list schema
        list_schema = self.get_list_schema(detail_schema)
        
        # Return all schemas
        return {
            'detail': detail_schema,
            'create': create_schema,
            'update': update_schema,
            'list': list_schema
        }