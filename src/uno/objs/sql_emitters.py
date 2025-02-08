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
                object_type_id VARCHAR(26);
                related_object_id VARCHAR(26) := uno.generate_ulid();
            BEGIN
                /*
                Function used to insert a record into the related_object table, when a record is inserted
                into a table that has a PK that is a FKDefinition to the related_object table.
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
