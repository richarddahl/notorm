# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from psycopg.sql import SQL, Identifier, Literal, Placeholder

from sqlalchemy import text
from sqlalchemy.engine import Engine

from uno.db.sql_emitters import (
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


@dataclass
class DropDatabaseSQL(SQLEmitter):
    """Drop database SQL emitter.

    This class extends SQLEmitter to generate and execute SQL for dropping a database.
    It forces the drop operation even if there are active connections.

    Note:
        This is a destructive operation that cannot be undone. Use with caution.

    Args:
        None

    Returns:
        None

    Raises:
        SQLAlchemyError: If there is an error executing the DROP DATABASE statement
    """

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Drop the database if it exists
            DROP DATABASE IF EXISTS {} WITH (FORCE);
            """
                )
                .format(DB_NAME)
                .as_string()
            )
        )


class DropRolesSQL(SQLEmitter):
    """Drop database roles used by the application.

    This class handles the removal of all application-specific database roles,
    including admin, writer, reader, login, and base roles. It uses a single SQL
    statement to drop all roles if they exist.

    Attributes:
        None

    Methods:
        emit_sql(conn: Engine) -> None: Executes SQL to drop all application roles.

    Args:
        conn (Engine): SQLAlchemy Engine connection object to execute SQL statements.

    Returns:
        None
    """

    def emit_sql(self, conn: Engine) -> None:
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


class CreateRolesSQL(SQLEmitter):
    """Creates a set of database roles with a hierarchical permission structure in PostgreSQL.

    This class creates the following roles if they don't already exist:
    - Base role: Foundation role that other roles inherit from
    - Reader role: Inherits from base role, for read-only access
    - Writer role: Inherits from base role, for write access
    - Admin role: Inherits from base role, for administrative access
    - Login role: Authentication role that can switch to other roles

    The roles are created using a DO block in PostgreSQL to ensure idempotency.
    The login role is granted the ability to switch to reader, writer, and admin roles.

    Args:
        conn (Engine): SQLAlchemy Engine instance representing the database connection

    Returns:
        None

    """

    def emit_sql(self, conn: Engine) -> None:
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


class CreateDatabaseSQL(SQLEmitter):
    """
    A class that emits SQL to create a new database.

    This class extends SQLEmitter to generate and execute SQL statements for database creation.
    The SQL statement sets the specified database name and assigns an admin role as the owner.

    Attributes:
        Inherits all attributes from SQLEmitter parent class.

    Methods:
        emit_sql(conn: Engine) -> None:
            Executes SQL to create a new database with specified owner.

    Args:
        conn (Engine): SQLAlchemy Engine connection object used to execute the SQL.

    Returns:
        None
    """

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Create the database
            CREATE DATABASE {db_name} WITH OWNER = {admin};
            """
                )
                .format(db_name=DB_NAME, admin=ADMIN_ROLE)
                .as_string()
            )
        )


class CreateSchemasAndExtensionsSQL(SQLEmitter):
    """SQL emitter for creating schemas and extensions in a PostgreSQL database.

    This class is responsible for generating and executing SQL statements that:
    1. Create the necessary schemas (uno and application-specific schema)
    2. Set up required PostgreSQL extensions (btree_gist, supa_audit, pgcrypto, pgjwt, age)
    3. Configure permissions and ownership for the Apache AGE (age) graph extension

    Attributes:
        None

    Methods:
        emit_sql(conn: Engine) -> str:
            Executes the combined SQL statements for creating schemas and extensions.

        emit_create_schemas_sql() -> str:
            Generates SQL for creating the uno and application-specific schemas.

        emit_create_extensions_sql() -> str:
            Generates SQL for creating and configuring all required PostgreSQL extensions.

    Dependencies:
        - SQLAlchemy Engine for database connection
        - PostgreSQL with support for the specified extensions
        - Required roles (ADMIN_ROLE, READER_ROLE, WRITER_ROLE) must be defined
    """

    def emit_sql(self, conn: Engine) -> str:
        conn.execute(
            text(
                f"""
                {self.emit_create_schemas_sql()}
                {self.emit_create_extensions_sql()}
                """
            )
        )

    def emit_create_schemas_sql(self) -> str:
        return (
            SQL(
                """
            -- Create the uno schemas
            CREATE SCHEMA IF NOT EXISTS uno AUTHORIZATION {admin_role};
            CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {admin_role};
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                schema=DB_SCHEMA,
            )
            .as_string()
        )

    def emit_create_extensions_sql(self) -> str:
        return (
            SQL(
                """
            -- Create the extensions
            SET search_path TO uno;

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
            )
            .as_string()
        )


