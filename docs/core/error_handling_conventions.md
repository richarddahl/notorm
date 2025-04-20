# Error Handling Conventions

This document describes the conventions for error handling in the codebase, focusing on the use of the Result monad pattern and best practices for contributors.

---

## 1. Use the Result Monad Everywhere
- All domain, service, and repository methods that can fail must return a `Result[T, str]` (or similar), never raise exceptions or return raw types.
- Use `Success(value, convert=True)` for successful outcomes and `Failure(error, convert=True)` for failures.
- Only raise exceptions at application boundaries (e.g., API endpoints) to translate `Result` failures into HTTP errors.

## 2. Type Annotations
- Use modern Python 3.10+ type annotations (e.g., `Result[T, str]`, `list[T]`, `X | Y`).
- Ensure all `Success` and `Failure` calls use explicit type parameters and `convert=True` where needed.

## 3. Repository Layer

- All repository methods (CRUD, batch, streaming, event-collecting) must return `Result` types, never raise exceptions directly.
- Use `Success(value)` and `Failure(error)` for all returns. (Use `convert=True` if your codebase requires it for compatibility.)
- Type annotations must use Python 3.10+ syntax (e.g., `Result[Entity, Exception]`, `str | None`, `list[T]`).

**Example: In-Memory Repository CRUD**

```python
from uno.core.errors.result import Result, Success, Failure

async def get(self, id: ID) -> Result[T, Exception]:
    try:
        entity = self.entities.get(id)
        if entity is None:
            return Failure(ValueError(f"Entity with ID {id} not found"))
        return Success(entity)
    except Exception as e:
        return Failure(e)

async def add(self, entity: T) -> Result[T, Exception]:
    try:
        entity_id = getattr(entity, "id", None)
        if not entity_id:
            return Failure(ValueError("Entity must have an ID"))
        if entity_id in self.entities:
            return Failure(ValueError(f"Entity with ID {entity_id} already exists"))
        self.entities[entity_id] = entity
        return Success(entity)
    except Exception as e:
        return Failure(e)
```

**Example: SQLAlchemy/DB Repository**

```python
async def get(self, id: ID) -> Result[T, str]:
    try:
        entity = await self.session.get(self.entity_type, id)
        if not entity:
            return Failure(f"No entity found for id={id}")
        return Success(entity)
    except SQLAlchemyError as err:
        return Failure(str(err))
```

**Event-Collecting and Aggregate Repositories**

- Use Result types for `collect_events`, `save`, and `update` methods.
- Example:

```python
async def save(self, aggregate: A) -> Result[A, Exception]:
    try:
        # ... event collection logic ...
        save_result = await super().save(aggregate)
        return Success(save_result)
    except Exception as e:
        return Failure(e)
```

### Error Handling Conventions

- Always wrap logic in try/except and return `Failure` for errors.
- Never raise exceptions from repository methods.
- Document all method signatures and return types with Result.
- Prefer explicit error messages in Failure for easier debugging.

### Modern Type Annotations

- Use `Result[T, Exception]`, `str | None`, `list[T]`, etc. (Python 3.10+)
- Avoid legacy `Optional`, `List`, etc. unless required for compatibility.

## 4. Helper Functions
- Helper functions that may fail should return `Result` instead of raising exceptions.
- If a helper is only used internally and cannot fail, it may return a raw type.

## 5. Consistency
- Do not mix exception raising and `Result` returns in the same layer.
- Prefer returning `Result` up the call stack until reaching the application boundary.

## 5. Linting and Tests
- Linting should enforce that no bare exceptions are raised in domain/service/repository code.
- Tests should check both success and failure cases for all `Result`-returning methods.

---

_Last updated: 2025-04-20_
