"""
Domain entities for the Attributes module.

This module contains domain entities for attribute types and attributes used in the application.
"""

from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Dict, Any, Set

from uno.domain.core import Entity, AggregateRoot
from uno.core.base.error import ValidationError


@dataclass
class MetaTypeRef:
    """Reference to a MetaType entity."""

    id: str
    name: Optional[str] = None


@dataclass
class QueryRef:
    """Reference to a Query entity."""

    id: str
    name: Optional[str] = None


@dataclass
class AttributeType(AggregateRoot[str]):
    """
    Domain entity for attribute types.

    Attribute types define the structure and behavior of attributes that can be
    associated with objects in the system.
    """

    name: str
    text: str
    parent_id: Optional[str] = None
    description_limiting_query_id: Optional[str] = None
    value_type_limiting_query_id: Optional[str] = None
    required: bool = False
    multiple_allowed: bool = False
    comment_required: bool = False
    display_with_objects: bool = False
    initial_comment: Optional[str] = None
    group_id: Optional[str] = None
    tenant_id: Optional[str] = None

    # Navigation properties (not persisted directly)
    parent: Optional["AttributeType"] = field(default=None, repr=False)
    children: List["AttributeType"] = field(default_factory=list, repr=False)
    describes: List[MetaTypeRef] = field(default_factory=list, repr=False)
    description_limiting_query: Optional[QueryRef] = field(default=None, repr=False)
    value_types: List[MetaTypeRef] = field(default_factory=list, repr=False)
    value_type_limiting_query: Optional[QueryRef] = field(default=None, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "AttributeTypeModel"

    def validate(self) -> None:
        """Validate the attribute type."""
        if not self.name:
            raise ValidationError("Name cannot be empty")
        if not self.text:
            raise ValidationError("Text cannot be empty")

        # Additional business rules
        if self.comment_required and not self.initial_comment:
            raise ValidationError(
                "Initial comment is required when comment is required"
            )

        # Circular reference check
        current = self
        parent_ids: Set[str] = set()
        while current.parent_id and current.parent_id not in parent_ids:
            parent_ids.add(current.parent_id)
            if current.parent_id == self.id:
                raise ValidationError("Circular reference detected in parent hierarchy")
            if not current.parent:  # Can't check further without parent loaded
                break
            current = current.parent

    def add_value_type(self, meta_type_id: str, name: Optional[str] = None) -> None:
        """
        Add a value type to this attribute type.

        Args:
            meta_type_id: The ID of the meta type
            name: Optional name of the meta type
        """
        ref = MetaTypeRef(id=meta_type_id, name=name)
        if ref not in self.value_types:
            self.value_types.append(ref)

    def add_describable_type(
        self, meta_type_id: str, name: Optional[str] = None
    ) -> None:
        """
        Add a meta type that this attribute type can describe.

        Args:
            meta_type_id: The ID of the meta type
            name: Optional name of the meta type
        """
        ref = MetaTypeRef(id=meta_type_id, name=name)
        if ref not in self.describes:
            self.describes.append(ref)

    def can_describe(self, meta_type_id: str) -> bool:
        """
        Check if this attribute type can describe a given meta type.

        Args:
            meta_type_id: The ID of the meta type to check

        Returns:
            True if this attribute type can describe the meta type
        """
        return any(mt.id == meta_type_id for mt in self.describes)

    def can_have_value_type(self, meta_type_id: str) -> bool:
        """
        Check if this attribute type can have a given meta type as a value.

        Args:
            meta_type_id: The ID of the meta type to check

        Returns:
            True if this attribute type can have the meta type as a value
        """
        return any(mt.id == meta_type_id for mt in self.value_types)


@dataclass
class Attribute(AggregateRoot[str]):
    """
    Domain entity for attributes.

    Attributes define characteristics of objects in the system.
    """

    attribute_type_id: str
    comment: Optional[str] = None
    follow_up_required: bool = False
    group_id: Optional[str] = None
    tenant_id: Optional[str] = None

    # Navigation properties (not persisted directly)
    attribute_type: Optional[AttributeType] = field(default=None, repr=False)
    value_ids: List[str] = field(default_factory=list, repr=False)
    meta_record_ids: List[str] = field(default_factory=list, repr=False)

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = "AttributeModel"

    def validate(self) -> None:
        """Validate the attribute."""
        if not self.attribute_type_id:
            raise ValidationError("Attribute type ID cannot be empty")

        # Check if comment is required but missing
        if (
            self.attribute_type
            and self.attribute_type.comment_required
            and not self.comment
        ):
            raise ValidationError("Comment is required for this attribute type")

    def add_value(self, value_id: str) -> None:
        """
        Add a value to this attribute.

        Args:
            value_id: The ID of the value to add
        """
        if value_id not in self.value_ids:
            # Check if multiple values are allowed
            if (
                self.attribute_type
                and not self.attribute_type.multiple_allowed
                and self.value_ids
            ):
                # Replace the existing value
                self.value_ids.clear()

            self.value_ids.append(value_id)

    def add_meta_record(self, meta_record_id: str) -> None:
        """
        Add a meta record to this attribute.

        Args:
            meta_record_id: The ID of the meta record to add
        """
        if meta_record_id not in self.meta_record_ids:
            self.meta_record_ids.append(meta_record_id)

    @property
    def has_values(self) -> bool:
        """Check if the attribute has any values."""
        return len(self.value_ids) > 0 or len(self.meta_record_ids) > 0
