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
                db_object_id VARCHAR(26) := uno.generate_ulid();
            BEGIN
                NEW.id = db_object_id;
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
                db_object_id VARCHAR(26) := uno.generate_ulid();
            BEGIN
                /*
                Function used to insert a record into the db_object table, when a record is inserted
                into a table that has a PK that is a FKDefinition to the db_object table.
                Set as a trigger on the table, so that the db_object record is created when the
                record is created.

                NOT USING sqlalchemy server_default, because triggers have access to TG_TABLE_SCHEMA
                and TG_TABLE_NAME making it simpler to get the object_type_id.
                */
                SELECT id
                    FROM uno.object_type
                    WHERE schema_name = TG_TABLE_SCHEMA AND table_name = TG_TABLE_NAME
                    INTO object_type_id;

                SET ROLE {settings.DB_NAME}_writer;
                INSERT INTO uno.db_object (id, object_type_id)
                    VALUES (db_object_id, object_type_id);
                NEW.id = db_object_id;
                RETURN NEW;
            END;
            """
        )

        return self.create_sql_function(
            "insert_db_object",
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
            "insert_db_object",
            timing="BEFORE",
            operation="INSERT",
            for_each="ROW",
            db_function=True,
        )
