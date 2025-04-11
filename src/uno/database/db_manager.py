"""
Database manager for PostgreSQL operations.

This module provides functionality for managing PostgreSQL database objects,
including databases, schemas, functions, types, triggers, and security policies.
It leaves table creation to Alembic migrations.
"""

import logging
from typing import Optional, Any, Callable, ContextManager, Type, List, Dict, Union

import psycopg
from sqlalchemy import text

from uno.database.config import ConnectionConfig
from uno.sql.emitter import SQLEmitter


class DBManager:
    """
    Manager for PostgreSQL database operations.

    This class provides methods for executing DDL statements and
    managing database objects like schemas, functions, and triggers.
    It integrates with SQLEmitters for SQL generation.
    """

    def __init__(
        self,
        connection_provider: Callable[[], ContextManager[psycopg.Connection]],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the database manager.

        Args:
            connection_provider: Function that provides a database connection
            logger: Optional logger instance
        """
        self.get_connection = connection_provider
        self.logger = logger or logging.getLogger(__name__)

    def execute_ddl(self, ddl: str) -> None:
        """
        Execute a DDL statement.

        This method validates and executes a DDL statement. It performs
        basic security checks to ensure the SQL is safe to execute.

        Args:
            ddl: The DDL statement to execute

        Raises:
            ValueError: If the DDL contains disallowed operations or is malformed
        """
        # Normalize for validation
        normalized_ddl = ddl.strip().upper()
        
        # Check for disallowed operations that could be destructive
        disallowed_patterns = [
            # Prevent dropping production or critical databases
            r"DROP\s+DATABASE\s+(PRODUCTION|PROD|LIVE|UNO_PROD|POSTGRES)",
            # Allow dropping test/dev databases in execute_ddl, but not the current database
            # (dropping the current DB is handled by initialize_database)
            
            # Prevent dropping critical extensions
            r"DROP\s+EXTENSION\s+PG_CRYPTO", 
            r"DROP\s+EXTENSION\s+UUID-OSSP",
            r"DROP\s+EXTENSION\s+PG_TRGM",
            
            # Prevent dangerous statements
            r"TRUNCATE\s+ALL\s+TABLES",
            r"GRANT\s+ALL.*TO\s+PUBLIC",
            r"CREATE\s+USER.*SUPERUSER",
        ]
        
        import re
        for pattern in disallowed_patterns:
            if re.search(pattern, normalized_ddl):
                error_msg = f"Disallowed operation in DDL statement: {pattern}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Validate basic SQL structure
        if not (
            normalized_ddl.startswith("CREATE") or
            normalized_ddl.startswith("ALTER") or
            normalized_ddl.startswith("DROP") or
            normalized_ddl.startswith("GRANT") or
            normalized_ddl.startswith("REVOKE") or
            normalized_ddl.startswith("COMMENT") or
            "FUNCTION" in normalized_ddl or
            "TRIGGER" in normalized_ddl or
            "INDEX" in normalized_ddl or
            "POLICY" in normalized_ddl
        ):
            self.logger.warning(f"Potentially non-DDL statement: {ddl[:100]}...")
        
        # Execute the statement
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    self.logger.debug(f"Executing DDL: {ddl[:100]}...")
                    cursor.execute(ddl)
                conn.commit()
                self.logger.info("DDL execution successful")
        except Exception as e:
            self.logger.error(f"DDL execution failed: {str(e)}")
            raise

    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script containing multiple statements.

        This method validates and executes a SQL script. It performs
        basic security checks to ensure the SQL is safe to execute.

        Args:
            script: The SQL script to execute
            
        Raises:
            ValueError: If the script contains disallowed operations
        """
        # Normalize for validation (preserving original for execution)
        normalized_script = script.strip().upper()
        
        # Check for disallowed operations that could be destructive
        disallowed_patterns = [
            # Prevent dropping production or critical databases
            r"DROP\s+DATABASE\s+(PRODUCTION|PROD|LIVE|UNO_PROD|POSTGRES)",
            # Allow dropping test/dev databases in execute_ddl, but not the current database
            # (dropping the current DB is handled by initialize_database)
            
            # Prevent dropping critical extensions
            r"DROP\s+EXTENSION\s+PG_CRYPTO", 
            r"DROP\s+EXTENSION\s+UUID-OSSP",
            r"DROP\s+EXTENSION\s+PG_TRGM",
            
            # Prevent dangerous statements
            r"TRUNCATE\s+ALL\s+TABLES",
            r"GRANT\s+ALL.*TO\s+PUBLIC",
            r"CREATE\s+USER.*SUPERUSER",
        ]
        
        import re
        for pattern in disallowed_patterns:
            if re.search(pattern, normalized_script):
                error_msg = f"Disallowed operation in SQL script: {pattern}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Execute the script
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    self.logger.debug(f"Executing SQL script ({len(script)} characters)")
                    cursor.execute(script)
                conn.commit()
                self.logger.info("SQL script execution successful")
        except Exception as e:
            self.logger.error(f"SQL script execution failed: {str(e)}")
            raise

    def execute_from_emitter(self, emitter: SQLEmitter) -> None:
        """
        Execute SQL generated by an SQLEmitter.

        This method is safer than direct SQL execution because it uses
        well-tested SQL emitters that generate standardized SQL.

        Args:
            emitter: The SQL emitter to generate and execute SQL from
            
        Raises:
            ValueError: If generated SQL contains disallowed operations
        """
        self.logger.info(f"Executing SQL from emitter: {emitter.__class__.__name__}")
        statements = emitter.generate_sql()
        self.logger.debug(f"Generated {len(statements)} SQL statements")
        
        for statement in statements:
            # Log statement metadata
            self.logger.debug(f"Executing {statement.type.name} statement: {statement.name}")
            self.execute_ddl(statement.sql)

    def execute_from_emitters(self, emitters: List[SQLEmitter]) -> None:
        """
        Execute SQL generated by multiple SQLEmitters.

        This method combines SQL from multiple emitters and executes them
        as a single script for better performance and atomicity.

        Args:
            emitters: List of SQL emitters to generate and execute SQL from
            
        Raises:
            ValueError: If generated SQL contains disallowed operations
        """
        self.logger.info(f"Executing SQL from {len(emitters)} emitters")
        
        # Collect all SQL statements
        all_sql_statements = []
        for emitter in emitters:
            self.logger.debug(f"Generating SQL from emitter: {emitter.__class__.__name__}")
            statements = emitter.generate_sql()
            for statement in statements:
                self.logger.debug(f"Generated {statement.type.name} statement: {statement.name}")
                all_sql_statements.append(statement.sql)

        # Execute as a batch if we have statements
        if all_sql_statements:
            combined_script = "\n\n".join(all_sql_statements)
            self.logger.debug(f"Executing combined script with {len(all_sql_statements)} statements")
            self.execute_script(combined_script)

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

    def create_extension(
        self, extension_name: str, schema: Optional[str] = None
    ) -> None:
        """
        Create a PostgreSQL extension.

        Args:
            extension_name: The name of the extension to create
            schema: Optional schema to create the extension in
        """
        schema_clause = f"SCHEMA {schema}" if schema else ""
        ddl = f"CREATE EXTENSION IF NOT EXISTS {extension_name} {schema_clause}"
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

    def type_exists(self, type_name: str, schema: Optional[str] = None) -> bool:
        """
        Check if a type exists in the database.

        Args:
            type_name: The name of the type to check
            schema: The schema containing the type

        Returns:
            True if the type exists, False otherwise
        """
        schema_clause = f"AND n.nspname = '{schema}'" if schema else ""

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_type t
                        JOIN pg_namespace n ON t.typnamespace = n.oid
                        WHERE t.typname = '{type_name}'
                        {schema_clause}
                    )
                """
                )
                result = cursor.fetchone()
                return result[0] if result else False

    def trigger_exists(
        self, trigger_name: str, table_name: str, schema: Optional[str] = None
    ) -> bool:
        """
        Check if a trigger exists in the database.

        Args:
            trigger_name: The name of the trigger to check
            table_name: The table the trigger is on
            schema: The schema containing the trigger

        Returns:
            True if the trigger exists, False otherwise
        """
        schema_clause = f"AND n.nspname = '{schema}'" if schema else ""

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_trigger t
                        JOIN pg_class c ON t.tgrelid = c.oid
                        JOIN pg_namespace n ON c.relnamespace = n.oid
                        WHERE t.tgname = '{trigger_name}'
                        AND c.relname = '{table_name}'
                        {schema_clause}
                    )
                """
                )
                result = cursor.fetchone()
                return result[0] if result else False

    def policy_exists(
        self, policy_name: str, table_name: str, schema: Optional[str] = None
    ) -> bool:
        """
        Check if a row-level security policy exists in the database.

        Args:
            policy_name: The name of the policy to check
            table_name: The table the policy is on
            schema: The schema containing the policy

        Returns:
            True if the policy exists, False otherwise
        """
        schema_clause = f"AND n.nspname = '{schema}'" if schema else ""

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT EXISTS (
                        SELECT 1
                        FROM pg_policy p
                        JOIN pg_class c ON p.polrelid = c.oid
                        JOIN pg_namespace n ON c.relnamespace = n.oid
                        WHERE p.polname = '{policy_name}'
                        AND c.relname = '{table_name}'
                        {schema_clause}
                    )
                """
                )
                result = cursor.fetchone()
                return result[0] if result else False

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

    def create_user(
        self, username: str, password: str, is_superuser: bool = False
    ) -> None:
        """
        Create a database user.

        Args:
            username: The name of the user to create
            password: The password for the user
            is_superuser: Whether the user should be a superuser
        """
        superuser_clause = "SUPERUSER" if is_superuser else "NOSUPERUSER"
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT FROM pg_catalog.pg_roles WHERE rolname = '{username}'
                        ) THEN
                            CREATE USER {username} WITH {superuser_clause} PASSWORD '{password}';
                        END IF;
                    END
                    $$;
                """
                )
            conn.commit()
            self.logger.info(f"Created user {username}")

    def create_role(
        self, rolename: str, granted_roles: Optional[List[str]] = None
    ) -> None:
        """
        Create a database role.

        Args:
            rolename: The name of the role to create
            granted_roles: Optional list of roles to grant to this role
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT FROM pg_catalog.pg_roles WHERE rolname = '{rolename}'
                        ) THEN
                            CREATE ROLE {rolename};
                        END IF;
                    END
                    $$;
                """
                )

                if granted_roles:
                    for role in granted_roles:
                        cursor.execute(f"GRANT {role} TO {rolename}")

            conn.commit()
            self.logger.info(f"Created role {rolename}")

    def grant_privileges(
        self,
        privileges: List[str],
        on_object: str,
        to_role: str,
        object_type: str = "TABLE",
        schema: Optional[str] = None,
    ) -> None:
        """
        Grant privileges to a role.

        Args:
            privileges: List of privileges to grant (e.g., ["SELECT", "INSERT"])
            on_object: The object to grant privileges on
            to_role: The role to grant privileges to
            object_type: The type of object (TABLE, SEQUENCE, etc.)
            schema: Optional schema containing the object
        """
        privileges_str = ", ".join(privileges)
        object_name = f"{schema}.{on_object}" if schema else on_object

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"GRANT {privileges_str} ON {object_type} {object_name} TO {to_role}"
                )
            conn.commit()
            self.logger.info(f"Granted {privileges_str} on {object_name} to {to_role}")
