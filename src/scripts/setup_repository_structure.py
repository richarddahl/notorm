#!/usr/bin/env python
"""
Setup Repository Structure

This script creates the target directory structure for the UNO framework
according to the architectural plan. It creates empty __init__.py files
to establish the package structure.

Usage:
    python setup_repository_structure.py [--dry-run]

Options:
    --dry-run    Show what would be created without making changes
"""

import argparse
import os
from pathlib import Path
from typing import List, Tuple

# Base directory for the project
BASE_DIR = Path("src/uno")

# Directory structure to create
DIRECTORY_STRUCTURE = [
    # Core layer
    "core/protocols",
    "core/errors",
    "core/config",
    "core/utils",
    "core/async",
    # Domain layer
    "domain/common/entities",
    "domain/common/value_objects",
    "domain/common/specifications",
    "domain/attributes",
    "domain/values",
    "domain/meta",
    "domain/vector_search",
    # Application layer
    "application/common",
    "application/attributes",
    "application/values",
    "application/workflows",
    "application/jobs",
    # Infrastructure layer
    "infrastructure/persistence",
    "infrastructure/persistence/repositories",
    "infrastructure/messaging",
    "infrastructure/messaging/adapters",
    "infrastructure/events",
    "infrastructure/di",
    "infrastructure/serialization",
    # Interface layer
    "interface/api/base",
    "interface/api/attributes",
    "interface/api/values",
    "interface/api/auth",
    "interface/cli",
    "interface/fastapi",
    # Cross-cutting layer
    "crosscutting/logging",
    "crosscutting/monitoring",
    "crosscutting/security",
    "crosscutting/validation",
]

