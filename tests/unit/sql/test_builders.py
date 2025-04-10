# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the SQL builders.

These tests verify the functionality of the SQLFunctionBuilder and SQLTriggerBuilder classes,
ensuring they correctly generate SQL statements with the provided configurations.
"""

import pytest
from uno.sql.builders.function import SQLFunctionBuilder
from uno.sql.builders.trigger import SQLTriggerBuilder


class TestSQLFunctionBuilder:
    """Tests for the SQLFunctionBuilder class."""

    def test_basic_function_build(self):
        """Test building a basic function with minimal configuration."""
        # Build a simple function
        function_sql = (
            SQLFunctionBuilder()
            .with_schema("public")
            .with_name("test_function")
            .with_body("BEGIN RETURN NULL; END;")
            .build()
        )
        
        # Check that the built SQL contains expected elements
        assert "CREATE OR REPLACE FUNCTION public.test_function()" in function_sql
        assert "RETURNS TRIGGER" in function_sql  # Default return type
        assert "LANGUAGE plpgsql" in function_sql  # Default language
        assert "VOLATILE" in function_sql  # Default volatility
        assert "BEGIN RETURN NULL; END;" in function_sql

    def test_function_build_with_all_options(self):
        """Test building a function with all available options."""
        # Build a function with all options
        function_sql = (
            SQLFunctionBuilder()
            .with_schema("custom")
            .with_name("complex_function")
            .with_args("arg1 INT, arg2 TEXT")
            .with_return_type("TABLE(id INT, name TEXT)")
            .with_body("BEGIN RETURN QUERY SELECT 1, 'test'; END;")
            .with_language("sql")
            .with_volatility("STABLE")
            .as_security_definer()
            .with_db_name("test_db")
            .build()
        )
        
        # Check that the built SQL contains expected elements
        assert "CREATE OR REPLACE FUNCTION custom.complex_function(arg1 INT, arg2 TEXT)" in function_sql
        assert "RETURNS TABLE(id INT, name TEXT)" in function_sql
        assert "LANGUAGE sql" in function_sql
        assert "STABLE" in function_sql
        assert "SECURITY DEFINER" in function_sql
        assert "SET ROLE test_db_admin;" in function_sql
        assert "RETURN QUERY SELECT 1, 'test'" in function_sql

    def test_function_build_with_invalid_volatility(self):
        """Test that an invalid volatility raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid volatility"):
            (
                SQLFunctionBuilder()
                .with_schema("public")
                .with_name("test_function")
                .with_body("BEGIN RETURN NULL; END;")
                .with_volatility("INVALID")  # This should raise ValueError
                .build()
            )

    def test_function_build_without_required_params(self):
        """Test that missing required parameters raise a ValueError."""
        # Missing schema
        with pytest.raises(ValueError, match="Schema, name, and body are required"):
            (
                SQLFunctionBuilder()
                .with_name("test_function")
                .with_body("BEGIN RETURN NULL; END;")
                .build()
            )
        
        # Missing name
        with pytest.raises(ValueError, match="Schema, name, and body are required"):
            (
                SQLFunctionBuilder()
                .with_schema("public")
                .with_body("BEGIN RETURN NULL; END;")
                .build()
            )
        
        # Missing body
        with pytest.raises(ValueError, match="Schema, name, and body are required"):
            (
                SQLFunctionBuilder()
                .with_schema("public")
                .with_name("test_function")
                .build()
            )

    def test_auto_admin_role_insertion(self):
        """Test that admin role is automatically inserted when db_name is provided."""
        # Build a function with auto role insertion
        function_sql = (
            SQLFunctionBuilder()
            .with_schema("public")
            .with_name("test_function")
            .with_body("BEGIN RETURN NULL; END;")
            .with_db_name("test_db")
            .build()
        )
        
        # Check that the admin role is inserted
        assert "SET ROLE test_db_admin;" in function_sql
        
        # Build a function with auto role insertion disabled
        function_sql = (
            SQLFunctionBuilder()
            .with_schema("public")
            .with_name("test_function")
            .with_body("BEGIN RETURN NULL; END;")
            .with_db_name("test_db")
            .with_auto_role(False)
            .build()
        )
        
        # Check that the admin role is not inserted
        assert "SET ROLE test_db_admin;" not in function_sql


