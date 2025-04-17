"""
Integration tests for entity-specific repositories.
"""

import pytest
from typing import AsyncGenerator, List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from uno.domain.models import (
    User, UserRole, Product, ProductCategory, 
    Order, OrderStatus, OrderItem
)
from uno.domain.repositories.sqlalchemy.user import UserRepository, UserModel
from uno.domain.repositories.sqlalchemy.product import ProductRepository, ProductModel
from uno.domain.repositories.sqlalchemy.order import OrderRepository, OrderModel, OrderItemModel
from uno.domain.repositories.sqlalchemy.base import SQLAlchemyUnitOfWork

# Test database URL - use SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Define metadata
Base = declarative_base()

@pytest.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(DATABASE_URL)
    
    # Create tables
    async with engine.begin() as conn:
        # Drop tables first if they exist
        await conn.run_sync(Base.metadata.drop_all)
        
        # Add the metadata from our models
        Base.metadata.tables.update(UserModel.metadata.tables)
        Base.metadata.tables.update(ProductModel.metadata.tables)
        Base.metadata.tables.update(OrderModel.metadata.tables)
        Base.metadata.tables.update(OrderItemModel.metadata.tables)
        
        # Create tables
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
async def user_repository(session_factory):
    """Create a repository for User entities."""
    repository = UserRepository(session_factory=session_factory)
    return repository


@pytest.fixture
async def product_repository(session_factory):
    """Create a repository for Product entities."""
    repository = ProductRepository(session_factory=session_factory)
    return repository


@pytest.fixture
async def order_repository(session_factory):
    """Create a repository for Order entities."""
    repository = OrderRepository(session_factory=session_factory)
    return repository


@pytest.fixture
async def unit_of_work(session_factory, user_repository, product_repository, order_repository):
    """Create a unit of work with repositories."""
    # Create unit of work
    uow = SQLAlchemyUnitOfWork(
        session_factory=session_factory,
        repositories={
            User: user_repository,
            Product: product_repository,
            Order: order_repository
        }
    )
    
    return uow


@pytest.fixture
async def sample_users(user_repository):
    """Create sample users in the database."""
    users = [
        User(
            id=str(uuid4()),
            username="user1",
            email="user1@example.com",
            password_hash="hashedpassword1",
            full_name="User One",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        ),
        User(
            id=str(uuid4()),
            username="user2",
            email="user2@example.com",
            password_hash="hashedpassword2",
            full_name="User Two",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        ),
        User(
            id=str(uuid4()),
            username="admin",
            email="admin@example.com",
            password_hash="hashedpasswordadmin",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        ),
        User(
            id=str(uuid4()),
            username="inactive",
            email="inactive@example.com",
            password_hash="hashedpasswordinactive",
            full_name="Inactive User",
            role=UserRole.USER,
            is_active=False,
            created_at=datetime.now(timezone.utc)
        ),
    ]
    
    # Add users to database
    for user in users:
        await user_repository.add(user)
    
    return users


@pytest.fixture
async def sample_products(product_repository):
    """Create sample products in the database."""
    products = [
        Product(
            id=str(uuid4()),
            name="Product 1",
            description="Description for Product 1",
            price=19.99,
            category=ProductCategory.ELECTRONICS,
            sku="SKU001",
            in_stock=True,
            stock_quantity=100,
            created_at=datetime.now(timezone.utc)
        ),
        Product(
            id=str(uuid4()),
            name="Product 2",
            description="Description for Product 2",
            price=29.99,
            category=ProductCategory.CLOTHING,
            sku="SKU002",
            in_stock=True,
            stock_quantity=50,
            created_at=datetime.now(timezone.utc)
        ),
        Product(
            id=str(uuid4()),
            name="Product 3",
            description="Description for Product 3",
            price=39.99,
            category=ProductCategory.ELECTRONICS,
            sku="SKU003",
            in_stock=False,
            stock_quantity=0,
            created_at=datetime.now(timezone.utc)
        ),
        Product(
            id=str(uuid4()),
            name="Product 4",
            description="Description for Product 4",
            price=49.99,
            category=ProductCategory.HOME,
            sku="SKU004",
            in_stock=True,
            stock_quantity=10,
            created_at=datetime.now(timezone.utc)
        ),
    ]
    
    # Add products to database
    for product in products:
        await product_repository.add(product)
    
    return products


