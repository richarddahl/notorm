"""
Integration tests for batch operations.

These tests verify that batch operations work correctly with a real database,
covering:
- Single-table batch operations (CRUD)
- Multi-table batch operations with relationships
- Error handling during batch operations
- Transaction management for batch operations
- Performance metrics for batch operations
"""

import asyncio
import pytest
import random
import time
import traceback
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple, Set

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    create_engine,
    Table,
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from uno.model import Model
from uno.domain.repository import UnoDBRepository
from uno.domain.core import Entity
from uno.database.session import async_session
from uno.database.db_manager import DBManager
from uno.queries.batch_operations import (
    BatchOperations,
    BatchConfig,
    BatchExecutionStrategy,
    BatchSize,
    BatchError,
    BatchMetrics,
    ResultCallback,
)


# Create test models
Base = declarative_base()


class TestModel(Base, Model):
    __tablename__ = "test_batch_models"

    __test__ = False  # Prevent pytest from collecting this class as a test

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Define one-to-many relationship with details
    details = relationship(
        "TestDetailModel", back_populates="parent", cascade="all, delete-orphan"
    )


class TestDetailModel(Base, Model):
    __tablename__ = "test_batch_details"
    __test__ = False  # Prevent pytest from collecting this class as a test

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("test_batch_models.id"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Define many-to-one relationship with parent
    parent = relationship("TestModel", back_populates="details")


class TestTagModel(Base, Model):
    __tablename__ = "test_batch_tags"
    __test__ = False  # Prevent pytest from collecting this class as a test

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)


# Association table for many-to-many relationship
test_model_tags = Table(
    "test_batch_model_tags",
    Base.metadata,
    Column("model_id", Integer, ForeignKey("test_batch_models.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("test_batch_tags.id"), primary_key=True),
)


# Models with unique constraints for testing error handling
class TestUniqueModel(Base, Model):
    __tablename__ = "test_batch_unique_models"
    __test__ = False  # Prevent pytest from collecting this class as a test

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)  # Unique constraint
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create domain entities
class TestEntity(Entity):
    __test__ = False  # Prevent pytest from collecting this class as a test

    id: str
    name: str
    description: Optional[str] = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    details: List["TestDetailEntity"] = []

    # Map to model class
    __uno_model__ = TestModel


class TestDetailEntity(Entity):
    __test__ = False  # Prevent pytest from collecting this class as a test
    id: str
    parent_id: str
    key: str
    value: str
    created_at: datetime

    # Map to model class
    __uno_model__ = TestDetailModel


class TestTagEntity(Entity):
    __test__ = False  # Prevent pytest from collecting this class as a test
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime

    # Map to model class
    __uno_model__ = TestTagModel


class TestUniqueEntity(Entity):
    __test__ = False  # Prevent pytest from collecting this class as a test
    id: str
    code: str
    name: str
    created_at: datetime

    # Map to model class
    __uno_model__ = TestUniqueModel


@pytest.fixture(scope="module")
async def test_engine():
    """Create a test database engine."""
    # Create engine with echo for debugging SQL
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
        echo=False,
    )

    # Create tables
    async with engine.begin() as conn:
        # Drop tables if they exist
        await conn.run_sync(Base.metadata.drop_all)
        # Create tables
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine
    await engine.dispose()


@pytest.fixture(scope="module")
async def database(test_engine):
    """Create a test database session."""
    # Create session factory
    session_factory = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create a session to use
    async with session_factory() as session:
        yield session


@pytest.fixture
def batch_config():
    """Create a batch configuration."""
    return BatchConfig(
        batch_size=10,
        max_workers=2,
        collect_metrics=True,
        log_progress=True,
        execution_strategy=BatchExecutionStrategy.CHUNKED,
    )


@pytest.fixture
def optimized_batch_config():
    """Create an optimized batch configuration for performance testing."""
    return BatchConfig(
        batch_size=25,
        max_workers=4,
        collect_metrics=True,
        log_progress=True,
        execution_strategy=BatchExecutionStrategy.PARALLEL,
    )


