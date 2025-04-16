# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL emitters for table-level operations."""

import logging
from typing import List, Set
from sqlalchemy import Table, Column, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.schema import ForeignKeyConstraint

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.builders import SQLFunctionBuilder, SQLTriggerBuilder, SQLIndexBuilder
from uno.sql.errors import (
    SQLErrorCode,
    SQLEmitterError,
    SQLExecutionError,
    SQLConfigError
)


class InsertMetaRecordFunction(SQLEmitter):
    """Emitter for creating meta record insertion function."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for meta record insertion function.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate insert meta record function
        writer_role = f"{self.config.DB_NAME}_writer"

        function_body = f"""
        DECLARE
            meta_id VARCHAR(26) := {self.config.DB_SCHEMA}.generate_ulid();
        BEGIN
            /*
            Function used to insert a record into the meta_record table, when a 
            polymorphic record is inserted.
            */
            SET ROLE {writer_role};

            INSERT INTO {self.config.DB_SCHEMA}.meta_record (id, meta_type_id) VALUES (meta_id, TG_TABLE_NAME);
            NEW.id = meta_id;
            RETURN NEW;
        END;
        """

        insert_meta_record_sql = (
            self.get_function_builder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name("insert_meta_record")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_meta_record_function",
                type=SQLStatementType.FUNCTION,
                sql=insert_meta_record_sql,
            )
        )

        return statements


class InsertMetaRecordTrigger(SQLEmitter):
    """Emitter for creating meta record insertion trigger."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for meta record insertion trigger.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate insert meta record trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_insert_meta_record_trigger")
            .with_function("insert_meta_record")
            .with_timing("BEFORE")
            .with_operation("INSERT")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_meta_record_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        return statements


class RecordStatusFunction(SQLEmitter):
    """Emitter for creating record status management function and trigger."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for record status function.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate record status function
        writer_role = f"{self.config.DB_NAME}_writer"

        function_body = f"""
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

        record_status_function_sql = (
            self.get_function_builder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name("insert_record_status")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_status_columns",
                type=SQLStatementType.FUNCTION,
                sql=record_status_function_sql,
            )
        )

        # Generate record status trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_insert_record_status_trigger")
            .with_function("insert_record_status")
            .with_timing("BEFORE")
            .with_operation("INSERT OR UPDATE OR DELETE")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="record_status_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        return statements


class RecordUserAuditFunction(SQLEmitter):
    """Emitter for creating user audit function and trigger."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for user audit function.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate user audit function
        writer_role = f"{self.config.DB_NAME}_writer"

        function_body = f"""
        DECLARE
            user_id VARCHAR(26) := current_setting('rls_var.user_id', TRUE);
        BEGIN
            SET ROLE {writer_role};

            IF user_id IS NULL OR user_id = '' THEN
                IF EXISTS (SELECT id FROM {self.config.DB_SCHEMA}.user) THEN
                    RAISE EXCEPTION 'No user defined in rls_vars';
                END IF;
            END IF;
            IF NOT EXISTS (SELECT id FROM {self.config.DB_SCHEMA}.user WHERE id = user_id) THEN
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

        user_audit_function_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name("manage_record_audit_columns")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="manage_record_user_audit_columns",
                type=SQLStatementType.FUNCTION,
                sql=user_audit_function_sql,
            )
        )

        # Generate user audit trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_record_user_audit_trigger")
            .with_function("manage_record_audit_columns")
            .with_timing("BEFORE")
            .with_operation("INSERT OR UPDATE OR DELETE")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="record_user_audit_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        return statements


