# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import Optional, ClassVar

from psycopg import sql
from pydantic import BaseModel, ConfigDict, computed_field
from sqlalchemy.sql import text
from sqlalchemy.engine.base import Connection
from sqlalchemy import Table

from uno.errors import UnoError
from uno.config import settings

# sql.SQL sql.Literal and Identifier objects are used to create sql.SQL strings
# that are passed to the database for execution.

# sql.SQL Literals
# These are Necessary for searchiing pg_roles
LIT_ADMIN_ROLE = sql.Literal(f"{settings.DB_NAME}_admin")
LIT_WRITER_ROLE = sql.Literal(f"{settings.DB_NAME}_writer")
LIT_READER_ROLE = sql.Literal(f"{settings.DB_NAME}_reader")
LIT_LOGIN_ROLE = sql.Literal(f"{settings.DB_NAME}_login")
LIT_BASE_ROLE = sql.Literal(f"{settings.DB_NAME}_base_role")

# sql.SQL
ADMIN_ROLE = sql.SQL(f"{settings.DB_NAME}_admin")
WRITER_ROLE = sql.SQL(f"{settings.DB_NAME}_writer")
READER_ROLE = sql.SQL(f"{settings.DB_NAME}_reader")
LOGIN_ROLE = sql.SQL(f"{settings.DB_NAME}_login")
BASE_ROLE = sql.SQL(f"{settings.DB_NAME}_base_role")
DB_NAME = sql.SQL(settings.DB_NAME)
DB_SCHEMA = sql.SQL(settings.DB_SCHEMA)