@pytest.fixture
def sequential_batch_config():
    """Create a sequential batch configuration for transaction testing."""
    return BatchConfig(
        batch_size=5,
        max_workers=1,
        collect_metrics=True,
        log_progress=True,
        execution_strategy=BatchExecutionStrategy.SEQUENTIAL,
    )


@pytest.fixture
def repository(database):
    """Create a repository for the test entity."""
    return UnoDBRepository(TestEntity, use_batch_operations=True, batch_size=10)


@pytest.fixture
def detail_repository(database):
    """Create a repository for the test detail entity."""
    return UnoDBRepository(TestDetailEntity, use_batch_operations=True, batch_size=20)


@pytest.fixture
def tag_repository(database):
    """Create a repository for the test tag entity."""
    return UnoDBRepository(TestTagEntity, use_batch_operations=True, batch_size=10)


@pytest.fixture
def unique_repository(database):
    """Create a repository for the test unique entity."""
    return UnoDBRepository(TestUniqueEntity, use_batch_operations=True, batch_size=10)


@pytest.fixture
def batch_operations(database, batch_config):
    """Create batch operations for the test model."""
    return BatchOperations(
        model_class=TestModel,
        session=database,
        batch_config=batch_config,
    )


@pytest.fixture
def detail_batch_operations(database, batch_config):
    """Create batch operations for the test detail model."""
    return BatchOperations(
        model_class=TestDetailModel,
        session=database,
        batch_config=batch_config,
    )


@pytest.fixture
def tag_batch_operations(database, batch_config):
    """Create batch operations for the test tag model."""
    return BatchOperations(
        model_class=TestTagModel,
        session=database,
        batch_config=batch_config,
    )


@pytest.fixture
def unique_batch_operations(database, batch_config):
    """Create batch operations for the test unique model."""
    return BatchOperations(
        model_class=TestUniqueModel,
        session=database,
        batch_config=batch_config,
    )


