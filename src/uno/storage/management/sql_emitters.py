# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from psycopg.sql import SQL, Identifier

from sqlalchemy import text
from sqlalchemy.engine import Connection

from uno.storage.sql.sql_emitter import (
    SQLEmitter,
    DB_SCHEMA,
    DB_NAME,
    ADMIN_ROLE,
    WRITER_ROLE,
    READER_ROLE,
    LOGIN_ROLE,
    BASE_ROLE,
    LIT_BASE_ROLE,  # Necessary for searchiing pg_roles
    LIT_READER_ROLE,  # Necessary for searchiing pg_roles
    LIT_WRITER_ROLE,  # Necessary for searchiing pg_roles
    LIT_ADMIN_ROLE,  # Necessary for searchiing pg_roles
    LIT_LOGIN_ROLE,  # Necessary for searchiing pg_roles
)
from uno.config import settings


class SetRole(SQLEmitter):
    def _emit_sql(self, conn: Connection, role_name: str) -> None:
        conn.execute(
            text(
                SQL(
                    """
            SET ROLE {db_name}_{role};
            """
                )
                .format(
                    db_name=DB_NAME,
                    role=SQL(role_name),
                )
                .as_string()
            )
        )


class DropDatabaseAndRoles(SQLEmitter):

    def _emit_sql(self, conn: Connection) -> None:

        self.drop_database(conn)
        self.drop_roles(conn)

    def drop_database(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Drop the database if it exists
            DROP DATABASE IF EXISTS {db_name} WITH (FORCE);
            """
                )
                .format(db_name=DB_NAME)
                .as_string()
            )
        )

    def drop_roles(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Drop the roles if they exist
            DROP ROLE IF EXISTS {admin_role};
            DROP ROLE IF EXISTS {writer_role};
            DROP ROLE IF EXISTS {reader_role};
            DROP ROLE IF EXISTS {login_role};
            DROP ROLE IF EXISTS {base_role};
            """
                )
                .format(
                    admin_role=ADMIN_ROLE,
                    writer_role=WRITER_ROLE,
                    reader_role=READER_ROLE,
                    login_role=LOGIN_ROLE,
                    base_role=BASE_ROLE,
                )
                .as_string()
            )
        )


class CreateRolesAndDatabase(SQLEmitter):

    def _emit_sql(self, conn: Connection) -> None:
        self.create_roles(conn)
        self.create_database(conn)

    def create_roles(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
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
        )

    def create_database(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Create the database
            CREATE DATABASE {db_name} WITH OWNER = {admin_role};
            """
                )
                .format(db_name=DB_NAME, admin_role=ADMIN_ROLE)
                .as_string()
            )
        )


class InsertSchemasAndExtensions(SQLEmitter):
    def _emit_sql(self, conn: Connection) -> None:
        self.create_schemas(conn)
        self.create_extensions(conn)

    def create_schemas(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Create the db_schema
            CREATE SCHEMA IF NOT EXISTS {db_schema} AUTHORIZATION {admin_role};
            """
                )
                .format(
                    admin_role=ADMIN_ROLE,
                    db_schema=DB_SCHEMA,
                )
                .as_string()
            )
        )

    def create_extensions(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Create the extensions
            SET search_path TO {db_schema};

            -- Creating the btree_gist extension
            CREATE EXTENSION IF NOT EXISTS btree_gist;

            -- Creating the supa_audit extension
            CREATE EXTENSION IF NOT EXISTS supa_audit CASCADE;

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
            GRANT USAGE ON SCHEMA ag_catalog TO
                {admin_role},
                {reader_role},
                {writer_role};
            ALTER SCHEMA ag_catalog OWNER TO {admin_role};
            SELECT * FROM ag_catalog.create_graph('graph');
            ALTER TABLE ag_catalog.ag_graph OWNER TO {admin_role};
            ALTER TABLE ag_catalog.ag_label OWNER TO {admin_role};
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
                    db_schema=DB_SCHEMA,
                )
                .as_string()
            )
        )


