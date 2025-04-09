# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap
from pydantic import computed_field
from uno.db.sql.classes import SQLEmitter


class RowLevelSecurity(SQLEmitter):
    @computed_field
    def enable_rls(self) -> str:
        """
        Emits the SQL statements to enable Row-Level Security (RLS)
        on the table.
        """
        admin_role = f"{self.config.DB_NAME}_admin"
        return textwrap.dedent(
            f"""
            -- Enable RLS for the table {self.table.name}
            SET ROLE {admin_role};
            ALTER TABLE {self.config.DB_SCHEMA}.{self.table.name} ENABLE ROW LEVEL SECURITY;
        """
        )

    @computed_field
    def force_rls(self) -> str:
        """
        Emits the SQL statements to force Row-Level Security (RLS)
        on the table for table owners and DB superusers.
        """
        admin_role = f"{self.config.DB_NAME}_admin"
        return textwrap.dedent(
            f"""
            -- FORCE RLS for the table {self.table.name}
            SET ROLE {admin_role};
            ALTER TABLE {self.config.DB_SCHEMA}.{self.table.name} FORCE ROW LEVEL SECURITY;
        """
        )


class UserRowLevelSecurity(RowLevelSecurity):
    @computed_field
    def select_policy(self) -> str:
        """
        Emits the SQL statement for the user select policy.
        Superusers can select all records; others can only select records associated with their tenant.
        """
        return textwrap.dedent(
            f"""
            /* 
            The policy to allow:
                Superusers to select all records;
                All other users to select only records associated with their tenant;
            */
            CREATE POLICY user_select_policy
            ON {self.config.DB_SCHEMA}.{self.table.name} FOR SELECT
            USING (
                email = current_setting('rls_var.email', true)::TEXT OR
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT OR
                (
                    SELECT reltuples < 2 AS has_records
                    FROM pg_class
                    WHERE relname = '{self.table.name}'
                    AND relkind = 'r'
                )
            );
        """
        )

    @computed_field
    def insert_policy(self) -> str:
        """
        Emits the SQL statement for the user insert policy.
        Superusers and Tenant Admins may insert, but regular users cannot.
        """
        return textwrap.dedent(
            f"""
            /*
            The policy to allow:
                Superusers to insert records;
                Tenant Admins to insert records associated with their tenant;
            Regular users cannot insert records.
            */
            CREATE POLICY user_insert_policy
            ON {self.config.DB_SCHEMA}.{self.table.name} FOR INSERT
            WITH CHECK (
                (
                    current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                    email = current_setting('rls_var.user_email', true)::TEXT OR
                    (
                        current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                        tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
                    )
                    OR
                    (
                        is_superuser = true AND
                        (
                            SELECT reltuples < 1 AS has_records
                            FROM pg_class
                            WHERE relname = '{self.table.name}'
                            AND relkind = 'r'
                        )
                    )
                )
            );
        """
        )

    @computed_field
    def update_policy(self) -> str:
        """
        Emits the SQL statement for the user update policy.
        Superusers can update all records; others can update only records associated with their tenant.
        """
        return textwrap.dedent(
            f"""
            /* 
            The policy to allow:
                Superusers to select all records;
                All other users to select only records associated with their tenant;
            */
            CREATE POLICY user_update_policy
            ON {self.config.DB_SCHEMA}.{self.table.name} FOR UPDATE
            USING (
                email = current_setting('rls_var.email', true)::TEXT OR
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            );
        """
        )

    @computed_field
    def delete_policy(self) -> str:
        """
        Emits the SQL statement for the user delete policy.
        Superusers and Tenant Admins may delete records; regular users cannot.
        """
        return textwrap.dedent(
            f"""
            /* 
            The policy to allow:
                Superusers to delete records;
                Tenant Admins to delete records associated with their tenant;
            Regular users cannot delete records.
            */
            CREATE POLICY user_delete_policy
            ON {self.config.DB_SCHEMA}.{self.table.name} FOR DELETE
            USING (
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                (
                    email = current_setting('rls_var.user_email', true)::TEXT AND
                    tenant_id = current_setting('rls_var.tenant_id', true)::TEXT 
                ) OR
                (
                    current_setting('rls_var.is_tenant_admin', true)::BOOLEAN = true AND
                    tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
                )
            );
        """
        )


# The remaining classes and functions for Tenant, Admin, Superuser and Public policies
# used similar patterns and can be refactored in the same manner.