# Initial files to create with basic content
INITIAL_FILES = [
    # Core protocols
    (
        "core/protocols/repository.py",
        """
\"\"\"Repository Protocol Definition\"\"\"
from typing import Generic, TypeVar, List, Optional, Any

T = TypeVar('T')
ID = TypeVar('ID')

class RepositoryProtocol(Generic[T, ID]):
    \"\"\"Base repository protocol for data access operations.\"\"\"
    
    async def get_by_id(self, id: ID) -> Optional[T]:
        \"\"\"Retrieve an entity by its ID.\"\"\"
        ...
    
    async def find_all(self) -> list[T]:
        \"\"\"Retrieve all entities.\"\"\"
        ...
    
    async def save(self, entity: T) -> T:
        \"\"\"Save an entity (create or update).\"\"\"
        ...
    
    async def delete(self, entity: T) -> None:
        \"\"\"Delete an entity.\"\"\"
        ...
    
    async def delete_by_id(self, id: ID) -> None:
        \"\"\"Delete an entity by its ID.\"\"\"
        ...
""",
    ),
    (
        "core/protocols/service.py",
        """
\"\"\"Service Protocol Definition\"\"\"
from typing import Generic, TypeVar, List, Optional, Any
from uno.core.errors.result import Result

T = TypeVar('T')
ID = TypeVar('ID')

class ServiceProtocol(Generic[T, ID]):
    \"\"\"Base service protocol for business operations.\"\"\"
    
    async def get_by_id(self, id: ID) -> Result[T]:
        \"\"\"Retrieve an entity by its ID.\"\"\"
        ...
    
    async def get_all(self) -> Result[list[T]]:
        \"\"\"Retrieve all entities.\"\"\"
        ...
    
    async def create(self, data: Any) -> Result[T]:
        \"\"\"Create a new entity.\"\"\"
        ...
    
    async def update(self, id: ID, data: Any) -> Result[T]:
        \"\"\"Update an existing entity.\"\"\"
        ...
    
    async def delete(self, id: ID) -> Result[None]:
        \"\"\"Delete an entity.\"\"\"
        ...
""",
    ),
    (
        "core/protocols/event.py",
        """
\"\"\"Event Protocol Definitions\"\"\"
from typing import Any, Dict, Generic, List, TypeVar, Protocol
from datetime import datetime

T = TypeVar('T')

class EventProtocol(Protocol):
    \"\"\"Base protocol for domain events.\"\"\"
    
    @property
    def event_id(self) -> str:
        \"\"\"Unique identifier for this event.\"\"\"
        ...
    
    @property
    def event_type(self) -> str:
        \"\"\"Type of this event.\"\"\"
        ...
    
    @property
    def occurred_at(self) -> datetime:
        \"\"\"When this event occurred.\"\"\"
        ...
    
    @property
    def data(self) -> dict[str, Any]:
        \"\"\"Event payload data.\"\"\"
        ...

class EventBusProtocol(Protocol):
    \"\"\"Protocol for event publishing and subscription.\"\"\"
    
    async def publish(self, event: EventProtocol) -> None:
        \"\"\"Publish an event to subscribers.\"\"\"
        ...
    
    async def subscribe(self, event_type: str, handler: Any) -> None:
        \"\"\"Subscribe to events of a specific type.\"\"\"
        ...
    
    async def unsubscribe(self, event_type: str, handler: Any) -> None:
        \"\"\"Unsubscribe from events of a specific type.\"\"\"
        ...
""",
    ),
    (
        "core/protocols/entity.py",
        """
\"\"\"Entity Protocol Definition\"\"\"
from typing import TypeVar, Generic, Protocol, Any

ID = TypeVar('ID')

class EntityProtocol(Protocol, Generic[ID]):
    \"\"\"Base protocol for domain entities.\"\"\"
    
    @property
    def id(self) -> ID:
        \"\"\"The unique identifier of the entity.\"\"\"
        ...
    
    def __eq__(self, other: Any) -> bool:
        \"\"\"Equal if IDs are equal.\"\"\"
        ...
    
    def __hash__(self) -> int:
        \"\"\"Hash based on ID.\"\"\"
        ...
""",
    ),
    (
        "core/protocols/__init__.py",
        """
\"\"\"Core Protocol Definitions

This package contains the core protocol interfaces that define
the contracts for the major components of the system.
\"\"\"

from uno.core.protocols.repository import RepositoryProtocol
from uno.core.protocols.service import ServiceProtocol
from uno.core.protocols.event import EventProtocol, EventBusProtocol
from uno.core.protocols.entity import EntityProtocol

__all__ = [
    'RepositoryProtocol',
    'ServiceProtocol',
    'EventProtocol',
    'EventBusProtocol',
    'EntityProtocol',
]
""",
    ),
    # Error framework
    (
        "core/errors/result.py",
        """
\"\"\"Result Pattern Implementation\"\"\"
from typing import Generic, TypeVar, Optional, List, Dict, Any, Union, Callable

T = TypeVar('T')
E = TypeVar('E')

class Result(Generic[T, E]):
    \"\"\"
    A container for return values or errors.
    
    This class implements the Result pattern, providing a way to
    handle errors without exceptions.
    \"\"\"
    
    def __init__(
        self, 
        value: Optional[T] = None, 
        error: Optional[E] = None,
        errors: Optional[list[E]] = None
    ):
        self._value = value
        self._error = error
        self._errors = errors or []
        
        if error:
            self._errors.append(error)
        
        self._is_success = not self._errors
    
    @property
    def is_success(self) -> bool:
        \"\"\"Whether the operation was successful.\"\"\"
        return self._is_success
    
    @property
    def is_failure(self) -> bool:
        \"\"\"Whether the operation failed.\"\"\"
        return not self._is_success
    
    @property
    def value(self) -> Optional[T]:
        \"\"\"The result value, if successful.\"\"\"
        return self._value
    
    @property
    def error(self) -> Optional[E]:
        \"\"\"The first error, if any.\"\"\"
        return self._errors[0] if self._errors else None
    
    @property
    def errors(self) -> list[E]:
        \"\"\"All errors.\"\"\"
        return self._errors.copy()
    
    def map(self, fn: Callable[[T], Any]) -> 'Result':
        \"\"\"Apply a function to the value if successful.\"\"\"
        if self.is_success:
            return Result(value=fn(self._value))
        return Result(errors=self._errors)
    
    def bind(self, fn: Callable[[T], 'Result']) -> 'Result':
        \"\"\"Chain operations that might fail.\"\"\"
        if self.is_success:
            return fn(self._value)
        return Result(errors=self._errors)
    
    @staticmethod
    def success(value: T) -> 'Result[T, Any]':
        \"\"\"Create a successful result.\"\"\"
        return Result(value=value)
    
    @staticmethod
    def failure(error: E) -> 'Result[Any, E]':
        \"\"\"Create a failed result.\"\"\"
        return Result(error=error)
    
    @staticmethod
    def failures(errors: list[E]) -> 'Result[Any, E]':
        \"\"\"Create a failed result with multiple errors.\"\"\"
        return Result(errors=errors)
""",
    ),
    (
        "core/errors/__init__.py",
        """
\"\"\"Error Handling Framework

This package contains the error handling components used throughout the system.
\"\"\"

from uno.core.errors.result import Result

__all__ = ['Result']
""",
    ),
    # Domain base classes
    (
        "domain/common/entities/base_entity.py",
        """
\"\"\"Base Entity Definition\"\"\"
from datetime import datetime
from typing import Generic, TypeVar, List, Any, Dict, Optional
from uuid import uuid4

ID = TypeVar('ID')

class BaseEntity(Generic[ID]):
    \"\"\"
    Base class for all domain entities.
    
    Entities are objects with a distinct identity that runs through time and
    different representations. They are defined by their identity, rather than
    their attributes.
    \"\"\"
    
    def __init__(self, id: Optional[ID] = None):
        self._id = id if id is not None else str(uuid4())
        self._created_at = datetime.now()
        self._updated_at = self._created_at
        self._events: list[Any] = []
    
    @property
    def id(self) -> ID:
        \"\"\"The unique identifier of this entity.\"\"\"
        return self._id
    
    @property
    def created_at(self) -> datetime:
        \"\"\"When this entity was created.\"\"\"
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        \"\"\"When this entity was last updated.\"\"\"
        return self._updated_at
    
    def _update_timestamp(self) -> None:
        \"\"\"Update the updated_at timestamp.\"\"\"
        self._updated_at = datetime.now()
    
    def add_event(self, event: Any) -> None:
        \"\"\"Add a domain event to this entity.\"\"\"
        self._events.append(event)
    
    def clear_events(self) -> list[Any]:
        \"\"\"Clear and return all pending events.\"\"\"
        events = self._events.copy()
        self._events.clear()
        return events
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
""",
    ),
    (
        "domain/common/value_objects/base_value_object.py",
        """
\"\"\"Base Value Object Definition\"\"\"
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ValueObject:
    \"\"\"
    Base class for all value objects.
    
    Value objects are objects that matter only as the combination of their
    attributes. Two value objects with the same values are considered equal.
    \"\"\"
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
    
    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))
""",
    ),
    # Infrastructure implementation
    (
        "infrastructure/persistence/database.py",
        """
\"\"\"Database Provider Implementation\"\"\"
from typing import Any, Optional, Dict
import asyncpg
from asyncpg.pool import Pool

class DatabaseProvider:
    \"\"\"
    Provider for database connections and operations.
    \"\"\"
    
    def __init__(self, connection_string: str):
        self._connection_string = connection_string
        self._pool: Optional[Pool] = None
    
    async def initialize(self) -> None:
        \"\"\"Initialize the connection pool.\"\"\"
        if not self._pool:
            self._pool = await asyncpg.create_pool(
                dsn=self._connection_string,
                min_size=5,
                max_size=20
            )
    
    async def close(self) -> None:
        \"\"\"Close the connection pool.\"\"\"
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def execute(self, query: str, *args: Any, timeout: Optional[float] = None) -> str:
        \"\"\"Execute a query and return the status.\"\"\"
        if not self._pool:
            await self.initialize()
        
        async with self._pool.acquire() as connection:
            return await connection.execute(query, *args, timeout=timeout)
    
    async def fetch(self, query: str, *args: Any, timeout: Optional[float] = None) -> list:
        \"\"\"Execute a query and return the results.\"\"\"
        if not self._pool:
            await self.initialize()
        
        async with self._pool.acquire() as connection:
            return await connection.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args: Any, timeout: Optional[float] = None) -> dict[str, Any] | None:
        \"\"\"Execute a query and return the first row.\"\"\"
        if not self._pool:
            await self.initialize()
        
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(query, *args, timeout=timeout)
            return dict(row) if row else None
    
    async def fetchval(self, query: str, *args: Any, timeout: Optional[float] = None) -> Any:
        \"\"\"Execute a query and return a single value.\"\"\"
        if not self._pool:
            await self.initialize()
        
        async with self._pool.acquire() as connection:
            return await connection.fetchval(query, *args, timeout=timeout)
    
    async def begin(self) -> 'Transaction':
        \"\"\"Begin a transaction.\"\"\"
        if not self._pool:
            await self.initialize()
        
        connection = await self._pool.acquire()
        transaction = connection.transaction()
        await transaction.start()
        
        return Transaction(connection, transaction)

class Transaction:
    \"\"\"A database transaction.\"\"\"
    
    def __init__(self, connection: Any, transaction: Any):
        self._connection = connection
        self._transaction = transaction
    
    async def execute(self, query: str, *args: Any, timeout: Optional[float] = None) -> str:
        \"\"\"Execute a query within the transaction.\"\"\"
        return await self._connection.execute(query, *args, timeout=timeout)
    
    async def fetch(self, query: str, *args: Any, timeout: Optional[float] = None) -> list:
        \"\"\"Execute a query within the transaction and return the results.\"\"\"
        return await self._connection.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args: Any, timeout: Optional[float] = None) -> dict[str, Any] | None:
        \"\"\"Execute a query within the transaction and return the first row.\"\"\"
        row = await self._connection.fetchrow(query, *args, timeout=timeout)
        return dict(row) if row else None
    
    async def fetchval(self, query: str, *args: Any, timeout: Optional[float] = None) -> Any:
        \"\"\"Execute a query within the transaction and return a single value.\"\"\"
        return await self._connection.fetchval(query, *args, timeout=timeout)
    
    async def commit(self) -> None:
        \"\"\"Commit the transaction.\"\"\"
        await self._transaction.commit()
        await self._connection.close()
    
    async def rollback(self) -> None:
        \"\"\"Roll back the transaction.\"\"\"
        await self._transaction.rollback()
        await self._connection.close()
    
    async def __aenter__(self) -> 'Transaction':
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
""",
    ),
    (
        "infrastructure/persistence/unit_of_work.py",
        """
\"\"\"Unit of Work Implementation\"\"\"
from typing import Dict, Type, Any, Optional
from uno.infrastructure.persistence.database import DatabaseProvider, Transaction

class UnitOfWork:
    \"\"\"
    Coordinates transactions and domain events across repositories.
    \"\"\"
    
    def __init__(self, db_provider: DatabaseProvider, event_bus: Any = None):
        self._db_provider = db_provider
        self._event_bus = event_bus
        self._transaction: Optional[Transaction] = None
        self._repositories: dict[str, Any] = {}
    
    def register_repository(self, name: str, repository: Any) -> None:
        \"\"\"Register a repository with this unit of work.\"\"\"
        self._repositories[name] = repository
    
    def repository(self, name: str) -> Any:
        \"\"\"Get a repository by name.\"\"\"
        return self._repositories.get(name)
    
    async def begin(self) -> None:
        \"\"\"Begin a transaction.\"\"\"
        self._transaction = await self._db_provider.begin()
        
        # Set transaction on all repositories
        for repo in self._repositories.values():
            if hasattr(repo, 'set_transaction'):
                repo.set_transaction(self._transaction)
    
    async def commit(self) -> None:
        \"\"\"Commit the transaction and publish events.\"\"\"
        if not self._transaction:
            return
        
        # Collect domain events from repositories
        events = []
        for repo in self._repositories.values():
            if hasattr(repo, 'collect_events'):
                events.extend(repo.collect_events())
        
        # Commit the transaction
        await self._transaction.commit()
        self._transaction = None
        
        # Reset repositories
        for repo in self._repositories.values():
            if hasattr(repo, 'set_transaction'):
                repo.set_transaction(None)
        
        # Publish events
        if self._event_bus:
            for event in events:
                await self._event_bus.publish(event)
    
    async def rollback(self) -> None:
        \"\"\"Roll back the transaction.\"\"\"
        if not self._transaction:
            return
        
        await self._transaction.rollback()
        self._transaction = None
        
        # Reset repositories
        for repo in self._repositories.values():
            if hasattr(repo, 'set_transaction'):
                repo.set_transaction(None)
    
    async def __aenter__(self) -> 'UnitOfWork':
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
""",
    ),
    (
        "infrastructure/persistence/repositories/sqlalchemy_repository.py",
        """
\"\"\"SQLAlchemy Repository Implementation\"\"\"
from typing import Generic, TypeVar, List, Optional, Type, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uno.core.protocols import RepositoryProtocol
from uno.domain.common.entities.base_entity import BaseEntity

T = TypeVar('T', bound=BaseEntity)
ID = TypeVar('ID')

class SqlAlchemyRepository(Generic[T, ID], RepositoryProtocol[T, ID]):
    \"\"\"
    Repository implementation using SQLAlchemy.
    \"\"\"
    
    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self._session = session
        self._model_class = model_class
        self._transaction = None
        self._pending_events: list[Any] = []
    
    def set_transaction(self, transaction: Any) -> None:
        \"\"\"Set the current transaction.\"\"\"
        self._transaction = transaction
    
    async def get_by_id(self, id: ID) -> Optional[T]:
        \"\"\"Retrieve an entity by ID.\"\"\"
        stmt = select(self._model_class).where(self._model_class.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_all(self) -> list[T]:
        \"\"\"Retrieve all entities.\"\"\"
        stmt = select(self._model_class)
        result = await self._session.execute(stmt)
        return result.scalars().all()
    
    async def save(self, entity: T) -> T:
        \"\"\"Save an entity.\"\"\"
        # Collect events
        self._pending_events.extend(entity.clear_events())
        
        # Save the entity
        self._session.add(entity)
        await self._session.flush()
        return entity
    
    async def delete(self, entity: T) -> None:
        \"\"\"Delete an entity.\"\"\"
        await self._session.delete(entity)
        await self._session.flush()
    
    async def delete_by_id(self, id: ID) -> None:
        \"\"\"Delete an entity by ID.\"\"\"
        entity = await self.get_by_id(id)
        if entity:
            await self.delete(entity)
    
    def collect_events(self) -> list[Any]:
        \"\"\"Collect and clear pending events.\"\"\"
        events = self._pending_events.copy()
        self._pending_events.clear()
        return events
""",
    ),
]


