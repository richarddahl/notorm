"""
Domain exceptions for the Uno framework.

This module defines exceptions that represent domain-level errors.

IMPORTANT: This file is deprecated and provided only for backward compatibility.
Use the uno.core.errors package instead.
"""

import warnings
from typing import Any, Dict, Optional

warnings.warn(
    "Importing from uno.domain.exceptions is deprecated. "
    "Import from uno.core.errors.base, uno.core.errors.result, etc. instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import from the new location to maintain backward compatibility
from uno.core.errors.base import UnoError


class DomainError(UnoError):
    """
    Base class for all domain-level exceptions.
    
    Domain errors represent business rule violations and other exceptional
    conditions that arise in the domain model.
    
    DEPRECATED: Use UnoError from uno.core.errors.base instead.
    """
    
    def __init__(self, message: str, code: str, details: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize domain error.
        
        Args:
            message: Human-readable error message
            code: Machine-readable error code
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.details = details or {}
        
        # Map to UnoError properties
        context = self.details.copy()
        if kwargs:
            context.update(kwargs)
        
        super().__init__(message=message, error_code=code, **context)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary representation.
        
        Returns:
            Dictionary with error details
        """
        return {
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }


class ValidationError(DomainError):
    """
    Exception raised when validation fails.
    
    This exception is raised when command validation or input validation fails.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            details: Validation error details
        """
        super().__init__(message, "VALIDATION_ERROR", details)


class DomainValidationError(DomainError):
    """
    Exception raised when domain validation fails.
    
    This exception is raised when an entity or value object fails validation,
    such as when a business rule is violated.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            details: Validation error details
        """
        super().__init__(message, "DOMAIN_VALIDATION_ERROR", details)


class EntityNotFoundError(DomainError):
    """
    Exception raised when an entity cannot be found.
    
    This exception is raised when attempting to retrieve an entity that
    doesn't exist in the repository.
    """
    
    def __init__(self, entity_type: str, entity_id: Any):
        """
        Initialize entity not found error.
        
        Args:
            entity_type: Type of entity that was not found
            entity_id: Identifier of the entity
        """
        message = f"{entity_type} with ID {entity_id} not found"
        details = {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
        }
        super().__init__(message, "ENTITY_NOT_FOUND", details)


class BusinessRuleViolationError(DomainError):
    """
    Exception raised when a business rule is violated.
    
    This exception is raised when an operation would violate a business rule,
    such as when attempting to perform an action that is not allowed in the
    current state.
    """
    
    def __init__(self, message: str, rule_name: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize business rule violation error.
        
        Args:
            message: Human-readable error message
            rule_name: Name of the violated business rule
            details: Additional error details
        """
        error_details = details or {}
        error_details["rule_name"] = rule_name
        super().__init__(message, "BUSINESS_RULE_VIOLATION", error_details)


class ConcurrencyError(DomainError):
    """
    Exception raised when a concurrency conflict occurs.
    
    This exception is raised when attempting to update an entity that has
    been modified by another operation since it was retrieved.
    """
    
    def __init__(self, entity_type: str, entity_id: Any):
        """
        Initialize concurrency error.
        
        Args:
            entity_type: Type of entity with the concurrency conflict
            entity_id: Identifier of the entity
        """
        message = f"Concurrency conflict for {entity_type} with ID {entity_id}"
        details = {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
        }
        super().__init__(message, "CONCURRENCY_CONFLICT", details)


class AggregateInvariantViolationError(DomainError):
    """
    Exception raised when an aggregate invariant is violated.
    
    This exception is raised when an operation would leave an aggregate
    in an invalid state, violating its invariants.
    """
    
    def __init__(self, aggregate_type: str, invariant_name: str, message: str):
        """
        Initialize aggregate invariant violation error.
        
        Args:
            aggregate_type: Type of aggregate with the violated invariant
            invariant_name: Name of the violated invariant
            message: Human-readable error message
        """
        details = {
            "aggregate_type": aggregate_type,
            "invariant_name": invariant_name,
        }
        super().__init__(message, "AGGREGATE_INVARIANT_VIOLATION", details)


class CommandHandlerNotFoundError(DomainError):
    """
    Exception raised when a command handler cannot be found.
    
    This exception is raised when attempting to dispatch a command for which
    there is no registered handler.
    """
    
    def __init__(self, command_type: str):
        """
        Initialize command handler not found error.
        
        Args:
            command_type: Type of command that has no handler
        """
        message = f"No handler registered for command {command_type}"
        details = {"command_type": command_type}
        super().__init__(message, "COMMAND_HANDLER_NOT_FOUND", details)


class QueryHandlerNotFoundError(DomainError):
    """
    Exception raised when a query handler cannot be found.
    
    This exception is raised when attempting to dispatch a query for which
    there is no registered handler.
    """
    
    def __init__(self, query_type: str):
        """
        Initialize query handler not found error.
        
        Args:
            query_type: Type of query that has no handler
        """
        message = f"No handler registered for query {query_type}"
        details = {"query_type": query_type}
        super().__init__(message, "QUERY_HANDLER_NOT_FOUND", details)


class CommandExecutionError(DomainError):
    """
    Exception raised when a command execution fails.
    
    This exception is raised when a command fails to execute due to an error
    in the command handler.
    """
    
    def __init__(self, command_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize command execution error.
        
        Args:
            command_type: Type of command that failed to execute
            message: Human-readable error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["command_type"] = command_type
        super().__init__(message, "COMMAND_EXECUTION_ERROR", error_details)


class QueryExecutionError(DomainError):
    """
    Exception raised when a query execution fails.
    
    This exception is raised when a query fails to execute due to an error
    in the query handler.
    """
    
    def __init__(self, query_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize query execution error.
        
        Args:
            query_type: Type of query that failed to execute
            message: Human-readable error message
            details: Additional error details
        """
        error_details = details or {}
        error_details["query_type"] = query_type
        super().__init__(message, "QUERY_EXECUTION_ERROR", error_details)


class AuthorizationError(DomainError):
    """
    Exception raised when authorization fails.
    
    This exception is raised when a user is not authorized to perform an operation.
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize authorization error.
        
        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(message, "AUTHORIZATION_ERROR", details)