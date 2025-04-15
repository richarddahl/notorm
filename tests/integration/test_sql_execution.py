# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Integration tests for SQL generation and execution.

This module tests the SQL generation and execution process with a real database connection,
verifying that generated SQL statements execute correctly and produce expected results.
"""

import pytest
import asyncio
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import uuid

from sqlalchemy import (
    MetaData, Table, Column, String, Text, Integer, 
    DateTime, Boolean, ForeignKey, func, select
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.exc import SQLAlchemyError

from uno.database.db import FilterParam
from uno.database.engine.sync import SyncEngineFactory
from uno.database.config import ConnectionConfig
from uno.settings import uno_settings
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.observers import BaseObserver, SQLObserver
from uno.core.errors import UnoError


# Custom test settings
class TestSettings:
    """Test settings for SQL execution integration tests."""
    
    DB_NAME = uno_settings.DB_NAME  # Use from main settings
    DB_SCHEMA = uno_settings.DB_SCHEMA  # Use from main settings
    DB_USER_PW = uno_settings.DB_USER_PW  # Use from main settings
    DB_SYNC_DRIVER = uno_settings.DB_SYNC_DRIVER  # Use from main settings
    UNO_ROOT = uno_settings.UNO_ROOT


# Test fixtures
@pytest.fixture
def connection_config():
    """Create a connection config for testing."""
    return ConnectionConfig(
        db_name=uno_settings.DB_NAME,
        db_schema=uno_settings.DB_SCHEMA,
        db_user_pw=uno_settings.DB_USER_PW,
        db_driver=uno_settings.DB_SYNC_DRIVER
    )


@pytest.fixture
def engine_factory():
    """Create an engine factory for testing."""
    return SyncEngineFactory()


@pytest.fixture
def db_connection(engine_factory, connection_config):
    """Create a database connection for testing."""
    engine = engine_factory.create_engine(connection_config)
    connection = engine.connect()
    transaction = connection.begin()
    
    yield connection
    
    # Rollback transaction to clean up
    transaction.rollback()
    connection.close()
    engine.dispose()


@pytest.fixture
def observer():
    """Create a SQL observer for testing."""
    class TestObserver(BaseObserver):
        def __init__(self):
            self.generated_statements = []
            self.executed_statements = []
            self.errors = []
            self.execution_times = []
        
        def on_sql_generated(self, emitter_name: str, statements: List[SQLStatement]) -> None:
            """Record SQL generation events."""
            for statement in statements:
                self.generated_statements.append({
                    "emitter": emitter_name,
                    "name": statement.name,
                    "type": statement.type,
                    "sql": statement.sql
                })
        
        def on_sql_executed(self, emitter_name: str, statements: List[SQLStatement], duration: float) -> None:
            """Record SQL execution events."""
            for statement in statements:
                self.executed_statements.append({
                    "emitter": emitter_name,
                    "name": statement.name,
                    "type": statement.type,
                    "sql": statement.sql
                })
            self.execution_times.append(duration)
        
        def on_sql_error(self, emitter_name: str, statements: List[SQLStatement], error: Exception) -> None:
            """Record SQL execution errors."""
            self.errors.append({
                "emitter": emitter_name,
                "error": str(error),
                "statements": [s.name for s in statements]
            })
    
    return TestObserver()


# SQL Emitter for testing basic table creation
class TestTableEmitter(SQLEmitter):
    """SQL emitter for creating test tables."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL for creating test tables."""
        schema_name = self.connection_config.db_schema
        
        # Create test table SQL
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.test_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            description TEXT,
            quantity INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            metadata JSONB
        );
        
        -- Add comments
        COMMENT ON TABLE {schema_name}.test_items IS 'Test items table for SQL integration tests';
        COMMENT ON COLUMN {schema_name}.test_items.id IS 'Unique identifier';
        COMMENT ON COLUMN {schema_name}.test_items.name IS 'Item name';
        """
        
        # Create index SQL
        create_index_sql = f"""
        CREATE INDEX IF NOT EXISTS idx_test_items_name ON {schema_name}.test_items (name);
        CREATE INDEX IF NOT EXISTS idx_test_items_created_at ON {schema_name}.test_items (created_at);
        CREATE INDEX IF NOT EXISTS idx_test_items_metadata ON {schema_name}.test_items USING GIN (metadata);
        """
        
        # Create statements
        return [
            SQLStatement(
                name="create_test_table",
                type=SQLStatementType.TABLE,
                sql=create_table_sql
            ),
            SQLStatement(
                name="create_test_indexes",
                type=SQLStatementType.INDEX,
                sql=create_index_sql,
                depends_on=["create_test_table"]
            )
        ]


# SQL Emitter for test functions
class TestFunctionEmitter(SQLEmitter):
    """SQL emitter for creating test functions."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL for creating test functions."""
        schema_name = self.connection_config.db_schema
        
        # Create function for inserting test items
        insert_function_sql = f"""
        CREATE OR REPLACE FUNCTION {schema_name}.insert_test_item(
            p_name VARCHAR,
            p_description TEXT DEFAULT NULL,
            p_quantity INTEGER DEFAULT 0,
            p_metadata JSONB DEFAULT NULL
        ) RETURNS UUID AS $$
        DECLARE
            new_id UUID;
        BEGIN
            INSERT INTO {schema_name}.test_items (
                name, 
                description, 
                quantity, 
                metadata
            ) VALUES (
                p_name,
                p_description,
                p_quantity,
                p_metadata
            ) RETURNING id INTO new_id;
            
            RETURN new_id;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Create function for retrieving test items with filters
        get_function_sql = f"""
        CREATE OR REPLACE FUNCTION {schema_name}.get_test_items(
            p_filter JSONB DEFAULT NULL
        ) RETURNS TABLE (
            id UUID,
            name VARCHAR,
            description TEXT,
            quantity INTEGER,
            is_active BOOLEAN,
            created_at TIMESTAMP WITH TIME ZONE,
            metadata JSONB
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                t.id,
                t.name,
                t.description,
                t.quantity,
                t.is_active,
                t.created_at,
                t.metadata
            FROM 
                {schema_name}.test_items t
            WHERE
                (p_filter IS NULL) OR
                (
                    (p_filter->>'name' IS NULL OR t.name ILIKE '%' || (p_filter->>'name') || '%') AND
                    (p_filter->>'min_quantity' IS NULL OR t.quantity >= (p_filter->>'min_quantity')::INTEGER) AND
                    (p_filter->>'max_quantity' IS NULL OR t.quantity <= (p_filter->>'max_quantity')::INTEGER) AND
                    (p_filter->>'is_active' IS NULL OR t.is_active = (p_filter->>'is_active')::BOOLEAN)
                );
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Create a function for a complex query with analytics
        analytics_function_sql = f"""
        CREATE OR REPLACE FUNCTION {schema_name}.analyze_test_items() 
        RETURNS TABLE (
            total_count BIGINT,
            active_count BIGINT,
            inactive_count BIGINT,
            avg_quantity NUMERIC,
            min_quantity INTEGER,
            max_quantity INTEGER,
            newest_item_id UUID,
            newest_item_name VARCHAR,
            newest_item_date TIMESTAMP WITH TIME ZONE
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH item_stats AS (
                SELECT
                    COUNT(*) AS total_count,
                    COUNT(*) FILTER (WHERE is_active = TRUE) AS active_count,
                    COUNT(*) FILTER (WHERE is_active = FALSE) AS inactive_count,
                    AVG(quantity) AS avg_quantity,
                    MIN(quantity) AS min_quantity,
                    MAX(quantity) AS max_quantity
                FROM
                    {schema_name}.test_items
            ),
            newest_item AS (
                SELECT
                    id,
                    name,
                    created_at
                FROM
                    {schema_name}.test_items
                ORDER BY
                    created_at DESC
                LIMIT 1
            )
            SELECT
                s.total_count,
                s.active_count,
                s.inactive_count,
                s.avg_quantity,
                s.min_quantity,
                s.max_quantity,
                n.id,
                n.name,
                n.created_at
            FROM
                item_stats s
            CROSS JOIN
                newest_item n;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Create statements
        return [
            SQLStatement(
                name="create_insert_function",
                type=SQLStatementType.FUNCTION,
                sql=insert_function_sql
            ),
            SQLStatement(
                name="create_get_function",
                type=SQLStatementType.FUNCTION,
                sql=get_function_sql
            ),
            SQLStatement(
                name="create_analytics_function",
                type=SQLStatementType.FUNCTION,
                sql=analytics_function_sql
            )
        ]


# SQL Emitter for test triggers
class TestTriggerEmitter(SQLEmitter):
    """SQL emitter for creating test triggers."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL for creating test triggers."""
        schema_name = self.connection_config.db_schema
        
        # Create audit function
        audit_function_sql = f"""
        CREATE OR REPLACE FUNCTION {schema_name}.test_items_audit_function()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                -- Log deletion
                RAISE NOTICE 'Item deleted: %', OLD.id;
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                -- Update metadata with modification info
                NEW.metadata = jsonb_set(
                    COALESCE(NEW.metadata, '{{}}'::jsonb),
                    '{{last_modified}}',
                    to_jsonb(now())
                );
                
                -- Record that an update happened
                NEW.metadata = jsonb_set(
                    COALESCE(NEW.metadata, '{{}}'::jsonb),
                    '{{last_operation}}',
                    '"UPDATE"'
                );
                
                RETURN NEW;
            ELSIF TG_OP = 'INSERT' THEN
                -- Set initial metadata
                NEW.metadata = jsonb_set(
                    COALESCE(NEW.metadata, '{{}}'::jsonb),
                    '{{created_by_trigger}}',
                    'true'
                );
                
                -- Record that an insert happened
                NEW.metadata = jsonb_set(
                    COALESCE(NEW.metadata, '{{}}'::jsonb),
                    '{{last_operation}}',
                    '"INSERT"'
                );
                
                RETURN NEW;
            END IF;
            
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Create trigger 
        create_trigger_sql = f"""
        DROP TRIGGER IF EXISTS test_items_audit_trigger ON {schema_name}.test_items;
        
        CREATE TRIGGER test_items_audit_trigger
        BEFORE INSERT OR UPDATE OR DELETE ON {schema_name}.test_items
        FOR EACH ROW EXECUTE FUNCTION {schema_name}.test_items_audit_function();
        """
        
        # Create statements
        return [
            SQLStatement(
                name="create_audit_function",
                type=SQLStatementType.FUNCTION,
                sql=audit_function_sql
            ),
            SQLStatement(
                name="create_audit_trigger",
                type=SQLStatementType.TRIGGER,
                sql=create_trigger_sql,
                depends_on=["create_audit_function"]
            )
        ]


# SQL Emitter for cleanup
class CleanupEmitter(SQLEmitter):
    """SQL emitter for cleaning up test objects."""
    
    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL for cleaning up test objects."""
        schema_name = self.connection_config.db_schema
        
        # Drop all test objects
        cleanup_sql = f"""
        -- Drop triggers
        DROP TRIGGER IF EXISTS test_items_audit_trigger ON {schema_name}.test_items;
        
        -- Drop functions
        DROP FUNCTION IF EXISTS {schema_name}.test_items_audit_function();
        DROP FUNCTION IF EXISTS {schema_name}.insert_test_item(VARCHAR, TEXT, INTEGER, JSONB);
        DROP FUNCTION IF EXISTS {schema_name}.get_test_items(JSONB);
        DROP FUNCTION IF EXISTS {schema_name}.analyze_test_items();
        
        -- Drop indexes
        DROP INDEX IF EXISTS {schema_name}.idx_test_items_name;
        DROP INDEX IF EXISTS {schema_name}.idx_test_items_created_at;
        DROP INDEX IF EXISTS {schema_name}.idx_test_items_metadata;
        
        -- Drop tables
        DROP TABLE IF EXISTS {schema_name}.test_items;
        """
        
        # Create statements
        return [
            SQLStatement(
                name="cleanup_test_objects",
                type=SQLStatementType.FUNCTION,
                sql=cleanup_sql
            )
        ]


# Tests
class TestSQLExecution:
    """Integration tests for SQL execution."""
    
    def test_table_creation_execution(self, db_connection, connection_config, observer):
        """Test creating tables and executing queries."""
        # Create emitters with observer
        table_emitter = TestTableEmitter(
            connection_config=connection_config
        )
        table_emitter.observers.append(observer)
        
        # Generate and execute SQL for table creation
        table_emitter.emit_sql(db_connection)
        
        # Verify observer captured events
        assert len(observer.generated_statements) == 2
        assert len(observer.executed_statements) == 2
        assert observer.generated_statements[0]["name"] == "create_test_table"
        assert observer.generated_statements[1]["name"] == "create_test_indexes"
        
        # Verify the table exists in the database
        result = db_connection.execute(
            f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = '{connection_config.db_schema}' AND table_name = 'test_items')"
        ).scalar()
        assert result is True
        
        # Verify the indexes exist in the database
        indexes_query = f"""
        SELECT indexname FROM pg_indexes 
        WHERE schemaname = '{connection_config.db_schema}' 
        AND tablename = 'test_items'
        """
        indexes = [row[0] for row in db_connection.execute(indexes_query).fetchall()]
        assert "idx_test_items_name" in indexes
        assert "idx_test_items_created_at" in indexes
        assert "idx_test_items_metadata" in indexes
    
    def test_function_creation_and_usage(self, db_connection, connection_config, observer):
        """Test creating and using SQL functions."""
        # Create tables first
        table_emitter = TestTableEmitter(
            connection_config=connection_config
        )
        table_emitter.emit_sql(db_connection)
        
        # Create functions
        function_emitter = TestFunctionEmitter(
            connection_config=connection_config
        )
        function_emitter.observers.append(observer)
        function_emitter.emit_sql(db_connection)
        
        # Verify observer captured events for function creation
        assert len(observer.generated_statements) == 3
        assert len(observer.executed_statements) == 3
        assert observer.generated_statements[0]["name"] == "create_insert_function"
        assert observer.generated_statements[1]["name"] == "create_get_function"
        assert observer.generated_statements[2]["name"] == "create_analytics_function"
        
        # Test the insert function
        schema_name = connection_config.db_schema
        # Insert test items
        items_to_insert = [
            {"name": "Test Item 1", "description": "Description 1", "quantity": 10, "metadata": {"category": "A"}},
            {"name": "Test Item 2", "description": "Description 2", "quantity": 20, "metadata": {"category": "B"}},
            {"name": "Test Item 3", "description": "Description 3", "quantity": 30, "metadata": {"category": "A"}},
            {"name": "Test Item 4", "description": "Description 4", "quantity": 40, "metadata": {"category": "C"}},
            {"name": "Test Item 5", "description": "Description 5", "quantity": 50, "metadata": {"category": "B"}}
        ]
        
        for item in items_to_insert:
            query = f"""
            SELECT {schema_name}.insert_test_item(
                %(name)s, 
                %(description)s, 
                %(quantity)s, 
                %(metadata)s::jsonb
            )
            """
            db_connection.execute(
                query, 
                {
                    "name": item["name"],
                    "description": item["description"],
                    "quantity": item["quantity"],
                    "metadata": json.dumps(item["metadata"])
                }
            )
        
        # Test the get function - get all items
        count_result = db_connection.execute(
            f"SELECT COUNT(*) FROM {schema_name}.test_items"
        ).scalar()
        assert count_result == 5
        
        # Test the get function with filters
        # Filter by min quantity
        filter_query = f"""
        SELECT * FROM {schema_name}.get_test_items(
            '{{"min_quantity": 30}}'::jsonb
        )
        """
        result = db_connection.execute(filter_query).fetchall()
        assert len(result) == 3  # Items with quantity >= 30
        
        # Filter by name
        filter_query = f"""
        SELECT * FROM {schema_name}.get_test_items(
            '{{"name": "Item 2"}}'::jsonb
        )
        """
        result = db_connection.execute(filter_query).fetchall()
        assert len(result) == 1  # Only Item 2 should match
        assert result[0][1] == "Test Item 2"  # name column
        
        # Test the analytics function
        analytics_query = f"""
        SELECT * FROM {schema_name}.analyze_test_items()
        """
        result = db_connection.execute(analytics_query).fetchone()
        
        # Verify analytics results
        assert result[0] == 5  # total_count
        assert result[1] == 5  # active_count (all are active by default)
        assert result[2] == 0  # inactive_count
        assert float(result[3]) == 30.0  # avg_quantity
        assert result[4] == 10  # min_quantity
        assert result[5] == 50  # max_quantity
        assert result[7] is not None  # newest_item_name
    
    def test_trigger_execution(self, db_connection, connection_config, observer):
        """Test creating and executing triggers."""
        # Create tables first
        table_emitter = TestTableEmitter(
            connection_config=connection_config
        )
        table_emitter.emit_sql(db_connection)
        
        # Create functions
        function_emitter = TestFunctionEmitter(
            connection_config=connection_config
        )
        function_emitter.emit_sql(db_connection)
        
        # Create triggers
        trigger_emitter = TestTriggerEmitter(
            connection_config=connection_config
        )
        trigger_emitter.observers.append(observer)
        trigger_emitter.emit_sql(db_connection)
        
        # Verify observer captured events for trigger creation
        assert len(observer.generated_statements) == 2
        assert len(observer.executed_statements) == 2
        assert observer.generated_statements[0]["name"] == "create_audit_function"
        assert observer.generated_statements[1]["name"] == "create_audit_trigger"
        
        schema_name = connection_config.db_schema
        
        # Insert an item and verify trigger modified the metadata
        insert_query = f"""
        SELECT {schema_name}.insert_test_item(
            'Trigger Test Item', 
            'Testing trigger', 
            100, 
            '{{"initial": true}}'::jsonb
        )
        """
        item_id = db_connection.execute(insert_query).scalar()
        
        # Fetch the item and verify metadata was updated by the trigger
        select_query = f"""
        SELECT metadata FROM {schema_name}.test_items
        WHERE id = '{item_id}'
        """
        result = db_connection.execute(select_query).scalar()
        
        # Check that the trigger added the expected metadata fields
        assert result is not None
        metadata = result
        assert metadata.get("created_by_trigger") is True
        assert metadata.get("last_operation") == "INSERT"
        assert metadata.get("initial") is True
        
        # Update the item and verify trigger modifies metadata
        update_query = f"""
        UPDATE {schema_name}.test_items
        SET quantity = 200
        WHERE id = '{item_id}'
        RETURNING metadata
        """
        updated_metadata = db_connection.execute(update_query).scalar()
        
        # Check that the trigger updated the metadata
        assert updated_metadata is not None
        assert updated_metadata.get("last_operation") == "UPDATE"
        assert "last_modified" in updated_metadata
    
    def test_dependency_ordering_execution(self, db_connection, connection_config, observer):
        """Test executing SQL statements with dependencies in the correct order."""
        # Create the emitter for triggers which has dependencies
        trigger_emitter = TestTriggerEmitter(
            connection_config=connection_config
        )
        trigger_emitter.observers.append(observer)
        
        # Deliberate failure - try to execute trigger before table exists
        with pytest.raises(SQLAlchemyError) as exc_info:
            trigger_emitter.emit_sql(db_connection)
        
        assert "does not exist" in str(exc_info.value)
        assert len(observer.errors) == 0  # Errors are not captured since execute_sql raises directly
        
        # Create table and retry
        table_emitter = TestTableEmitter(
            connection_config=connection_config
        )
        table_emitter.emit_sql(db_connection)
        
        # Now trigger should succeed
        trigger_emitter.emit_sql(db_connection)
        
        # Verify observer captured events in the correct order
        assert len(observer.executed_statements) == 4  # 2 from table, 2 from trigger
        
        # Check for presence and order of dependency-ordered statements
        function_names = [stmt["name"] for stmt in observer.executed_statements]
        
        # Check the table was created before indexes
        assert function_names.index("create_test_table") < function_names.index("create_test_indexes")
        
        # Check the audit function was created before the trigger
        assert function_names.index("create_audit_function") < function_names.index("create_audit_trigger")
    
    def test_complex_query_execution(self, db_connection, connection_config, observer):
        """Test executing complex queries with multiple functions and CTEs."""
        # Set up the database first
        table_emitter = TestTableEmitter(connection_config=connection_config)
        table_emitter.emit_sql(db_connection)
        
        function_emitter = TestFunctionEmitter(connection_config=connection_config)
        function_emitter.emit_sql(db_connection)
        
        trigger_emitter = TestTriggerEmitter(connection_config=connection_config)
        trigger_emitter.emit_sql(db_connection)
        
        schema_name = connection_config.db_schema
        
        # Create some test items
        categories = ["A", "B", "C", "D"]
        for i in range(20):
            item = {
                "name": f"Complex Item {i+1}",
                "description": f"Complex item description {i+1}",
                "quantity": (i+1) * 5,
                "metadata": {
                    "category": categories[i % len(categories)], 
                    "tags": [f"tag{j}" for j in range(1, (i % 5) + 2)]
                }
            }
            
            insert_query = f"""
            SELECT {schema_name}.insert_test_item(
                %(name)s, 
                %(description)s, 
                %(quantity)s, 
                %(metadata)s::jsonb
            )
            """
            db_connection.execute(
                insert_query, 
                {
                    "name": item["name"],
                    "description": item["description"],
                    "quantity": item["quantity"],
                    "metadata": json.dumps(item["metadata"])
                }
            )
        
        # Create a complex query that uses CTEs and window functions
        complex_query = f"""
        WITH category_stats AS (
            SELECT
                (metadata->>'category') AS category,
                COUNT(*) AS item_count,
                SUM(quantity) AS total_quantity,
                AVG(quantity) AS avg_quantity,
                JSONB_AGG(
                    JSONB_BUILD_OBJECT(
                        'id', id,
                        'name', name,
                        'quantity', quantity,
                        'tags', metadata->'tags'
                    )
                ) AS items
            FROM
                {schema_name}.test_items
            GROUP BY
                metadata->>'category'
        ),
        ranked_categories AS (
            SELECT
                category,
                item_count,
                total_quantity,
                avg_quantity,
                items,
                RANK() OVER (ORDER BY total_quantity DESC) AS quantity_rank,
                RANK() OVER (ORDER BY item_count DESC) AS count_rank
            FROM
                category_stats
        )
        SELECT
            category,
            item_count,
            total_quantity,
            avg_quantity,
            quantity_rank,
            count_rank,
            items
        FROM
            ranked_categories
        ORDER BY
            (quantity_rank + count_rank) ASC
        """
        
        # Execute the complex query
        result = db_connection.execute(complex_query).fetchall()
        
        # Verify the results
        assert len(result) == len(categories)
        
        # Check the structure of the first result
        first_category = result[0]
        assert first_category[0] in categories  # category
        assert isinstance(first_category[1], int)  # item_count
        assert isinstance(first_category[2], int)  # total_quantity
        assert isinstance(first_category[3], float)  # avg_quantity
        assert isinstance(first_category[4], int)  # quantity_rank
        assert isinstance(first_category[5], int)  # count_rank
        assert isinstance(first_category[6], dict)  # items
        assert len(first_category[6]) > 0  # items array
    
    def test_transaction_handling(self, engine_factory, connection_config, observer):
        """Test SQL execution within transactions with proper rollback on failure."""
        # Create a connection with a transaction
        engine = engine_factory.create_engine(connection_config)
        connection = engine.connect()
        transaction = connection.begin()
        
        try:
            # Set up the database first
            table_emitter = TestTableEmitter(connection_config=connection_config)
            table_emitter.emit_sql(connection)
            
            function_emitter = TestFunctionEmitter(connection_config=connection_config)
            function_emitter.emit_sql(connection)
            
            schema_name = connection_config.db_schema
            
            # Insert some data
            insert_query = f"""
            SELECT {schema_name}.insert_test_item(
                'Transaction Test Item', 
                'Testing transactions', 
                100, 
                '{{"transaction": true}}'::jsonb
            )
            """
            connection.execute(insert_query)
            
            # Verify the data exists in this transaction
            count_query = f"SELECT COUNT(*) FROM {schema_name}.test_items"
            count = connection.execute(count_query).scalar()
            assert count == 1
            
            # Intentionally introduce an error to trigger rollback
            error_query = "SELECT invalid_function();"
            with pytest.raises(SQLAlchemyError):
                connection.execute(error_query)
            
            # Rollback the transaction
            transaction.rollback()
            
            # Start a new transaction to verify rollback worked
            new_transaction = connection.begin()
            try:
                # Check that the table exists but data was rolled back
                count = connection.execute(count_query).scalar()
                assert count == 0  # Data should have been rolled back
            finally:
                new_transaction.rollback()
                connection.close()
                engine.dispose()
        except:
            transaction.rollback()
            connection.close()
            engine.dispose()
            raise
    
    def test_cleanup(self, db_connection, connection_config):
        """Test cleaning up all test objects."""
        # Clean up any existing objects
        cleanup_emitter = CleanupEmitter(connection_config=connection_config)
        cleanup_emitter.emit_sql(db_connection)
        
        schema_name = connection_config.db_schema
        
        # Verify the test_items table doesn't exist
        result = db_connection.execute(
            f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = '{schema_name}' AND table_name = 'test_items')"
        ).scalar()
        assert result is False
        
        # Verify the functions don't exist
        result = db_connection.execute(
            f"SELECT COUNT(*) FROM pg_proc WHERE proname = 'insert_test_item' AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = '{schema_name}')"
        ).scalar()
        assert result == 0
        
        result = db_connection.execute(
            f"SELECT COUNT(*) FROM pg_proc WHERE proname = 'test_items_audit_function' AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = '{schema_name}')"
        ).scalar()
        assert result == 0