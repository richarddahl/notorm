# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the repository code generator module.

These tests verify the functionality of the repository generation tools.
"""

import pytest
from unittest.mock import patch, MagicMock
import ast
import re

from uno.devtools.codegen.repository import (
    RepositoryGenerator,
    RepositoryDefinition,
    QueryMethod,
    BulkOperation,
    RepositoryGeneratorConfig,
)


class TestRepositoryGenerator:
    """Tests for the RepositoryGenerator class."""

    def test_generate_repository_basic(self):
        """Test generating a basic repository."""
        # Create a repository definition
        repo_def = RepositoryDefinition(
            name="UserRepository", model_name="User", table_name="users"
        )

        # Create a repository generator
        generator = RepositoryGenerator()

        # Generate the repository code
        repo_code = generator.generate_repository(repo_def)

        # Check the generated code
        assert "class UserRepository(UnoRepository):" in repo_code
        assert "model_class = User" in repo_code
        assert "def __init__(self, session: DbSession)" in repo_code
        assert "super().__init__(session)" in repo_code
        assert "def get_by_id(self, id: int)" in repo_code
        assert "def list_all(self)" in repo_code
        assert "def create(self, data: dict)" in repo_code
        assert "def update(self, id: int, data: dict)" in repo_code
        assert "def delete(self, id: int)" in repo_code

        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(repo_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

    def test_generate_repository_with_query_methods(self):
        """Test generating a repository with custom query methods."""
        # Create a repository definition with query methods
        repo_def = RepositoryDefinition(
            name="ProductRepository",
            model_name="Product",
            table_name="products",
            query_methods=[
                QueryMethod(
                    name="find_by_category",
                    parameters=[{"name": "category", "type": "str"}],
                    return_type="List[Product]",
                    query="return self.query.filter(self.model_class.category == category).all()",
                ),
                QueryMethod(
                    name="find_active_by_price_range",
                    parameters=[
                        {"name": "min_price", "type": "float"},
                        {"name": "max_price", "type": "float"},
                    ],
                    return_type="List[Product]",
                    query="return self.query.filter(\n"
                    + "    self.model_class.active == True,\n"
                    + "    self.model_class.price >= min_price,\n"
                    + "    self.model_class.price <= max_price\n"
                    + ").all()",
                ),
            ],
        )

        # Create a repository generator
        generator = RepositoryGenerator()

        # Generate the repository code
        repo_code = generator.generate_repository(repo_def)

        # Check the generated code
        assert "class ProductRepository(UnoRepository):" in repo_code
        assert (
            "def find_by_category(self, category: str) -> List[Product]:" in repo_code
        )
        assert (
            "return self.query.filter(self.model_class.category == category).all()"
            in repo_code
        )
        assert (
            "def find_active_by_price_range(self, min_price: float, max_price: float) -> List[Product]:"
            in repo_code
        )
        assert "self.model_class.price >= min_price" in repo_code
        assert "self.model_class.price <= max_price" in repo_code

        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(repo_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

    def test_generate_repository_with_bulk_operations(self):
        """Test generating a repository with bulk operations."""
        # Create a repository definition with bulk operations
        repo_def = RepositoryDefinition(
            name="OrderRepository",
            model_name="Order",
            table_name="orders",
            bulk_operations=[
                BulkOperation(
                    name="bulk_create",
                    operation_type="create",
                    parameter_name="orders",
                    parameter_type="List[Dict[str, Any]]",
                ),
                BulkOperation(
                    name="bulk_update",
                    operation_type="update",
                    parameter_name="order_updates",
                    parameter_type="List[Tuple[int, Dict[str, Any]]]",
                ),
            ],
        )

        # Create a repository generator
        generator = RepositoryGenerator()

        # Generate the repository code
        repo_code = generator.generate_repository(repo_def)

        # Check the generated code
        assert "class OrderRepository(UnoRepository):" in repo_code
        assert "def bulk_create(self, orders: List[Dict[str, Any]])" in repo_code
        assert (
            "def bulk_update(self, order_updates: List[Tuple[int, Dict[str, Any]]])"
            in repo_code
        )
        assert "for order_data in orders:" in repo_code
        assert "for order_id, update_data in order_updates:" in repo_code

        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(repo_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

    def test_generate_from_model(self):
        """Test generating a repository from a model class."""
        # Create a mock model class
        mock_model = MagicMock()
        mock_model.__name__ = "User"
        mock_model.__tablename__ = "users"

        # Mock the model fields
        mock_column = MagicMock()
        mock_column.primary_key = False
        mock_column.name = "name"
        mock_column.type.python_type = str

        mock_pk_column = MagicMock()
        mock_pk_column.primary_key = True
        mock_pk_column.name = "id"
        mock_pk_column.type.python_type = int

        # Mock model columns
        mock_model.__table__ = MagicMock()
        mock_model.__table__.columns = [mock_pk_column, mock_column]

        # Create a generator
        with patch("uno.devtools.codegen.repository.inspect") as mock_inspect:
            # Configure the mock inspect module
            mock_inspect.getmembers.return_value = []

            # Create a generator
            generator = RepositoryGenerator()

            # Generate repository from the model
            repo_code = generator.generate_from_model(mock_model)

            # Check the generated code
            assert "class UserRepository(UnoRepository):" in repo_code
            assert "model_class = User" in repo_code
            assert "def get_by_id(self, id: int)" in repo_code

            # Since we have a 'name' column, there should be a get_by_name method
            assert "def get_by_name(self, name: str)" in repo_code

    def test_generate_repository_with_async(self):
        """Test generating an async repository."""
        # Create a repository definition
        repo_def = RepositoryDefinition(
            name="UserRepository", model_name="User", table_name="users", is_async=True
        )

        # Create a repository generator
        generator = RepositoryGenerator()

        # Generate the repository code
        repo_code = generator.generate_repository(repo_def)

        # Check the generated code
        assert "class UserRepository(AsyncUnoRepository):" in repo_code
        assert "async def get_by_id(self, id: int)" in repo_code
        assert "async def list_all(self)" in repo_code
        assert "async def create(self, data: dict)" in repo_code
        assert "async def update(self, id: int, data: dict)" in repo_code
        assert "async def delete(self, id: int)" in repo_code

        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(repo_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")

    def test_formatting_options(self):
        """Test code formatting options."""
        # Create a simple repository definition
        repo_def = RepositoryDefinition(
            name="SimpleRepository",
            model_name="SimpleModel",
            table_name="simple_models",
        )

        # Create a generator with different formatting options
        config = RepositoryGeneratorConfig(
            include_imports=True, include_docstrings=True, include_type_annotations=True
        )
        generator = RepositoryGenerator(config=config)

        # Generate the repository code
        repo_code = generator.generate_repository(repo_def)

        # Check that the code includes imports
        assert "from typing import " in repo_code
        assert "from uno.dependencies.repository import UnoRepository" in repo_code

        # Check that the code includes docstrings
        assert '"""' in repo_code
        assert "Repository for SimpleModel entities" in repo_code

        # Check that the code includes type annotations
        assert "-> " in repo_code
