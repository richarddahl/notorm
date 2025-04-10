# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the SQL statement representations.

These tests verify the functionality of the SQLStatement class and SQLStatementType enum,
ensuring they correctly represent SQL statements and their types.
"""

import pytest
from uno.sql.statement import SQLStatement, SQLStatementType


class TestSQLStatementType:
    """Tests for the SQLStatementType enum."""

    def test_sql_statement_type_values(self):
        """Test that SQLStatementType enum has expected values."""
        # Check that all expected types are defined
        expected_types = [
            "FUNCTION", "TRIGGER", "INDEX", "CONSTRAINT", "GRANT",
            "VIEW", "PROCEDURE", "TABLE", "ROLE", "SCHEMA",
            "EXTENSION", "DATABASE", "INSERT"
        ]
        
        for type_name in expected_types:
            # Verify the type exists in the enum
            assert hasattr(SQLStatementType, type_name)
            
            # Verify the enum value is lowercase of the name
            enum_member = getattr(SQLStatementType, type_name)
            assert enum_member.value == type_name.lower()


class TestSQLStatement:
    """Tests for the SQLStatement class."""

    def test_sql_statement_initialization(self):
        """Test initializing an SQLStatement with minimal parameters."""
        # Create a statement with just the required parameters
        statement = SQLStatement(
            name="test_statement",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;"
        )
        
        # Check that the attributes are set correctly
        assert statement.name == "test_statement"
        assert statement.type == SQLStatementType.FUNCTION
        assert "CREATE FUNCTION test()" in statement.sql
        assert statement.depends_on == []  # Default empty list

    def test_sql_statement_with_dependencies(self):
        """Test initializing an SQLStatement with dependencies."""
        # Create a statement with dependencies
        statement = SQLStatement(
            name="test_trigger",
            type=SQLStatementType.TRIGGER,
            sql="CREATE TRIGGER test_trigger AFTER INSERT ON test_table FOR EACH ROW EXECUTE FUNCTION test_function();",
            depends_on=["test_function", "test_table"]
        )
        
        # Check that the attributes are set correctly
        assert statement.name == "test_trigger"
        assert statement.type == SQLStatementType.TRIGGER
        assert "CREATE TRIGGER test_trigger" in statement.sql
        assert statement.depends_on == ["test_function", "test_table"]

    def test_sql_statement_model_validation(self):
        """Test that SQLStatement performs model validation."""
        # Missing required parameter 'name'
        with pytest.raises(ValueError):
            SQLStatement(
                type=SQLStatementType.FUNCTION,
                sql="CREATE FUNCTION test() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;"
            )
        
        # Missing required parameter 'type'
        with pytest.raises(ValueError):
            SQLStatement(
                name="test_statement",
                sql="CREATE FUNCTION test() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;"
            )
        
        # Missing required parameter 'sql'
        with pytest.raises(ValueError):
            SQLStatement(
                name="test_statement",
                type=SQLStatementType.FUNCTION
            )
        
        # Invalid type for 'type' parameter
        with pytest.raises(ValueError):
            SQLStatement(
                name="test_statement",
                type="FUNCTION",  # Should be an SQLStatementType enum
                sql="CREATE FUNCTION test() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;"
            )
        
        # Invalid type for 'depends_on' parameter
        with pytest.raises(ValueError):
            SQLStatement(
                name="test_statement",
                type=SQLStatementType.FUNCTION,
                sql="CREATE FUNCTION test() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE plpgsql;",
                depends_on="test_dependency"  # Should be a list
            )