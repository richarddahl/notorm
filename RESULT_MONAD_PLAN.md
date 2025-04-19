# Result Monad Migration Plan

## Overview

This document outlines a comprehensive plan for migrating the `uno` codebase to consistently use the Result monad pattern for error handling throughout all components. The Result monad is a functional programming concept that allows for explicit error handling without exceptions, improving code reliability and making the flow of errors more visible.

## Current State Analysis

### Current Error Handling Approaches

The codebase currently uses a mix of error handling strategies:

1. **Result Monad Pattern**: Some components (particularly in the domain layer repositories and services) already use the `Result[T, E]` type with `Success` and `Failure` wrappers.

2. **Direct Exception Handling**: Many components use traditional try/except blocks, especially in:
   - Application services
   - Infrastructure components
   - Background job processing
   - Event handling
   - Query execution

3. **Mixed Approaches**: Some modules use a combination of both approaches, which can lead to inconsistency and confusion.

### Existing Result Monad Implementation

The codebase includes a robust Result monad implementation in `src/uno/core/errors/result.py` with the following features:

- Generic `Result[T, E]` class
- `Success` and `Failure` factory functions
- Monadic operations (`map`, `bind`, `combine`)
- Error aggregation
- Context/metadata support
- Validation-specific specialization (`ValidationResult`)

## Migration Strategy

### Phase 1: Preparation and Standards

1. **Documentation & Standards**:
   - Establish clear guidelines for Result monad usage
   - Document best practices for converting exception-based code to Result pattern
   - Create examples of common patterns for different component types

2. **Utility Functions**:
   - Implement additional helper functions for common error handling scenarios
   - Create decorators for easily converting exception-based functions to Result-returning functions

3. **Testing Infrastructure**:
   - Update test utilities to support Result-based assertions
   - Create test helpers for verifying Success/Failure cases

### Phase 2: Core Infrastructure Migration

1. **Core Protocol Interfaces**:
   - Update all core protocol interfaces to use Result return types
   - Ensure that interface methods that can fail return Results

2. **Data Access Layer**:
   - Complete the migration of all repository implementations to use Result
   - Standardize error hierarchies for data access failures

3. **Infrastructure Services**:
   - Migrate infrastructure service implementations to use Result pattern
   - Update service factory methods to properly propagate Results

### Phase 3: Application Services Migration

1. **Command Handlers**:
   - Update command handler interfaces to return Results
   - Migrate all implementations to use Results
   - Ensure proper error mapping from domain to application level

2. **Query Handlers**:
   - Update query handler interfaces to return Results
   - Migrate implementations to use Results
   - Create specialized query error types

3. **Background Processing**:
   - Migrate job execution to use Result pattern
   - Create job-specific error types for different failure scenarios

### Phase 4: API and Presentation Layer

1. **API Controllers**:
   - Add Result handling to API endpoints
   - Create mapping from Results to HTTP responses
   - Ensure consistent error responses

2. **Error Middleware**:
   - Update error handling middleware to properly interpret Result failures
   - Ensure consistent error response formats

### Phase 5: Cross-Cutting Concerns

1. **Logging & Monitoring**:
   - Update logging to properly capture Result metadata
   - Add Result-aware metrics collection

2. **Event System**:
   - Ensure event handlers properly use and propagate Results
   - Update event publishing to use Results for operation status

## Implementation Details

### Code Pattern Transformations

#### 1. Exception-Based Repository to Result-Based

**Before:**

```python
async def get_by_id(self, entity_id: str) -> Optional[Entity]:
    try:
        # Database operation
        result = await self._session.execute(...)
        if not result:
            return None
        return Entity(...)
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise RepositoryError(f"Failed to get entity: {str(e)}")
```

**After:**

```python
async def get_by_id(self, entity_id: str) -> Result[Optional[Entity], RepositoryError]:
    try:
        # Database operation
        result = await self._session.execute(...)
        if not result:
            return Success(None)
        return Success(Entity(...))
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return Failure(RepositoryError(f"Failed to get entity: {str(e)}"))
```

