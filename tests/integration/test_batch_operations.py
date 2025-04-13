"""
Integration tests for batch operations.

These tests verify that batch operations work correctly with a real database.
"""

import asyncio
import pytest
import random
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from uno.model import Model
from uno.domain.repository import UnoDBRepository
from uno.domain.core import Entity
from uno.queries.batch_operations import (
    BatchOperations,
    BatchConfig,
    BatchExecutionStrategy,
    BatchSize,
)


# Create test models
Base = declarative_base()


class TestModel(Base, Model):
    __tablename__ = 'test_batch_models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create domain entity
class TestEntity(Entity):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Map to model class
    __uno_model__ = TestModel


@pytest.fixture(scope="module")
async def database():
    """Create a test database connection."""
    # Create engine
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
        echo=False,
    )
    
    # Create session factory
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        # Drop table if it exists
        await conn.run_sync(Base.metadata.drop_all)
        # Create table
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a session to use
    async with async_session() as session:
        yield session
    
    # Drop table after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Dispose engine
    await engine.dispose()


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
def repository(database):
    """Create a repository for the test entity."""
    return UnoDBRepository(TestEntity, use_batch_operations=True, batch_size=10)


@pytest.fixture
def batch_operations(database, batch_config):
    """Create batch operations for the test model."""
    return BatchOperations(
        model_class=TestModel,
        session=database,
        batch_config=batch_config,
    )


@pytest.mark.asyncio
async def test_batch_insert(batch_operations):
    """Test batch insert operations."""
    # Generate test records
    records = [
        {
            'name': f'Test {i}',
            'description': f'Description for test {i}',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
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
            'id': i,
            'name': f'Updated {i}',
            'description': f'Updated description for test {i}',
            'updated_at': datetime.utcnow(),
        }
        for i in range(1, 26)  # Update first 25 records
    ]
    
    # Update records
    result = await batch_operations.batch_update(
        records=updates,
        id_field='id',
        fields_to_update=['name', 'description', 'updated_at'],
        return_models=False,
    )
    
    # Check result
    assert result == 25
    
    # Verify records were updated
    models = await batch_operations.batch_get(
        id_values=list(range(1, 26)),
    )
    
    assert all(model.name.startswith('Updated') for model in models)


@pytest.mark.asyncio
async def test_batch_upsert(batch_operations):
    """Test batch upsert operations."""
    # Create records for upsert (mix of new and existing)
    upserts = []
    
    # Update existing records
    for i in range(1, 11):
        upserts.append({
            'id': i,
            'name': f'Upserted {i}',
            'description': f'Upserted description for test {i}',
            'updated_at': datetime.utcnow(),
        })
    
    # New records
    for i in range(51, 61):
        upserts.append({
            'name': f'New {i}',
            'description': f'New description for test {i}',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        })
    
    # Perform upsert
    result = await batch_operations.batch_upsert(
        records=upserts,
        constraint_columns=['id'],
        return_models=False,
    )
    
    # Check result (should be 20 - 10 updated, 10 inserted)
    assert result == 20
    
    # Verify records were upserted
    # Get updated records
    updated_models = await batch_operations.batch_get(
        id_values=list(range(1, 11)),
    )
    
    assert all(model.name.startswith('Upserted') for model in updated_models)
    
    # Get new records
    new_models = await batch_operations.batch_get(
        id_values=list(range(51, 61)),
    )
    
    assert len(new_models) == 10
    assert all(model.name.startswith('New') for model in new_models)


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
            name=f'Entity {i}',
            description=f'Description for entity {i}',
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
        entity.name = f'Updated {entity.name}'
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
    remaining_entities = await repository.batch_get([str(i + 100) for i in range(1, 21)])
    
    # Should have 10 entities left, all with updated names
    assert len(remaining_entities) == 10
    assert all(entity.name.startswith('Updated') for entity in remaining_entities)