class PrivilegeAndSearchPathSQL(SQLEmitter):
    """A SQL emitter class responsible for managing database privileges and search paths.

    This class generates SQL statements to configure database access controls and search paths
    for different database roles. It handles three main operations:
    1. Revoking existing access privileges
    2. Setting up search paths for different roles
    3. Granting appropriate schema privileges

    Methods:
        emit_sql(conn: Engine) -> str:
            Executes all SQL statements in the correct order using the provided database connection.

        emit_revoke_access_sql() -> str:
            Generates SQL to revoke all existing privileges from schemas and tables for all roles.

        emit_set_search_paths_sql() -> str:
            Generates SQL to set up the search path hierarchy for each database role.

        emit_grant_schema_privileges_sql() -> str:
            Generates SQL to grant appropriate privileges to schemas and set up role inheritance.

    The class manages privileges for the following schemas:
    - uno
    - audit
    - graph
    - ag_catalog
    - custom schema (specified by DB_SCHEMA)

    And handles the following roles:
    - base role
    - login role
    - reader role
    - writer role
    - admin role
    """

    def emit_sql(self, conn: Engine) -> str:
        conn.execute(
            text(
                "\n".join(
                    [
                        self.emit_revoke_access_sql(),
                        self.emit_set_search_paths_sql(),
                        self.emit_grant_schema_privileges_sql(),
                    ]
                )
            )
        )

    def emit_revoke_access_sql(self) -> str:
        return (
            SQL(
                """
            -- Explicitly revoke all privileges on all schemas and tables
            REVOKE ALL ON SCHEMA
                uno,
                audit,
                graph,
                ag_catalog,
                {schema} 
            FROM
                public,
                {base_role},
                {login_role},
                {reader_role},
                {writer_role},
                {admin_role};

            REVOKE ALL ON ALL TABLES IN SCHEMA
                uno,
                audit,
                graph,
                ag_catalog,
                {schema} 
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
                schema=DB_SCHEMA,
                base_role=BASE_ROLE,
                login_role=LOGIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                admin_role=ADMIN_ROLE,
            )
            .as_string()
        )

    def emit_set_search_paths_sql(self) -> str:
        return (
            SQL(
                """
            -- Set the search paths for the roles
            ALTER ROLE
                {base_role}
            SET search_path TO
                ag_catalog,
                uno,
                audit,
                graph,
                {schema};

            ALTER ROLE
                {login_role}
            SET search_path TO
                ag_catalog,
                uno,
                audit,
                graph,
                {schema};


            ALTER ROLE
                {reader_role}
            SET search_path TO
                ag_catalog,
                uno,
                audit,
                graph,
                {schema};

            ALTER ROLE
                {writer_role}
            SET search_path TO
                ag_catalog,
                uno,
                audit,
                graph,
                {schema};

            ALTER ROLE
                {admin_role}
            SET search_path TO
                ag_catalog,
                uno,
                audit,
                graph,
                {schema};
            """
            )
            .format(
                base_role=BASE_ROLE,
                login_role=LOGIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                admin_role=ADMIN_ROLE,
                schema=DB_SCHEMA,
            )
            .as_string()
        )

    def emit_grant_schema_privileges_sql(self) -> str:
        return (
            SQL(
                """
            -- Grant ownership of the uno schemas to the DB admin role
            ALTER SCHEMA audit OWNER TO {admin_role};
            ALTER SCHEMA uno OWNER TO {admin_role};
            ALTER SCHEMA graph OWNER TO {admin_role};
            ALTER SCHEMA ag_catalog OWNER TO {admin_role};

            ALTER SCHEMA {schema} OWNER TO {admin_role};
            ALTER TABLE audit.record_version OWNER TO {admin_role};

            -- Grant connect privileges to the DB login role
            GRANT CONNECT ON DATABASE {db_name} TO {login_role};

            -- Grant usage privileges for users to created schemas
            GRANT USAGE ON SCHEMA
                uno,
                audit,
                graph,
                ag_catalog,
                {schema}
            TO
                {login_role},
                {admin_role},
                {reader_role},
                {writer_role};

            GRANT CREATE ON SCHEMA
                uno,
                audit,
                graph,
                {schema}
            TO
                {admin_role};

            GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA
                uno,
                audit,
                graph,
                ag_catalog,
                {schema}
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
                schema=DB_SCHEMA,
                admin_role=ADMIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                login_role=LOGIN_ROLE,
            )
            .as_string()
        )