class InsertPermission(SQLEmitter):
    """Emitter for inserting permissions for meta types."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for permission insertion.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate insert permissions function
        function_body = f"""
        BEGIN
            /*
            Function to create a new Permission record when a new MetaType is inserted.
            Records are created for each meta_type with each of the following permissions:
                SELECT, INSERT, UPDATE, DELETE
            Deleted automatically by the DB via the FKDefinition Constraints ondelete when a meta_type is deleted.
            */
            SET ROLE {self.config.DB_NAME}_admin;
            INSERT INTO {self.config.DB_SCHEMA}.permission(meta_type_id, operation)
                VALUES (NEW.id, 'SELECT'::{self.config.DB_SCHEMA}.sqloperation);
            INSERT INTO {self.config.DB_SCHEMA}.permission(meta_type_id, operation)
                VALUES (NEW.id, 'INSERT'::{self.config.DB_SCHEMA}.sqloperation);
            INSERT INTO {self.config.DB_SCHEMA}.permission(meta_type_id, operation)
                VALUES (NEW.id, 'UPDATE'::{self.config.DB_SCHEMA}.sqloperation);
            INSERT INTO {self.config.DB_SCHEMA}.permission(meta_type_id, operation)
                VALUES (NEW.id, 'DELETE'::{self.config.DB_SCHEMA}.sqloperation);
            RETURN NEW;
        END;
        """

        insert_permissions_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name("insert_permissions")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_permissions",
                type=SQLStatementType.FUNCTION,
                sql=insert_permissions_sql,
            )
        )

        # Generate insert permissions trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_insert_permissions_trigger")
            .with_function("insert_permissions")
            .with_timing("AFTER")
            .with_operation("INSERT")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_permissions_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        return statements


class ValidateGroupInsert(SQLEmitter):
    """Emitter for validating group insertions."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for group validation.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate validate group insert function
        function_body = f"""
        DECLARE
            group_count INT4;
            tenanttype {self.config.DB_SCHEMA}.tenanttype;
        BEGIN
            SELECT {self.config.DB_SCHEMA}.tenant_type INTO tenanttype
            FROM {self.config.DB_SCHEMA}.tenant
            WHERE id = NEW.tenant_id;

            SELECT COUNT(*) INTO group_count
            FROM {self.config.DB_SCHEMA}.group
            WHERE tenant_id = NEW.tenant_id;

            IF NOT {self.config.ENFORCE_MAX_GROUPS} THEN
                RETURN NEW;
            END IF;

            IF tenanttype = 'INDIVIDUAL' AND
                {self.config.MAX_INDIVIDUAL_GROUPS} > 0 AND
                group_count >= {self.config.MAX_INDIVIDUAL_GROUPS} THEN
                    RAISE EXCEPTION 'Group Count Exceeded';
            END IF;
            IF
                tenanttype = 'BUSINESS' AND
                {self.config.MAX_BUSINESS_GROUPS} > 0 AND
                group_count >= {self.config.MAX_BUSINESS_GROUPS} THEN
                    RAISE EXCEPTION 'Group Count Exceeded';
            END IF;
            IF
                tenanttype = 'CORPORATE' AND
                {self.config.MAX_CORPORATE_GROUPS} > 0 AND
                group_count >= {self.config.MAX_CORPORATE_GROUPS} THEN
                    RAISE EXCEPTION 'Group Count Exceeded';
            END IF;
            IF
                tenanttype = 'ENTERPRISE' AND
                {self.config.MAX_ENTERPRISE_GROUPS} > 0 AND
                group_count >= {self.config.MAX_ENTERPRISE_GROUPS} THEN
                    RAISE EXCEPTION 'Group Count Exceeded';
            END IF;
            RETURN NEW;
        END;
        """

        validate_group_insert_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name(f"{self.table.name}_validate_group_insert")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="validate_group_insert",
                type=SQLStatementType.FUNCTION,
                sql=validate_group_insert_sql,
            )
        )

        # Generate validate group insert trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_validate_group_insert_trigger")
            .with_function(f"{self.table.name}_validate_group_insert")
            .with_timing("BEFORE")
            .with_operation("INSERT")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="validate_group_insert_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        return statements


