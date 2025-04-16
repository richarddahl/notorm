"""
Tests for SQL module domain entities.

This module contains tests for all domain entities defined in the SQL module,
including value objects, entities, and aggregates.
"""

import uuid
import pytest
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

from uno.domain.core import Entity, AggregateRoot, ValueObject
from uno.sql.entities import (
    SQLStatementId, 
    SQLEmitterId, 
    SQLConfigId,
    SQLStatementType,
    SQLTransactionIsolationLevel,
    SQLFunctionVolatility,
    SQLFunctionLanguage,
    SQLStatement,
    SQLExecution,
    SQLEmitter,
    SQLFunction,
    SQLTrigger,
    DatabaseConnectionInfo,
    SQLConfiguration
)


class TestSQLValueObjects:
    """Tests for SQL module value objects."""

    def test_sql_statement_id_creation(self):
        """Test creating a SQLStatementId value object."""
        id_value = str(uuid.uuid4())
        statement_id = SQLStatementId(value=id_value)
        assert statement_id.value == id_value
        
        # Test immutability
        with pytest.raises(AttributeError):
            statement_id.value = "new_value"
    
    def test_sql_emitter_id_creation(self):
        """Test creating a SQLEmitterId value object."""
        id_value = str(uuid.uuid4())
        emitter_id = SQLEmitterId(value=id_value)
        assert emitter_id.value == id_value
        
        # Test immutability
        with pytest.raises(AttributeError):
            emitter_id.value = "new_value"
    
    def test_sql_config_id_creation(self):
        """Test creating a SQLConfigId value object."""
        id_value = str(uuid.uuid4())
        config_id = SQLConfigId(value=id_value)
        assert config_id.value == id_value
        
        # Test immutability
        with pytest.raises(AttributeError):
            config_id.value = "new_value"
    
    def test_value_objects_equality(self):
        """Test equality of value objects with same values."""
        id_value = str(uuid.uuid4())
        
        # Same value should produce equal objects
        statement_id1 = SQLStatementId(value=id_value)
        statement_id2 = SQLStatementId(value=id_value)
        assert statement_id1 == statement_id2
        
        # Different value should produce unequal objects
        statement_id3 = SQLStatementId(value=str(uuid.uuid4()))
        assert statement_id1 != statement_id3


class TestSQLEnums:
    """Tests for SQL module enums."""
    
    def test_sql_statement_type_enum(self):
        """Test SQLStatementType enum values."""
        assert SQLStatementType.FUNCTION.value == "function"
        assert SQLStatementType.TRIGGER.value == "trigger"
        assert SQLStatementType.INDEX.value == "index"
        assert SQLStatementType.CONSTRAINT.value == "constraint"
        assert SQLStatementType.GRANT.value == "grant"
        assert SQLStatementType.VIEW.value == "view"
        assert SQLStatementType.PROCEDURE.value == "procedure"
        assert SQLStatementType.TABLE.value == "table"
        assert SQLStatementType.ROLE.value == "role"
        assert SQLStatementType.SCHEMA.value == "schema"
        assert SQLStatementType.EXTENSION.value == "extension"
        assert SQLStatementType.DATABASE.value == "database"
        assert SQLStatementType.INSERT.value == "insert"
    
    def test_sql_transaction_isolation_level_enum(self):
        """Test SQLTransactionIsolationLevel enum values."""
        assert SQLTransactionIsolationLevel.READ_UNCOMMITTED.value == "READ UNCOMMITTED"
        assert SQLTransactionIsolationLevel.READ_COMMITTED.value == "READ COMMITTED"
        assert SQLTransactionIsolationLevel.REPEATABLE_READ.value == "REPEATABLE READ"
        assert SQLTransactionIsolationLevel.SERIALIZABLE.value == "SERIALIZABLE"
        assert SQLTransactionIsolationLevel.AUTOCOMMIT.value == "AUTOCOMMIT"
    
    def test_sql_function_volatility_enum(self):
        """Test SQLFunctionVolatility enum values."""
        assert SQLFunctionVolatility.VOLATILE.value == "VOLATILE"
        assert SQLFunctionVolatility.STABLE.value == "STABLE"
        assert SQLFunctionVolatility.IMMUTABLE.value == "IMMUTABLE"
    
    def test_sql_function_language_enum(self):
        """Test SQLFunctionLanguage enum values."""
        assert SQLFunctionLanguage.PLPGSQL.value == "plpgsql"
        assert SQLFunctionLanguage.SQL.value == "sql"
        assert SQLFunctionLanguage.PYTHON.value == "plpython3u"
        assert SQLFunctionLanguage.PLTCL.value == "pltcl"


