"""
Tests for the specification translators module.
"""

import pytest
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, patch, MagicMock

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from uno.domain.specifications import (
    Specification, AttributeSpecification, AndSpecification,
    OrSpecification, NotSpecification, specification_factory
)
from uno.domain.specification_translators import (
    PostgreSQLSpecificationTranslator, 
    PostgreSQLRepository,
    AsyncPostgreSQLRepository
)
from uno.domain.models import Entity
from uno.model import UnoModel


# Mocked Entity for testing
class TestEntity(Entity):
    name: str
    age: int
    is_active: bool


# Mocked SQLAlchemy Model for testing
class TestModel(UnoModel):
    __tablename__ = "test_model"
    
    id = sa.Column(sa.String, primary_key=True)
    name = sa.Column(sa.String)
    age = sa.Column(sa.Integer)
    is_active = sa.Column(sa.Boolean)


# Create specification factory for TestEntity
TestEntitySpecification = specification_factory(TestEntity)


class TestPostgreSQLSpecificationTranslator:
    
    def setup_method(self):
        self.translator = PostgreSQLSpecificationTranslator(TestModel)
    
    def test_translate_attribute_specification(self):
        # Create attribute specification
        spec = AttributeSpecification("name", "test")
        
        # Translate specification
        query = self.translator.translate(spec)
        
        # Check SQL string representation (simplified test)
        sql_str = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "test_model" in sql_str
        assert "name" in sql_str
        assert "test" in sql_str
    
    def test_translate_and_specification(self):
        # Create AND specification
        spec1 = AttributeSpecification("name", "test")
        spec2 = AttributeSpecification("age", 25)
        and_spec = AndSpecification(spec1, spec2)
        
        # Translate specification
        query = self.translator.translate(and_spec)
        
        # Check SQL string representation (simplified test)
        sql_str = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "test_model" in sql_str
        assert "name" in sql_str
        assert "test" in sql_str
        assert "age" in sql_str
        assert "25" in sql_str
        assert "AND" in sql_str
    
    def test_translate_or_specification(self):
        # Create OR specification
        spec1 = AttributeSpecification("name", "test")
        spec2 = AttributeSpecification("age", 25)
        or_spec = OrSpecification(spec1, spec2)
        
        # Translate specification
        query = self.translator.translate(or_spec)
        
        # Check SQL string representation (simplified test)
        sql_str = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "test_model" in sql_str
        assert "name" in sql_str
        assert "test" in sql_str
        assert "age" in sql_str
        assert "25" in sql_str
        assert "OR" in sql_str
    
    def test_translate_not_specification(self):
        # Create NOT specification
        spec = AttributeSpecification("is_active", True)
        not_spec = NotSpecification(spec)
        
        # Translate specification
        query = self.translator.translate(not_spec)
        
        # Check SQL string representation (simplified test)
        sql_str = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "test_model" in sql_str
        assert "is_active" in sql_str
        assert "NOT" in sql_str
    
    def test_translate_complex_specification(self):
        # Create a complex specification
        spec1 = AttributeSpecification("name", "test")
        spec2 = AttributeSpecification("age", 25)
        spec3 = AttributeSpecification("is_active", True)
        
        # (name = 'test' OR age = 25) AND NOT is_active
        complex_spec = AndSpecification(
            OrSpecification(spec1, spec2),
            NotSpecification(spec3)
        )
        
        # Translate specification
        query = self.translator.translate(complex_spec)
        
        # Check SQL string representation (simplified test)
        sql_str = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "test_model" in sql_str
        assert "name" in sql_str
        assert "test" in sql_str
        assert "age" in sql_str
        assert "25" in sql_str
        assert "is_active" in sql_str
        assert "OR" in sql_str
        assert "AND" in sql_str
        assert "NOT" in sql_str


class TestPostgreSQLRepository:
    
    def setup_method(self):
        # Create mocked session factory
        self.session_mock = AsyncMock(spec=AsyncSession)
        self.session_mock.__aenter__.return_value = self.session_mock
        self.session_mock.__aexit__.return_value = None
        
        self.session_factory = MagicMock(return_value=self.session_mock)
        
        # Create repository
        self.repository = AsyncPostgreSQLRepository(
            TestEntity, TestModel, self.session_factory
        )
    
    @pytest.mark.asyncio
    async def test_find_by_specification(self):
        # Create attribute specification
        spec = AttributeSpecification("name", "test")
        
        # Mock models to return
        model1 = TestModel(id="1", name="test", age=30, is_active=True)
        model2 = TestModel(id="2", name="test", age=25, is_active=False)
        
        # Mock query execution
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [model1, model2]
        self.session_mock.execute.return_value = result_mock
        
        # Execute find_by_specification
        entities = await self.repository.find_by_specification(spec)
        
        # Check results
        assert len(entities) == 2
        assert isinstance(entities[0], TestEntity)
        assert entities[0].id == "1"
        assert entities[0].name == "test"
        assert entities[0].age == 30
        assert entities[0].is_active is True
        
        assert isinstance(entities[1], TestEntity)
        assert entities[1].id == "2"
        assert entities[1].name == "test"
        assert entities[1].age == 25
        assert entities[1].is_active is False
        
        # Verify session was used correctly
        self.session_factory.assert_called_once()
        self.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_by_specification(self):
        # Create attribute specification
        spec = AttributeSpecification("name", "test")
        
        # Mock count result
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 5
        self.session_mock.execute.return_value = result_mock
        
        # Execute count_by_specification
        count = await self.repository.count_by_specification(spec)
        
        # Check results
        assert count == 5
        
        # Verify session was used correctly
        self.session_factory.assert_called_once()
        self.session_mock.execute.assert_called_once()