class InsertGroupForTenant(SQLEmitter):
    """Emitter for inserting a group for a new tenant."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for group insertion.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate insert group for tenant function
        admin_role = f"{self.config.DB_NAME}_admin"

        function_body = f"""
        BEGIN
            SET ROLE {admin_role};
            INSERT INTO {self.config.DB_SCHEMA}.group(tenant_id, name) VALUES (NEW.id, NEW.name);
            RETURN NEW;
        END;
        """

        insert_group_function_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name("insert_group_for_tenant")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_group_for_tenant",
                type=SQLStatementType.FUNCTION,
                sql=insert_group_function_sql,
            )
        )

        # Generate insert group for tenant trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table("tenant")  # Hard-coded to tenant table
            .with_name("insert_group_for_tenant_trigger")
            .with_function("insert_group_for_tenant")
            .with_timing("AFTER")
            .with_operation("INSERT")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_group_for_tenant_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        return statements


class DefaultGroupTenant(SQLEmitter):
    """Emitter for setting default tenant for a group."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for default group tenant.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate default group tenant function
        function_body = f"""
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

        default_group_function_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name(f"{self.table.name}_insert_default_group_column")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_default_group_column",
                type=SQLStatementType.FUNCTION,
                sql=default_group_function_sql,
            )
        )

        # Generate default group tenant trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_default_group_tenant_trigger")
            .with_function(f"{self.table.name}_insert_default_group_column")
            .with_timing("BEFORE")
            .with_operation("INSERT")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="default_group_tenant_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        return statements


class UserRecordUserAuditFunction(SQLEmitter):
    """Emitter for user-specific audit function (special case for first user)."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for user-specific audit function.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None or self.table.name != "user":
            return statements

        # Generate user audit function for the user table
        writer_role = f"{self.config.DB_NAME}_writer"

        function_body = f"""
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
                NOT EXISTS (SELECT id FROM {self.config.DB_SCHEMA}.user WHERE id = user_id) THEN
                    RAISE EXCEPTION 'user_id in rls_vars is not a valid user';
            END IF;
            IF user_id IS NULL AND
                EXISTS (SELECT id FROM {self.config.DB_SCHEMA}.user) THEN
                    IF TG_OP = 'UPDATE' THEN
                        IF NOT EXISTS (SELECT id FROM {self.config.DB_SCHEMA}.user WHERE id = OLD.id) THEN
                            RAISE EXCEPTION 'No user defined in rls_vars and this is not the first user being updated';
                        ELSE
                            user_id := OLD.id;
                        END IF;
                    ELSE
                        RAISE EXCEPTION 'No user defined in rls_vars and this is not the first user created';
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

        user_audit_function_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name("manage_user_audit_columns")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="manage_user_user_audit_columns",
                type=SQLStatementType.FUNCTION,
                sql=user_audit_function_sql,
            )
        )

        # Generate user audit trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_user_audit_trigger")
            .with_function("manage_user_audit_columns")
            .with_timing("BEFORE")
            .with_operation("INSERT OR UPDATE OR DELETE")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="user_audit_trigger",
                type=SQLStatementType.TRIGGER,
                sql=trigger_sql,
            )
        )

        return statements


class AlterGrants(SQLEmitter):
    """Emitter for altering grants on a table."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for altering grants.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate alter grants SQL
        admin_role = f"{self.config.DB_NAME}_admin"
        writer_role = f"{self.config.DB_NAME}_writer"
        reader_role = f"{self.config.DB_NAME}_reader"

        alter_grants_sql = f"""
        SET ROLE {admin_role};
        -- Configure table ownership and privileges
        ALTER TABLE {self.config.DB_SCHEMA}.{self.table.name} OWNER TO {admin_role};
        REVOKE ALL ON {self.config.DB_SCHEMA}.{self.table.name} FROM PUBLIC, {writer_role}, {reader_role};
        GRANT SELECT ON {self.config.DB_SCHEMA}.{self.table.name} TO
            {reader_role},
            {writer_role};
        GRANT ALL ON {self.config.DB_SCHEMA}.{self.table.name} TO
            {writer_role};
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="alter_grants", type=SQLStatementType.GRANT, sql=alter_grants_sql
            )
        )

        return statements


class InsertMetaType(SQLEmitter):
    """Emitter for inserting a meta type for a table."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for inserting meta type.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate insert meta type SQL
        writer_role = f"{self.config.DB_NAME}_writer"

        insert_meta_type_sql = f"""
        -- Create the meta_type record
        SET ROLE {writer_role};
        INSERT INTO {self.config.DB_SCHEMA}.meta_type (id)
        VALUES ('{self.table.name}')
        ON CONFLICT DO NOTHING;
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_meta_type",
                type=SQLStatementType.INSERT,
                sql=insert_meta_type_sql,
            )
        )

        return statements


class RecordVersionAudit(SQLEmitter):
    """Emitter for enabling version auditing on a table."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for version auditing.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate enable version audit SQL
        enable_version_audit_sql = f"""
        -- Enable auditing for the table
        SELECT audit.enable_tracking('{self.table.name}'::regclass);
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="enable_version_audit",
                type=SQLStatementType.FUNCTION,
                sql=enable_version_audit_sql,
            )
        )

        return statements


class EnableHistoricalAudit(SQLEmitter):
    """Emitter for enabling historical auditing on a table."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for historical auditing.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate create history table SQL
        admin_role = f"{self.config.DB_NAME}_admin"

        create_history_table_sql = f"""
        SET ROLE {admin_role};
        CREATE TABLE audit.{self.config.DB_SCHEMA}_{self.table.name}
        AS (
            SELECT 
                t1.*,
                t2.meta_type_id
            FROM {self.config.DB_SCHEMA}.{self.table.name} t1
            INNER JOIN meta_record t2
            ON t1.id = t2.id
        )
        WITH NO DATA;

        ALTER TABLE audit.{self.config.DB_SCHEMA}_{self.table.name}
        ADD COLUMN pk INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY;

        CREATE INDEX {self.config.DB_SCHEMA}_{self.table.name}_pk_idx
        ON audit.{self.config.DB_SCHEMA}_{self.table.name} (pk);

        CREATE INDEX {self.config.DB_SCHEMA}_{self.table.name}_id_modified_at_idx
        ON audit.{self.config.DB_SCHEMA}_{self.table.name} (id, modified_at);
        """

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_history_table",
                type=SQLStatementType.TABLE,
                sql=create_history_table_sql,
            )
        )

        # Generate insert history record function
        function_body = f"""
        BEGIN
            INSERT INTO audit.{self.config.DB_SCHEMA}_{self.table.name}
            SELECT *
            FROM {self.config.DB_SCHEMA}.{self.table.name}
            WHERE id = NEW.id;
            RETURN NEW;
        END;
        """

        insert_history_record_sql = (
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name(f"{self.table.name}_history")
            .with_return_type("TRIGGER")
            .with_body(function_body)
            .as_security_definer()
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_history_record",
                type=SQLStatementType.FUNCTION,
                sql=insert_history_record_sql,
            )
        )

        # Generate history trigger
        trigger_sql = (
            SQLTriggerBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_table(self.table.name)
            .with_name(f"{self.table.name}_history_trigger")
            .with_function(f"{self.table.name}_history")
            .with_timing("AFTER")
            .with_operation("INSERT OR UPDATE")
            .with_for_each("ROW")
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="history_trigger", type=SQLStatementType.TRIGGER, sql=trigger_sql
            )
        )

        return statements


