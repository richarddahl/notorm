"""
Composite specification implementations for the Specification pattern.

This module provides composite classes that combine specifications using logical
operators (AND, OR, NOT) to create more complex specifications from simple ones.
"""

from typing import Generic, TypeVar, List

from uno.domain.entity.specification.base import Specification

T = TypeVar('T')  # The type of objects the specification checks


class CompositeSpecification(Specification[T]):
    """
    Base class for composite specifications.
    
    Composite specifications combine other specifications using logical operators.
    """
    pass


class AndSpecification(CompositeSpecification[T]):
    """
    Specification that combines two specifications with logical AND.
    
    This specification is satisfied only when both of its component specifications are satisfied.
    """
    
    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Initialize with two specifications to combine with AND.
        
        Args:
            left: First specification to check
            right: Second specification to check
        """
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies both specifications.
        
        Args:
            candidate: The object to check against the specification
            
        Returns:
            True if both specifications are satisfied, False otherwise
        """
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)
    
    def __str__(self) -> str:
        """Return a string representation of the specification."""
        return f"({self.left}) AND ({self.right})"


class OrSpecification(CompositeSpecification[T]):
    """
    Specification that combines two specifications with logical OR.
    
    This specification is satisfied when either of its component specifications is satisfied.
    """
    
    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Initialize with two specifications to combine with OR.
        
        Args:
            left: First specification to check
            right: Second specification to check
        """
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies either specification.
        
        Args:
            candidate: The object to check against the specification
            
        Returns:
            True if either specification is satisfied, False otherwise
        """
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)
    
    def __str__(self) -> str:
        """Return a string representation of the specification."""
        return f"({self.left}) OR ({self.right})"


class NotSpecification(CompositeSpecification[T]):
    """
    Specification that negates another specification.
    
    This specification is satisfied when its component specification is not satisfied.
    """
    
    def __init__(self, specification: Specification[T]):
        """
        Initialize with a specification to negate.
        
        Args:
            specification: The specification to negate
        """
        self.specification = specification
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate does not satisfy the inner specification.
        
        Args:
            candidate: The object to check against the specification
            
        Returns:
            True if the specification is not satisfied, False otherwise
        """
        return not self.specification.is_satisfied_by(candidate)
    
    def __str__(self) -> str:
        """Return a string representation of the specification."""
        return f"NOT ({self.specification})"


class AllSpecification(CompositeSpecification[T]):
    """
    Specification that combines multiple specifications with logical AND.
    
    This specification is satisfied only when all of its component specifications are satisfied.
    """
    
    def __init__(self, specifications: List[Specification[T]]):
        """
        Initialize with a list of specifications to combine with AND.
        
        Args:
            specifications: List of specifications to check
        """
        self.specifications = specifications
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies all specifications.
        
        Args:
            candidate: The object to check against the specification
            
        Returns:
            True if all specifications are satisfied, False otherwise
        """
        return all(spec.is_satisfied_by(candidate) for spec in self.specifications)
    
    def __str__(self) -> str:
        """Return a string representation of the specification."""
        return " AND ".join(f"({spec})" for spec in self.specifications)


class AnySpecification(CompositeSpecification[T]):
    """
    Specification that combines multiple specifications with logical OR.
    
    This specification is satisfied when any of its component specifications is satisfied.
    """
    
    def __init__(self, specifications: List[Specification[T]]):
        """
        Initialize with a list of specifications to combine with OR.
        
        Args:
            specifications: List of specifications to check
        """
        self.specifications = specifications
    
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Check if the candidate satisfies any specification.
        
        Args:
            candidate: The object to check against the specification
            
        Returns:
            True if any specification is satisfied, False otherwise
        """
        return any(spec.is_satisfied_by(candidate) for spec in self.specifications)
    
    def __str__(self) -> str:
        """Return a string representation of the specification."""
        return " OR ".join(f"({spec})" for spec in self.specifications)