"""
Integration tests for specification translators.
"""

import pytest
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from uno.domain.models import Entity
from uno.domain.specifications import (
    Specification, AttributeSpecification, AndSpecification,
    OrSpecification, NotSpecification, specification_factory
)
from uno.domain.specification_translators import (
    PostgreSQLSpecificationTranslator, AsyncPostgreSQLRepository
)

# Test entity
class Product(Entity):
    name: str
    price: float
    category: str
    in_stock: bool
    created_at: datetime

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

# Test database URL - use SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    """Create a test database and session."""
    # Create async engine
    engine = create_async_engine(DATABASE_URL)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    
    # Create a session
    async with async_session() as session:
        # Insert test data
        products = [
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
            ProductModel(
                id="3", 
                name="Gadget X", 
                price=49.99, 
                category="Electronics", 
                in_stock=True,
                created_at=datetime.now(timezone.utc)
            ),
            ProductModel(
                id="4", 
                name="Gadget Y", 
                price=59.99, 
                category="Electronics", 
                in_stock=False,
                created_at=datetime.now(timezone.utc)
            ),
            ProductModel(
                id="5", 
                name="Tool Z", 
                price=39.99, 
                category="Tools", 
                in_stock=False,
                created_at=datetime.now(timezone.utc)
            ),
        ]
        
        session.add_all(products)
        await session.commit()
        
        yield session
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
def session_factory(db_session):
    """Create a session factory that returns the db_session."""
    async def _session_factory():
        return db_session
    
    return _session_factory

@pytest.mark.asyncio
async def test_postgresql_specification_translator(db_session, session_factory):
    """Test the PostgreSQL specification translator with SQLAlchemy."""
    # Create translator
    translator = PostgreSQLSpecificationTranslator(ProductModel)
    
    # Create simple specification - all Tools category products
    tools_spec = AttributeSpecification("category", "Tools")
    
    # Translate specification
    query = translator.translate(tools_spec)
    
    # Execute query
    result = await db_session.execute(query)
    products = result.scalars().all()
    
    # Check results
    assert len(products) == 3
    assert all(p.category == "Tools" for p in products)
    
    # Create complex specification - in-stock Electronics products
    electronics_in_stock_spec = AndSpecification(
        AttributeSpecification("category", "Electronics"),
        AttributeSpecification("in_stock", True)
    )
    
    # Translate specification
    query = translator.translate(electronics_in_stock_spec)
    
    # Execute query
    result = await db_session.execute(query)
    products = result.scalars().all()
    
    # Check results
    assert len(products) == 1
    assert products[0].category == "Electronics"
    assert products[0].in_stock is True
    assert products[0].name == "Gadget X"
    
    # Create NOT specification - non-Tools products
    not_tools_spec = NotSpecification(AttributeSpecification("category", "Tools"))
    
    # Translate specification
    query = translator.translate(not_tools_spec)
    
    # Execute query
    result = await db_session.execute(query)
    products = result.scalars().all()
    
    # Check results
    assert len(products) == 2
    assert all(p.category == "Electronics" for p in products)

@pytest.mark.asyncio
async def test_async_postgresql_repository(session_factory):
    """Test the AsyncPostgreSQLRepository implementation."""
    # Create repository
    repository = AsyncPostgreSQLRepository(
        entity_type=Product,
        model_class=ProductModel,
        session_factory=session_factory
    )
    
    # Create specification for all in-stock products
    in_stock_spec = AttributeSpecification("in_stock", True)
    
    # Find products
    products = await repository.find_by_specification(in_stock_spec)
    
    # Check results
    assert len(products) == 3
    assert all(isinstance(p, Product) for p in products)
    assert all(p.in_stock is True for p in products)
    
    # Count products
    count = await repository.count_by_specification(in_stock_spec)
    assert count == 3
    
    # Create complex specification - expensive Tools
    expensive_tools_spec = AndSpecification(
        AttributeSpecification("category", "Tools"),
        AttributeSpecification("price", 29.99)  # Exact price match
    )
    
    # Find products
    products = await repository.find_by_specification(expensive_tools_spec)
    
    # Check results
    assert len(products) == 1
    assert products[0].name == "Widget B"
    assert products[0].category == "Tools"
    assert products[0].price == 29.99