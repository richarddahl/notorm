"""
Schema manager for database operations.

This module provides functionality for managing database schemas,
including DDL operations and migrations.
"""

import logging
from typing import Optional, List, Dict, Any, Callable, ContextManager
from contextlib import contextmanager

import psycopg
from sqlalchemy import text

from uno.database.config import ConnectionConfig


class DBManager:
    """
    Manager for database schema operations.

    This class provides methods for executing DDL statements and
    managing database schemas.
    """

    def __init__(
        self,
        connection_provider: Callable[[], ContextManager[psycopg.Connection]],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the schema manager.

        Args:
            connection_provider: Function that provides a database connection
            logger: Optional logger instance
        """
        self.get_connection = connection_provider
        self.logger = logger or logging.getLogger(__name__)

    def execute_ddl(self, ddl: str) -> None:
        """
        Execute a DDL statement.

        Args:
            ddl: The DDL statement to execute
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                self.logger.debug(f"Executing DDL: {ddl[:100]}...")
                cursor.execute(ddl)
            conn.commit()

    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script containing multiple statements.

        Args:
            script: The SQL script to execute
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                self.logger.debug(f"Executing SQL script ({len(script)} characters)")
                cursor.execute(script)
            conn.commit()

    def create_schema(self, schema_name: str) -> None:
        """
        Create a database schema if it doesn't exist.

        Args:
            schema_name: The name of the schema to create
        """
        ddl = f"CREATE SCHEMA IF NOT EXISTS {schema_name}"
        self.execute_ddl(ddl)

    def drop_schema(self, schema_name: str, cascade: bool = False) -> None:
        """
        Drop a database schema.

        Args:
            schema_name: The name of the schema to drop
            cascade: Whether to drop objects within the schema
        """
        cascade_stmt = "CASCADE" if cascade else ""
        ddl = f"DROP SCHEMA IF EXISTS {schema_name} {cascade_stmt}"
        self.execute_ddl(ddl)

    def table_exists(self, table_name: str, schema: Optional[str] = None) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: The name of the table to check
            schema: The schema containing the table

        Returns:
            True if the table exists, False otherwise
        """
        schema_clause = f"AND table_schema = '{schema}'" if schema else ""

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_name = '{table_name}'
                        {schema_clause}
                    )
                """
                )
                result = cursor.fetchone()
                return result[0] if result else False

    def function_exists(self, function_name: str, schema: Optional[str] = None) -> bool:
        """
        Check if a function exists in the database.

        Args:
            function_name: The name of the function to check
            schema: The schema containing the function

        Returns:
            True if the function exists, False otherwise
        """
        schema_clause = f"AND n.nspname = '{schema}'" if schema else ""

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_proc p
                        JOIN pg_namespace n ON p.pronamespace = n.oid
                        WHERE p.proname = '{function_name}'
                        {schema_clause}
                    )
                """
                )
                result = cursor.fetchone()
                return result[0] if result else False

    def create_tables(self, models: List[Any]) -> None:
        """
        Create tables for the given models using SQLAlchemy's metadata.

        Args:
            models: List of SQLAlchemy model classes
        """
        from sqlalchemy import MetaData

        # Collect metadata from models
        metadata = MetaData()
        for model in models:
            if hasattr(model, "__table__"):
                metadata.tables[model.__table__.name] = model.__table__

        # Generate DDL and execute
        ddl = self.generate_tables_ddl(metadata)
        self.execute_script(ddl)

    def generate_tables_ddl(self, metadata: Any) -> str:
        """
        Generate DDL for creating tables from SQLAlchemy metadata.

        Args:
            metadata: SQLAlchemy MetaData object

        Returns:
            DDL script for creating tables
        """
        from sqlalchemy.schema import CreateTable

        ddl_statements = []
        for table in metadata.sorted_tables:
            create_table = CreateTable(table)
            ddl_statements.append(str(create_table).rstrip() + ";")

        return "\n\n".join(ddl_statements)

    def initialize_database(self, config: ConnectionConfig) -> None:
        """
        Initialize a new database.

        This method creates a new database and initializes it with
        the required schemas and extensions.

        Args:
            config: Database connection configuration
        """
        # Create a connection to the postgres database
        admin_config = ConnectionConfig(
            db_role=config.db_role,
            db_user_pw=config.db_user_pw,
            db_host=config.db_host,
            db_port=config.db_port,
            db_name="postgres",  # Connect to postgres database
            db_driver=config.db_driver,
        )

        # Create connection to postgres database
        admin_conn = psycopg.connect(
            host=admin_config.db_host,
            port=admin_config.db_port,
            user=admin_config.db_role,
            password=admin_config.db_user_pw,
            dbname=admin_config.db_name,
        )

        try:
            # Create the new database
            with admin_conn.cursor() as cursor:
                # Close existing connections
                cursor.execute(
                    f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{config.db_name}'
                    AND pid <> pg_backend_pid()
                """
                )

                # Drop the database if it exists
                cursor.execute(f"DROP DATABASE IF EXISTS {config.db_name}")

                # Create the database
                cursor.execute(f"CREATE DATABASE {config.db_name}")

            admin_conn.commit()
            self.logger.info(f"Created database {config.db_name}")

        finally:
            # Close the admin connection
            admin_conn.close()

        # Now connect to the new database and initialize schemas
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Create the main schema
                if config.db_schema:
                    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {config.db_schema}")

                # Create essential extensions
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

                # Additional initialization as needed

            conn.commit()
            self.logger.info(f"Initialized database {config.db_name}")

    def drop_database(self, config: ConnectionConfig) -> None:
        """
        Drop a database.

        This method drops an existing database.

        Args:
            config: Database connection configuration
        """
        # Create a connection to the postgres database
        admin_config = ConnectionConfig(
            db_role=config.db_role,
            db_user_pw=config.db_user_pw,
            db_host=config.db_host,
            db_port=config.db_port,
            db_name="postgres",  # Connect to postgres database
            db_driver=config.db_driver,
        )

        # Create connection to postgres database
        admin_conn = psycopg.connect(
            host=admin_config.db_host,
            port=admin_config.db_port,
            user=admin_config.db_role,
            password=admin_config.db_user_pw,
            dbname=admin_config.db_name,
        )

        try:
            # Drop the database
            with admin_conn.cursor() as cursor:
                # Close existing connections
                cursor.execute(
                    f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{config.db_name}'
                    AND pid <> pg_backend_pid()
                """
                )

                # Drop the database
                cursor.execute(f"DROP DATABASE IF EXISTS {config.db_name}")

            admin_conn.commit()
            self.logger.info(f"Dropped database {config.db_name}")

        finally:
            # Close the admin connection
            admin_conn.close()