class GrantPrivilegesAndSetSearchPaths(SQLEmitter):

    def _emit_sql(self, conn: Connection) -> None:
        self.revokePrivileges(conn)
        self.setSearchPath(conn)
        self.grantSchemaPrivileges(conn)

    def revokePrivileges(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Explicitly revoke all privileges on all db_schemas and tables
            REVOKE ALL ON SCHEMA
                audit,
                graph,
                ag_catalog,
                {db_schema} 
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
                {db_schema} 
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
                    db_schema=DB_SCHEMA,
                    base_role=BASE_ROLE,
                    login_role=LOGIN_ROLE,
                    reader_role=READER_ROLE,
                    writer_role=WRITER_ROLE,
                    admin_role=ADMIN_ROLE,
                )
                .as_string()
            )
        )

    def setSearchPath(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Set the search paths for the roles
            ALTER ROLE
                {base_role}
            SET search_path TO
                {db_schema},
                audit,
                graph,
                ag_catalog;

            ALTER ROLE
                {login_role}
            SET search_path TO
                {db_schema},
                audit,
                graph,
                ag_catalog;

            ALTER ROLE
                {reader_role}
            SET search_path TO
                {db_schema},
                audit,
                graph,
                ag_catalog;

            ALTER ROLE
                {writer_role}
            SET search_path TO
                {db_schema},
                audit,
                graph,
                ag_catalog;

            ALTER ROLE
                {admin_role}
            SET search_path TO
                {db_schema},
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
                    db_schema=DB_SCHEMA,
                )
                .as_string()
            )
        )

    def grantSchemaPrivileges(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Grant ownership of the db_schemas to the DB admin role
            ALTER SCHEMA audit OWNER TO {admin_role};
            ALTER SCHEMA graph OWNER TO {admin_role};
            ALTER SCHEMA ag_catalog OWNER TO {admin_role};

            ALTER SCHEMA {db_schema} OWNER TO {admin_role};
            ALTER TABLE audit.record_version OWNER TO {admin_role};

            -- Grant connect privileges to the DB login role
            GRANT CONNECT ON DATABASE {db_name} TO {login_role};

            -- Grant usage privileges for users to created db_schemas
            GRANT USAGE ON SCHEMA
                audit,
                graph,
                ag_catalog,
                {db_schema}
            TO
                {login_role},
                {admin_role},
                {reader_role},
                {writer_role};

            GRANT CREATE ON SCHEMA
                audit,
                graph,
                {db_schema}
            TO
                {admin_role};

            GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA
                audit,
                graph,
                ag_catalog,
                {db_schema}
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
                    db_schema=DB_SCHEMA,
                    admin_role=ADMIN_ROLE,
                    reader_role=READER_ROLE,
                    writer_role=WRITER_ROLE,
                    login_role=LOGIN_ROLE,
                )
                .as_string()
            )
        )


class CreatePGULID(SQLEmitter):

    def _emit_sql(self, conn: Connection) -> None:
        with open("src/uno/db/sql/pgulid.sql", "r") as file:
            sql = file.read()
        conn.execute(text(SQL(sql).format(db_schema=DB_SCHEMA).as_string()))


class CreateTokenSecret(SQLEmitter):
    def _emit_sql(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
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
                    db_schema=DB_SCHEMA,
                )
                .as_string()
            )
        )


class GrantPrivileges(SQLEmitter):
    def _emit_sql(self, conn: Connection) -> None:
        self.grant_table_privileges(conn)
        self.grant_sequence_privileges(conn)

    def grant_table_privileges(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Grant table privileges to the roles
            SET ROLE {admin_role};
            GRANT SELECT ON ALL TABLES IN SCHEMA
                audit,
                graph,
                ag_catalog,
                {db_schema}
            TO
                {reader_role},
                {writer_role};

            GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON ALL TABLES IN SCHEMA
                audit,
                graph,
                {db_schema} 
            TO
                {writer_role},
                {admin_role};

            --REVOKE SELECT, INSERT, UPDATE (id) ON user FROM 
            --    {reader_role},
            --    {writer_role};

            GRANT ALL ON ALL TABLES IN SCHEMA
                audit,
                graph,
                ag_catalog
            TO
                {admin_role};
            """
                )
                .format(
                    admin_role=ADMIN_ROLE,
                    reader_role=READER_ROLE,
                    writer_role=WRITER_ROLE,
                    db_schema=DB_SCHEMA,
                )
                .as_string()
            )
        )

    def grant_sequence_privileges(self, conn: Connection) -> None:
        conn.execute(
            text(
                SQL(
                    """
                    -- Grant table privileges to the roles
                    SET ROLE {admin_role};
                    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA
                        audit,
                        graph,
                        ag_catalog,
                        {db_schema}
                    TO
                        {reader_role},
                        {writer_role};

                    """
                )
                .format(
                    admin_role=ADMIN_ROLE,
                    reader_role=READER_ROLE,
                    writer_role=WRITER_ROLE,
                    db_schema=DB_SCHEMA,
                )
                .as_string()
            )
        )


class InsertMetaRecordFunction(SQLEmitter):
    def _emit_sql(self, conn: Connection) -> None:
        function_string = (
            SQL(
                """
            DECLARE
                meta_id VARCHAR(26) := {db_schema}.generate_ulid();
                table_name VARCHAR(255) := TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME;
            BEGIN
                /*
                Function used to insert a record into the meta_record table, when a 
                polymorphic record is inserted.
                */
                SET ROLE {writer_role};
                INSERT INTO {db_schema}.meta_record (id, meta_type_id)
                    VALUES (meta_id, table_name);
                NEW.id = meta_id;
                RETURN NEW;
            END;
            """
            )
            .format(
                db_schema=DB_SCHEMA,
                writer_role=WRITER_ROLE,
            )
            .as_string()
        )

        conn.execute(
            text(
                self.create_sql_function(
                    "insert_meta_record",
                    function_string,
                    timing="BEFORE",
                    operation="INSERT",
                    # security_definer="SECURITY DEFINER",
                    include_trigger=False,
                    db_function=True,
                )
            )
        )
