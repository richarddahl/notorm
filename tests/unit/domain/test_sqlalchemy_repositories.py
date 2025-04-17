"""
Tests for the SQLAlchemy repository implementations.
"""

import pytest
import os
from typing import Dict, Any, List, Optional, AsyncGenerator, cast
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeMeta

from uno.domain.models import Entity
from uno.domain.specifications import (
    Specification, AttributeSpecification, AndSpecification,
    OrSpecification, NotSpecification, specification_factory
)
from uno.domain.sqlalchemy_repositories import (
    SQLAlchemyRepository, SQLAlchemyUnitOfWork
)

# Test entity
class Product(Entity):
    name: str
    price: float
    category: str
    in_stock: bool = True
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: Optional[datetime] = None


# SQLAlchemy setup
Base = declarative_base()

class ProductModel(Base):
    __tablename__ = "products"
    
    id = sa.Column(sa.String, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    price = sa.Column(sa.Float, nullable=False)
    category = sa.Column(sa.String, nullable=False)
    in_stock = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

# Create specification factory for Product
ProductSpecification = specification_factory(Product)


class TestSQLAlchemyRepository:
    
    @pytest.fixture
    def session_factory(self):
        """Create a session factory with a mock session."""
        session_mock = AsyncMock(spec=AsyncSession)
        session_mock.__aenter__.return_value = session_mock
        session_mock.__aexit__.return_value = None
        
        def factory():
            return session_mock
        
        # Store session mock for assertions
        factory.session_mock = session_mock
        
        return factory
    
    @pytest.fixture
    def repository(self, session_factory):
        """Create a repository with the mock session factory."""
        return SQLAlchemyRepository(
            entity_type=Product,
            model_class=ProductModel,
            session_factory=session_factory
        )
    
    @pytest.mark.asyncio
    async def test_get(self, repository, session_factory):
        """Test getting an entity by ID."""
        # Mock model to return
        model = ProductModel(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Get entity by ID
        entity = await repository.get("1")
        
        # Verify entity
        assert entity is not None
        assert entity.id == "1"
        assert entity.name == "Widget A"
        assert entity.price == 19.99
        assert entity.category == "Tools"
        assert entity.in_stock is True
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_not_found(self, repository, session_factory):
        """Test getting a non-existent entity by ID."""
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = None
        session_factory.session_mock.execute.return_value = result_mock
        
        # Get entity by ID
        entity = await repository.get("999")
        
        # Verify entity is None
        assert entity is None
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find(self, repository, session_factory):
        """Test finding entities with a specification."""
        # Create specification
        spec = AttributeSpecification("category", "Tools")
        
        # Mock models to return
        models = [
            ProductModel(
                id="1", 
                name="Widget A", 
                price=19.99, 
                category="Tools", 
                in_stock=True,
                created_at=datetime.now(timezone.utc)
            ),
            ProductModel(
                id="2", 
                name="Widget B", 
                price=29.99, 
                category="Tools", 
                in_stock=True,
                created_at=datetime.now(timezone.utc)
            ),
        ]
        
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = models
        session_factory.session_mock.execute.return_value = result_mock
        
        # Find entities
        entities = await repository.find(spec)
        
        # Verify entities
        assert len(entities) == 2
        assert all(isinstance(e, Product) for e in entities)
        assert entities[0].name == "Widget A"
        assert entities[1].name == "Widget B"
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_one(self, repository, session_factory):
        """Test finding one entity with a specification."""
        # Create specification
        spec = AttributeSpecification("name", "Widget A")
        
        # Mock model to return
        model = ProductModel(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Find one entity
        entity = await repository.find_one(spec)
        
        # Verify entity
        assert entity is not None
        assert entity.id == "1"
        assert entity.name == "Widget A"
        assert entity.price == 19.99
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count(self, repository, session_factory):
        """Test counting entities with a specification."""
        # Create specification
        spec = AttributeSpecification("category", "Tools")
        
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 3
        session_factory.session_mock.execute.return_value = result_mock
        
        # Count entities
        count = await repository.count(spec)
        
        # Verify count
        assert count == 3
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exists(self, repository, session_factory):
        """Test checking if entities exist with a specification."""
        # Create specification
        spec = AttributeSpecification("category", "Tools")
        
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 3  # Count > 0, so exists is True
        session_factory.session_mock.execute.return_value = result_mock
        
        # Check if entities exist
        exists = await repository.exists(spec)
        
        # Verify exists
        assert exists is True
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add(self, repository, session_factory):
        """Test adding an entity."""
        # Create entity to add
        entity = Product(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Add entity
        await repository.add(entity)
        
        # Verify session was used correctly
        session_factory.session_mock.add.assert_called_once()
        session_factory.session_mock.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update(self, repository, session_factory):
        """Test updating an entity."""
        # Create entity to update
        entity = Product(
            id="1",
            name="Widget A Updated",
            price=24.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Mock model to return
        model = ProductModel(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Update entity
        await repository.update(entity)
        
        # Verify model was updated
        assert model.name == "Widget A Updated"
        assert model.price == 24.99
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
        session_factory.session_mock.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove(self, repository, session_factory):
        """Test removing an entity."""
        # Create entity to remove
        entity = Product(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock model to return
        model = ProductModel(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock session execute result
        result_mock = MagicMock()
        result_mock.scalars.return_value.first.return_value = model
        session_factory.session_mock.execute.return_value = result_mock
        
        # Remove entity
        await repository.remove(entity)
        
        # Verify session was used correctly
        session_factory.session_mock.execute.assert_called_once()
        session_factory.session_mock.delete.assert_called_once_with(model)
        session_factory.session_mock.commit.assert_called_once()


class TestSQLAlchemyUnitOfWork:
    
    @pytest.fixture
    def session_factory(self):
        """Create a session factory with a mock session."""
        session_mock = AsyncMock(spec=AsyncSession)
        session_mock.__aenter__.return_value = session_mock
        session_mock.__aexit__.return_value = None
        
        def factory():
            return session_mock
        
        # Store session mock for assertions
        factory.session_mock = session_mock
        
        return factory
    
    @pytest.fixture
    def repository_factory(self, session_factory):
        """Create a factory for repositories."""
        def factory(entity_type, model_class):
            return SQLAlchemyRepository(
                entity_type=entity_type,
                model_class=model_class,
                session_factory=session_factory
            )
        
        return factory
    
    @pytest.fixture
    def unit_of_work(self, session_factory, repository_factory):
        """Create a unit of work with repositories."""
        # Create repositories
        repositories = {
            Product: repository_factory(Product, ProductModel)
        }
        
        # Create unit of work
        uow = SQLAlchemyUnitOfWork(
            session_factory=session_factory,
            repositories=repositories
        )
        
        return uow
    
    @pytest.mark.asyncio
    async def test_commit(self, unit_of_work, session_factory):
        """Test committing changes in the unit of work."""
        # Create entities
        entity1 = Product(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        entity2 = Product(
            id="2",
            name="Widget B",
            price=29.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Mock models
        model1 = ProductModel(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        model2 = ProductModel(
            id="2",
            name="Widget B",
            price=29.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Use the unit of work
        async with unit_of_work:
            # Register entities
            await unit_of_work.register_new(entity1)
            await unit_of_work.register_dirty(entity2)
            
            # Directly call commit to test
            await unit_of_work.commit()
        
        # Verify session was used correctly
        session_factory.session_mock.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback(self, unit_of_work, session_factory):
        """Test rolling back changes in the unit of work."""
        # Create entities
        entity1 = Product(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Use the unit of work with an exception
        try:
            async with unit_of_work:
                # Register entities
                await unit_of_work.register_new(entity1)
                
                # Raise an exception to trigger rollback
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Verify session was used correctly
        session_factory.session_mock.rollback.assert_called_once()
        session_factory.session_mock.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_flush(self, unit_of_work, session_factory):
        """Test flushing changes in the unit of work."""
        # Create entities
        entity1 = Product(
            id="1",
            name="Widget A",
            price=19.99,
            category="Tools",
            in_stock=True,
            created_at=datetime.now(timezone.utc)
        )
        
        # Use the unit of work
        async with unit_of_work:
            # Register entities
            await unit_of_work.register_new(entity1)
            
            # Flush changes
            await unit_of_work.flush()
        
        # Verify session was used correctly
        session_factory.session_mock.flush.assert_called_once()
        session_factory.session_mock.commit.assert_called_once()