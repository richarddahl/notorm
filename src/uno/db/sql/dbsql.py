# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import logging
from pydantic import computed_field
from sqlalchemy.exc import SQLAlchemyError

from uno.db.sql.classes import SQLEmitter
from uno.errors import UnoError


class CreateRolesAndDatabase(SQLEmitter):
    @computed_field
    def create_roles(self) -> str:
        """
        Create roles in the database.

        :return: SQL statement for creating roles
        """
        try:
            db_user_pw = self.config.DB_USER_PW
            base_role = f"{self.config.DB_NAME}_base_role"
            login_role = f"{self.config.DB_NAME}_login"
            reader_role = f"{self.config.DB_NAME}_reader"
            writer_role = f"{self.config.DB_NAME}_writer"
            admin_role = f"{self.config.DB_NAME}_admin"

            return f"""
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
        except SQLAlchemyError as e:
            logging.error(f"Error creating roles: {e}")
            raise UnoError(f"Failed to create roles: {e}", "SQL_ROLE_CREATION_ERROR")

    @computed_field
    def create_database(self) -> str:
        """
        Create the database.

        :return: SQL statement for creating the database
        """
        try:
            db_name = self.config.DB_NAME
            admin_role = f"{self.config.DB_NAME}_admin"
            return f"""
            -- Create the database
            CREATE DATABASE {db_name} WITH OWNER = {admin_role};
            """
        except SQLAlchemyError as e:
            logging.error(f"Error creating database: {e}")
            raise UnoError(
                f"Failed to create database: {e}", "SQL_DATABASE_CREATION_ERROR"
            )


class CreateSchemasAndExtensions(SQLEmitter):
    @computed_field
    def create_schemas(self) -> str:
        """
        Create schemas in the database.

        :return: SQL statement for creating schemas
        """
        try:
            db_schema = self.config.DB_SCHEMA
            admin_role = f"{self.config.DB_NAME}_admin"
            return f"""
            -- Create the schema
            CREATE SCHEMA IF NOT EXISTS {db_schema} AUTHORIZATION {admin_role};
            """
        except SQLAlchemyError as e:
            logging.error(f"Error creating schemas: {e}")
            raise UnoError(
                f"Failed to create schemas: {e}", "SQL_SCHEMA_CREATION_ERROR"
            )

    @computed_field
    def create_extensions(self) -> str:
        """
        Create extensions in the database.

        :return: SQL statement for creating extensions
        """
        try:
            db_schema = self.config.DB_SCHEMA
            reader_role = f"{self.config.DB_NAME}_reader"
            writer_role = f"{self.config.DB_NAME}_writer"
            admin_role = f"{self.config.DB_NAME}_admin"
            return f"""
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
        except SQLAlchemyError as e:
            logging.error(f"Error creating extensions: {e}")
            raise UnoError(
                f"Failed to create extensions: {e}", "SQL_EXTENSION_CREATION_ERROR"
            )


class RevokeAndGrantPrivilegesAndSetSearchPaths(SQLEmitter):
    @computed_field
    def revoke_privileges(self) -> str:
        """
        Revoke privileges on schemas and tables.

        :return: SQL statement for revoking privileges
        """
        try:
            db_schema = self.config.DB_SCHEMA
            db_name = self.config.DB_NAME
            base_role = f"{self.config.DB_NAME}_base_role"
            login_role = f"{self.config.DB_NAME}_login"
            reader_role = f"{self.config.DB_NAME}_reader"
            writer_role = f"{self.config.DB_NAME}_writer"
            admin_role = f"{self.config.DB_NAME}_admin"
            return f"""
            -- Explicitly revoke all privileges on schemas and tables
            REVOKE ALL ON SCHEMA audit, graph, ag_catalog, {db_schema}
            FROM public, {base_role}, {login_role}, {reader_role}, {writer_role}, {admin_role};

            REVOKE ALL ON ALL TABLES IN SCHEMA audit, graph, ag_catalog, {db_schema}
            FROM public, {base_role}, {login_role}, {reader_role}, {writer_role}, {admin_role};

            REVOKE CONNECT ON DATABASE {db_name} FROM public, {base_role}, {reader_role}, {writer_role}, {admin_role};
            """
        except SQLAlchemyError as e:
            logging.error(f"Error revoking privileges: {e}")
            raise UnoError(
                f"Failed to revoke privileges: {e}", "SQL_PRIVILEGE_REVOKE_ERROR"
            )

    @computed_field
    def set_search_paths(self) -> str:
        """
        Set search paths for roles.

        :return: SQL statement for setting search paths
        """
        try:
            db_schema = self.config.DB_SCHEMA
            base_role = f"{self.config.DB_NAME}_base_role"
            login_role = f"{self.config.DB_NAME}_login"
            reader_role = f"{self.config.DB_NAME}_reader"
            writer_role = f"{self.config.DB_NAME}_writer"
            admin_role = f"{self.config.DB_NAME}_admin"
            return f"""
            ALTER ROLE {base_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
            ALTER ROLE {login_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
            ALTER ROLE {reader_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
            ALTER ROLE {writer_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
            ALTER ROLE {admin_role} SET search_path TO {db_schema}, audit, graph, ag_catalog;
            """
        except SQLAlchemyError as e:
            logging.error(f"Error setting search paths: {e}")
            raise UnoError(f"Failed to set search paths: {e}", "SQL_SEARCH_PATH_ERROR")

    @computed_field
    def grant_schema_privileges(self) -> str:
        """
        Grant schema privileges to roles.

        :return: SQL statement for granting schema privileges
        """
        try:
            db_schema = self.config.DB_SCHEMA
            db_name = self.config.DB_NAME
            login_role = f"{self.config.DB_NAME}_login"
            reader_role = f"{self.config.DB_NAME}_reader"
            writer_role = f"{self.config.DB_NAME}_writer"
            admin_role = f"{self.config.DB_NAME}_admin"
            return f"""
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
        except SQLAlchemyError as e:
            logging.error(f"Error granting schema privileges: {e}")
            raise UnoError(
                f"Failed to grant schema privileges: {e}", "SQL_SCHEMA_PRIVILEGE_ERROR"
            )


class CreatePGULID(SQLEmitter):
    @computed_field
    def create_pgulid(self) -> str:
        """
        Create PGULID function from SQL file.

        :return: SQL statement for creating PGULID
        """
        try:
            db_schema = self.config.DB_SCHEMA
            # Assume UNO_ROOT is provided via self.config if needed.
            uno_root = self.config.UNO_ROOT
            with open(f"{uno_root}/uno/db/sql/pgulid.sql", "r") as file:
                sql_statement = file.read()
            return sql_statement.format(schema_name=db_schema)
        except FileNotFoundError as e:
            logging.error(f"Error reading PGULID SQL file: {e}")
            raise UnoError(
                f"Failed to read PGULID SQL file: {e}", "SQL_FILE_READ_ERROR"
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating PGULID: {e}")
            raise UnoError(f"Failed to create PGULID: {e}", "SQL_PGULID_CREATION_ERROR")


class CreateTokenSecret(SQLEmitter):
    @computed_field
    def create_token_secret_table(self) -> str:
        """
        Create token secret table and trigger.

        :return: SQL statement for creating token secret table and trigger
        """
        try:
            db_name = self.config.DB_NAME
            admin_role = f"{self.config.DB_NAME}_admin"
            return f"""
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
        except SQLAlchemyError as e:
            logging.error(f"Error creating token secret table: {e}")
            raise UnoError(
                f"Failed to create token secret table: {e}",
                "SQL_TOKEN_SECRET_CREATION_ERROR",
            )


