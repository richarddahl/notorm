# DI Refactoring Report: Concrete-to-Abstract Opportunities

This report lists concrete-to-abstract refactoring opportunities in the codebase, focusing on provider modules and dependency registration. It identifies areas of tight coupling to concrete implementations and provides actionable suggestions for moving to abstract interfaces or protocols, improving flexibility and testability.

---

## 1. Application Layer Providers

### a. src/uno/application/queries/domain_provider.py

**Current Pattern:**
```python
from uno.queries.domain_repositories import (
    QueryPathRepository,
    QueryValueRepository,
    QueryRepository,
)
from uno.queries.domain_services import (
    QueryPathService,
    QueryValueService,
    QueryService,
)

container.register(QueryPathRepository, ...)
container.register(QueryValueRepository, ...)
container.register(QueryRepository, ...)
container.register(QueryPathService, ...)
container.register(QueryValueService, ...)
container.register(QueryService, ...)
```

**Refactoring Opportunity:**
- Define abstract base classes or protocols for repositories and services (e.g., `IQueryRepository`, `IQueryService`).
- Register implementations using their abstract types:
  ```python
  container.register(IQueryRepository, QueryRepository, ...)
  container.register(IQueryService, QueryService, ...)
  ```
- Update all consumers to depend on interfaces, not concrete classes.

---

### b. src/uno/application/workflows/domain_provider.py

**Current Pattern:**
```python
from uno.workflows.domain_repositories import WorkflowDefRepository, ...
from uno.workflows.domain_services import WorkflowDefService, ...

container.register(WorkflowDefRepository, ...)
container.register(WorkflowDefService, ...)
# ... and similar for other workflow types
```

**Refactoring Opportunity:**
- Define interfaces/protocols (e.g., `IWorkflowDefRepository`, `IWorkflowDefService`).
- Register and resolve by abstract type:
  ```python
  container.register(IWorkflowDefRepository, WorkflowDefRepository, ...)
  container.register(IWorkflowDefService, WorkflowDefService, ...)
  ```
- Refactor service constructors and consumers to depend on interfaces.

---

## 2. Domain Layer Providers

### a. src/uno/domain/domain_provider.py

**Current Pattern:**
```python
from uno.values.domain_repositories import AttachmentRepository, ...
from uno.values.domain_services import AttachmentService, ...

container.register(AttachmentRepository, ...)
container.register(AttachmentService, ...)
# ... and similar for other value types
```

**Refactoring Opportunity:**
- Create interfaces for value repositories and services (e.g., `IAttachmentRepository`, `IAttachmentService`).
- Register by interface:
  ```python
  container.register(IAttachmentRepository, AttachmentRepository, ...)
  container.register(IAttachmentService, AttachmentService, ...)
  ```
- Update all usages to depend on the interface.

---

## 3. Infrastructure Layer Providers

### a. src/uno/infrastructure/database/domain_provider.py and provider.py

**Current Pattern:**
```python
from uno.database.domain_repositories import SqlAlchemyDatabaseSessionRepository, ...
from uno.database.domain_services import DatabaseManagerService, ...

container.register(SqlAlchemyDatabaseSessionRepository, ...)
container.register(DatabaseManagerService, ...)
# ... and similar for other DB services
```

**Refactoring Opportunity:**
- Define interfaces (e.g., `IDatabaseSessionRepository`, `IDatabaseManagerService`).
- Register and resolve by interface:
  ```python
  container.register(IDatabaseSessionRepository, SqlAlchemyDatabaseSessionRepository, ...)
  container.register(IDatabaseManagerService, DatabaseManagerService, ...)
  ```
- Ensure all application and domain code depend only on interfaces.

---

## 4. General Patterns

### a. Logger Injection

**Current Pattern:**
```python
logger = logging.getLogger("uno.queries")
container.register(QueryService, lambda c: QueryService(..., logger=logger), ...)
```

**Refactoring Opportunity:**
- Define a `LoggerFactory` interface or protocol.
- Inject a logger factory or use DI to provide loggers, allowing for easier mocking/testing.

---

### b. Manual Circular Dependency Injection

**Current Pattern:**
```python
recipient_service = container.resolve(WorkflowRecipientService)
action_service = container.resolve(WorkflowActionService)
recipient_service.action_service = action_service
```

**Refactoring Opportunity:**
- Refactor to constructor injection using interfaces, or use provider/factory patterns to delay resolution and avoid manual wiring.

---

# Summary Table

| Module/Path                                      | Concrete Type(s)            | Suggested Abstract Type(s)         |
|--------------------------------------------------|-----------------------------|------------------------------------|
| application/queries/domain_provider.py           | QueryRepository, ...        | IQueryRepository, IQueryService    |
| application/workflows/domain_provider.py         | WorkflowDefRepository, ...  | IWorkflowDefRepository, ...        |
| domain/domain_provider.py                        | AttachmentRepository, ...   | IAttachmentRepository, ...         |
| infrastructure/database/domain_provider.py       | SqlAlchemyDatabaseSessionRepository, ... | IDatabaseSessionRepository, ... |
| infrastructure/database/provider.py              | DatabaseProvider, ...       | IDatabaseProvider, ...             |

---

# Next Steps

1. Define interfaces/protocols for all major repository and service types.
2. Register implementations by their abstract type in the DI container.
3. Refactor all consuming code to depend on abstractions, not concrete classes.
4. Consider extracting logger creation to a factory or DI-provided service.
5. Track progress in your `DI_ISSUES.md` as you decouple each module.

Define interfaces/protocols for all major repository and service types.
Register implementations by their abstract type in the DI container.
Refactor all consuming code to depend on abstractions, not concrete classes.
Consider extracting logger creation to a factory or DI-provided service.
Track progress in your DI_ISSUES.md as you decouple each module.