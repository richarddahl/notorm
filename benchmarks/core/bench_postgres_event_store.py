"""
PostgreSQL Event Store Benchmarks

This module contains benchmarks for the PostgreSQL event store implementation.
It measures performance aspects of event persistence and retrieval.
"""

import asyncio
import uuid
import random
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, UTC, timedelta

from benchmarks.core.benchmark_runner import Benchmark, register_benchmark

# Import required UNO components
from uno.core.events import Event, PostgresEventStore, PostgresEventStoreConfig


# Define some test events
class UserCreated(Event):
    """Event indicating a user was created."""
    user_id: str
    email: str
    username: str


class UserEmailChanged(Event):
    """Event indicating a user's email was changed."""
    user_id: str
    old_email: str
    new_email: str


class UserDeactivated(Event):
    """Event indicating a user was deactivated."""
    user_id: str
    reason: Optional[str] = None


@register_benchmark
class PostgresEventStoreAppendBenchmark(Benchmark):
    """Benchmark for PostgreSQL event store event appending."""
    
    category = "events"
    name = "postgres_event_store_append"
    description = "Measures the performance of appending events to the PostgreSQL event store"
    tags = ["events", "event_store", "postgres", "core"]
    
    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Set up a PostgreSQL connection
        connection_string = os.environ.get(
            "POSTGRES_CONNECTION_STRING", 
            "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
        )
        
        # Create a unique schema for this benchmark run
        self.schema = f"bench_{uuid.uuid4().hex[:8]}"
        
        # Configure the event store
        self.config = PostgresEventStoreConfig(
            connection_string=connection_string,
            schema=self.schema,
            table_name="events",
            create_schema_if_missing=True
        )
        
        # Create the event store
        self.event_store = PostgresEventStore(config=self.config)
        
        # Initialize the store
        await self.event_store.initialize()
        
        # Generate some test aggregates
        self.aggregate_ids = [str(uuid.uuid4()) for _ in range(10)]
        
        # Generate test events factory functions
        def create_user_event(aggregate_id: str) -> Event:
            """Create a UserCreated event."""
            return UserCreated(
                event_id=str(uuid.uuid4()),
                user_id=aggregate_id,
                email=f"user_{aggregate_id[:8]}@example.com",
                username=f"user_{aggregate_id[:8]}",
                aggregate_id=aggregate_id,
                aggregate_type="User"
            )
        
        def change_email_event(aggregate_id: str) -> Event:
            """Create a UserEmailChanged event."""
            return UserEmailChanged(
                event_id=str(uuid.uuid4()),
                user_id=aggregate_id,
                old_email=f"user_{aggregate_id[:8]}@example.com",
                new_email=f"new_{aggregate_id[:8]}@example.com",
                aggregate_id=aggregate_id,
                aggregate_type="User"
            )
        
        def deactivate_user_event(aggregate_id: str) -> Event:
            """Create a UserDeactivated event."""
            return UserDeactivated(
                event_id=str(uuid.uuid4()),
                user_id=aggregate_id,
                reason="Benchmark test",
                aggregate_id=aggregate_id,
                aggregate_type="User"
            )
        
        self.event_factories = [
            create_user_event,
            change_email_event,
            deactivate_user_event
        ]
    
    async def teardown(self) -> None:
        """Clean up the benchmark environment."""
        # Clean up by dropping the schema
        try:
            async with self.event_store._engine.begin() as conn:
                await conn.execute(f"DROP SCHEMA IF EXISTS {self.schema} CASCADE")
        except Exception as e:
            self.logger.error(f"Error cleaning up benchmark schema: {e}")
    
    async def run_iteration(self) -> Dict[str, Any]:
        """Run a single benchmark iteration."""
        # Select a random aggregate
        aggregate_id = random.choice(self.aggregate_ids)
        
        # Create a set of events for this aggregate
        events = [
            factory(aggregate_id) 
            for factory in random.sample(self.event_factories, random.randint(1, 3))
        ]
        
        # Append events to the store
        start_time = asyncio.get_event_loop().time()
        version = await self.event_store.append_events(events)
        end_time = asyncio.get_event_loop().time()
        
        # Return metrics
        return {
            "events_appended": len(events),
            "aggregate_id": aggregate_id,
            "aggregate_version": version,
            "append_time": (end_time - start_time)
        }