class GrantPrivileges(SQLEmitter):
    @computed_field
    def grant_schema_privileges(self) -> str:
        """
        Grant table privileges to roles.

        :return: SQL statement for granting table privileges
        """
        try:
            db_schema = self.config.DB_SCHEMA
            admin_role = f"{self.config.DB_NAME}_admin"
            writer_role = f"{self.config.DB_NAME}_writer"
            reader_role = f"{self.config.DB_NAME}_reader"
            return f"""
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
        except SQLAlchemyError as e:
            logging.error(f"Error granting table privileges: {e}")
            raise UnoError(
                f"Failed to grant table privileges: {e}", "SQL_TABLE_PRIVILEGE_ERROR"
            )


class SetRole(SQLEmitter):
    @computed_field
    def create_set_role(self) -> str:
        """
        Create or replace the set_role function.

        :return: SQL statement to create set_role function.
        """
        try:
            db_name = self.config.DB_NAME
            return f"""
            SET ROLE {db_name}_admin;
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
        except SQLAlchemyError as e:
            logging.error(f"Error creating set_role function: {e}")
            raise UnoError(
                f"Failed to create set_role function: {e}",
                "SQL_SET_ROLE_CREATION_ERROR",
            )

    @computed_field
    def set_role_permissions(self) -> str:
        """
        Manage permissions for the set_role function.

        :return: SQL statement for setting role permissions.
        """
        try:
            writer_role = f"{self.config.DB_NAME}_writer"
            reader_role = f"{self.config.DB_NAME}_reader"
            login_role = f"{self.config.DB_NAME}_login"
            return f"""
            REVOKE EXECUTE ON FUNCTION set_role(TEXT) FROM public;
            GRANT EXECUTE ON FUNCTION set_role(TEXT)
            TO {login_role}, {reader_role}, {writer_role};
            """
        except SQLAlchemyError as e:
            logging.error(f"Error setting role permissions: {e}")
            raise UnoError(
                f"Failed to set role permissions: {e}", "SQL_SET_ROLE_PERMISSION_ERROR"
            )


class DropDatabaseAndRoles(SQLEmitter):
    @computed_field
    def drop_database(self) -> str:
        return f"""
            -- Drop the database if it exists
            DROP DATABASE IF EXISTS {self.config.DB_NAME} WITH (FORCE);
        """

    @computed_field
    def drop_roles(self) -> str:
        admin_role = f"{self.config.DB_NAME}_admin"
        writer_role = f"{self.config.DB_NAME}_writer"
        reader_role = f"{self.config.DB_NAME}_reader"
        login_role = f"{self.config.DB_NAME}_login"
        base_role = f"{self.config.DB_NAME}_base_role"
        return f"""
            -- Drop the roles if they exist
            DROP ROLE IF EXISTS {admin_role};
            DROP ROLE IF EXISTS {writer_role};
            DROP ROLE IF EXISTS {reader_role};
            DROP ROLE IF EXISTS {login_role};
            DROP ROLE IF EXISTS {base_role};
        """