class TestSQLStatement:
    """Tests for SQLStatement entity."""
    
    def test_sql_statement_creation(self):
        """Test creating a SQLStatement entity."""
        id_value = str(uuid.uuid4())
        statement_id = SQLStatementId(value=id_value)
        statement = SQLStatement(
            id=statement_id,
            name="test_function",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
        )
        
        assert statement.id == statement_id
        assert statement.name == "test_function"
        assert statement.type == SQLStatementType.FUNCTION
        assert "CREATE FUNCTION test_function()" in statement.sql
        assert isinstance(statement.created_at, datetime)
        assert statement.depends_on == []
    
    def test_sql_statement_with_dependencies(self):
        """Test creating a SQLStatement entity with dependencies."""
        id_value = str(uuid.uuid4())
        statement_id = SQLStatementId(value=id_value)
        statement = SQLStatement(
            id=statement_id,
            name="test_function",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;",
            depends_on=["another_function", "some_table"]
        )
        
        assert statement.depends_on == ["another_function", "some_table"]
        assert statement.has_dependency("another_function")
        assert statement.has_dependency("some_table")
        assert not statement.has_dependency("non_existent_dependency")
    
    def test_add_dependency(self):
        """Test adding a dependency to a SQLStatement."""
        id_value = str(uuid.uuid4())
        statement_id = SQLStatementId(value=id_value)
        statement = SQLStatement(
            id=statement_id,
            name="test_function",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
        )
        
        statement.add_dependency("new_dependency")
        assert statement.has_dependency("new_dependency")
        
        # Test adding a duplicate dependency doesn't duplicate it
        statement.add_dependency("new_dependency")
        assert statement.depends_on.count("new_dependency") == 1
    
    def test_remove_dependency(self):
        """Test removing a dependency from a SQLStatement."""
        id_value = str(uuid.uuid4())
        statement_id = SQLStatementId(value=id_value)
        statement = SQLStatement(
            id=statement_id,
            name="test_function",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;",
            depends_on=["dep1", "dep2", "dep3"]
        )
        
        # Test removing an existing dependency
        result = statement.remove_dependency("dep2")
        assert result is True
        assert not statement.has_dependency("dep2")
        assert statement.depends_on == ["dep1", "dep3"]
        
        # Test removing a non-existent dependency
        result = statement.remove_dependency("non_existent")
        assert result is False
        assert statement.depends_on == ["dep1", "dep3"]


class TestSQLExecution:
    """Tests for SQLExecution entity."""
    
    def test_sql_execution_creation(self):
        """Test creating a SQLExecution entity."""
        statement_id = SQLStatementId(value=str(uuid.uuid4()))
        execution = SQLExecution(
            statement_id=statement_id,
            duration_ms=150.5,
            success=True
        )
        
        assert execution.statement_id == statement_id
        assert execution.duration_ms == 150.5
        assert execution.success is True
        assert execution.error_message is None
        assert isinstance(execution.executed_at, datetime)
        assert isinstance(execution.id, str)
        assert uuid.UUID(execution.id)  # Verifies it's a valid UUID
        assert execution.metadata == {}
    
    def test_sql_execution_failure(self):
        """Test creating a SQLExecution entity for a failed execution."""
        statement_id = SQLStatementId(value=str(uuid.uuid4()))
        execution = SQLExecution(
            statement_id=statement_id,
            duration_ms=50.2,
            success=False,
            error_message="Syntax error in SQL statement"
        )
        
        assert execution.success is False
        assert execution.error_message == "Syntax error in SQL statement"
    
    def test_sql_execution_with_metadata(self):
        """Test creating a SQLExecution entity with metadata."""
        statement_id = SQLStatementId(value=str(uuid.uuid4()))
        metadata = {
            "user": "test_user",
            "connection_id": 12345,
            "row_count": 42
        }
        
        execution = SQLExecution(
            statement_id=statement_id,
            duration_ms=75.8,
            success=True,
            metadata=metadata
        )
        
        assert execution.metadata == metadata
        assert execution.metadata["user"] == "test_user"
        assert execution.metadata["connection_id"] == 12345
        assert execution.metadata["row_count"] == 42


