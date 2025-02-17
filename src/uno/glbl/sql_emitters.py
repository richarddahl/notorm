# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from pydantic.dataclasses import dataclass

from uno.db.sql_emitters import SQLEmitter

from uno.config import settings


@dataclass
class InsertObjectTypeRecordSQL(SQLEmitter):
    all_tables: bool = True
    timing: str = "AFTER"

    def emit_sql(self) -> str:
        return textwrap.dedent(
            f"""
            -- Create the object_type record
            SET ROLE {settings.DB_NAME}_writer;
            INSERT INTO uno.object_type (schema_name, table_name)
            VALUES ('{self.schema}', '{self.table_name}');
            """
        )


@dataclass
class InsertULIDSQL(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = textwrap.dedent(
            f"""
            -- SET ROLE {settings.DB_NAME}_writer;
            DECLARE
                related_object_id VARCHAR(26) := uno.generate_ulid();
            BEGIN
                NEW.id = related_object_id;
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
        function_string = textwrap.dedent(
            f"""
            DECLARE
                object_type_id int;
                related_object_id VARCHAR(26) := uno.generate_ulid();
            BEGIN
                /*
                Function used to insert a record into the related_object table, when a record is inserted
                into a table that has a PK that is a FKDefinition to the related_object table.
                Set as a trigger on the table, so that the related_object record is created when the
                record is created.

                NOT USING sqlalchemy server_default, because triggers have access to TG_TABLE_SCHEMA
                and TG_TABLE_NAME making it simpler to get the object_type_id.
                */
                SELECT id
                    FROM uno.object_type
                    WHERE schema_name = TG_TABLE_SCHEMA AND table_name = TG_TABLE_NAME
                    INTO object_type_id;

                SET ROLE {settings.DB_NAME}_writer;
                INSERT INTO uno.related_object (id, object_type_id)
                    VALUES (related_object_id, object_type_id);
                NEW.id = related_object_id;
                RETURN NEW;
            END;
            """
        )

        return self.create_sql_function(
            "insert_related_object",
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
            "insert_related_object",
            timing="BEFORE",
            operation="INSERT",
            for_each="ROW",
            db_function=True,
        )


@dataclass
class InsertPermissionSQL(SQLEmitter):
    def emit_sql(self) -> str:
        function_string = """
            BEGIN
                /*
                Function to create a new Permission record when a new ObjectType is inserted.
                Records are created for each object_type with each of the following permissions:
                    SELECT, INSERT, UPDATE, DELETE
                Deleted automatically by the DB via the FKDefinition Constraints ondelete when a object_type is deleted.
                */
                INSERT INTO uno.permission(object_type_id, operation)
                    VALUES (NEW.id, 'SELECT'::uno.sqloperation);
                INSERT INTO uno.permission(object_type_id, operation)
                    VALUES (NEW.id, 'INSERT'::uno.sqloperation);
                INSERT INTO uno.permission(object_type_id, operation)
                    VALUES (NEW.id, 'UPDATE'::uno.sqloperation);
                INSERT INTO uno.permission(object_type_id, operation)
                    VALUES (NEW.id, 'DELETE'::uno.sqloperation);
                RETURN NEW;
            END;
            """

        return self.create_sql_function(
            "create_permissions",
            function_string,
            timing="AFTER",
            operation="INSERT",
            include_trigger=True,
            db_function=True,
        )
