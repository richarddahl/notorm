"""
Integration tests for SQLAlchemy repository implementation.
"""

import pytest
from typing import AsyncGenerator, List, Optional
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from uno.domain.models import Entity
from uno.domain.specifications import (
    AttributeSpecification, AndSpecification, 
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

# Test database URL
DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(DATABASE_URL)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create session factory
    async_session_maker = sessionmaker(
        db_engine, expire_on_commit=False, class_=AsyncSession
    )
    
    # Create a session
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def session_factory(db_session):
    """Create a session factory that returns the db_session."""
    async def _session_factory():
        return db_session
    
    return _session_factory


@pytest.fixture
async def product_repository(session_factory):
    """Create a repository for Product entities."""
    repository = SQLAlchemyRepository(
        entity_type=Product,
        model_class=ProductModel,
        session_factory=session_factory
    )
    
    return repository


@pytest.fixture
async def sample_products(db_session):
    """Create sample products in the database."""
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
    
    db_session.add_all(products)
    await db_session.commit()
    
    return products


@pytest.fixture
async def unit_of_work(session_factory, product_repository):
    """Create a unit of work with repositories."""
    # Create unit of work
    uow = SQLAlchemyUnitOfWork(
        session_factory=session_factory,
        repositories={Product: product_repository}
    )
    
    return uow


@pytest.mark.asyncio
async def test_repository_get(product_repository, sample_products):
    """Test getting products by ID."""
    # Get product by ID
    product = await product_repository.get("1")
    
    # Verify product
    assert product is not None
    assert product.id == "1"
    assert product.name == "Widget A"
    assert product.price == 19.99
    assert product.category == "Tools"
    assert product.in_stock is True
    
    # Get non-existent product
    product = await product_repository.get("999")
    assert product is None


@pytest.mark.asyncio
async def test_repository_find(product_repository, sample_products):
    """Test finding products with specifications."""
    # Find all Tools
    tools_spec = AttributeSpecification("category", "Tools")
    tools = await product_repository.find(tools_spec)
    
    # Verify tools
    assert len(tools) == 3
    assert all(p.category == "Tools" for p in tools)
    
    # Find all in-stock products
    in_stock_spec = AttributeSpecification("in_stock", True)
    in_stock_products = await product_repository.find(in_stock_spec)
    
    # Verify in-stock products
    assert len(in_stock_products) == 3
    assert all(p.in_stock is True for p in in_stock_products)
    
    # Find in-stock Tools
    in_stock_tools_spec = AndSpecification(
        AttributeSpecification("category", "Tools"),
        AttributeSpecification("in_stock", True)
    )
    in_stock_tools = await product_repository.find(in_stock_tools_spec)
    
    # Verify in-stock tools
    assert len(in_stock_tools) == 2
    assert all(p.category == "Tools" and p.in_stock is True for p in in_stock_tools)
    
    # Find products that are either Electronics or not in stock
    complex_spec = OrSpecification(
        AttributeSpecification("category", "Electronics"),
        AttributeSpecification("in_stock", False)
    )
    complex_results = await product_repository.find(complex_spec)
    
    # Verify complex results
    assert len(complex_results) == 4
    assert all(p.category == "Electronics" or p.in_stock is False for p in complex_results)


@pytest.mark.asyncio
async def test_repository_find_one(product_repository, sample_products):
    """Test finding a single product with a specification."""
    # Find a specific product
    widget_a_spec = AttributeSpecification("name", "Widget A")
    widget_a = await product_repository.find_one(widget_a_spec)
    
    # Verify product
    assert widget_a is not None
    assert widget_a.name == "Widget A"
    assert widget_a.price == 19.99
    
    # Find a non-existent product
    non_existent_spec = AttributeSpecification("name", "Non-existent")
    non_existent = await product_repository.find_one(non_existent_spec)
    
    # Verify result is None
    assert non_existent is None


@pytest.mark.asyncio
async def test_repository_count(product_repository, sample_products):
    """Test counting products with specifications."""
    # Count all products
    all_count = await product_repository.count(AttributeSpecification("id", None).not_())
    assert all_count == 5
    
    # Count all Tools
    tools_count = await product_repository.count(AttributeSpecification("category", "Tools"))
    assert tools_count == 3
    
    # Count in-stock Electronics
    in_stock_electronics_count = await product_repository.count(
        AndSpecification(
            AttributeSpecification("category", "Electronics"),
            AttributeSpecification("in_stock", True)
        )
    )
    assert in_stock_electronics_count == 1


@pytest.mark.asyncio
async def test_repository_exists(product_repository, sample_products):
    """Test checking if products exist with specifications."""
    # Check if Tools exist
    tools_exist = await product_repository.exists(AttributeSpecification("category", "Tools"))
    assert tools_exist is True
    
    # Check if expensive products exist (price > 100)
    expensive_exist = await product_repository.exists(AttributeSpecification("price", 100))
    assert expensive_exist is False


@pytest.mark.asyncio
async def test_repository_add(product_repository):
    """Test adding a product."""
    # Create a new product
    new_product = Product(
        id="6",
        name="New Product",
        price=99.99,
        category="New Category",
        in_stock=True,
        created_at=datetime.now(timezone.utc)
    )
    
    # Add the product
    await product_repository.add(new_product)
    
    # Verify the product was added
    added_product = await product_repository.get("6")
    assert added_product is not None
    assert added_product.id == "6"
    assert added_product.name == "New Product"
    assert added_product.price == 99.99
    assert added_product.category == "New Category"


@pytest.mark.asyncio
async def test_repository_update(product_repository, sample_products):
    """Test updating a product."""
    # Get a product to update
    product = await product_repository.get("1")
    assert product is not None
    
    # Update the product
    product.name = "Updated Widget A"
    product.price = 24.99
    product.updated_at = datetime.now(timezone.utc)
    
    # Save the update
    await product_repository.update(product)
    
    # Verify the update
    updated_product = await product_repository.get("1")
    assert updated_product is not None
    assert updated_product.name == "Updated Widget A"
    assert updated_product.price == 24.99
    assert updated_product.updated_at is not None


@pytest.mark.asyncio
async def test_repository_remove(product_repository, sample_products):
    """Test removing a product."""
    # Get a product to remove
    product = await product_repository.get("1")
    assert product is not None
    
    # Remove the product
    await product_repository.remove(product)
    
    # Verify the product was removed
    removed_product = await product_repository.get("1")
    assert removed_product is None


@pytest.mark.asyncio
async def test_unit_of_work(unit_of_work, product_repository):
    """Test using the unit of work."""
    # Create a new product
    new_product = Product(
        id="7",
        name="UoW Product",
        price=199.99,
        category="UoW Category",
        in_stock=True,
        created_at=datetime.now(timezone.utc)
    )
    
    # Use the unit of work
    async with unit_of_work:
        # Register the new product
        await unit_of_work.register_new(new_product)
    
    # Verify the product was added
    added_product = await product_repository.get("7")
    assert added_product is not None
    assert added_product.name == "UoW Product"
    assert added_product.price == 199.99


@pytest.mark.asyncio
async def test_unit_of_work_rollback(unit_of_work, product_repository):
    """Test rolling back changes in the unit of work."""
    # Create a new product
    new_product = Product(
        id="8",
        name="Rollback Product",
        price=299.99,
        category="Rollback Category",
        in_stock=True,
        created_at=datetime.now(timezone.utc)
    )
    
    # Use the unit of work with an exception
    try:
        async with unit_of_work:
            # Register the new product
            await unit_of_work.register_new(new_product)
            
            # Raise an exception to trigger rollback
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # Verify the product was not added
    product = await product_repository.get("8")
    assert product is None