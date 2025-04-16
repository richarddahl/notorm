# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain repositories for the Schema module.

This module defines repository interfaces and implementations for the Schema module,
providing data storage and retrieval for schema entities.
"""

from typing import Dict, List, Optional, Type, Protocol, cast
import json
from pathlib import Path
import os

from pydantic import BaseModel, create_model

from uno.core.errors.result import Result, Success, Failure, ErrorDetails
from uno.schema.entities import (
    SchemaId, SchemaDefinition, SchemaType, FieldDefinition, 
    SchemaConfiguration, PaginatedResult
)


# Repository Protocols

class SchemaDefinitionRepositoryProtocol(Protocol):
    """Repository protocol for schema definitions."""
    
    def save(self, schema: SchemaDefinition) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Save a schema definition.
        
        Args:
            schema: The schema definition to save
            
        Returns:
            Result containing the saved schema definition
        """
        ...
    
    def get_by_id(self, schema_id: SchemaId) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Get a schema definition by ID.
        
        Args:
            schema_id: The ID of the schema to retrieve
            
        Returns:
            Result containing the schema definition if found
        """
        ...
    
    def get_by_name(self, name: str) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Get a schema definition by name.
        
        Args:
            name: The name of the schema to retrieve
            
        Returns:
            Result containing the schema definition if found
        """
        ...
    
    def list(self, 
             schema_type: Optional[SchemaType] = None, 
             page: int = 1, 
             page_size: int = 25) -> Result[PaginatedResult[SchemaDefinition], ErrorDetails]:
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
    
    def delete(self, schema_id: SchemaId) -> Result[None, ErrorDetails]:
        """
        Delete a schema definition.
        
        Args:
            schema_id: The ID of the schema to delete
            
        Returns:
            Result indicating success or failure
        """
        ...


class SchemaConfigurationRepositoryProtocol(Protocol):
    """Repository protocol for schema configurations."""
    
    def save(self, name: str, config: SchemaConfiguration) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Save a schema configuration.
        
        Args:
            name: The name of the configuration
            config: The configuration to save
            
        Returns:
            Result containing the saved configuration
        """
        ...
    
    def get(self, name: str) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Get a schema configuration by name.
        
        Args:
            name: The name of the configuration to retrieve
            
        Returns:
            Result containing the configuration if found
        """
        ...
    
    def list(self) -> Result[List[str], ErrorDetails]:
        """
        List all schema configuration names.
        
        Returns:
            Result containing a list of configuration names
        """
        ...
    
    def delete(self, name: str) -> Result[None, ErrorDetails]:
        """
        Delete a schema configuration.
        
        Args:
            name: The name of the configuration to delete
            
        Returns:
            Result indicating success or failure
        """
        ...


# In-Memory Repository Implementations

