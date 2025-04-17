"""
Example demonstrating batch operations for common database patterns.

This example shows how to use the batch operations module to efficiently
perform bulk database operations with PostgreSQL.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional, Union

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from uno.model import Model
from uno.queries.batch_operations import (
    BatchOperations,
    BatchConfig,
    BatchExecutionStrategy,
    BatchSize,
)


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create models
Base = declarative_base()


class User(Base, Model):
    """User model for demonstration."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC), onupdate=lambda: datetime.now(datetime.UTC))

    # Relationships
    posts = relationship("Post", back_populates="author")


class Post(Base, Model):
    """Post model for demonstration."""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC), onupdate=lambda: datetime.now(datetime.UTC))

    # Relationships
    author = relationship("User", back_populates="posts")


class Comment(Base, Model):
    """Comment model for demonstration."""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC))

    # Relationships
    author = relationship("User")
    post = relationship("Post")


async def setup_database():
    """Set up the database connection and create tables."""
    # Create engine
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/batch_example",
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
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    return engine, async_session


@dataclass
class BatchOperationResult:
    """Result of a batch operation."""

    name: str
    strategy: str
    batch_size: int
    record_count: int
    elapsed_time: float
    operations_per_second: float
    successful: int
    failed: int

    def __str__(self):
        return (
            f"{self.name} ({self.strategy} with batch size {self.batch_size}):\n"
            f"  - {self.record_count} records in {self.elapsed_time:.2f}s\n"
            f"  - {self.operations_per_second:.2f} ops/s\n"
            f"  - {self.successful} successful, {self.failed} failed"
        )


async def demonstrate_batch_insert(session: AsyncSession) -> BatchOperationResult:
    """Demonstrate batch insert operations."""
    logger.info("Demonstrating batch insert...")

    # Create batch operations for User model
    batch_config = BatchConfig(
        batch_size=BatchSize.LARGE.value,
        execution_strategy=BatchExecutionStrategy.CHUNKED,
        collect_metrics=True,
        log_progress=True,
    )

    batch_ops = BatchOperations(
        model_class=User,
        session=session,
        batch_config=batch_config,
    )

    # Generate test users
    users = [
        {
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "full_name": f"User {i}",
            "is_active": True,
            "created_at": datetime.now(datetime.UTC),
            "updated_at": datetime.now(datetime.UTC),
        }
        for i in range(1, 1001)  # 1000 users
    ]

    # Measure time
    start_time = time.time()

    # Insert users in batch
    result = await batch_ops.batch_insert(
        records=users,
        return_models=False,
    )

    elapsed_time = time.time() - start_time

    # Create result summary
    return BatchOperationResult(
        name="Batch Insert",
        strategy=batch_config.execution_strategy.value,
        batch_size=batch_config.batch_size,
        record_count=len(users),
        elapsed_time=elapsed_time,
        operations_per_second=len(users) / elapsed_time if elapsed_time > 0 else 0,
        successful=result,
        failed=0,
    )


async def demonstrate_batch_get(session: AsyncSession) -> BatchOperationResult:
    """Demonstrate batch get operations."""
    logger.info("Demonstrating batch get...")

    # Create batch operations for User model
    batch_config = BatchConfig(
        batch_size=BatchSize.LARGE.value,
        execution_strategy=BatchExecutionStrategy.PARALLEL,
        max_workers=4,
        collect_metrics=True,
        log_progress=True,
    )

    batch_ops = BatchOperations(
        model_class=User,
        session=session,
        batch_config=batch_config,
    )

    # Generate IDs to retrieve
    ids = list(range(1, 501))  # 500 users

    # Measure time
    start_time = time.time()

    # Get users in batch
    users = await batch_ops.batch_get(
        id_values=ids,
        load_relations=False,
        parallel=True,
    )

    elapsed_time = time.time() - start_time

    # Create result summary
    return BatchOperationResult(
        name="Batch Get",
        strategy=batch_config.execution_strategy.value,
        batch_size=batch_config.batch_size,
        record_count=len(ids),
        elapsed_time=elapsed_time,
        operations_per_second=len(ids) / elapsed_time if elapsed_time > 0 else 0,
        successful=len(users),
        failed=len(ids) - len(users),
    )


