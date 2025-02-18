# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from psycopg.sql import SQL, Identifier, Literal

from uno.db.sql_emitters import SQLEmitter
from uno.config import settings


# SQL Literal and Identifier objects are used to create SQL strings
# that are passed to the database for execution.

# SQL Literals
LIT_ADMIN_ROLE = Literal(f"{settings.DB_NAME}_admin")
LIT_WRITER_ROLE = Literal(f"{settings.DB_NAME}_writer")
LIT_READER_ROLE = Literal(f"{settings.DB_NAME}_reader")
LIT_LOGIN_ROLE = Literal(f"{settings.DB_NAME}_login")
LIT_BASE_ROLE = Literal(f"{settings.DB_NAME}_base_role")

# SQL Identifiers
ADMIN_ROLE = Identifier(f"{settings.DB_NAME}_admin")
WRITER_ROLE = Identifier(f"{settings.DB_NAME}_writer")
READER_ROLE = Identifier(f"{settings.DB_NAME}_reader")
LOGIN_ROLE = Identifier(f"{settings.DB_NAME}_login")
BASE_ROLE = Identifier(f"{settings.DB_NAME}_base_role")
DB_NAME = Identifier(settings.DB_NAME)
DB_SCHEMA = Identifier(settings.DB_SCHEMA)


@dataclass
class DropDatabaseSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return (
            SQL(
                """
            -- Drop the database if it exists
            DROP DATABASE IF EXISTS {} WITH (FORCE);
            """
            )
            .format(DB_NAME)
            .as_string()
        )


class DropRolesSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return (
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


class CreateRolesSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return (
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


class CreateDatabaseSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return (
            SQL(
                """
            -- Create the database
            CREATE DATABASE {db_name} WITH OWNER = {admin};
            """
            )
            .format(db_name=DB_NAME, admin=ADMIN_ROLE)
            .as_string()
        )


class CreateSchemasAndExtensionsSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return "\n".join(
            [
                self.emit_create_schemas_sql(),
                self.emit_create_extensions_sql(),
            ]
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
    def emit_sql(self) -> str:
        return "\n".join(
            [
                self.emit_revoke_access_sql(),
                self.emit_set_search_paths_sql(),
                self.emit_grant_schema_privileges_sql(),
            ]
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
    def emit_sql(self) -> str:
        return (
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


class PGULIDSQLSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return SQL(
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


class CreateTokenSecretSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return (
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
