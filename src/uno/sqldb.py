# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from psycopg import sql
from pydantic import computed_field

from uno.config import settings


class CreateRolesAndDatabase(SQLEmitter):
    @computed_field
    def create_roles(self) -> str:
        return (
            sql.SQL(
                """
            DO $$
            BEGIN
                -- Create the base role with permissions that all other users will inherit
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {lit_base_role}) THEN
                    CREATE ROLE {base_role} NOINHERIT;
                END IF;

                -- Create the reader role
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {lit_reader_role}) THEN
                    CREATE ROLE {reader_role} INHERIT IN ROLE {base_role};
                END IF;

                -- Create the writer role
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {lit_writer_role}) THEN

                    CREATE ROLE {writer_role} INHERIT IN ROLE {base_role};
                END IF;

                -- Create the admin role
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {lit_admin_role}) THEN
                    CREATE ROLE {admin_role} INHERIT IN ROLE {base_role};
                END IF;

                -- Create the authentication role
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {lit_login_role}) THEN
                    CREATE ROLE {login_role} NOINHERIT LOGIN PASSWORD {password} IN ROLE
                        {base_role};
                END IF;

                -- Grant the reader, writer, and admin roles to the authentication role
                -- Allows the login role to SET ROLE to any of the other roles
                GRANT {reader_role}, {writer_role}, {admin_role} TO {login_role};
            END $$;
            """
            )
            .format(
                lit_base_role=LIT_BASE_ROLE,
                base_role=BASE_ROLE,
                lit_reader_role=LIT_READER_ROLE,
                reader_role=READER_ROLE,
                lit_writer_role=LIT_WRITER_ROLE,
                writer_role=WRITER_ROLE,
                lit_admin_role=LIT_ADMIN_ROLE,
                admin_role=ADMIN_ROLE,
                lit_login_role=LIT_LOGIN_ROLE,
                login_role=LOGIN_ROLE,
                password=settings.DB_USER_PW,
            )
            .as_string()
        )

    @computed_field
    def create_database(self) -> str:
        return (
            sql.SQL(
                """
            -- Create the database
            CREATE DATABASE {db_name} WITH OWNER = {admin_role};
            """
            )
            .format(
                db_name=DB_NAME,
                admin_role=ADMIN_ROLE,
            )
            .as_string()
        )