class TablePrivilegeSQL(SQLEmitter):
    """SQL emitter for managing table privileges in PostgreSQL database.

    This class handles the emission of SQL statements that manage table privileges for different roles
    in the database. It sets up a hierarchical permission structure where:
    - Admin role has full privileges on all schemas
    - Writer role has CRUD operations on most tables
    - Reader role has read-only access to most tables

    The privileges are granted on the following schemas:
    - uno
    - audit
    - graph
    - ag_catalog
    - custom schema (specified by DB_SCHEMA)

    Special cases:
    - The 'id' column of uno.user table has restricted access for reader and writer roles

    Args:
        None

    Returns:
        None

    Raises:
        SQLAlchemyError: If there's an error executing the SQL statements
    """

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Grant table privileges to the roles
            SET ROLE {admin_role};
            GRANT SELECT ON ALL TABLES IN SCHEMA
                uno,
                audit,
                graph,
                ag_catalog,
                {schema}
            TO
                {reader_role},
                {writer_role};

            GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON ALL TABLES IN SCHEMA
                uno,
                audit,
                graph,
                {schema} 
            TO
                {writer_role},
                {admin_role};

            REVOKE SELECT, INSERT, UPDATE (id) ON uno.user FROM 
                {reader_role},
                {writer_role};

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
                    schema=DB_SCHEMA,
                )
                .as_string()
            )
        )