'''
def tenant__emit_select_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to select all records;
            All other users to select only their tenant;
        */
        CREATE POLICY tenant__emit_select_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            id = current_setting('rls_var.tenant_id', true)::TEXT
        );
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def tenant__emit_insert_policy_sql(self) -> str:
    return (
        text(
            sql.SQL(
                """
        /*
        The policy to allow:
            Superusers to insert records;
            Tenant Admins to insert user records associated with the tenant;
        Regular users cannot insert user records.
        */
        CREATE POLICY tenant__emit_insert_policy
        ON {schema_name}.{table_name} FOR INSERT
        WITH CHECK (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def tenant_update_policy_sql(self) -> str:
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to select all records;
            All other users to select only user records associated with their tenant;
        */
        CREATE POLICY tenant_update_policy
        ON {schema_name}.{table_name} FOR UPDATE
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def tenant_delete_policy_sql(self) -> str:
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to delete tenant records;
        */
        CREATE POLICY tenant_delete_policy
        ON {schema_name}.{table_name} FOR DELETE
        USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


class TenantRowLevelSecurity(RowLevelSecurity):
    _emit_select_policy: Callable = tenant__emit_select_policy_sql
    _emit_insert_policy: Callable = tenant__emit_insert_policy_sql
    _emit_update_policy: Callable = tenant_update_policy_sql
    _emit_delete_policy: Callable = tenant_delete_policy_sql


def admin__emit_select_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
        */
        CREATE POLICY admin__emit_select_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def admin__emit_insert_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to insert a record;
            Tenant Admin users to insert a record associated with their tenant;
        */
        CREATE POLICY admin__emit_insert_policy
        ON {schema_name}.{table_name} FOR INSERT
        WITH CHECK (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def admin_update_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to update all records;
            Tenant Admin users to update all records associated with their tenant;
        */
        CREATE POLICY admin_update_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
            )
            .format(table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def admin_delete_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to delete all records;
            Tenant Admin users to delete all records associated with their tenant;
        */
        CREATE POLICY user__emit_select_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


class AdminRowLevelSecurity(RowLevelSecurity):
    _emit_select_policy: Callable = admin__emit_select_policy_sql
    _emit_insert_policy: Callable = admin__emit_insert_policy_sql
    _emit_update_policy: Callable = admin_update_policy_sql
    _emit_delete_policy: Callable = admin_delete_policy_sql


def def ault__emit_select_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
            Regular users to select only records associated with their Groups or that they own.;
        */
        CREATE POLICY user__emit_select_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            ) OR
            (
                owned_by_id = current_setting('rls_var.user_id', true)::TEXT OR
                group_id IN ({schema_name}.permissible_groups('{table_name}', 'SELECT')::TEXT[])
            )
        );
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def def ault__emit_insert_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
            Regular users to select only records associated with their Groups or that they own.;
        */
        CREATE POLICY user__emit_select_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            ) OR
            (
                owned_by_id = current_setting('rls_var.user_id', true)::TEXT OR
                group_id IN ({schema_name}.permissible_groups('{table_name}', 'INSERT')::TEXT[])
            )
        );
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def def ault_update_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
            Regular users to select only records associated with their Groups or that they own.;
        */
        CREATE POLICY user__emit_select_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            ) OR
            (
                owned_by_id = current_setting('rls_var.user_id', true)::TEXT OR
                group_id IN ({schema_name}.permissible_groups('{table_name}', 'UPDATE')::TEXT[])
            )
        );
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def def ault_delete_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
            Regular users to select only records associated with their Groups or that they own.;
        */
        CREATE POLICY user__emit_select_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            ) OR
            (
                owned_by_id = current_setting('rls_var.user_id', true)::TEXT OR
                group_id IN ({schema_name}.permissible_groups('{table_name}', 'DELETE')::TEXT[])
            )
        );
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


class DefaultRowLevelSecurity(RowLevelSecurity):
    _emit_select_policy: Callable = def ault__emit_select_policy_sql
    _emit_insert_policy: Callable = def ault__emit_insert_policy_sql
    _emit_update_policy: Callable = def ault_update_policy_sql
    _emit_delete_policy: Callable = def ault_delete_policy_sql


def superuser__emit_select_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to select all records;
        */
        CREATE POLICY tenant__emit_select_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def superuser__emit_insert_policy_sql(self) -> str:
    return (
        text(
            sql.SQL(
                """
        /*
        The policy to allow:
            Superusers to insert records;
        */
        CREATE POLICY tenant__emit_insert_policy
        ON {schema_name}.{table_name} FOR INSERT
        WITH CHECK (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def superuser_update_policy_sql(self) -> str:
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to update records;
        */
        CREATE POLICY tenant_update_policy
        ON {schema_name}.{table_name} FOR UPDATE
        USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


def superuser_delete_policy_sql(self) -> str:
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            Superusers to delete records;
        */
        CREATE POLICY tenant_delete_policy
        ON {schema_name}.{table_name} FOR DELETE
        USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


class SuperuserRowLevelSecurity(RowLevelSecurity):
    _emit_select_policy: Callable = superuser__emit_select_policy_sql
    _emit_insert_policy: Callable = superuser__emit_insert_policy_sql
    _emit_update_policy: Callable = superuser_update_policy_sql
    _emit_delete_policy: Callable = superuser_delete_policy_sql


def public__emit_select_policy_sql(self):
    return (
        text(
            sql.SQL(
                """
        /* 
        The policy to allow:
            All users to select all records;
        */
        CREATE POLICY tenant__emit_select_policy
        ON {schema_name}.{table_name} FOR SELECT
        USING (true);
        """
            )
            .format(schema_name=DB_SCHEMA, table_name=sql.SQL(self.table.name))
            .as_string()
        )
    )


class PublicReadSuperuserWriteRowLevelSecurity(RowLevelSecurity):
    _emit_select_policy: Callable = public__emit_select_policy_sql
    _emit_insert_policy: Callable = superuser__emit_insert_policy_sql
    _emit_update_policy: Callable = superuser_update_policy_sql
    _emit_delete_policy: Callable = superuser_delete_policy_sql

'''
