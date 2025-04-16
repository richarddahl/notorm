# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain services for the Schema module.

This module defines service interfaces and implementations for the Schema module,
providing business logic for schema creation, validation, transformation, and management.
"""

from typing import Dict, List, Any, Optional, Type, TypeVar, Generic, Union, get_args, get_origin, cast
import inspect
import logging
from datetime import datetime

from pydantic import BaseModel, ValidationError, create_model, Field

from uno.core.errors.result import Result, Success, Failure, ErrorDetails
from uno.schema.entities import (
    SchemaId, SchemaDefinition, SchemaType, FieldDefinition, 
    SchemaConfiguration, PaginatedResult, PaginationMetadata,
    SchemaCreationRequest, SchemaUpdateRequest, SchemaValidationRequest,
    ApiSchemaCreationRequest
)
from uno.schema.domain_repositories import (
    SchemaDefinitionRepositoryProtocol,
    SchemaConfigurationRepositoryProtocol
)


# Type variable for improved type safety
T = TypeVar('T', bound=BaseModel)


# Service Protocols

class SchemaManagerServiceProtocol(Protocol):
    """Protocol for schema manager service."""
    
    def create_schema_definition(
        self, request: SchemaCreationRequest
    ) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Create a new schema definition.
        
        Args:
            request: The schema creation request
            
        Returns:
            Result containing the created schema definition
        """
        ...
    
    def update_schema_definition(
        self, schema_id: SchemaId, request: SchemaUpdateRequest
    ) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Update an existing schema definition.
        
        Args:
            schema_id: The ID of the schema to update
            request: The schema update request
            
        Returns:
            Result containing the updated schema definition
        """
        ...
    
    def get_schema_definition(
        self, schema_id: SchemaId
    ) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Get a schema definition by ID.
        
        Args:
            schema_id: The ID of the schema to retrieve
            
        Returns:
            Result containing the schema definition if found
        """
        ...
    
    def delete_schema_definition(
        self, schema_id: SchemaId
    ) -> Result[None, ErrorDetails]:
        """
        Delete a schema definition.
        
        Args:
            schema_id: The ID of the schema to delete
            
        Returns:
            Result indicating success or failure
        """
        ...
    
    def list_schema_definitions(
        self, 
        schema_type: Optional[SchemaType] = None,
        page: int = 1,
        page_size: int = 25
    ) -> Result[PaginatedResult[SchemaDefinition], ErrorDetails]:
        """
        List schema definitions with optional filtering.
        
        Args:
            schema_type: Optional schema type to filter by
            page: Page number for pagination
            page_size: Items per page
            
        Returns:
            Result containing paginated schema definitions
        """
        ...
    
    def add_schema_configuration(
        self, name: str, config: SchemaConfiguration
    ) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Add a schema configuration.
        
        Args:
            name: The name of the configuration
            config: The configuration to add
            
        Returns:
            Result containing the added configuration
        """
        ...
    
    def get_schema_configuration(
        self, name: str
    ) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Get a schema configuration by name.
        
        Args:
            name: The name of the configuration to retrieve
            
        Returns:
            Result containing the configuration if found
        """
        ...
    
    def delete_schema_configuration(
        self, name: str
    ) -> Result[None, ErrorDetails]:
        """
        Delete a schema configuration.
        
        Args:
            name: The name of the configuration to delete
            
        Returns:
            Result indicating success or failure
        """
        ...
    
    def list_schema_configurations(
        self
    ) -> Result[List[str], ErrorDetails]:
        """
        List all schema configuration names.
        
        Returns:
            Result containing a list of configuration names
        """
        ...


class SchemaValidationServiceProtocol(Protocol):
    """Protocol for schema validation service."""
    
    def validate_data(
        self, schema_id: SchemaId, data: Dict[str, Any]
    ) -> Result[Dict[str, Any], ErrorDetails]:
        """
        Validate data against a schema.
        
        Args:
            schema_id: The ID of the schema to validate against
            data: The data to validate
            
        Returns:
            Result containing the validated data if successful
        """
        ...
    
    def create_validation_model(
        self, schema_definition: SchemaDefinition
    ) -> Result[Type[BaseModel], ErrorDetails]:
        """
        Create a Pydantic model for validation.
        
        Args:
            schema_definition: The schema definition to create a model from
            
        Returns:
            Result containing the created model class
        """
        ...


