"""
Service pattern protocol definitions.

This module defines the protocols (interfaces) for the service pattern,
establishing clear contracts for all service implementations.
"""

from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar, runtime_checkable

from uno.core.errors.result import Result

# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type
InputT = TypeVar("InputT")  # Input type
OutputT = TypeVar("OutputT")  # Output type
ParamsT = TypeVar("ParamsT")  # Parameters type


@runtime_checkable
class ServiceProtocol(Protocol[InputT, OutputT]):
    """
    Protocol for the basic service pattern.
    
    Services encapsulate domain logic and business operations, coordinating
    between domain objects and infrastructure components.
    """
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the service operation.
        
        Args:
            input_data: The input data for the operation
            
        Returns:
            A Result containing either the operation result or error information
        """
        ...


@runtime_checkable
class CrudServiceProtocol(Protocol[T, ID]):
    """
    Protocol for CRUD service operations.
    
    Defines the standard operations for managing domain entities:
    Create, Read, Update, and Delete.
    """
    
    async def get(self, id: ID) -> Result[Optional[T]]:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            
        Returns:
            Result containing the entity or None if not found
        """
        ...
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Result[List[T]]:
        """
        List entities with optional filtering, ordering, and pagination.
        
        Args:
            filters: Optional filters to apply
            order_by: Optional ordering
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            Result containing the list of matching entities
        """
        ...
    
    async def create(self, data: Dict[str, Any]) -> Result[T]:
        """
        Create a new entity.
        
        Args:
            data: Entity data
            
        Returns:
            Result containing the created entity
        """
        ...
    
    async def update(self, id: ID, data: Dict[str, Any]) -> Result[T]:
        """
        Update an existing entity.
        
        Args:
            id: Entity ID
            data: Updated entity data
            
        Returns:
            Result containing the updated entity
        """
        ...
    
    async def delete(self, id: ID) -> Result[bool]:
        """
        Delete an entity.
        
        Args:
            id: Entity ID
            
        Returns:
            Result indicating success or failure
        """
        ...


@runtime_checkable
class AggregateCrudServiceProtocol(CrudServiceProtocol[T, ID], Protocol[T, ID]):
    """
    Protocol for aggregate CRUD service operations.
    
    Extends the standard CRUD service with operations specific to aggregate roots,
    such as version-based optimistic concurrency control.
    """
    
    async def update_with_version(
        self, id: ID, version: int, data: Dict[str, Any]
    ) -> Result[T]:
        """
        Update an aggregate with optimistic concurrency control.
        
        Args:
            id: Aggregate ID
            version: Expected current version for concurrency control
            data: Updated aggregate data
            
        Returns:
            Result containing the updated aggregate
        """
        ...
    
    async def delete_with_version(self, id: ID, version: int) -> Result[bool]:
        """
        Delete an aggregate with optimistic concurrency control.
        
        Args:
            id: Aggregate ID
            version: Expected current version for concurrency control
            
        Returns:
            Result indicating success or failure
        """
        ...


@runtime_checkable
class QueryServiceProtocol(Protocol[ParamsT, OutputT]):
    """
    Protocol for query service operations.
    
    Query services handle read-only operations, retrieving and transforming data
    without modifying domain state.
    """
    
    async def execute_query(self, params: ParamsT) -> Result[OutputT]:
        """
        Execute a query operation.
        
        Args:
            params: Query parameters
            
        Returns:
            Result containing the query results
        """
        ...
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count entities matching filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Result containing the count
        """
        ...


@runtime_checkable
class ApplicationServiceProtocol(Protocol[InputT, OutputT]):
    """
    Protocol for application services.
    
    Application services coordinate complex operations that may involve
    multiple domain services, external systems, or infrastructure components.
    """
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the application service operation.
        
        Args:
            input_data: Input data for the operation
            
        Returns:
            Result containing the operation result
        """
        ...
    
    async def validate(self, input_data: InputT) -> Optional[Result[OutputT]]:
        """
        Validate input data before execution.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            None if validation passes, or Failure result if validation fails
        """
        ...


@runtime_checkable
class DomainEventPublisherProtocol(Protocol):
    """
    Protocol for domain event publishing.
    
    Domain event publishers are responsible for collecting and publishing
    domain events to interested subscribers.
    """
    
    def publish_event(self, event: Any) -> None:
        """
        Publish a domain event.
        
        Args:
            event: The domain event to publish
        """
        ...
    
    def publish_events(self, events: List[Any]) -> None:
        """
        Publish multiple domain events.
        
        Args:
            events: The domain events to publish
        """
        ...