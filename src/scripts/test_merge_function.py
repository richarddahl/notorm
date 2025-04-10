#!/usr/bin/env python

# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Manual test script for the TableMergeFunction.

This script creates a test table, generates the merge function SQL,
and tests the function with various operations.

Usage:
    python src/scripts/test_merge_function.py
"""

import os
import json
import argparse
from sqlalchemy import MetaData, Table, Column, String, Integer, UniqueConstraint, create_engine
from sqlalchemy.sql import text

from uno.sql.emitters import TableMergeFunction
from uno.database.config import ConnectionConfig
from uno.settings import uno_settings


def main():
    """Run the manual test."""
    parser = argparse.ArgumentParser(description="Test the TableMergeFunction")
    parser.add_argument("--schema", default=uno_settings.DB_SCHEMA, help="Database schema")
    parser.add_argument("--db-name", default=uno_settings.DB_NAME, help="Database name")
    parser.add_argument("--drop-only", action="store_true", help="Only drop existing objects")
    args = parser.parse_args()
    
    # Create connection configuration
    connection_config = ConnectionConfig(
        db_name=args.db_name,
        db_schema=args.schema,
        db_user_pw=uno_settings.DB_USER_PW,
        db_driver=uno_settings.DB_SYNC_DRIVER
    )
    
    # Create engine
    engine = create_engine(connection_config.connection_url)
    
    # Define test table
    metadata = MetaData()
    test_table = Table(
        "test_merge_manual",
        metadata,
        Column("id", String(26), primary_key=True),
        Column("email", String(255)),
        Column("username", String(100)),
        Column("name", String(255)),
        Column("age", Integer),
        UniqueConstraint("email", name="test_merge_manual_email_key"),
        UniqueConstraint("username", name="test_merge_manual_username_key"),
        schema=args.schema
    )
    
    # Drop existing objects
    with engine.connect() as conn:
        # Drop function if exists
        conn.execute(text(
            f"DROP FUNCTION IF EXISTS {args.schema}.merge_test_merge_manual_record(jsonb)"
        ))
        # Drop table if exists
        conn.execute(text(
            f"DROP TABLE IF EXISTS {args.schema}.test_merge_manual"
        ))
        conn.commit()
        print("Dropped existing objects")
    
    if args.drop_only:
        return
    
    # Create table
    metadata.create_all(engine)
    print(f"Created table {args.schema}.test_merge_manual")
    
    # Create merge function
    emitter = TableMergeFunction(
        table=test_table,
        connection_config=connection_config
    )
    
    # Generate and print SQL
    statements = emitter.generate_sql()
    sql = statements[0].sql
    
    print("\nGenerated SQL for merge function:")
    print("-" * 80)
    print(sql)
    print("-" * 80)
    
    # Execute SQL
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print(f"Created function {args.schema}.merge_test_merge_manual_record")
    
    # Test the function
    def execute_merge(data):
        """Execute merge function with given data."""
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT {args.schema}.merge_test_merge_manual_record(:data)"),
                {"data": json.dumps(data)}
            ).scalar()
            return json.loads(result)
    
    # Test 1: Insert new record
    data1 = {
        "id": "user123",
        "email": "test@example.com",
        "username": "testuser",
        "name": "Test User",
        "age": 30
    }
    print("\nTest 1: Insert new record")
    print(f"Input: {json.dumps(data1, indent=2)}")
    result1 = execute_merge(data1)
    print(f"Result: {json.dumps(result1, indent=2)}")
    
    # Test 2: Update record
    data2 = {
        "id": "user123",
        "name": "Updated Name",
        "age": 31
    }
    print("\nTest 2: Update record")
    print(f"Input: {json.dumps(data2, indent=2)}")
    result2 = execute_merge(data2)
    print(f"Result: {json.dumps(result2, indent=2)}")
    
    # Test 3: Select with no changes
    data3 = {
        "id": "user123",
        "name": "Updated Name"  # No change from previous
    }
    print("\nTest 3: Select with no changes")
    print(f"Input: {json.dumps(data3, indent=2)}")
    result3 = execute_merge(data3)
    print(f"Result: {json.dumps(result3, indent=2)}")
    
    # Test 4: Insert using unique constraint
    data4 = {
        "email": "another@example.com",
        "username": "another",
        "name": "Another User",
        "age": 25
    }
    print("\nTest 4: Insert using unique constraint")
    print(f"Input: {json.dumps(data4, indent=2)}")
    result4 = execute_merge(data4)
    print(f"Result: {json.dumps(result4, indent=2)}")
    
    # Test 5: Update using unique constraint
    data5 = {
        "email": "another@example.com",
        "name": "Updated Another"
    }
    print("\nTest 5: Update using unique constraint")
    print(f"Input: {json.dumps(data5, indent=2)}")
    result5 = execute_merge(data5)
    print(f"Result: {json.dumps(result5, indent=2)}")
    
    print("\nAll tests completed successfully")
    
    # Optional: Drop the table and function
    if input("\nDrop test objects? (y/n): ").lower() == 'y':
        with engine.connect() as conn:
            conn.execute(text(
                f"DROP FUNCTION IF EXISTS {args.schema}.merge_test_merge_manual_record(jsonb)"
            ))
            conn.execute(text(
                f"DROP TABLE IF EXISTS {args.schema}.test_merge_manual"
            ))
            conn.commit()
        print("Dropped test objects")


if __name__ == "__main__":
    main()