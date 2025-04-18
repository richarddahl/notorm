# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Repository implementations for schema entities in the DTO module.

This module provides repository interfaces and implementations for
persistent storage and retrieval of schema definitions and related objects.
"""

import uuid
import json
import os
from typing import Dict, List, Optional, Protocol, runtime_checkable, TypeVar
from pathlib import Path
from datetime import datetime, UTC

from uno.core.base.error import BaseError
from uno.dto.entities import SchemaDefinition, SchemaId, SchemaConfiguration


# Generic type parameters
SchemaDefT = TypeVar('SchemaDefT', bound=SchemaDefinition)
SchemaConfT = TypeVar('SchemaConfT', bound=SchemaConfiguration)


@runtime_checkable
class SchemaDefinitionRepositoryProtocol(Protocol[SchemaDefT]):
    """Protocol for repositories that store and retrieve schema definitions."""
    
    async def get_by_id(self, schema_id: uuid.UUID) -> Optional[SchemaDefT]:
        """Get a schema definition by ID."""
        ...
        
    async def get_by_name_version(self, name: str, version: str) -> Optional[SchemaDefT]:
        """Get a schema definition by name and version."""
        ...
        
    async def list_schemas(self, limit: int = 100, offset: int = 0) -> List[SchemaDefT]:
        """List schema definitions with pagination."""
        ...
        
    async def add(self, schema: SchemaDefT) -> SchemaDefT:
        """Add a new schema definition."""
        ...
        
    async def update(self, schema: SchemaDefT) -> SchemaDefT:
        """Update an existing schema definition."""
        ...
        
    async def delete(self, schema_id: uuid.UUID) -> bool:
        """Delete a schema definition by ID."""
        ...


@runtime_checkable
class SchemaConfigurationRepositoryProtocol(Protocol[SchemaConfT]):
    """Protocol for repositories that store and retrieve schema configurations."""
    
    async def get_by_schema_id(self, schema_id: uuid.UUID) -> Optional[SchemaConfT]:
        """Get a schema configuration by schema ID."""
        ...
        
    async def get_by_name_version(self, name: str, version: str) -> Optional[SchemaConfT]:
        """Get a schema configuration by schema name and version."""
        ...
        
    async def add(self, schema_id: uuid.UUID, config: SchemaConfT) -> SchemaConfT:
        """Add a new schema configuration."""
        ...
        
    async def update(self, schema_id: uuid.UUID, config: SchemaConfT) -> SchemaConfT:
        """Update an existing schema configuration."""
        ...
        
    async def delete(self, schema_id: uuid.UUID) -> bool:
        """Delete a schema configuration by schema ID."""
        ...


class InMemorySchemaDefinitionRepository:
    """In-memory implementation of the schema definition repository."""
    
    def __init__(self):
        """Initialize the repository with an empty dictionary."""
        self.schemas: Dict[uuid.UUID, SchemaDefinition] = {}
        self.name_version_map: Dict[str, uuid.UUID] = {}
        
    async def get_by_id(self, schema_id: uuid.UUID) -> Optional[SchemaDefinition]:
        """Get a schema definition by ID."""
        return self.schemas.get(schema_id)
        
    async def get_by_name_version(self, name: str, version: str) -> Optional[SchemaDefinition]:
        """Get a schema definition by name and version."""
        key = f"{name}:{version}"
        schema_id = self.name_version_map.get(key)
        if schema_id:
            return self.schemas.get(schema_id)
        return None
        
    async def list_schemas(self, limit: int = 100, offset: int = 0) -> List[SchemaDefinition]:
        """List schema definitions with pagination."""
        schemas = list(self.schemas.values())
        return schemas[offset:offset + limit]
        
    async def add(self, schema: SchemaDefinition) -> SchemaDefinition:
        """Add a new schema definition."""
        key = f"{schema.id.name}:{schema.id.version}"
        if key in self.name_version_map:
            raise BaseError(
                f"Schema with name {schema.id.name} and version {schema.id.version} already exists",
                "SCHEMA_ALREADY_EXISTS",
                schema_name=schema.id.name,
                schema_version=schema.id.version
            )
            
        # Store the schema
        self.schemas[schema.id.id] = schema
        self.name_version_map[key] = schema.id.id
        return schema
        
    async def update(self, schema: SchemaDefinition) -> SchemaDefinition:
        """Update an existing schema definition."""
        if schema.id.id not in self.schemas:
            raise BaseError(
                f"Schema with ID {schema.id.id} not found",
                "SCHEMA_NOT_FOUND",
                schema_id=str(schema.id.id)
            )
            
        # Update the schema
        schema.updated_at = datetime.now(UTC)
        self.schemas[schema.id.id] = schema
        return schema
        
    async def delete(self, schema_id: uuid.UUID) -> bool:
        """Delete a schema definition by ID."""
        if schema_id not in self.schemas:
            return False
            
        # Get the schema to remove the name-version mapping
        schema = self.schemas[schema_id]
        key = f"{schema.id.name}:{schema.id.version}"
        
        # Remove the schema
        del self.schemas[schema_id]
        if key in self.name_version_map:
            del self.name_version_map[key]
            
        return True


class InMemorySchemaConfigurationRepository:
    """In-memory implementation of the schema configuration repository."""
    
    def __init__(self):
        """Initialize the repository with an empty dictionary."""
        self.configs: Dict[uuid.UUID, SchemaConfiguration] = {}
        self.name_version_map: Dict[str, uuid.UUID] = {}
        
    async def get_by_schema_id(self, schema_id: uuid.UUID) -> Optional[SchemaConfiguration]:
        """Get a schema configuration by schema ID."""
        return self.configs.get(schema_id)
        
    async def get_by_name_version(self, name: str, version: str) -> Optional[SchemaConfiguration]:
        """Get a schema configuration by schema name and version."""
        key = f"{name}:{version}"
        schema_id = self.name_version_map.get(key)
        if schema_id:
            return self.configs.get(schema_id)
        return None
        
    async def add(self, schema_id: uuid.UUID, config: SchemaConfiguration) -> SchemaConfiguration:
        """Add a new schema configuration."""
        if schema_id in self.configs:
            raise BaseError(
                f"Configuration for schema with ID {schema_id} already exists",
                "SCHEMA_CONFIG_ALREADY_EXISTS",
                schema_id=str(schema_id)
            )
            
        # Store the configuration
        self.configs[schema_id] = config
        return config
        
    async def update(self, schema_id: uuid.UUID, config: SchemaConfiguration) -> SchemaConfiguration:
        """Update an existing schema configuration."""
        if schema_id not in self.configs:
            raise BaseError(
                f"Configuration for schema with ID {schema_id} not found",
                "SCHEMA_CONFIG_NOT_FOUND",
                schema_id=str(schema_id)
            )
            
        # Update the configuration
        self.configs[schema_id] = config
        return config
        
    async def delete(self, schema_id: uuid.UUID) -> bool:
        """Delete a schema configuration by schema ID."""
        if schema_id not in self.configs:
            return False
            
        # Remove the configuration
        del self.configs[schema_id]
        return True


class FileSchemaDefinitionRepository:
    """File-based implementation of the schema definition repository."""
    
    def __init__(self, directory: str):
        """
        Initialize the repository with a directory path.
        
        Args:
            directory: The directory to store schema files in
        """
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.schemas: Dict[uuid.UUID, SchemaDefinition] = {}
        self.name_version_map: Dict[str, uuid.UUID] = {}
        self._load_schemas()
        
    def _load_schemas(self) -> None:
        """Load schemas from the directory."""
        for file_path in self.directory.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    schema = SchemaDefinition.model_validate(data)
                    self.schemas[schema.id.id] = schema
                    key = f"{schema.id.name}:{schema.id.version}"
                    self.name_version_map[key] = schema.id.id
            except Exception as e:
                # Log error but continue loading other schemas
                print(f"Error loading schema from {file_path}: {str(e)}")
                
    def _save_schema(self, schema: SchemaDefinition) -> None:
        """Save a schema to a file."""
        file_path = self.directory / f"{schema.id.id}.json"
        with open(file_path, "w") as f:
            f.write(schema.model_dump_json(indent=2))
        
    async def get_by_id(self, schema_id: uuid.UUID) -> Optional[SchemaDefinition]:
        """Get a schema definition by ID."""
        return self.schemas.get(schema_id)
        
    async def get_by_name_version(self, name: str, version: str) -> Optional[SchemaDefinition]:
        """Get a schema definition by name and version."""
        key = f"{name}:{version}"
        schema_id = self.name_version_map.get(key)
        if schema_id:
            return self.schemas.get(schema_id)
        return None
        
    async def list_schemas(self, limit: int = 100, offset: int = 0) -> List[SchemaDefinition]:
        """List schema definitions with pagination."""
        schemas = list(self.schemas.values())
        return schemas[offset:offset + limit]
        
    async def add(self, schema: SchemaDefinition) -> SchemaDefinition:
        """Add a new schema definition."""
        key = f"{schema.id.name}:{schema.id.version}"
        if key in self.name_version_map:
            raise BaseError(
                f"Schema with name {schema.id.name} and version {schema.id.version} already exists",
                "SCHEMA_ALREADY_EXISTS",
                schema_name=schema.id.name,
                schema_version=schema.id.version
            )
            
        # Store the schema
        self.schemas[schema.id.id] = schema
        self.name_version_map[key] = schema.id.id
        self._save_schema(schema)
        return schema
        
    async def update(self, schema: SchemaDefinition) -> SchemaDefinition:
        """Update an existing schema definition."""
        if schema.id.id not in self.schemas:
            raise BaseError(
                f"Schema with ID {schema.id.id} not found",
                "SCHEMA_NOT_FOUND",
                schema_id=str(schema.id.id)
            )
            
        # Update the schema
        schema.updated_at = datetime.now(UTC)
        self.schemas[schema.id.id] = schema
        self._save_schema(schema)
        return schema
        
    async def delete(self, schema_id: uuid.UUID) -> bool:
        """Delete a schema definition by ID."""
        if schema_id not in self.schemas:
            return False
            
        # Get the schema to remove the name-version mapping
        schema = self.schemas[schema_id]
        key = f"{schema.id.name}:{schema.id.version}"
        
        # Remove the schema file
        file_path = self.directory / f"{schema_id}.json"
        if file_path.exists():
            os.remove(file_path)
            
        # Remove from memory
        del self.schemas[schema_id]
        if key in self.name_version_map:
            del self.name_version_map[key]
            
        return True


class FileSchemaConfigurationRepository:
    """File-based implementation of the schema configuration repository."""
    
    def __init__(self, directory: str):
        """
        Initialize the repository with a directory path.
        
        Args:
            directory: The directory to store configuration files in
        """
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.configs: Dict[uuid.UUID, SchemaConfiguration] = {}
        self._load_configs()
        
    def _load_configs(self) -> None:
        """Load configurations from the directory."""
        for file_path in self.directory.glob("*.config.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    config = SchemaConfiguration.model_validate(data["config"])
                    schema_id = uuid.UUID(data["schema_id"])
                    self.configs[schema_id] = config
            except Exception as e:
                # Log error but continue loading other configurations
                print(f"Error loading configuration from {file_path}: {str(e)}")
                
    def _save_config(self, schema_id: uuid.UUID, config: SchemaConfiguration) -> None:
        """Save a configuration to a file."""
        data = {
            "schema_id": str(schema_id),
            "config": config.model_dump()
        }
        file_path = self.directory / f"{schema_id}.config.json"
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
    async def get_by_schema_id(self, schema_id: uuid.UUID) -> Optional[SchemaConfiguration]:
        """Get a schema configuration by schema ID."""
        return self.configs.get(schema_id)
        
    async def get_by_name_version(self, name: str, version: str) -> Optional[SchemaConfiguration]:
        """Get a schema configuration by schema name and version."""
        # This implementation requires a schema ID, which we don't have from name/version
        # In a real implementation, we would need to look up the schema ID first
        return None
        
    async def add(self, schema_id: uuid.UUID, config: SchemaConfiguration) -> SchemaConfiguration:
        """Add a new schema configuration."""
        if schema_id in self.configs:
            raise BaseError(
                f"Configuration for schema with ID {schema_id} already exists",
                "SCHEMA_CONFIG_ALREADY_EXISTS",
                schema_id=str(schema_id)
            )
            
        # Store the configuration
        self.configs[schema_id] = config
        self._save_config(schema_id, config)
        return config
        
    async def update(self, schema_id: uuid.UUID, config: SchemaConfiguration) -> SchemaConfiguration:
        """Update an existing schema configuration."""
        if schema_id not in self.configs:
            raise BaseError(
                f"Configuration for schema with ID {schema_id} not found",
                "SCHEMA_CONFIG_NOT_FOUND",
                schema_id=str(schema_id)
            )
            
        # Update the configuration
        self.configs[schema_id] = config
        self._save_config(schema_id, config)
        return config
        
    async def delete(self, schema_id: uuid.UUID) -> bool:
        """Delete a schema configuration by schema ID."""
        if schema_id not in self.configs:
            return False
            
        # Remove the configuration file
        file_path = self.directory / f"{schema_id}.config.json"
        if file_path.exists():
            os.remove(file_path)
            
        # Remove from memory
        del self.configs[schema_id]
        return True