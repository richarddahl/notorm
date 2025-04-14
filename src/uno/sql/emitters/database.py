# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL emitters for database-level operations."""

import logging
from typing import List, Optional
import os

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.errors import (
    SQLErrorCode,
    SQLEmitterError,
    SQLExecutionError,
    SQLConfigError
)


class CreateRolesAndDatabase(SQLEmitter):
    """Emitter for creating database roles and the database itself."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for creating roles and database.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate create roles SQL
        db_user_pw = self.config.DB_USER_PW
        db_name = self.config.DB_NAME
        base_role = f"{db_name}_base_role"
        login_role = f"{db_name}_login"
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"
        admin_role = f"{db_name}_admin"

        create_roles_sql = f"""
        DO $$
        BEGIN
            -- Create the base role with permissions that all other users will inherit
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{base_role}') THEN
                CREATE ROLE {base_role} NOINHERIT;
            END IF;

            -- Create the reader role
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{reader_role}') THEN
                CREATE ROLE {reader_role} INHERIT IN ROLE {base_role};
            END IF;

            -- Create the writer role
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{writer_role}') THEN
                CREATE ROLE {writer_role} INHERIT IN ROLE {base_role};
            END IF;

            -- Create the admin role
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{admin_role}') THEN
                CREATE ROLE {admin_role} INHERIT IN ROLE {base_role};
            END IF;

            -- Create the authentication role
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{login_role}') THEN
                CREATE ROLE {login_role} NOINHERIT LOGIN PASSWORD '{db_user_pw}' IN ROLE {base_role};
            END IF;

            -- Grant the reader, writer, and admin roles to the authentication role
            GRANT {reader_role}, {writer_role}, {admin_role} TO {login_role};
        END $$;
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_roles", type=SQLStatementType.ROLE, sql=create_roles_sql
            )
        )

        # Generate create database SQL
        create_database_sql = f"""
        -- Create the database
        CREATE DATABASE {db_name} WITH OWNER = {admin_role};
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_database",
                type=SQLStatementType.DATABASE,
                sql=create_database_sql,
            )
        )

        return statements


class CreateSchemasAndExtensions(SQLEmitter):
    """Emitter for creating schemas and extensions in the database."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for creating schemas and extensions.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate create schemas SQL
        db_schema = self.config.DB_SCHEMA
        admin_role = f"{self.config.DB_NAME}_admin"

        create_schemas_sql = f"""
        -- Create the schema
        CREATE SCHEMA IF NOT EXISTS {db_schema} AUTHORIZATION {admin_role};
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_schemas",
                type=SQLStatementType.SCHEMA,
                sql=create_schemas_sql,
            )
        )

        # Generate create extensions SQL
        db_schema = self.config.DB_SCHEMA
        reader_role = f"{self.config.DB_NAME}_reader"
        writer_role = f"{self.config.DB_NAME}_writer"
        admin_role = f"{self.config.DB_NAME}_admin"

        create_extensions_sql = f"""
        -- Create the extensions
        SET search_path TO {db_schema};

        CREATE EXTENSION IF NOT EXISTS btree_gist;

        CREATE EXTENSION IF NOT EXISTS supa_audit CASCADE;

        CREATE EXTENSION IF NOT EXISTS hstore;

        SET pgmeta.log = 'all';
        SET pgmeta.log_relation = on;
        SET pgmeta.log_line_prefix = '%m %u %d [%p]: ';

        CREATE EXTENSION IF NOT EXISTS pgcrypto;

        CREATE EXTENSION IF NOT EXISTS pgjwt;

        CREATE EXTENSION IF NOT EXISTS age;

        -- Add pgvector extension for vector similarity search
        CREATE EXTENSION IF NOT EXISTS vector;

        -- Configure schemas and permissions
        ALTER SCHEMA ag_catalog OWNER TO {admin_role};
        GRANT USAGE ON SCHEMA ag_catalog TO {admin_role}, {reader_role}, {writer_role};
        SELECT * FROM ag_catalog.create_graph('graph');
        ALTER TABLE ag_catalog.ag_graph OWNER TO {admin_role};
        ALTER TABLE ag_catalog.ag_label OWNER TO {admin_role};
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ag_catalog TO {admin_role};
        ALTER TABLE graph._ag_label_edge OWNER TO {admin_role};
        ALTER TABLE graph._ag_label_vertex OWNER TO {admin_role};
        ALTER SEQUENCE graph._ag_label_edge_id_seq OWNER TO {admin_role};
        ALTER SEQUENCE graph._ag_label_vertex_id_seq OWNER TO {admin_role};
        ALTER SEQUENCE graph._label_id_seq OWNER TO {admin_role};
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_extensions",
                type=SQLStatementType.EXTENSION,
                sql=create_extensions_sql,
            )
        )

        return statements