def create_directory_structure(dry_run: bool = False) -> None:
    """Create the directory structure."""
    print("Creating directory structure...")

    # Create base directory if it doesn't exist
    if not os.path.exists(BASE_DIR) and not dry_run:
        os.makedirs(BASE_DIR)

    # Create directories
    for directory in DIRECTORY_STRUCTURE:
        dir_path = BASE_DIR / directory

        if dry_run:
            print(f"Would create directory: {dir_path}")
        else:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")

            # Create __init__.py in each directory
            init_file = dir_path / "__init__.py"
            if not os.path.exists(init_file):
                with open(init_file, "w") as f:
                    module_name = directory.replace("/", ".")
                    f.write(f'"""{module_name} module"""\n')
                print(f"Created file: {init_file}")


def create_initial_files(dry_run: bool = False) -> None:
    """Create initial files with content."""
    print("\nCreating initial files...")

    for file_path, content in INITIAL_FILES:
        full_path = BASE_DIR / file_path

        if dry_run:
            print(f"Would create file: {full_path}")
        else:
            if not os.path.exists(full_path):
                with open(full_path, "w") as f:
                    f.write(content.strip())
                print(f"Created file: {full_path}")


def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Setup UNO framework repository structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making changes",
    )

    args = parser.parse_args()

    print("UNO Framework Repository Structure Setup")
    print("=======================================")

    if args.dry_run:
        print("\nDRY RUN MODE: No changes will be made\n")

    # Create directory structure
    create_directory_structure(args.dry_run)

    # Create initial files
    create_initial_files(args.dry_run)

    print("\nSetup complete!")
    if args.dry_run:
        print("This was a dry run. Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
