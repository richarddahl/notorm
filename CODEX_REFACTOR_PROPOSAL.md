# Codex Refactor Proposal

## 1. Overview

This document outlines a high-level refactoring plan to standardize and modernize the Python codebase. It catalogs existing modern idioms, identifies legacy or brittle anti-patterns, and proposes a phased strategy to improve consistency, maintainability, and safety.

## 2. Modern Python Patterns Already in Place
The codebase leverages many modern practices, including:
- **Type Hints (PEP 484+)**: Extensive use of parameter and return annotations, featuring `TypeVar`, `Protocol`, `Literal`, and other advanced typing constructs.
- **f‑Strings**: Clear, concise string interpolation through f‑strings in log messages, SQL statements, and error messages.
- **Async/Await Ecosystem**: `async def` functions, `await`, `contextlib.asynccontextmanager`, and `AsyncExitStack` for asynchronous I/O and task management.
- **Dataclasses**: `@dataclass` for lightweight, boilerplate-free data containers.
- **Pathlib**: Use of `pathlib.Path` for filesystem operations, replacing `os.path`.
- **Comprehensions & Generators**: List, dict, and set comprehensions, plus generator expressions, for concise iteration logic.
- **Context Managers**: `with` statements for resource management (files, DB sessions, locks).
- **Typed Protocols & ABCs**: Interface definitions via `typing.Protocol` and `abc.ABC` for pluggable components.
- **Logging Framework**: Structured logging with the standard `logging` module, custom handlers, and lazy interpolation.

## 3. Legacy & Anti-Patterns to Address
Despite strong patterns, several areas need refactoring:
- **Old‑Style Formatting**: `%` and `.format()`-based strings (~600 occurrences) coexist with f‑strings.
- **Regex‑Based Code Transforms**: Scripts like `modernize_datetime.py` rely on fragile regex instead of AST-based codemods.
- **Hand‑Rolled CLI Parsers**: Many scripts use `sys.argv` and manual parsing; lacks auto-generated help and type safety.
- **Broad Exception Handlers**: `except:` and generic `except Exception` clauses mask hidden bugs and swallow unexpected errors.
- **Mutable Default Arguments**: Patterns that risk shared state across calls instead of using `None` + in-body initialization.
- **Dynamic Import Hacks**: `uno/core/async_utils.py` uses runtime import gymnastics to work around keyword conflicts.
- **Ad‑hoc Logging vs. print()**: Some scripts still use `print()` for user feedback instead of unified logging.
- **Global Singletons**: Module-level factories and managers (`engine_factory`, `init_db_manager`) increase coupling and complicate testing.
- **Manual SQL Assembly**: A few modules concatenate SQL strings directly rather than using parameterized queries or SQLAlchemy core.
- **Code Duplication**: Repeated boilerplate across `src/scripts/` (settings loading, logger setup, error handling).

## 4. Proposed Refactoring Strategy
We recommend a phased approach, delivering incremental safety and consistency gains:

### Phase 1: Formatting & CLI Standardization
1. Migrate all `%` and `.format()` usages to f‑strings for consistency.
2. Introduce a shared CLI framework (`argparse` or `click`):
   - Centralize help generation, subcommands, and type coercion.
   - Replace manual `sys.argv` parsing in `src/scripts/`.
3. Replace `print()` calls in scripts with the standardized logger setup.

### Phase 2: AST-Driven Codemods & Exception Hardening
1. Replace regex-based scripts with AST-based transformations (e.g., `lib2to3` or `ast` + `astor`):
   - Modernize `datetime.utcnow()` → `datetime.now(timezone.UTC)` safely across the codebase.
2. Audit and tighten exception handlers:
   - Change blind `except:` to targeted exceptions.
   - Propagate or log unexpected error types instead of silencing.
3. Remove mutable default arguments by refactoring to `None` sentinel and in-body initialization.

### Phase 3: Dependency Injection & Dynamic Imports
1. Factor out common startup logic in `src/scripts/cli_utils.py`:
   - Logger configuration, settings loading, error reporting.
2. Refactor dynamic import hacks:
   - Rename or alias `uno.core.async` subfolder to avoid Python keyword conflicts.
   - Simplify `uno/core/async_utils.py` to normal imports post-package rename.
3. Convert module-level singletons to factory functions or DI containers:
   - Increase testability by allowing injection of mocks.

### Phase 4: SQL Safety & Linting Enforcement
1. Migrate direct SQL concatenations to parameterized queries (using SQLAlchemy core/ORM or `psycopg` parameter syntax).
2. Introduce pre-commit hooks and CI checks:
   - `flake8`/`black` for style, `mypy` for type coverage, `isort` for import order.
   - Fail builds on new violations to enforce consistency.

## 5. Roadmap & Milestones
| Phase | Deliverables | Timeline |
|------:|:-------------|:--------:|
| 1     | f‑string audit, shared CLI framework, logging consolidation | 2 weeks |
| 2     | AST codemods, exception refactor, default args audit | 4 weeks |
| 3     | DI refactor, async package rename, shared `cli_utils` library | 3 weeks |
| 4     | SQL safety migration, CI gating (mypy/flake8) | 2 weeks |

## 6. Impact & Risks
- **No Backward Compatibility Required**: This library is new and not yet in use, so breaking changes are acceptable and no effort to preserve backward compatibility is needed.
- **Review Overhead**: Large codemods require careful review; mitigate with incremental PRs and trunk-based development.
- **Testing Gaps**: Ensure full coverage before refactoring critical paths. Mitigation: Expand integration tests around DB and async flows.

## 7. Next Steps
1. Kick off Phase 1 with a spike on a single script directory to validate the shared CLI approach.
2. Draft initial CLI helper module (`cli_utils.py`) and integrate with a few scripts.
3. Circulate this proposal for team feedback and finalize the project plan.

_Document generated: CODEX refactor proposal v1.0_