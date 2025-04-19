"""
Base service protocols and classes for the Uno framework.

DEPRECATED: This module has been deprecated and replaced by the new domain entity framework
in uno.domain.entity.service. Please use the new implementation instead.

This module now serves as a redirection layer to the new implementation.
"""

import warnings
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast, Protocol, runtime_checkable

# Import from the new implementation to re-export
from uno.domain.entity.service import (
    DomainService, DomainServiceWithUnitOfWork, 
    ApplicationService, CrudService, ServiceFactory
)
from uno.core.errors.result import Result, Success, Failure
from uno.core.base.error import BaseError

# Emit a strong deprecation warning
warnings.warn(
    "IMPORTANT: The uno.core.base.service module is deprecated and will be removed in a future release. "
    "Use uno.domain.entity.service instead for all service implementations.",
    DeprecationWarning,
    stacklevel=2
)

# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type
InputT = TypeVar("InputT")  # Input type
OutputT = TypeVar("OutputT")  # Output type
ParamsT = TypeVar("ParamsT")  # Parameters type


# Re-export protocols for backward compatibility
@runtime_checkable
class ServiceProtocol(Protocol[InputT, OutputT]):
    """
    Protocol defining the standard service interface.
    
    DEPRECATED: Use ApplicationService from uno.domain.entity.service instead.
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
    Protocol defining the standard CRUD service interface.
    
    DEPRECATED: Use CrudService from uno.domain.entity.service instead.
    """
    
    async def get(self, id: ID) -> Result[T]:
        """Get an entity by ID."""
        ...
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Result[List[T]]:
        """List entities matching filter criteria."""
        ...
    
    async def create(self, entity: T) -> Result[T]:
        """Create a new entity."""
        ...
    
    async def update(self, entity: T) -> Result[T]:
        """Update an existing entity."""
        ...
    
    async def delete(self, id: ID) -> Result[bool]:
        """Delete an entity by ID."""
        ...


@runtime_checkable
class QueryServiceProtocol(Protocol[InputT, OutputT]):
    """
    Protocol defining the standard query service interface.
    
    DEPRECATED: Use ApplicationService from uno.domain.entity.service instead.
    """
    
    async def query(self, params: InputT) -> Result[OutputT]:
        """
        Execute a query with the given parameters.
        
        Args:
            params: The query parameters
            
        Returns:
            A Result containing either the query result or error information
        """
        ...


# Backward compatibility classes
class BaseService(Generic[InputT, OutputT], ApplicationService[InputT, OutputT]):
    """
    Base class for all services.
    
    DEPRECATED: Use ApplicationService from uno.domain.entity.service instead.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "BaseService is deprecated. "
            "Use uno.domain.entity.service.ApplicationService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the service operation.
        
        Args:
            input_data: The input data for the operation
            
        Returns:
            A Result containing either the operation result or error information
        """
        raise NotImplementedError(
            "This method is deprecated. Use the appropriate method in the "
            "new domain entity service classes from uno.domain.entity.service."
        )


class BaseQueryService(Generic[InputT, OutputT], ApplicationService[InputT, OutputT]):
    """
    Base class for query services.
    
    DEPRECATED: Use ApplicationService from uno.domain.entity.service instead.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with a deprecation warning."""
        warnings.warn(
            "BaseQueryService is deprecated. "
            "Use uno.domain.entity.service.ApplicationService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)
    
    async def query(self, params: InputT) -> Result[OutputT]:
        """
        Execute a query with the given parameters.
        
        Args:
            params: The query parameters
            
        Returns:
            A Result containing either the query result or error information
        """
        raise NotImplementedError(
            "This method is deprecated. Use the appropriate method in the "
            "new domain entity service classes from uno.domain.entity.service."
        )