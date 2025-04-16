"""
Repository implementations for the API module.

This module defines repository protocols and implementations for the API module,
including repositories for API resources, endpoint configurations, and other
domain entities.
"""

from typing import List, Optional, Dict, Any, Protocol, Type, TypeVar, Generic
from dataclasses import dataclass
import os
import json
import logging
from pathlib import Path

from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.catalog import ErrorCodes, UnoError
from uno.domain.repositories import Repository

from .entities import ApiResource, EndpointConfig


# Type variables
T = TypeVar('T')
ResourceT = TypeVar('ResourceT', bound=ApiResource)


class ApiResourceRepositoryProtocol(Repository[ApiResource, str], Protocol):
    """
    Protocol for API resource repositories.
    
    This protocol defines the interface for repositories that manage API resources,
    including methods for retrieving, creating, updating, and deleting resources.
    """
    
    async def get_by_name(self, name: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by name.
        
        Args:
            name: The name of the resource to retrieve
            
        Returns:
            Result containing the API resource if found, or None if not found
        """
        ...
    
    async def get_by_path_prefix(self, path_prefix: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by path prefix.
        
        Args:
            path_prefix: The path prefix of the resource to retrieve
            
        Returns:
            Result containing the API resource if found, or None if not found
        """
        ...
    
    async def get_by_entity_type(self, entity_type_name: str) -> Result[List[ApiResource]]:
        """
        Get all API resources for a specific entity type.
        
        Args:
            entity_type_name: The name of the entity type
            
        Returns:
            Result containing a list of API resources for the entity type
        """
        ...


class EndpointConfigRepositoryProtocol(Repository[EndpointConfig, str], Protocol):
    """
    Protocol for endpoint configuration repositories.
    
    This protocol defines the interface for repositories that manage endpoint configurations,
    including methods for retrieving, creating, updating, and deleting endpoint configs.
    """
    
    async def get_by_path(self, path: str) -> Result[List[EndpointConfig]]:
        """
        Get all endpoint configurations for a specific path.
        
        Args:
            path: The path to search for
            
        Returns:
            Result containing a list of endpoint configurations for the path
        """
        ...
    
    async def get_by_resource_id(self, resource_id: str) -> Result[List[EndpointConfig]]:
        """
        Get all endpoint configurations for a specific API resource.
        
        Args:
            resource_id: The ID of the API resource
            
        Returns:
            Result containing a list of endpoint configurations for the resource
        """
        ...


@dataclass
class InMemoryApiResourceRepository(ApiResourceRepositoryProtocol):
    """
    In-memory implementation of the API resource repository.
    
    This repository stores API resources in memory, suitable for testing or
    simple applications that don't require persistence.
    """
    
    resources: Dict[str, ApiResource] = None
    logger: logging.Logger = None
    
    def __post_init__(self):
        """Initialize the repository with default values."""
        if self.resources is None:
            self.resources = {}
        if self.logger is None:
            self.logger = logging.getLogger(__name__)
    
    async def get_by_id(self, id: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by ID.
        
        Args:
            id: The ID of the resource to retrieve
            
        Returns:
            Result containing the API resource if found, or None if not found
        """
        if id in self.resources:
            return Success(self.resources[id])
        return Success(None)
    
    async def get_by_name(self, name: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by name.
        
        Args:
            name: The name of the resource to retrieve
            
        Returns:
            Result containing the API resource if found, or None if not found
        """
        for resource in self.resources.values():
            if resource.name == name:
                return Success(resource)
        return Success(None)
    
    async def get_by_path_prefix(self, path_prefix: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by path prefix.
        
        Args:
            path_prefix: The path prefix of the resource to retrieve
            
        Returns:
            Result containing the API resource if found, or None if not found
        """
        # Normalize path prefix
        if not path_prefix.startswith('/'):
            path_prefix = f'/{path_prefix}'
        
        for resource in self.resources.values():
            if resource.path_prefix == path_prefix:
                return Success(resource)
        return Success(None)
    
    async def get_by_entity_type(self, entity_type_name: str) -> Result[List[ApiResource]]:
        """
        Get all API resources for a specific entity type.
        
        Args:
            entity_type_name: The name of the entity type
            
        Returns:
            Result containing a list of API resources for the entity type
        """
        result = []
        for resource in self.resources.values():
            if resource.entity_type_name == entity_type_name:
                result.append(resource)
        return Success(result)
    
    async def list(self, filters: Optional[Dict[str, Any]] = None, options: Optional[Dict[str, Any]] = None) -> Result[List[ApiResource]]:
        """
        List API resources, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            options: Optional options for pagination, sorting, etc.
            
        Returns:
            Result containing a list of API resources
        """
        resources = list(self.resources.values())
        
        # Apply filters if provided
        if filters:
            filtered_resources = []
            for resource in resources:
                match = True
                for key, value in filters.items():
                    if hasattr(resource, key):
                        attr_value = getattr(resource, key)
                        if attr_value != value:
                            match = False
                            break
                    else:
                        match = False
                        break
                if match:
                    filtered_resources.append(resource)
            resources = filtered_resources
        
        # Apply pagination if provided
        if options and "pagination" in options:
            pagination = options["pagination"]
            limit = pagination.get("limit", 100)
            offset = pagination.get("offset", 0)
            resources = resources[offset:offset+limit]
        
        return Success(resources)
    
    async def add(self, resource: ApiResource) -> Result[ApiResource]:
        """
        Add a new API resource.
        
        Args:
            resource: The API resource to add
            
        Returns:
            Result containing the added API resource
        """
        # Check for existing resource with same ID
        if resource.id in self.resources:
            return Failure(UnoError(
                code=ErrorCodes.DUPLICATE_RESOURCE,
                message=f"API resource with ID '{resource.id}' already exists",
                context={"resource_id": resource.id}
            ))
        
        # Validate the resource
        try:
            resource.validate()
        except ValueError as e:
            return Failure(UnoError(
                code=ErrorCodes.VALIDATION_ERROR,
                message=str(e),
                context={"resource": resource}
            ))
        
        # Add the resource
        self.resources[resource.id] = resource
        return Success(resource)
    
    async def update(self, resource: ApiResource) -> Result[ApiResource]:
        """
        Update an existing API resource.
        
        Args:
            resource: The API resource to update
            
        Returns:
            Result containing the updated API resource
        """
        # Check if resource exists
        if resource.id not in self.resources:
            return Failure(UnoError(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"API resource with ID '{resource.id}' not found",
                context={"resource_id": resource.id}
            ))
        
        # Validate the resource
        try:
            resource.validate()
        except ValueError as e:
            return Failure(UnoError(
                code=ErrorCodes.VALIDATION_ERROR,
                message=str(e),
                context={"resource": resource}
            ))
        
        # Update the resource
        self.resources[resource.id] = resource
        return Success(resource)
    
    async def delete(self, id: str) -> Result[bool]:
        """
        Delete an API resource.
        
        Args:
            id: The ID of the resource to delete
            
        Returns:
            Result containing a boolean indicating success
        """
        if id in self.resources:
            del self.resources[id]
            return Success(True)
        return Success(False)  # Not an error if resource doesn't exist
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count API resources, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Result containing the count of API resources
        """
        if filters:
            # Apply filters and count the result
            list_result = await self.list(filters=filters)
            if list_result.is_failure():
                return Failure(list_result.error)
            return Success(len(list_result.value))
        
        # Simple count without filters
        return Success(len(self.resources))


@dataclass
class InMemoryEndpointConfigRepository(EndpointConfigRepositoryProtocol):
    """
    In-memory implementation of the endpoint configuration repository.
    
    This repository stores endpoint configurations in memory, suitable for testing or
    simple applications that don't require persistence.
    """
    
    endpoints: Dict[str, EndpointConfig] = None
    endpoints_by_resource: Dict[str, List[str]] = None
    logger: logging.Logger = None
    
    def __post_init__(self):
        """Initialize the repository with default values."""
        if self.endpoints is None:
            self.endpoints = {}
        if self.endpoints_by_resource is None:
            self.endpoints_by_resource = {}
        if self.logger is None:
            self.logger = logging.getLogger(__name__)
    
    async def get_by_id(self, id: str) -> Result[Optional[EndpointConfig]]:
        """
        Get an endpoint configuration by ID.
        
        Args:
            id: The ID of the endpoint configuration to retrieve
            
        Returns:
            Result containing the endpoint configuration if found, or None if not found
        """
        if id in self.endpoints:
            return Success(self.endpoints[id])
        return Success(None)
    
    async def get_by_path(self, path: str) -> Result[List[EndpointConfig]]:
        """
        Get all endpoint configurations for a specific path.
        
        Args:
            path: The path to search for
            
        Returns:
            Result containing a list of endpoint configurations for the path
        """
        result = []
        for endpoint in self.endpoints.values():
            if endpoint.path == path:
                result.append(endpoint)
        return Success(result)
    
    async def get_by_resource_id(self, resource_id: str) -> Result[List[EndpointConfig]]:
        """
        Get all endpoint configurations for a specific API resource.
        
        Args:
            resource_id: The ID of the API resource
            
        Returns:
            Result containing a list of endpoint configurations for the resource
        """
        if resource_id in self.endpoints_by_resource:
            endpoint_ids = self.endpoints_by_resource[resource_id]
            result = [self.endpoints[id] for id in endpoint_ids if id in self.endpoints]
            return Success(result)
        return Success([])
    
    async def list(self, filters: Optional[Dict[str, Any]] = None, options: Optional[Dict[str, Any]] = None) -> Result[List[EndpointConfig]]:
        """
        List endpoint configurations, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            options: Optional options for pagination, sorting, etc.
            
        Returns:
            Result containing a list of endpoint configurations
        """
        endpoints = list(self.endpoints.values())
        
        # Apply filters if provided
        if filters:
            filtered_endpoints = []
            for endpoint in endpoints:
                match = True
                for key, value in filters.items():
                    if hasattr(endpoint, key):
                        attr_value = getattr(endpoint, key)
                        if attr_value != value:
                            match = False
                            break
                    else:
                        match = False
                        break
                if match:
                    filtered_endpoints.append(endpoint)
            endpoints = filtered_endpoints
        
        # Apply pagination if provided
        if options and "pagination" in options:
            pagination = options["pagination"]
            limit = pagination.get("limit", 100)
            offset = pagination.get("offset", 0)
            endpoints = endpoints[offset:offset+limit]
        
        return Success(endpoints)
    
    async def add(self, endpoint: EndpointConfig) -> Result[EndpointConfig]:
        """
        Add a new endpoint configuration.
        
        Args:
            endpoint: The endpoint configuration to add
            
        Returns:
            Result containing the added endpoint configuration
        """
        # Check for existing endpoint with same ID
        if endpoint.id in self.endpoints:
            return Failure(UnoError(
                code=ErrorCodes.DUPLICATE_RESOURCE,
                message=f"Endpoint configuration with ID '{endpoint.id}' already exists",
                context={"endpoint_id": endpoint.id}
            ))
        
        # Validate the endpoint
        try:
            endpoint.validate()
        except ValueError as e:
            return Failure(UnoError(
                code=ErrorCodes.VALIDATION_ERROR,
                message=str(e),
                context={"endpoint": endpoint}
            ))
        
        # Add the endpoint
        self.endpoints[endpoint.id] = endpoint
        
        # Add to resource index if resource_id is available
        if hasattr(endpoint, 'resource_id') and endpoint.resource_id:
            resource_id = endpoint.resource_id
            if resource_id not in self.endpoints_by_resource:
                self.endpoints_by_resource[resource_id] = []
            self.endpoints_by_resource[resource_id].append(endpoint.id)
        
        return Success(endpoint)
    
    async def update(self, endpoint: EndpointConfig) -> Result[EndpointConfig]:
        """
        Update an existing endpoint configuration.
        
        Args:
            endpoint: The endpoint configuration to update
            
        Returns:
            Result containing the updated endpoint configuration
        """
        # Check if endpoint exists
        if endpoint.id not in self.endpoints:
            return Failure(UnoError(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Endpoint configuration with ID '{endpoint.id}' not found",
                context={"endpoint_id": endpoint.id}
            ))
        
        # Validate the endpoint
        try:
            endpoint.validate()
        except ValueError as e:
            return Failure(UnoError(
                code=ErrorCodes.VALIDATION_ERROR,
                message=str(e),
                context={"endpoint": endpoint}
            ))
        
        # Get old endpoint to update resource index if needed
        old_endpoint = self.endpoints[endpoint.id]
        
        # Update the endpoint
        self.endpoints[endpoint.id] = endpoint
        
        # Update resource index if resource_id changed
        if (hasattr(old_endpoint, 'resource_id') and hasattr(endpoint, 'resource_id') and 
                old_endpoint.resource_id != endpoint.resource_id):
            
            # Remove from old resource
            if old_endpoint.resource_id and old_endpoint.resource_id in self.endpoints_by_resource:
                if endpoint.id in self.endpoints_by_resource[old_endpoint.resource_id]:
                    self.endpoints_by_resource[old_endpoint.resource_id].remove(endpoint.id)
            
            # Add to new resource
            if endpoint.resource_id:
                if endpoint.resource_id not in self.endpoints_by_resource:
                    self.endpoints_by_resource[endpoint.resource_id] = []
                self.endpoints_by_resource[endpoint.resource_id].append(endpoint.id)
        
        return Success(endpoint)
    
    async def delete(self, id: str) -> Result[bool]:
        """
        Delete an endpoint configuration.
        
        Args:
            id: The ID of the endpoint configuration to delete
            
        Returns:
            Result containing a boolean indicating success
        """
        if id in self.endpoints:
            # Get endpoint to update resource index
            endpoint = self.endpoints[id]
            
            # Delete endpoint
            del self.endpoints[id]
            
            # Update resource index
            if hasattr(endpoint, 'resource_id') and endpoint.resource_id:
                resource_id = endpoint.resource_id
                if resource_id in self.endpoints_by_resource and id in self.endpoints_by_resource[resource_id]:
                    self.endpoints_by_resource[resource_id].remove(id)
            
            return Success(True)
        return Success(False)  # Not an error if endpoint doesn't exist
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count endpoint configurations, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Result containing the count of endpoint configurations
        """
        if filters:
            # Apply filters and count the result
            list_result = await self.list(filters=filters)
            if list_result.is_failure():
                return Failure(list_result.error)
            return Success(len(list_result.value))
        
        # Simple count without filters
        return Success(len(self.endpoints))


@dataclass
class FileApiResourceRepository(ApiResourceRepositoryProtocol):
    """
    File-based implementation of the API resource repository.
    
    This repository stores API resources in JSON files, providing simple
    persistence between application restarts.
    """
    
    directory: str
    logger: logging.Logger = None
    resources: Dict[str, ApiResource] = None
    
    def __post_init__(self):
        """Initialize the repository and ensure the directory exists."""
        if self.logger is None:
            self.logger = logging.getLogger(__name__)
        
        if self.resources is None:
            self.resources = {}
        
        # Ensure directory exists
        os.makedirs(self.directory, exist_ok=True)
        
        # Load resources from directory
        self._load_resources()
    
    def _load_resources(self) -> None:
        """Load resources from the directory."""
        try:
            resource_dir = Path(self.directory)
            for file_path in resource_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    # Create ApiResource from JSON data
                    resource = ApiResource(
                        id=data.get("id"),
                        name=data.get("name"),
                        path_prefix=data.get("path_prefix"),
                        entity_type_name=data.get("entity_type_name"),
                        tags=data.get("tags", []),
                        description=data.get("description")
                    )
                    
                    # Load endpoints if available
                    endpoints = []
                    for endpoint_data in data.get("endpoints", []):
                        endpoint = EndpointConfig(
                            id=endpoint_data.get("id"),
                            path=endpoint_data.get("path"),
                            method=endpoint_data.get("method"),
                            tags=endpoint_data.get("tags", []),
                            summary=endpoint_data.get("summary"),
                            description=endpoint_data.get("description"),
                            operation_id=endpoint_data.get("operation_id"),
                            deprecated=endpoint_data.get("deprecated", False),
                            security=endpoint_data.get("security", []),
                            responses=endpoint_data.get("responses", {})
                        )
                        endpoints.append(endpoint)
                    
                    resource.endpoints = endpoints
                    self.resources[resource.id] = resource
                    
                except Exception as e:
                    self.logger.error(f"Error loading resource from {file_path}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error loading resources: {str(e)}")
    
    def _save_resource(self, resource: ApiResource) -> None:
        """
        Save a resource to a file.
        
        Args:
            resource: The resource to save
        """
        try:
            file_path = os.path.join(self.directory, f"{resource.id}.json")
            
            # Convert resource to dict
            resource_dict = {
                "id": resource.id,
                "name": resource.name,
                "path_prefix": resource.path_prefix,
                "entity_type_name": resource.entity_type_name,
                "tags": resource.tags,
                "description": resource.description,
                "endpoints": []
            }
            
            # Add endpoints
            for endpoint in resource.endpoints:
                endpoint_dict = {
                    "id": endpoint.id,
                    "path": endpoint.path,
                    "method": endpoint.method.value,
                    "tags": endpoint.tags,
                    "summary": endpoint.summary,
                    "description": endpoint.description,
                    "operation_id": endpoint.operation_id,
                    "deprecated": endpoint.deprecated,
                    "security": endpoint.security,
                    "responses": endpoint.responses
                }
                resource_dict["endpoints"].append(endpoint_dict)
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(resource_dict, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving resource {resource.id}: {str(e)}")
    
    async def get_by_id(self, id: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by ID.
        
        Args:
            id: The ID of the resource to retrieve
            
        Returns:
            Result containing the API resource if found, or None if not found
        """
        if id in self.resources:
            return Success(self.resources[id])
        return Success(None)
    
    async def get_by_name(self, name: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by name.
        
        Args:
            name: The name of the resource to retrieve
            
        Returns:
            Result containing the API resource if found, or None if not found
        """
        for resource in self.resources.values():
            if resource.name == name:
                return Success(resource)
        return Success(None)
    
    async def get_by_path_prefix(self, path_prefix: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by path prefix.
        
        Args:
            path_prefix: The path prefix of the resource to retrieve
            
        Returns:
            Result containing the API resource if found, or None if not found
        """
        # Normalize path prefix
        if not path_prefix.startswith('/'):
            path_prefix = f'/{path_prefix}'
        
        for resource in self.resources.values():
            if resource.path_prefix == path_prefix:
                return Success(resource)
        return Success(None)
    
    async def get_by_entity_type(self, entity_type_name: str) -> Result[List[ApiResource]]:
        """
        Get all API resources for a specific entity type.
        
        Args:
            entity_type_name: The name of the entity type
            
        Returns:
            Result containing a list of API resources for the entity type
        """
        result = []
        for resource in self.resources.values():
            if resource.entity_type_name == entity_type_name:
                result.append(resource)
        return Success(result)
    
    async def list(self, filters: Optional[Dict[str, Any]] = None, options: Optional[Dict[str, Any]] = None) -> Result[List[ApiResource]]:
        """
        List API resources, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            options: Optional options for pagination, sorting, etc.
            
        Returns:
            Result containing a list of API resources
        """
        resources = list(self.resources.values())
        
        # Apply filters if provided
        if filters:
            filtered_resources = []
            for resource in resources:
                match = True
                for key, value in filters.items():
                    if hasattr(resource, key):
                        attr_value = getattr(resource, key)
                        if attr_value != value:
                            match = False
                            break
                    else:
                        match = False
                        break
                if match:
                    filtered_resources.append(resource)
            resources = filtered_resources
        
        # Apply pagination if provided
        if options and "pagination" in options:
            pagination = options["pagination"]
            limit = pagination.get("limit", 100)
            offset = pagination.get("offset", 0)
            resources = resources[offset:offset+limit]
        
        return Success(resources)
    
    async def add(self, resource: ApiResource) -> Result[ApiResource]:
        """
        Add a new API resource.
        
        Args:
            resource: The API resource to add
            
        Returns:
            Result containing the added API resource
        """
        # Check for existing resource with same ID
        if resource.id in self.resources:
            return Failure(UnoError(
                code=ErrorCodes.DUPLICATE_RESOURCE,
                message=f"API resource with ID '{resource.id}' already exists",
                context={"resource_id": resource.id}
            ))
        
        # Validate the resource
        try:
            resource.validate()
        except ValueError as e:
            return Failure(UnoError(
                code=ErrorCodes.VALIDATION_ERROR,
                message=str(e),
                context={"resource": resource}
            ))
        
        # Add the resource
        self.resources[resource.id] = resource
        
        # Save to file
        self._save_resource(resource)
        
        return Success(resource)
    
    async def update(self, resource: ApiResource) -> Result[ApiResource]:
        """
        Update an existing API resource.
        
        Args:
            resource: The API resource to update
            
        Returns:
            Result containing the updated API resource
        """
        # Check if resource exists
        if resource.id not in self.resources:
            return Failure(UnoError(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"API resource with ID '{resource.id}' not found",
                context={"resource_id": resource.id}
            ))
        
        # Validate the resource
        try:
            resource.validate()
        except ValueError as e:
            return Failure(UnoError(
                code=ErrorCodes.VALIDATION_ERROR,
                message=str(e),
                context={"resource": resource}
            ))
        
        # Update the resource
        self.resources[resource.id] = resource
        
        # Save to file
        self._save_resource(resource)
        
        return Success(resource)
    
    async def delete(self, id: str) -> Result[bool]:
        """
        Delete an API resource.
        
        Args:
            id: The ID of the resource to delete
            
        Returns:
            Result containing a boolean indicating success
        """
        if id in self.resources:
            # Remove from memory
            del self.resources[id]
            
            # Remove file if it exists
            file_path = os.path.join(self.directory, f"{id}.json")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    self.logger.error(f"Error deleting resource file {file_path}: {str(e)}")
            
            return Success(True)
        return Success(False)  # Not an error if resource doesn't exist
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count API resources, optionally filtered.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Result containing the count of API resources
        """
        if filters:
            # Apply filters and count the result
            list_result = await self.list(filters=filters)
            if list_result.is_failure():
                return Failure(list_result.error)
            return Success(len(list_result.value))
        
        # Simple count without filters
        return Success(len(self.resources))