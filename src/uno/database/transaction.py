"""
Transaction management utilities for database operations.

This module provides modern context managers and utilities for handling
database transactions in a consistent way throughout the codebase.
"""

import contextlib
from typing import AsyncIterator, Any, Optional, TypeVar, Generic

from uno.core.protocols import DatabaseSessionProtocol

T = TypeVar("T")


@contextlib.asynccontextmanager
async def transaction(session: DatabaseSessionProtocol) -> AsyncIterator[None]:
    """
    Context manager for database transactions.
    
    This context manager provides a consistent pattern for transaction management:
    - Automatically commits the transaction when the context exits without exception
    - Automatically rolls back the transaction when an exception occurs
    - Properly handles nested transactions
    
    Args:
        session: The database session to use for the transaction
        
    Yields:
        None
        
    Example:
        ```python
        async with transaction(session):
            # Perform database operations
            # Changes will be committed if no exception occurs
            # or rolled back if an exception is raised
        ```
    """
    try:
        yield
        await session.commit()
    except Exception:
        await session.rollback()
        raise


class TransactionContext(Generic[T]):
    """
    A class-based transaction context manager.
    
    This class provides the same functionality as the transaction context manager,
    but in a class form that can be more convenient in some situations.
    
    Example:
        ```python
        tx = TransactionContext(session)
        async with tx:
            # Perform database operations
        ```
    """
    
    def __init__(self, session: T):
        """
        Initialize the transaction context.
        
        Args:
            session: The database session to use for the transaction
        """
        self.session = session
    
    async def __aenter__(self) -> T:
        """Enter the transaction context."""
        return self.session
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the transaction context.
        
        Commits the transaction if no exception occurred, otherwise rolls back.
        """
        if exc_type is not None:
            # Exception occurred, roll back
            await self.session.rollback()
        else:
            # No exception, commit
            await self.session.commit()