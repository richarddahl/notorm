# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL emitters for table-level operations."""

import logging
from typing import List

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.builders import SQLFunctionBuilder, SQLTriggerBuilder, SQLIndexBuilder
from uno.errors import UnoError


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
            SQLFunctionBuilder()
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
            SQLFunctionBuilder()
            .with_schema(self.config.DB_SCHEMA)
            .with_name("insert_record_status_columns")
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
            .with_name(f"{self.table.name}_record_status_trigger")
            .with_function("insert_record_status_columns")
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
            INSERT INTO permission(meta_type_id, operation)
                VALUES (NEW.id, 'SELECT'::{self.config.DB_SCHEMA}.sqloperation);
            INSERT INTO permission(meta_type_id, operation)
                VALUES (NEW.id, 'INSERT'::{self.config.DB_SCHEMA}.sqloperation);
            INSERT INTO permission(meta_type_id, operation)
                VALUES (NEW.id, 'UPDATE'::{self.config.DB_SCHEMA}.sqloperation);
            INSERT INTO permission(meta_type_id, operation)
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
            tenanttype tenanttype;
        BEGIN
            SELECT tenant_type INTO tenanttype
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
