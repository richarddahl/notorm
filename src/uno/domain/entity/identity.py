"""
Identity management for domain entities.

This module provides utilities for generating, validating, and managing
entity identities in a type-safe way.
"""

import uuid
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, Protocol, cast
from pydantic import BaseModel, ConfigDict

T = TypeVar('T')


class Identity(Generic[T], BaseModel):
    """
    Value object representing an entity identity.
    
    This class wraps a primitive value (string, int, etc.) to create a
    type-safe identity for domain entities.
    
    Example:
        ```python
        class UserId(Identity[str]):
            pass
            
        user_id = UserId(value=str(uuid.uuid4()))
        ```
    """
    
    model_config = ConfigDict(
        frozen=True,  # Immutable
    )
    
    value: T
    
    def __eq__(self, other: Any) -> bool:
        """
        Compare identities by value.
        
        Args:
            other: The object to compare with
            
        Returns:
            True if the identities have the same value and type, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        """
        Hash identity by value.
        
        Returns:
            Hash value based on identity type and value
        """
        return hash((self.__class__, self.value))
    
    def __str__(self) -> str:
        """
        Convert identity to string.
        
        Returns:
            String representation of the identity value
        """
        return str(self.value)
    
    def __repr__(self) -> str:
        """
        Create readable representation of the identity.
        
        Returns:
            Readable representation of the identity
        """
        return f"{self.__class__.__name__}({self.value!r})"


class IdentityGenerator(Protocol, Generic[T]):
    """
    Protocol for generating entity identities.
    
    Implementations of this protocol are responsible for generating
    unique identities for domain entities.
    """
    
    @abstractmethod
    def next_id(self) -> T:
        """
        Generate a new unique identity.
        
        Returns:
            A new unique identity
        """
        pass


class UuidGenerator(IdentityGenerator[str]):
    """Generator for UUID-based string identities."""
    
    def next_id(self) -> str:
        """
        Generate a new UUID-based identity.
        
        Returns:
            A new UUID as a string
        """
        return str(uuid.uuid4())


class SequentialGenerator(IdentityGenerator[int]):
    """Generator for sequential integer identities."""
    
    def __init__(self, start: int = 1):
        """
        Initialize the generator.
        
        Args:
            start: The starting value for the sequence
        """
        self._next = start
    
    def next_id(self) -> int:
        """
        Generate the next sequential identity.
        
        Returns:
            The next sequential integer identity
        """
        result = self._next
        self._next += 1
        return result


# Default identity generators
default_uuid_generator = UuidGenerator()
default_sequential_generator = SequentialGenerator()