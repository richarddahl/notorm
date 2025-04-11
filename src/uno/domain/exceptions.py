"""
Domain exceptions for the Uno framework.

This module defines exceptions that represent domain-level errors.
"""

from typing import Any, Dict, Optional


class DomainError(Exception):
    """
    Base class for all domain-level exceptions.
    
    Domain errors represent business rule violations and other exceptional
    conditions that arise in the domain model.
    """
    
    def __init__(self, message: str, code: str, details: Optional[Dict[str, Any]] = None):
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
        super().__init__(message)
    
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