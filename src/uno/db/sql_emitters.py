# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import Optional
from abc import ABC, abstractmethod

from psycopg.sql import SQL, Identifier, Literal

from dataclasses import dataclass

from uno.config import settings


@dataclass
class SQLEmitter(ABC):
    table_name: Optional[str] = None
    schema: Optional[str] = settings.DB_SCHEMA
    timing: Optional[str] = "AFTER"

    @abstractmethod
    def emit_sql(self) -> str:
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
            f"{self.schema}." if db_function else f"{self.schema}.{self.table_name}_"
        )
        # return SQL(
        #    """
        #    CREATE OR REPLACE TRIGGER {table_name}_{function_name}_trigger
        #        {timing} {operation}
        #        ON {schema}.{table_name}
        #        FOR EACH {for_each}
        #        EXECUTE FUNCTION {trigger_scope}{function_name}();
        #    """
        # ).format(
        #    table_name=SQL.Identifier(self.table_name),
        #    function_name=SQL.Identifier(function_name),
        #    timing=SQL.Literal(timing),
        #    operation=SQL.Literal(operation),
        #    for_each=SQL.Literal(for_each),
        #    trigger_scope=SQL.Identifier(trigger_scope),
        #    schema=SQL.Identifier(self.schema),
        # )

        return textwrap.dedent(
            f"""
            CREATE OR REPLACE TRIGGER {self.table_name}_{function_name}_trigger
                {timing} {operation}
                ON {self.schema}.{self.table_name}
                FOR EACH {for_each}
                EXECUTE FUNCTION {trigger_scope}{function_name}();
            """
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
            f"{self.schema}.{function_name}"
            if db_function
            else f"{self.schema}.{self.table_name}_{function_name}"
        )
        fnct_string = textwrap.dedent(
            f"""
            SET ROLE {settings.DB_NAME}_admin;
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
        if not include_trigger:
            return fnct_string
        trggr_string = self.create_sql_trigger(
            function_name,
            timing=timing,
            operation=operation,
            for_each=for_each,
            db_function=db_function,
        )
        return f"{textwrap.dedent(fnct_string)}\n{textwrap.dedent(trggr_string)}"


@dataclass
class AlterGrantSQL(SQLEmitter):
    all_tables: bool = True
    timing: str = "AFTER"

    def emit_sql(self) -> str:
        return textwrap.dedent(
            f"""
            SET ROLE {settings.DB_NAME}_admin;
            -- Congigure table ownership and privileges
            ALTER TABLE {self.schema}.{self.table_name} OWNER TO {settings.DB_NAME}_admin;
            GRANT SELECT ON {self.schema}.{self.table_name} TO
                {settings.DB_NAME}_reader,
                {settings.DB_NAME}_writer;
            GRANT INSERT, UPDATE, DELETE ON {self.schema}.{self.table_name} TO
                {settings.DB_NAME}_writer;
            """
        )


@dataclass
class RecordVersionAuditSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return textwrap.dedent(
            f"""
            -- Enable auditing for the table
            SELECT audit.enable_tracking('{self.schema}.{self.table_name}'::regclass);
            """
        )


@dataclass
class HistoryTableAuditSQL(SQLEmitter):
    def emit_sql(self) -> str:
        return f"{self.emit_create_history_table_sql}\n{self.emit_create_history_function_and_trigger_sql}"

    def emit_create_history_table_sql(self) -> str:
        return textwrap.dedent(
            f"""
            SET ROLE {settings.DB_NAME}_admin;
            CREATE TABLE audit.{self.schema}_{self.table_name}
            AS (SELECT * FROM {self.schema}.{self.table_name})
            WITH NO DATA;

            ALTER TABLE audit.{self.schema}_{self.table_name}
            ADD COLUMN pk INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY;

            CREATE INDEX {self.schema}_{self.table_name}_pk_idx
            ON audit.{self.schema}_{self.table_name} (pk);

            CREATE INDEX {self.schema}_{self.table_name}_id_modified_at_idx
            ON audit.{self.schema}_{self.table_name} (id, modified_at);
            """
        )

    def emit_create_history_function_and_trigger_sql(self) -> str:
        function_string = f"""
            INSERT INTO audit.{self.schema}_{self.table_name}
            SELECT *
            FROM {self.schema}.{self.table_name}
            WHERE id = NEW.id;
            RETURN NEW;
            """

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
                schema=Identifier(self.schema),
                db_role=Identifier(f"{settings.DB_NAME}_writer"),
                table_name=Literal(self.table_name),
            )
            .as_string()
        )


@dataclass
class InsertULIDSQL(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = textwrap.dedent(
            f"""
            -- SET ROLE {settings.DB_NAME}_writer;
            DECLARE
                relatedobject_id VARCHAR(26) := uno.generate_ulid();
            BEGIN
                NEW.id = relatedobject_id;
                RETURN NEW;
            END;
            """
        )

        return self.create_sql_function(
            "insert_ulid",
            function_string,
            timing="BEFORE",
            operation="INSERT",
            include_trigger=True,
            db_function=True,
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
        function_string = SQL(
            """
            BEGIN
                /*
                Function to create a new Permission record when a new ObjectType is inserted.
                Records are created for each objecttype with each of the following permissions:
                    SELECT, INSERT, UPDATE, DELETE
                Deleted automatically by the DB via the FKDefinition Constraints ondelete when a objecttype is deleted.
                */
                INSERT INTO uno.permission(objecttype_name, operation)
                    VALUES (NEW.name, 'SELECT'::uno.sqloperation);
                INSERT INTO uno.permission(objecttype_name, operation)
                    VALUES (NEW.name, 'INSERT'::uno.sqloperation);
                INSERT INTO uno.permission(objecttype_name, operation)
                    VALUES (NEW.name, 'UPDATE'::uno.sqloperation);
                INSERT INTO uno.permission(objecttype_name, operation)
                    VALUES (NEW.name, 'DELETE'::uno.sqloperation);
                RETURN NEW;
            END;
            """
        ).as_string()

        return self.create_sql_function(
            "create_permissions",
            function_string,
            timing="AFTER",
            operation="INSERT",
            include_trigger=True,
            db_function=True,
        )
