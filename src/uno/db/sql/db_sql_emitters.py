# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from pydantic import computed_field
from psycopg.sql import SQL

from uno.db.sql.sql_emitter import (
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
    @computed_field
    def set_role(self, role_name: str) -> str:
        return (
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


class DropDatabaseAndRoles(SQLEmitter):
    @computed_field
    def drop_database(self) -> str:
        return (
            SQL(
                """
            -- Drop the database if it exists
            DROP DATABASE IF EXISTS {db_name} WITH (FORCE);
            """
            )
            .format(db_name=DB_NAME)
            .as_string()
        )

    @computed_field
    def drop_roles(self) -> str:
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


class CreateRolesAndDatabase(SQLEmitter):
    @computed_field
    def create_roles(self) -> str:
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

    @computed_field
    def create_database(self) -> str:
        return (
            SQL(
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
            SQL(
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
    def creaet_extensions(self) -> str:
        return (
            SQL(
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
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class RevokeAndGrantPrivilegesAndSetSearchPaths(SQLEmitter):
    @computed_field
    def revoke_privileges(self) -> str:
        return (
            SQL(
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
            SQL(
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
            SQL(
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
        with open("src/uno/db/sql/pgulid.sql", "r") as file:
            sql = file.read()
        return SQL(sql).format(schema_name=DB_SCHEMA).as_string()


class CreateTokenSecret(SQLEmitter):
    @computed_field
    def create_token_secret_table(self) -> str:
        return (
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
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class GrantPrivileges(SQLEmitter):
    @computed_field
    def grant_schema_privileges(self) -> str:
        return (
            SQL(
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


class InsertMetaRecordFunction(SQLEmitter):
    @computed_field
    def insert_meta_record_function(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                meta_id VARCHAR(26) := {schema_name}.generate_ulid();
            BEGIN
                /*
                Function used to insert a record into the meta table, when a 
                polymorphic record is inserted.
                */
                SET ROLE {writer_role};

                INSERT INTO {schema_name}.meta (id, meta_type_id) VALUES (meta_id, TG_TABLE_NAME);
                NEW.id = meta_id;
                RETURN NEW;
            END;
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                writer_role=WRITER_ROLE,
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_meta_record",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=False,
            db_function=True,
        )


class InsertMetaRecordTrigger(SQLEmitter):
    @computed_field
    def insert_meta_record_trigger(self) -> str:
        return self.create_sql_trigger(
            "insert_meta_record",
            timing="BEFORE",
            operation="INSERT",
            for_each="ROW",
            db_function=True,
        )


class RecordStatusFunction(SQLEmitter):
    @computed_field
    def insert_status_columns(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                now TIMESTAMP := NOW();
            BEGIN
                SET ROLE {writer_role};

                IF TG_OP = 'INSERT' THEN
                    NEW.is_active = TRUE;
                    NEW.is_deleted = FALSE;
                    NEW.created_at = now;
                    NEW.modified_at = now;
                ELSIF TG_OP = 'UPDATE' THEN
                    NEW.modified_at = now;
                ELSIF TG_OP = 'DELETE' THEN
                    NEW.is_active = FALSE;
                    NEW.is_deleted = TRUE;
                    NEW.deleted_at = now;
                END IF;

                RETURN NEW;
            END;
            """
            )
            .format(writer_role=WRITER_ROLE)
            .as_string()
        )

        return self.create_sql_function(
            "insert_record_status_columns",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
            db_function=True,
        )


class RecordUserAuditFunction(SQLEmitter):
    @computed_field
    def manage_record_user_audit_columns(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                user_id VARCHAR(26) := current_setting('rls_var.user_id', TRUE);
            BEGIN
                SET ROLE {writer_role};


                IF user_id IS NULL OR user_id = '' THEN
                    IF EXISTS (SELECT id FROM {schema_name}.user) THEN
                        RAISE EXCEPTION 'No user def ined in rls_vars';
                    END IF;
                END IF;
                IF NOT EXISTS (SELECT id FROM {schema_name}.user WHERE id = user_id) THEN
                    RAISE EXCEPTION 'User ID in rls_vars is not a valid user';
                END IF;

                IF TG_OP = 'INSERT' THEN
                    NEW.created_by_id = user_id;
                    NEW.modified_by_id = user_id;
                ELSIF TG_OP = 'UPDATE' THEN
                    NEW.modified_by_id = user_id;
                ELSIF TG_OP = 'DELETE' THEN
                    NEW.deleted_by_id = user_id;
                END IF;

                RETURN NEW;
            END;
            """
            )
            .format(
                writer_role=WRITER_ROLE,
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

        return self.create_sql_function(
            "manage_record_audit_columns",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
            db_function=True,
        )


class InsertPermission(SQLEmitter):

    @computed_field
    def insert_permissions(self) -> str:
        function_string = (
            SQL(
                """
            BEGIN
                /*
                Function to create a new Permission record when a new MetaType is inserted.
                Records are created for each meta_type with each of the following permissions:
                    SELECT, INSERT, UPDATE, DELETE
                Deleted automatically by the DB via the FKDefinition Constraints ondelete when a meta_type is deleted.
                */
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'SELECT'::{schema_name}.sqloperation);
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'INSERT'::{schema_name}.sqloperation);
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'UPDATE'::{schema_name}.sqloperation);
                INSERT INTO permission(meta_type_id, operation)
                    VALUES (NEW.id, 'DELETE'::{schema_name}.sqloperation);
                RETURN NEW;
            END;
            """
            )
            .format(schema_name=DB_SCHEMA)
            .as_string()
        )

        return self.create_sql_function(
            "insert_permissions",
            function_string,
            timing="AFTER",
            operation="INSERT",
            include_trigger=True,
            db_function=True,
        )


class ValidateGroupInsert(SQLEmitter):

    @computed_field
    def validate_group_insert(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                group_count INT4;
                tenanttype tenanttype;
            BEGIN
                SELECT tenant_type INTO tenanttype
                FROM {schema_name}.tenant
                WHERE id = NEW.tenant_id;

                SELECT COUNT(*) INTO group_count
                FROM {schema_name}.group
                WHERE tenant_id = NEW.tenant_id;

                IF NOT {ENFORCE_MAX_GROUPS} THEN
                    RETURN NEW;
                END IF;

                IF tenanttype = 'INDIVIDUAL' AND
                    {MAX_INDIVIDUAL_GROUPS} > 0 AND
                    group_count >= {MAX_INDIVIDUAL_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                IF
                    tenanttype = 'BUSINESS' AND
                    {MAX_BUSINESS_GROUPS} > 0 AND
                    group_count >= {MAX_BUSINESS_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                IF
                    tenanttype = 'CORPORATE' AND
                    {MAX_CORPORATE_GROUPS} > 0 AND
                    group_count >= {MAX_CORPORATE_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                IF
                    tenanttype = 'ENTERPRISE' AND
                    {MAX_ENTERPRISE_GROUPS} > 0 AND
                    group_count >= {MAX_ENTERPRISE_GROUPS} THEN
                        RAISE EXCEPTION 'Group Count Exceeded';
                END IF;
                RETURN NEW;
            END;
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                ENFORCE_MAX_GROUPS=settings.ENFORCE_MAX_GROUPS,
                MAX_INDIVIDUAL_GROUPS=settings.MAX_INDIVIDUAL_GROUPS,
                MAX_BUSINESS_GROUPS=settings.MAX_BUSINESS_GROUPS,
                MAX_CORPORATE_GROUPS=settings.MAX_CORPORATE_GROUPS,
                MAX_ENTERPRISE_GROUPS=settings.MAX_ENTERPRISE_GROUPS,
            )
            .as_string()
        )

        return self.create_sql_function(
            "validate_group_insert",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )


class InsertGroupForTenant(SQLEmitter):
    @computed_field
    def insert_group_for_tenant(self) -> str:
        return (
            SQL(
                """
                SET ROLE {admin_role};
                CREATE OR REPLACE FUNCTION {schema_name}.insert_group_for_tenant()
                RETURNS TRIGGER
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    SET ROLE {admin_role};
                    INSERT INTO {schema_name}.group(tenant_id, name) VALUES (NEW.id, NEW.name);
                    RETURN NEW;
                END;
                $$;

                CREATE OR REPLACE TRIGGER insert_group_for_tenant_trigger
                -- The trigger to call the function
                AFTER INSERT ON tenant
                FOR EACH ROW
                EXECUTE FUNCTION {schema_name}.insert_group_for_tenant();
                """
            )
            .format(
                schema_name=DB_SCHEMA,
                admin_role=ADMIN_ROLE,
            )
            .as_string()
        )


class DefaultGroupTenant(SQLEmitter):
    @computed_field
    def insert_default_group_column(self) -> str:
        function_string = SQL(
            """
            DECLARE
                tenant_id VARCHAR(26) := current_setting('rls_var.tenant_id', true);
            BEGIN
                IF tenant_id IS NULL THEN
                    RAISE EXCEPTION 'tenant_id is NULL';
                END IF;

                NEW.tenant_id = tenant_id;

                RETURN NEW;
            END;
            """
        ).as_string()
        return self.create_sql_function(
            "insert_default_group_column",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=False,
        )


class UserRecordUserAuditFunction(SQLEmitter):
    @computed_field
    def manage_user_user_audit_columns(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                user_id VARCHAR(26) := current_setting('rls_var.user_id', TRUE);
            BEGIN
                /*
                Function used to insert a record into the meta_record table, when a record is inserted
                into a table that has a PK that is a FKDefinition to the meta_record table.
                Set as a trigger on the table, so that the meta_record record is created when the
                record is created.

                Has particular logic to handle the case where the first user is created, as
                the user_id is not yet set in the rls_vars.
                */

                SET ROLE {writer_role};
                IF user_id IS NOT NULL AND
                    NOT EXISTS (SELECT id FROM {schema_name}.user WHERE id = user_id) THEN
                        RAISE EXCEPTION 'user_id in rls_vars is not a valid user';
                END IF;
                IF user_id IS NULL AND
                    EXISTS (SELECT id FROM {schema_name}.user) THEN
                        IF TG_OP = 'UPDATE' THEN
                            IF NOT EXISTS (SELECT id FROM {schema_name}.user WHERE id = OLD.id) THEN
                                RAISE EXCEPTION 'No user def ined in rls_vars and this is not the first user being updated';
                            ELSE
                                user_id := OLD.id;
                            END IF;
                        ELSE
                            RAISE EXCEPTION 'No user def ined in rls_vars and this is not the first user created';
                        END IF;
                END IF;

                IF TG_OP = 'INSERT' THEN
                    IF user_id IS NULL THEN
                        user_id := NEW.id;
                    END IF;
                    NEW.created_by_id = user_id;
                    NEW.modified_by_id = user_id;
                ELSIF TG_OP = 'UPDATE' THEN
                    NEW.modified_by_id = user_id;
                ELSIF TG_OP = 'DELETE' THEN
                    NEW.deleted_by_id = user_id;
                END IF;

                RETURN NEW;
            END;
            """
            )
            .format(
                writer_role=WRITER_ROLE,
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

        return self.create_sql_function(
            "manage_audit_columns",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
            db_function=False,
        )
