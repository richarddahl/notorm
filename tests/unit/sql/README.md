# SQL Module Tests

This directory contains tests for the SQL-related modules in the NotORM framework. These tests focus on the SQL generation and execution components.

## Test Files

### `test_emitters.py`

Tests for the SQL emitters that generate database objects:
- Function emitters (InsertMetaRecordFunction, RecordStatusFunction)
- Trigger emitters (InsertMetaRecordTrigger)
- Grant emitters (AlterGrants)
- Base emitter functionality (formatting, configuration)

These tests verify that the SQL generation logic correctly produces valid SQL statements for creating database objects like functions, triggers, and grants with the proper configuration values.

### `test_builders.py`

Tests for the SQL builders that construct SQL statements:
- SQLFunctionBuilder for creating function definitions
- SQLTriggerBuilder for creating trigger definitions

These tests ensure that the builders correctly handle different configurations, validate inputs, and generate properly formatted SQL statements.

### `test_statement.py`

Tests for the SQL statement representations:
- SQLStatement class that represents a single SQL statement with metadata
- SQLStatementType enum that defines the types of SQL statements

These tests verify the basic structure and validation of SQL statements and their types.

## Running the Tests

To run just the SQL module tests:

```bash
ENV=test pytest tests/unit/sql/
```

To run a specific test file:

```bash
ENV=test pytest tests/unit/sql/test_emitters.py
```

## Testing Strategy

The SQL module tests follow these principles:

1. **Isolation**: Tests mock database connections and configuration to avoid external dependencies
2. **Completeness**: Tests cover both basic and complex uses of builders and emitters
3. **Validation**: Tests verify that validators correctly catch and report invalid inputs
4. **Output verification**: Tests check that generated SQL contains the expected elements

Most tests focus on validating the structure and content of the generated SQL rather than the exact format, since whitespace and indentation may vary without affecting functionality.