"""
Domain service base classes.

This module provides base classes for domain services, which encapsulate domain
business logic that doesn't fit naturally in entities.
"""

from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Dict, Any

from uno.core.errors.result import Result, Success, Failure

# Type variables
T = TypeVar('T')  # Result type
InputT = TypeVar('InputT')  # Input type


@dataclass
class DomainServiceContext:
    """
    Context for domain services.
    
    This class provides the execution context for domain services,
    including user information, tenant context, etc.
    """
    
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = None


class DomainService(Generic[InputT, T]):
    """
    Base class for domain services.
    
    Domain services implement business logic that doesn't naturally
    fit within entities, particularly logic that operates on multiple
    entities or aggregates.
    """
    
    async def execute(self, input_data: InputT, context: Optional[DomainServiceContext] = None) -> Result[T]:
        """
        Execute the domain service.
        
        Args:
            input_data: Input data for the service
            context: Optional context information
            
        Returns:
            Result containing the execution result or error
        """
        try:
            # Use default context if not provided
            ctx = context or DomainServiceContext()
            
            # Execute the service logic
            return await self._execute_internal(input_data, ctx)
        except Exception as e:
            # Log any exceptions
            self._log_error(e)
            
            # Return failure result
            return Failure(str(e))
    
    async def _execute_internal(self, input_data: InputT, context: DomainServiceContext) -> Result[T]:
        """
        Internal implementation of the domain service.
        
        Override this method in derived classes to implement
        the domain logic.
        
        Args:
            input_data: Input data for the service
            context: Context information
            
        Returns:
            Result containing the execution result or error
        """
        raise NotImplementedError("Domain services must implement _execute_internal")
    
    def _log_error(self, error: Exception) -> None:
        """
        Log an error during service execution.
        
        Args:
            error: The exception that occurred
        """
        # This default implementation just prints the error
        # Derived classes should implement proper logging
        print(f"Error in {self.__class__.__name__}: {str(error)}")