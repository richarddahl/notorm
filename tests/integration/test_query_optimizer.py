"""
Integration tests for the query optimizer and query cache.

This module tests the query optimizer and query cache in a real
database environment, verifying that query analysis, optimization,
and caching work correctly together.
"""

import asyncio
import time
import pytest
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, text, Table
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, sessionmaker

from uno.database.query_optimizer import (
    QueryOptimizer, OptimizationConfig, OptimizationLevel, 
    QueryPlan, IndexRecommendation, IndexType, optimize_query
)
from uno.database.query_cache import QueryCache, QueryCacheConfig, cached_query, CacheBackend, CacheStrategy
from uno.database.session import get_engine, async_session


# Define test models
Base = declarative_base()


class TestProduct(Base):
    """Test product model for optimizer tests."""
    
    __tablename__ = 'test_optimizer_products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    category = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with orders
    order_items = relationship("TestOrderItem", back_populates="product")


class TestCustomer(Base):
    """Test customer model for optimizer tests."""
    
    __tablename__ = 'test_optimizer_customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20))
    address = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with orders
    orders = relationship("TestOrder", back_populates="customer")


class TestOrder(Base):
    """Test order model for optimizer tests."""
    
    __tablename__ = 'test_optimizer_orders'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('test_optimizer_customers.id'), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='pending')
    total_amount = Column(Float, default=0.0)
    
    # Relationships
    customer = relationship("TestCustomer", back_populates="orders")
    items = relationship("TestOrderItem", back_populates="order")


class TestOrderItem(Base):
    """Test order item model for optimizer tests."""
    
    __tablename__ = 'test_optimizer_order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('test_optimizer_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('test_optimizer_products.id'), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("TestOrder", back_populates="items")
    product = relationship("TestProduct", back_populates="order_items")


@pytest.fixture(scope="module")
async def setup_test_db():
    """Set up test database tables and sample data."""
    engine = get_engine()
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Insert sample data
    async with async_session() as session:
        # Add products
        products = []
        for i in range(1, 21):
            product = TestProduct(
                name=f"Product {i}",
                description=f"Description for product {i}",
                price=10.0 + i,
                category=f"Category {(i-1) // 5 + 1}",
                is_active=True
            )
            products.append(product)
        
        session.add_all(products)
        await session.flush()
        
        # Add customers
        customers = []
        for i in range(1, 11):
            customer = TestCustomer(
                name=f"Customer {i}",
                email=f"customer{i}@example.com",
                phone=f"555-{1000+i}",
                address=f"Address {i}"
            )
            customers.append(customer)
        
        session.add_all(customers)
        await session.flush()
        
        # Add orders
        orders = []
        for i in range(1, 31):
            order = TestOrder(
                customer_id=((i-1) % 10) + 1,
                status=['pending', 'completed', 'shipped'][i % 3],
                total_amount=0  # Will be calculated
            )
            orders.append(order)
        
        session.add_all(orders)
        await session.flush()
        
        # Add order items
        order_items = []
        for order in orders:
            # Each order has 1-3 products
            num_items = (order.id % 3) + 1
            total = 0.0
            
            for j in range(num_items):
                product_id = ((order.id + j) % 20) + 1
                product = next(p for p in products if p.id == product_id)
                quantity = (order.id % 5) + 1
                price = product.price
                
                order_item = TestOrderItem(
                    order_id=order.id,
                    product_id=product_id,
                    quantity=quantity,
                    price=price
                )
                order_items.append(order_item)
                total += quantity * price
            
            # Update order total
            order.total_amount = total
        
        session.add_all(order_items)
        await session.commit()
    
    yield
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def query_optimizer(setup_test_db):
    """Create a query optimizer instance for testing."""
    # Create a session for the optimizer
    async with async_session() as session:
        # Create optimizer configuration
        config = OptimizationConfig(
            enabled=True,
            optimization_level=OptimizationLevel.STANDARD,
            analyze_queries=True,
            collect_statistics=True,
            rewrite_queries=True,
            recommend_indexes=True,
            log_recommendations=True,
        )
        
        # Create the optimizer
        optimizer = QueryOptimizer(session=session, config=config)
        
        # Load schema information
        await optimizer.load_schema_information()
        
        yield optimizer


