# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Test: `ENV=test pytest tests/path/to/test_file.py::TestClass::test_method`
- Test (verbose): `ENV=test pytest -vv --capture=tee-sys --show-capture=all`
- Type check: `mypy --install-types --non-interactive src/uno tests`
- Run app: `uvicorn main:app --reload`
- Database: `python src/scripts/createdb.py|dropdb.py|createsuperuser.py`

## Code Style Guidelines
- Python 3.12+ with type hints throughout
- Imports: group standard lib, third-party, local imports
- Naming: PascalCase for classes, snake_case for functions/variables
- Indentation: 4 spaces, ~88-100 char line length
- Documentation: comprehensive docstrings with Args/Returns/Raises
- Error handling: use custom UnoError with context and error codes
- Testing: pytest with fixtures, TestClass and test_method naming
- Project structure: modular with separation of concerns
- Boolean tests: Always use if var is None rather than if not var