# TESTING.md

## 1. Testing Philosophy

- **Test-Driven Development (TDD):** Encourage writing tests before implementation for new features and bug fixes.
- **Pyramid Approach:** Focus on unit tests, supplement with integration and end-to-end tests.
- **Isolate Side Effects:** Use mocks/fakes for external dependencies (DB, APIs, etc.).
- **Result Monad Pattern:** Test both success and failure cases, especially for monadic error handling.

## 2. Tools & Libraries

- **pytest:** Primary test runner and assertion library.
- **pytest-cov:** Code coverage reporting.
- **pytest-mock:** For mocking dependencies.
- **factory_boy:** For generating test data.
- **hypothesis:** Property-based testing for edge cases.
- **tox:** For multi-environment testing (optional, recommended for library code).
- **mypy:** Static type checking.
- **ruff or flake8:** Linting for code style and quality.
- **coverage.py:** Standalone coverage reporting (if needed).

## 3. Test Structure

```
/tests
    /unit
        test_<module>.py
    /integration
        test_<integration>.py
    /e2e
        test_<workflow>.py
    /factories
        <entity>_factory.py
conftest.py
```

- **Unit:** Isolated tests for functions, classes, and methods.
- **Integration:** Test interactions between components (e.g., repository ↔ DB).
- **E2E:** Simulate real user workflows, possibly via API or CLI.

## 4. Coverage Goals

- **Unit:** ≥ 90%
- **Integration:** ≥ 80%
- **E2E:** ≥ 70% (focus on critical paths)

## 5. Writing Good Tests

- Use descriptive names and docstrings.
- Test both "happy path" and edge/error cases.
- Use fixtures for setup/teardown.
- Prefer factories over hand-crafted data.
- Assert on both output and side effects.

## 6. Running Tests

- **All tests:** `pytest`
- **With coverage:** `pytest --cov=src`
- **Type checks:** `mypy src/`
- **Lint:** `ruff src/` or `flake8 src/`
- **Multi-env:** `tox`

## 7. CI Integration

- Add test, lint, and type-check steps to your CI pipeline (GitHub Actions, GitLab CI, etc.).
- Fail builds on test, lint, or type-check failures.

## 8. Advanced Topics

- **Property-based testing:** Use `hypothesis` for functions with complex input spaces.
- **Database tests:** Use transaction rollbacks or in-memory DBs for speed/isolation.
- **Dependency Injection:** Use test containers/providers to inject mocks/fakes.

## 9. Example `pytest` Configuration

Add a `pytest.ini`:

```ini
[pytest]
testpaths = tests
addopts = --strict-markers
```
