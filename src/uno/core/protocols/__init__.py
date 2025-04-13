# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Protocol definitions for the Uno framework.

This module contains protocol definitions for components used throughout the framework.
Protocols provide interface definitions that help break circular dependencies
and improve code organization.
"""

from typing import Any, Dict, List, Optional, Protocol, Set, Type, TypeVar, Union, runtime_checkable, Tuple, Generic
from types import TracebackType
import asyncio
from pydantic import BaseModel

# Type variables
ModelT = TypeVar("ModelT", bound=BaseModel)
T = TypeVar("T", covariant=True)
Self = TypeVar("Self")

# Import other protocol types
from uno.core.protocols.filter_protocols import UnoFilterProtocol


@runtime_checkable
class DatabaseSessionProtocol(Protocol):
    """Protocol for database session objects."""
    
    async def execute(self, query: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a query.
        
        Args:
            query: The query to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Query result
        """
        ...
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...
    
    async def rollback(self) -> None:
        """Roll back the current transaction."""
        ...
    
    async def close(self) -> None:
        """Close the session."""
        ...
    
    async def fetchone(self) -> Optional[Dict[str, Any]]:
        """
        Fetch one result row.
        
        Returns:
            A row as a dictionary, or None if no rows available
        """
        ...
    
    async def fetchall(self) -> List[Dict[str, Any]]:
        """
        Fetch all result rows.
        
        Returns:
            A list of rows as dictionaries
        """
        ...


@runtime_checkable
class DatabaseSessionContextProtocol(Protocol):
    """Protocol for database session context objects."""
    
    async def __aenter__(self) -> DatabaseSessionProtocol:
        """
        Enter the context.
        
        Returns:
            The session object
        """
        ...
    
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        """
        Exit the context.
        
        Args:
            exc_type: Exception type, if an exception was raised
            exc_val: Exception value, if an exception was raised
            exc_tb: Exception traceback, if an exception was raised
            
        Returns:
            True if the exception was handled, False otherwise
        """
        ...

@runtime_checkable
class DatabaseSessionFactoryProtocol(Protocol):
    """Protocol for database session factory objects."""
    
    def __call__(self, **kwargs: Any) -> DatabaseSessionContextProtocol:
        """
        Create a session context.
        
        Args:
            **kwargs: Additional options for the session
            
        Returns:
            A session context object
        """
        ...


T_Model = TypeVar("T_Model")
T_Key = TypeVar("T_Key")
T_Schema = TypeVar("T_Schema")
T_Result = TypeVar("T_Result")
T_Extra = TypeVar("T_Extra")

@runtime_checkable
class DatabaseRepository(Protocol, Generic[T_Model, T_Key, T_Schema, T_Result, T_Extra]):
    """Protocol for database repositories."""
    
    async def get(self, **kwargs: Any) -> T_Model:
        """
        Get an entity by parameters.
        
        Args:
            **kwargs: Filter parameters
            
        Returns:
            The entity if found
            
        Raises:
            NotFoundException: If no entity is found
        """
        ...
    
    async def filter(self, filters: Optional[Any] = None) -> List[T_Model]:
        """
        Filter entities by parameters.
        
        Args:
            filters: Filter parameters
            
        Returns:
            A list of matching entities
        """
        ...
    
    async def create(self, schema: T_Schema) -> List[T_Model]:
        """
        Create a new entity.
        
        Args:
            schema: The schema containing entity data
            
        Returns:
            A list containing the created entity
        """
        ...
    
    async def update(self, to_db_model: T_Model) -> T_Model:
        """
        Update an entity.
        
        Args:
            to_db_model: The model to update
            
        Returns:
            The updated model
        """
        ...
    
    async def delete(self, model: T_Model) -> None:
        """
        Delete an entity.
        
        Args:
            model: The model to delete
        """
        ...
    
    async def merge(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Merge entity data.
        
        Args:
            data: The data to merge
            
        Returns:
            A list containing the merged entity data and action
        """
        ...


@runtime_checkable
class FilterManagerProtocol(Protocol):
    """Protocol for filter managers."""
    
    def create_filters_from_table(
        self,
        model_class: Type[BaseModel],
        exclude_from_filters: bool = False,
        exclude_fields: Optional[List[str]] = None,
    ) -> Dict[str, UnoFilterProtocol]:
        """
        Create filters from a model's table.
        
        Args:
            model_class: The model class to create filters from
            exclude_from_filters: Whether to exclude this model from filters
            exclude_fields: List of field names to exclude from filtering
            
        Returns:
            A dictionary of filter names to filter objects
        """
        ...
    
    def create_filter_params(
        self,
        model_class: Type[BaseModel],
    ) -> Type[BaseModel]:
        """
        Create a filter parameters model for a model class.
        
        Args:
            model_class: The model class to create filter parameters for
            
        Returns:
            A Pydantic model class for filter parameters
        """
        ...
        
    def validate_filter_params(
        self,
        filter_params: BaseModel,
        model_class: Type[BaseModel],
    ) -> List[Any]:
        """
        Validate filter parameters.
        
        Args:
            filter_params: The filter parameters to validate
            model_class: The model class to validate against
            
        Returns:
            A list of validated filter tuples
        """
        ...


@runtime_checkable
class SchemaManagerProtocol(Protocol):
    """Protocol for schema managers."""
    
    def get_schema(self, schema_type: str) -> Type[BaseModel]:
        """
        Get a schema by type.
        
        Args:
            schema_type: The type of schema to get
            
        Returns:
            The schema class
        """
        ...


@runtime_checkable
class DBClientProtocol(Protocol):
    """Protocol for database clients."""
    
    async def query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results.
        
        Args:
            query: The query to execute
            params: Optional query parameters
            
        Returns:
            A list of dictionaries representing the query results
        """
        ...