async def demonstrate_batch_update(session: AsyncSession) -> BatchOperationResult:
    """Demonstrate batch update operations."""
    logger.info("Demonstrating batch update...")

    # Create batch operations for User model
    batch_config = BatchConfig(
        batch_size=BatchSize.MEDIUM.value,
        execution_strategy=BatchExecutionStrategy.CHUNKED,
        collect_metrics=True,
        log_progress=True,
    )

    batch_ops = BatchOperations(
        model_class=User,
        session=session,
        batch_config=batch_config,
    )

    # Generate updates
    updates = [
        {
            "id": i,
            "full_name": f"Updated User {i}",
            "updated_at": datetime.now(datetime.UTC),
        }
        for i in range(1, 501)  # 500 users
    ]

    # Measure time
    start_time = time.time()

    # Update users in batch
    result = await batch_ops.batch_update(
        records=updates,
        id_field="id",
        fields_to_update=["full_name", "updated_at"],
        return_models=False,
    )

    elapsed_time = time.time() - start_time

    # Create result summary
    return BatchOperationResult(
        name="Batch Update",
        strategy=batch_config.execution_strategy.value,
        batch_size=batch_config.batch_size,
        record_count=len(updates),
        elapsed_time=elapsed_time,
        operations_per_second=len(updates) / elapsed_time if elapsed_time > 0 else 0,
        successful=result,
        failed=len(updates) - result,
    )


async def demonstrate_batch_upsert(session: AsyncSession) -> BatchOperationResult:
    """Demonstrate batch upsert operations."""
    logger.info("Demonstrating batch upsert...")

    # Create batch operations for User model
    batch_config = BatchConfig(
        batch_size=BatchSize.LARGE.value,
        execution_strategy=BatchExecutionStrategy.OPTIMISTIC,
        collect_metrics=True,
        log_progress=True,
    )

    batch_ops = BatchOperations(
        model_class=User,
        session=session,
        batch_config=batch_config,
    )

    # Generate records with mix of new and existing
    records = []

    # Updates to existing users
    for i in range(1, 101):
        records.append(
            {
                "id": i,
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "full_name": f"Updated User {i}",
                "is_active": True,
                "updated_at": datetime.now(datetime.UTC),
            }
        )

    # New users
    for i in range(1001, 1101):
        records.append(
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "full_name": f"User {i}",
                "is_active": True,
                "created_at": datetime.now(datetime.UTC),
                "updated_at": datetime.now(datetime.UTC),
            }
        )

    # Measure time
    start_time = time.time()

    # Upsert users in batch
    result = await batch_ops.batch_upsert(
        records=records,
        constraint_columns=["username"],
        return_models=False,
    )

    elapsed_time = time.time() - start_time

    # Create result summary
    return BatchOperationResult(
        name="Batch Upsert",
        strategy=batch_config.execution_strategy.value,
        batch_size=batch_config.batch_size,
        record_count=len(records),
        elapsed_time=elapsed_time,
        operations_per_second=len(records) / elapsed_time if elapsed_time > 0 else 0,
        successful=result,
        failed=len(records) - result,
    )


async def demonstrate_batch_delete(session: AsyncSession) -> BatchOperationResult:
    """Demonstrate batch delete operations."""
    logger.info("Demonstrating batch delete...")

    # Create batch operations for User model
    batch_config = BatchConfig(
        batch_size=BatchSize.LARGE.value,
        execution_strategy=BatchExecutionStrategy.CHUNKED,
        collect_metrics=True,
        log_progress=True,
    )

    batch_ops = BatchOperations(
        model_class=User,
        session=session,
        batch_config=batch_config,
    )

    # Generate IDs to delete
    ids = list(range(501, 751))  # 250 users

    # Measure time
    start_time = time.time()

    # Delete users in batch
    result = await batch_ops.batch_delete(
        id_values=ids,
        return_models=False,
    )

    elapsed_time = time.time() - start_time

    # Create result summary
    return BatchOperationResult(
        name="Batch Delete",
        strategy=batch_config.execution_strategy.value,
        batch_size=batch_config.batch_size,
        record_count=len(ids),
        elapsed_time=elapsed_time,
        operations_per_second=len(ids) / elapsed_time if elapsed_time > 0 else 0,
        successful=result,
        failed=len(ids) - result,
    )


