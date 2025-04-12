# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the API code generator module.

These tests verify the functionality of the API endpoint generation tools.
"""

import pytest
from unittest.mock import patch, MagicMock
import ast
import re

from uno.devtools.codegen.api import (
    ApiGenerator,
    ApiDefinition,
    EndpointDefinition,
    EndpointType,
    ApiGeneratorConfig
)


class TestApiGenerator:
    """Tests for the ApiGenerator class."""
    
    def test_generate_api_basic(self):
        """Test generating basic API endpoints."""
        # Create an API definition
        api_def = ApiDefinition(
            name="UserApi",
            model_name="User",
            schema_name="UserSchema",
            repository_name="UserRepository",
            route_prefix="/users",
            endpoints=[
                EndpointDefinition(type=EndpointType.GET_ALL),
                EndpointDefinition(type=EndpointType.GET_BY_ID),
                EndpointDefinition(type=EndpointType.CREATE),
                EndpointDefinition(type=EndpointType.UPDATE),
                EndpointDefinition(type=EndpointType.DELETE)
            ]
        )
        
        # Create an API generator
        generator = ApiGenerator()
        
        # Generate the API code
        api_code = generator.generate_api(api_def)
        
        # Check the generated code
        assert "class UserApi:" in api_code
        assert "def __init__(self, repository: UserRepository)" in api_code
        assert "@router.get(\"/\"" in api_code
        assert "@router.get(\"/{id}\"" in api_code
        assert "@router.post(\"/\"" in api_code
        assert "@router.put(\"/{id}\"" in api_code
        assert "@router.delete(\"/{id}\"" in api_code
        
        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(api_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_generate_api_with_filtering(self):
        """Test generating API endpoints with filtering."""
        # Create an API definition with filtering
        api_def = ApiDefinition(
            name="ProductApi",
            model_name="Product",
            schema_name="ProductSchema",
            repository_name="ProductRepository",
            route_prefix="/products",
            endpoints=[
                EndpointDefinition(
                    type=EndpointType.GET_ALL,
                    include_filtering=True,
                    filter_fields=["category", "price"]
                )
            ]
        )
        
        # Create an API generator
        generator = ApiGenerator()
        
        # Generate the API code
        api_code = generator.generate_api(api_def)
        
        # Check the generated code
        assert "class ProductApi:" in api_code
        assert "@router.get(\"/\"" in api_code
        assert "def get_all" in api_code
        assert "category: Optional[str] = None" in api_code
        assert "price: Optional[float] = None" in api_code
        assert "filters = {}" in api_code
        assert "if category is not None:" in api_code
        assert "if price is not None:" in api_code
        
        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(api_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_generate_api_with_pagination(self):
        """Test generating API endpoints with pagination."""
        # Create an API definition with pagination
        api_def = ApiDefinition(
            name="OrderApi",
            model_name="Order",
            schema_name="OrderSchema",
            repository_name="OrderRepository",
            route_prefix="/orders",
            endpoints=[
                EndpointDefinition(
                    type=EndpointType.GET_ALL,
                    include_pagination=True
                )
            ]
        )
        
        # Create an API generator
        generator = ApiGenerator()
        
        # Generate the API code
        api_code = generator.generate_api(api_def)
        
        # Check the generated code
        assert "class OrderApi:" in api_code
        assert "@router.get(\"/\"" in api_code
        assert "def get_all" in api_code
        assert "skip: int = 0" in api_code
        assert "limit: int = 100" in api_code
        assert "total =" in api_code
        assert "items =" in api_code
        assert "return {" in api_code
        assert "\"items\":" in api_code
        assert "\"total\":" in api_code
        assert "\"skip\":" in api_code
        assert "\"limit\":" in api_code
        
        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(api_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_generate_api_with_validation(self):
        """Test generating API endpoints with validation."""
        # Create an API definition with validation
        api_def = ApiDefinition(
            name="UserApi",
            model_name="User",
            schema_name="UserSchema",
            repository_name="UserRepository",
            route_prefix="/users",
            endpoints=[
                EndpointDefinition(
                    type=EndpointType.CREATE,
                    include_validation=True
                ),
                EndpointDefinition(
                    type=EndpointType.UPDATE,
                    include_validation=True
                )
            ]
        )
        
        # Create an API generator
        generator = ApiGenerator()
        
        # Generate the API code
        api_code = generator.generate_api(api_def)
        
        # Check the generated code
        assert "class UserApi:" in api_code
        assert "@router.post(\"/\"" in api_code
        assert "def create" in api_code
        assert "user_data: UserSchema" in api_code
        assert "try:" in api_code
        assert "except ValidationError as e:" in api_code
        assert "raise HTTPException(status_code=400, detail=str(e))" in api_code
        
        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(api_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_generate_api_async(self):
        """Test generating async API endpoints."""
        # Create an API definition with async endpoints
        api_def = ApiDefinition(
            name="UserApi",
            model_name="User",
            schema_name="UserSchema",
            repository_name="UserRepository",
            route_prefix="/users",
            is_async=True,
            endpoints=[
                EndpointDefinition(type=EndpointType.GET_ALL),
                EndpointDefinition(type=EndpointType.GET_BY_ID),
                EndpointDefinition(type=EndpointType.CREATE)
            ]
        )
        
        # Create an API generator
        generator = ApiGenerator()
        
        # Generate the API code
        api_code = generator.generate_api(api_def)
        
        # Check the generated code
        assert "class UserApi:" in api_code
        assert "async def get_all" in api_code
        assert "async def get_by_id" in api_code
        assert "async def create" in api_code
        assert "await self.repository" in api_code
        
        # Try to parse the generated code to ensure it's valid Python
        try:
            ast.parse(api_code)
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
    
    def test_generate_from_model_and_schema(self):
        """Test generating an API from a model and schema."""
        # Create mock model and schema classes
        mock_model = MagicMock()
        mock_model.__name__ = "User"
        
        mock_schema = MagicMock()
        mock_schema.__name__ = "UserSchema"
        
        # Create a mock repository class
        mock_repository = MagicMock()
        mock_repository.__name__ = "UserRepository"
        
        # Create a generator
        generator = ApiGenerator()
        
        # Generate API from the model and schema
        api_code = generator.generate_from_model_schema(
            mock_model, 
            mock_schema, 
            mock_repository,
            route_prefix="/users"
        )
        
        # Check the generated code
        assert "class UserApi:" in api_code
        assert "def __init__(self, repository: UserRepository)" in api_code
        assert "@router.get(\"/\"" in api_code
        assert "@router.get(\"/{id}\"" in api_code
        assert "@router.post(\"/\"" in api_code
        assert "@router.put(\"/{id}\"" in api_code
        assert "@router.delete(\"/{id}\"" in api_code
    
    def test_formatting_options(self):
        """Test code formatting options."""
        # Create a simple API definition
        api_def = ApiDefinition(
            name="SimpleApi",
            model_name="SimpleModel",
            schema_name="SimpleSchema",
            repository_name="SimpleRepository",
            route_prefix="/simple",
            endpoints=[
                EndpointDefinition(type=EndpointType.GET_ALL),
                EndpointDefinition(type=EndpointType.GET_BY_ID)
            ]
        )
        
        # Create a generator with different formatting options
        config = ApiGeneratorConfig(
            include_imports=True,
            include_docstrings=True,
            include_error_handling=True,
            include_response_models=True
        )
        generator = ApiGenerator(config=config)
        
        # Generate the API code
        api_code = generator.generate_api(api_def)
        
        # Check that the code includes imports
        assert "from fastapi import " in api_code
        assert "from typing import " in api_code
        
        # Check that the code includes docstrings
        assert '"""' in api_code
        assert "API endpoints for SimpleModel" in api_code
        
        # Check that the code includes error handling
        assert "try:" in api_code
        assert "except " in api_code
        assert "HTTPException" in api_code
        
        # Check that the code includes response models
        assert "response_model=" in api_code