#### 2. Service Method Using Results

**Before:**

```python
async def process_command(self, command: Command) -> CommandResult:
    try:
        entity = await self._repository.get_by_id(command.entity_id)
        if not entity:
            raise EntityNotFoundError(f"Entity {command.entity_id} not found")
        
        # Process command
        entity.update(command.data)
        await self._repository.update(entity)
        return CommandResult(success=True)
    except (EntityNotFoundError, ValidationError) as e:
        return CommandResult(success=False, error=str(e))
    except Exception as e:
        logger.error(f"Failed to process command: {e}")
        return CommandResult(success=False, error="Internal error")
```

**After:**

```python
async def process_command(self, command: Command) -> Result[Entity, CommandError]:
    # Get entity
    entity_result = await self._repository.get_by_id(command.entity_id)
    if entity_result.is_failure():
        return Failure(CommandError.from_repository_error(entity_result.error()))
    
    entity = entity_result.value()
    if not entity:
        return Failure(CommandError.entity_not_found(command.entity_id))
    
    # Process command
    try:
        entity.update(command.data)
    except ValidationError as e:
        return Failure(CommandError.validation_error(str(e)))
    
    # Update entity
    update_result = await self._repository.update(entity)
    if update_result.is_failure():
        return Failure(CommandError.from_repository_error(update_result.error()))
    
    return Success(update_result.value())
```

### Utility Functions To Implement

```python
# Decorator for converting exception-based functions to Result
def to_result(error_type: Type[E] = Exception):
    def decorator(fn):
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs) -> Result[Any, E]:
            try:
                result = await fn(*args, **kwargs)
                return Success(result)
            except Exception as e:
                if isinstance(e, error_type):
                    return Failure(e)
                return Failure(error_type(str(e)))
        
        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs) -> Result[Any, E]:
            try:
                result = fn(*args, **kwargs)
                return Success(result)
            except Exception as e:
                if isinstance(e, error_type):
                    return Failure(e)
                return Failure(error_type(str(e)))
        
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper
    return decorator
```

## Migration Sequence

To minimize disruption, the migration will follow this sequence:

1. Start with the **innermost layers** (domain entities, value objects)
2. Move outward to **repositories and domain services**
3. Continue to **application services** and use cases
4. Finally, update **API controllers** and external interfaces

This inside-out approach ensures that each layer can depend on the Results returned by the inner layers it calls.

## Testing Strategy

1. **Unit Tests**: Update unit tests to verify both success and failure cases explicitly
2. **Integration Tests**: Ensure proper Result propagation across component boundaries
3. **Error Scenario Testing**: Add tests for specific error scenarios to verify proper Result handling

## Timeline Estimation

- **Phase 1 (Preparation)**: 1-2 weeks
- **Phase 2 (Core Infrastructure)**: 2-3 weeks
- **Phase 3 (Application Services)**: 2-3 weeks
- **Phase 4 (API Layer)**: 1-2 weeks
- **Phase 5 (Cross-Cutting)**: 1-2 weeks

Total estimated time: 7-12 weeks, depending on codebase size and complexity.

## Success Criteria

1. All public methods that can fail return `Result` types
2. No uncaught exceptions in normal operation
3. All error paths are explicit and documented
4. Consistent error handling across all components
5. Improved error observability and traceability

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes to public APIs | High | Medium | Version the APIs and provide migration guides |
| Performance impact from Result wrapping | Medium | Low | Profile critical paths and optimize as needed |
| Developer learning curve | Medium | Medium | Provide clear documentation and examples |
| Inconsistent adoption | Medium | High | Use static analysis tools to enforce Result usage |
| Backward compatibility issues | High | Medium | Create adapters for legacy code interaction |

## Conclusion

This migration plan provides a structured approach to adopting the Result monad pattern throughout the `uno` codebase. Following this plan will lead to more explicit error handling, improved code reliability, and better developer experience when dealing with error cases.

The Result monad pattern aligns well with the clean architecture principles already present in the codebase, further enhancing the separation of concerns and making the flow of errors more visible across architectural boundaries.