@pytest.mark.asyncio
async def test_batch_insert(batch_operations):
    """Test batch insert operations."""
    # Generate test records
    records = [
        {
            "name": f"Test {i}",
            "description": f"Description for test {i}",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(1, 51)  # 50 records
    ]

    # Insert records
    result = await batch_operations.batch_insert(
        records=records,
        return_models=False,
    )

    # Check result
    assert result == 50

    # Verify records were inserted
    query = "SELECT COUNT(*) FROM test_batch_models"
    count_result = await batch_operations.batch_execute_sql(query, [{}])

    assert count_result[0][0] == 50


@pytest.mark.asyncio
async def test_batch_get(batch_operations):
    """Test batch get operations."""
    # Get existing records
    ids = list(range(1, 51))  # IDs 1-50

    # Get records
    models = await batch_operations.batch_get(
        id_values=ids,
        parallel=True,
    )

    # Check result
    assert len(models) == 50
    assert all(isinstance(model, TestModel) for model in models)
    assert all(model.id in ids for model in models)


@pytest.mark.asyncio
async def test_batch_update(batch_operations):
    """Test batch update operations."""
    # Create update records
    updates = [
        {
            "id": i,
            "name": f"Updated {i}",
            "description": f"Updated description for test {i}",
            "updated_at": datetime.utcnow(),
        }
        for i in range(1, 26)  # Update first 25 records
    ]

    # Update records
    result = await batch_operations.batch_update(
        records=updates,
        id_field="id",
        fields_to_update=["name", "description", "updated_at"],
        return_models=False,
    )

    # Check result
    assert result == 25

    # Verify records were updated
    models = await batch_operations.batch_get(
        id_values=list(range(1, 26)),
    )

    assert all(model.name.startswith("Updated") for model in models)


@pytest.mark.asyncio
async def test_batch_upsert(batch_operations):
    """Test batch upsert operations."""
    # Create records for upsert (mix of new and existing)
    upserts = []

    # Update existing records
    for i in range(1, 11):
        upserts.append(
            {
                "id": i,
                "name": f"Upserted {i}",
                "description": f"Upserted description for test {i}",
                "updated_at": datetime.utcnow(),
            }
        )

    # New records
    for i in range(51, 61):
        upserts.append(
            {
                "name": f"New {i}",
                "description": f"New description for test {i}",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

    # Perform upsert
    result = await batch_operations.batch_upsert(
        records=upserts,
        constraint_columns=["id"],
        return_models=False,
    )

    # Check result (should be 20 - 10 updated, 10 inserted)
    assert result == 20

    # Verify records were upserted
    # Get updated records
    updated_models = await batch_operations.batch_get(
        id_values=list(range(1, 11)),
    )

    assert all(model.name.startswith("Upserted") for model in updated_models)

    # Get new records
    new_models = await batch_operations.batch_get(
        id_values=list(range(51, 61)),
    )

    assert len(new_models) == 10
    assert all(model.name.startswith("New") for model in new_models)


@pytest.mark.asyncio
async def test_batch_delete(batch_operations):
    """Test batch delete operations."""
    # Delete records
    ids = list(range(26, 51))  # Delete records 26-50

    # Delete records
    result = await batch_operations.batch_delete(
        id_values=ids,
        return_models=False,
    )

    # Check result
    assert result == 25

    # Verify records were deleted
    models = await batch_operations.batch_get(
        id_values=ids,
    )

    assert len(models) == 0

    # Verify total count
    query = "SELECT COUNT(*) FROM test_batch_models"
    count_result = await batch_operations.batch_execute_sql(query, [{}])

    assert count_result[0][0] == 35  # 50 initial + 10 new - 25 deleted


@pytest.mark.asyncio
async def test_repository_batch_operations(repository, database):
    """Test repository batch operations."""
    # Create entities
    entities = [
        TestEntity(
            id=str(i + 100),
            name=f"Entity {i}",
            description=f"Description for entity {i}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        for i in range(1, 21)  # 20 entities
    ]

    # Add entities in batch
    added_entities = await repository.batch_add(entities)

    # Check result
    assert len(added_entities) == 20
    assert all(isinstance(entity, TestEntity) for entity in added_entities)

    # Get entities in batch
    ids = [str(i + 100) for i in range(1, 21)]
    retrieved_entities = await repository.batch_get(ids)

    # Check result
    assert len(retrieved_entities) == 20
    assert all(entity.id in ids for entity in retrieved_entities)

    # Update entities in batch
    for entity in retrieved_entities[:10]:
        entity.name = f"Updated {entity.name}"
        entity.updated_at = datetime.utcnow()

    updated_count = await repository.batch_update(retrieved_entities[:10])

    # Check result
    assert updated_count == 10

    # Remove entities in batch
    remove_ids = [str(i + 100) for i in range(11, 21)]
    removed_count = await repository.batch_remove(remove_ids)

    # Check result
    assert removed_count == 10

    # Verify final state
    remaining_entities = await repository.batch_get(
        [str(i + 100) for i in range(1, 21)]
    )

    # Should have 10 entities left, all with updated names
    assert len(remaining_entities) == 10
    assert all(entity.name.startswith("Updated") for entity in remaining_entities)


@pytest.mark.asyncio
async def test_batch_error_handling(unique_batch_operations):
    """Test error handling during batch operations."""
    # Create records with unique constraints
    records = [
        {
            "code": f"CODE-{i}",
            "name": f"Unique {i}",
            "created_at": datetime.utcnow(),
        }
        for i in range(1, 6)  # 5 unique records
    ]

    # Insert records
    result = await unique_batch_operations.batch_insert(
        records=records,
        return_models=False,
    )

    assert result == 5

    # Try to insert records with duplicate codes (should fail)
    duplicate_records = [
        {
            "code": "CODE-1",  # Duplicate code
            "name": "Duplicate 1",
            "created_at": datetime.utcnow(),
        },
        {
            "code": "CODE-2",  # Duplicate code
            "name": "Duplicate 2",
            "created_at": datetime.utcnow(),
        },
        {
            "code": "CODE-NEW",  # New code that should work
            "name": "New Record",
            "created_at": datetime.utcnow(),
        },
    ]

    # Configure batch operations to collect errors
    # This should continue processing after errors
    unique_batch_operations.batch_config.continue_on_error = True

    # Insert with duplicates and collect errors
    try:
        await unique_batch_operations.batch_insert(
            records=duplicate_records,
            return_models=False,
        )
        assert False, "Should have raised BatchError"
    except BatchError as e:
        # Verify the error details
        assert len(e.errors) == 2  # Should have 2 errors for duplicates
        assert e.successful_count == 1  # 1 record should have been successful
        assert all(isinstance(err, IntegrityError) for err in e.errors.values())

    # Verify that the non-duplicate record was inserted
    async with async_session() as session:
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_unique_models WHERE code = 'CODE-NEW'"
        )
        assert result.scalar() == 1

    # Test transaction rollback on error
    # Configure batch operations to stop on first error and use transaction
    unique_batch_operations.batch_config.continue_on_error = False
    unique_batch_operations.batch_config.use_transaction = True

    # Create more test records
    transaction_records = [
        {
            "code": "TX-1",
            "name": "Transaction 1",
            "created_at": datetime.utcnow(),
        },
        {
            "code": "TX-2",
            "name": "Transaction 2",
            "created_at": datetime.utcnow(),
        },
        {
            "code": "CODE-1",  # Duplicate that will cause failure
            "name": "Transaction Fail",
            "created_at": datetime.utcnow(),
        },
    ]

    # Try to insert with transaction
    try:
        await unique_batch_operations.batch_insert(
            records=transaction_records,
            return_models=False,
        )
        assert False, "Should have raised exception"
    except Exception as e:
        # Verify it's an integrity error
        assert isinstance(e, IntegrityError)

    # Verify that none of the records were inserted (transaction rollback)
    async with async_session() as session:
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_unique_models WHERE code LIKE 'TX-%'"
        )
        assert result.scalar() == 0

    # Test error callback
    error_records = []
    success_records = []

    def error_callback(record, error):
        error_records.append((record, error))
        return False  # Don't retry

    def success_callback(record, result):
        success_records.append((record, result))
        return True

    # Configure callbacks
    callbacks = ResultCallback(on_error=error_callback, on_success=success_callback)

    # Create test records with mix of valid and invalid
    callback_records = [
        {
            "code": "CB-1",
            "name": "Callback 1",
            "created_at": datetime.utcnow(),
        },
        {
            "code": "CODE-1",  # Will fail
            "name": "Callback Fail 1",
            "created_at": datetime.utcnow(),
        },
        {
            "code": "CB-2",
            "name": "Callback 2",
            "created_at": datetime.utcnow(),
        },
        {
            "code": "CODE-2",  # Will fail
            "name": "Callback Fail 2",
            "created_at": datetime.utcnow(),
        },
    ]

    # Configure to continue on error
    unique_batch_operations.batch_config.continue_on_error = True
    unique_batch_operations.batch_config.use_transaction = False

    # Insert with callbacks
    try:
        await unique_batch_operations.batch_insert(
            records=callback_records, return_models=False, callbacks=callbacks
        )
        assert False, "Should have raised BatchError"
    except BatchError as e:
        # Verify error and callback behavior
        assert len(e.errors) == 2
        assert e.successful_count == 2

        # Verify callbacks were called
        assert len(error_records) == 2
        assert len(success_records) == 2

    # Verify successful inserts
    async with async_session() as session:
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_unique_models WHERE code IN ('CB-1', 'CB-2')"
        )
        assert result.scalar() == 2


@pytest.mark.asyncio
async def test_batch_transaction_management(
    batch_operations, detail_batch_operations, sequential_batch_config
):
    """Test transaction management for batch operations."""
    # Create batch operations with transaction support
    transactional_batch_ops = BatchOperations(
        model_class=TestModel,
        session=batch_operations.session,
        batch_config=sequential_batch_config,
    )

    # Enable transaction support
    transactional_batch_ops.batch_config.use_transaction = True

    # Create parent records
    parent_records = [
        {
            "name": f"TX Parent {i}",
            "description": f"Transaction parent {i}",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(1, 4)  # 3 parent records
    ]

    # Insert with transaction
    parent_result = await transactional_batch_ops.batch_insert(
        records=parent_records,
        return_models=True,
    )

    assert len(parent_result) == 3
    parent_ids = [p.id for p in parent_result]

    # Create detail batch ops with transaction support
    transactional_detail_ops = BatchOperations(
        model_class=TestDetailModel,
        session=detail_batch_operations.session,
        batch_config=sequential_batch_config,
    )

    # Enable transaction support
    transactional_detail_ops.batch_config.use_transaction = True

    # Now create detail records for each parent
    detail_records = []
    for parent_id in parent_ids:
        # Each parent gets 3 detail records
        for i in range(1, 4):
            detail_records.append(
                {
                    "parent_id": parent_id,
                    "key": f"TX Key {i}",
                    "value": f"TX Value {i} for parent {parent_id}",
                    "created_at": datetime.utcnow(),
                }
            )

    # Insert details with transaction
    detail_result = await transactional_detail_ops.batch_insert(
        records=detail_records,
        return_models=False,
    )

    assert detail_result == 9  # 3 parents * 3 details

    # Now create an invalid transaction that should be rolled back
    # Create a detail without a valid parent_id to cause a foreign key error
    invalid_details = [
        {
            "parent_id": 9999,  # Non-existent parent
            "key": "Invalid Key",
            "value": "Invalid Value",
            "created_at": datetime.utcnow(),
        }
    ]

    # Try to insert invalid details
    try:
        await transactional_detail_ops.batch_insert(
            records=invalid_details,
            return_models=False,
        )
        assert False, "Should have raised a foreign key error"
    except Exception as e:
        # Expect a foreign key constraint error
        assert (
            "foreign key constraint" in str(e).lower()
            or "fk constraint" in str(e).lower()
        )

    # Verify that all previous operations succeeded but the invalid one was rolled back
    async with async_session() as session:
        # Check parents
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_models WHERE name LIKE 'TX Parent%'"
        )
        assert result.scalar() == 3

        # Check valid details
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_details WHERE key LIKE 'TX Key%'"
        )
        assert result.scalar() == 9

        # Check invalid details didn't get inserted
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_details WHERE key = 'Invalid Key'"
        )
        assert result.scalar() == 0


