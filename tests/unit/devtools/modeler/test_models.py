"""
Tests for the modeler module models.
"""

import pytest
from uno.devtools.modeler.models import Field, Entity, Relationship, Model, RelationshipType

class TestField:
    """Tests for the Field class."""
    
    def test_field_creation(self):
        """Test creating a field with various attributes."""
        # Basic field
        field = Field(name="test_field", type="string")
        assert field.name == "test_field"
        assert field.type == "string"
        assert field.nullable is False
        assert field.primary_key is False
        assert field.foreign_key is None
        assert field.default is None
        assert field.description is None
        assert field.metadata == {}
        
        # Field with all attributes
        field = Field(
            name="id",
            type="uuid",
            nullable=False,
            primary_key=True,
            foreign_key="other_table.id",
            default="uuid_generate_v4()",
            description="Primary key field",
            metadata={"index": True}
        )
        assert field.name == "id"
        assert field.type == "uuid"
        assert field.nullable is False
        assert field.primary_key is True
        assert field.foreign_key == "other_table.id"
        assert field.default == "uuid_generate_v4()"
        assert field.description == "Primary key field"
        assert field.metadata == {"index": True}


class TestEntity:
    """Tests for the Entity class."""
    
    def test_entity_creation(self):
        """Test creating an entity with fields."""
        # Create an entity with fields
        fields = [
            Field(name="id", type="uuid", primary_key=True),
            Field(name="name", type="string", nullable=False),
            Field(name="description", type="text", nullable=True)
        ]
        
        entity = Entity(
            name="Product",
            table_name="products",
            fields=fields,
            description="Product entity",
            metadata={"versioned": True}
        )
        
        assert entity.name == "Product"
        assert entity.table_name == "products"
        assert len(entity.fields) == 3
        assert entity.description == "Product entity"
        assert entity.metadata == {"versioned": True}
    
    def test_primary_key_fields(self):
        """Test getting primary key fields."""
        fields = [
            Field(name="id", type="uuid", primary_key=True),
            Field(name="name", type="string", nullable=False),
            Field(name="tenant_id", type="uuid", primary_key=True)  # Composite key
        ]
        
        entity = Entity(name="Product", fields=fields)
        
        # Test primary_key_fields property
        pk_fields = entity.primary_key_fields
        assert len(pk_fields) == 2
        assert pk_fields[0].name == "id"
        assert pk_fields[1].name == "tenant_id"


class TestRelationship:
    """Tests for the Relationship class."""
    
    def test_relationship_creation(self):
        """Test creating relationships between entities."""
        relationship = Relationship(
            source_entity="Product",
            target_entity="Category",
            source_field="category_id",
            target_field="id",
            relationship_type=RelationshipType.MANY_TO_ONE,
            nullable=True,
            name="product_category",
            description="Product belongs to a category",
            metadata={"on_delete": "CASCADE"}
        )
        
        assert relationship.source_entity == "Product"
        assert relationship.target_entity == "Category"
        assert relationship.source_field == "category_id"
        assert relationship.target_field == "id"
        assert relationship.relationship_type == RelationshipType.MANY_TO_ONE
        assert relationship.nullable is True
        assert relationship.name == "product_category"
        assert relationship.description == "Product belongs to a category"
        assert relationship.metadata == {"on_delete": "CASCADE"}


class TestModel:
    """Tests for the Model class."""
    
    def test_model_creation(self):
        """Test creating a complete model with entities and relationships."""
        # Create entities
        product_entity = Entity(
            name="Product",
            table_name="products",
            fields=[
                Field(name="id", type="uuid", primary_key=True),
                Field(name="name", type="string"),
                Field(name="category_id", type="uuid")
            ]
        )
        
        category_entity = Entity(
            name="Category",
            table_name="categories",
            fields=[
                Field(name="id", type="uuid", primary_key=True),
                Field(name="name", type="string")
            ]
        )
        
        # Create relationship
        relationship = Relationship(
            source_entity="Product",
            target_entity="Category",
            source_field="category_id",
            target_field="id",
            relationship_type=RelationshipType.MANY_TO_ONE
        )
        
        # Create model
        model = Model(
            name="Ecommerce",
            entities=[product_entity, category_entity],
            relationships=[relationship],
            description="Ecommerce data model",
            metadata={"version": "1.0"}
        )
        
        assert model.name == "Ecommerce"
        assert len(model.entities) == 2
        assert len(model.relationships) == 1
        assert model.description == "Ecommerce data model"
        assert model.metadata == {"version": "1.0"}
    
    def test_model_serialization(self):
        """Test model serialization to and from dictionary."""
        # Create a simple model
        entity = Entity(
            name="User",
            fields=[
                Field(name="id", type="uuid", primary_key=True),
                Field(name="username", type="string", nullable=False)
            ]
        )
        
        model = Model(name="Auth", entities=[entity])
        
        # Convert to dictionary
        model_dict = model.to_dict()
        
        # Check dictionary structure
        assert model_dict["name"] == "Auth"
        assert len(model_dict["entities"]) == 1
        assert model_dict["entities"][0]["name"] == "User"
        assert len(model_dict["entities"][0]["fields"]) == 2
        
        # Convert back to model
        reconstructed_model = Model.from_dict(model_dict)
        assert reconstructed_model.name == model.name
        assert len(reconstructed_model.entities) == len(model.entities)
        assert reconstructed_model.entities[0].name == model.entities[0].name