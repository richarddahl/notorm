"""
Data models for the Uno visual modeler.

This module defines the data models used for representing database entities
and relationships in the visual modeler.
"""

from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Field:
    """Represents a field in an entity."""

    name: str
    type: str
    nullable: bool = False
    primary_key: bool = False
    foreign_key: str | None = None
    default: Optional[Any] = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    """Represents an entity in the data model."""

    name: str
    table_name: str | None = None
    fields: list[Field] = field(default_factory=list)
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def primary_key_fields(self) -> list[Field]:
        """Get the primary key fields for this entity."""
        return [field for field in self.fields if field.primary_key]


@dataclass
class Relationship:
    """Represents a relationship between entities."""

    source_entity: str
    target_entity: str
    source_field: str
    target_field: str
    relationship_type: str  # one-to-one, one-to-many, many-to-many
    nullable: bool = False
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class RelationshipType(str, Enum):
    """Types of relationships between entities."""

    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_ONE = "many-to-one"
    MANY_TO_MANY = "many-to-many"


class ModelType(str, Enum):
    """Types of models to analyze."""

    ENTITY = "entity"
    REPOSITORY = "repository"
    SERVICE = "service"
    ALL = "all"


@dataclass
class Model:
    """Represents a complete data model."""

    name: str
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "entities": [self._entity_to_dict(entity) for entity in self.entities],
            "relationships": [
                self._relationship_to_dict(rel) for rel in self.relationships
            ],
            "metadata": self.metadata,
        }

    def _entity_to_dict(self, entity: Entity) -> dict[str, Any]:
        """Convert an entity to a dictionary."""
        return {
            "name": entity.name,
            "table_name": entity.table_name,
            "fields": [self._field_to_dict(field) for field in entity.fields],
            "description": entity.description,
            "metadata": entity.metadata,
        }

    def _field_to_dict(self, field: Field) -> dict[str, Any]:
        """Convert a field to a dictionary."""
        return {
            "name": field.name,
            "type": field.type,
            "nullable": field.nullable,
            "primary_key": field.primary_key,
            "foreign_key": field.foreign_key,
            "default": field.default,
            "description": field.description,
            "metadata": field.metadata,
        }

    def _relationship_to_dict(self, relationship: Relationship) -> dict[str, Any]:
        """Convert a relationship to a dictionary."""
        return {
            "source_entity": relationship.source_entity,
            "target_entity": relationship.target_entity,
            "source_field": relationship.source_field,
            "target_field": relationship.target_field,
            "relationship_type": relationship.relationship_type,
            "nullable": relationship.nullable,
            "name": relationship.name,
            "description": relationship.description,
            "metadata": relationship.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Model":
        """Create a model from a dictionary."""
        entities = []
        for entity_data in data.get("entities", []):
            fields = []
            for field_data in entity_data.get("fields", []):
                fields.append(
                    Field(
                        name=field_data["name"],
                        type=field_data["type"],
                        nullable=field_data.get("nullable", False),
                        primary_key=field_data.get("primary_key", False),
                        foreign_key=field_data.get("foreign_key"),
                        default=field_data.get("default"),
                        description=field_data.get("description"),
                        metadata=field_data.get("metadata", {}),
                    )
                )

            entities.append(
                Entity(
                    name=entity_data["name"],
                    table_name=entity_data.get("table_name"),
                    fields=fields,
                    description=entity_data.get("description"),
                    metadata=entity_data.get("metadata", {}),
                )
            )

        relationships = []
        for rel_data in data.get("relationships", []):
            relationships.append(
                Relationship(
                    source_entity=rel_data["source_entity"],
                    target_entity=rel_data["target_entity"],
                    source_field=rel_data["source_field"],
                    target_field=rel_data["target_field"],
                    relationship_type=rel_data["relationship_type"],
                    nullable=rel_data.get("nullable", False),
                    name=rel_data.get("name"),
                    description=rel_data.get("description"),
                    metadata=rel_data.get("metadata", {}),
                )
            )

        return cls(
            name=data["name"],
            entities=entities,
            relationships=relationships,
            description=data.get("description"),
            metadata=data.get("metadata", {}),
        )
