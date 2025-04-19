"""
Repository factory for the Uno framework.

This module provides factory functions for creating repositories and unit of work
instances, simplifying the creation and configuration of repositories.

DEPRECATED: The UnitOfWork functionality in this module is deprecated. Use the 
AbstractUnitOfWork, DatabaseUnitOfWork, and related classes from uno.core.uow instead.
"""

import logging
import warnings
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from uno.domain.core import Entity, AggregateRoot
from uno.domain.specifications import Specification
from uno.core.base.repository import BaseRepository
from uno.infrastructure.repositories.base import AggregateRepository
from uno.infrastructure.repositories.sqlalchemy import (
    SQLAlchemyRepository,
    SQLAlchemySpecificationRepository,
    SQLAlchemyBatchRepository,
    SQLAlchemyStreamingRepository,
    SQLAlchemyEventCollectingRepository,
    SQLAlchemyAggregateRepository,
    SQLAlchemyCompleteRepository
)
from uno.infrastructure.repositories.in_memory import (
    InMemoryRepository,
    InMemorySpecificationRepository,
    InMemoryBatchRepository,
    InMemoryStreamingRepository,
    InMemoryEventCollectingRepository,
    InMemoryAggregateRepository,
    InMemoryCompleteRepository
)

# Legacy imports marked for deprecation
from uno.infrastructure.repositories.unit_of_work import (
    UnitOfWork,
    SQLAlchemyUnitOfWork,
    InMemoryUnitOfWork
)

# Import the modern UnitOfWork implementations
from uno.core.uow import (
    AbstractUnitOfWork,
    DatabaseUnitOfWork,
    SqlAlchemyUnitOfWork as ModernSqlAlchemyUnitOfWork,
    InMemoryUnitOfWork as ModernInMemoryUnitOfWork,
)

warnings.warn(
    "The UnitOfWork functionality in this module is deprecated. "
    "Use AbstractUnitOfWork, DatabaseUnitOfWork, and related classes from uno.core.uow instead.",
    DeprecationWarning,
    stacklevel=2
)

# Type variables
T = TypeVar("T")  # Entity type
E = TypeVar("E", bound=Entity)  # Entity type with Entity constraint
A = TypeVar("A", bound=AggregateRoot)  # Aggregate type
ID = TypeVar("ID")  # ID type
M = TypeVar("M")  # Model type