class SchemaTransformationServiceProtocol(Protocol):
    """Protocol for schema transformation service."""
    
    def create_model_from_schema(
        self, schema_definition: SchemaDefinition
    ) -> Result[Type[BaseModel], ErrorDetails]:
        """
        Create a Pydantic model from a schema definition.
        
        Args:
            schema_definition: The schema definition to create a model from
            
        Returns:
            Result containing the created model class
        """
        ...
    
    def create_api_schemas(
        self, request: ApiSchemaCreationRequest
    ) -> Result[Dict[str, SchemaDefinition], ErrorDetails]:
        """
        Create a complete set of API schemas.
        
        Args:
            request: The API schema creation request
            
        Returns:
            Result containing the created schema definitions
        """
        ...
    
    def create_dto_from_entity(
        self, 
        entity_class: Type[Any], 
        schema_type: SchemaType,
        include_fields: Optional[Set[str]] = None,
        exclude_fields: Optional[Set[str]] = None
    ) -> Result[Type[BaseModel], ErrorDetails]:
        """
        Create a DTO from an entity class.
        
        Args:
            entity_class: The entity class to create a DTO from
            schema_type: The type of schema to create
            include_fields: Optional fields to include
            exclude_fields: Optional fields to exclude
            
        Returns:
            Result containing the created DTO class
        """
        ...


# Service Implementations

