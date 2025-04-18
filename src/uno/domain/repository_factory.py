"""
Repository factory for creating repository instances.

This module provides factories for creating repositories and unit of work instances,
making it easier to use the standardized repository pattern.
"""

import logging
from typing import (
    Type, TypeVar, Optional, Dict, Any, Callable, 
    cast, Generic, Union, Tuple
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from uno.domain.core import Entity, AggregateRoot
from uno.domain.repository import (
    Repository, AggregateRepository,
    SQLAlchemyRepository, SQLAlchemyAggregateRepository,
    InMemoryRepository, InMemoryAggregateRepository
)
from uno.domain.unit_of_work import (
    UnitOfWork, SQLAlchemyUnitOfWork, InMemoryUnitOfWork,
    UnitOfWorkManager
)
from uno.domain.specifications import Specification
from uno.core.errors.result import Result, Success, Failure


T = TypeVar("T", bound=Entity)
A = TypeVar("A", bound=AggregateRoot)
M = TypeVar("M")  # Type for ORM models


class RepositoryFactory:
    """
    Factory for creating repositories.
    
    This factory simplifies the creation of repositories for different entity types,
    with support for SQLAlchemy and in-memory implementations.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the repository factory.
        
        Args:
            logger: Optional logger for diagnostic output
        """
        self.logger = logger or logging.getLogger(__name__)
        self._model_registry: Dict[Type[Entity], Type[Any]] = {}
        self._session_factory: Optional[Callable[[], AsyncSession]] = None
        self._uow_manager = UnitOfWorkManager(logger)
    
    def register_model(self, entity_type: Type[T], model_class: Type[M]) -> None:
        """
        Register a model class for an entity type.
        
        Args:
            entity_type: The entity type
            model_class: The corresponding ORM model class
        """
        self._model_registry[entity_type] = model_class
    
    def set_session_factory(self, session_factory: Callable[[], AsyncSession]) -> None:
        """
        Set the SQLAlchemy session factory.
        
        Args:
            session_factory: Factory function that creates SQLAlchemy sessions
        """
        self._session_factory = session_factory
    
    def create_from_connection_string(
        self, 
        connection_string: str, 
        echo: bool = False
    ) -> None:
        """
        Create and set a session factory from a database connection string.
        
        Args:
            connection_string: SQLAlchemy connection string
            echo: Whether to echo SQL statements
        """
        engine = create_async_engine(connection_string, echo=echo)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        
        def create_session() -> AsyncSession:
            return session_factory()
        
        self.set_session_factory(create_session)
    
    def create_repository(
        self, 
        entity_type: Type[T], 
        session: Optional[AsyncSession] = None,
        in_memory: bool = False
    ) -> Repository[T]:
        """
        Create a repository for an entity type.
        
        Args:
            entity_type: The entity type
            session: Optional SQLAlchemy session (if not using in_memory)
            in_memory: Whether to create an in-memory repository
            
        Returns:
            A repository instance
            
        Raises:
            ValueError: If model isn't registered for SQLAlchemy repository,
                        or if no session factory is set and no session provided
        """
        if in_memory:
            # Create an in-memory repository
            if issubclass(entity_type, AggregateRoot):
                return InMemoryAggregateRepository(
                    cast(Type[AggregateRoot], entity_type),
                    self.logger
                )
            else:
                return InMemoryRepository(entity_type, self.logger)
        else:
            # Create a SQLAlchemy repository
            if entity_type not in self._model_registry:
                raise ValueError(f"No model class registered for entity type {entity_type.__name__}")
            
            model_class = self._model_registry[entity_type]
            
            if session is None:
                if self._session_factory is None:
                    raise ValueError("No session factory set and no session provided")
                session = self._session_factory()
            
            if issubclass(entity_type, AggregateRoot):
                return SQLAlchemyAggregateRepository(
                    cast(Type[AggregateRoot], entity_type),
                    session,
                    model_class,
                    self.logger
                )
            else:
                return SQLAlchemyRepository(
                    entity_type,
                    session,
                    model_class,
                    self.logger
                )
    
    def create_unit_of_work(
        self,
        session: Optional[AsyncSession] = None,
        in_memory: bool = False
    ) -> UnitOfWork:
        """
        Create a unit of work.
        
        Args:
            session: Optional SQLAlchemy session (if not using in_memory)
            in_memory: Whether to create an in-memory unit of work
            
        Returns:
            A unit of work instance
            
        Raises:
            ValueError: If no session factory is set and no session provided
        """
        if in_memory:
            return InMemoryUnitOfWork(self.logger)
        else:
            if session is None:
                if self._session_factory is None:
                    raise ValueError("No session factory set and no session provided")
                session = self._session_factory()
            
            return SQLAlchemyUnitOfWork(session, self.logger)
    
    def register_unit_of_work(
        self,
        name: str,
        in_memory: bool = False
    ) -> None:
        """
        Register a unit of work factory with the manager.
        
        Args:
            name: The name for the unit of work
            in_memory: Whether to create an in-memory unit of work
            
        Raises:
            ValueError: If no session factory is set for SQLAlchemy unit of work
        """
        if in_memory:
            self._uow_manager.register_factory(
                name, lambda: InMemoryUnitOfWork(self.logger)
            )
        else:
            if self._session_factory is None:
                raise ValueError("No session factory set for SQLAlchemy unit of work")
            
            self._uow_manager.register_factory(
                name, lambda: SQLAlchemyUnitOfWork(
                    self._session_factory(), self.logger
                )
            )
    
    @property
    def uow_manager(self) -> UnitOfWorkManager:
        """Get the unit of work manager."""
        return self._uow_manager


class SpecificationFactory(Generic[T]):
    """
    Factory for creating specifications for an entity type.
    
    This factory simplifies the creation of specifications for advanced querying.
    """
    
    def __init__(self, entity_type: Type[T]):
        """
        Initialize the specification factory.
        
        Args:
            entity_type: The entity type
        """
        self.entity_type = entity_type
    
    def equals(self, field: str, value: Any) -> Specification[T]:
        """
        Create a specification for field equality.
        
        Args:
            field: The field name
            value: The value to compare
            
        Returns:
            A specification
        """
        from uno.domain.specifications import AttributeSpecification
        return AttributeSpecification(field, value)
    
    def not_equals(self, field: str, value: Any) -> Specification[T]:
        """
        Create a specification for field inequality.
        
        Args:
            field: The field name
            value: The value to compare
            
        Returns:
            A specification
        """
        return self.equals(field, value).not_()
    
    def greater_than(self, field: str, value: Any) -> Specification[T]:
        """
        Create a specification for field > value.
        
        Args:
            field: The field name
            value: The value to compare
            
        Returns:
            A specification
        """
        from uno.domain.specifications import PredicateSpecification
        
        def predicate(entity: T) -> bool:
            if not hasattr(entity, field):
                return False
            entity_value = getattr(entity, field)
            return entity_value is not None and entity_value > value
        
        return PredicateSpecification(predicate, f"{field}_gt_{value}")
    
    def greater_than_or_equal(self, field: str, value: Any) -> Specification[T]:
        """
        Create a specification for field >= value.
        
        Args:
            field: The field name
            value: The value to compare
            
        Returns:
            A specification
        """
        from uno.domain.specifications import PredicateSpecification
        
        def predicate(entity: T) -> bool:
            if not hasattr(entity, field):
                return False
            entity_value = getattr(entity, field)
            return entity_value is not None and entity_value >= value
        
        return PredicateSpecification(predicate, f"{field}_gte_{value}")
    
    def less_than(self, field: str, value: Any) -> Specification[T]:
        """
        Create a specification for field < value.
        
        Args:
            field: The field name
            value: The value to compare
            
        Returns:
            A specification
        """
        from uno.domain.specifications import PredicateSpecification
        
        def predicate(entity: T) -> bool:
            if not hasattr(entity, field):
                return False
            entity_value = getattr(entity, field)
            return entity_value is not None and entity_value < value
        
        return PredicateSpecification(predicate, f"{field}_lt_{value}")
    
    def less_than_or_equal(self, field: str, value: Any) -> Specification[T]:
        """
        Create a specification for field <= value.
        
        Args:
            field: The field name
            value: The value to compare
            
        Returns:
            A specification
        """
        from uno.domain.specifications import PredicateSpecification
        
        def predicate(entity: T) -> bool:
            if not hasattr(entity, field):
                return False
            entity_value = getattr(entity, field)
            return entity_value is not None and entity_value <= value
        
        return PredicateSpecification(predicate, f"{field}_lte_{value}")
    
    def in_list(self, field: str, values: list) -> Specification[T]:
        """
        Create a specification for field in values.
        
        Args:
            field: The field name
            values: The list of values
            
        Returns:
            A specification
        """
        from uno.domain.specifications import PredicateSpecification
        
        def predicate(entity: T) -> bool:
            if not hasattr(entity, field):
                return False
            entity_value = getattr(entity, field)
            return entity_value in values
        
        return PredicateSpecification(predicate, f"{field}_in_{values}")
    
    def contains(self, field: str, value: str, case_sensitive: bool = False) -> Specification[T]:
        """
        Create a specification for string contains.
        
        Args:
            field: The field name
            value: The substring to check for
            case_sensitive: Whether the comparison is case sensitive
            
        Returns:
            A specification
        """
        from uno.domain.specifications import PredicateSpecification
        
        def predicate(entity: T) -> bool:
            if not hasattr(entity, field):
                return False
            entity_value = getattr(entity, field)
            if entity_value is None:
                return False
            
            str_value = str(entity_value)
            search_value = value
            
            if not case_sensitive:
                str_value = str_value.lower()
                search_value = value.lower()
                
            return search_value in str_value
        
        return PredicateSpecification(predicate, f"{field}_contains_{value}")
    
    def range(self, field: str, min_value: Any, max_value: Any) -> Specification[T]:
        """
        Create a specification for min_value <= field <= max_value.
        
        Args:
            field: The field name
            min_value: The minimum value
            max_value: The maximum value
            
        Returns:
            A specification
        """
        return self.greater_than_or_equal(field, min_value).and_(
            self.less_than_or_equal(field, max_value)
        )
    
    def is_null(self, field: str) -> Specification[T]:
        """
        Create a specification for field is None.
        
        Args:
            field: The field name
            
        Returns:
            A specification
        """
        from uno.domain.specifications import PredicateSpecification
        
        def predicate(entity: T) -> bool:
            if not hasattr(entity, field):
                return True  # If the field doesn't exist, treat as null
            return getattr(entity, field) is None
        
        return PredicateSpecification(predicate, f"{field}_is_null")
    
    def is_not_null(self, field: str) -> Specification[T]:
        """
        Create a specification for field is not None.
        
        Args:
            field: The field name
            
        Returns:
            A specification
        """
        return self.is_null(field).not_()
    
    def true(self) -> Specification[T]:
        """
        Create a specification that is always satisfied.
        
        Returns:
            A specification
        """
        from uno.domain.specifications import PredicateSpecification
        return PredicateSpecification(lambda _: True, "true")
    
    def false(self) -> Specification[T]:
        """
        Create a specification that is never satisfied.
        
        Returns:
            A specification
        """
        from uno.domain.specifications import PredicateSpecification
        return PredicateSpecification(lambda _: False, "false")


# Global repository factory instance
repository_factory = RepositoryFactory()


def create_specification_factory(entity_type: Type[T]) -> SpecificationFactory[T]:
    """
    Create a specification factory for an entity type.
    
    Args:
        entity_type: The entity type
        
    Returns:
        A specification factory
    """
    return SpecificationFactory(entity_type)


def register_entity_model(entity_type: Type[T], model_class: Type[M]) -> None:
    """
    Register a model class for an entity type with the global factory.
    
    Args:
        entity_type: The entity type
        model_class: The corresponding ORM model class
    """
    repository_factory.register_model(entity_type, model_class)


def setup_database(connection_string: str, echo: bool = False) -> None:
    """
    Set up the database connection for the global factory.
    
    Args:
        connection_string: SQLAlchemy connection string
        echo: Whether to echo SQL statements
    """
    repository_factory.create_from_connection_string(connection_string, echo)


def get_repository(
    entity_type: Type[T], 
    session: Optional[AsyncSession] = None,
    in_memory: bool = False
) -> Repository[T]:
    """
    Get a repository for an entity type from the global factory.
    
    Args:
        entity_type: The entity type
        session: Optional SQLAlchemy session
        in_memory: Whether to use an in-memory repository
        
    Returns:
        A repository instance
    """
    return repository_factory.create_repository(entity_type, session, in_memory)


def get_unit_of_work(
    session: Optional[AsyncSession] = None,
    in_memory: bool = False
) -> UnitOfWork:
    """
    Get a unit of work from the global factory.
    
    Args:
        session: Optional SQLAlchemy session
        in_memory: Whether to use an in-memory unit of work
        
    Returns:
        A unit of work instance
    """
    return repository_factory.create_unit_of_work(session, in_memory)


def get_uow_manager() -> UnitOfWorkManager:
    """
    Get the unit of work manager from the global factory.
    
    Returns:
        The unit of work manager
    """
    return repository_factory.uow_manager
"""