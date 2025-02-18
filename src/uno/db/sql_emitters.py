# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional
from abc import ABC, abstractmethod

from psycopg.sql import SQL, Identifier, Literal

from dataclasses import dataclass

from uno.config import settings

db_schema = Identifier(settings.DB_SCHEMA)


# SQL Literals
LIT_ADMIN_ROLE = Literal(f"{settings.DB_NAME}_admin")
LIT_WRITER_ROLE = Literal(f"{settings.DB_NAME}_writer")
LIT_READER_ROLE = Literal(f"{settings.DB_NAME}_reader")
LIT_LOGIN_ROLE = Literal(f"{settings.DB_NAME}_login")
LIT_BASE_ROLE = Literal(f"{settings.DB_NAME}_base_role")

# SQL Identifiers
ADMIN_ROLE = SQL(f"{settings.DB_NAME}_admin")
WRITER_ROLE = SQL(f"{settings.DB_NAME}_writer")
READER_ROLE = SQL(f"{settings.DB_NAME}_reader")
LOGIN_ROLE = SQL(f"{settings.DB_NAME}_login")
BASE_ROLE = SQL(f"{settings.DB_NAME}_base_role")
DB_NAME = SQL(settings.DB_NAME)
DB_SCHEMA = Identifier(settings.DB_SCHEMA)


@dataclass
class SQLEmitter(ABC):
    table_name: str | None = None
    timing: Optional[str] = "AFTER"

    @abstractmethod
    def emit_sql(self, table_name: str) -> str:
        raise NotImplementedError

    def create_sql_trigger(
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
            else f"{settings.DB_SCHEMA}.{self.table_name}_"
        )
        return (
            SQL(
                """
            CREATE OR REPLACE TRIGGER {table_name}_{function_name}_trigger
                {timing} {operation}
                ON {db_schema}.{table_name}
                FOR EACH {for_each}
                EXECUTE FUNCTION {trigger_scope}{function_name}();
            """
            )
            .format(
                table_name=SQL(self.table_name),
                function_name=SQL(function_name),
                timing=SQL(timing),
                operation=SQL(operation),
                for_each=SQL(for_each),
                trigger_scope=SQL(trigger_scope),
                db_schema=DB_SCHEMA,
            )
            .as_string()
        )

    def create_sql_function(
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
            else f"{settings.DB_SCHEMA}.{self.table_name}_{function_name}"
        )
        fnct_string = (
            SQL(
                """
            SET ROLE {admin};
            CREATE OR REPLACE FUNCTION {full_function_name}({function_args})
            RETURNS {return_type}
            LANGUAGE plpgsql
            {volatile}
            {security_definer}
            AS $$
            {function_string}
            $$;
            """
            )
            .format(
                admin=ADMIN_ROLE,
                full_function_name=SQL(full_function_name),
                function_args=SQL(function_args),
                return_type=SQL(return_type),
                volatile=SQL(volatile),
                security_definer=SQL(security_definer),
                function_string=SQL(function_string),
            )
            .as_string()
        )

        if not include_trigger:
            return fnct_string
        trggr_string = self.create_sql_trigger(
            function_name,
            timing=timing,
            operation=operation,
            for_each=for_each,
            db_function=db_function,
        )
        return SQL(
            "{fnct_string}\n{trggr_string}".format(
                fnct_string=fnct_string, trggr_string=trggr_string
            )
        ).as_string()


@dataclass
class AlterGrantSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return (
            SQL(
                """
            SET ROLE {admin};
            -- Congigure table ownership and privileges
            ALTER TABLE {db_schema}.{table_name} OWNER TO {admin};
            GRANT SELECT ON {db_schema}.{table_name} TO
                {reader},
                {writer};
            GRANT INSERT, UPDATE, DELETE ON {db_schema}.{table_name} TO
                {writer};
            """
            )
            .format(
                admin=ADMIN_ROLE,
                reader=READER_ROLE,
                writer=WRITER_ROLE,
                db_schema=DB_SCHEMA,
                table_name=SQL(self.table_name),
            )
            .as_string()
        )


@dataclass
class RecordVersionAuditSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return (
            SQL(
                """
            -- Enable auditing for the table
            SELECT audit.enable_tracking('{db_schema}.{table_name}'::regclass);
            """
            )
            .format(db_schema=DB_SCHEMA, table_name=SQL(self.table_name))
            .as_string()
        )


@dataclass
class HistoryTableAuditSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return f"{self.emit_create_history_table_sql}\n{self.emit_create_history_function_and_trigger_sql}"

    def emit_create_history_table_sql(self) -> str:
        return (
            SQL(
                """
            SET ROLE {db_name}_admin;
            CREATE TABLE audit.{db_schema}_{table_name}
            AS (SELECT * FROM {db_schema}.{table_name})
            WITH NO DATA;

            ALTER TABLE audit.{db_schema}_{table_name}
            ADD COLUMN pk INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY;

            CREATE INDEX {db_schema}_{table_name}_pk_idx
            ON audit.{db_schema}_{table_name} (pk);

            CREATE INDEX {db_schema}_{table_name}_id_modified_at_idx
            ON audit.{db_schema}_{table_name} (id, modified_at);
            """
            )
            .format(
                db_name=SQL(settings.DB_NAME),
                db_schema=SQL(settings.DB_SCHEMA),
                table_name=SQL(self.table_name),
            )
            .as_string()
        )

    def emit_create_history_function_and_trigger_sql(self) -> str:
        function_string = SQL(
            """
            INSERT INTO audit.{db_schema}_{table_name}
            SELECT *
            FROM {db_schema}.{table_name}
            WHERE id = NEW.id;
            RETURN NEW;
            """
        ).format(db_schema=SQL(settings.DB_SCHEMA), table_name=SQL(self.table_name))

        return self.create_sql_function(
            "history",
            function_string,
            timing="AFTER",
            operation="INSERT OR UPDATE",
            include_trigger=True,
            db_function=False,
            security_definer="SECURITY DEFINER",
        )


