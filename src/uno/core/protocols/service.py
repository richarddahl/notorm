"""
Service Protocol Definitions

This module defines the service pattern protocols used throughout the system.
Services encapsulate business logic and orchestrate domain operations.
"""

from collections.abc import Protocol
from typing import Any, TypeVar, runtime_checkable

from uno.core.errors.result import Result

# Type variables for service protocols
T = TypeVar('T')  # Entity/Domain object type
ID = TypeVar('ID')  # ID type (typically str, UUID, or int)
DTO = TypeVar('DTO')  # Data Transfer Object type for input/output


@runtime_checkable
class ServiceProtocol(Protocol[T, ID]):
    """
    Protocol defining the basic service pattern interface.
    
    Services encapsulate business logic and orchestrate operations
    on domain entities. They implement use cases by coordinating
    repositories and domain objects.
    
    Type parameters:
        T: The entity/domain object type this service manages
        ID: The type of the entity's identifier
    """
    
    async def get_by_id(self, id: ID) -> Result[T | None, Any]:
        """
        Retrieve an entity by its unique identifier.
        
        Args:
            id: The unique identifier of the entity
            
        Returns:
            Result containing the entity if found, or an error
        """
        ...
    
    async def get_all(self) -> Result[list[T], Any]:
        """
        Retrieve all entities of this type.
        
        Returns:
            Result containing a list of all entities, or an error
        """
        ...
    
    async def create(self, data: Any) -> Result[T, Any]:
        """
        Create a new entity.
        
        Args:
            data: The data for the new entity
            
        Returns:
            Result containing the created entity, or an error
        """
        ...
    
    async def update(self, id: ID, data: Any) -> Result[T, Any]:
        """
        Update an existing entity.
        
        Args:
            id: The unique identifier of the entity to update
            data: The updated data
            
        Returns:
            Result containing the updated entity, or an error
        """
        ...
    
    async def delete(self, id: ID) -> Result[None, Any]:
        """
        Delete an entity.
        
        Args:
            id: The unique identifier of the entity to delete
            
        Returns:
            Result indicating success or failure
        """
        ...


@runtime_checkable
class CrudServiceProtocol(ServiceProtocol[T, ID], Protocol[T, ID, DTO]):
    """
    Extended service protocol with CRUD operations using DTOs.
    
    This protocol adds methods for working with Data Transfer Objects
    for input/output operations, providing a more structured approach
    to data handling in services.
    
    Type parameters:
        T: The entity/domain object type this service manages
        ID: The type of the entity's identifier
        DTO: The Data Transfer Object type for input/output
    """
    
    async def create_from_dto(self, dto: DTO) -> Result[T, Any]:
        """
        Create a new entity from a DTO.
        
        Args:
            dto: The DTO containing data for the new entity
            
        Returns:
            Result containing the created entity, or an error
        """
        ...
    
    async def update_from_dto(self, id: ID, dto: DTO) -> Result[T, Any]:
        """
        Update an existing entity using a DTO.
        
        Args:
            id: The unique identifier of the entity to update
            dto: The DTO containing updated data
            
        Returns:
            Result containing the updated entity, or an error
        """
        ...
    
    async def to_dto(self, entity: T) -> Result[DTO, Any]:
        """
        Convert an entity to a DTO.
        
        Args:
            entity: The entity to convert
            
        Returns:
            The DTO representation of the entity
        """
        ...
    
    async def to_entity(self, dto: DTO) -> Result[T, Any]:
        """
        Convert a DTO to an entity.
        
        Args:
            dto: The DTO to convert
            
        Returns:
            The entity representation of the DTO
        """
        ...


@runtime_checkable
class QueryServiceProtocol(Protocol[T]):
    """
    Protocol for query-focused services.
    
    This protocol defines methods for complex queries and read operations,
    following the CQRS pattern where query operations are separated from
    command operations.
    
    Type parameters:
        T: The entity/domain object type this service queries
    """
    
    async def query(self, query_params: dict[str, Any]) -> Result[list[T], Any]:
        """
        Execute a query with the given parameters.
        
        Args:
            query_params: The query parameters
            
        Returns:
            Result containing the query results, or an error
        """
        ...
    
    async def query_single(self, query_params: dict[str, Any]) -> Result[T | None, Any]:
        """
        Execute a query expecting a single result.
        
        Args:
            query_params: The query parameters
            
        Returns:
            Result containing the single result if found, or an error
        """
        ...
    
    async def count(self, query_params: dict[str, Any]) -> Result[int, Any]:
        """
        Count the results of a query.
        
        Args:
            query_params: The query parameters
            
        Returns:
            Result containing the count, or an error
        """
        ...