class CreateSchemasAndExtensions(SQLEmitter):
    @computed_field
    def create_schemas(self) -> str:
        return (
            sql.SQL(
                """
            -- Create the schema_name
            CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {admin_role};
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

    @computed_field
    def create_extensions(self) -> str:
        return (
            sql.SQL(
                """
            -- Create the extensions
            SET search_path TO {schema_name};

            -- Creating the btree_gist extension
            CREATE EXTENSION IF NOT EXISTS btree_gist;

            -- Creating the supa_audit extension
            CREATE EXTENSION IF NOT EXISTS supa_audit CASCADE;

            -- Creating the HSTORE extension
            CREATE EXTENSION IF NOT EXISTS hstore;

            -- Set the pgmeta configuration for supa_audit
            SET pgmeta.log = 'all';
            SET pgmeta.log_relation = on;
            SET pgmeta.log_line_prefix = '%m %u %d [%p]: ';

            -- Creating the pgcrypto extension
            CREATE EXTENSION IF NOT EXISTS pgcrypto;

            -- Creating the pgjwt extension
            CREATE EXTENSION IF NOT EXISTS pgjwt;

            -- Creating the age extension
            CREATE EXTENSION IF NOT EXISTS age;

            -- Configuring the age extension
            ALTER SCHEMA ag_catalog OWNER TO {admin_role};
            GRANT USAGE ON SCHEMA ag_catalog TO
                {admin_role},
                {reader_role},
                {writer_role};
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
            )
            .format(
                admin_role=ADMIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class RevokeAndGrantPrivilegesAndSetSearchPaths(SQLEmitter):
    @computed_field
    def revoke_privileges(self) -> str:
        return (
            sql.SQL(
                """
            -- Explicitly revoke all privileges on all db_schemas and tables
            REVOKE ALL ON SCHEMA
                audit,
                graph,
                ag_catalog,
                {schema_name} 
            FROM
                public,
                {base_role},
                {login_role},
                {reader_role},
                {writer_role},
                {admin_role};

            REVOKE ALL ON ALL TABLES IN SCHEMA
                audit,
                graph,
                ag_catalog,
                {schema_name} 
            FROM
                public,
                {base_role},
                {login_role},
                {reader_role},
                {writer_role},
                {admin_role};

            REVOKE CONNECT ON DATABASE {db_name} FROM
                public,
                {base_role},
                {reader_role},
                {writer_role},
                {admin_role};
            """
            )
            .format(
                db_name=DB_NAME,
                schema_name=DB_SCHEMA,
                base_role=BASE_ROLE,
                login_role=LOGIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                admin_role=ADMIN_ROLE,
            )
            .as_string()
        )

    @computed_field
    def set_search_paths(self) -> str:
        return (
            sql.SQL(
                """
            -- Set the search paths for the roles
            ALTER ROLE
                {base_role}
            SET search_path TO
                {schema_name},
                audit,
                graph,
                ag_catalog;

            ALTER ROLE
                {login_role}
            SET search_path TO
                {schema_name},
                audit,
                graph,
                ag_catalog;

            ALTER ROLE
                {reader_role}
            SET search_path TO
                {schema_name},
                audit,
                graph,
                ag_catalog;

            ALTER ROLE
                {writer_role}
            SET search_path TO
                {schema_name},
                audit,
                graph,
                ag_catalog;

            ALTER ROLE
                {admin_role}
            SET search_path TO
                {schema_name},
                audit,
                graph,
                ag_catalog;
            """
            )
            .format(
                base_role=BASE_ROLE,
                login_role=LOGIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                admin_role=ADMIN_ROLE,
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

    @computed_field
    def grant_schema_privileges(self) -> str:
        return (
            sql.SQL(
                """
            -- Grant ownership of the db_schemas to the DB admin role
            ALTER SCHEMA audit OWNER TO {admin_role};
            ALTER SCHEMA graph OWNER TO {admin_role};
            ALTER SCHEMA ag_catalog OWNER TO {admin_role};

            ALTER SCHEMA {schema_name} OWNER TO {admin_role};
            ALTER TABLE audit.record_version OWNER TO {admin_role};

            -- Grant connect privileges to the DB login role
            GRANT CONNECT ON DATABASE {db_name} TO {login_role};

            -- Grant usage privileges for users to created db_schemas
            GRANT USAGE ON SCHEMA
                audit,
                graph,
                ag_catalog,
                {schema_name}
            TO
                {login_role},
                {admin_role},
                {reader_role},
                {writer_role};

            GRANT CREATE ON SCHEMA
                audit,
                graph,
                {schema_name}
            TO
                {admin_role};

            GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA
                audit,
                graph,
                ag_catalog,
                {schema_name}
            TO
                {login_role},
                {admin_role},
                {reader_role},
                {writer_role};

            GRANT {admin_role} TO {login_role} WITH INHERIT FALSE, SET TRUE;
            GRANT {writer_role} TO {login_role} WITH INHERIT FALSE, SET TRUE;
            GRANT {reader_role} TO {login_role} WITH INHERIT FALSE, SET TRUE;
            """
            )
            .format(
                db_name=DB_NAME,
                schema_name=DB_SCHEMA,
                admin_role=ADMIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                login_role=LOGIN_ROLE,
            )
            .as_string()
        )


class CreatePGULID(SQLEmitter):
    @computed_field
    def create_pgulid(self) -> str:
        with open(f"{settings.UNO_ROOT}/uno/pgulid.sql", "r") as file:
            sql_statment = file.read()
        return sql.SQL(sql_statment).format(schema_name=DB_SCHEMA).as_string()


class CreateTokenSecret(SQLEmitter):
    @computed_field
    def create_token_secret_table(self) -> str:
        return (
            sql.SQL(
                """
            /* creating the token_secret table in database: {db_name} */
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
                /* 
                Delete the existing Token Secret
                Before returing the new token secret
                This ensures we only have one token secret at a time
                We only store this in the database as it is 
                more secure there than in the environment variables
                */
                DELETE FROM audit.token_secret;
                RETURN NEW;
            END;
            $$;

            CREATE TRIGGER set_token_secret_trigger
            BEFORE INSERT ON audit.token_secret
            FOR EACH ROW
            EXECUTE FUNCTION audit.set_token_secret();
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                db_name=DB_NAME,
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class GrantPrivileges(SQLEmitter):
    @computed_field
    def grant_schema_privileges(self) -> str:
        return (
            sql.SQL(
                """
            -- Grant table privileges to the roles
            SET ROLE {admin_role};
            GRANT SELECT ON ALL TABLES IN SCHEMA
                audit,
                graph,
                ag_catalog,
                {schema_name}
            TO
                {reader_role},
                {writer_role};

            GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON ALL TABLES IN SCHEMA
                audit,
                graph,
                {schema_name} 
            TO
                {writer_role},
                {admin_role};

            GRANT ALL ON ALL TABLES IN SCHEMA
                audit,
                graph,
                ag_catalog
            TO
                {admin_role};

            -- Grant table privileges to the roles
            SET ROLE {admin_role};
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA
                audit,
                graph,
                ag_catalog,
                {schema_name}
            TO
                {reader_role},
                {writer_role};

            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class SetRole(SQLEmitter):
    """
    A class that generates SQL statements for managing roles and permissions in a database.

    Methods:
        create_set_role() -> str:
            Generates the SQL statement to create the `set_role` function, which allows
            setting the role dynamically based on the current database and a provided role name.

        set_role_permissions() -> str:
            Generates the SQL statement to manage permissions for the `set_role` function,
            revoking public access and granting execute permissions to specific roles.
    """

    @computed_field
    def create_set_role(self) -> str:
        """
        Generates a SQL script to create a helper function for dynamically
        setting roles within the database.

        Returns:
            str: A SQL script that:
                1. Sets the role to `{db_name}_admin`.
                2. Creates or replaces a `set_role` function in the database. This function accepts
                   a role name as input, constructs a `SET ROLE` command dynamically using the
                   current database name and the provided role name, and executes it.

        Notes:
            - The `set_role` function uses PL/pgSQL as its language.
            - The `db_name` is dynamically injected into the SQL script using the `DB_NAME` variable.
            - The function raises a log in the database to confirm the role change.
        """
        return textwrap.dedent(
            sql.SQL(
                """
            SET ROLE {db_name}_admin;
            -- Create the set_role function
            CREATE OR REPLACE FUNCTION set_role(role_name TEXT)
            RETURNS VOID
            LANGUAGE plpgsql
            AS $$
            DECLARE
                db_name TEXT := current_database();
                set_role_command TEXT;  
                complete_role_name TEXT:= CONCAT(db_name, '_', role_name);
            BEGIN
                set_role_command := CONCAT('SET ROLE ', complete_role_name);
                EXECUTE set_role_command;
                --RAISE LOG 'Role set to: % by User: %, in Database: %', complete_role_name, current_user, db_name;
            END $$;
            """
            )
            .format(db_name=DB_NAME)
            .as_string()
        )

    @computed_field
    def set_role_permissions(self) -> str:
        return (
            sql.SQL(
                """
            -- REVOKE EXECUTE permission on the set_role function from public
            REVOKE EXECUTE ON FUNCTION set_role(TEXT) FROM public;
            -- Grant EXECUTE permission on the set_role function to the login role
            GRANT EXECUTE ON FUNCTION set_role(TEXT) TO {login_role}, {reader_role}, {writer_role};
            """
            )
            .format(
                login_role=LOGIN_ROLE, reader_role=READER_ROLE, writer_role=WRITER_ROLE
            )
            .as_string()
        )
