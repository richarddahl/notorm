"""
Domain entities for the API module.

This module defines domain entities used by the API module, such as endpoint configurations,
API resources, and other domain objects needed for API functionality.
"""

from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Dict, Any, Set
from enum import Enum

from uno.domain.core import Entity, AggregateRoot


class HttpMethod(Enum):
    """HTTP methods for API endpoints."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class EndpointConfig(Entity[str]):
    """
    Domain entity for API endpoint configuration.
    
    This entity defines the configuration for an API endpoint, including the path,
    method, tags, and other metadata needed to create and document the endpoint.
    """
    
    id: str  # Unique identifier for the endpoint
    path: str  # URL path for the endpoint
    method: HttpMethod  # HTTP method for the endpoint
    tags: List[str] = field(default_factory=list)  # OpenAPI tags
    summary: Optional[str] = None  # OpenAPI summary
    description: Optional[str] = None  # OpenAPI description
    operation_id: Optional[str] = None  # OpenAPI operationId
    deprecated: bool = False  # Whether the endpoint is deprecated
    
    # Custom metadata
    security: List[Dict[str, List[str]]] = field(default_factory=list)
    responses: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize after dataclass creation."""
        # Ensure method is an enum
        if isinstance(self.method, str):
            self.method = HttpMethod(self.method)
    
    def validate(self) -> None:
        """Validate the endpoint configuration."""
        if not self.id:
            raise ValueError("Endpoint ID cannot be empty")
        if not self.path:
            raise ValueError("Endpoint path cannot be empty")
        if not isinstance(self.method, HttpMethod):
            raise ValueError(f"Invalid HTTP method: {self.method}")


@dataclass
class ApiResource(AggregateRoot[str]):
    """
    Domain entity for an API resource.
    
    This entity defines a resource in the API, which is a collection of related
    endpoints that operate on the same domain entity type.
    """
    
    id: str  # Unique identifier for the resource
    name: str  # Name of the resource
    path_prefix: str  # URL path prefix for all endpoints in this resource
    entity_type_name: str  # Name of the entity type this resource operates on
    tags: List[str] = field(default_factory=list)  # OpenAPI tags for all endpoints
    description: Optional[str] = None  # Description of the resource
    
    # Related endpoints
    endpoints: List[EndpointConfig] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate the API resource."""
        if not self.id:
            raise ValueError("Resource ID cannot be empty")
        if not self.name:
            raise ValueError("Resource name cannot be empty")
        if not self.path_prefix:
            raise ValueError("Path prefix cannot be empty")
        if not self.entity_type_name:
            raise ValueError("Entity type name cannot be empty")
        
        # Path prefix should start with a slash
        if not self.path_prefix.startswith("/"):
            self.path_prefix = f"/{self.path_prefix}"
    
    def add_endpoint(self, endpoint: EndpointConfig) -> None:
        """
        Add an endpoint to this resource.
        
        Args:
            endpoint: The endpoint to add
        """
        if endpoint not in self.endpoints:
            self.endpoints.append(endpoint)
    
    def remove_endpoint(self, endpoint: EndpointConfig) -> None:
        """
        Remove an endpoint from this resource.
        
        Args:
            endpoint: The endpoint to remove
        """
        if endpoint in self.endpoints:
            self.endpoints.remove(endpoint)
    
    def get_endpoint(self, endpoint_id: str) -> Optional[EndpointConfig]:
        """
        Get an endpoint by ID.
        
        Args:
            endpoint_id: The ID of the endpoint to get
            
        Returns:
            The endpoint if found, None otherwise
        """
        for endpoint in self.endpoints:
            if endpoint.id == endpoint_id:
                return endpoint
        return None