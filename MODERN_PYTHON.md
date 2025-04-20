# Modern Python & Tooling Audit

_Last updated: 2025-04-20_

## 1. Legacy Type Hint Audit

### Findings
- **Legacy type hints** (e.g., `List`, `Dict`, `Optional`, `Union`, etc. from `typing`) are still present in many modules (e.g., `domain_endpoints.py`, `multi_tenant.py`, `entities.py`, `errors.py`, and more).
- **Modern Python 3.10+ syntax** (`list[str]`, `str | None`, etc.) is not yet fully adopted across the codebase.
- **Action:** Refactor all type annotations to use modern built-in generics and union syntax. Ensure all `Success`/`Failure` calls use explicit type parameters.

### Example (before → after)
```python
from typing import List, Optional

def foo(bar: list[str], baz: Optional[int] = None) -> Optional[str]:
    ...
# becomes

def foo(bar: list[str], baz: int | None = None) -> str | None:
    ...
```

---

## 2. Tool Configuration Centralization

### Findings
- `pyproject.toml` exists and should be the single source of truth for tool configs.
- No `.cfg` files found, but further checks for `.rc` and other dotfiles are needed (e.g., `.flake8`, `.isort.cfg`, `.mypy.ini`).
- **Action:** Move all tool configs (e.g., `black`, `isort`, `mypy`, `pytest`, `ruff`, etc.) into `pyproject.toml` if not already present. Remove obsolete config files.

---

## 3. Deprecated/Legacy Code & Documentation

### Findings
- Several documentation files (`README.md`, `README_MODERNIZATION.md`, `CLAUDE.md`, etc.) reference legacy patterns, deprecated scripts, or migration steps.
- Some scripts and code comments still mention deprecated modules or patterns (e.g., legacy DI, repository migration, outdated async patterns).
- **Action:**
  - Remove or update references to legacy code in docs and comments.
  - Remove or archive deprecated scripts and modules.
  - Ensure all onboarding and developer docs reference only modern patterns and APIs.

---

## Progress Tracking
- [ ] Audit and refactor all type hints to modern syntax
- [ ] Centralize all tool configs in `pyproject.toml`
- [ ] Remove/update deprecated code and documentation

---

**For details, see search results and codebase audit logs. This file will be updated as progress continues.**