@register_benchmark
class PostgresEventStoreRetrievalBenchmark(Benchmark):
    """Benchmark for PostgreSQL event store event retrieval."""
    
    category = "events"
    name = "postgres_event_store_retrieval"
    description = "Measures the performance of retrieving events from the PostgreSQL event store"
    tags = ["events", "event_store", "postgres", "core"]
    
    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Set up a PostgreSQL connection
        connection_string = os.environ.get(
            "POSTGRES_CONNECTION_STRING", 
            "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
        )
        
        # Create a unique schema for this benchmark run
        self.schema = f"bench_{uuid.uuid4().hex[:8]}"
        
        # Configure the event store
        self.config = PostgresEventStoreConfig(
            connection_string=connection_string,
            schema=self.schema,
            table_name="events",
            create_schema_if_missing=True
        )
        
        # Create the event store
        self.event_store = PostgresEventStore(config=self.config)
        
        # Initialize the store
        await self.event_store.initialize()
        
        # Create test aggregates and events
        self.aggregate_ids = []
        
        # Create 10 aggregates with 10 events each
        for i in range(10):
            aggregate_id = str(uuid.uuid4())
            self.aggregate_ids.append(aggregate_id)
            
            # Create events for this aggregate
            events = []
            # First event is always UserCreated
            events.append(UserCreated(
                event_id=str(uuid.uuid4()),
                user_id=aggregate_id,
                email=f"user_{i}@example.com",
                username=f"user_{i}",
                aggregate_id=aggregate_id,
                aggregate_type="User"
            ))
            
            # Add more events
            for j in range(1, 10):
                if j % 3 == 0:
                    # Email change
                    events.append(UserEmailChanged(
                        event_id=str(uuid.uuid4()),
                        user_id=aggregate_id,
                        old_email=f"user_{i}@example.com",
                        new_email=f"user_{i}_{j}@example.com",
                        aggregate_id=aggregate_id,
                        aggregate_type="User"
                    ))
                else:
                    # Deactivation (alternating with reactivation)
                    events.append(UserDeactivated(
                        event_id=str(uuid.uuid4()),
                        user_id=aggregate_id,
                        reason=f"Test reason {j}",
                        aggregate_id=aggregate_id,
                        aggregate_type="User"
                    ))
            
            # Store the events
            await self.event_store.append_events(events)
    
    async def teardown(self) -> None:
        """Clean up the benchmark environment."""
        # Clean up by dropping the schema
        try:
            async with self.event_store._engine.begin() as conn:
                await conn.execute(f"DROP SCHEMA IF EXISTS {self.schema} CASCADE")
        except Exception as e:
            self.logger.error(f"Error cleaning up benchmark schema: {e}")
    
    async def run_iteration(self) -> Dict[str, Any]:
        """Run a single benchmark iteration."""
        # Select a random aggregate
        aggregate_id = random.choice(self.aggregate_ids)
        
        # Choose a random retrieval method
        method = random.choice(["by_aggregate", "by_type", "by_both"])
        
        if method == "by_aggregate":
            # Get events by aggregate
            start_time = asyncio.get_event_loop().time()
            events = await self.event_store.get_events_by_aggregate(aggregate_id)
            end_time = asyncio.get_event_loop().time()
            
            return {
                "method": "get_events_by_aggregate",
                "aggregate_id": aggregate_id,
                "events_retrieved": len(events),
                "retrieval_time": (end_time - start_time)
            }
            
        elif method == "by_type":
            # Get events by type
            event_type = random.choice([
                "user_created", 
                "user_email_changed", 
                "user_deactivated"
            ])
            
            start_time = asyncio.get_event_loop().time()
            events = await self.event_store.get_events_by_type(event_type)
            end_time = asyncio.get_event_loop().time()
            
            return {
                "method": "get_events_by_type",
                "event_type": event_type,
                "events_retrieved": len(events),
                "retrieval_time": (end_time - start_time)
            }
            
        else:  # by_both
            # Get all events for the aggregate since yesterday
            yesterday = datetime.now(UTC) - timedelta(days=1)
            
            start_time = asyncio.get_event_loop().time()
            events = await self.event_store.get_events_by_aggregate(aggregate_id)
            end_time = asyncio.get_event_loop().time()
            
            return {
                "method": "get_events_by_aggregate_since",
                "aggregate_id": aggregate_id,
                "since": yesterday.isoformat(),
                "events_retrieved": len(events),
                "retrieval_time": (end_time - start_time)
            }