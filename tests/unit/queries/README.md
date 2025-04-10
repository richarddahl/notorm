# Query Module Tests

This directory contains tests for the query-related modules in the NotORM framework. These tests focus on the functionality of filters and query construction.

## Test Files

### `test_filter.py`

Tests for the `UnoFilter` class and related lookup definitions. These tests verify:

- The structure and content of lookup dictionaries (text, numeric, boolean, datetime)
- Filter initialization and property access
- Cypher path generation with various options (with/without parent, escaping)
- Query generation for different data types (string, boolean, datetime)
- Validation and error handling for invalid inputs

Common issues when working with these tests:
- Use `@patch("uno.queries.filter.UnoFilter.cypher_path")` instead of `patch.object` for Pydantic models
- When testing SQL formatting, use flexible assertions that check for substrings rather than exact matches
- Ensure proper cleanup when mocking methods on Pydantic model instances

### `test_filter_manager.py`

Tests for the `UnoFilterManager` class which handles filter creation and validation. These tests verify:

- Filter creation from database tables and columns
- Type-specific filter handling (boolean, numeric, datetime, text)
- Filter parameter generation and validation
- Error handling for invalid filter parameters
- Special parameter handling (order_by, limit, offset)

Common issues when working with these tests:
- Avoid naming conflicts between mock objects and their attributes
- Use properties to protect attributes that might be overwritten
- Be careful with attribute setting in mock objects

## Running the Tests

To run just the query module tests:

```bash
ENV=test pytest tests/unit/queries/
```

To run a specific test file:

```bash
ENV=test pytest tests/unit/queries/test_filter.py
```

To run with verbose output:

```bash
ENV=test pytest tests/unit/queries/test_filter_manager.py -v
```