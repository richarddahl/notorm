"""
Base specification pattern implementation for domain models.

This module provides a flexible, composable way to express business rules
and constraints on domain entities.
"""

from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar, Any, Callable, Dict

from uno.domain.protocols import EntityProtocol, SpecificationProtocol

# Type variable for the entity being specified
T = TypeVar('T', bound=EntityProtocol)


class Specification(Generic[T], ABC):
    """Base class for all specifications."""
    
    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity satisfies this specification.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the specification is satisfied, False otherwise
        """
        pass
    
    def and_(self, other: SpecificationProtocol[T]) -> SpecificationProtocol[T]:
        """
        Combine with another specification using AND.
        
        Args:
            other: The specification to combine with
            
        Returns:
            A new specification that is satisfied when both are satisfied
        """
        return AndSpecification(self, other)
    
    def or_(self, other: SpecificationProtocol[T]) -> SpecificationProtocol[T]:
        """
        Combine with another specification using OR.
        
        Args:
            other: The specification to combine with
            
        Returns:
            A new specification that is satisfied when either is satisfied
        """
        return OrSpecification(self, other)
    
    def not_(self) -> SpecificationProtocol[T]:
        """
        Negate this specification.
        
        Returns:
            A new specification that is satisfied when this one is not
        """
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    """Specification that is satisfied when both of its components are satisfied."""
    
    def __init__(self, left: SpecificationProtocol[T], right: SpecificationProtocol[T]):
        """
        Initialize the AND specification.
        
        Args:
            left: The left specification
            right: The right specification
        """
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity satisfies both specifications.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if both specifications are satisfied, False otherwise
        """
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)


class OrSpecification(Specification[T]):
    """Specification that is satisfied when either of its components is satisfied."""
    
    def __init__(self, left: SpecificationProtocol[T], right: SpecificationProtocol[T]):
        """
        Initialize the OR specification.
        
        Args:
            left: The left specification
            right: The right specification
        """
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity satisfies either specification.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if either specification is satisfied, False otherwise
        """
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)


class NotSpecification(Specification[T]):
    """Specification that is satisfied when its component is not satisfied."""
    
    def __init__(self, specification: SpecificationProtocol[T]):
        """
        Initialize the NOT specification.
        
        Args:
            specification: The specification to negate
        """
        self.specification = specification
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity does not satisfy the specification.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the specification is not satisfied, False otherwise
        """
        return not self.specification.is_satisfied_by(entity)


class AttributeSpecification(Specification[T]):
    """Specification that checks a single attribute against a value."""
    
    def __init__(self, attribute: str, value: Any):
        """
        Initialize the attribute specification.
        
        Args:
            attribute: The attribute to check
            value: The value to compare against
        """
        self.attribute = attribute
        self.value = value
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's attribute equals the expected value.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the attribute equals the value, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        return getattr(entity, self.attribute) == self.value


class PredicateSpecification(Specification[T]):
    """Specification that uses a predicate function to check an entity."""
    
    def __init__(self, predicate: Callable[[T], bool], name: str = None):
        """
        Initialize the predicate specification.
        
        Args:
            predicate: The predicate function
            name: Optional name for the specification
        """
        self.predicate = predicate
        self.name = name or predicate.__name__
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity satisfies the predicate.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the predicate returns True, False otherwise
        """
        return self.predicate(entity)


class DictionarySpecification(Specification[Dict[str, Any]]):
    """Specification that checks a dictionary against conditions."""
    
    def __init__(self, conditions: Dict[str, Any]):
        """
        Initialize the dictionary specification.
        
        Args:
            conditions: Dictionary of key-value pairs to check
        """
        self.conditions = conditions
    
    def is_satisfied_by(self, entity: Dict[str, Any]) -> bool:
        """
        Check if the dictionary satisfies all conditions.
        
        Args:
            entity: The dictionary to check
            
        Returns:
            True if all conditions are satisfied, False otherwise
        """
        for key, value in self.conditions.items():
            if key not in entity or entity[key] != value:
                return False
        return True


def specification_factory(entity_type: Type[T]) -> Type[Specification[T]]:
    """
    Create a specification class for a specific entity type.
    
    Args:
        entity_type: The entity type
        
    Returns:
        A specification class for the entity type
    """
    class EntitySpecification(Specification[entity_type]):
        """Specification for a specific entity type."""
        
        @classmethod
        def attribute(cls, attribute: str, value: Any) -> Specification[entity_type]:
            """
            Create a specification for an attribute.
            
            Args:
                attribute: The attribute to check
                value: The value to compare against
                
            Returns:
                A specification that checks if the attribute equals the value
            """
            return AttributeSpecification(attribute, value)
        
        @classmethod
        def predicate(cls, predicate: Callable[[entity_type], bool], name: str = None) -> Specification[entity_type]:
            """
            Create a specification for a predicate function.
            
            Args:
                predicate: The predicate function
                name: Optional name for the specification
                
            Returns:
                A specification that uses the predicate function
            """
            return PredicateSpecification(predicate, name)
    
    return EntitySpecification