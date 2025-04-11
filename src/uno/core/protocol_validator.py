"""
Protocol validation utilities for the Uno framework.

This module provides utilities for validating that concrete implementations 
correctly fulfill protocol interfaces, helping to catch implementation errors 
early in development.
"""

import functools
import inspect
import typing
from types import ModuleType
from typing import (
    Any, Callable, Dict, List, Optional, Protocol, Set, Type, TypeVar, Union, Tuple,
    get_type_hints, runtime_checkable, cast
)

T = TypeVar('T')
P = TypeVar('P')


class ProtocolValidationError(Exception):
    """Exception raised when a concrete class fails to implement a protocol correctly."""
    
    def __init__(
        self, 
        cls: Type[Any], 
        protocol: Any,  # We use Any instead of Type[Protocol] to avoid typing issues
        missing_attributes: List[str],
        type_mismatches: Dict[str, Tuple[str, str]]
    ):
        self.cls = cls
        self.protocol = protocol
        self.missing_attributes = missing_attributes
        self.type_mismatches = type_mismatches
        
        message_parts = [f"Class '{cls.__name__}' does not properly implement protocol '{protocol.__name__}'"]
        
        if missing_attributes:
            attributes_str = ", ".join(f"'{attr}'" for attr in missing_attributes)
            message_parts.append(f"Missing attributes: {attributes_str}")
        
        if type_mismatches:
            mismatch_str = ", ".join(
                f"'{attr}' (expected: {expected_found[0]}, found: {expected_found[1]})" 
                for attr, expected_found in type_mismatches.items()
            )
            message_parts.append(f"Type mismatches: {mismatch_str}")
        
        super().__init__(". ".join(message_parts))


def validate_protocol(cls: Type[Any], protocol: Any) -> None:
    """
    Validate that a class correctly implements a protocol.
    
    Args:
        cls: The class to validate.
        protocol: The protocol to validate against.
        
    Raises:
        ProtocolValidationError: If the class doesn't properly implement the protocol.
        TypeError: If the protocol parameter is not a Protocol type.
    """
    if not hasattr(protocol, '_is_protocol') or not protocol._is_protocol:
        raise TypeError(f"The provided type '{protocol.__name__}' is not a Protocol.")
    
    # Get all protocol attributes (methods, properties, etc.)
    protocol_attrs = _get_protocol_attributes(protocol)
    
    # Track validation issues
    missing_attributes = []
    type_mismatches = {}
    
    # Get type hints for protocol and class
    protocol_type_hints = get_type_hints(protocol)
    try:
        cls_type_hints = get_type_hints(cls)
    except (NameError, TypeError):
        # Handle forward references or other type hint issues
        cls_type_hints = {}
    
    # Check each protocol attribute
    for attr_name in protocol_attrs:
        # Skip dunder methods that are likely to be implemented by the Python runtime
        if attr_name.startswith('__') and attr_name.endswith('__'):
            if attr_name not in ('__aenter__', '__aexit__', '__enter__', '__exit__'):
                continue
        
        # Check if attribute exists in the class
        # For dataclasses, check if it's a field in __annotations__
        if attr_name in getattr(cls, '__annotations__', {}):
            # Attribute exists as a dataclass field
            pass
        elif not hasattr(cls, attr_name):
            missing_attributes.append(attr_name)
            continue
        
        # Verify attribute type if available
        if attr_name in protocol_type_hints and attr_name in cls_type_hints:
            protocol_type = protocol_type_hints[attr_name]
            cls_type = cls_type_hints[attr_name]
            
            # Check if types are compatible
            if not _are_types_compatible(cls_type, protocol_type):
                type_mismatches[attr_name] = (
                    _type_to_str(protocol_type),
                    _type_to_str(cls_type)
                )
    
    # Raise an error if any issues were found
    if missing_attributes or type_mismatches:
        raise ProtocolValidationError(cls, protocol, missing_attributes, type_mismatches)


def validate_implementation(instance: Any, protocol: Any) -> None:
    """
    Validate that an instance correctly implements a protocol.
    
    Args:
        instance: The instance to validate.
        protocol: The protocol to validate against.
        
    Raises:
        ProtocolValidationError: If the instance doesn't properly implement the protocol.
        TypeError: If the protocol parameter is not a Protocol type.
    """
    validate_protocol(type(instance), protocol)