class PGULIDSQLSQL(SQLEmitter):
    """Emitter class for PostgreSQL ULID generation SQL function.

    This class emits SQL code that creates a PostgreSQL function 'uno.generate_ulid()'
    which generates Universally Unique Lexicographically Sortable Identifiers (ULIDs).

    A ULID is a 26-character Crockford Base32 string, encoding:
    - First 10 characters: timestamp with millisecond precision
    - Last 16 characters: random values for uniqueness

    The implementation is based on OK Log's Go implementation of the ULID spec
    (https://github.com/oklog/ulid).

    Attributes:
        None

    Methods:
        emit_sql(conn: Engine) -> str: Executes SQL to create the ULID generation function
            Args:
                conn (Engine): SQLAlchemy engine connection object
            Returns:
                str: Empty string as function creates PostgreSQL function
    """

    def emit_sql(self, conn: Engine) -> str:
        conn.execute(
            text(
                SQL(
                    """
            -- pgulid is based on OK Log's Go implementation of the ULID spec
            --
            -- https://github.com/oklog/ulid
            -- https://github.com/ulid/spec
            --
            -- Copyright 2016 The Oklog Authors
            -- Licensed under the Apache License, Version 2.0 (the "License");
            -- you may not use this file except in compliance with the License.
            -- You may obtain a copy of the License at
            --
            -- http://www.apache.org/licenses/LICENSE-2.0
            --
            -- Unless required by applicable law or agreed to in writing, software
            -- distributed under the License is distributed on an "AS IS" BASIS,
            -- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
            -- See the License for the specific language governing permissions and
            -- limitations under the License.

            CREATE EXTENSION IF NOT EXISTS pgcrypto;

            CREATE FUNCTION uno.generate_ulid()
            RETURNS TEXT
            AS $$
            DECLARE
            -- Crockford's Base32
            encoding   BYTEA = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';
            timestamp  BYTEA = '\\000\\000\\000\\000\\000\\000';
            output     TEXT = '';

            unix_time  BIGINT;
            ulid       BYTEA;
            BEGIN
            -- 6 timestamp bytes
            unix_time = (EXTRACT(EPOCH FROM CLOCK_TIMESTAMP()) * 1000)::BIGINT;
            timestamp = SET_BYTE(timestamp, 0, (unix_time >> 40)::BIT(8)::INTEGER);
            timestamp = SET_BYTE(timestamp, 1, (unix_time >> 32)::BIT(8)::INTEGER);
            timestamp = SET_BYTE(timestamp, 2, (unix_time >> 24)::BIT(8)::INTEGER);
            timestamp = SET_BYTE(timestamp, 3, (unix_time >> 16)::BIT(8)::INTEGER);
            timestamp = SET_BYTE(timestamp, 4, (unix_time >> 8)::BIT(8)::INTEGER);
            timestamp = SET_BYTE(timestamp, 5, unix_time::BIT(8)::INTEGER);

            -- 10 entropy bytes
            ulid = timestamp || uno.gen_random_bytes(10);

            -- Encode the timestamp
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 0) & 224) >> 5));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 0) & 31)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 1) & 248) >> 3));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 1) & 7) << 2) | ((GET_BYTE(ulid, 2) & 192) >> 6)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 2) & 62) >> 1));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 2) & 1) << 4) | ((GET_BYTE(ulid, 3) & 240) >> 4)));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 3) & 15) << 1) | ((GET_BYTE(ulid, 4) & 128) >> 7)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 4) & 124) >> 2));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 4) & 3) << 3) | ((GET_BYTE(ulid, 5) & 224) >> 5)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 5) & 31)));

            -- Encode the entropy
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 6) & 248) >> 3));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 6) & 7) << 2) | ((GET_BYTE(ulid, 7) & 192) >> 6)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 7) & 62) >> 1));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 7) & 1) << 4) | ((GET_BYTE(ulid, 8) & 240) >> 4)));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 8) & 15) << 1) | ((GET_BYTE(ulid, 9) & 128) >> 7)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 9) & 124) >> 2));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 9) & 3) << 3) | ((GET_BYTE(ulid, 10) & 224) >> 5)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 10) & 31)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 11) & 248) >> 3));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 11) & 7) << 2) | ((GET_BYTE(ulid, 12) & 192) >> 6)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 12) & 62) >> 1));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 12) & 1) << 4) | ((GET_BYTE(ulid, 13) & 240) >> 4)));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 13) & 15) << 1) | ((GET_BYTE(ulid, 14) & 128) >> 7)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 14) & 124) >> 2));
            output = output || CHR(GET_BYTE(encoding, ((GET_BYTE(ulid, 14) & 3) << 3) | ((GET_BYTE(ulid, 15) & 224) >> 5)));
            output = output || CHR(GET_BYTE(encoding, (GET_BYTE(ulid, 15) & 31)));

            RETURN output;
            END
            $$
            LANGUAGE plpgsql
            VOLATILE;
            """
                ).as_string()
            )
        )


class CreateTokenSecretSQL(SQLEmitter):
    """Creates a table and associated trigger for managing authentication token secrets in the database.

    This class generates SQL to:
    1. Create a 'token_secret' table in the 'uno' schema with a single TEXT column
    2. Create a trigger function that ensures only one token secret exists at a time
    3. Create a trigger that runs the function before inserts

    The token_secret table is designed to store a single authentication secret used
    for signing JWT tokens. The trigger mechanism ensures that any new secret insertion
    will first delete the existing secret, maintaining only one active secret.

    This approach provides more security than environment variables by storing the
    secret in the database.

    Args:
        None

    Returns:
        None: Executes SQL statements directly on the database connection
    """

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """

            /* creating the token_secret table in database: {db_name} */
            SET ROLE {admin_role};
            CREATE TABLE uno.token_secret (
                token_secret TEXT PRIMARY KEY
            );

            CREATE OR REPLACE FUNCTION uno.set_token_secret()
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
                DELETE FROM uno.token_secret;
                RETURN NEW;
            END;
            $$;

            CREATE TRIGGER set_token_secret_trigger
            BEFORE INSERT ON uno.token_secret
            FOR EACH ROW
            EXECUTE FUNCTION uno.set_token_secret();
            """
                )
                .format(admin_role=ADMIN_ROLE, db_name=DB_NAME)
                .as_string()
            )
        )


