"""
Context managers and decorators for the Unit of Work pattern.

This module provides utilities for working with Unit of Work instances
in various contexts, including decorators for service methods and
context managers for transaction boundaries.
"""

import inspect
import functools
import logging
from contextlib import asynccontextmanager
from typing import (
    Any, Callable, TypeVar, AsyncContextManager,
    AsyncIterator, Optional, cast, Protocol, ParamSpec,
)

from uno.core.protocols import UnitOfWork
from uno.core.uow.base import AbstractUnitOfWork

# Type variables
T = TypeVar("T")
P = ParamSpec("P")
R = TypeVar("R")

# Type aliases
UnitOfWorkFactory = Callable[[], AsyncContextManager[AbstractUnitOfWork]]


@asynccontextmanager
async def transaction(
    uow_factory: UnitOfWorkFactory,
    logger: Optional[logging.Logger] = None,
) -> AsyncIterator[AbstractUnitOfWork]:
    """
    Context manager for a transaction using a Unit of Work.
    
    This provides an async context manager that creates a new Unit of Work,
    begins a transaction, and either commits or rolls back the transaction
    when the context exits.
    
    Example:
        async with transaction(get_uow) as uow:
            # Operations within the transaction
            repo = uow.get_repository(UserRepository)
            user = await repo.get_by_id(user_id)
            user.update_email(new_email)
            await repo.update(user)
            # Transaction is automatically committed if no exception occurs
    
    Args:
        uow_factory: Factory function that creates a Unit of Work
        logger: Optional logger for diagnostics
        
    Yields:
        The Unit of Work instance
    """
    logger = logger or logging.getLogger(__name__)
    
    try:
        async with uow_factory() as uow:
            yield uow
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        raise


def unit_of_work(
    uow_factory: UnitOfWorkFactory,
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator that provides a Unit of Work for a function.
    
    This decorator wraps an async function with a Unit of Work context,
    automatically injecting the Unit of Work as a parameter if the function
    signature includes a 'uow' parameter.
    
    Example:
        @unit_of_work(get_uow)
        async def update_user_email(user_id: str, email: str, uow: UnitOfWork) -> None:
            repo = uow.get_repository(UserRepository)
            user = await repo.get_by_id(user_id)
            if user:
                user.update_email(email)
                await repo.update(user)
    
    Args:
        uow_factory: Factory function that creates a Unit of Work
        logger: Optional logger for diagnostics
        
    Returns:
        Decorated function that uses a Unit of Work
    """
    logger = logger or logging.getLogger(__name__)
    
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Check if the function expects a uow parameter
            sig = inspect.signature(func)
            needs_uow = 'uow' in sig.parameters
            
            async with transaction(uow_factory, logger) as uow:
                # Add uow to kwargs if needed
                if needs_uow and 'uow' not in kwargs:
                    kwargs = dict(kwargs)
                    kwargs['uow'] = uow
                
                # Call the function
                return await func(*args, **kwargs)
        
        return cast(Callable[P, R], wrapper)
    
    return decorator