def find_protocol_implementations(
    module_or_package: Union[ModuleType, str], 
    protocol: Any
) -> List[Type[Any]]:
    """
    Find all classes in a module or package that implement a specific protocol.
    
    Args:
        module_or_package: Module, package, or string name to search in.
        protocol: The protocol to look for implementations of.
        
    Returns:
        A list of classes that implement the protocol.
    """
    if isinstance(module_or_package, str):
        import importlib
        module_or_package = importlib.import_module(module_or_package)
    
    implementations = []
    
    # Process the module itself
    for name, obj in inspect.getmembers(module_or_package):
        if (inspect.isclass(obj) and 
            obj.__module__ == module_or_package.__name__ and
            not inspect.isabstract(obj)):
            try:
                # Use isinstance for runtime protocols
                if hasattr(protocol, '_is_runtime_protocol') and protocol._is_runtime_protocol:
                    if isinstance(obj(), protocol):
                        implementations.append(obj)
                # Use static validation for non-runtime protocols
                else:
                    try:
                        validate_protocol(obj, protocol)
                        implementations.append(obj)
                    except ProtocolValidationError:
                        pass
            except (TypeError, Exception):
                # Skip classes that can't be instantiated without arguments
                # or have other issues
                continue
    
    # Process sub-modules if it's a package
    if hasattr(module_or_package, '__path__'):
        import pkgutil
        for _, submodule_name, is_pkg in pkgutil.iter_modules(module_or_package.__path__):
            full_name = f"{module_or_package.__name__}.{submodule_name}"
            try:
                import importlib
                submodule = importlib.import_module(full_name)
                implementations.extend(find_protocol_implementations(submodule, protocol))
            except ImportError:
                # Skip modules that can't be imported
                continue
    
    return implementations


def _get_protocol_attributes(protocol: Any) -> Set[str]:
    """
    Extract all attributes defined in a protocol, including those from parent protocols.
    
    Args:
        protocol: The protocol to extract attributes from.
        
    Returns:
        A set of attribute names.
    """
    # Start with the protocol's own __annotations__
    attrs = set(getattr(protocol, '__annotations__', {}))
    
    # Add methods and properties defined in the protocol
    for attr_name, attr in inspect.getmembers(protocol):
        # Skip private attributes, special methods, and framework-related attributes
        if (attr_name not in attrs and 
            not attr_name.startswith('_abc_') and 
            not attr_name.startswith('_is_') and
            not attr_name.startswith('__pytest_') and
            not attr_name.startswith('_pytest_') and
            attr_name not in ('__module__', '__qualname__', '__parameters__')):
            
            # Only include if it's an actual protocol element (method, property)
            # and not something inherited from object or added by frameworks
            if inspect.isfunction(attr) or inspect.ismethod(attr) or isinstance(attr, property):
                attrs.add(attr_name)
    
    # Add attributes from parent protocols
    for base in protocol.__bases__:
        if hasattr(base, '_is_protocol') and base._is_protocol:
            attrs.update(_get_protocol_attributes(base))
    
    return attrs


def _are_types_compatible(concrete_type: Any, protocol_type: Any) -> bool:
    """
    Check if a concrete type is compatible with a protocol type.
    
    Args:
        concrete_type: The type from the concrete implementation.
        protocol_type: The type from the protocol.
        
    Returns:
        True if the types are compatible, False otherwise.
    """
    # Handle basic types
    if concrete_type == protocol_type:
        return True
    
    # Handle Optional types
    if getattr(protocol_type, '__origin__', None) is Union:
        # Optional[X] is represented as Union[X, None]
        if type(None) in protocol_type.__args__:
            # If protocol accepts None, concrete can be anything
            if type(None) in getattr(concrete_type, '__args__', ()):
                # If both types are Optional, compare the non-None types
                protocol_inner = next((t for t in protocol_type.__args__ if t is not type(None)), Any)
                concrete_inner = next((t for t in concrete_type.__args__ if t is not type(None)), Any)
                return _are_types_compatible(concrete_inner, protocol_inner)
    
    # Handle generic types like List, Dict, etc.
    if (hasattr(protocol_type, '__origin__') and 
        hasattr(concrete_type, '__origin__') and
        protocol_type.__origin__ == concrete_type.__origin__):
        # Compare type arguments recursively
        for p_arg, c_arg in zip(protocol_type.__args__, concrete_type.__args__):
            if not _are_types_compatible(c_arg, p_arg):
                return False
        return True
    
    # Handle protocol subtyping
    if (hasattr(protocol_type, '_is_protocol') and protocol_type._is_protocol and
        inspect.isclass(concrete_type)):
        try:
            validate_protocol(concrete_type, protocol_type)
            return True
        except ProtocolValidationError:
            return False
    
    # Handle callable types
    if protocol_type is Callable or (
        hasattr(protocol_type, '__origin__') and protocol_type.__origin__ is Callable
    ):
        if concrete_type is Callable or (
            hasattr(concrete_type, '__origin__') and concrete_type.__origin__ is Callable
        ):
            # Special case for comparing Callable types
            # This is a simplified check; a more complete one would compare argument types
            # and return types
            return True
    
    # Default to allowing Any in protocol
    if protocol_type is Any:
        return True
    
    # For other types, assume they're not compatible
    return False