class InMemorySchemaDefinitionRepository:
    """In-memory implementation of the schema definition repository."""
    
    def __init__(self):
        self._schemas: Dict[str, SchemaDefinition] = {}
    
    def save(self, schema: SchemaDefinition) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Save a schema definition.
        
        Args:
            schema: The schema definition to save
            
        Returns:
            Result containing the saved schema definition
        """
        self._schemas[str(schema.id)] = schema
        return Success(schema)
    
    def get_by_id(self, schema_id: SchemaId) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Get a schema definition by ID.
        
        Args:
            schema_id: The ID of the schema to retrieve
            
        Returns:
            Result containing the schema definition if found
        """
        schema = self._schemas.get(str(schema_id))
        if schema is None:
            return Failure(ErrorDetails(
                code="SCHEMA_NOT_FOUND",
                message=f"Schema with ID {schema_id} not found"
            ))
        return Success(schema)
    
    def get_by_name(self, name: str) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Get a schema definition by name.
        
        Args:
            name: The name of the schema to retrieve
            
        Returns:
            Result containing the schema definition if found
        """
        for schema in self._schemas.values():
            if schema.name == name:
                return Success(schema)
        
        return Failure(ErrorDetails(
            code="SCHEMA_NOT_FOUND",
            message=f"Schema with name {name} not found"
        ))
    
    def list(self, 
             schema_type: Optional[SchemaType] = None, 
             page: int = 1, 
             page_size: int = 25) -> Result[PaginatedResult[SchemaDefinition], ErrorDetails]:
        """
        List schema definitions with optional filtering.
        
        Args:
            schema_type: Optional schema type to filter by
            page: Page number for pagination
            page_size: Items per page
            
        Returns:
            Result containing paginated schema definitions
        """
        # Filter schemas by type if specified
        if schema_type is not None:
            schemas = [s for s in self._schemas.values() if s.type == schema_type]
        else:
            schemas = list(self._schemas.values())
        
        # Sort schemas by name
        schemas.sort(key=lambda s: s.name)
        
        # Calculate pagination
        total = len(schemas)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Get schemas for the requested page
        page_schemas = schemas[start_idx:end_idx] if start_idx < total else []
        
        # Create pagination metadata
        from uno.schema.entities import PaginationMetadata
        metadata = PaginationMetadata(
            total=total,
            page=page,
            page_size=page_size
        )
        
        # Create paginated result
        paginated_result = PaginatedResult(
            items=page_schemas,
            metadata=metadata
        )
        
        return Success(paginated_result)
    
    def delete(self, schema_id: SchemaId) -> Result[None, ErrorDetails]:
        """
        Delete a schema definition.
        
        Args:
            schema_id: The ID of the schema to delete
            
        Returns:
            Result indicating success or failure
        """
        if str(schema_id) not in self._schemas:
            return Failure(ErrorDetails(
                code="SCHEMA_NOT_FOUND",
                message=f"Schema with ID {schema_id} not found"
            ))
        
        del self._schemas[str(schema_id)]
        return Success(None)


class InMemorySchemaConfigurationRepository:
    """In-memory implementation of the schema configuration repository."""
    
    def __init__(self):
        self._configs: Dict[str, SchemaConfiguration] = {}
    
    def save(self, name: str, config: SchemaConfiguration) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Save a schema configuration.
        
        Args:
            name: The name of the configuration
            config: The configuration to save
            
        Returns:
            Result containing the saved configuration
        """
        self._configs[name] = config
        return Success(config)
    
    def get(self, name: str) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Get a schema configuration by name.
        
        Args:
            name: The name of the configuration to retrieve
            
        Returns:
            Result containing the configuration if found
        """
        config = self._configs.get(name)
        if config is None:
            return Failure(ErrorDetails(
                code="SCHEMA_CONFIG_NOT_FOUND",
                message=f"Schema configuration with name {name} not found"
            ))
        return Success(config)
    
    def list(self) -> Result[List[str], ErrorDetails]:
        """
        List all schema configuration names.
        
        Returns:
            Result containing a list of configuration names
        """
        return Success(list(self._configs.keys()))
    
    def delete(self, name: str) -> Result[None, ErrorDetails]:
        """
        Delete a schema configuration.
        
        Args:
            name: The name of the configuration to delete
            
        Returns:
            Result indicating success or failure
        """
        if name not in self._configs:
            return Failure(ErrorDetails(
                code="SCHEMA_CONFIG_NOT_FOUND",
                message=f"Schema configuration with name {name} not found"
            ))
        
        del self._configs[name]
        return Success(None)


# File-Based Repository Implementations

class FileSchemaDefinitionRepository:
    """File-based implementation of the schema definition repository."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir / "schemas"
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, schema: SchemaDefinition) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Save a schema definition to a file.
        
        Args:
            schema: The schema definition to save
            
        Returns:
            Result containing the saved schema definition
        """
        try:
            file_path = self.base_dir / f"{schema.id.value}.json"
            
            # Convert schema to dict
            schema_dict = schema.to_dict()
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(schema_dict, f, indent=2)
            
            return Success(schema)
        except Exception as e:
            return Failure(ErrorDetails(
                code="SCHEMA_SAVE_ERROR",
                message=f"Error saving schema: {str(e)}"
            ))
    
    def get_by_id(self, schema_id: SchemaId) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Get a schema definition by ID from a file.
        
        Args:
            schema_id: The ID of the schema to retrieve
            
        Returns:
            Result containing the schema definition if found
        """
        file_path = self.base_dir / f"{schema_id.value}.json"
        
        if not file_path.exists():
            return Failure(ErrorDetails(
                code="SCHEMA_NOT_FOUND",
                message=f"Schema with ID {schema_id} not found"
            ))
        
        try:
            with open(file_path, 'r') as f:
                schema_dict = json.load(f)
            
            # This is a partial implementation - in a real system, we would 
            # deserialize the JSON back to a SchemaDefinition object
            # For simplicity, we're returning a failure
            return Failure(ErrorDetails(
                code="NOT_IMPLEMENTED",
                message="Deserialization of schema definitions from file is not fully implemented"
            ))
        except Exception as e:
            return Failure(ErrorDetails(
                code="SCHEMA_LOAD_ERROR",
                message=f"Error loading schema: {str(e)}"
            ))
    
    def get_by_name(self, name: str) -> Result[SchemaDefinition, ErrorDetails]:
        """
        Get a schema definition by name from files.
        
        Args:
            name: The name of the schema to retrieve
            
        Returns:
            Result containing the schema definition if found
        """
        try:
            # Scan all schema files
            for file_path in self.base_dir.glob("*.json"):
                with open(file_path, 'r') as f:
                    schema_dict = json.load(f)
                
                if schema_dict.get("name") == name:
                    # This is a partial implementation - in a real system, we would 
                    # deserialize the JSON back to a SchemaDefinition object
                    # For simplicity, we're returning a failure
                    return Failure(ErrorDetails(
                        code="NOT_IMPLEMENTED",
                        message="Deserialization of schema definitions from file is not fully implemented"
                    ))
            
            return Failure(ErrorDetails(
                code="SCHEMA_NOT_FOUND",
                message=f"Schema with name {name} not found"
            ))
        except Exception as e:
            return Failure(ErrorDetails(
                code="SCHEMA_LOAD_ERROR",
                message=f"Error loading schema: {str(e)}"
            ))
    
    def list(self, 
             schema_type: Optional[SchemaType] = None, 
             page: int = 1, 
             page_size: int = 25) -> Result[PaginatedResult[SchemaDefinition], ErrorDetails]:
        """
        List schema definitions from files with optional filtering.
        
        Args:
            schema_type: Optional schema type to filter by
            page: Page number for pagination
            page_size: Items per page
            
        Returns:
            Result containing paginated schema definitions
        """
        try:
            # This is a partial implementation - in a real system, we would 
            # deserialize the JSON back to SchemaDefinition objects and implement
            # filtering and pagination
            # For simplicity, we're returning a failure
            return Failure(ErrorDetails(
                code="NOT_IMPLEMENTED",
                message="Listing schema definitions from file is not fully implemented"
            ))
        except Exception as e:
            return Failure(ErrorDetails(
                code="SCHEMA_LIST_ERROR",
                message=f"Error listing schemas: {str(e)}"
            ))
    
    def delete(self, schema_id: SchemaId) -> Result[None, ErrorDetails]:
        """
        Delete a schema definition file.
        
        Args:
            schema_id: The ID of the schema to delete
            
        Returns:
            Result indicating success or failure
        """
        file_path = self.base_dir / f"{schema_id.value}.json"
        
        if not file_path.exists():
            return Failure(ErrorDetails(
                code="SCHEMA_NOT_FOUND",
                message=f"Schema with ID {schema_id} not found"
            ))
        
        try:
            os.remove(file_path)
            return Success(None)
        except Exception as e:
            return Failure(ErrorDetails(
                code="SCHEMA_DELETE_ERROR",
                message=f"Error deleting schema: {str(e)}"
            ))