@pytest.mark.asyncio
async def test_multi_table_batch_operations(
    batch_operations, detail_batch_operations, tag_batch_operations
):
    """Test batch operations across multiple related tables."""
    # First, create parent records
    parent_records = [
        {
            "name": f"Parent {i}",
            "description": f"Description for parent {i}",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(1, 6)  # 5 parent records
    ]

    # Insert parent records
    parent_result = await batch_operations.batch_insert(
        records=parent_records,
        return_models=True,  # Get the models to use their IDs
    )

    # Verify parent records
    assert len(parent_result) == 5
    parent_ids = [p.id for p in parent_result]

    # Now create detail records for each parent
    detail_records = []
    for parent_id in parent_ids:
        # Each parent gets 3 detail records
        for i in range(1, 4):
            detail_records.append(
                {
                    "parent_id": parent_id,
                    "key": f"Key {i}",
                    "value": f"Value {i} for parent {parent_id}",
                    "created_at": datetime.utcnow(),
                }
            )

    # Insert detail records
    detail_result = await detail_batch_operations.batch_insert(
        records=detail_records,
        return_models=False,
    )

    # Verify detail records
    assert detail_result == 15  # 5 parents * 3 details

    # Create tags
    tag_records = [
        {
            "name": f"Tag {i}",
            "description": f"Description for tag {i}",
            "created_at": datetime.utcnow(),
        }
        for i in range(1, 6)  # 5 tags
    ]

    # Insert tags
    tag_result = await tag_batch_operations.batch_insert(
        records=tag_records,
        return_models=True,
    )

    # Verify tags
    assert len(tag_result) == 5
    tag_ids = [t.id for t in tag_result]

    # Now verify the entire structure with a join query
    async with async_session() as session:
        # Query parents with their details
        result = await session.execute(
            """
            SELECT m.id, m.name, COUNT(d.id) AS detail_count
            FROM test_batch_models m
            LEFT JOIN test_batch_details d ON m.id = d.parent_id
            GROUP BY m.id, m.name
            ORDER BY m.id
        """
        )

        parent_detail_counts = list(result.mappings())

        # Verify each parent has 3 details
        assert len(parent_detail_counts) == 5
        for pdc in parent_detail_counts:
            assert pdc["detail_count"] == 3

    # Test batch updates across tables
    # Update first 3 parents
    parent_updates = [
        {
            "id": parent_ids[i],
            "name": f"Updated Parent {parent_ids[i]}",
            "updated_at": datetime.utcnow(),
        }
        for i in range(3)
    ]

    update_result = await batch_operations.batch_update(
        records=parent_updates,
        id_field="id",
        fields_to_update=["name", "updated_at"],
        return_models=False,
    )

    assert update_result == 3

    # Get detail IDs for first parent
    async with async_session() as session:
        result = await session.execute(
            "SELECT id FROM test_batch_details WHERE parent_id = :parent_id",
            {"parent_id": parent_ids[0]},
        )
        detail_ids = [row[0] for row in result.fetchall()]

    # Update details for first parent
    detail_updates = [
        {
            "id": detail_id,
            "value": f"Updated value for detail {detail_id}",
        }
        for detail_id in detail_ids
    ]

    detail_update_result = await detail_batch_operations.batch_update(
        records=detail_updates,
        id_field="id",
        fields_to_update=["value"],
        return_models=False,
    )

    assert detail_update_result == 3

    # Verify the updates
    async with async_session() as session:
        # Check parent updates
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_models WHERE name LIKE 'Updated Parent%'"
        )
        assert result.scalar() == 3

        # Check detail updates
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_details WHERE value LIKE 'Updated value%'"
        )
        assert result.scalar() == 3

    # Test batch deletion across tables
    # Delete the last 2 parents (this should cascade to their details)
    delete_parent_ids = parent_ids[3:5]

    delete_result = await batch_operations.batch_delete(
        id_values=delete_parent_ids,
        return_models=False,
    )

    assert delete_result == 2

    # Verify cascading deletion of details
    async with async_session() as session:
        # Check parents were deleted
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_models WHERE id IN :ids",
            {"ids": tuple(delete_parent_ids)},
        )
        assert result.scalar() == 0

        # Check details were cascaded
        result = await session.execute(
            "SELECT COUNT(*) FROM test_batch_details WHERE parent_id IN :ids",
            {"ids": tuple(delete_parent_ids)},
        )
        assert result.scalar() == 0

        # Check remaining records
        result = await session.execute("SELECT COUNT(*) FROM test_batch_models")
        assert result.scalar() == 3

        result = await session.execute("SELECT COUNT(*) FROM test_batch_details")
        assert result.scalar() == 9  # 3 parents * 3 details