class RevokeAndGrantPrivilegesAndSetSearchPaths(SQLEmitter):
    """Emitter for revoking and granting privileges, and setting search paths."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for privileges and search paths.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate revoke privileges SQL
        db_schema = self.config.DB_SCHEMA
        db_name = self.config.DB_NAME
        base_role = f"{db_name}_base_role"
        login_role = f"{db_name}_login"
        reader_role = f"{db_name}_reader"
        writer_role = f"{db_name}_writer"
        admin_role = f"{db_name}_admin"

        revoke_privileges_sql = f"""
        -- Explicitly revoke all privileges on schemas and tables
        REVOKE ALL ON SCHEMA audit, graph, ag_catalog, {db_schema}
        FROM public, {base_role}, {login_role}, {reader_role}, {writer_role}, {admin_role};

        REVOKE ALL ON ALL TABLES IN SCHEMA audit, graph, ag_catalog, {db_schema}
        FROM public, {base_role}, {login_role}, {reader_role}, {writer_role}, {admin_role};

        REVOKE CONNECT ON DATABASE {db_name} FROM public, {base_role}, {reader_role}, {writer_role}, {admin_role};
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="revoke_privileges",
                type=SQLStatementType.GRANT,
                sql=revoke_privileges_sql,
            )
        )

        # Generate set search paths SQL
        set_search_paths_sql = f"""
        ALTER ROLE {base_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
        ALTER ROLE {login_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
        ALTER ROLE {reader_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
        ALTER ROLE {writer_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
        ALTER ROLE {admin_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="set_search_paths",
                type=SQLStatementType.GRANT,
                sql=set_search_paths_sql,
            )
        )

        # Generate grant schema privileges SQL
        grant_schema_privileges_sql = f"""
        ALTER SCHEMA audit OWNER TO {admin_role};
        ALTER SCHEMA graph OWNER TO {admin_role};
        ALTER SCHEMA ag_catalog OWNER TO {admin_role};
        ALTER SCHEMA {db_schema} OWNER TO {admin_role};
        ALTER TABLE audit.record_version OWNER TO {admin_role};

        GRANT CONNECT ON DATABASE {db_name} TO {login_role};

        GRANT USAGE ON SCHEMA audit, graph, ag_catalog, {db_schema}
        TO {login_role}, {admin_role}, {reader_role}, {writer_role};

        GRANT CREATE ON SCHEMA audit, graph, {db_schema} TO {admin_role};

        GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit, graph, ag_catalog, {db_schema}
        TO {login_role}, {admin_role}, {reader_role}, {writer_role};

        GRANT {admin_role} TO {login_role} WITH INHERIT FALSE, SET TRUE;
        GRANT {writer_role} TO {login_role} WITH INHERIT FALSE, SET TRUE;
        GRANT {reader_role} TO {login_role} WITH INHERIT FALSE, SET TRUE;
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="grant_schema_privileges",
                type=SQLStatementType.GRANT,
                sql=grant_schema_privileges_sql,
            )
        )

        return statements


class CreatePGULID(SQLEmitter):
    """Emitter for creating PGULID function from SQL file."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for creating PGULID.

        Returns:
            List of SQL statements with metadata

        Raises:
            UnoError: If the PGULID SQL file cannot be read
        """
        statements = []

        try:
            # Get the PGULID SQL from file
            db_schema = self.config.DB_SCHEMA
            uno_root = self.config.UNO_ROOT

            with open(f"{uno_root}/uno/sql/pgulid.sql", "r") as file:
                pgulid_sql = file.read()

            # Format the SQL with the schema name
            pgulid_sql = pgulid_sql.format(schema_name=db_schema)

            # Add the statement to the list
            statements.append(
                SQLStatement(
                    name="create_pgulid", type=SQLStatementType.FUNCTION, sql=pgulid_sql
                )
            )

        except FileNotFoundError as e:
            logging.error(f"Error reading PGULID SQL file: {e}")
            raise UnoError(
                f"Failed to read PGULID SQL file: {e}", "SQL_FILE_READ_ERROR"
            )

        return statements


class CreateTokenSecret(SQLEmitter):
    """Emitter for creating token secret table and trigger."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for creating token secret.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate token secret SQL
        db_name = self.config.DB_NAME
        admin_role = f"{db_name}_admin"

        create_token_secret_sql = f"""
        /* Creating the token_secret table in database: {db_name} */
        SET ROLE {admin_role};
        DROP TABLE IF EXISTS audit.token_secret CASCADE;
        CREATE TABLE audit.token_secret (
            token_secret TEXT PRIMARY KEY
        );

        CREATE OR REPLACE FUNCTION audit.set_token_secret()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            DELETE FROM audit.token_secret;
            RETURN NEW;
        END;
        $$;

        CREATE TRIGGER set_token_secret_trigger
        BEFORE INSERT ON audit.token_secret
        FOR EACH ROW
        EXECUTE FUNCTION audit.set_token_secret();
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_token_secret_table",
                type=SQLStatementType.TABLE,
                sql=create_token_secret_sql,
            )
        )

        return statements


