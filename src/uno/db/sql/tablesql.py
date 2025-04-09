import logging
from sqlalchemy.exc import SQLAlchemyError

from pydantic import computed_field

from uno.db.sql.classes import SQLEmitter
from uno.errors import UnoError
from uno.settings import uno_settings


class InsertMetaRecordFunction(SQLEmitter):
    @computed_field
    def insert_meta_record_function(self) -> str:
        """
        Create a SQL function to insert a meta record.

        :return: SQL function statement
        """
        try:
            writer_role = f"{self.config.DB_NAME}_writer"
            function_string = f"""
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

            return self.create_sql_function(
                "insert_meta_record",
                function_string,
                timing="BEFORE",
                operation="INSERT",
                include_trigger=False,
                db_function=True,
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL function for insert_meta_record: {e}")
            raise UnoError(
                f"Failed to create SQL function: {e}", "SQL_FUNCTION_CREATION_ERROR"
            )


class InsertMetaRecordTrigger(SQLEmitter):
    @computed_field
    def insert_meta_record_trigger(self) -> str:
        """
        Create a SQL trigger for inserting a meta record.

        :return: SQL trigger statement
        """
        try:
            return self.create_sql_trigger(
                "insert_meta_record",
                timing="BEFORE",
                operation="INSERT",
                for_each="ROW",
                db_function=True,
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL trigger for insert_meta_record: {e}")
            raise UnoError(
                f"Failed to create SQL trigger: {e}", "SQL_TRIGGER_CREATION_ERROR"
            )


class RecordStatusFunction(SQLEmitter):
    @computed_field
    def insert_status_columns(self) -> str:
        """
        Create a SQL function to manage record status columns.

        :return: SQL function statement
        """
        try:
            writer_role = f"{self.config.DB_NAME}_writer"
            function_string = f"""
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

            return self.create_sql_function(
                "insert_record_status_columns",
                function_string,
                timing="BEFORE",
                operation="INSERT OR UPDATE OR DELETE",
                include_trigger=True,
                db_function=True,
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL function for record status: {e}")
            raise UnoError(
                f"Failed to create SQL function: {e}", "SQL_FUNCTION_CREATION_ERROR"
            )


class RecordUserAuditFunction(SQLEmitter):
    @computed_field
    def manage_record_user_audit_columns(self) -> str:
        """
        Create a SQL function to manage user audit columns.

        :return: SQL function statement
        """
        try:
            writer_role = f"{self.config.DB_NAME}_writer"
            function_string = f"""
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

            return self.create_sql_function(
                "manage_record_audit_columns",
                function_string,
                timing="BEFORE",
                operation="INSERT OR UPDATE OR DELETE",
                include_trigger=True,
                db_function=True,
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL function for user audit: {e}")
            raise UnoError(
                f"Failed to create SQL function: {e}", "SQL_FUNCTION_CREATION_ERROR"
            )


class InsertPermission(SQLEmitter):
    @computed_field
    def insert_permissions(self) -> str:
        """
        Create a SQL function to insert permissions.

        :return: SQL function statement
        """
        try:
            function_string = f"""
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

            return self.create_sql_function(
                "insert_permissions",
                function_string,
                timing="AFTER",
                operation="INSERT",
                include_trigger=True,
                db_function=True,
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL function for permissions: {e}")
            raise UnoError(
                f"Failed to create SQL function: {e}", "SQL_FUNCTION_CREATION_ERROR"
            )


class ValidateGroupInsert(SQLEmitter):
    @computed_field
    def validate_group_insert(self) -> str:
        """
        Create a SQL function to validate group insertions.

        :return: SQL function statement
        """
        try:
            function_string = f"""
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

            return self.create_sql_function(
                "validate_group_insert",
                function_string,
                timing="BEFORE",
                operation="INSERT",
                include_trigger=True,
                db_function=False,
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL function for group validation: {e}")
            raise UnoError(
                f"Failed to create SQL function: {e}", "SQL_FUNCTION_CREATION_ERROR"
            )


class InsertGroupForTenant(SQLEmitter):
    @computed_field
    def insert_group_for_tenant(self) -> str:
        """
        Create a SQL function and trigger to insert a group for a tenant.

        :return: SQL function and trigger statement
        """
        try:
            admin_role = f"{self.config.DB_NAME}_admin"
            return f"""
                SET ROLE {admin_role};
                CREATE OR REPLACE FUNCTION {self.config.DB_SCHEMA}.insert_group_for_tenant()
                RETURNS TRIGGER
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    SET ROLE {admin_role};
                    INSERT INTO {self.config.DB_SCHEMA}.group(tenant_id, name) VALUES (NEW.id, NEW.name);
                    RETURN NEW;
                END;
                $$;

                CREATE OR REPLACE TRIGGER insert_group_for_tenant_trigger
                -- The trigger to call the function
                AFTER INSERT ON tenant
                FOR EACH ROW
                EXECUTE FUNCTION {self.config.DB_SCHEMA}.insert_group_for_tenant();
                """
        except SQLAlchemyError as e:
            logging.error(
                f"Error creating SQL function and trigger for group insertion: {e}"
            )
            raise UnoError(
                f"Failed to create SQL function and trigger: {e}",
                "SQL_FUNCTION_TRIGGER_CREATION_ERROR",
            )


class DefaultGroupTenant(SQLEmitter):
    @computed_field
    def insert_default_group_column(self) -> str:
        """
        Create a SQL function to insert a default group column.

        :return: SQL function statement
        """
        try:
            function_string = f"""
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
            return self.create_sql_function(
                "insert_default_group_column",
                function_string,
                timing="BEFORE",
                operation="INSERT",
                include_trigger=True,
                db_function=False,
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL function for default group column: {e}")
            raise UnoError(
                f"Failed to create SQL function: {e}", "SQL_FUNCTION_CREATION_ERROR"
            )


class UserRecordUserAuditFunction(SQLEmitter):
    @computed_field
    def manage_user_user_audit_columns(self) -> str:
        """
        Create a SQL function to manage user audit columns.

        :return: SQL function statement
        """
        try:
            writer_role = f"{self.config.DB_NAME}_writer"
            function_string = f"""
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

            return self.create_sql_function(
                "manage_audit_columns",
                function_string,
                timing="BEFORE",
                operation="INSERT OR UPDATE OR DELETE",
                include_trigger=True,
                db_function=False,
            )
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL function for user audit: {e}")
            raise UnoError(
                f"Failed to create SQL function: {e}", "SQL_FUNCTION_CREATION_ERROR"
            )


class AlterGrants(SQLEmitter):
    @computed_field
    def alter_grants(self) -> str:
        """
        Create a SQL statement to alter grants on a table.

        :return: SQL statement
        """
        try:
            admin_role = f"{self.config.DB_NAME}_admin"
            writer_role = f"{self.config.DB_NAME}_writer"
            reader_role = f"{self.config.DB_NAME}_reader"
            return f"""
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
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL statement for altering grants: {e}")
            raise UnoError(
                f"Failed to create SQL statement: {e}", "SQL_STATEMENT_CREATION_ERROR"
            )


class InsertMetaType(SQLEmitter):
    @computed_field
    def insert_meta_type(self) -> str:
        """
        Create a SQL statement to insert a meta type.

        :return: SQL statement
        """
        try:
            writer_role = f"{self.config.DB_NAME}_writer"
            return f"""
            -- Create the meta_type record
            SET ROLE {writer_role};
            INSERT INTO {self.config.DB_SCHEMA}.meta_type (id)
            VALUES ('{self.table.name}')
            ON CONFLICT DO NOTHING;
            """
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL statement for inserting meta type: {e}")
            raise UnoError(
                f"Failed to create SQL statement: {e}", "SQL_STATEMENT_CREATION_ERROR"
            )


class RecordVersionAudit(SQLEmitter):
    @computed_field
    def enable_version_audit(self) -> str:
        """
        Create a SQL statement to enable version auditing.

        :return: SQL statement
        """
        try:
            return f"""
            -- Enable auditing for the table
            SELECT audit.enable_tracking('{self.table.name}'::regclass);
            """
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL statement for version audit: {e}")
            raise UnoError(
                f"Failed to create SQL statement: {e}", "SQL_STATEMENT_CREATION_ERROR"
            )


class EnableHistoricalAudit(SQLEmitter):
    @computed_field
    def create_history_table(self) -> str:
        """
        Create a SQL statement to create a history table.

        :return: SQL statement
        """
        try:
            admin_role = f"{self.config.DB_NAME}_admin"
            return f"""
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
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL statement for history table: {e}")
            raise UnoError(
                f"Failed to create SQL statement: {e}", "SQL_STATEMENT_CREATION_ERROR"
            )

    @computed_field
    def insert_history_record(self) -> str:
        """
        Create a SQL function to insert a history record.

        :return: SQL function statement
        """
        try:
            function_string = f"""
            BEGIN
                INSERT INTO audit.{self.config.DB_SCHEMA}_{self.table.name}
                SELECT *
                FROM {self.config.DB_SCHEMA}.{self.table.name}
                WHERE id = NEW.id;
                RETURN NEW;
            END;
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
        except SQLAlchemyError as e:
            logging.error(f"Error creating SQL function for history record: {e}")
            raise UnoError(
                f"Failed to create SQL function: {e}", "SQL_FUNCTION_CREATION_ERROR"
            )
