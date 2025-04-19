"""
Base specification implementations for the Specification pattern.

This module provides the base classes for implementing the Specification pattern,
which allows for encapsulating query criteria in reusable, composable objects.

The Specification pattern is useful for:
- Building complex queries by composing simple ones (AND, OR, NOT)
- Creating a DSL for business rules
- Separating query logic from domain objects
- Making business rules explicit and testable
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Optional, TypeVar, Type, Tuple, Protocol, runtime_checkable

T = TypeVar('T')  # The type of objects the specification checks


@runtime_checkable
class Specifiable(Protocol):
    """Protocol for objects that can be checked against specifications."""
    pass


class Specification(Generic[T], ABC):
    """
    Base class for all specifications.
    
    A specification is an object that encapsulates a business rule or a query criterion
    and determines whether a given object satisfies it.
    """
    
    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.
        
        Args:
            candidate: The object to check against the specification
            
        Returns:
            True if the candidate satisfies the specification, False otherwise
        """
        pass
    
    def and_(self, other: 'Specification[T]') -> 'Specification[T]':
        """
        Combine this specification with another using logical AND.
        
        Args:
            other: Another specification to combine with
            
        Returns:
            A new specification that is satisfied only when both specifications are satisfied
        """
        from uno.domain.entity.specification.composite import AndSpecification
        return AndSpecification(self, other)
    
    def or_(self, other: 'Specification[T]') -> 'Specification[T]':
        """
        Combine this specification with another using logical OR.
        
        Args:
            other: Another specification to combine with
            
        Returns:
            A new specification that is satisfied when either specification is satisfied
        """
        from uno.domain.entity.specification.composite import OrSpecification
        return OrSpecification(self, other)
    
    def not_(self) -> 'Specification[T]':
        """
        Negate this specification.
        
        Returns:
            A new specification that is satisfied when this specification is not satisfied
        """
        from uno.domain.entity.specification.composite import NotSpecification
        return NotSpecification(self)


class PredicateSpecification(Specification[T]):
    """
    Specification based on a predicate function.
    
    This is a simple way to create specifications from functions.
    """
    
    def __init__(self, predicate: Callable[[T], bool], description: Optional[str] = None):
        """
        Initialize the specification with a predicate.
        
        Args:
            predicate: Function that takes an object and returns a boolean
            description: Optional description of what the specification checks
        """
        self.predicate = predicate
        self.description = description or f"Predicate {predicate.__name__}"
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.
        
        Args:
            candidate: The object to check against the specification
            
        Returns:
            True if the candidate satisfies the predicate, False otherwise
        """
        return self.predicate(candidate)
    
    def __str__(self) -> str:
        """Return a string representation of the specification."""
        return self.description


class AttributeSpecification(Specification[T]):
    """
    Specification that checks an attribute of an object.
    
    This is useful for simple equality checks on object attributes.
    """
    
    def __init__(
        self, 
        attribute_name: str, 
        expected_value: Any,
        comparator: Optional[Callable[[Any, Any], bool]] = None
    ):
        """
        Initialize the specification with an attribute name and expected value.
        
        Args:
            attribute_name: The name of the attribute to check
            expected_value: The expected value of the attribute
            comparator: Optional function to compare the attribute value with the expected value
        """
        self.attribute_name = attribute_name
        self.expected_value = expected_value
        self.comparator = comparator or (lambda a, b: a == b)
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies this specification.
        
        Args:
            candidate: The object to check against the specification
            
        Returns:
            True if the attribute has the expected value, False otherwise
        """
        # Use getattr to access the attribute, if it exists
        if hasattr(candidate, self.attribute_name):
            attribute_value = getattr(candidate, self.attribute_name)
            return self.comparator(attribute_value, self.expected_value)
        
        # If the candidate is a dict, try to access the attribute as a key
        if isinstance(candidate, dict) and self.attribute_name in candidate:
            return self.comparator(candidate[self.attribute_name], self.expected_value)
        
        return False
    
    def __str__(self) -> str:
        """Return a string representation of the specification."""
        return f"{self.attribute_name} == {self.expected_value}"