class SQLEmitter(BaseModel):
    exclude_fields: ClassVar[list[str]] = ["table"]
    table: Optional[Table] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def emit_sql(self, connection: Connection) -> None:
        for statement_name, sql_statement in self.model_dump(
            exclude=self.exclude_fields
        ).items():
            connection.execute(text(sql_statement))

    def createsqltrigger(
        self,
        function_name: str,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        db_function: bool = True,
    ) -> str:

        trigger_scope = (
            f"{settings.DB_SCHEMA}."
            if db_function
            else f"{settings.DB_SCHEMA}.{self.table.name}_"
        )
        trigger_prefix = self.table.name
        return textwrap.dedent(
            sql.SQL(
                """
            CREATE OR REPLACE TRIGGER {trigger_prefix}_{function_name}_trigger
                {timing} {operation}
                ON {schema_name}.{table_name}
                FOR EACH {for_each}
                EXECUTE FUNCTION {trigger_scope}{function_name}();
            """
            )
            .format(
                table_name=sql.SQL(self.table.name),
                trigger_prefix=sql.SQL(trigger_prefix),
                function_name=sql.SQL(function_name),
                timing=sql.SQL(timing),
                operation=sql.SQL(operation),
                for_each=sql.SQL(for_each),
                trigger_scope=sql.SQL(trigger_scope),
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

    def createsqlfunction(
        self,
        function_name: str,
        function_string: str,
        function_args: str = "",
        db_function: bool = True,
        return_type: str = "TRIGGER",
        volatile: str = "VOLATILE",
        include_trigger: bool = False,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        security_definer: str = "",
    ) -> str:

        if function_args and include_trigger is True:
            raise ValueError(
                "Function arguments cannot be used when creating a trigger function."
            )
        full_function_name = (
            f"{settings.DB_SCHEMA}.{function_name}"
            if db_function
            else f"{self.table.name}_{function_name}"
        )
        ADMIN_ROLE = sql.SQL(f"{settings.DB_NAME}_admin")
        fnct_string = textwrap.dedent(
            sql.SQL(
                """
            SET ROLE {admin_role};
            CREATE OR REPLACE FUNCTION {full_function_name}({function_args})
            RETURNS {return_type}
            LANGUAGE plpgsql
            {volatile}
            {security_definer}
            AS $fnct$ 
            {function_string}
            $fnct$;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                full_function_name=sql.SQL(full_function_name),
                function_args=sql.SQL(function_args),
                return_type=sql.SQL(return_type),
                volatile=sql.SQL(volatile),
                security_definer=sql.SQL(security_definer),
                function_string=sql.SQL(function_string),
            )
            .as_string()
        )

        if not include_trigger:
            return textwrap.dedent(fnct_string)
        trggr_string = self.createsqltrigger(
            function_name,
            timing=timing,
            operation=operation,
            for_each=for_each,
            db_function=db_function,
        )
        return textwrap.dedent(
            sql.SQL(
                "{fnct_string}\n{trggr_string}".format(
                    fnct_string=fnct_string, trggr_string=trggr_string
                )
            ).as_string()
        )


## DB sql.SQL


class DropDatabaseAndRoles(SQLEmitter):
    @computed_field
    def drop_database(self) -> str:
        return (
            sql.SQL(
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
            sql.SQL(
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


class InsertMetaRecordFunction(SQLEmitter):
    @computed_field
    def insert_meta_record_function(self) -> str:
        function_string = (
            sql.SQL(
                """
            DECLARE
                meta_id VARCHAR(26) := {schema_name}.generate_ulid();
            BEGIN
                /*
                Function used to insert a record into the meta_record table, when a 
                polymorphic record is inserted.
                */
                SET ROLE {writer_role};

                INSERT INTO {schema_name}.meta_record (id, meta_type_id) VALUES (meta_id, TG_TABLE_NAME);
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

        return self.createsqlfunction(
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
        return self.createsqltrigger(
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
            sql.SQL(
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

        return self.createsqlfunction(
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
            sql.SQL(
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

        return self.createsqlfunction(
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
            sql.SQL(
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

        return self.createsqlfunction(
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
            sql.SQL(
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

        return self.createsqlfunction(
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
            sql.SQL(
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
        function_string = sql.SQL(
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
        return self.createsqlfunction(
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
            sql.SQL(
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

        return self.createsqlfunction(
            "manage_audit_columns",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
            db_function=False,
        )


## TABLE sql.SQL


class AlterGrants(SQLEmitter):

    @computed_field
    def alter_grants(self) -> str:
        return (
            sql.SQL(
                """
            SET ROLE {admin_role};
            -- Congigure table ownership and privileges
            ALTER TABLE {schema_name}.{table_name} OWNER TO {admin_role};
            REVOKE ALL ON {schema_name}.{table_name} FROM PUBLIC, {writer_role}, {reader_role};
            GRANT SELECT ON {schema_name}.{table_name} TO
                {reader_role},
                {writer_role};
            GRANT ALL ON {schema_name}.{table_name} TO
                {writer_role};
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                reader_role=READER_ROLE,
                writer_role=WRITER_ROLE,
                table_name=sql.SQL(self.table.name),
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class InsertMetaType(SQLEmitter):

    @computed_field
    def insert_meta_type(self) -> str:
        return (
            sql.SQL(
                """
            -- Create the meta_type record
            SET ROLE {writer_role};
            INSERT INTO {schema_name}.meta_type (id)
            VALUES ({table_name})
            ON CONFLICT DO NOTHING;
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                writer_role=WRITER_ROLE,
                table_name=sql.Literal(self.table.name),
            )
            .as_string()
        )


class RecordVersionAudit(SQLEmitter):

    @computed_field
    def enable_version_audit(self) -> str:
        return (
            sql.SQL(
                """
            -- Enable auditing for the table
            SELECT audit.enable_tracking('{table_name}'::regclass);
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                table_name=sql.SQL(self.table.name),
            )
            .as_string()
        )


class EnableHistoricalAudit(SQLEmitter):

    @computed_field
    def create_history_table(self) -> str:
        return (
            sql.SQL(
                """
            SET ROLE {db_name}_admin;
            CREATE TABLE audit.{schema_name}_{table_name}
            AS (
                SELECT 
                    t1.*,
                    t2.meta_type_id
                FROM {schema_name}.{table_name} t1
                INNER JOIN meta_record t2
                ON t1.id = t2.id
            )
            WITH NO DATA;

            ALTER TABLE audit.{schema_name}_{table_name}
            ADD COLUMN pk INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY;

            CREATE INDEX {schema_name}_{table_name}_pk_idx
            ON audit.{schema_name}_{table_name} (pk);

            CREATE INDEX {schema_name}_{table_name}_id_modified_at_idx
            ON audit.{schema_name}_{table_name} (id, modified_at);
            """
            )
            .format(
                db_name=DB_NAME,
                schema_name=DB_SCHEMA,
                table_name=sql.SQL(self.table.name),
            )
            .as_string()
        )

    @computed_field
    def insert_history_record(self) -> str:
        function_string = (
            sql.SQL(
                """
            BEGIN
                INSERT INTO audit.{schema_name}_{table_name}
                SELECT *
                FROM {schema_name}.{table_name}
                WHERE id = NEW.id;
                RETURN NEW;
            END;
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                table_name=sql.SQL(self.table.name),
            )
            .as_string()
        )

        return self.createsqlfunction(
            "history",
            function_string,
            timing="AFTER",
            operation="INSERT OR UPDATE",
            include_trigger=True,
            db_function=False,
            security_definer="SECURITY DEFINER",
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


class MergeOrCreate(SQLEmitter):

    @computed_field
    def create_merge_or_create_function(self) -> str:
        return textwrap.dedent(
            sql.SQL(
                """
                CREATE OR REPLACE FUNCTION merge_or_insert(
                    table_name TEXT, 
                    data JSONB, 
                    pk_fields TEXT[], 
                    uq_field_sets JSONB[]
                ) RETURNS TABLE (result JSONB) AS $$
                DECLARE
                    columns TEXT;
                    values TEXT;
                    match_conditions TEXT;
                    update_set TEXT;
                    sql TEXT;
                    pk_match_conditions TEXT;
                    uq_match_conditions TEXT;
                BEGIN
                    -- Extract column names and values from the JSONB data
                    SELECT string_agg(key, ', ') INTO columns
                    FROM jsonb_object_keys(data);

                    SELECT string_agg(format('%%L AS %I', value, key), ', ') INTO values
                    FROM jsonb_each_text(data);

                    -- Generate the update set clause
                    SELECT string_agg(format('%I = EXCLUDED.%I', key, key), ', ') INTO update_set
                    FROM jsonb_object_keys(data);

                    -- Initialize match conditions
                    match_conditions := '';

                    -- Add primary key conditions
                    IF array_length(pk_fields, 1) > 0 THEN
                        SELECT string_agg(format('%I = EXCLUDED.%I', field, field), ' AND ') INTO pk_match_conditions
                        FROM unnest(pk_fields) AS field;

                        match_conditions := format('(%s)', pk_match_conditions);
                    END IF;

                    -- Add unique field sets conditions
                    IF jsonb_array_length(uq_field_sets) > 0 THEN
                        SELECT string_agg(
                            format('(%s)', string_agg(format('%I = EXCLUDED.%I', field, field), ' AND ')),
                            ' OR '
                        ) INTO uq_match_conditions
                        FROM jsonb_array_elements(uq_field_sets) AS uq_set, jsonb_array_elements_text(uq_set) AS field;

                        IF match_conditions <> '' THEN
                            match_conditions := match_conditions || ' OR ' || uq_match_conditions;
                        ELSE
                            match_conditions := uq_match_conditions;
                        END IF;
                    END IF;

                    -- Construct the MERGE statement with a RETURNING clause
                    sql := format(
                        'MERGE INTO %I AS target
                        USING (VALUES (%s)) AS source (%s)
                        ON %s
                        WHEN MATCHED THEN
                            UPDATE SET %s
                            RETURNING target.*
                        WHEN NOT MATCHED THEN
                            INSERT (%s) VALUES (%s)
                            RETURNING target.*',
                        table_name, values, columns, match_conditions, update_set, columns, columns
                    );

                    -- Execute the MERGE statement and return the results
                    RETURN QUERY EXECUTE sql;
                END;
                $$ LANGUAGE plpgsql;
            """
            )
            .format(schema_name=DB_SCHEMA)
            .as_string()
        )


class SQLConfig(BaseModel):
    registry: ClassVar[dict[str, type["SQLConfig"]]] = {}
    sql_emitters: ClassVar[dict[str, SQLEmitter]] = {}
    table: ClassVar[Optional[Table]] = None

    def __init_subclass__(cls, **kwargs) -> None:

        super().__init_subclass__(**kwargs)
        # Don't add the SQLConfig class itself to the registry
        if cls is SQLConfig:
            return
        # Add the subclass to the registry if it is not already there
        if cls.__name__ not in cls.registry:
            cls.registry.update({cls.__name__: cls})
        else:
            raise UnoError(
                f"SQLConfig class: {cls.__name__} already exists in the registry.",
                "DUPLICATE_SQLCONFIG",
            )

    # End of __init_subclass__

    @classmethod
    def emit_sql(cls, connection: Connection) -> None:
        for sql_emitter in cls.sql_emitters:
            sql_emitter(table=cls.table).emit_sql(connection)
