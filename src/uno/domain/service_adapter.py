"""
Service adapters for migrating from legacy services to the unified pattern.

This module provides adapter classes that allow legacy services to be used
with the standardized service pattern and vice versa, enabling a smooth
migration path for modules using older service implementations.
"""

import logging
from typing import TypeVar, Generic, Dict, List, Optional, Any, Type, Union, cast

from uno.core.errors.result import Result, Success, Failure
from uno.domain.unified_services import (
    DomainService, ReadOnlyDomainService, EntityService, 
    DomainServiceProtocol
)

# Type variables
EntityT = TypeVar('EntityT')
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')


class LegacyServiceAdapter(DomainServiceProtocol[InputT, OutputT]):
    """
    Adapter for using legacy services with the standardized service interface.
    
    This adapter wraps a legacy service implementation and exposes it through the
    standardized DomainServiceProtocol interface, allowing code that expects the 
    standardized interface to work with legacy services.
    """
    
    def __init__(
        self, 
        legacy_service: Any,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the legacy service adapter.
        
        Args:
            legacy_service: The legacy service to adapt
            logger: Optional logger for diagnostic output
        """
        self.legacy_service = legacy_service
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the service operation.
        
        Args:
            input_data: Input data for the operation
            
        Returns:
            Result containing the operation result or error
        """
        try:
            # Check if the legacy service has an execute method
            if hasattr(self.legacy_service, "execute") and callable(self.legacy_service.execute):
                result = await self.legacy_service.execute(input_data)
                
                # Handle different result patterns
                if isinstance(result, Result):
                    return result
                elif isinstance(result, tuple) and len(result) == 2:
                    # Some legacy services return (success, value) tuples
                    success, value = result
                    if success:
                        return Success(value)
                    else:
                        return Failure(str(value))
                else:
                    # Assume success if we got a result
                    return Success(cast(OutputT, result))
            
            # If there's no execute method, try to find an appropriate method based on input type
            method_name = self._infer_method_name(input_data)
            if method_name and hasattr(self.legacy_service, method_name):
                method = getattr(self.legacy_service, method_name)
                result = await method(input_data)
                return Success(cast(OutputT, result))
            
            self.logger.error(f"Could not find appropriate method in legacy service")
            return Failure("Could not find appropriate method in legacy service")
            
        except Exception as e:
            self.logger.error(f"Error executing legacy service: {str(e)}")
            return Failure(str(e))
    
    def _infer_method_name(self, input_data: Any) -> Optional[str]:
        """
        Infer an appropriate method name based on input data.
        
        Args:
            input_data: The input data
            
        Returns:
            A method name if one can be inferred, None otherwise
        """
        # Try to infer based on input class name
        if hasattr(input_data, "__class__") and hasattr(input_data.__class__, "__name__"):
            class_name = input_data.__class__.__name__
            
            # Check for common patterns
            if class_name.endswith("Command"):
                base_name = class_name[:-7].lower()
                return f"handle_{base_name}_command"
            elif class_name.endswith("Query"):
                base_name = class_name[:-5].lower()
                return f"handle_{base_name}_query"
            elif class_name.endswith("Input"):
                base_name = class_name[:-5].lower()
                return f"process_{base_name}"
        
        return None


class StandardServiceAdapter:
    """
    Adapter for using standardized services with legacy code.
    
    This adapter wraps a standardized Domain Service implementation and exposes it through
    an interface compatible with legacy service patterns, allowing legacy code to
    work with standardized services.
    """
    
    def __init__(
        self, 
        standard_service: DomainServiceProtocol[InputT, OutputT],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the standard service adapter.
        
        Args:
            standard_service: The standardized service to adapt
            logger: Optional logger for diagnostic output
        """
        self.standard_service = standard_service
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute(self, *args, **kwargs):
        """
        Execute the service operation.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            The operation result
            
        Raises:
            Exception: If the operation fails
        """
        # Convert arguments to appropriate input format
        input_data = self._convert_args_to_input(*args, **kwargs)
        
        # Execute the standardized service
        result = await self.standard_service.execute(input_data)
        
        # Convert result to legacy format
        if result.is_success:
            return result.value
        else:
            raise Exception(str(result.error))
    
    def _convert_args_to_input(self, *args, **kwargs) -> Any:
        """
        Convert arguments to a format the standardized service can process.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Input data in a format the service can process
        """
        # If there's one positional arg and no kwargs, assume it's already
        # in the right format
        if len(args) == 1 and not kwargs:
            return args[0]
        
        # If there are kwargs, use those as a dict
        if kwargs:
            return kwargs
        
        # If there are multiple args, convert to a dict with positional names
        if len(args) > 1:
            return {f"arg{i}": arg for i, arg in enumerate(args)}
        
        # Fallback - empty dict
        return {}


# Registry of service implementations by module
_service_registry: Dict[str, Dict[str, Type[DomainServiceProtocol]]] = {}


def register_service_implementation(
    module_name: str, 
    service_name: str, 
    service_class: Type[DomainServiceProtocol]
) -> None:
    """
    Register a service implementation for a module.
    
    This function allows modules to register their service implementations
    for use by the central service factory.
    
    Args:
        module_name: The name of the module (e.g., 'attributes', 'values')
        service_name: The name of the service within the module
        service_class: The service class to register
    """
    if module_name not in _service_registry:
        _service_registry[module_name] = {}
    
    _service_registry[module_name][service_name] = service_class


def get_service_implementation(
    module_name: str, 
    service_name: str
) -> Optional[Type[DomainServiceProtocol]]:
    """
    Get the registered service implementation for a module service.
    
    Args:
        module_name: The name of the module
        service_name: The name of the service within the module
        
    Returns:
        The service class if registered, None otherwise
    """
    if module_name in _service_registry:
        return _service_registry[module_name].get(service_name)
    return None


# Example registration for module services
# This would typically be done in each module's __init__.py
"""
from uno.domain.service_adapter import register_service_implementation
from my_module.services import MyDomainService

register_service_implementation('my_module', 'my_domain_service', MyDomainService)
"""