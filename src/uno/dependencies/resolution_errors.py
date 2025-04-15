# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error classes for dependency resolution failures.

This module provides detailed error classes for dependency injection resolution
failures, including helpful context information and suggestions.
"""

from typing import Type, Dict, Any, List, Optional, Set


class DependencyResolutionError(Exception):
    """Base class for dependency resolution errors."""
    
    def __init__(
        self, 
        message: str,
        service_type: Optional[Type] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.service_type = service_type
        self.context = context or {}
        self.message = message
        super().__init__(message)


class ServiceNotRegisteredError(DependencyResolutionError):
    """Error raised when a service type is not registered with the container."""
    
    def __init__(
        self,
        service_type: Type,
        similar_services: Optional[List[Type]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.similar_services = similar_services or []
        type_name = getattr(service_type, "__name__", str(service_type))
        
        message = f"No registration found for {type_name}"
        
        if similar_services:
            similar_names = [getattr(t, "__name__", str(t)) for t in similar_services[:3]]
            message += f". Did you mean one of: {', '.join(similar_names)}?"
        
        super().__init__(message, service_type, context)


class CircularDependencyError(DependencyResolutionError):
    """Error raised when a circular dependency is detected."""
    
    def __init__(
        self,
        service_type: Type,
        dependency_chain: List[Type],
        context: Optional[Dict[str, Any]] = None
    ):
        self.dependency_chain = dependency_chain
        type_name = getattr(service_type, "__name__", str(service_type))
        
        chain_repr = " -> ".join([getattr(t, "__name__", str(t)) for t in dependency_chain])
        
        message = (
            f"Circular dependency detected while resolving {type_name}. "
            f"Dependency chain: {chain_repr}"
        )
        
        super().__init__(message, service_type, context)


class ScopeMismatchError(DependencyResolutionError):
    """Error raised when a scoped service is requested outside a scope."""
    
    def __init__(
        self,
        service_type: Type,
        expected_scope: str,
        actual_scope: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.expected_scope = expected_scope
        self.actual_scope = actual_scope
        type_name = getattr(service_type, "__name__", str(service_type))
        
        if actual_scope:
            message = (
                f"Scoped service {type_name} cannot be resolved in {actual_scope} scope. "
                f"Expected: {expected_scope}"
            )
        else:
            message = f"Scoped service {type_name} cannot be resolved outside a scope."
        
        super().__init__(message, service_type, context)


class MissingDependencyError(DependencyResolutionError):
    """Error raised when a required dependency cannot be resolved."""
    
    def __init__(
        self,
        service_type: Type,
        dependency_type: Type,
        parameter_name: str,
        possible_resolutions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.dependency_type = dependency_type
        self.parameter_name = parameter_name
        self.possible_resolutions = possible_resolutions or []
        
        service_name = getattr(service_type, "__name__", str(service_type))
        dependency_name = getattr(dependency_type, "__name__", str(dependency_type))
        
        message = (
            f"Cannot resolve required dependency {dependency_name} for parameter '{parameter_name}' "
            f"while resolving {service_name}"
        )
        
        if possible_resolutions:
            message += ". Possible solutions:\n" + "\n".join(
                f"- {solution}" for solution in possible_resolutions
            )
        
        super().__init__(message, service_type, context)


class DependencyGraphError(DependencyResolutionError):
    """Error raised for issues in the dependency graph."""
    
    def __init__(
        self,
        message: str,
        service_type: Optional[Type] = None,
        affected_services: Optional[List[Type]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.affected_services = affected_services or []
        
        if affected_services:
            service_names = [getattr(t, "__name__", str(t)) for t in affected_services[:5]]
            if len(affected_services) > 5:
                service_names.append(f"... ({len(affected_services) - 5} more)")
            
            message += f"\nAffected services: {', '.join(service_names)}"
        
        super().__init__(message, service_type, context)


class ServiceInitializationError(DependencyResolutionError):
    """Error raised when a service fails to initialize."""
    
    def __init__(
        self,
        service_type: Type,
        original_error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        self.original_error = original_error
        type_name = getattr(service_type, "__name__", str(service_type))
        
        message = (
            f"Error initializing service {type_name}: {str(original_error)}"
        )
        
        if context is None:
            context = {}
        
        context["original_error"] = original_error
        
        super().__init__(message, service_type, context)


class ServiceDisposalError(DependencyResolutionError):
    """Error raised when a service fails to dispose properly."""
    
    def __init__(
        self,
        service_type: Type,
        original_error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        self.original_error = original_error
        type_name = getattr(service_type, "__name__", str(service_type))
        
        message = (
            f"Error disposing service {type_name}: {str(original_error)}"
        )
        
        if context is None:
            context = {}
        
        context["original_error"] = original_error
        
        super().__init__(message, service_type, context)


def format_dependency_chain(
    dependency_chain: List[Type], 
    highlight_index: Optional[int] = None
) -> str:
    """Format a dependency chain for error messages."""
    if not dependency_chain:
        return ""
    
    formatted = []
    for i, dep in enumerate(dependency_chain):
        name = getattr(dep, "__name__", str(dep))
        
        if i == highlight_index:
            formatted.append(f"[{name}]")  # Highlight with brackets
        else:
            formatted.append(name)
    
    return " -> ".join(formatted)