@pytest.fixture
async def sample_orders(order_repository, sample_users, sample_products):
    """Create sample orders in the database."""
    orders = [
        Order(
            id=str(uuid4()),
            user_id=sample_users[0].id,
            status=OrderStatus.PENDING,
            total_amount=19.99,
            shipping_address={
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345"
            },
            payment_method="credit_card",
            order_date=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            items=[
                OrderItem(
                    id=str(uuid4()),
                    product_id=sample_products[0].id,
                    quantity=1,
                    unit_price=19.99,
                    total_price=19.99
                )
            ]
        ),
        Order(
            id=str(uuid4()),
            user_id=sample_users[1].id,
            status=OrderStatus.SHIPPED,
            total_amount=69.98,
            shipping_address={
                "street": "456 Oak St",
                "city": "Othertown",
                "state": "NY",
                "zip": "67890"
            },
            payment_method="paypal",
            order_date=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            items=[
                OrderItem(
                    id=str(uuid4()),
                    product_id=sample_products[1].id,
                    quantity=1,
                    unit_price=29.99,
                    total_price=29.99
                ),
                OrderItem(
                    id=str(uuid4()),
                    product_id=sample_products[3].id,
                    quantity=1,
                    unit_price=39.99,
                    total_price=39.99
                )
            ]
        ),
        Order(
            id=str(uuid4()),
            user_id=sample_users[0].id,
            status=OrderStatus.DELIVERED,
            total_amount=49.99,
            shipping_address={
                "street": "789 Pine St",
                "city": "Sometown",
                "state": "TX",
                "zip": "54321"
            },
            payment_method="credit_card",
            order_date=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            items=[
                OrderItem(
                    id=str(uuid4()),
                    product_id=sample_products[3].id,
                    quantity=1,
                    unit_price=49.99,
                    total_price=49.99
                )
            ]
        )
    ]
    
    # Add orders to database
    for order in orders:
        await order_repository.add(order)
    
    return orders


@pytest.mark.asyncio
async def test_user_repository(user_repository, sample_users):
    """Test the user repository."""
    # Test find_by_username
    user = await user_repository.find_by_username("user1")
    assert user is not None
    assert user.username == "user1"
    assert user.email == "user1@example.com"
    
    # Test find_by_email
    user = await user_repository.find_by_email("admin@example.com")
    assert user is not None
    assert user.username == "admin"
    assert user.role == UserRole.ADMIN
    
    # Test find_by_username_or_email
    user = await user_repository.find_by_username_or_email("user2@example.com")
    assert user is not None
    assert user.username == "user2"
    
    # Test find_active
    active_users = await user_repository.find_active()
    assert len(active_users) == 3
    assert all(user.is_active for user in active_users)
    
    # Test find_by_role
    admin_users = await user_repository.find_by_role(UserRole.ADMIN)
    assert len(admin_users) == 1
    assert admin_users[0].username == "admin"
    
    # Test find_active_by_role
    active_regular_users = await user_repository.find_active_by_role(UserRole.USER)
    assert len(active_regular_users) == 2
    assert all(user.role == UserRole.USER and user.is_active for user in active_regular_users)
    
    # Test deactivate
    user = await user_repository.find_by_username("user1")
    await user_repository.deactivate(user)
    updated_user = await user_repository.get(user.id)
    assert updated_user.is_active is False
    
    # Test activate
    user = await user_repository.find_by_username("inactive")
    await user_repository.activate(user)
    updated_user = await user_repository.get(user.id)
    assert updated_user.is_active is True
    
    # Test change_role
    user = await user_repository.find_by_username("user2")
    await user_repository.change_role(user, UserRole.ADMIN)
    updated_user = await user_repository.get(user.id)
    assert updated_user.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_product_repository(product_repository, sample_products):
    """Test the product repository."""
    # Test find_by_category
    electronics = await product_repository.find_by_category(ProductCategory.ELECTRONICS)
    assert len(electronics) == 2
    assert all(product.category == ProductCategory.ELECTRONICS for product in electronics)
    
    # Test find_by_sku
    product = await product_repository.find_by_sku("SKU001")
    assert product is not None
    assert product.name == "Product 1"
    assert product.price == 19.99
    
    # Test find_in_stock
    in_stock = await product_repository.find_in_stock()
    assert len(in_stock) == 3
    assert all(product.in_stock for product in in_stock)
    
    # Test find_in_stock_by_category
    in_stock_electronics = await product_repository.find_in_stock_by_category(ProductCategory.ELECTRONICS)
    assert len(in_stock_electronics) == 1
    assert in_stock_electronics[0].name == "Product 1"
    assert in_stock_electronics[0].category == ProductCategory.ELECTRONICS
    assert in_stock_electronics[0].in_stock is True
    
    # Test find_low_stock
    low_stock = await product_repository.find_low_stock(20)
    assert len(low_stock) == 1
    assert low_stock[0].name == "Product 4"
    assert low_stock[0].stock_quantity == 10
    
    # Test update_stock_quantity
    product = await product_repository.find_by_sku("SKU001")
    await product_repository.update_stock_quantity(product, 50)
    updated_product = await product_repository.get(product.id)
    assert updated_product.stock_quantity == 50
    assert updated_product.in_stock is True
    
    # Test setting stock to zero
    product = await product_repository.find_by_sku("SKU002")
    await product_repository.update_stock_quantity(product, 0)
    updated_product = await product_repository.get(product.id)
    assert updated_product.stock_quantity == 0
    assert updated_product.in_stock is False


