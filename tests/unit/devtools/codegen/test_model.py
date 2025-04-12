# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the model code generator module.

These tests verify the functionality of the model generation tools.
"""

import pytest
from unittest.mock import patch, MagicMock
import ast
import re

from uno.devtools.codegen.model import (
    ModelGenerator,
    ModelDefinition,
    FieldDefinition,
    RelationshipDefinition,
    RelationshipType,
    ModelGeneratorConfig
)


class TestModelGenerator:
    """Tests for the ModelGenerator class."""
    
    def test_generate_model_basic(self):
        """Test generating a basic model."""
        # Create a model definition
        model_def = ModelDefinition(
            name="User",
            table_name="users",
            fields=[
                FieldDefinition(name="id", field_type="int", primary_key=True),
                FieldDefinition(name="name", field_type="str", nullable=False),
                FieldDefinition(name="email", field_type="str", unique=True),
                FieldDefinition(name="active", field_type="bool", default=True)
            ]
        )
        
        # Create a model generator
        generator = ModelGenerator()
        
        # Generate the model code
        model_code = generator.generate_model(model_def)
        
        # Check the generated code
        assert "class User(UnoModel):" in model_code
        assert "__tablename__ = 'users'" in model_code
        assert "id = Column(Integer, primary_key=True)" in model_code
        assert "name = Column(String, nullable=False)" in model_code
        assert "email = Column(String, unique=True)" in model_code
        assert "active = Column(Boolean, default=True)" in model_code
        
        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(model_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_generate_model_with_relationships(self):
        """Test generating a model with relationships."""
        # Create a model definition with relationships
        model_def = ModelDefinition(
            name="Post",
            table_name="posts",
            fields=[
                FieldDefinition(name="id", field_type="int", primary_key=True),
                FieldDefinition(name="title", field_type="str"),
                FieldDefinition(name="content", field_type="str"),
                FieldDefinition(name="user_id", field_type="int", foreign_key="users.id")
            ],
            relationships=[
                RelationshipDefinition(
                    name="user",
                    target_model="User",
                    type=RelationshipType.MANY_TO_ONE,
                    foreign_key="user_id"
                ),
                RelationshipDefinition(
                    name="comments",
                    target_model="Comment",
                    type=RelationshipType.ONE_TO_MANY,
                    back_populates="post"
                )
            ]
        )
        
        # Create a model generator
        generator = ModelGenerator()
        
        # Generate the model code
        model_code = generator.generate_model(model_def)
        
        # Check the generated code
        assert "class Post(UnoModel):" in model_code
        assert "__tablename__ = 'posts'" in model_code
        assert "user_id = Column(Integer, ForeignKey('users.id'))" in model_code
        assert "user = relationship(\"User\"" in model_code
        assert "comments = relationship(\"Comment\"" in model_code
        assert "back_populates=\"post\"" in model_code
        
        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(model_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_generate_schema(self):
        """Test generating a Pydantic schema for a model."""
        # Create a model definition
        model_def = ModelDefinition(
            name="User",
            table_name="users",
            fields=[
                FieldDefinition(name="id", field_type="int", primary_key=True),
                FieldDefinition(name="name", field_type="str", nullable=False),
                FieldDefinition(name="email", field_type="str", unique=True),
                FieldDefinition(
                    name="password", 
                    field_type="str", 
                    exclude_from_schema=True
                )
            ]
        )
        
        # Create a model generator
        generator = ModelGenerator()
        
        # Generate the schema code
        schema_code = generator.generate_schema(model_def)
        
        # Check the generated code
        assert "class UserSchema(UnoSchema):" in schema_code
        assert "id: int" in schema_code
        assert "name: str" in schema_code
        assert "email: str" in schema_code
        assert "password: str" not in schema_code  # Should be excluded
        
        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(schema_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_generate_from_database(self):
        """Test generating models from database schema."""
        # Mock the database reflection
        reflected_tables = {
            "users": {
                "columns": {
                    "id": {"type": "INTEGER", "primary_key": True},
                    "name": {"type": "VARCHAR", "nullable": False},
                    "email": {"type": "VARCHAR", "unique": True},
                    "created_at": {"type": "TIMESTAMP", "default": "NOW()"}
                },
                "foreign_keys": [],
                "indexes": [
                    {"name": "users_email_idx", "columns": ["email"]}
                ]
            }
        }
        
        # Create a model generator with a mock database inspector
        with patch("uno.devtools.codegen.model.get_db_inspector") as mock_inspector:
            # Configure the mock inspector
            mock_inspector.return_value.get_table_names.return_value = ["users"]
            mock_inspector.return_value.get_columns.return_value = [
                {"name": "id", "type": "INTEGER", "primary_key": True},
                {"name": "name", "type": "VARCHAR", "nullable": False},
                {"name": "email", "type": "VARCHAR", "unique": True},
                {"name": "created_at", "type": "TIMESTAMP", "default": "NOW()"}
            ]
            mock_inspector.return_value.get_foreign_keys.return_value = []
            mock_inspector.return_value.get_indexes.return_value = [
                {"name": "users_email_idx", "column_names": ["email"]}
            ]
            
            # Create a generator
            generator = ModelGenerator()
            
            # Generate models from the database
            models = generator.generate_from_database(tables=["users"])
            
            # Check the generated models
            assert "users" in models
            user_model = models["users"]
            assert "class User(UnoModel):" in user_model
            assert "__tablename__ = 'users'" in user_model
            assert "id = Column(Integer, primary_key=True)" in user_model
            assert "name = Column(String, nullable=False)" in user_model
            assert "email = Column(String, unique=True)" in user_model
    
    def test_generate_with_validation(self):
        """Test generating a schema with validation rules."""
        # Create a model definition with validation
        model_def = ModelDefinition(
            name="Product",
            table_name="products",
            fields=[
                FieldDefinition(name="id", field_type="int", primary_key=True),
                FieldDefinition(
                    name="name", 
                    field_type="str", 
                    nullable=False,
                    validation={"min_length": 3, "max_length": 100}
                ),
                FieldDefinition(
                    name="price", 
                    field_type="float",
                    validation={"gt": 0}
                ),
                FieldDefinition(
                    name="category", 
                    field_type="str",
                    validation={"pattern": "^[A-Z][a-z]+$"}
                )
            ]
        )
        
        # Create a model generator
        generator = ModelGenerator()
        
        # Generate the schema code
        schema_code = generator.generate_schema(model_def)
        
        # Check the generated code includes validation
        assert "name: str = Field(" in schema_code
        assert "min_length=3" in schema_code
        assert "max_length=100" in schema_code
        assert "price: float = Field(" in schema_code
        assert "gt=0" in schema_code
        assert "category: str = Field(" in schema_code
        assert "pattern=" in schema_code
        
        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(schema_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_formatting_options(self):
        """Test code formatting options."""
        # Create a simple model definition
        model_def = ModelDefinition(
            name="SimpleModel",
            table_name="simple_models",
            fields=[
                FieldDefinition(name="id", field_type="int", primary_key=True),
                FieldDefinition(name="name", field_type="str")
            ]
        )
        
        # Create a generator with different formatting options
        config = ModelGeneratorConfig(
            include_imports=True,
            include_docstrings=True,
            include_type_annotations=True
        )
        generator = ModelGenerator(config=config)
        
        # Generate the model code
        model_code = generator.generate_model(model_def)
        
        # Check that the code includes imports
        assert "from sqlalchemy import Column" in model_code
        
        # Check that the code includes docstrings
        assert '"""' in model_code
        assert "SimpleModel model class" in model_code
        
        # Check that the code includes type annotations
        assert "# type: " in model_code or ": " in model_code