def implements(*protocols: Any) -> Callable[[Type[T]], Type[T]]:
    """
    A decorator to mark a class as an implementation of one or more protocols.
    
    This decorator validates that the class correctly implements all specified
    protocols at class definition time.
    
    Args:
        *protocols: One or more Protocol types that the class should implement.
        
    Returns:
        A decorator function that validates and returns the decorated class.
        
    Example:
        @implements(Repository[User, UUID])
        class UserRepository:
            async def get(self, id: UUID) -> Optional[User]:
                ...
    """
    def decorator(cls: Type[T]) -> Type[T]:
        for protocol in protocols:
            validate_protocol(cls, protocol)
        
        # Add a marker to the class for introspection
        # Use hasattr with getattr to make mypy happy
        if not hasattr(cls, '__implemented_protocols__'):
            # We annotate the class with a dynamically created attribute, need to ignore mypy here
            setattr(cls, '__implemented_protocols__', [])  # type: ignore
        
        for protocol in protocols:
            protocols_list = getattr(cls, '__implemented_protocols__')  # type: ignore
            if protocol not in protocols_list:
                protocols_list.append(protocol)
        
        return cls
    
    return decorator


def verify_all_implementations(modules: List[Union[str, ModuleType]]) -> Dict[str, List[ProtocolValidationError]]:
    """
    Verify all protocol implementations in the given modules.
    
    This is useful for running a system-wide protocol validation check
    to ensure all implementations correctly fulfill their protocols.
    
    Args:
        modules: A list of modules or module names to check.
        
    Returns:
        A dictionary mapping class names to a list of validation errors.
    """
    errors = {}
    
    for module in modules:
        if isinstance(module, str):
            import importlib
            module = importlib.import_module(module)
        
        # Process the module and all its submodules
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and hasattr(obj, '__implemented_protocols__'):
                class_errors = []
                
                for protocol in obj.__implemented_protocols__:
                    try:
                        validate_protocol(obj, protocol)
                    except ProtocolValidationError as e:
                        class_errors.append(e)
                
                if class_errors:
                    errors[f"{obj.__module__}.{obj.__name__}"] = class_errors
        
        # Process submodules if it's a package
        if hasattr(module, '__path__'):
            import pkgutil
            for _, submodule_name, is_pkg in pkgutil.iter_modules(module.__path__):
                full_name = f"{module.__name__}.{submodule_name}"
                try:
                    import importlib
                    submodule = importlib.import_module(full_name)
                    submodule_errors = verify_all_implementations([submodule])
                    errors.update(submodule_errors)
                except ImportError:
                    # Skip modules that can't be imported
                    continue
    
    return errors


def _type_to_str(typ: Any) -> str:
    """
    Convert a type to a readable string representation.
    
    Args:
        typ: The type to convert.
        
    Returns:
        A string representation of the type.
    """
    if typ is Any:
        return 'Any'
    
    if hasattr(typ, '__origin__'):
        if typ.__origin__ is Union:
            if type(None) in typ.__args__:
                # Optional[X]
                non_none_args = [arg for arg in typ.__args__ if arg is not type(None)]
                if len(non_none_args) == 1:
                    return f'Optional[{_type_to_str(non_none_args[0])}]'
            return f"Union[{', '.join(_type_to_str(arg) for arg in typ.__args__)}]"
        
        # Handle generic types
        args_str = ', '.join(_type_to_str(arg) for arg in typ.__args__)
        origin_name = typ.__origin__.__name__
        return f"{origin_name}[{args_str}]"
    
    # Handle protocols
    if hasattr(typ, '_is_protocol') and typ._is_protocol:
        return f"Protocol[{typ.__name__}]"
    
    # Handle simple types
    if isinstance(typ, type):
        return typ.__name__
    
    # Default case
    return str(typ)