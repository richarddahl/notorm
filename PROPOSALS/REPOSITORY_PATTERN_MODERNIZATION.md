# Repository Pattern Modernization

This document outlines the plan for modernizing the repository pattern implementation in the uno framework.

## Current Issues

1. **Complex Repository Base Class**: The current `Repository` class is overly complex with too many responsibilities.
2. **Limited Protocol Usage**: Current implementations don't leverage Python's Protocol system effectively.
3. **Manual Transaction Management**: Repositories manage transactions explicitly rather than using context managers.
4. **No Specification Integration**: Repositories don't leverage the specification pattern for querying.
5. **Inconsistent Async Support**: Async support is mixed with synchronous code in confusing ways.
6. **Complex Inheritance Hierarchies**: Deep inheritance hierarchies make the code hard to understand and maintain.
7. **No Generic Type Parameters**: Limited use of generics reduces type safety and developer experience.
8. **Event Publishing Mixed with Data Access**: Repositories handle both data access and event publishing.

## Modernization Goals

1. **Protocol-Based Interfaces**: Define clear protocol interfaces for repository operations.
2. **Specification Pattern Integration**: Use specifications for querying data.
3. **Separation of Concerns**: Separate data access from event publishing and other concerns.
4. **Type Safety**: Leverage Python's type system for better developer experience.
5. **Context Managers for Transactions**: Use context managers for transaction handling.
6. **Modern Async Support**: Implement proper async patterns with structured concurrency.
7. **Result Pattern Integration**: Return result objects instead of raising exceptions.
8. **Simplified API**: Provide a clean, simple API for common repository operations.

## Implementation Plan

### Phase 1: Define Repository Protocols

1. Create `uno.domain.repository_protocols.py` with:
   - `RepositoryProtocol[T]` - Base protocol for all repositories
   - `ReadRepositoryProtocol[T]` - Protocol for read-only operations
   - `WriteRepositoryProtocol[T]` - Protocol for write operations
   - `UnitOfWorkProtocol` - Protocol for transaction management
   - `SpecificationRepositoryProtocol[T]` - Protocol for specification-based querying

2. Define method signatures:
   - `get(id)` - Get entity by ID
   - `find(specification)` - Find entities matching a specification
   - `find_one(specification)` - Find a single entity matching a specification
   - `add(entity)` - Add a new entity
   - `update(entity)` - Update an existing entity
   - `remove(entity)` - Remove an entity
   - `exists(specification)` - Check if an entity exists matching a specification
   - `count(specification)` - Count entities matching a specification

### Phase 2: Implement Core Repository Classes

1. Create `uno.domain.repositories.py` with implementations:
   - `Repository[T]` - Base class implementing common repository operations
   - `SpecificationRepository[T]` - Repository with specification-based querying
   - `InMemoryRepository[T]` - In-memory repository for testing
   - `SqlAlchemyRepository[T]` - SQLAlchemy-based repository

2. Implement unit of work pattern:
   - `UnitOfWork` - Base class for unit of work
   - `SqlAlchemyUnitOfWork` - SQLAlchemy-based unit of work
   - `AsyncUnitOfWork` - Async unit of work
   - `SqlAlchemyAsyncUnitOfWork` - Async SQLAlchemy unit of work

### Phase 3: Implement Specification Translation

1. Create `uno.domain.specification_translator.py` with:
   - `SpecificationTranslator` - Base class for translating specifications
   - `SqlAlchemyTranslator` - Translates specifications to SQLAlchemy queries
   - `InMemoryTranslator` - Translates specifications to in-memory filters

2. Implement translation for:
   - `AndSpecification`
   - `OrSpecification`
   - `NotSpecification`
   - `AttributeSpecification`
   - `PredicateSpecification`
   - Custom domain-specific specifications

### Phase 4: Implement Result Pattern Integration

1. Create result classes in `uno.domain.repository_results.py`:
   - `RepositoryResult[T]` - Base result class for repository operations
   - `GetResult[T]` - Result for get operations
   - `FindResult[T]` - Result for find operations
   - `AddResult[T]` - Result for add operations
   - `UpdateResult[T]` - Result for update operations
   - `RemoveResult[T]` - Result for remove operations

2. Integrate with existing `CommandResult` from domain model:
   - Repository methods return `RepositoryResult` subtypes
   - Domain services use repository results to build command results

### Phase 5: Implement Async Support

1. Create async protocols in `uno.domain.repository_protocols.py`:
   - `AsyncRepositoryProtocol[T]`
   - `AsyncReadRepositoryProtocol[T]`
   - `AsyncWriteRepositoryProtocol[T]`
   - `AsyncUnitOfWorkProtocol`

2. Implement async repositories in `uno.domain.async_repositories.py`:
   - `AsyncRepository[T]`
   - `AsyncSpecificationRepository[T]`
   - `AsyncSqlAlchemyRepository[T]`

3. Implement async unit of work:
   - `AsyncUnitOfWork`
   - `AsyncSqlAlchemyUnitOfWork`

### Phase 6: Update Existing Repositories