class GrantPrivileges(SQLEmitter):
    """Emitter for granting privileges on tables."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for granting table privileges.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate grant privileges SQL
        db_schema = self.config.DB_SCHEMA
        admin_role = f"{self.config.DB_NAME}_admin"
        writer_role = f"{self.config.DB_NAME}_writer"
        reader_role = f"{self.config.DB_NAME}_reader"

        grant_privileges_sql = f"""
        SET ROLE {admin_role};
        GRANT SELECT ON ALL TABLES IN SCHEMA audit, graph, ag_catalog, {db_schema}
        TO {reader_role}, {writer_role};

        GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON ALL TABLES IN SCHEMA audit, graph, {db_schema} 
        TO {writer_role}, {admin_role};

        GRANT ALL ON ALL TABLES IN SCHEMA audit, graph, ag_catalog TO {admin_role};

        SET ROLE {admin_role};
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit, graph, ag_catalog, {db_schema}
        TO {reader_role}, {writer_role};
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="grant_schema_privileges",
                type=SQLStatementType.GRANT,
                sql=grant_privileges_sql,
            )
        )

        return statements


class SetRole(SQLEmitter):
    """Emitter for creating and configuring the set_role function."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for the set_role function.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate set_role function SQL
        db_name = self.config.DB_NAME
        admin_role = f"{db_name}_admin"

        create_set_role_sql = f"""
        SET ROLE {admin_role};
        CREATE OR REPLACE FUNCTION set_role(role_name TEXT)
        RETURNS VOID
        LANGUAGE plpgsql
        AS $$
        DECLARE
            db_name TEXT := current_database();
            complete_role_name TEXT:= CONCAT(db_name, '_', role_name);
            set_role_command TEXT:= CONCAT('SET ROLE ', complete_role_name);
        BEGIN
            EXECUTE set_role_command;
        END;
        $$;
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_set_role",
                type=SQLStatementType.FUNCTION,
                sql=create_set_role_sql,
            )
        )

        # Generate set_role permissions SQL
        writer_role = f"{db_name}_writer"
        reader_role = f"{db_name}_reader"
        login_role = f"{db_name}_login"

        set_role_permissions_sql = f"""
        REVOKE EXECUTE ON FUNCTION set_role(TEXT) FROM public;
        GRANT EXECUTE ON FUNCTION set_role(TEXT)
        TO {login_role}, {reader_role}, {writer_role};
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="set_role_permissions",
                type=SQLStatementType.GRANT,
                sql=set_role_permissions_sql,
            )
        )

        return statements


class DropDatabaseAndRoles(SQLEmitter):
    """Emitter for dropping database and roles."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for dropping database and roles.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate drop database SQL - separate each statement to avoid transaction issues
        db_name = self.config.DB_NAME

        # First statement: Terminate existing connections
        terminate_connections_sql = f"""
        -- Terminate all existing connections to the database
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '{db_name}'
        AND pid <> pg_backend_pid();
        """

        # Add terminate connections statement to the list
        statements.append(
            SQLStatement(
                name="terminate_connections",
                type=SQLStatementType.FUNCTION,
                sql=terminate_connections_sql,
            )
        )

        # Second statement: Drop the database
        drop_database_sql = f"""
        -- Drop the database if it exists (without force)
        DROP DATABASE IF EXISTS {db_name};
        """

        # Add drop database statement to the list
        statements.append(
            SQLStatement(
                name="drop_database",
                type=SQLStatementType.DATABASE,
                sql=drop_database_sql,
            )
        )

        # Generate drop roles SQL
        admin_role = f"{db_name}_admin"
        writer_role = f"{db_name}_writer"
        reader_role = f"{db_name}_reader"
        login_role = f"{db_name}_login"
        base_role = f"{db_name}_base_role"

        drop_roles_sql = f"""
        -- Drop the roles if they exist
        DROP ROLE IF EXISTS {admin_role};
        DROP ROLE IF EXISTS {writer_role};
        DROP ROLE IF EXISTS {reader_role};
        DROP ROLE IF EXISTS {login_role};
        DROP ROLE IF EXISTS {base_role};
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="drop_roles", type=SQLStatementType.ROLE, sql=drop_roles_sql
            )
        )

        return statements