class TestSQLEmitter:
    """Tests for SQLEmitter entity."""
    
    def test_sql_emitter_creation(self):
        """Test creating a SQLEmitter entity."""
        emitter_id = SQLEmitterId(value=str(uuid.uuid4()))
        emitter = SQLEmitter(
            id=emitter_id,
            name="function_emitter",
            description="Emits SQL function statements",
            statement_types=[SQLStatementType.FUNCTION, SQLStatementType.PROCEDURE]
        )
        
        assert emitter.id == emitter_id
        assert emitter.name == "function_emitter"
        assert emitter.description == "Emits SQL function statements"
        assert SQLStatementType.FUNCTION in emitter.statement_types
        assert SQLStatementType.PROCEDURE in emitter.statement_types
        assert emitter.configuration == {}
        assert isinstance(emitter.created_at, datetime)
        assert isinstance(emitter.updated_at, datetime)
    
    def test_generates_statement_type(self):
        """Test checking if an emitter generates a specific statement type."""
        emitter_id = SQLEmitterId(value=str(uuid.uuid4()))
        emitter = SQLEmitter(
            id=emitter_id,
            name="function_emitter",
            statement_types=[SQLStatementType.FUNCTION, SQLStatementType.PROCEDURE]
        )
        
        assert emitter.generates_statement_type(SQLStatementType.FUNCTION) is True
        assert emitter.generates_statement_type(SQLStatementType.PROCEDURE) is True
        assert emitter.generates_statement_type(SQLStatementType.TRIGGER) is False
        assert emitter.generates_statement_type(SQLStatementType.TABLE) is False
    
    def test_add_statement_type(self):
        """Test adding a statement type to an emitter."""
        emitter_id = SQLEmitterId(value=str(uuid.uuid4()))
        emitter = SQLEmitter(
            id=emitter_id,
            name="function_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        
        original_updated_at = emitter.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        emitter.add_statement_type(SQLStatementType.TRIGGER)
        
        assert emitter.generates_statement_type(SQLStatementType.TRIGGER) is True
        assert emitter.updated_at > original_updated_at
        
        # Test adding duplicate doesn't change the list
        emitter.add_statement_type(SQLStatementType.FUNCTION)
        assert emitter.statement_types.count(SQLStatementType.FUNCTION) == 1
    
    def test_update_configuration(self):
        """Test updating the configuration of an emitter."""
        emitter_id = SQLEmitterId(value=str(uuid.uuid4()))
        emitter = SQLEmitter(
            id=emitter_id,
            name="function_emitter",
            configuration={"schema": "public", "add_comments": True}
        )
        
        original_updated_at = emitter.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        emitter.update_configuration({"schema": "custom", "prepend_header": True})
        
        assert emitter.configuration == {
            "schema": "custom",  # Overwrites existing key
            "add_comments": True,  # Keeps existing key
            "prepend_header": True  # Adds new key
        }
        
        assert emitter.updated_at > original_updated_at


class TestSQLFunction:
    """Tests for SQLFunction entity."""
    
    def test_sql_function_creation(self):
        """Test creating a SQLFunction entity."""
        function = SQLFunction(
            name="test_function",
            body="BEGIN RETURN NEW; END;",
            args="id INTEGER, name TEXT",
            schema="custom",
            return_type="RECORD",
            language=SQLFunctionLanguage.PLPGSQL,
            volatility=SQLFunctionVolatility.STABLE,
            security_definer=True
        )
        
        assert function.name == "test_function"
        assert function.body == "BEGIN RETURN NEW; END;"
        assert function.args == "id INTEGER, name TEXT"
        assert function.schema == "custom"
        assert function.return_type == "RECORD"
        assert function.language == SQLFunctionLanguage.PLPGSQL
        assert function.volatility == SQLFunctionVolatility.STABLE
        assert function.security_definer is True
        assert isinstance(function.id, str)
        assert uuid.UUID(function.id)  # Verifies it's a valid UUID
        assert isinstance(function.created_at, datetime)
        assert isinstance(function.updated_at, datetime)
    
    def test_function_defaults(self):
        """Test default values for SQLFunction entity."""
        function = SQLFunction(
            name="test_function",
            body="BEGIN RETURN NEW; END;"
        )
        
        assert function.args == ""
        assert function.schema == "public"
        assert function.return_type == "TRIGGER"
        assert function.language == SQLFunctionLanguage.PLPGSQL
        assert function.volatility == SQLFunctionVolatility.VOLATILE
        assert function.security_definer is False
    
    def test_to_sql(self):
        """Test generating SQL statement for a function."""
        function = SQLFunction(
            name="test_function",
            body="BEGIN RETURN NEW; END;",
            args="id INTEGER, name TEXT",
            schema="custom",
            return_type="RECORD",
            language=SQLFunctionLanguage.PLPGSQL,
            volatility=SQLFunctionVolatility.STABLE,
            security_definer=True
        )
        
        sql = function.to_sql()
        
        assert "CREATE OR REPLACE FUNCTION custom.test_function(id INTEGER, name TEXT)" in sql
        assert "RETURNS RECORD" in sql
        assert "LANGUAGE plpgsql" in sql
        assert "STABLE" in sql
        assert "SECURITY DEFINER" in sql
        assert "BEGIN RETURN NEW; END;" in sql
    
    def test_update_body(self):
        """Test updating the body of a function."""
        function = SQLFunction(
            name="test_function",
            body="BEGIN RETURN NEW; END;"
        )
        
        original_updated_at = function.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        function.update_body("BEGIN RETURN NULL; END;")
        
        assert function.body == "BEGIN RETURN NULL; END;"
        assert function.updated_at > original_updated_at
    
    def test_update_args(self):
        """Test updating the arguments of a function."""
        function = SQLFunction(
            name="test_function",
            body="BEGIN RETURN NEW; END;",
            args="id INTEGER"
        )
        
        original_updated_at = function.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        function.update_args("id INTEGER, name TEXT, active BOOLEAN")
        
        assert function.args == "id INTEGER, name TEXT, active BOOLEAN"
        assert function.updated_at > original_updated_at


class TestSQLTrigger:
    """Tests for SQLTrigger entity."""
    
    def test_sql_trigger_creation(self):
        """Test creating a SQLTrigger entity."""
        trigger = SQLTrigger(
            name="test_trigger",
            table="users",
            function_name="user_audit_function",
            schema="app",
            events=["INSERT", "UPDATE"],
            when="NEW.active = TRUE",
            for_each="ROW"
        )
        
        assert trigger.name == "test_trigger"
        assert trigger.table == "users"
        assert trigger.function_name == "user_audit_function"
        assert trigger.schema == "app"
        assert trigger.events == ["INSERT", "UPDATE"]
        assert trigger.when == "NEW.active = TRUE"
        assert trigger.for_each == "ROW"
        assert isinstance(trigger.id, str)
        assert uuid.UUID(trigger.id)  # Verifies it's a valid UUID
        assert isinstance(trigger.created_at, datetime)
        assert isinstance(trigger.updated_at, datetime)
    
    def test_trigger_defaults(self):
        """Test default values for SQLTrigger entity."""
        trigger = SQLTrigger(
            name="test_trigger",
            table="users",
            function_name="user_audit_function"
        )
        
        assert trigger.schema == "public"
        assert trigger.events == []
        assert trigger.when is None
        assert trigger.for_each == "ROW"
    
    def test_to_sql(self):
        """Test generating SQL statement for a trigger."""
        trigger = SQLTrigger(
            name="test_trigger",
            table="users",
            function_name="user_audit_function",
            schema="app",
            events=["INSERT", "UPDATE"],
            when="NEW.active = TRUE",
            for_each="ROW"
        )
        
        sql = trigger.to_sql()
        
        assert "CREATE OR REPLACE TRIGGER test_trigger" in sql
        assert "ROW INSERT OR UPDATE ON app.users" in sql
        assert "WHEN (NEW.active = TRUE)" in sql
        assert "EXECUTE FUNCTION app.user_audit_function()" in sql
    
    def test_to_sql_without_when(self):
        """Test generating SQL statement for a trigger without a when clause."""
        trigger = SQLTrigger(
            name="test_trigger",
            table="users",
            function_name="user_audit_function",
            events=["INSERT", "UPDATE", "DELETE"],
            for_each="STATEMENT"
        )
        
        sql = trigger.to_sql()
        
        assert "CREATE OR REPLACE TRIGGER test_trigger" in sql
        assert "STATEMENT INSERT OR UPDATE OR DELETE ON public.users" in sql
        assert "WHEN" not in sql
        assert "EXECUTE FUNCTION public.user_audit_function()" in sql
    
    def test_update_events(self):
        """Test updating the events of a trigger."""
        trigger = SQLTrigger(
            name="test_trigger",
            table="users",
            function_name="user_audit_function",
            events=["INSERT"]
        )
        
        original_updated_at = trigger.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        trigger.update_events(["INSERT", "UPDATE", "DELETE"])
        
        assert trigger.events == ["INSERT", "UPDATE", "DELETE"]
        assert trigger.updated_at > original_updated_at
    
    def test_update_when_condition(self):
        """Test updating the when condition of a trigger."""
        trigger = SQLTrigger(
            name="test_trigger",
            table="users",
            function_name="user_audit_function",
            when="NEW.active = TRUE"
        )
        
        original_updated_at = trigger.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        trigger.update_when_condition("NEW.active = TRUE AND NEW.role = 'admin'")
        
        assert trigger.when == "NEW.active = TRUE AND NEW.role = 'admin'"
        assert trigger.updated_at > original_updated_at
        
        # Test setting when condition to None
        trigger.update_when_condition(None)
        assert trigger.when is None


class TestDatabaseConnectionInfo:
    """Tests for DatabaseConnectionInfo entity."""
    
    def test_database_connection_info_creation(self):
        """Test creating a DatabaseConnectionInfo entity."""
        connection_info = DatabaseConnectionInfo(
            db_name="testdb",
            db_user="testuser",
            db_host="localhost",
            db_port=5432,
            db_schema="app",
            admin_role="testdb_admin",
            writer_role="testdb_writer",
            reader_role="testdb_reader"
        )
        
        assert connection_info.db_name == "testdb"
        assert connection_info.db_user == "testuser"
        assert connection_info.db_host == "localhost"
        assert connection_info.db_port == 5432
        assert connection_info.db_schema == "app"
        assert connection_info.admin_role == "testdb_admin"
        assert connection_info.writer_role == "testdb_writer"
        assert connection_info.reader_role == "testdb_reader"
        assert isinstance(connection_info.id, str)
        assert uuid.UUID(connection_info.id)  # Verifies it's a valid UUID
    
    def test_connection_info_defaults(self):
        """Test default values for DatabaseConnectionInfo entity."""
        connection_info = DatabaseConnectionInfo(
            db_name="testdb",
            db_user="testuser",
            db_host="localhost"
        )
        
        assert connection_info.db_port == 5432
        assert connection_info.db_schema == "public"
        assert connection_info.admin_role == "testdb_admin"
        assert connection_info.writer_role == "testdb_writer"
        assert connection_info.reader_role == "testdb_reader"
    
    def test_post_init_role_generation(self):
        """Test post-init method generates default roles based on db_name."""
        connection_info = DatabaseConnectionInfo(
            db_name="customdb",
            db_user="testuser",
            db_host="localhost"
        )
        
        assert connection_info.admin_role == "customdb_admin"
        assert connection_info.writer_role == "customdb_writer"
        assert connection_info.reader_role == "customdb_reader"
        
        # Test that explicitly set roles are not overwritten
        connection_info = DatabaseConnectionInfo(
            db_name="customdb",
            db_user="testuser",
            db_host="localhost",
            admin_role="explicit_admin",
            writer_role="explicit_writer",
            reader_role="explicit_reader"
        )
        
        assert connection_info.admin_role == "explicit_admin"
        assert connection_info.writer_role == "explicit_writer"
        assert connection_info.reader_role == "explicit_reader"


class TestSQLConfiguration:
    """Tests for SQLConfiguration entity."""
    
    def test_sql_configuration_creation(self):
        """Test creating a SQLConfiguration entity."""
        config_id = SQLConfigId(value=str(uuid.uuid4()))
        connection_info = DatabaseConnectionInfo(
            db_name="testdb",
            db_user="testuser",
            db_host="localhost"
        )
        emitter1 = SQLEmitter(
            id=SQLEmitterId(value=str(uuid.uuid4())),
            name="function_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        emitter2 = SQLEmitter(
            id=SQLEmitterId(value=str(uuid.uuid4())),
            name="trigger_emitter",
            statement_types=[SQLStatementType.TRIGGER]
        )
        
        config = SQLConfiguration(
            id=config_id,
            name="test_config",
            description="Test SQL configuration",
            connection_info=connection_info,
            emitters=[emitter1, emitter2],
            metadata={"version": "1.0", "environment": "test"}
        )
        
        assert config.id == config_id
        assert config.name == "test_config"
        assert config.description == "Test SQL configuration"
        assert config.connection_info == connection_info
        assert len(config.emitters) == 2
        assert emitter1 in config.emitters
        assert emitter2 in config.emitters
        assert config.metadata == {"version": "1.0", "environment": "test"}
        assert isinstance(config.created_at, datetime)
        assert isinstance(config.updated_at, datetime)
    
    def test_add_emitter(self):
        """Test adding an emitter to a configuration."""
        config_id = SQLConfigId(value=str(uuid.uuid4()))
        config = SQLConfiguration(
            id=config_id,
            name="test_config"
        )
        
        original_updated_at = config.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        emitter = SQLEmitter(
            id=SQLEmitterId(value=str(uuid.uuid4())),
            name="function_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        
        config.add_emitter(emitter)
        
        assert emitter in config.emitters
        assert config.updated_at > original_updated_at
        
        # Test adding a duplicate emitter doesn't duplicate it
        config.add_emitter(emitter)
        assert len(config.emitters) == 1
    
    def test_remove_emitter(self):
        """Test removing an emitter from a configuration."""
        config_id = SQLConfigId(value=str(uuid.uuid4()))
        emitter1_id = SQLEmitterId(value=str(uuid.uuid4()))
        emitter2_id = SQLEmitterId(value=str(uuid.uuid4()))
        
        emitter1 = SQLEmitter(
            id=emitter1_id,
            name="function_emitter"
        )
        emitter2 = SQLEmitter(
            id=emitter2_id,
            name="trigger_emitter"
        )
        
        config = SQLConfiguration(
            id=config_id,
            name="test_config",
            emitters=[emitter1, emitter2]
        )
        
        original_updated_at = config.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        # Test removing an existing emitter
        result = config.remove_emitter(emitter1_id)
        
        assert result is True
        assert emitter1 not in config.emitters
        assert len(config.emitters) == 1
        assert config.updated_at > original_updated_at
        
        # Test removing a non-existent emitter
        non_existent_id = SQLEmitterId(value=str(uuid.uuid4()))
        result = config.remove_emitter(non_existent_id)
        
        assert result is False
        assert len(config.emitters) == 1
    
    def test_get_emitter(self):
        """Test getting an emitter by ID from a configuration."""
        config_id = SQLConfigId(value=str(uuid.uuid4()))
        emitter1_id = SQLEmitterId(value=str(uuid.uuid4()))
        emitter2_id = SQLEmitterId(value=str(uuid.uuid4()))
        
        emitter1 = SQLEmitter(
            id=emitter1_id,
            name="function_emitter"
        )
        emitter2 = SQLEmitter(
            id=emitter2_id,
            name="trigger_emitter"
        )
        
        config = SQLConfiguration(
            id=config_id,
            name="test_config",
            emitters=[emitter1, emitter2]
        )
        
        # Test getting an existing emitter
        result = config.get_emitter(emitter1_id)
        assert result == emitter1
        
        # Test getting a non-existent emitter
        non_existent_id = SQLEmitterId(value=str(uuid.uuid4()))
        result = config.get_emitter(non_existent_id)
        assert result is None
    
    def test_update_metadata(self):
        """Test updating metadata of a configuration."""
        config_id = SQLConfigId(value=str(uuid.uuid4()))
        config = SQLConfiguration(
            id=config_id,
            name="test_config",
            metadata={"version": "1.0", "environment": "test"}
        )
        
        original_updated_at = config.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        config.update_metadata({"version": "1.1", "author": "test_user"})
        
        assert config.metadata == {
            "version": "1.1",  # Overwrites existing key
            "environment": "test",  # Keeps existing key
            "author": "test_user"  # Adds new key
        }
        assert config.updated_at > original_updated_at
    
    def test_set_connection_info(self):
        """Test setting connection info of a configuration."""
        config_id = SQLConfigId(value=str(uuid.uuid4()))
        config = SQLConfiguration(
            id=config_id,
            name="test_config"
        )
        
        original_updated_at = config.updated_at
        
        # Wait a tiny bit to ensure timestamp will be different
        import time
        time.sleep(0.001)
        
        connection_info = DatabaseConnectionInfo(
            db_name="testdb",
            db_user="testuser",
            db_host="localhost"
        )
        
        config.set_connection_info(connection_info)
        
        assert config.connection_info == connection_info
        assert config.updated_at > original_updated_at