1. Identify all existing repository implementations
2. Create new implementations using the new base classes
3. Replace old implementations with new ones
4. Update all repository clients to use the new API

### Phase 7: Documentation and Examples

1. Create comprehensive documentation:
   - `docs/domain/repositories.md` - Overview of the repository pattern
   - `docs/domain/unit_of_work.md` - Unit of work pattern documentation
   - `docs/domain/specifications_with_repositories.md` - Using specifications with repositories
   - `docs/domain/async_repositories.md` - Async repository documentation

2. Create examples:
   - `examples/domain/repository_example.py` - Basic repository usage
   - `examples/domain/specifications_with_repositories_example.py` - Using specifications with repositories
   - `examples/domain/unit_of_work_example.py` - Unit of work pattern usage
   - `examples/domain/async_repository_example.py` - Async repository usage

### Phase 8: Testing

1. Implement comprehensive tests:
   - Unit tests for all repository implementations
   - Integration tests for database repositories
   - Performance tests for repository operations

## Implementation Details

### Repository Protocol

```python
@runtime_checkable
class RepositoryProtocol(Protocol[T]):
    """Protocol for repositories."""
    
    def get(self, id: Any) -> Optional[T]:
        """Get entity by ID."""
        ...
    
    def find(self, specification: SpecificationProtocol[T]) -> List[T]:
        """Find entities matching a specification."""
        ...
    
    def find_one(self, specification: SpecificationProtocol[T]) -> Optional[T]:
        """Find a single entity matching a specification."""
        ...
    
    def add(self, entity: T) -> None:
        """Add a new entity."""
        ...
    
    def update(self, entity: T) -> None:
        """Update an existing entity."""
        ...
    
    def remove(self, entity: T) -> None:
        """Remove an entity."""
        ...
    
    def exists(self, specification: SpecificationProtocol[T]) -> bool:
        """Check if an entity exists matching a specification."""
        ...
    
    def count(self, specification: SpecificationProtocol[T]) -> int:
        """Count entities matching a specification."""
        ...
```

### Unit of Work Protocol

```python
@runtime_checkable
class UnitOfWorkProtocol(Protocol):
    """Protocol for unit of work."""
    
    def __enter__(self) -> 'UnitOfWorkProtocol':
        """Enter the unit of work context."""
        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the unit of work context."""
        ...
    
    def commit(self) -> None:
        """Commit the unit of work."""
        ...
    
    def rollback(self) -> None:
        """Rollback the unit of work."""
        ...
    
    def register_new(self, entity: EntityProtocol) -> None:
        """Register a new entity."""
        ...
    
    def register_dirty(self, entity: EntityProtocol) -> None:
        """Register a modified entity."""
        ...
    
    def register_removed(self, entity: EntityProtocol) -> None:
        """Register a removed entity."""
        ...
```

### Repository Implementation

```python
class Repository(Generic[T]):
    """Base repository implementation."""
    
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWorkProtocol]):
        """Initialize repository."""
        self.unit_of_work_factory = unit_of_work_factory
    
    def get(self, id: Any) -> Optional[T]:
        """Get entity by ID."""
        with self.unit_of_work_factory() as uow:
            return self._get(id, uow)
    
    def _get(self, id: Any, uow: UnitOfWorkProtocol) -> Optional[T]:
        """Internal get implementation."""
        raise NotImplementedError
    
    def find(self, specification: SpecificationProtocol[T]) -> List[T]:
        """Find entities matching a specification."""
        with self.unit_of_work_factory() as uow:
            return self._find(specification, uow)
    
    def _find(self, specification: SpecificationProtocol[T], uow: UnitOfWorkProtocol) -> List[T]:
        """Internal find implementation."""
        raise NotImplementedError
    
    # Additional methods...
```

### Specification Integration

```python
class SpecificationRepository(Repository[T]):
    """Repository with specification-based querying."""
    
    def __init__(
        self, 
        unit_of_work_factory: Callable[[], UnitOfWorkProtocol],
        translator: SpecificationTranslator
    ):
        """Initialize repository."""
        super().__init__(unit_of_work_factory)
        self.translator = translator
    
    def _find(self, specification: SpecificationProtocol[T], uow: UnitOfWorkProtocol) -> List[T]:
        """Find entities matching a specification."""
        # Translate specification to query
        query = self.translator.translate(specification)
        # Execute query
        return self._execute_query(query)
    
    def _execute_query(self, query: Any) -> List[T]:
        """Execute a query."""
        raise NotImplementedError
```

## Success Criteria

1. **Protocol-Based Design**: All repository interactions are defined through clear protocol interfaces.
2. **Specification Support**: All repositories support specification-based querying.
3. **Type Safety**: All repository implementations have proper generic type annotations.
4. **Modern Async Support**: All repositories have both synchronous and asynchronous implementations.
5. **Simplified API**: The repository API is clean, simple, and consistent.
6. **Comprehensive Documentation**: All repository patterns are well-documented with examples.
7. **Complete Test Coverage**: All repository implementations have comprehensive tests.
8. **Zero Legacy Code**: No legacy repository code remains in the codebase.