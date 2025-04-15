"""
Domain entities for the Meta module.

This module contains domain entities for meta types and meta records used in the application.
These are core entities that provide a foundation for type and record tracking in the system.
"""

from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Dict, Any, Set

from uno.domain.core import Entity, AggregateRoot
from uno.core.errors.base import ValidationError


@dataclass
class MetaType(AggregateRoot[str]):
    """
    Domain entity for meta types.

    Meta types define the types of records in the system and are used for
    type-safety and tracking throughout the application.
    """

    id: str
    name: Optional[str] = None  # Derived from ID but can be customized
    description: Optional[str] = None

    # Navigation properties (not persisted directly)
    meta_records: List["MetaRecord"] = field(default_factory=list, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "MetaTypeModel"

    def validate(self) -> None:
        """Validate the meta type."""
        if not self.id:
            raise ValidationError("ID cannot be empty")

        # Ensure ID is valid
        if not self.id.isalnum() and "_" not in self.id:
            raise ValidationError(
                "ID must contain only alphanumeric characters and underscores"
            )

    @property
    def display_name(self) -> str:
        """Get a human-readable display name for this meta type."""
        if self.name:
            return self.name

        # Convert ID to a readable name (e.g., "user_profile" -> "User Profile")
        return " ".join(word.capitalize() for word in self.id.split("_"))


@dataclass
class MetaRecord(AggregateRoot[str]):
    """
    Domain entity for meta records.

    Meta records represent specific instances of meta types and serve as
    the base for all identifiable objects in the system.
    """

    id: str
    meta_type_id: str

    # Navigation properties (not persisted directly)
    meta_type: Optional[MetaType] = field(default=None, repr=False)
    attributes: List[str] = field(default_factory=list, repr=False)  # IDs of attributes

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "MetaRecordModel"

    def validate(self) -> None:
        """Validate the meta record."""
        if not self.id:
            raise ValidationError("ID cannot be empty")
        if not self.meta_type_id:
            raise ValidationError("Meta type ID cannot be empty")

    def add_attribute(self, attribute_id: str) -> None:
        """
        Add an attribute to this meta record.

        Args:
            attribute_id: The ID of the attribute to add
        """
        if attribute_id not in self.attributes:
            self.attributes.append(attribute_id)

    @property
    def type_name(self) -> str:
        """Get the name of the meta type."""
        if self.meta_type:
            return self.meta_type.display_name
        return self.meta_type_id
