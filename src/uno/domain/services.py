"""
Domain services for the Uno framework.

This module contains the base classes for domain services, which encapsulate
domain operations that don't naturally belong to a single entity or value object.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast
from abc import ABC, abstractmethod

from uno.core.result import Result, Success, Failure
from uno.core.uow import UnitOfWork
from uno.core.events import EventBus
from uno.domain.exceptions import DomainError


InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')
RepoT = TypeVar('RepoT')
UowT = TypeVar('UowT', bound=UnitOfWork)


class DomainService(ABC, Generic[InputT, OutputT, UowT]):
    """
    Base class for domain services.
    
    Domain services encapsulate operations that don't naturally belong to
    entities or value objects. They are typically stateless and operate on
    multiple domain objects.
    
    Type Parameters:
        InputT: Type of input data
        OutputT: Type of output data
        UowT: Type of unit of work
    """
    
    def __init__(self, uow: UowT, event_bus: Optional[EventBus] = None):
        """
        Initialize domain service.
        
        Args:
            uow: Unit of work for transaction management
            event_bus: Optional event bus for publishing domain events
        """
        self.uow = uow
        self.event_bus = event_bus
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the domain service operation within a transaction.
        
        This method provides transactional boundaries and error handling
        for the domain operation.
        
        Args:
            input_data: Input data for the operation
            
        Returns:
            Result with operation output or failure details
        """
        try:
            # Start transaction
            async with self.uow:
                # Execute the domain operation
                result = await self._execute_internal(input_data)
                
                # If successful, commit transaction
                if result.is_success:
                    await self.uow.commit()
                else:
                    # If failed, rollback is automatic via context exit
                    pass
                
                return result
                
        except DomainError as e:
            # Domain errors are returned as failures
            return Failure(e)
        except Exception as e:
            # Unexpected errors are wrapped and returned as failures
            return Failure(e)
    
    @abstractmethod
    async def _execute_internal(self, input_data: InputT) -> Result[OutputT]:
        """
        Internal implementation of the domain service operation.
        
        This method should be implemented by derived classes to provide
        the specific domain operation logic.
        
        Args:
            input_data: Input data for the operation
            
        Returns:
            Result with operation output or failure details
        """
        pass


class ReadOnlyDomainService(ABC, Generic[InputT, OutputT, UowT]):
    """
    Base class for read-only domain services.
    
    Read-only domain services perform operations that don't modify domain state,
    such as complex queries or calculations. They don't require transaction
    management but still operate within the domain model.
    
    Type Parameters:
        InputT: Type of input data
        OutputT: Type of output data
        UowT: Type of unit of work
    """
    
    def __init__(self, uow: UowT):
        """
        Initialize read-only domain service.
        
        Args:
            uow: Unit of work for accessing repositories
        """
        self.uow = uow
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the read-only domain service operation.
        
        Args:
            input_data: Input data for the operation
            
        Returns:
            Result with operation output or failure details
        """
        try:
            return await self._execute_internal(input_data)
        except DomainError as e:
            return Failure(e)
        except Exception as e:
            return Failure(e)
    
    @abstractmethod
    async def _execute_internal(self, input_data: InputT) -> Result[OutputT]:
        """
        Internal implementation of the read-only domain service operation.
        
        This method should be implemented by derived classes to provide
        the specific domain operation logic.
        
        Args:
            input_data: Input data for the operation
            
        Returns:
            Result with operation output or failure details
        """
        pass


class DomainServiceFactory:
    """
    Factory for creating domain services.
    
    This factory creates and configures domain services with appropriate
    dependencies, such as unit of work and event bus.
    """
    
    def __init__(self, uow_factory: Any, event_bus: Optional[EventBus] = None):
        """
        Initialize domain service factory.
        
        Args:
            uow_factory: Factory for creating units of work
            event_bus: Optional event bus for publishing domain events
        """
        self.uow_factory = uow_factory
        self.event_bus = event_bus
    
    def create_service(self, service_class: Type[Any], **kwargs: Any) -> Any:
        """
        Create a domain service instance.
        
        Args:
            service_class: Domain service class to instantiate
            **kwargs: Additional constructor arguments
            
        Returns:
            Domain service instance
        """
        uow = self.uow_factory.create_uow()
        
        # Determine if service requires event bus
        if issubclass(service_class, DomainService) and self.event_bus is not None:
            service = service_class(uow=uow, event_bus=self.event_bus, **kwargs)
        else:
            service = service_class(uow=uow, **kwargs)
            
        return service