class TableMergeFunction(SQLEmitter):
    """Emitter for table-specific merge function.

    This emitter generates a PL/pgSQL function for each table that accepts
    a JSONB parameter containing model_dump from a domain entity DTO. It uses
    PostgreSQL 16's MERGE command to:
    1. Look up the record using PK or unique constraints
    2. Update only non-PK, non-unique constraint columns if found
    3. Insert the record if not found
    4. Return the operation performed ('inserted', 'updated', 'selected')
    """

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL for table-specific merge function.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Require a table to be set
        if self.table is None:
            return statements

        schema_name = self.connection_config.db_schema
        table_name = self.table.name
        function_name = f"merge_{table_name}_record"

        # Get primary key columns
        pk_columns: Set[str] = set()
        for constraint in self.table.constraints:
            if isinstance(constraint, PrimaryKeyConstraint):
                pk_columns = {col.name for col in constraint.columns}
                break

        # Get unique constraint columns
        unique_constraints = []
        for constraint in self.table.constraints:
            if isinstance(constraint, UniqueConstraint):
                unique_constraints.append([col.name for col in constraint.columns])

        # Format the primary key array for SQL
        pk_array_sql = (
            "ARRAY[" + ", ".join([f"'{pk}'" for pk in pk_columns]) + "]"
            if pk_columns
            else "ARRAY[]::text[]"
        )

        # Format the unique constraints array for SQL
        uc_arrays = []
        for constraint in unique_constraints:
            constraint_array = (
                "ARRAY[" + ", ".join([f"'{col}'" for col in constraint]) + "]"
            )
            uc_arrays.append(constraint_array)

        uc_arrays_sql = ", ".join(uc_arrays)
        uc_array_sql = f"ARRAY[{uc_arrays_sql}]" if uc_arrays else "ARRAY[]::text[][]"

        # Generate the function SQL
        function_sql = f"""
CREATE OR REPLACE FUNCTION {schema_name}.{function_name}(
    data jsonb
) RETURNS jsonb AS $$$
DECLARE
    match_condition text := '';
    update_set_clause text := '';
    insert_columns text := '';
    insert_values text := '';
    merge_query text;
    result_record jsonb;
    action_performed text;
    column_name text;
    column_value jsonb;
    debug_info jsonb;
    source_clause text := '';
    record_exists boolean := false;
    needs_update boolean := false;
    
    -- Primary key columns for this table
    primary_keys text[] := {pk_array_sql};
    
    -- Unique constraint columns for this table
    unique_constraints text[][] := {uc_array_sql};
    
    -- All keys to check
    all_keys text[];
    
    -- Keys from the data
    data_keys text[];
BEGIN
    -- Validate inputs
    IF data IS NULL THEN
        RAISE EXCEPTION 'Invalid parameter: data must be provided';
    END IF;
    
    -- Get all keys from the data
    SELECT array_agg(key) INTO data_keys FROM jsonb_object_keys(data) AS key;
    
    -- APPROACH 1: Try to use primary key if all columns are in the data
    IF primary_keys IS NOT NULL AND array_length(primary_keys, 1) > 0 THEN
        IF (SELECT bool_and(data ? key) FROM unnest(primary_keys) AS key) THEN
            all_keys := primary_keys;
        END IF;
    END IF;
    
    -- APPROACH 2: If primary key not usable, try each unique constraint
    IF all_keys IS NULL AND array_length(unique_constraints, 1) > 0 THEN
        FOR i IN 1..array_length(unique_constraints, 1) LOOP
            IF (SELECT bool_and(data ? key) FROM unnest(unique_constraints[i]) AS key) THEN
                all_keys := unique_constraints[i];
                EXIT;
            END IF;
        END LOOP;
    END IF;
    
    -- Create debug info
    debug_info := jsonb_build_object(
        'table', '{table_name}',
        'schema', '{schema_name}',
        'data_keys', to_jsonb(data_keys),
        'primary_keys', to_jsonb(primary_keys),
        'unique_constraints', to_jsonb(unique_constraints),
        'selected_keys', to_jsonb(all_keys)
    );
    
    -- Raise exception if no usable keys found
    IF all_keys IS NULL OR array_length(all_keys, 1) = 0 THEN
        RAISE EXCEPTION 'No primary keys or unique constraints found in the data. Ensure that the data includes either all PK columns or all columns of at least one unique constraint. Debug: %', debug_info;
    END IF;
    
    -- First check if the record exists and get its current values
    EXECUTE format('
        SELECT EXISTS(
            SELECT 1 FROM {schema_name}.{table_name}
            WHERE %s
        ),
        (SELECT to_jsonb(t.*) FROM {schema_name}.{table_name} t WHERE %s)
    ',
    array_to_string(
        array(
            SELECT format('%I = %L', key, data->>key)
            FROM unnest(all_keys) AS key
        ),
        ' AND '
    ),
    array_to_string(
        array(
            SELECT format('%I = %L', key, data->>key)
            FROM unnest(all_keys) AS key
        ),
        ' AND '
    )
    ) INTO record_exists, result_record;
    
    -- Check if any non-key columns need to be updated
    IF record_exists THEN
        needs_update := false;
        FOR column_name, column_value IN SELECT * FROM jsonb_each(data) LOOP
            -- Skip null values in updates when column is required
            -- Skip key columns
            -- Skip columns not in the data but in the result_record
            IF NOT (column_name = ANY(all_keys)) AND 
               column_value IS NOT NULL AND
               (result_record->>column_name IS DISTINCT FROM column_value#>>'{{}}') THEN
                needs_update := true;
                EXIT;
            END IF;
        END LOOP;
    END IF;
    
    -- Build match condition for the MERGE statement
    FOREACH column_name IN ARRAY all_keys LOOP
        IF match_condition != '' THEN
            match_condition := match_condition || ' AND ';
        END IF;
        match_condition := match_condition || format('target.%I = source.%I', column_name, column_name);
    END LOOP;
    
    -- Build source CTE clause
    FOR column_name, column_value IN SELECT * FROM jsonb_each(data) LOOP
        IF source_clause != '' THEN
            source_clause := source_clause || ', ';
        END IF;
        source_clause := source_clause || format(
            '%s AS %I',
            CASE 
                WHEN jsonb_typeof(column_value) = 'null' THEN 'NULL'
                ELSE format('%L', column_value#>>'{{}}')
            END,
            column_name
        );
        
        -- Add to insert columns and values
        IF insert_columns != '' THEN
            insert_columns := insert_columns || ', ';
            insert_values := insert_values || ', ';
        END IF;
        insert_columns := insert_columns || quote_ident(column_name);
        insert_values := insert_values || format('source.%I', column_name);
        
        -- Add to update clause if not a key column
        IF NOT (column_name = ANY(all_keys)) AND column_value IS NOT NULL THEN
            IF update_set_clause != '' THEN
                update_set_clause := update_set_clause || ', ';
            END IF;
            update_set_clause := update_set_clause || format('%I = source.%I', column_name, column_name);
        END IF;
    END LOOP;
    
    -- Handle case when update_set_clause is empty
    IF update_set_clause = '' THEN
        -- Use a dummy update that doesn't change anything
        update_set_clause := format('%I = target.%I', primary_keys[1], primary_keys[1]);
    END IF;
    
    -- Only perform the operation if we need to create or update
    IF NOT record_exists OR needs_update THEN
        -- Construct the MERGE statement without RETURNING (not supported in PG16)
        merge_query := format('
            WITH source AS (
                SELECT %s
            )
            MERGE INTO {schema_name}.{table_name} AS target
            USING source
            ON %s
            WHEN MATCHED %s THEN
                UPDATE SET %s
            WHEN NOT MATCHED THEN
                INSERT (%s)
                VALUES (%s);
        ',
        source_clause,
        match_condition,
        CASE WHEN needs_update THEN '' ELSE 'AND false' END,
        update_set_clause,
        insert_columns,
        insert_values
        );
        
        -- Execute the MERGE statement
        EXECUTE merge_query;
    END IF;
    
    -- Now get the final record state
    EXECUTE format('
        SELECT to_jsonb(t.*)
        FROM {schema_name}.{table_name} t
        WHERE %s
    ',
    array_to_string(
        array(
            SELECT format('t.%I = %L', key, data->>key)
            FROM unnest(all_keys) AS key
        ),
        ' AND '
    )
    ) INTO result_record;
    
    -- Determine action performed
    IF NOT record_exists THEN
        action_performed := 'inserted';
    ELSIF needs_update THEN
        action_performed := 'updated';
    ELSE
        action_performed := 'selected';
    END IF;
    
    -- Add the action to the result
    result_record := jsonb_set(result_record, '{{_action}}', to_jsonb(action_performed));
    
    RETURN result_record;
END;
$$ LANGUAGE plpgsql;
"""

        # Create a SQL statement with metadata
        statements.append(
            SQLStatement(
                name=f"{table_name}_merge_function",
                type=SQLStatementType.FUNCTION,
                sql=function_sql,
            )
        )

        return statements