@pytest.mark.asyncio
async def test_batch_operations_performance(
    optimized_batch_config, batch_config, sequential_batch_config, database
):
    """Test performance characteristics of different batch operation strategies."""
    # Create batch operations with different configurations
    optimized_ops = BatchOperations(
        model_class=TestModel,
        session=database,
        batch_config=optimized_batch_config,  # Parallel with larger batch size
    )

    standard_ops = BatchOperations(
        model_class=TestModel,
        session=database,
        batch_config=batch_config,  # Chunked with medium batch size
    )

    sequential_ops = BatchOperations(
        model_class=TestModel,
        session=database,
        batch_config=sequential_batch_config,  # Sequential with small batch size
    )

    # Generate a large number of records for performance testing
    num_records = 100
    records = [
        {
            "name": f"Performance Test {i}",
            "description": f"Test record for performance benchmarking {i}",
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(1, num_records + 1)
    ]

    # Test insertion performance for each strategy
    strategies = {
        "Optimized (Parallel)": optimized_ops,
        "Standard (Chunked)": standard_ops,
        "Sequential": sequential_ops,
    }

    performance_results = {}
    for strategy_name, ops in strategies.items():
        # Clean up previous records
        await database.execute(
            "DELETE FROM test_batch_models WHERE name LIKE 'Performance Test%'"
        )
        await database.commit()

        # Measure insertion time
        start_time = time.time()
        result = await ops.batch_insert(
            records=records,
            return_models=False,
        )
        end_time = time.time()

        assert result == num_records

        # Record performance
        insertion_time = end_time - start_time
        performance_results[strategy_name] = {
            "insertion_time": insertion_time,
            "records_per_second": num_records / insertion_time,
            "batch_config": ops.batch_config,
        }

    # Log performance results
    print("\nBatch Operations Performance Results:")
    for strategy_name, metrics in performance_results.items():
        print(f"  {strategy_name}:")
        print(f"    Insertion time: {metrics['insertion_time']:.4f} seconds")
        print(f"    Records per second: {metrics['records_per_second']:.2f}")
        print(f"    Batch size: {metrics['batch_config'].batch_size}")
        print(f"    Workers: {metrics['batch_config'].max_workers}")

    # Test update performance
    print("\nBatch Update Performance:")

    # Get IDs for existing records
    result = await database.execute(
        "SELECT id FROM test_batch_models WHERE name LIKE 'Performance Test%'"
    )
    record_ids = [row[0] for row in result.fetchall()[:num_records]]

    # Create update records
    update_records = [
        {
            "id": record_id,
            "status": "updated",
            "description": f"Updated performance test record {i}",
            "updated_at": datetime.utcnow(),
        }
        for i, record_id in enumerate(record_ids, 1)
    ]

    # Measure update performance for each strategy
    for strategy_name, ops in strategies.items():
        start_time = time.time()
        result = await ops.batch_update(
            records=update_records,
            id_field="id",
            fields_to_update=["status", "description", "updated_at"],
            return_models=False,
        )
        end_time = time.time()

        assert result == num_records

        update_time = end_time - start_time
        print(f"  {strategy_name}:")
        print(f"    Update time: {update_time:.4f} seconds")
        print(f"    Records per second: {num_records / update_time:.2f}")

    # Retrieve the metrics for each strategy
    # (Metrics are collected if collect_metrics=True in BatchConfig)
    for strategy_name, ops in strategies.items():
        metrics = ops.get_metrics()
        print(f"\n  {strategy_name} Metrics:")
        print(f"    Total operations: {metrics.total_operations}")
        print(f"    Successful operations: {metrics.successful_operations}")
        print(f"    Failed operations: {metrics.failed_operations}")
        print(
            f"    Average operation time: {metrics.average_operation_time:.6f} seconds"
        )

        # Additional metrics may be available depending on implementation

    # Performance assertions
    # These assertions help ensure that the optimized strategy is actually faster
    # than the sequential strategy, but they're flexible enough to account for
    # potential variations in test environments
    assert (
        performance_results["Optimized (Parallel)"]["insertion_time"]
        < performance_results["Sequential"]["insertion_time"]
    ), "Optimized parallel strategy should be faster than sequential"