@pytest.fixture
async def query_cache():
    """Create a query cache instance for testing."""
    # Create cache configuration
    config = QueryCacheConfig(
        enabled=True,
        strategy=CacheStrategy.SIMPLE,
        backend=CacheBackend.MEMORY,
        default_ttl=30.0,  # 30 seconds for testing
        track_dependencies=True,
    )
    
    # Create the cache
    cache = QueryCache(config=config)
    
    yield cache
    
    # Clean up
    await cache.clear()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_plan_analysis(query_optimizer):
    """Test query plan analysis functionality."""
    # Define a test query
    query = select(TestProduct).where(TestProduct.category == "Category 1")
    
    # Analyze the query
    plan = await query_optimizer.analyze_query(query)
    
    # Check the plan
    assert plan is not None
    assert isinstance(plan, QueryPlan)
    assert plan.estimated_rows > 0
    assert plan.plan_type is not None
    assert isinstance(plan.operations, list)
    assert len(plan.operations) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_index_recommendations(query_optimizer):
    """Test index recommendation functionality."""
    # Define a query that would benefit from an index
    query = select(TestProduct).where(
        (TestProduct.category == "Category 1") & 
        (TestProduct.price > 15.0)
    )
    
    # Analyze the query
    plan = await query_optimizer.analyze_query(query)
    
    # Get index recommendations
    recommendations = query_optimizer.recommend_indexes(plan)
    
    # Check recommendations
    assert isinstance(recommendations, list)
    
    # May have recommendations depending on the database state
    if recommendations:
        recommendation = recommendations[0]
        assert isinstance(recommendation, IndexRecommendation)
        assert recommendation.table_name == 'test_optimizer_products' or recommendation.table_name == 'test_optimizer_products'
        assert len(recommendation.column_names) > 0
        assert recommendation.get_creation_sql() is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_rewrite(query_optimizer):
    """Test query rewrite functionality."""
    # Define a query that can be rewritten
    query = "SELECT COUNT(*) FROM test_optimizer_products"
    
    # Try to rewrite the query
    rewrite_result = await query_optimizer.rewrite_query(query)
    
    # Check the result
    assert rewrite_result is not None
    
    # If a rewrite was found, check its properties
    if rewrite_result.is_success:
        rewrite = rewrite_result.value
        assert rewrite.original_query == query
        assert rewrite.rewritten_query is not None
        assert rewrite.rewrite_type is not None
        assert rewrite.estimated_improvement is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_optimized_query(query_optimizer, setup_test_db):
    """Test execution of optimized queries."""
    # Define a query
    query = select(TestProduct).where(
        (TestProduct.price > 15.0) &
        (TestProduct.is_active == True)
    )
    
    # Execute the optimized query
    result = await query_optimizer.execute_optimized_query(query)
    
    # Check the result
    assert result is not None
    assert isinstance(result, list)
    
    # Check that statistics were collected
    stats = query_optimizer.get_statistics()
    assert len(stats) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_slow_query_detection(query_optimizer, setup_test_db):
    """Test detection of slow queries and statistics tracking."""
    # Set very low threshold to consider all queries as "slow"
    query_optimizer.config.slow_query_threshold = 0.0
    
    # Define a complex query that should be slow enough for testing
    query = """
    SELECT p.name, c.name, SUM(oi.quantity * oi.price) as total
    FROM test_optimizer_products p
    JOIN test_optimizer_order_items oi ON p.id = oi.product_id
    JOIN test_optimizer_orders o ON oi.order_id = o.id
    JOIN test_optimizer_customers c ON o.customer_id = c.id
    WHERE p.category = 'Category 1'
    GROUP BY p.name, c.name
    ORDER BY total DESC
    """
    
    # Execute the query
    result = await query_optimizer.execute_optimized_query(query)
    
    # Check that slow queries were recorded
    slow_queries = query_optimizer.get_slow_queries()
    assert len(slow_queries) > 0
    
    # Check that the slow query has a query plan
    for stats in slow_queries:
        assert stats.query_text in query or query in stats.query_text
        if stats.latest_plan:
            assert isinstance(stats.latest_plan, QueryPlan)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_optimize_query_helper(setup_test_db):
    """Test the optimize_query helper function."""
    async with async_session() as session:
        # Define a query
        query = select(TestProduct).where(TestProduct.category == "Category 1")
        
        # Optimize the query
        optimized_query, recommendations = await optimize_query(
            query=query,
            session=session,
        )
        
        # Check the results
        assert optimized_query is not None
        assert isinstance(recommendations, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_cache_basic(query_cache):
    """Test basic query cache functionality."""
    # Define a test key and value
    test_key = "test_key"
    test_value = {"data": "test_value"}
    
    # Check cache miss
    result = await query_cache.get(test_key)
    assert result.is_error
    
    # Set value in cache
    await query_cache.set(test_key, test_value, ttl=10.0)
    
    # Check cache hit
    result = await query_cache.get(test_key)
    assert result.is_success
    assert result.value == test_value
    
    # Check cache statistics
    stats = query_cache.get_stats()
    assert stats["performance"]["hits"] == 1
    assert stats["performance"]["misses"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_cache_expiration(query_cache):
    """Test cache expiration functionality."""
    # Define a test key and value
    test_key = "expiring_key"
    test_value = {"data": "expiring_value"}
    
    # Set value with short TTL
    await query_cache.set(test_key, test_value, ttl=1.0)
    
    # Check immediate hit
    result = await query_cache.get(test_key)
    assert result.is_success
    assert result.value == test_value
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    
    # Check expired miss
    result = await query_cache.get(test_key)
    assert result.is_error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_cache_invalidation(query_cache):
    """Test cache invalidation functionality."""
    # Set multiple values
    await query_cache.set("key1", "value1")
    await query_cache.set("key2", "value2")
    await query_cache.set("key3", "value3")
    
    # Verify values are cached
    assert (await query_cache.get("key1")).is_success
    assert (await query_cache.get("key2")).is_success
    assert (await query_cache.get("key3")).is_success
    
    # Invalidate specific key
    await query_cache.invalidate("key2")
    
    # Check invalidation
    assert (await query_cache.get("key1")).is_success
    assert (await query_cache.get("key2")).is_error
    assert (await query_cache.get("key3")).is_success
    
    # Invalidate by pattern
    await query_cache.invalidate_by_pattern("key")
    
    # Check all invalidated
    assert (await query_cache.get("key1")).is_error
    assert (await query_cache.get("key3")).is_error


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_cache_dependencies(query_cache):
    """Test cache dependency tracking."""
    # Set values with dependencies
    await query_cache.set(
        "query1", 
        "result1", 
        dependencies=["products", "customers"]
    )
    await query_cache.set(
        "query2", 
        "result2", 
        dependencies=["products"]
    )
    await query_cache.set(
        "query3", 
        "result3", 
        dependencies=["orders"]
    )
    
    # Verify values are cached
    assert (await query_cache.get("query1")).is_success
    assert (await query_cache.get("query2")).is_success
    assert (await query_cache.get("query3")).is_success
    
    # Invalidate by table dependency
    await query_cache.invalidate_by_table("products")
    
    # Check invalidation
    assert (await query_cache.get("query1")).is_error
    assert (await query_cache.get("query2")).is_error
    assert (await query_cache.get("query3")).is_success


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cached_query_decorator(query_cache, setup_test_db):
    """Test the cached_query decorator."""
    # Define a function with cached_query decorator
    @cached_query(ttl=10.0, dependencies=["test_optimizer_products"], cache_instance=query_cache)
    async def get_products_by_category(session: AsyncSession, category: str):
        query = select(TestProduct).where(TestProduct.category == category)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    # Execute the function
    async with async_session() as session:
        # First call - should miss cache
        start_time = time.time()
        products1 = await get_products_by_category(session, "Category 1")
        first_duration = time.time() - start_time
        
        # Second call - should hit cache
        start_time = time.time()
        products2 = await get_products_by_category(session, "Category 1")
        second_duration = time.time() - start_time
        
        # Check results
        assert products1 == products2
        assert len(products1) > 0
        
        # Check cache statistics
        stats = query_cache.get_stats()
        assert stats["performance"]["hits"] >= 1
        assert stats["performance"]["misses"] >= 1
        
        # Different parameter - should miss cache
        products3 = await get_products_by_category(session, "Category 2")
        assert products3 != products1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_optimizer_with_cache(query_optimizer, query_cache, setup_test_db):
    """Test integration between query optimizer and query cache."""
    # Define a query
    query = select(TestProduct).where(
        (TestProduct.category == "Category 1") & 
        (TestProduct.price > 15.0)
    )
    
    # Create a cache key
    from uno.database.query_cache import QueryCacheKey
    cache_key = QueryCacheKey.from_select(query)
    
    # Check cache miss
    cache_result = await query_cache.get(cache_key)
    assert cache_result.is_error
    
    # Execute with optimizer
    query_result = await query_optimizer.execute_optimized_query(query)
    
    # Store in cache manually
    await query_cache.set(
        cache_key, 
        query_result,
        dependencies=["test_optimizer_products"]
    )
    
    # Check cache hit
    cache_result = await query_cache.get(cache_key)
    assert cache_result.is_success
    assert cache_result.value == query_result
    
    # Verify data is same as from direct query
    async with async_session() as session:
        direct_result = await session.execute(query)
        direct_data = list(direct_result.scalars().all())
        assert len(direct_data) == len(query_result)