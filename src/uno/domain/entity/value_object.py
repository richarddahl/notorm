"""
Value objects for domain entities.

This module provides the ValueObject base class, which serves as the foundation
for all value objects in the domain model. Value objects are immutable objects
that represent concepts in the domain and are characterized by their attributes
rather than an identity.
"""

from typing import Any, Optional, TypeVar, Type
from pydantic import BaseModel, ConfigDict

T = TypeVar('T', bound='ValueObject')


class ValueObject(BaseModel):
    """
    Base class for all value objects.
    
    Value objects are immutable objects that describe aspects of the domain.
    They have no identity and are defined by their attributes.
    
    Characteristics:
    - Immutability: Cannot be changed after creation
    - Equality: Determined by attribute values, not identity
    - Self-validation: Validates its own attributes
    """
    
    # Make the model immutable
    model_config = ConfigDict(
        frozen=True,  # Immutability
        arbitrary_types_allowed=True,
    )
    
    def equals(self, other: Any) -> bool:
        """
        Check if this value object is equal to another.
        
        Args:
            other: The object to compare with
            
        Returns:
            True if equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        
        # Compare by attribute values
        return self.model_dump() == other.model_dump()
    
    def __eq__(self, other: Any) -> bool:
        """
        Equality operator.
        
        Args:
            other: The object to compare with
            
        Returns:
            True if equal, False otherwise
        """
        return self.equals(other)
    
    def __hash__(self) -> int:
        """
        Hash function.
        
        Returns:
            Hash of the frozen object
        """
        # Since the object is immutable, we can hash its attributes
        return hash(tuple(sorted(self.model_dump().items())))
    
    def with_changes(self: T, **kwargs: Any) -> T:
        """
        Create a new instance of this value object with some changes.
        
        Since value objects are immutable, we need to create a new instance
        to change any attribute.
        
        Args:
            **kwargs: Attributes to change
            
        Returns:
            A new instance with the changes applied
        """
        # Create a new instance with the changes
        return self.__class__(**{**self.model_dump(), **kwargs})