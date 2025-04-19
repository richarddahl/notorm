"""
Base class for domain entities in the UNO framework.

This module provides the EntityBase class, which is the foundation for all
domain entities in the UNO framework. It implements identity equality,
timestamp tracking, and other essential entity behaviors.
"""

import uuid
from datetime import datetime, UTC
from typing import TypeVar, Generic, Any, ClassVar, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field, model_validator

ID = TypeVar('ID')


class EntityBase(Generic[ID], BaseModel):
    """
    Base class for all domain entities.
    
    Entities are objects that have a distinct identity that runs through time
    and different representations. They are defined by their identity, not by
    their attributes.
    
    This base class provides:
    - Identity management
    - Equality and hashing based on identity
    - Creation and modification timestamps
    - Change tracking
    """
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra='ignore',
        frozen=False,
    )
    
    id: ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None
    
    # Class variables to track entity metadata
    __track_changes__: ClassVar[bool] = True
    __changes__: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    
    @model_validator(mode='after')
    def set_defaults(self) -> 'EntityBase':
        """Set default values for the entity."""
        if self.updated_at is None:
            self.updated_at = self.created_at
        return self
    
    def __eq__(self, other: Any) -> bool:
        """
        Compare entities by identity.
        
        Entities are considered equal if they have the same type and ID.
        
        Args:
            other: The object to compare with
            
        Returns:
            True if the entities are equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """
        Hash entity by identity.
        
        Returns:
            Hash value based on entity type and ID
        """
        return hash((self.__class__, self.id))
    
    def mark_modified(self) -> None:
        """
        Mark the entity as modified.
        
        This updates the updated_at timestamp to the current time.
        """
        self.updated_at = datetime.now(UTC)
    
    def record_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """
        Record a change to an entity field.
        
        This method is called when a field is changed, and it records the
        change in the __changes__ dictionary.
        
        Args:
            field: The field that changed
            old_value: The previous value
            new_value: The new value
        """
        if not self.__track_changes__:
            return
            
        if field not in self.__changes__:
            self.__changes__[field] = {
                'old': old_value,
                'new': new_value,
                'timestamp': datetime.now(UTC)
            }
        else:
            # Update the new value but keep the original old value
            self.__changes__[field]['new'] = new_value
            self.__changes__[field]['timestamp'] = datetime.now(UTC)
    
    def get_changes(self) -> Dict[str, Any]:
        """
        Get the changes recorded for this entity.
        
        Returns:
            A dictionary of recorded changes
        """
        return self.__changes__.copy()
    
    def clear_changes(self) -> None:
        """Clear the recorded changes."""
        self.__changes__.clear()
    
    @classmethod
    def create(cls, **kwargs: Any) -> 'EntityBase[ID]':
        """
        Create a new entity instance.
        
        This factory method provides a consistent way to create entities,
        ensuring all required fields are set properly.
        
        Args:
            **kwargs: Entity attributes
            
        Returns:
            A new entity instance
        """
        # Generate a UUID if ID is not provided and ID is a string
        if 'id' not in kwargs and cls.__annotations__.get('id', None) == str:
            kwargs['id'] = str(uuid.uuid4())
            
        return cls(**kwargs)