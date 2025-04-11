# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Protocol definitions for the Uno framework.

This module provides structured interfaces (protocols) that define the shapes of
the objects used in the Uno framework, enhancing type safety and interoperability.
"""

from typing import Any, Dict, List, Optional, Protocol, TypeVar, Set, Type, runtime_checkable, Union
from types import TracebackType

import asyncio
from contextlib import AsyncExitStack
from pydantic import BaseModel

# Type variables for generic protocols
T = TypeVar("T", covariant=True)
ModelT = TypeVar("ModelT", bound=BaseModel)
Self = TypeVar("Self")


@runtime_checkable
class ConnectionProtocol(Protocol):
    """Protocol for database connection objects."""
    
    async def execute(self, query: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a query.
        
        Args:
            query: The query to execute
            *args: Positional arguments for the query
            **kwargs: Keyword arguments for the query
            
        Returns:
            The query result
        """
        ...
    
    async def fetchall(self) -> List[Dict[str, Any]]:
        """
        Fetch all rows from a query result.
        
        Returns:
            A list of dictionaries representing the rows
        """
        ...
    
    async def fetchone(self) -> Optional[Dict[str, Any]]:
        """
        Fetch a single row from a query result.
        
        Returns:
            A dictionary representing the row, or None if no row is available
        """
        ...
    
    async def commit(self) -> None:
        """
        Commit the current transaction.
        """
        ...
    
    async def rollback(self) -> None:
        """
        Roll back the current transaction.
        """
        ...
    
    async def close(self) -> None:
        """
        Close the connection.
        """
        ...
    
    async def __aenter__(self) -> "ConnectionProtocol":
        """
        Enter the connection context.
        
        Returns:
            The connection object
        """
        ...
    
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        """
        Exit the connection context.
        
        Args:
            exc_type: The exception type, if an exception was raised
            exc_val: The exception instance, if an exception was raised
            exc_tb: The traceback, if an exception was raised
            
        Returns:
            True if the exception was handled, False otherwise
        """
        ...


@runtime_checkable
class EngineProtocol(Protocol):
    """Protocol for database engine objects."""
    
    async def connect(self) -> ConnectionProtocol:
        """
        Connect to the database.
        
        Returns:
            A connection object
        """
        ...
    
    async def close(self) -> None:
        """
        Close all connections in the engine's pool.
        """
        ...
    
    @property
    def dialect(self) -> str:
        """
        Get the database dialect name.
        
        Returns:
            The dialect name (e.g., "postgresql")
        """
        ...


@runtime_checkable
class DBClientProtocol(Protocol):
    """Protocol for database client objects."""
    
    async def execute(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a query.
        
        Args:
            query: The query to execute
            parameters: Parameters for the query
            
        Returns:
            The query result
        """
        ...
    
    async def execute_many(self, query: str, parameters_list: List[Dict[str, Any]]) -> List[Any]:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: The query to execute
            parameters_list: A list of parameter dictionaries
            
        Returns:
            A list of query results
        """
        ...
    
    async def fetch_all(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and fetch all results.
        
        Args:
            query: The query to execute
            parameters: Parameters for the query
            
        Returns:
            A list of dictionaries representing the rows
        """
        ...
    
    async def fetch_one(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Execute a query and fetch a single result.
        
        Args:
            query: The query to execute
            parameters: Parameters for the query
            
        Returns:
            A dictionary representing the row, or None if no row is available
        """
        ...
    
    async def transaction(self) -> AsyncExitStack:
        """
        Start a transaction.
        
        Returns:
            An AsyncExitStack context manager for the transaction
        """
        ...


@runtime_checkable
class SchemaValidatorProtocol(Protocol):
    """Protocol for schema validators."""
    
    def validate(self, data: Any, schema_name: str) -> Dict[str, Any]:
        """
        Validate data against a schema.
        
        Args:
            data: The data to validate
            schema_name: The name of the schema to validate against
            
        Returns:
            The validated data
            
        Raises:
            ValidationError: If validation fails
        """
        ...
    
    def validate_list(self, data_list: List[Any], schema_name: str) -> List[Dict[str, Any]]:
        """
        Validate a list of data items against a schema.
        
        Args:
            data_list: The list of data items to validate
            schema_name: The name of the schema to validate against
            
        Returns:
            The validated data items
            
        Raises:
            ValidationError: If validation fails for any item
        """
        ...


@runtime_checkable
class SchemaManagerProtocol(Protocol):
    """Protocol for schema managers."""
    
    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """
        Get a schema by name.
        
        Args:
            schema_name: The name of the schema to get
            
        Returns:
            The schema if found, None otherwise
        """
        ...
    
    def get_list_schema(self, model: Type[Any]) -> Type[BaseModel]:
        """
        Get or create a schema for lists of the given model.
        
        Args:
            model: The model to create a list schema for
            
        Returns:
            A schema class for lists of the given model
        """
        ...
    
    def create_schema(self, schema_name: str, model: Type[BaseModel]) -> Type[BaseModel]:
        """
        Create a schema for a model.
        
        Args:
            schema_name: The name of the schema to create
            model: The model to create a schema for
            
        Returns:
            The created schema class
        """
        ...
    
    def create_all_schemas(self, model: Type[BaseModel]) -> Dict[str, Type[BaseModel]]:
        """
        Create all schemas for a model.
        
        Args:
            model: The model to create schemas for
            
        Returns:
            A dictionary of schema names to schema classes
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
    ) -> Dict[str, Any]:
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