class TestSQLTriggerBuilder:
    """Tests for the SQLTriggerBuilder class."""

    def test_basic_trigger_build(self):
        """Test building a basic trigger with minimal configuration."""
        # Build a simple trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema("public")
            .with_table("users")
            .with_name("test_trigger")
            .with_function("test_function")
            .build()
        )
        
        # Check that the built SQL contains expected elements
        assert "CREATE OR REPLACE TRIGGER test_trigger" in trigger_sql
        assert "BEFORE UPDATE" in trigger_sql  # Default timing and operation
        assert "ON public.users" in trigger_sql
        assert "FOR EACH ROW" in trigger_sql  # Default for_each
        assert "EXECUTE FUNCTION public.test_function();" in trigger_sql

    def test_trigger_build_with_all_options(self):
        """Test building a trigger with all available options."""
        # Build a trigger with all options
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema("custom")
            .with_table("orders")
            .with_name("complex_trigger")
            .with_function("audit_function")
            .with_timing("AFTER")
            .with_operation("INSERT OR UPDATE OR DELETE")
            .with_for_each("STATEMENT")
            .build()
        )
        
        # Check that the built SQL contains expected elements
        assert "CREATE OR REPLACE TRIGGER complex_trigger" in trigger_sql
        assert "AFTER INSERT OR UPDATE OR DELETE" in trigger_sql
        assert "ON custom.orders" in trigger_sql
        assert "FOR EACH STATEMENT" in trigger_sql
        assert "EXECUTE FUNCTION custom.audit_function();" in trigger_sql

    def test_trigger_build_with_invalid_timing(self):
        """Test that an invalid timing raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid timing"):
            (
                SQLTriggerBuilder()
                .with_schema("public")
                .with_table("users")
                .with_name("test_trigger")
                .with_function("test_function")
                .with_timing("INVALID")  # This should raise ValueError
                .build()
            )

    def test_trigger_build_with_invalid_operation(self):
        """Test that an invalid operation raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid operation"):
            (
                SQLTriggerBuilder()
                .with_schema("public")
                .with_table("users")
                .with_name("test_trigger")
                .with_function("test_function")
                .with_operation("INVALID")  # This should raise ValueError
                .build()
            )

    def test_trigger_build_with_invalid_for_each(self):
        """Test that an invalid for_each raises a ValueError."""
        with pytest.raises(ValueError, match="Invalid for_each"):
            (
                SQLTriggerBuilder()
                .with_schema("public")
                .with_table("users")
                .with_name("test_trigger")
                .with_function("test_function")
                .with_for_each("INVALID")  # This should raise ValueError
                .build()
            )

    def test_trigger_build_without_required_params(self):
        """Test that missing required parameters raise a ValueError."""
        # Missing schema
        with pytest.raises(ValueError, match="Schema, table name, trigger name, and function name are required"):
            (
                SQLTriggerBuilder()
                .with_table("users")
                .with_name("test_trigger")
                .with_function("test_function")
                .build()
            )
        
        # Missing table
        with pytest.raises(ValueError, match="Schema, table name, trigger name, and function name are required"):
            (
                SQLTriggerBuilder()
                .with_schema("public")
                .with_name("test_trigger")
                .with_function("test_function")
                .build()
            )
        
        # Missing trigger name
        with pytest.raises(ValueError, match="Schema, table name, trigger name, and function name are required"):
            (
                SQLTriggerBuilder()
                .with_schema("public")
                .with_table("users")
                .with_function("test_function")
                .build()
            )
        
        # Missing function name
        with pytest.raises(ValueError, match="Schema, table name, trigger name, and function name are required"):
            (
                SQLTriggerBuilder()
                .with_schema("public")
                .with_table("users")
                .with_name("test_trigger")
                .build()
            )