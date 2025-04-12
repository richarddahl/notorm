"""Schema definitions for the offline store.

This module provides classes for defining the structure of collections
in the offline store.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union


@dataclass
class IndexDefinition:
    """Definition of an index on a collection.
    
    Attributes:
        name: The name of the index.
        key_path: The field or fields to index.
        unique: Whether the index values must be unique.
        multi_entry: Whether to create an entry for each array element.
    """
    
    name: str
    key_path: Union[str, List[str]]
    unique: bool = False
    multi_entry: bool = False


@dataclass
class RelationshipDefinition:
    """Definition of a relationship between collections.
    
    Attributes:
        name: The name of the relationship.
        collection: The related collection.
        type: The type of relationship.
        foreign_key: The foreign key field.
        local_key: The local key field (defaults to primary key).
    """
    
    name: str
    collection: str
    type: str  # "one-to-one", "one-to-many", "many-to-one", "many-to-many"
    foreign_key: str
    local_key: Optional[str] = None
    
    def __post_init__(self):
        """Validate relationship definition."""
        valid_types = ["one-to-one", "one-to-many", "many-to-one", "many-to-many"]
        if self.type not in valid_types:
            raise ValueError(f"Invalid relationship type: {self.type}. "
                           f"Valid options are: {', '.join(valid_types)}")


@dataclass
class CollectionSchema:
    """Schema definition for a collection.
    
    Attributes:
        name: The name of the collection.
        key_path: The primary key field or fields.
        indexes: List of index definitions.
        relationships: List of relationship definitions.
        versioned: Whether to track version history for records.
        constraints: Additional constraints for the collection.
        encryption: Whether to encrypt this collection.
        sensitive_fields: Fields to encrypt if collection encryption is enabled.
    """
    
    name: str
    key_path: Union[str, List[str]]
    indexes: List[IndexDefinition] = field(default_factory=list)
    relationships: List[RelationshipDefinition] = field(default_factory=list)
    versioned: bool = False
    constraints: Dict[str, Any] = field(default_factory=dict)
    encryption: bool = False
    sensitive_fields: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the schema and set up indexes for the key path."""
        # If key_path is not already indexed, add an implicit index for it
        key_path_indexed = False
        
        for index in self.indexes:
            if index.key_path == self.key_path:
                key_path_indexed = True
                break
        
        if not key_path_indexed:
            # Add an implicit index for the key path
            index_name = f"{self.name}_key_idx"
            if isinstance(self.key_path, list):
                index_name = f"{self.name}_compound_key_idx"
            
            self.indexes.append(IndexDefinition(
                name=index_name,
                key_path=self.key_path,
                unique=True
            ))
            
        # Validate relationship definitions
        for relationship in self.relationships:
            # Check that local_key is either null or matches key_path
            if relationship.local_key is not None:
                if isinstance(self.key_path, str) and relationship.local_key != self.key_path:
                    raise ValueError(f"Relationship {relationship.name} local_key {relationship.local_key} "
                                   f"does not match collection key_path {self.key_path}")
                elif isinstance(self.key_path, list) and relationship.local_key not in self.key_path:
                    raise ValueError(f"Relationship {relationship.name} local_key {relationship.local_key} "
                                   f"is not part of collection key_path {self.key_path}")
                
    def get_key_name(self) -> str:
        """Get the name of the primary key field.
        
        Returns:
            The name of the primary key field, or the first field in a compound key.
            
        Raises:
            ValueError: If the key path is an empty list.
        """
        if isinstance(self.key_path, str):
            return self.key_path
        elif isinstance(self.key_path, list) and len(self.key_path) > 0:
            return self.key_path[0]
        else:
            raise ValueError(f"Invalid key path for collection {self.name}")
    
    def add_index(self, index: IndexDefinition) -> None:
        """Add an index to the schema.
        
        Args:
            index: The index definition to add.
            
        Raises:
            ValueError: If an index with the same name already exists.
        """
        for existing_index in self.indexes:
            if existing_index.name == index.name:
                raise ValueError(f"Index {index.name} already exists in collection {self.name}")
        
        self.indexes.append(index)
    
    def add_relationship(self, relationship: RelationshipDefinition) -> None:
        """Add a relationship to the schema.
        
        Args:
            relationship: The relationship definition to add.
            
        Raises:
            ValueError: If a relationship with the same name already exists.
        """
        for existing_rel in self.relationships:
            if existing_rel.name == relationship.name:
                raise ValueError(f"Relationship {relationship.name} already exists in collection {self.name}")
        
        self.relationships.append(relationship)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema to a dictionary.
        
        Returns:
            A dictionary representation of the schema.
        """
        return {
            "name": self.name,
            "key_path": self.key_path,
            "indexes": [
                {
                    "name": idx.name,
                    "key_path": idx.key_path,
                    "unique": idx.unique,
                    "multi_entry": idx.multi_entry
                }
                for idx in self.indexes
            ],
            "relationships": [
                {
                    "name": rel.name,
                    "collection": rel.collection,
                    "type": rel.type,
                    "foreign_key": rel.foreign_key,
                    "local_key": rel.local_key
                }
                for rel in self.relationships
            ],
            "versioned": self.versioned,
            "constraints": self.constraints,
            "encryption": self.encryption,
            "sensitive_fields": self.sensitive_fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionSchema':
        """Create a schema from a dictionary.
        
        Args:
            data: The schema data.
            
        Returns:
            A CollectionSchema instance.
        """
        indexes = [
            IndexDefinition(
                name=idx["name"],
                key_path=idx["key_path"],
                unique=idx.get("unique", False),
                multi_entry=idx.get("multi_entry", False)
            )
            for idx in data.get("indexes", [])
        ]
        
        relationships = [
            RelationshipDefinition(
                name=rel["name"],
                collection=rel["collection"],
                type=rel["type"],
                foreign_key=rel["foreign_key"],
                local_key=rel.get("local_key")
            )
            for rel in data.get("relationships", [])
        ]
        
        return cls(
            name=data["name"],
            key_path=data["key_path"],
            indexes=indexes,
            relationships=relationships,
            versioned=data.get("versioned", False),
            constraints=data.get("constraints", {}),
            encryption=data.get("encryption", False),
            sensitive_fields=data.get("sensitive_fields", [])
        )