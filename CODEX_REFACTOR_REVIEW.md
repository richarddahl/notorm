<!--
  CODEX_REFACTOR_REVIEW.md
  Review of legacy modules and code not integrated into the unified refactoring of the Uno platform.
-->
# Refactor Review: Legacy Code Audit

## Overview
This document identifies code modules, scripts, and artifacts in the repository that appear to be legacy or no longer integrated with the modern, unified approaches implemented in the recent refactoring. These items can be candidates for removal, archiving, or relocation to a separate tools repository.

---

## 1. Legacy Test Files (Project Root)
These standalone test scripts duplicate functionality already covered by the structured `tests/` directory and are not integrated into the unified test suite:
  - `basic_event_test.py`  
    • Defines its own `BasicEvent` class and is never imported by application code.
  - `test_basic_event.py`  
    • Pulls in `uno.core.events.basic.BasicEvent` with a `sys.path` hack; duplicates `tests/core/test_event_basic.py`.
  
**Recommendation:** Remove both files from the project root.

---

## 2. Root-level Artifacts
- `uno.log`  
  • Application log file checked into version control.  
- `__pycache__/` (at project root)  
  • Python bytecode cache directory; should be in `.gitignore` and removed.
- `migrations/update_insert_permissions_function.sql`  
  • A standalone SQL migration script not managed by the new Alembic/Uno migration framework (`src/uno/migrations`).
  
**Recommendation:**  
- Add `uno.log` and root `__pycache__/` to `.gitignore` or remove entirely.  
- Consolidate or re-implement `update_insert_permissions_function.sql` as an Alembic/Uno migration under `src/uno/migrations`.

---

## 3. Legacy Refactoring & DDD Generation Scripts (`src/scripts`)
The following scripts under `src/scripts/` were primarily used to drive one-time modernization, validation, and DDD code generation. They are not part of the runtime or CI scripts defined in `pyproject.toml` and clutter the codebase:

- **Modernization Utilities**
  - `modernize_async.py`
  - `modernize_datetime.py`
  - `modernize_domain.py`
  - `modernize_error_classes.py`
  - `modernize_imports.py`
  - `modernize_result.py`

- **Refactoring Helpers**
  - `refactor_dependency_service.py`
  - `test_merge_function.py`

- **DDD Compliance & Generation**
  - `ddd_generator.py`
  - `ddd_lib.py`
  - `check_attributes_ddd.py`
  - `check_authorization_ddd.py`
  - `check_meta_ddd.py`
  - `check_queries_ddd.py`
  - `check_reports_ddd.py`
  - `check_values_ddd.py`
  - `check_workflow_ddd.py`

- **Validation Scripts**
  - `validate_clean_slate.py`
  - `validate_config_protocol.py`
  - `validate_import_standards.py`
  - `validate_protocols.py`
  - `validate_reports.py`
  - `validate_workflows.py`

**Recommendation:** Archive or remove these scripts. If ongoing DDD code generation tooling is needed, migrate a minimal subset (e.g., `ddd-lib`) into a dedicated developer-tools package or repo.

---

## 4. Deprecated Example Code
- `src/uno/examples/`  
  • Contains example applications and domain models. Review which examples remain relevant; obsolete ones can be pruned.

**Recommendation:** Rationalize examples under a single `examples/` folder or relocate to documentation site; remove duplicates.

---

## 5. Summary of Recommendations
1. Remove or ignore root-level test scripts (`basic_event_test.py`, `test_basic_event.py`) and `uno.log`.  
2. Clean up root `__pycache__/` directory; rely on standard build artifacts.  
3. Migrate `migrations/update_insert_permissions_function.sql` into the unified Alembic/Uno migrations.  
4. Archive or delete one-time modernization and validation scripts in `src/scripts`.  
5. Clean up and consolidate example code under `src/uno/examples/`.

These steps will reduce maintenance overhead and clarify which code is integral to the unified Uno framework versus development tooling or legacy artifacts.