@dataclass
class AlterTablesBeforeInsertFirstUser(SQLEmitter):
    """Class for emitting SQL to modify tables before inserting the first user.

    This class handles the necessary table modifications required before inserting
    the initial user into the system. It performs the following operations:
    1. Sets the role to admin
    2. Disables row level security on the user table
    3. Drops NOT NULL constraints on created_by_id and modified_by_id columns in meta table

    Inherits from SQLEmitter base class.

    Methods:
        emit_sql(conn: Engine) -> None: Executes the SQL statements using the provided database connection
    """

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """
                -- Set the role to the admin role
                SET ROLE {admin};
                -- Disable row level security on the user table
                ALTER TABLE {db_schema}.user DISABLE ROW LEVEL SECURITY;

                -- Drop the NOT NULL constraint on the user table for the created_by_id and modified_by_id columns
                ALTER TABLE {db_schema}.user ALTER COLUMN created_by_id DROP NOT NULL;
                ALTER TABLE {db_schema}.user ALTER COLUMN modified_by_id DROP NOT NULL;
            """
                )
                .format(admin=ADMIN_ROLE, db_schema=DB_SCHEMA)
                .as_string()
            )
        )


@dataclass
class UpdateRecordOfFirstUser(SQLEmitter):
    user_id: str = None

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """
                -- Set the role to the writer role
                SET ROLE {writer};
                -- Update the user record for the first user
                UPDATE {db_schema}.user
                SET created_by_id = {user_id}, modified_by_id = {user_id}
                WHERE id = {user_id};
            """
                )
                .format(
                    writer=WRITER_ROLE,
                    db_schema=DB_SCHEMA,
                    user_id=self.user_id,
                )
                .as_string()
            )
        )


@dataclass
class AlterTablesAfterInsertFirstUser(SQLEmitter):
    """Emits SQL to alter tables after first user is inserted.

    After the first user is inserted, this class emits SQL that:
    1. Sets the role to admin
    2. Adds NOT NULL constraints to created_by_id and modified_by_id columns in the meta table
    3. Enables row level security on the user table

    Args:
        None

    Inherits:
        SQLEmitter

    Methods:
        emit_sql(conn: Engine) -> None: Executes the SQL statements using the provided database connection
    """

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """
                -- Set the role to the admin role
                SET ROLE {admin};
                -- Add the null constraint back to the user table for the created_by_id and modified_by_id columns
                ALTER TABLE {db_schema}.user ALTER COLUMN created_by_id SET NOT NULL;
                ALTER TABLE {db_schema}.user ALTER COLUMN modified_by_id SET NOT NULL;

                -- Enable row level security on the user table
                ALTER TABLE {db_schema}.user ENABLE ROW LEVEL SECURITY;
            """
                )
                .format(admin=ADMIN_ROLE, db_schema=DB_SCHEMA)
                .as_string()
            )
        )


@dataclass
class InsertMetaFunctionSQL(SQLEmitter):
    def emit_sql(self, conn: Engine) -> None:
        function_string = (
            SQL(
                """
            DECLARE
                meta_id VARCHAR(26) := {db_schema}.generate_ulid();
            BEGIN
                /*
                Function used to insert a record into the meta table, when a record is inserted
                into a table that has a PK that is a FKDefinition to the meta table.
                Set as a trigger on the table, so that the meta record is created when the
                record is created.
                */

                SET ROLE {writer};
                INSERT INTO {db_schema}.meta (id, meta_type_name)
                    VALUES (meta_id, TG_TABLE_NAME);
                NEW.id = meta_id;
                RETURN NEW;
            END;
            """
            )
            .format(
                db_schema=DB_SCHEMA,
                writer=WRITER_ROLE,
            )
            .as_string()
        )

        conn.execute(
            text(
                self.create_sql_function(
                    "insert_meta",
                    function_string,
                    timing="BEFORE",
                    operation="INSERT",
                    include_trigger=False,
                    db_function=True,
                )
            )
        )
