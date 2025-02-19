# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional
from abc import ABC, abstractmethod

from psycopg.sql import SQL, Identifier, Literal
from sqlalchemy import text
from sqlalchemy.engine import Engine

from dataclasses import dataclass

from uno.config import settings

# SQL Literal and Identifier objects are used to create SQL strings
# that are passed to the database for execution.

# SQL Literals
# These are Necessary for searchiing pg_roles
LIT_ADMIN_ROLE = Literal(f"{settings.DB_NAME}_admin")
LIT_WRITER_ROLE = Literal(f"{settings.DB_NAME}_writer")
LIT_READER_ROLE = Literal(f"{settings.DB_NAME}_reader")
LIT_LOGIN_ROLE = Literal(f"{settings.DB_NAME}_login")
LIT_BASE_ROLE = Literal(f"{settings.DB_NAME}_base_role")

# SQL
ADMIN_ROLE = SQL(f"{settings.DB_NAME}_admin")
WRITER_ROLE = SQL(f"{settings.DB_NAME}_writer")
READER_ROLE = SQL(f"{settings.DB_NAME}_reader")
LOGIN_ROLE = SQL(f"{settings.DB_NAME}_login")
BASE_ROLE = SQL(f"{settings.DB_NAME}_base_role")
DB_NAME = SQL(settings.DB_NAME)
DB_SCHEMA = SQL(settings.DB_SCHEMA)


@dataclass
class SQLEmitter(ABC):
    """SQL Emitter base class for creating PostgreSQL functions and triggers.

    This abstract base class provides methods to generate SQL for creating PostgreSQL
    functions and triggers. It handles proper SQL formatting and escaping.

    Attributes:
        table_name (str | None): The name of the database table to create triggers/functions for.
        timing (str | None): The timing of trigger execution ("BEFORE", "AFTER", etc).
            Defaults to "AFTER".

    Methods:
        emit_sql: Abstract method that must be implemented by subclasses to emit SQL.
        create_sql_trigger: Creates a PostgreSQL trigger SQL statement.
        create_sql_function: Creates a PostgreSQL function SQL statement with optional trigger.
    """

    table_name: str | None = None
    timing: Optional[str] = "AFTER"

    @abstractmethod
    def emit_sql(self, table_name: str, conn: Engine) -> str:
        """
        Emits an SQL statement for a given table.

        Args:
            table_name (str): The name of the table to generate SQL for.
            conn (Engine): SQLAlchemy Engine connection object.

        Returns:
            str: The generated SQL statement.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
        raise NotImplementedError

    def create_sql_trigger(
        self,
        function_name: str,
        timing: str = "BEFORE",
        operation: str = "UPDATE",
        for_each: str = "ROW",
        db_function: bool = True,
    ) -> str:
        """Creates a PostgreSQL trigger SQL statement.

        This method generates a SQL statement for creating or replacing a trigger in PostgreSQL.
        The trigger can be configured to execute before or after specified operations and can
        reference either a database function or a table-specific function.

        Args:
            function_name (str): Name of the function to be executed by the trigger
            timing (str, optional): When the trigger should fire ("BEFORE" or "AFTER"). Defaults to "BEFORE".
            operation (str, optional): Database operation that activates the trigger ("INSERT", "UPDATE", "DELETE"). Defaults to "UPDATE".
            for_each (str, optional): Whether to fire once per statement or row ("ROW" or "STATEMENT"). Defaults to "ROW".
            db_function (bool, optional): If True, function is in database schema. If False, function is table-specific. Defaults to True.

        Returns:
            str: Complete SQL statement for creating the trigger

        Example:
            >>> create_sql_trigger("update_timestamp", "BEFORE", "UPDATE")
            'CREATE OR REPLACE TRIGGER table_update_timestamp_trigger
             BEFORE UPDATE ON schema.table
             FOR EACH ROW
             EXECUTE FUNCTION schema.update_timestamp();'
        """
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
        """Creates a SQL function and optionally a corresponding trigger.

        This method generates SQL statements to create a PostgreSQL function and optionally
        a trigger that calls that function. The function can be either a standalone database
        function or associated with a specific table.

        Args:
            function_name (str): Name of the function to create
            function_string (str): The actual PL/pgSQL function body code
            function_args (str, optional): Function arguments declaration. Defaults to "".
            db_function (bool, optional): If True, creates standalone function. If False,
                prefixes function name with table name. Defaults to True.
            return_type (str, optional): SQL return type for the function. Defaults to "TRIGGER".
            volatile (str, optional): Function volatility (VOLATILE/STABLE/IMMUTABLE).
                Defaults to "VOLATILE".
            include_trigger (bool, optional): Whether to create a trigger for this function.
                Defaults to False.
            timing (str, optional): Trigger timing (BEFORE/AFTER). Defaults to "BEFORE".
            operation (str, optional): Trigger operation (INSERT/UPDATE/DELETE).
                Defaults to "UPDATE".
            for_each (str, optional): Trigger granularity (ROW/STATEMENT). Defaults to "ROW".
            security_definer (str, optional): SECURITY DEFINER clause if needed.
                Defaults to "".

        Returns:
            str: SQL statement(s) for creating the function and optional trigger

        Raises:
            ValueError: If both function_args and include_trigger are specified
        """

        if function_args and include_trigger is True:
            raise ValueError(
                "Function arguments cannot be used when creating a trigger function."
            )
        full_function_name = (
            f"{settings.DB_SCHEMA}.{function_name}"
            if db_function
            else f"{settings.DB_SCHEMA}.{self.table_name}_{function_name}"
        )
        ADMIN_ROLE = SQL(f"{settings.DB_NAME}_admin")
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
    """
    Emits SQL statements to alter table ownership and grant privileges.

    This class generates and executes SQL statements that:
    1. Sets the role to admin
    2. Changes table ownership to admin role
    3. Grants SELECT privileges to reader and writer roles
    4. Grants INSERT, UPDATE, DELETE privileges to writer role

    Where used:
    Base

    Args:
        table_name (str): Name of the table to alter grants for

    Example:
        ```
        alter_grants = AlterGrantSQL("my_table")
        alter_grants.emit_sql(engine)
        ```
    """

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
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
                    table_name=Identifier(self.table_name),
                )
                .as_string()
            )
        )


@dataclass
class RecordVersionAuditSQL(SQLEmitter):
    """Emits SQL to enable record version auditing for a specified table.

    This class prepares and executes SQL to enable audit tracking on a database table
    using the audit schema's enable_tracking function.

    Where used:
    RecordVersionAuditMixin

    Args:
        table_name (str): The name of the table to enable auditing for.

    Example:
        ```python
        emitter = RecordVersionAuditSQL("my_table")
        emitter.emit_sql(engine)
        ```

    Note:
        Requires audit schema and enable_tracking function to be previously set up in the database.
        Uses the global DB_SCHEMA constant for the schema name.
    """

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Enable auditing for the table
            SELECT audit.enable_tracking('{db_schema}.{table_name}'::regclass);
            """
                )
                .format(
                    db_schema=DB_SCHEMA,
                    table_name=SQL(self.table_name),
                )
                .as_string()
            )
        )