class SchemaManagerService:
    """Service for managing schema definitions and configurations."""
    
    def __init__(
        self,
        schema_repository: SchemaDefinitionRepositoryProtocol,
        config_repository: SchemaConfigurationRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the schema manager service.
        
        Args:
            schema_repository: Repository for schema definitions
            config_repository: Repository for schema configurations
            logger: Optional logger
        """
        self.schema_repository = schema_repository
        self.config_repository = config_repository
        self.logger = logger or logging.getLogger(__name__)
    
    def create_schema_definition(
        self, request: SchemaCreationRequest
    ) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Create a new schema definition.
        
        Args:
            request: The schema creation request
            
        Returns:
            Result containing the created schema definition
        """
        # Log the operation
        self.logger.debug(f"Creating schema definition: {request.name}")
        
        # Check for existing schema with same name
        existing_schema = self.schema_repository.get_by_name(request.name)
        if isinstance(existing_schema, Success):
            return Failure(ErrorDetails(
                code="SCHEMA_ALREADY_EXISTS",
                message=f"Schema with name {request.name} already exists"
            ))
        
        # Convert schema type string to enum
        try:
            schema_type = SchemaType[request.type]
        except KeyError:
            return Failure(ErrorDetails(
                code="INVALID_SCHEMA_TYPE",
                message=f"Invalid schema type: {request.type}"
            ))
        
        # Create schema ID
        schema_id = SchemaId(f"{request.name}Schema")
        
        # Create schema definition
        schema = SchemaDefinition(
            id=schema_id,
            name=request.name,
            type=schema_type,
            description=request.description
        )
        
        # Add fields to the schema
        for field_name, field_info in request.fields.items():
            try:
                field_def = FieldDefinition(
                    name=field_name,
                    annotation=field_info.get("annotation", Any),
                    description=field_info.get("description", ""),
                    required=field_info.get("required", True),
                    default=field_info.get("default")
                )
                
                result = schema.add_field(field_def)
                if isinstance(result, Failure):
                    return result
            except Exception as e:
                self.logger.error(f"Error creating field {field_name}: {str(e)}")
                return Failure(ErrorDetails(
                    code="FIELD_CREATION_ERROR",
                    message=f"Error creating field {field_name}: {str(e)}"
                ))
        
        # Save the schema
        return self.schema_repository.save(schema)
    
    def update_schema_definition(
        self, schema_id: SchemaId, request: SchemaUpdateRequest
    ) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Update an existing schema definition.
        
        Args:
            schema_id: The ID of the schema to update
            request: The schema update request
            
        Returns:
            Result containing the updated schema definition
        """
        # Log the operation
        self.logger.debug(f"Updating schema definition: {schema_id}")
        
        # Get the existing schema
        schema_result = self.schema_repository.get_by_id(schema_id)
        if isinstance(schema_result, Failure):
            return schema_result
        
        schema = schema_result.value
        
        # Update description if provided
        if request.description is not None:
            schema.description = request.description
        
        # Add new fields
        for field_name, field_info in request.fields_to_add.items():
            try:
                field_def = FieldDefinition(
                    name=field_name,
                    annotation=field_info.get("annotation", Any),
                    description=field_info.get("description", ""),
                    required=field_info.get("required", True),
                    default=field_info.get("default")
                )
                
                result = schema.add_field(field_def)
                if isinstance(result, Failure):
                    return result
            except Exception as e:
                self.logger.error(f"Error adding field {field_name}: {str(e)}")
                return Failure(ErrorDetails(
                    code="FIELD_ADDITION_ERROR",
                    message=f"Error adding field {field_name}: {str(e)}"
                ))
        
        # Update existing fields
        for field_name, field_info in request.fields_to_update.items():
            try:
                # Get existing field
                field_result = schema.get_field(field_name)
                if isinstance(field_result, Failure):
                    return field_result
                
                existing_field = field_result.value
                
                # Update field properties
                updated_field = FieldDefinition(
                    name=field_name,
                    annotation=field_info.get("annotation", existing_field.annotation),
                    description=field_info.get("description", existing_field.description),
                    required=field_info.get("required", existing_field.required),
                    default=field_info.get("default", existing_field.default)
                )
                
                result = schema.update_field(updated_field)
                if isinstance(result, Failure):
                    return result
            except Exception as e:
                self.logger.error(f"Error updating field {field_name}: {str(e)}")
                return Failure(ErrorDetails(
                    code="FIELD_UPDATE_ERROR",
                    message=f"Error updating field {field_name}: {str(e)}"
                ))
        
        # Remove fields
        for field_name in request.fields_to_remove:
            result = schema.remove_field(field_name)
            if isinstance(result, Failure):
                return result
        
        # Save the updated schema
        return self.schema_repository.save(schema)
    
    def get_schema_definition(
        self, schema_id: SchemaId
    ) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Get a schema definition by ID.
        
        Args:
            schema_id: The ID of the schema to retrieve
            
        Returns:
            Result containing the schema definition if found
        """
        return self.schema_repository.get_by_id(schema_id)
    
    def delete_schema_definition(
        self, schema_id: SchemaId
    ) -> Result[None, ErrorDetails]:
        """
        Delete a schema definition.
        
        Args:
            schema_id: The ID of the schema to delete
            
        Returns:
            Result indicating success or failure
        """
        return self.schema_repository.delete(schema_id)
    
    def list_schema_definitions(
        self, 
        schema_type: Optional[SchemaType] = None,
        page: int = 1,
        page_size: int = 25
    ) -> Result[PaginatedResult[SchemaDefinition], ErrorDetails]:
        """
        List schema definitions with optional filtering.
        
        Args:
            schema_type: Optional schema type to filter by
            page: Page number for pagination
            page_size: Items per page
            
        Returns:
            Result containing paginated schema definitions
        """
        return self.schema_repository.list(schema_type, page, page_size)
    
    def add_schema_configuration(
        self, name: str, config: SchemaConfiguration
    ) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Add a schema configuration.
        
        Args:
            name: The name of the configuration
            config: The configuration to add
            
        Returns:
            Result containing the added configuration
        """
        # Validate configuration
        validation_result = config.validate()
        if isinstance(validation_result, Failure):
            return validation_result
        
        # Save configuration
        return self.config_repository.save(name, config)
    
    def get_schema_configuration(
        self, name: str
    ) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Get a schema configuration by name.
        
        Args:
            name: The name of the configuration to retrieve
            
        Returns:
            Result containing the configuration if found
        """
        return self.config_repository.get(name)
    
    def delete_schema_configuration(
        self, name: str
    ) -> Result[None, ErrorDetails]:
        """
        Delete a schema configuration.
        
        Args:
            name: The name of the configuration to delete
            
        Returns:
            Result indicating success or failure
        """
        return self.config_repository.delete(name)
    
    def list_schema_configurations(
        self
    ) -> Result[List[str], ErrorDetails]:
        """
        List all schema configuration names.
        
        Returns:
            Result containing a list of configuration names
        """
        return self.config_repository.list()
    
    def register_standard_configurations(self) -> Result[None, ErrorDetails]:
        """
        Register standard schema configurations.
        
        This creates the default set of schema configurations used by the application.
        
        Returns:
            Result indicating success or failure
        """
        try:
            # Create schema for storing data in the database with all fields
            data_config = SchemaConfiguration()
            self.add_schema_configuration("data", data_config)
            
            # Create schema for API responses with all fields
            api_config = SchemaConfiguration()
            self.add_schema_configuration("api", api_config)
            
            # Create schema for form editing
            edit_config = SchemaConfiguration(
                exclude_fields={"created_at", "updated_at", "version"}
            )
            self.add_schema_configuration("edit", edit_config)
            
            # Create schema for viewing
            view_config = SchemaConfiguration(
                exclude_fields={"private_fields", "password", "secret_key"}
            )
            self.add_schema_configuration("view", view_config)
            
            # Create schema for list views with minimal fields
            list_config = SchemaConfiguration(
                include_fields={"id", "name", "display_name", "created_at"}
            )
            self.add_schema_configuration("list", list_config)
            
            return Success(None)
        except Exception as e:
            self.logger.error(f"Error registering standard configurations: {str(e)}")
            return Failure(ErrorDetails(
                code="CONFIG_REGISTRATION_ERROR",
                message=f"Error registering standard configurations: {str(e)}"
            ))


class SchemaValidationService:
    """Service for validating data against schemas."""
    
    def __init__(
        self,
        schema_repository: SchemaDefinitionRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the schema validation service.
        
        Args:
            schema_repository: Repository for schema definitions
            logger: Optional logger
        """
        self.schema_repository = schema_repository
        self.logger = logger or logging.getLogger(__name__)
        self._validation_models: Dict[str, Type[BaseModel]] = {}
    
    def validate_data(
        self, schema_id: SchemaId, data: Dict[str, Any]
    ) -> Result[Dict[str, Any], ErrorDetails]:
        """
        Validate data against a schema.
        
        Args:
            schema_id: The ID of the schema to validate against
            data: The data to validate
            
        Returns:
            Result containing the validated data if successful
        """
        # Log the operation
        self.logger.debug(f"Validating data against schema: {schema_id}")
        
        # Get the validation model
        model_class = self._validation_models.get(str(schema_id))
        
        if model_class is None:
            # Get the schema definition
            schema_result = self.schema_repository.get_by_id(schema_id)
            if isinstance(schema_result, Failure):
                return schema_result
            
            # Create validation model
            model_result = self.create_validation_model(schema_result.value)
            if isinstance(model_result, Failure):
                return model_result
            
            model_class = model_result.value
            self._validation_models[str(schema_id)] = model_class
        
        # Validate the data
        try:
            # Create an instance of the model
            model_instance = model_class(**data)
            
            # Return validated data
            return Success(model_instance.model_dump())
        except ValidationError as e:
            self.logger.error(f"Validation error: {str(e)}")
            return Failure(ErrorDetails(
                code="VALIDATION_ERROR",
                message="Data validation failed",
                details=e.errors()
            ))
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return Failure(ErrorDetails(
                code="VALIDATION_ERROR",
                message=f"Error validating data: {str(e)}"
            ))
    
    def create_validation_model(
        self, schema_definition: SchemaDefinition
    ) -> Result[Type[BaseModel], ErrorDetails]:
        """
        Create a Pydantic model for validation.
        
        Args:
            schema_definition: The schema definition to create a model from
            
        Returns:
            Result containing the created model class
        """
        try:
            # Create field definitions for the model
            fields = {}
            
            for field_name, field_def in schema_definition.fields.items():
                # Determine field type and default
                field_type = field_def.annotation
                
                if field_def.required:
                    # Required field
                    field_default = ...
                else:
                    # Optional field with default
                    field_default = field_def.default
                
                # Add field to the model
                fields[field_name] = (field_type, field_default)
            
            # Create the model class
            model_name = f"{schema_definition.name}ValidationModel"
            model_class = create_model(
                model_name,
                __base__=BaseModel,
                **fields
            )
            
            return Success(model_class)
        except Exception as e:
            self.logger.error(f"Error creating validation model: {str(e)}")
            return Failure(ErrorDetails(
                code="MODEL_CREATION_ERROR",
                message=f"Error creating validation model: {str(e)}"
            ))


class SchemaTransformationService:
    """Service for transforming between different schema representations."""
    
    def __init__(
        self,
        schema_repository: SchemaDefinitionRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the schema transformation service.
        
        Args:
            schema_repository: Repository for schema definitions
            logger: Optional logger
        """
        self.schema_repository = schema_repository
        self.logger = logger or logging.getLogger(__name__)
    
    def create_model_from_schema(
        self, schema_definition: SchemaDefinition
    ) -> Result[Type[BaseModel], ErrorDetails]:
        """
        Create a Pydantic model from a schema definition.
        
        Args:
            schema_definition: The schema definition to create a model from
            
        Returns:
            Result containing the created model class
        """
        try:
            # Create field definitions for the model
            fields = {}
            
            for field_name, field_def in schema_definition.fields.items():
                # Determine field type
                field_type = field_def.annotation
                
                # Create field
                field = Field(
                    default=... if field_def.required else field_def.default,
                    description=field_def.description
                )
                
                # Add field to the model
                fields[field_name] = (field_type, field)
            
            # Create the model class
            model_name = f"{schema_definition.name}Model"
            model_class = create_model(
                model_name,
                __base__=BaseModel,
                **fields
            )
            
            return Success(model_class)
        except Exception as e:
            self.logger.error(f"Error creating model from schema: {str(e)}")
            return Failure(ErrorDetails(
                code="MODEL_CREATION_ERROR",
                message=f"Error creating model from schema: {str(e)}"
            ))
    
    def create_api_schemas(
        self, request: ApiSchemaCreationRequest
    ) -> Result[Dict[str, SchemaDefinition], ErrorDetails]:
        """
        Create a complete set of API schemas.
        
        Args:
            request: The API schema creation request
            
        Returns:
            Result containing the created schema definitions
        """
        try:
            result_schemas: Dict[str, SchemaDefinition] = {}
            
            # Start with a detail schema (includes all fields)
            detail_schema_id = SchemaId(f"{request.entity_name}DetailSchema")
            detail_schema = SchemaDefinition(
                id=detail_schema_id,
                name=f"{request.entity_name}Detail",
                type=SchemaType.DETAIL,
                description=f"Detail schema for {request.entity_name}"
            )
            
            # Add all fields from the request
            for field_name, field_info in request.fields.items():
                field_def = FieldDefinition(
                    name=field_name,
                    annotation=field_info.get("annotation", Any),
                    description=field_info.get("description", ""),
                    required=field_info.get("required", True),
                    default=field_info.get("default")
                )
                
                detail_schema.add_field(field_def)
            
            # Save the detail schema
            result = self.schema_repository.save(detail_schema)
            if isinstance(result, Failure):
                return result
            
            result_schemas["detail"] = detail_schema
            
            # Create a schema for creation (no id required)
            if request.create_create_schema:
                create_schema_id = SchemaId(f"{request.entity_name}CreateSchema")
                create_schema = SchemaDefinition(
                    id=create_schema_id,
                    name=f"{request.entity_name}Create",
                    type=SchemaType.CREATE,
                    description=f"Creation schema for {request.entity_name}"
                )
                
                # Add fields except id, created_at, updated_at
                for field_name, field_info in request.fields.items():
                    if field_name not in ["id", "created_at", "updated_at", "version"]:
                        field_def = FieldDefinition(
                            name=field_name,
                            annotation=field_info.get("annotation", Any),
                            description=field_info.get("description", ""),
                            required=field_info.get("required", True),
                            default=field_info.get("default")
                        )
                        
                        create_schema.add_field(field_def)
                
                # Save the create schema
                result = self.schema_repository.save(create_schema)
                if isinstance(result, Failure):
                    return result
                
                result_schemas["create"] = create_schema
            
            # Create a schema for updates (all fields optional except id)
            if request.create_update_schema:
                update_schema_id = SchemaId(f"{request.entity_name}UpdateSchema")
                update_schema = SchemaDefinition(
                    id=update_schema_id,
                    name=f"{request.entity_name}Update",
                    type=SchemaType.UPDATE,
                    description=f"Update schema for {request.entity_name}"
                )
                
                # Add id field
                id_field_info = request.fields.get("id", {"annotation": str, "required": True})
                id_field = FieldDefinition(
                    name="id",
                    annotation=id_field_info.get("annotation", str),
                    description="Identifier for the entity",
                    required=True
                )
                update_schema.add_field(id_field)
                
                # Add other fields as optional
                for field_name, field_info in request.fields.items():
                    if field_name not in ["id", "created_at", "updated_at", "version"]:
                        field_def = FieldDefinition(
                            name=field_name,
                            annotation=field_info.get("annotation", Any),
                            description=field_info.get("description", ""),
                            required=False,
                            default=field_info.get("default")
                        )
                        
                        update_schema.add_field(field_def)
                
                # Save the update schema
                result = self.schema_repository.save(update_schema)
                if isinstance(result, Failure):
                    return result
                
                result_schemas["update"] = update_schema
            
            # Create a schema for list views
            if request.create_list_schema:
                list_schema_id = SchemaId(f"{request.entity_name}ListSchema")
                list_schema = SchemaDefinition(
                    id=list_schema_id,
                    name=f"{request.entity_name}List",
                    type=SchemaType.LIST,
                    description=f"List schema for {request.entity_name}"
                )
                
                # Add basic fields for list view
                list_fields = ["id", "name", "created_at", "updated_at"]
                for field_name in list_fields:
                    if field_name in request.fields:
                        field_info = request.fields[field_name]
                        field_def = FieldDefinition(
                            name=field_name,
                            annotation=field_info.get("annotation", Any),
                            description=field_info.get("description", ""),
                            required=field_info.get("required", True),
                            default=field_info.get("default")
                        )
                        
                        list_schema.add_field(field_def)
                
                # Save the list schema
                result = self.schema_repository.save(list_schema)
                if isinstance(result, Failure):
                    return result
                
                result_schemas["list"] = list_schema
            
            return Success(result_schemas)
        except Exception as e:
            self.logger.error(f"Error creating API schemas: {str(e)}")
            return Failure(ErrorDetails(
                code="API_SCHEMA_CREATION_ERROR",
                message=f"Error creating API schemas: {str(e)}"
            ))
    
    def create_dto_from_entity(
        self, 
        entity_class: Type[Any], 
        schema_type: SchemaType,
        include_fields: Optional[Set[str]] = None,
        exclude_fields: Optional[Set[str]] = None
    ) -> Result[Type[BaseModel], ErrorDetails]:
        """
        Create a DTO from an entity class.
        
        Args:
            entity_class: The entity class to create a DTO from
            schema_type: The type of schema to create
            include_fields: Optional fields to include
            exclude_fields: Optional fields to exclude
            
        Returns:
            Result containing the created DTO class
        """
        try:
            # Get type hints from the entity class
            type_hints = {}
            
            if hasattr(entity_class, "model_fields"):
                # If it's a Pydantic model
                field_names = entity_class.model_fields.keys()
                field_types = {name: field.annotation for name, field in entity_class.model_fields.items()}
            else:
                # Otherwise use inspect
                field_types = inspect.get_type_hints(entity_class)
                field_names = field_types.keys()
            
            # Filter fields based on include/exclude parameters
            filtered_fields = {}
            for field_name in field_names:
                # Skip private fields, methods, and class variables
                if field_name.startswith('_'):
                    continue
                
                # Apply include/exclude filters
                if include_fields is not None and field_name not in include_fields:
                    continue
                if exclude_fields is not None and field_name in exclude_fields:
                    continue
                
                # Apply schema type specific filters
                if schema_type == SchemaType.CREATE and field_name in ["id", "created_at", "updated_at", "version"]:
                    continue
                if schema_type == SchemaType.UPDATE and field_name in ["created_at", "updated_at", "version"]:
                    continue
                
                # Get field type
                field_type = field_types.get(field_name, Any)
                
                # Determine if the field is required
                required = True
                if schema_type == SchemaType.UPDATE and field_name != "id":
                    required = False
                
                # Add the field
                if required:
                    filtered_fields[field_name] = (field_type, ...)
                else:
                    filtered_fields[field_name] = (field_type, None)
            
            # Create DTO class
            dto_name = f"{entity_class.__name__}{schema_type.name.title()}DTO"
            dto_class = create_model(
                dto_name,
                __base__=BaseModel,
                **filtered_fields
            )
            
            return Success(dto_class)
        except Exception as e:
            self.logger.error(f"Error creating DTO from entity: {str(e)}")
            return Failure(ErrorDetails(
                code="DTO_CREATION_ERROR",
                message=f"Error creating DTO from entity: {str(e)}"
            ))