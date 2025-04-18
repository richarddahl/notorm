# Import Standards Fix Guide

This guide provides specific fixes for 444 violations across 89 files.

## src/uno/api/domain_endpoints.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/api/domain_repositories.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/api/domain_services.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/api/error_handlers.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/api/service_endpoint_adapter.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/application/dto/__init__.py

### Replace UnoDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `UnoDTO` with `BaseDTO`

### Replace UnoDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `UnoDTO` with `BaseDTO`

---

## src/uno/application/queries/batch_operations.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 36
Change from:
```python
from uno.model import UnoModel as Model
```
To:
```python
from uno.domain.base.model import UnoModel as Model
```

---

## src/uno/application/queries/common_patterns.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 34
Change from:
```python
from uno.model import UnoModel as Model
```
To:
```python
from uno.domain.base.model import UnoModel as Model
```

---

## src/uno/application/queries/errors.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/application/queries/models.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 18
Change from:
```python
from uno.model import UnoModel, PostgresTypes
```
To:
```python
from uno.domain.base.model import UnoModel, PostgresTypes
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/application/queries/optimized_queries.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 33
Change from:
```python
from uno.model import UnoModel as Model
```
To:
```python
from uno.domain.base.model import UnoModel as Model
```

---

## src/uno/application/workflows/conditions.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/application/workflows/engine.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/application/workflows/errors.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/application/workflows/executor.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/application/workflows/integration.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/application/workflows/models.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 28
Change from:
```python
from uno.model import UnoModel, PostgresTypes
```
To:
```python
from uno.domain.base.model import UnoModel, PostgresTypes
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/application/workflows/provider.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/application/workflows/recipients.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/attributes/errors.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/attributes/models.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 14
Change from:
```python
from uno.model import UnoModel, PostgresTypes
```
To:
```python
from uno.domain.base.model import UnoModel, PostgresTypes
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/attributes/repositories.py

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

---

## src/uno/core/__init__.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/base/service.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/di_testing.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/errors/__init__.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/errors/base.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/errors/core_errors.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/errors/examples.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/errors/logging.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/errors/result.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/errors/security.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/errors/validation.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/examples/async_example.py

### Fix import on line 12
Change from:
```python
from uno.core.async_manager import (
```
To:
```python
from uno.core.async.task_manager import (
```

---

## src/uno/core/examples/batch_operations_example.py

### Fix import on line 20
Change from:
```python
from uno.model import Model
```
To:
```python
from uno.domain.base.model import Model
```

---

## src/uno/core/examples/error_handling_example.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/examples/modern_architecture_example.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/examples/monitoring_example.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/examples/resource_example.py

### Fix import on line 19
Change from:
```python
from uno.core.async_manager import get_async_manager, run_application
```
To:
```python
from uno.core.async.task_manager import get_async_manager, run_application
```

---

## src/uno/core/fastapi_error_handlers.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/core/fastapi_integration.py

### Fix import on line 15
Change from:
```python
from uno.core.async_manager import get_async_manager
```
To:
```python
from uno.core.async.task_manager import get_async_manager
```

---

## src/uno/core/monitoring/dashboard.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/dependencies/modern_provider.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/dependencies/service.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 12
Change from:
```python
from uno.model import UnoModel
```
To:
```python
from uno.domain.base.model import UnoModel
```

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoService with BaseService
1. Add import: `from uno.core.base.service import BaseService`
2. Replace all occurrences of `UnoService` with `BaseService`

---

## src/uno/dependencies/testing.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 20
Change from:
```python
from uno.model import UnoModel
```
To:
```python
from uno.domain.base.model import UnoModel
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/devtools/cli/codegen.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/devtools/codegen/api.py

### Fix import on line 175
Change from:
```python
imports.append(f"from uno.model import {model_name}")
```
To:
```python
imports.append(f"from uno.domain.base.model import {model_name}")
```

### Fix import on line 177
Change from:
```python
imports.append(f"from uno.repository import {repository_name}")
```
To:
```python
imports.append(f"from uno.core.base.repository import {repository_name}")
```

---

## src/uno/devtools/codegen/model.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `UnoDTO` with `BaseDTO`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `UnoDTO` with `BaseDTO`

### Replace UnoDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `UnoDTO` with `BaseDTO`

### Fix import on line 158
Change from:
```python
imports.append(f"from uno.model import {base_model_class}")
```
To:
```python
imports.append(f"from uno.domain.base.model import {base_model_class}")
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `UnoDTO` with `BaseDTO`

---

## src/uno/devtools/codegen/project.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

---

## src/uno/devtools/codegen/repository.py

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Fix import on line 135
Change from:
```python
imports.append(f"from uno.model import {model_name}")
```
To:
```python
imports.append(f"from uno.domain.base.model import {model_name}")
```

---

## src/uno/devtools/codegen/service.py

### Replace UnoService with BaseService
1. Add import: `from uno.core.base.service import BaseService`
2. Replace all occurrences of `UnoService` with `BaseService`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoService with BaseService
1. Add import: `from uno.core.base.service import BaseService`
2. Replace all occurrences of `UnoService` with `BaseService`

### Replace UnoService with BaseService
1. Add import: `from uno.core.base.service import BaseService`
2. Replace all occurrences of `UnoService` with `BaseService`

---

## src/uno/devtools/debugging/error_enhancer.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/devtools/debugging/middleware.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/devtools/debugging/repository_debug.py

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

---

## src/uno/devtools/docs/extractors.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/domain/__init__.py

### Evaluate backward compatibility on line 327
Code: `warnings.warn(`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Evaluate backward compatibility on line 339
Code: `DeprecationWarning,`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

---

## src/uno/domain/base/model.py

### Evaluate backward compatibility on line 177
Code: `# For backward compatibility only - use BaseModel directly in new code`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/domain/exceptions.py

### Evaluate backward compatibility on line 13
Code: `warnings.warn(`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Evaluate backward compatibility on line 16
Code: `DeprecationWarning,`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/domain/specification_translators/postgresql.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 33
Change from:
```python
from uno.model import UnoModel
```
To:
```python
from uno.domain.base.model import UnoModel
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/dto/dto_manager.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/enums.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/examples/ecommerce_app/catalog/repository/models.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 17
Change from:
```python
from uno.model import UnoModel
```
To:
```python
from uno.domain.base.model import UnoModel
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/examples/ecommerce_app/main.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/authorization/mixins.py

### Fix import on line 16
Change from:
```python
from uno.model import PostgresTypes
```
To:
```python
from uno.domain.base.model import PostgresTypes
```

---

## src/uno/infrastructure/authorization/models.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 25
Change from:
```python
from uno.model import UnoModel, PostgresTypes
```
To:
```python
from uno.domain.base.model import UnoModel, PostgresTypes
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/infrastructure/authorization/repositories.py

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

---

## src/uno/infrastructure/database/db.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/database/enhanced_db.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 44
Change from:
```python
from uno.model import UnoModel
```
To:
```python
from uno.domain.base.model import UnoModel
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 530
Change from:
```python
from uno.model import UnoModel
```
To:
```python
from uno.domain.base.model import UnoModel
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/infrastructure/database/errors.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/database/pg_error_handler.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/messaging/models.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 15
Change from:
```python
from uno.model import UnoModel, PostgresTypes
```
To:
```python
from uno.domain.base.model import UnoModel, PostgresTypes
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/infrastructure/reports/errors.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/reports/models.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 18
Change from:
```python
from uno.model import UnoModel, PostgresTypes
```
To:
```python
from uno.domain.base.model import UnoModel, PostgresTypes
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/infrastructure/repositories/__init__.py

### Evaluate backward compatibility on line 42
Code: `# For backward compatibility`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

---

## src/uno/infrastructure/services/di.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/services/factory.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/sql/classes.py

### Evaluate backward compatibility on line 24
Code: `warnings.warn(`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Evaluate backward compatibility on line 27
Code: `DeprecationWarning,`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

---

## src/uno/infrastructure/sql/config.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/sql/emitter.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/sql/emitters/database.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/sql/errors.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/infrastructure/sql/registry.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/meta/models.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 8
Change from:
```python
from uno.model import UnoModel, PostgresTypes
```
To:
```python
from uno.domain.base.model import UnoModel, PostgresTypes
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/meta/repositories.py

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

---

## src/uno/migrations/env.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 14
Change from:
```python
from uno.model import UnoModel
```
To:
```python
from uno.domain.base.model import UnoModel
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/mixins.py

### Fix import on line 15
Change from:
```python
from uno.model import PostgresTypes
```
To:
```python
from uno.domain.base.model import PostgresTypes
```

---

## src/uno/model.py

### Evaluate backward compatibility on line 177
Code: `# For backward compatibility only - use BaseModel directly in new code`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---

## src/uno/values/errors.py

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

### Replace UnoError with BaseError
1. Add import: `from uno.core.base.error import BaseError`
2. Replace all occurrences of `UnoError` with `BaseError`

---

## src/uno/values/models.py

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Fix import on line 15
Change from:
```python
from uno.model import UnoModel, PostgresTypes
```
To:
```python
from uno.domain.base.model import UnoModel, PostgresTypes
```

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

### Replace UnoModel with BaseModel
1. Add import: `from uno.domain.base.model import BaseModel`
2. Replace all occurrences of `UnoModel` with `BaseModel`

---