@dataclass
class CreateHistoryTableSQL(SQLEmitter):
    """Creates a history/audit table for tracking changes in the main table.

    This class generates and executes SQL to create an audit table that mirrors the structure
    of the original table, with additional audit columns. The created table will be in the
    'audit' schema and will include:
    - All columns from the original table
    - A generated identity primary key column 'pk'
    - Indexes on the pk and (id, modified_at) columns

    The audit table is initially created empty (WITH NO DATA) and will be populated through
    triggers or other mechanisms when changes occur in the main table.

    Args:
        None directly, but inherits from SQLEmitter which provides table_name

    Returns:
        None

    Example:
        ```
        emitter = CreateHistoryTableSQL()
        emitter.emit_sql(engine)
        ```

    Note:
        - Requires {db_name}_admin role privileges
        - Creates table in the audit schema
        - Table will be named audit.{db_schema}_{table_name}
    """

    def emit_sql(self, conn: Engine) -> None:
        """
        Creates an audit table for tracking changes in the database.

        This method executes SQL to:
        1. Set the database role
        2. Create an audit table as a copy of the source table structure (without data)
        3. Add an auto-incrementing primary key column
        4. Create indexes for efficient querying

        Args:
            conn (Engine): SQLAlchemy engine connection object

        Returns:
            None

        Raises:
            SQLAlchemyError: If there is an error executing the SQL statements
        """
        conn.execute(
            text(
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
                    db_name=DB_NAME,
                    db_schema=DB_SCHEMA,
                    table_name=SQL(self.table_name),
                )
                .as_string()
            )
        )