class FileSchemaConfigurationRepository:
    """File-based implementation of the schema configuration repository."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir / "schema_configs"
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, name: str, config: SchemaConfiguration) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Save a schema configuration to a file.
        
        Args:
            name: The name of the configuration
            config: The configuration to save
            
        Returns:
            Result containing the saved configuration
        """
        try:
            file_path = self.base_dir / f"{name}.json"
            
            # Convert config to dict
            config_dict = config.to_dict()
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            return Success(config)
        except Exception as e:
            return Failure(ErrorDetails(
                code="SCHEMA_CONFIG_SAVE_ERROR",
                message=f"Error saving schema configuration: {str(e)}"
            ))
    
    def get(self, name: str) -> Result[SchemaConfiguration, ErrorDetails]:
        """
        Get a schema configuration by name from a file.
        
        Args:
            name: The name of the configuration to retrieve
            
        Returns:
            Result containing the configuration if found
        """
        file_path = self.base_dir / f"{name}.json"
        
        if not file_path.exists():
            return Failure(ErrorDetails(
                code="SCHEMA_CONFIG_NOT_FOUND",
                message=f"Schema configuration with name {name} not found"
            ))
        
        try:
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
            
            # This is a partial implementation - in a real system, we would 
            # deserialize the JSON back to a SchemaConfiguration object
            # For simplicity, we're returning a failure
            return Failure(ErrorDetails(
                code="NOT_IMPLEMENTED",
                message="Deserialization of schema configurations from file is not fully implemented"
            ))
        except Exception as e:
            return Failure(ErrorDetails(
                code="SCHEMA_CONFIG_LOAD_ERROR",
                message=f"Error loading schema configuration: {str(e)}"
            ))
    
    def list(self) -> Result[List[str], ErrorDetails]:
        """
        List all schema configuration names from files.
        
        Returns:
            Result containing a list of configuration names
        """
        try:
            config_names = [file_path.stem for file_path in self.base_dir.glob("*.json")]
            return Success(config_names)
        except Exception as e:
            return Failure(ErrorDetails(
                code="SCHEMA_CONFIG_LIST_ERROR",
                message=f"Error listing schema configurations: {str(e)}"
            ))
    
    def delete(self, name: str) -> Result[None, ErrorDetails]:
        """
        Delete a schema configuration file.
        
        Args:
            name: The name of the configuration to delete
            
        Returns:
            Result indicating success or failure
        """
        file_path = self.base_dir / f"{name}.json"
        
        if not file_path.exists():
            return Failure(ErrorDetails(
                code="SCHEMA_CONFIG_NOT_FOUND",
                message=f"Schema configuration with name {name} not found"
            ))
        
        try:
            os.remove(file_path)
            return Success(None)
        except Exception as e:
            return Failure(ErrorDetails(
                code="SCHEMA_CONFIG_DELETE_ERROR",
                message=f"Error deleting schema configuration: {str(e)}"
            ))