@pytest.mark.asyncio
async def test_order_repository(order_repository, sample_orders, sample_users):
    """Test the order repository."""
    # Test find_by_user
    user_orders = await order_repository.find_by_user(sample_users[0].id)
    assert len(user_orders) == 2
    assert all(order.user_id == sample_users[0].id for order in user_orders)
    
    # Test find_by_status
    pending_orders = await order_repository.find_by_status(OrderStatus.PENDING)
    assert len(pending_orders) == 1
    assert pending_orders[0].status == OrderStatus.PENDING
    
    # Test find_by_user_and_status
    delivered_user_orders = await order_repository.find_by_user_and_status(
        sample_users[0].id, OrderStatus.DELIVERED
    )
    assert len(delivered_user_orders) == 1
    assert delivered_user_orders[0].user_id == sample_users[0].id
    assert delivered_user_orders[0].status == OrderStatus.DELIVERED
    
    # Test update_status
    order = pending_orders[0]
    await order_repository.update_status(order, OrderStatus.SHIPPED)
    updated_order = await order_repository.get(order.id)
    assert updated_order.status == OrderStatus.SHIPPED


@pytest.mark.asyncio
async def test_unit_of_work(unit_of_work, user_repository, product_repository):
    """Test using the unit of work pattern."""
    # Create a new user and product
    new_user = User(
        id=str(uuid4()),
        username="newuser",
        email="newuser@example.com",
        password_hash="hashedpassword",
        full_name="New User",
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    
    new_product = Product(
        id=str(uuid4()),
        name="New Product",
        description="Description for New Product",
        price=59.99,
        category=ProductCategory.BOOKS,
        sku="SKU005",
        in_stock=True,
        stock_quantity=25,
        created_at=datetime.now(timezone.utc)
    )
    
    # Use unit of work to add both entities in a single transaction
    async with unit_of_work:
        await unit_of_work.register_new(new_user)
        await unit_of_work.register_new(new_product)
    
    # Verify entities were added
    added_user = await user_repository.get(new_user.id)
    assert added_user is not None
    assert added_user.username == "newuser"
    
    added_product = await product_repository.get(new_product.id)
    assert added_product is not None
    assert added_product.name == "New Product"
    
    # Test transaction rollback
    failed_user = User(
        id=str(uuid4()),
        username="newuser",  # Duplicate username should cause error
        email="anotheruser@example.com",
        password_hash="hashedpassword",
        full_name="Another User",
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    
    another_product = Product(
        id=str(uuid4()),
        name="Another Product",
        description="Description for Another Product",
        price=69.99,
        category=ProductCategory.TOYS,
        sku="SKU006",
        in_stock=True,
        stock_quantity=30,
        created_at=datetime.now(timezone.utc)
    )
    
    # Attempt to add both entities, but this should fail
    try:
        async with unit_of_work:
            await unit_of_work.register_new(failed_user)
            await unit_of_work.register_new(another_product)
    except Exception:
        pass  # Expected to fail
    
    # Verify that neither entity was added
    failed_user_check = await user_repository.find_by_username("anotheruser@example.com")
    assert failed_user_check is None
    
    another_product_check = await product_repository.find_by_sku("SKU006")
    assert another_product_check is None