@dataclass
class InsertObjectTypeRecordSQL(SQLEmitter):
    all_tables: bool = True
    timing: str = "AFTER"

    def emit_sql(self) -> str:
        return (
            SQL(
                """
            -- Create the objecttype record
            SET ROLE {db_role};
            INSERT INTO {schema}.objecttype (name)
            VALUES ({table_name});
            """
            )
            .format(
                schema=DB_SCHEMA,
                db_role=Identifier(f"{settings.DB_NAME}_writer"),
                table_name=Literal(self.table_name),
            )
            .as_string()
        )


@dataclass
class InsertRelatedObjectFunctionSQL(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                relatedobject_id VARCHAR(26) := {db_schema}.generate_ulid();
                -- user_id VARCHAR(26) := current_setting('rls_var.user_id', true);
            BEGIN
                /*
                Function used to insert a record into the relatedobject table, when a record is inserted
                into a table that has a PK that is a FKDefinition to the relatedobject table.
                Set as a trigger on the table, so that the relatedobject record is created when the
                record is created.
                */

                SET ROLE {db_role};
                INSERT INTO {db_schema}.relatedobject (id, objecttype_name)
                    VALUES (relatedobject_id, {objecttype_name});
                NEW.id = relatedobject_id;
                RETURN NEW;
            END;
            """
            )
            .format(
                db_schema=Identifier(settings.DB_SCHEMA),
                db_role=Identifier(f"{settings.DB_NAME}_writer"),
                objecttype_name=Literal(self.table_name),
            )
            .as_string()
        )

        return self.create_sql_function(
            "insert_relatedobject",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=True,
        )


@dataclass
class InsertRelatedObjectTriggerSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return self.create_sql_trigger(
            "insert_relatedobject",
            timing="BEFORE",
            operation="INSERT",
            for_each="ROW",
            db_function=True,
        )


@dataclass
class InsertPermissionSQL(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = (
            SQL(
                """
            BEGIN
                /*
                Function to create a new Permission record when a new ObjectType is inserted.
                Records are created for each objecttype with each of the following permissions:
                    SELECT, INSERT, UPDATE, DELETE
                Deleted automatically by the DB via the FKDefinition Constraints ondelete when a objecttype is deleted.
                */
                INSERT INTO {db_schema}.permission(objecttype_name, operation)
                    VALUES (NEW.name, 'SELECT'::uno.sqloperation);
                INSERT INTO {db_schema}.permission(objecttype_name, operation)
                    VALUES (NEW.name, 'INSERT'::uno.sqloperation);
                INSERT INTO {db_schema}.permission(objecttype_name, operation)
                    VALUES (NEW.name, 'UPDATE'::uno.sqloperation);
                INSERT INTO {db_schema}.permission(objecttype_name, operation)
                    VALUES (NEW.name, 'DELETE'::uno.sqloperation);
                RETURN NEW;
            END;
            """
            )
            .format(db_schema=DB_SCHEMA)
            .as_string()
        )

        return self.create_sql_function(
            "create_permissions",
            function_string,
            timing="AFTER",
            operation="INSERT",
            include_trigger=True,
            db_function=True,
        )


class GenericRecordAuditUserSQL(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = (
            SQL(
                """
            DECLARE
                user_id TEXT := current_setting('rls_var.user_id', true);
                valid_user_id VARCHAR(26);
            BEGIN
                /* 
                Function used to set the owned_by_id and modified_by_id fields
                of a table to the user_id of the user making the change. 
                */

                SELECT current_setting('rls_var.user_id', true) INTO user_id;

                IF user_id IS NULL THEN
                    RAISE EXCEPTION 'user_id is NULL';
                END IF;

                IF user_id = '' THEN
                    RAISE EXCEPTION 'user_id is an empty string';
                END IF;

                SELECT id INTO valid_user_id FROM {db_schema}.user WHERE id = user_id;
                IF NOT valid_user_id THEN
                    RAISE EXCEPTION 'user_id in rls_vars is not a valid user';
                END IF;

                -- NEW.modified_at := NOW();
                NEW.modified_by_id = user_id;

                IF TG_OP = 'INSERT' THEN
                    -- NEW.created_at := NOW();
                    NEW.owned_by_id = user_id;
                END IF;

                IF TG_OP = 'DELETE' THEN
                    -- NEW.deleted_at = NOW();
                    NEW.deleted_by_id = user_id;
                END IF;

                RETURN NEW;
            END;
            """
            )
            .format(db_schema=db_schema)
            .as_string()
        )

        return self.create_sql_function(
            "general_record_audit_users",
            function_string,
            timing="BEFORE",
            operation="INSERT OR UPDATE OR DELETE",
            include_trigger=True,
        )
