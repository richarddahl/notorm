# Import Standards Fix Guide

This guide provides specific fixes for 78 violations across 27 files.

## src/uno/application/dto/__init__.py

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

---

## src/uno/application/dto/dto.py

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

---

## src/uno/application/dto/manager.py

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

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

## src/uno/core/base/__init__.py

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

---

## src/uno/core/base/dto.py

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

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

## src/uno/dependencies/service.py

### Replace UnoRepository with BaseRepository
1. Add import: `from uno.core.base.repository import BaseRepository`
2. Replace all occurrences of `UnoRepository` with `BaseRepository`

### Replace UnoService with BaseService
1. Add import: `from uno.core.base.service import BaseService`
2. Replace all occurrences of `UnoService` with `BaseService`

---

## src/uno/devtools/codegen/api.py

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

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

---

## src/uno/devtools/codegen/project.py

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

---

## src/uno/devtools/codegen/service.py

### Replace UnoService with BaseService
1. Add import: `from uno.core.base.service import BaseService`
2. Replace all occurrences of `UnoService` with `BaseService`

### Replace UnoService with BaseService
1. Add import: `from uno.core.base.service import BaseService`
2. Replace all occurrences of `UnoService` with `BaseService`

### Replace UnoService with BaseService
1. Add import: `from uno.core.base.service import BaseService`
2. Replace all occurrences of `UnoService` with `BaseService`

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

## src/uno/domain/__init__.py

### Evaluate backward compatibility on line 327
Code: `warnings.warn(`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

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

---

## src/uno/dto/__init__.py

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

---

## src/uno/dto/dto_manager.py

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

---

## src/uno/dto/entities/__init__.py

### Replace BaseDTO with BaseDTO
1. Add import: `from uno.core.base.dto import BaseDTO`
2. Replace all occurrences of `BaseDTO` with `BaseDTO`

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

## src/uno/infrastructure/repositories/__init__.py

### Evaluate backward compatibility on line 42
Code: `# For backward compatibility`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

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

## src/uno/model.py

### Evaluate backward compatibility on line 177
Code: `# For backward compatibility only - use BaseModel directly in new code`
If this is a backward compatibility layer, consider removing it completely if not needed.
If this is a deprecation warning, ensure it directs users to the correct standardized imports.

---