class RepositoryFactory:
    """
    Factory for creating repositories.
    
    This class provides methods for creating various types of repositories,
    configured for different persistence mechanisms and capabilities.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the repository factory.
        
        Args:
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._specification_translators: Dict[Type, Any] = {}
    
    def register_specification_translator(
        self, entity_type: Type, translator: Any
    ) -> None:
        """
        Register a specification translator for an entity type.
        
        Args:
            entity_type: The entity type the translator is for
            translator: The specification translator
        """
        self._specification_translators[entity_type] = translator
        self.logger.debug(f"Registered specification translator for {entity_type.__name__}")
    
    def get_specification_translator(
        self, entity_type: Type
    ) -> Optional[Any]:
        """
        Get the specification translator for an entity type.
        
        Args:
            entity_type: The entity type to get the translator for
            
        Returns:
            The specification translator or None if not registered
        """
        return self._specification_translators.get(entity_type)
    
    def create_sqlalchemy_repository(
        self,
        entity_type: Type[T],
        session: AsyncSession,
        model_class: Type[M],
        include_specification: bool = False,
        include_batch: bool = False,
        include_streaming: bool = False,
        include_events: bool = False,
        is_aggregate: bool = False,
    ) -> BaseRepository[T, Any]:
        """
        Create a SQLAlchemy repository.
        
        Args:
            entity_type: The type of entity this repository manages
            session: SQLAlchemy async session
            model_class: SQLAlchemy model class
            include_specification: Whether to include specification support
            include_batch: Whether to include batch operation support
            include_streaming: Whether to include streaming support
            include_events: Whether to include event collection
            is_aggregate: Whether the entity is an aggregate root
            
        Returns:
            The created repository
        """
        # Get specification translator if needed
        translator = None
        if include_specification:
            translator = self.get_specification_translator(entity_type)
        
        # Create appropriate repository based on capabilities
        if is_aggregate:
            # Aggregate repository always includes event collection
            return SQLAlchemyAggregateRepository(
                entity_type=entity_type,
                session=session,
                model_class=model_class,
                logger=self.logger,
                specification_translator=translator if include_specification else None
            )
        elif include_specification and include_batch and include_streaming and include_events:
            # Complete repository with all capabilities
            return SQLAlchemyCompleteRepository(
                entity_type=entity_type,
                session=session,
                model_class=model_class,
                logger=self.logger,
                specification_translator=translator
            )
        elif include_specification:
            # Repository with specification support
            return SQLAlchemySpecificationRepository(
                entity_type=entity_type,
                session=session,
                model_class=model_class,
                logger=self.logger,
                specification_translator=translator
            )
        elif include_batch:
            # Repository with batch support
            return SQLAlchemyBatchRepository(
                entity_type=entity_type,
                session=session,
                model_class=model_class,
                logger=self.logger
            )
        elif include_streaming:
            # Repository with streaming support
            return SQLAlchemyStreamingRepository(
                entity_type=entity_type,
                session=session,
                model_class=model_class,
                logger=self.logger
            )
        elif include_events:
            # Repository with event collection
            return SQLAlchemyEventCollectingRepository(
                entity_type=entity_type,
                session=session,
                model_class=model_class,
                logger=self.logger
            )
        else:
            # Basic repository
            return SQLAlchemyRepository(
                entity_type=entity_type,
                session=session,
                model_class=model_class,
                logger=self.logger
            )
    
    def create_in_memory_repository(
        self,
        entity_type: Type[T],
        include_specification: bool = False,
        include_batch: bool = False,
        include_streaming: bool = False,
        include_events: bool = False,
        is_aggregate: bool = False,
    ) -> BaseRepository[T, Any]:
        """
        Create an in-memory repository.
        
        Args:
            entity_type: The type of entity this repository manages
            include_specification: Whether to include specification support
            include_batch: Whether to include batch operation support
            include_streaming: Whether to include streaming support
            include_events: Whether to include event collection
            is_aggregate: Whether the entity is an aggregate root
            
        Returns:
            The created repository
        """
        # Create appropriate repository based on capabilities
        if is_aggregate:
            # Aggregate repository always includes event collection
            return InMemoryAggregateRepository(
                entity_type=entity_type,
                logger=self.logger
            )
        elif include_specification and include_batch and include_streaming and include_events:
            # Complete repository with all capabilities
            return InMemoryCompleteRepository(
                entity_type=entity_type,
                logger=self.logger
            )
        elif include_specification:
            # Repository with specification support
            return InMemorySpecificationRepository(
                entity_type=entity_type,
                logger=self.logger
            )
        elif include_batch:
            # Repository with batch support
            return InMemoryBatchRepository(
                entity_type=entity_type,
                logger=self.logger
            )
        elif include_streaming:
            # Repository with streaming support
            return InMemoryStreamingRepository(
                entity_type=entity_type,
                logger=self.logger
            )
        elif include_events:
            # Repository with event collection
            return InMemoryEventCollectingRepository(
                entity_type=entity_type,
                logger=self.logger
            )
        else:
            # Basic repository
            return InMemoryRepository(
                entity_type=entity_type,
                logger=self.logger
            )
    
    def create_repository(
        self,
        entity_type: Type[T],
        session_or_model: Union[AsyncSession, None] = None,
        model_class: Optional[Type[Any]] = None,
        in_memory: bool = False,
        include_specification: bool = False,
        include_batch: bool = False,
        include_streaming: bool = False,
        include_events: bool = False,
    ) -> BaseRepository[T, Any]:
        """
        Create a repository based on the provided options.
        
        Args:
            entity_type: The type of entity this repository manages
            session_or_model: SQLAlchemy session or None for in-memory
            model_class: SQLAlchemy model class (required for SQLAlchemy)
            in_memory: Whether to create an in-memory repository
            include_specification: Whether to include specification support
            include_batch: Whether to include batch operation support
            include_streaming: Whether to include streaming support
            include_events: Whether to include event collection
            
        Returns:
            The created repository
        """
        # Determine if entity is an aggregate
        is_aggregate = issubclass(entity_type, AggregateRoot)
        
        # Always include events for aggregates
        if is_aggregate:
            include_events = True
        
        # Create in-memory repository if specified or no session provided
        if in_memory or session_or_model is None:
            return self.create_in_memory_repository(
                entity_type=entity_type,
                include_specification=include_specification,
                include_batch=include_batch,
                include_streaming=include_streaming,
                include_events=include_events,
                is_aggregate=is_aggregate
            )
        
        # Create SQLAlchemy repository
        if model_class is None:
            raise ValueError("model_class is required for SQLAlchemy repositories")
        
        return self.create_sqlalchemy_repository(
            entity_type=entity_type,
            session=session_or_model,
            model_class=model_class,
            include_specification=include_specification,
            include_batch=include_batch,
            include_streaming=include_streaming,
            include_events=include_events,
            is_aggregate=is_aggregate
        )


class UnitOfWorkFactory:
    """
    Factory for creating unit of work instances.
    
    DEPRECATED: This class is deprecated. Use the UnitOfWork implementations from
    uno.core.uow instead.
    
    This class provides methods for creating various types of unit of work,
    configured for different persistence mechanisms.
    """
    
    def __init__(
        self,
        session_factory: Optional[Callable[[], AsyncSession]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the unit of work factory.
        
        Args:
            session_factory: Optional factory for creating SQLAlchemy sessions
            logger: Optional logger for diagnostic output
        """
        warnings.warn(
            "UnitOfWorkFactory is deprecated. Use the UnitOfWork implementations from "
            "uno.core.uow instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.session_factory = session_factory
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_sqlalchemy_unit_of_work(
        self, session: Optional[AsyncSession] = None
    ) -> SQLAlchemyUnitOfWork:
        """
        Create a SQLAlchemy unit of work.
        
        DEPRECATED: Use SqlAlchemyUnitOfWork from uno.core.uow instead.
        
        Args:
            session: Optional SQLAlchemy session (created from factory if not provided)
            
        Returns:
            SQLAlchemy unit of work
        """
        warnings.warn(
            "create_sqlalchemy_unit_of_work is deprecated. Use SqlAlchemyUnitOfWork from "
            "uno.core.uow instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if session is None:
            if self.session_factory is None:
                raise ValueError(
                    "Session factory is required to create a SQLAlchemy unit of work "
                    "when no session is provided"
                )
            session = self.session_factory()
        
        return SQLAlchemyUnitOfWork(session=session, logger=self.logger)
    
    def create_in_memory_unit_of_work(self) -> InMemoryUnitOfWork:
        """
        Create an in-memory unit of work.
        
        DEPRECATED: Use InMemoryUnitOfWork from uno.core.uow instead.
        
        Returns:
            In-memory unit of work
        """
        warnings.warn(
            "create_in_memory_unit_of_work is deprecated. Use InMemoryUnitOfWork from "
            "uno.core.uow instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return InMemoryUnitOfWork(logger=self.logger)
    
    def create_unit_of_work(
        self, in_memory: bool = False, session: Optional[AsyncSession] = None
    ) -> UnitOfWork:
        """
        Create a unit of work based on the provided options.
        
        DEPRECATED: Use uno.core.uow instead.
        
        Args:
            in_memory: Whether to create an in-memory unit of work
            session: Optional SQLAlchemy session (created from factory if not provided)
            
        Returns:
            The created unit of work
        """
        warnings.warn(
            "create_unit_of_work is deprecated. Use the UnitOfWork implementations from "
            "uno.core.uow instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if in_memory:
            return self.create_in_memory_unit_of_work()
        else:
            return self.create_sqlalchemy_unit_of_work(session)


# Default instances
_repository_factory: Optional[RepositoryFactory] = None
_unit_of_work_factory: Optional[UnitOfWorkFactory] = None


def get_repository_factory() -> RepositoryFactory:
    """
    Get the default repository factory.
    
    Returns:
        The default repository factory
    """
    global _repository_factory
    
    if _repository_factory is None:
        _repository_factory = RepositoryFactory()
    
    return _repository_factory


def get_unit_of_work_factory() -> UnitOfWorkFactory:
    """
    Get the default unit of work factory.
    
    DEPRECATED: Use uno.core.uow instead.
    
    Returns:
        The default unit of work factory
    """
    warnings.warn(
        "get_unit_of_work_factory is deprecated. Use the UnitOfWork implementations from "
        "uno.core.uow instead.",
        DeprecationWarning,
        stacklevel=2
    )
    global _unit_of_work_factory
    
    if _unit_of_work_factory is None:
        _unit_of_work_factory = UnitOfWorkFactory()
    
    return _unit_of_work_factory


def initialize_factories(
    session_factory: Optional[Callable[[], AsyncSession]] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Initialize the default factories.
    
    Args:
        session_factory: Optional factory for creating SQLAlchemy sessions
        logger: Optional logger for diagnostic output
    """
    global _repository_factory, _unit_of_work_factory
    
    _repository_factory = RepositoryFactory(logger=logger)
    _unit_of_work_factory = UnitOfWorkFactory(
        session_factory=session_factory,
        logger=logger
    )


def create_repository(
    entity_type: Type[T],
    session_or_model: Union[AsyncSession, None] = None,
    model_class: Optional[Type[Any]] = None,
    in_memory: bool = False,
    include_specification: bool = False,
    include_batch: bool = False,
    include_streaming: bool = False,
    include_events: bool = False,
) -> BaseRepository[T, Any]:
    """
    Create a repository using the default factory.
    
    Args:
        entity_type: The type of entity this repository manages
        session_or_model: SQLAlchemy session or None for in-memory
        model_class: SQLAlchemy model class (required for SQLAlchemy)
        in_memory: Whether to create an in-memory repository
        include_specification: Whether to include specification support
        include_batch: Whether to include batch operation support
        include_streaming: Whether to include streaming support
        include_events: Whether to include event collection
        
    Returns:
        The created repository
    """
    return get_repository_factory().create_repository(
        entity_type=entity_type,
        session_or_model=session_or_model,
        model_class=model_class,
        in_memory=in_memory,
        include_specification=include_specification,
        include_batch=include_batch,
        include_streaming=include_streaming,
        include_events=include_events
    )


def create_unit_of_work(
    in_memory: bool = False, session: Optional[AsyncSession] = None
) -> UnitOfWork:
    """
    Create a unit of work using the default factory.
    
    DEPRECATED: Use uno.core.uow instead.
    
    Args:
        in_memory: Whether to create an in-memory unit of work
        session: Optional SQLAlchemy session
        
    Returns:
        The created unit of work
    """
    warnings.warn(
        "create_unit_of_work is deprecated. Use the UnitOfWork implementations from "
        "uno.core.uow instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_unit_of_work_factory().create_unit_of_work(
        in_memory=in_memory,
        session=session
    )