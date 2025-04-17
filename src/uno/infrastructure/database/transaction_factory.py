"""
Transaction factory for database operations.

This module provides factory functions to create transaction context managers
for different database types and scenarios.
"""

import contextlib
from typing import Any, AsyncIterator, Callable, Optional, TypeVar

from uno.core.protocols import (
    DatabaseSessionProtocol,
    DatabaseSessionContextProtocol,
    DatabaseSessionFactoryProtocol,
)
from uno.database.transaction import transaction, TransactionContext

T = TypeVar("T")


def create_transaction_manager(
    session_factory: DatabaseSessionFactoryProtocol,
    db_role: str = "writer",
) -> Callable[[], AsyncIterator[DatabaseSessionProtocol]]:
    """
    Create a transaction manager function for a specific session factory.
    
    This factory function returns a context manager function that creates a
    session from the provided factory and wraps it in a transaction.
    
    Args:
        session_factory: The session factory to use
        db_role: The database role to use for the session
        
    Returns:
        A context manager function that yields a session within a transaction
    """
    
    @contextlib.asynccontextmanager
    async def transaction_manager() -> AsyncIterator[DatabaseSessionProtocol]:
        """
        Context manager that creates a session and manages a transaction.
        
        Yields:
            A database session within a transaction
        """
        # Get configuration for the session
        from uno.database.config import get_default_connection_config
        
        config = get_default_connection_config()
        config.db_role = db_role
        
        # Create session
        session = session_factory.create_session(config)
        
        # Use transaction context
        try:
            async with TransactionContext(session):
                yield session
        finally:
            await session.close()
    
    return transaction_manager


def create_read_transaction_manager(
    session_factory: DatabaseSessionFactoryProtocol,
) -> Callable[[], AsyncIterator[DatabaseSessionProtocol]]:
    """
    Create a read-only transaction manager.
    
    This is a convenience function that creates a transaction manager with the "reader" role.
    
    Args:
        session_factory: The session factory to use
        
    Returns:
        A context manager function that yields a read-only session
    """
    return create_transaction_manager(session_factory, db_role="reader")


def create_write_transaction_manager(
    session_factory: DatabaseSessionFactoryProtocol,
) -> Callable[[], AsyncIterator[DatabaseSessionProtocol]]:
    """
    Create a write transaction manager.
    
    This is a convenience function that creates a transaction manager with the "writer" role.
    
    Args:
        session_factory: The session factory to use
        
    Returns:
        A context manager function that yields a write session
    """
    return create_transaction_manager(session_factory, db_role="writer")


@contextlib.asynccontextmanager
async def readonly_transaction(
    session: DatabaseSessionProtocol,
) -> AsyncIterator[None]:
    """
    Context manager for read-only transactions.
    
    This is optimized for read-only operations and may use different isolation levels
    or other optimizations compared to the standard transaction manager.
    
    Args:
        session: The database session
        
    Yields:
        None
    """
    try:
        # Start transaction with read-only mode if supported by the database
        await session.execute("SET TRANSACTION READ ONLY")
        yield
        await session.commit()
    except Exception:
        await session.rollback()
        raise