@dataclass
class InsertHistoryTableRecordSQL(SQLEmitter):
    """Generates and executes SQL to create a trigger function for auditing table changes.

    This class extends SQLEmitter to create a trigger function that copies newly inserted
    or updated records into a corresponding history/audit table. The history table must
    exist in the 'audit' schema and follow the naming pattern 'audit.{schema}_{table}'.

    Parameters
    ----------
    table_name : str
        The name of the table to create the history trigger for.
        The audit table must already exist as audit.{schema}_{table_name}

    Returns
    -------
    None
        Executes the SQL directly on the database connection.

    Notes
    -----
    - Creates a SECURITY DEFINER trigger function
    - Trigger fires AFTER INSERT OR UPDATE operations
    - Copies the entire row into the audit table using the NEW record's ID
    - The audit table must have identical structure to the source table
    """

    def emit_sql(self, conn: Engine) -> None:
        """Creates and executes a SQL function that audits table changes by inserting records into an audit table.

        This method generates a trigger function that copies newly inserted or updated records
        into a corresponding audit table in the audit schema. The audit table must follow the same
        structure as the source table.

        Args:
            conn (Engine): SQLAlchemy Engine object representing the database connection

        Returns:
            None

        Example:
            ```
            emitter = SQLEmitter('users')
            emitter.emit_sql(engine)
            # Creates trigger function that copies changes from schema.users to audit.schema_users
            ```
        """
        function_string = (
            SQL(
                """
            BEGIN
                INSERT INTO audit.{db_schema}_{table_name}
                SELECT *
                FROM {db_schema}.{table_name}
                WHERE id = NEW.id;
                RETURN NEW;
            END;
            """
            )
            .format(
                db_schema=DB_SCHEMA,
                table_name=SQL(self.table_name),
            )
            .as_string()
        )

        conn.execute(
            text(
                self.create_sql_function(
                    "history",
                    function_string,
                    timing="AFTER",
                    operation="INSERT OR UPDATE",
                    include_trigger=True,
                    db_function=False,
                    security_definer="SECURITY DEFINER",
                )
            )
        )


@dataclass
class InsertObjectTypeRecordSQL(SQLEmitter):
    """Emits SQL to create an object_type record in the database.

    This class is responsible for inserting a new record into the object_type table
    with the specified table name. The SQL is executed with elevated privileges using
    the database writer role.

    Attributes:
        timing (str): Specifies when the SQL should be executed ("AFTER")

    Args:
        table_name (str): Name of the table to be inserted into object_type table

    Example:
        ```
        emitter = InsertObjectTypeRecordSQL(table_name="my_table")
        emitter.emit_sql(engine)
        ```
    """

    timing: str = "AFTER"

    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                SQL(
                    """
            -- Create the object_type record
            SET ROLE {db_role};
            INSERT INTO {schema}.object_type (name)
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
        )


@dataclass
class InsertRelatedObjectFunctionSQL(SQLEmitter):
    def emit_sql(self, conn: Engine) -> None:
        function_string = (
            SQL(
                """
            DECLARE
                relatedobject_id VARCHAR(26) := {db_schema}.generate_ulid();
                -- user_id VARCHAR(26) := current_setting('rls_var.user_id', true);
            BEGIN
                /*
                Function used to insert a record into the related_object table, when a record is inserted
                into a table that has a PK that is a FKDefinition to the related_object table.
                Set as a trigger on the table, so that the related_object record is created when the
                record is created.
                */

                SET ROLE {db_role};
                INSERT INTO {db_schema}.related_object (id, objecttype_name)
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

        conn.execute(
            text(
                self.create_sql_function(
                    "insert_relatedobject",
                    function_string,
                    timing="BEFORE",
                    operation="INSERT",
                    include_trigger=True,
                    db_function=True,
                )
            )
        )


@dataclass
class InsertRelatedObjectTriggerSQL(SQLEmitter):
    def emit_sql(self, conn: Engine) -> None:
        conn.execute(
            text(
                self.create_sql_trigger(
                    "insert_relatedobject",
                    timing="BEFORE",
                    operation="INSERT",
                    for_each="ROW",
                    db_function=True,
                )
            )
        )


@dataclass
class InsertPermissionSQL(SQLEmitter):
    def emit_sql(self, conn: Engine) -> None:
        function_string = (
            SQL(
                """
            BEGIN
                /*
                Function to create a new Permission record when a new ObjectType is inserted.
                Records are created for each object_type with each of the following permissions:
                    SELECT, INSERT, UPDATE, DELETE
                Deleted automatically by the DB via the FKDefinition Constraints ondelete when a object_type is deleted.
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

        conn.execute(
            text(
                self.create_sql_function(
                    "create_permissions",
                    function_string,
                    timing="AFTER",
                    operation="INSERT",
                    include_trigger=True,
                    db_function=True,
                )
            )
        )


class GenericRecordAuditUserSQL(SQLEmitter):
    def emit_sql(self, conn: Engine) -> None:
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
            .format(db_schema=DB_SCHEMA)
            .as_string()
        )

        conn.execute(
            text(
                self.create_sql_function(
                    "general_record_audit_users",
                    function_string,
                    timing="BEFORE",
                    operation="INSERT OR UPDATE OR DELETE",
                    include_trigger=True,
                )
            )
        )