async def demonstrate_batch_import(session: AsyncSession) -> BatchOperationResult:
    """Demonstrate batch import operations."""
    logger.info("Demonstrating batch import...")

    # Create batch operations for Post model
    batch_config = BatchConfig(
        batch_size=BatchSize.MEDIUM.value,
        execution_strategy=BatchExecutionStrategy.CHUNKED,
        collect_metrics=True,
        log_progress=True,
    )

    batch_ops = BatchOperations(
        model_class=Post,
        session=session,
        batch_config=batch_config,
    )

    # Generate posts
    posts = []

    # 500 posts, 5 per user for first 100 users
    for user_id in range(1, 101):
        for i in range(1, 6):
            posts.append(
                {
                    "title": f"Post {i} by User {user_id}",
                    "content": f"This is post {i} by user {user_id}.",
                    "user_id": user_id,
                    "published": True,
                    "created_at": datetime.now(datetime.UTC),
                    "updated_at": datetime.now(datetime.UTC),
                }
            )

    # Measure time
    start_time = time.time()

    # Import posts in batch
    result = await batch_ops.batch_import(
        records=posts,
        unique_fields=["user_id", "title"],
        update_on_conflict=True,
        return_stats=True,
    )

    elapsed_time = time.time() - start_time

    # Create result summary
    return BatchOperationResult(
        name="Batch Import",
        strategy=batch_config.execution_strategy.value,
        batch_size=batch_config.batch_size,
        record_count=len(posts),
        elapsed_time=elapsed_time,
        operations_per_second=len(posts) / elapsed_time if elapsed_time > 0 else 0,
        successful=result.get("inserted", 0) + result.get("updated", 0),
        failed=result.get("errors", 0),
    )


async def demonstrate_batch_compute(session: AsyncSession) -> BatchOperationResult:
    """Demonstrate batch compute operations."""
    logger.info("Demonstrating batch compute...")

    # Create batch operations for Post model
    batch_config = BatchConfig(
        batch_size=BatchSize.LARGE.value,
        execution_strategy=BatchExecutionStrategy.PARALLEL,
        max_workers=4,
        collect_metrics=True,
        log_progress=True,
    )

    batch_ops = BatchOperations(
        model_class=Post,
        session=session,
        batch_config=batch_config,
    )

    # Generate post IDs
    post_ids = list(range(1, 501))  # 500 posts

    # Define compute function
    def compute_post_summary(post):
        """Compute a summary of a post."""
        # This would typically do some more complex processing
        words = post.content.split()
        word_count = len(words)
        title_length = len(post.title)
        return {
            "post_id": post.id,
            "title_length": title_length,
            "word_count": word_count,
            "avg_word_length": (
                sum(len(word) for word in words) / word_count if word_count > 0 else 0
            ),
        }

    # Measure time
    start_time = time.time()

    # Compute post summaries in batch
    summaries = await batch_ops.batch_compute(
        id_values=post_ids,
        compute_fn=compute_post_summary,
        load_relations=False,
        parallel=True,
    )

    elapsed_time = time.time() - start_time

    # Create result summary
    return BatchOperationResult(
        name="Batch Compute",
        strategy=batch_config.execution_strategy.value,
        batch_size=batch_config.batch_size,
        record_count=len(post_ids),
        elapsed_time=elapsed_time,
        operations_per_second=len(post_ids) / elapsed_time if elapsed_time > 0 else 0,
        successful=len(summaries),
        failed=len(post_ids) - len(summaries),
    )


async def demonstrate_batch_operations():
    """Demonstrate various batch operations."""
    # Setup database
    engine, session_factory = await setup_database()

    try:
        # Create session
        async with session_factory() as session:
            # Demonstrate operations
            results = []

            # Insert
            result = await demonstrate_batch_insert(session)
            results.append(result)
            logger.info(str(result))

            # Get
            result = await demonstrate_batch_get(session)
            results.append(result)
            logger.info(str(result))

            # Update
            result = await demonstrate_batch_update(session)
            results.append(result)
            logger.info(str(result))

            # Upsert
            result = await demonstrate_batch_upsert(session)
            results.append(result)
            logger.info(str(result))

            # Delete
            result = await demonstrate_batch_delete(session)
            results.append(result)
            logger.info(str(result))

            # Import
            result = await demonstrate_batch_import(session)
            results.append(result)
            logger.info(str(result))

            # Compute
            result = await demonstrate_batch_compute(session)
            results.append(result)
            logger.info(str(result))

            # Commit changes
            await session.commit()

            # Display summary
            logger.info("\n=== Batch Operations Summary ===")
            for result in results:
                logger.info(str(result))

    finally:
        # Close engine
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(demonstrate_batch_operations())
