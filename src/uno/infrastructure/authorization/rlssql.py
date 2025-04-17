# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap
from typing import Any, Callable
from pydantic import computed_field
from uno.sql.emitter import SQLEmitter


class RowLevelSecurity(SQLEmitter):
    def get_admin_role(self) -> str:
        """
        Safely gets the admin role name.
        
        Returns:
            Admin role name for the database
        """
        return f"{self.config.DB_NAME}_admin" if hasattr(self.config, "DB_NAME") else "admin"
    
    def get_table_name(self) -> str:
        """
        Safely gets the table name from the SQLEmitter.
        
        Returns:
            Table name as a string
            
        Raises:
            ValueError: If table is not set 
        """
        if self.table is None:
            raise ValueError("Table not set for Row-Level Security")
        return self.table.name
    
    @computed_field
    def enable_rls(self) -> str:
        """
        Emits the SQL statements to enable Row-Level Security (RLS)
        on the table.
        """
        admin_role = self.get_admin_role()
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            -- Enable RLS for the table {table_name}
            SET ROLE {admin_role};
            ALTER TABLE {schema_name}.{table_name} ENABLE ROW LEVEL SECURITY;
        """), admin_role=admin_role, table_name=table_name)

    @computed_field
    def force_rls(self) -> str:
        """
        Emits the SQL statements to force Row-Level Security (RLS)
        on the table for table owners and DB superusers.
        """
        admin_role = self.get_admin_role()
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            -- FORCE RLS for the table {table_name}
            SET ROLE {admin_role};
            ALTER TABLE {schema_name}.{table_name} FORCE ROW LEVEL SECURITY;
        """), admin_role=admin_role, table_name=table_name)


class UserRowLevelSecurity(RowLevelSecurity):
    @computed_field
    def select_policy(self) -> str:
        """
        Emits the SQL statement for the user select policy.
        Superusers can select all records; others can only select records associated with their tenant.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to select all records;
                All other users to select only records associated with their tenant;
            */
            CREATE POLICY user_select_policy
            ON {schema_name}.{table_name} FOR SELECT
            USING (
                email = current_setting('rls_var.email', true)::TEXT OR
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT OR
                (
                    SELECT reltuples < 2 AS has_records
                    FROM pg_class
                    WHERE relname = '{table_name}'
                    AND relkind = 'r'
                )
            );
        """), table_name=table_name)

    @computed_field
    def insert_policy(self) -> str:
        """
        Emits the SQL statement for the user insert policy.
        Superusers and Tenant Admins may insert, but regular users cannot.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /*
            The policy to allow:
                Superusers to insert records;
                Tenant Admins to insert records associated with their tenant;
            Regular users cannot insert records.
            */
            CREATE POLICY user_insert_policy
            ON {schema_name}.{table_name} FOR INSERT
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
                            WHERE relname = '{table_name}'
                            AND relkind = 'r'
                        )
                    )
                )
            );
        """), table_name=table_name)

    @computed_field
    def update_policy(self) -> str:
        """
        Emits the SQL statement for the user update policy.
        Superusers can update all records; others can update only records associated with their tenant.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to select all records;
                All other users to select only records associated with their tenant;
            */
            CREATE POLICY user_update_policy
            ON {schema_name}.{table_name} FOR UPDATE
            USING (
                email = current_setting('rls_var.email', true)::TEXT OR
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            );
        """), table_name=table_name)

    @computed_field
    def delete_policy(self) -> str:
        """
        Emits the SQL statement for the user delete policy.
        Superusers and Tenant Admins may delete records; regular users cannot.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to delete records;
                Tenant Admins to delete records associated with their tenant;
            Regular users cannot delete records.
            */
            CREATE POLICY user_delete_policy
            ON {schema_name}.{table_name} FOR DELETE
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
        """), table_name=table_name)


# The remaining classes and functions for Tenant, Admin, Superuser and Public policies
# have been refactored below to use the proper SQLEmitter pattern.

class TenantRowLevelSecurity(RowLevelSecurity):
    @computed_field
    def select_policy(self) -> str:
        """
        Emits the SQL statement for the tenant select policy.
        Superusers can select all records; all other users can select only their tenant.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to select all records;
                All other users to select only their tenant;
            */
            CREATE POLICY tenant_select_policy
            ON {schema_name}.{table_name} FOR SELECT
            USING (
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                id = current_setting('rls_var.tenant_id', true)::TEXT
            );
        """), table_name=table_name)

    @computed_field
    def insert_policy(self) -> str:
        """
        Emits the SQL statement for the tenant insert policy.
        Only superusers can insert tenant records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /*
            The policy to allow:
                Superusers to insert records;
                Tenant Admins to insert user records associated with the tenant;
            Regular users cannot insert user records.
            */
            CREATE POLICY tenant_insert_policy
            ON {schema_name}.{table_name} FOR INSERT
            WITH CHECK (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """), table_name=table_name)

    @computed_field
    def update_policy(self) -> str:
        """
        Emits the SQL statement for the tenant update policy.
        Superusers can update all records; tenant admins can update their own tenant records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
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
        """), table_name=table_name)

    @computed_field
    def delete_policy(self) -> str:
        """
        Emits the SQL statement for the tenant delete policy.
        Only superusers can delete tenant records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to delete tenant records;
            */
            CREATE POLICY tenant_delete_policy
            ON {schema_name}.{table_name} FOR DELETE
            USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """), table_name=table_name)


class AdminRowLevelSecurity(RowLevelSecurity):
    @computed_field
    def select_policy(self) -> str:
        """
        Emits the SQL statement for the admin select policy.
        Superusers can select all records; tenant admins can select records associated with their tenant.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to select all records;
                Tenant Admin users to select all records associated with their tenant;
            */
            CREATE POLICY admin_select_policy
            ON {schema_name}.{table_name} FOR SELECT
            USING (
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                (
                    current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                    tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
                )
            );
        """), table_name=table_name)

    @computed_field
    def insert_policy(self) -> str:
        """
        Emits the SQL statement for the admin insert policy.
        Superusers can insert records; tenant admins can insert records for their tenant.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to insert a record;
                Tenant Admin users to insert a record associated with their tenant;
            */
            CREATE POLICY admin_insert_policy
            ON {schema_name}.{table_name} FOR INSERT
            WITH CHECK (
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                (
                    current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                    tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
                )
            );
        """), table_name=table_name)

    @computed_field
    def update_policy(self) -> str:
        """
        Emits the SQL statement for the admin update policy.
        Superusers can update all records; tenant admins can update records for their tenant.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to update all records;
                Tenant Admin users to update all records associated with their tenant;
            */
            CREATE POLICY admin_update_policy
            ON {schema_name}.{table_name} FOR UPDATE
            USING (
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                (
                    current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                    tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
                )
            );
        """), table_name=table_name)

    @computed_field
    def delete_policy(self) -> str:
        """
        Emits the SQL statement for the admin delete policy.
        Superusers can delete all records; tenant admins can delete records for their tenant.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to delete all records;
                Tenant Admin users to delete all records associated with their tenant;
            */
            CREATE POLICY admin_delete_policy
            ON {schema_name}.{table_name} FOR DELETE
            USING (
                current_setting('rls_var.is_superuser', true)::BOOLEAN OR
                (
                    current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                    tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
                )
            );
        """), table_name=table_name)


class DefaultRowLevelSecurity(RowLevelSecurity):
    @computed_field
    def select_policy(self) -> str:
        """
        Emits the SQL statement for the default select policy.
        Superusers can select all records; tenant admins can select records for their tenant;
        regular users can select records they own or have group access to.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to select all records;
                Tenant Admin users to select all records associated with their tenant;
                Regular users to select only records associated with their Groups or that they own.;
            */
            CREATE POLICY default_select_policy
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
        """), table_name=table_name)

    @computed_field
    def insert_policy(self) -> str:
        """
        Emits the SQL statement for the default insert policy.
        Superusers and tenant admins can insert records; regular users can insert if they have group access.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to insert records;
                Tenant Admin users to insert records associated with their tenant;
                Regular users to insert only records associated with their Groups or that they own.;
            */
            CREATE POLICY default_insert_policy
            ON {schema_name}.{table_name} FOR INSERT
            WITH CHECK (
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
        """), table_name=table_name)

    @computed_field
    def update_policy(self) -> str:
        """
        Emits the SQL statement for the default update policy.
        Superusers and tenant admins can update records; regular users can update if they have group access.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to update all records;
                Tenant Admin users to update all records associated with their tenant;
                Regular users to update only records associated with their Groups or that they own.;
            */
            CREATE POLICY default_update_policy
            ON {schema_name}.{table_name} FOR UPDATE
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
        """), table_name=table_name)

    @computed_field
    def delete_policy(self) -> str:
        """
        Emits the SQL statement for the default delete policy.
        Superusers and tenant admins can delete records; regular users can delete if they have group access.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to delete all records;
                Tenant Admin users to delete all records associated with their tenant;
                Regular users to delete only records associated with their Groups or that they own.;
            */
            CREATE POLICY default_delete_policy
            ON {schema_name}.{table_name} FOR DELETE
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
        """), table_name=table_name)


class SuperuserRowLevelSecurity(RowLevelSecurity):
    @computed_field
    def select_policy(self) -> str:
        """
        Emits the SQL statement for the superuser select policy.
        Only superusers can select records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to select all records;
            */
            CREATE POLICY superuser_select_policy
            ON {schema_name}.{table_name} FOR SELECT
            USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """), table_name=table_name)

    @computed_field
    def insert_policy(self) -> str:
        """
        Emits the SQL statement for the superuser insert policy.
        Only superusers can insert records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /*
            The policy to allow:
                Superusers to insert records;
            */
            CREATE POLICY superuser_insert_policy
            ON {schema_name}.{table_name} FOR INSERT
            WITH CHECK (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """), table_name=table_name)

    @computed_field
    def update_policy(self) -> str:
        """
        Emits the SQL statement for the superuser update policy.
        Only superusers can update records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to update records;
            */
            CREATE POLICY superuser_update_policy
            ON {schema_name}.{table_name} FOR UPDATE
            USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """), table_name=table_name)

    @computed_field
    def delete_policy(self) -> str:
        """
        Emits the SQL statement for the superuser delete policy.
        Only superusers can delete records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to delete records;
            */
            CREATE POLICY superuser_delete_policy
            ON {schema_name}.{table_name} FOR DELETE
            USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """), table_name=table_name)


class PublicReadSuperuserWriteRowLevelSecurity(RowLevelSecurity):
    @computed_field
    def select_policy(self) -> str:
        """
        Emits the SQL statement for the public select policy.
        All users can select all records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                All users to select all records;
            */
            CREATE POLICY public_read_policy
            ON {schema_name}.{table_name} FOR SELECT
            USING (true);
        """), table_name=table_name)
    
    @computed_field
    def insert_policy(self) -> str:
        """
        Emits the SQL statement for the superuser insert policy.
        Only superusers can insert records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /*
            The policy to allow:
                Superusers to insert records;
            */
            CREATE POLICY superuser_insert_policy
            ON {schema_name}.{table_name} FOR INSERT
            WITH CHECK (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """), table_name=table_name)

    @computed_field
    def update_policy(self) -> str:
        """
        Emits the SQL statement for the superuser update policy.
        Only superusers can update records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to update records;
            */
            CREATE POLICY superuser_update_policy
            ON {schema_name}.{table_name} FOR UPDATE
            USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """), table_name=table_name)

    @computed_field
    def delete_policy(self) -> str:
        """
        Emits the SQL statement for the superuser delete policy.
        Only superusers can delete records.
        """
        table_name = self.get_table_name()
        
        return self.format_sql_template(textwrap.dedent("""
            /* 
            The policy to allow:
                Superusers to delete records;
            */
            CREATE POLICY superuser_delete_policy
            ON {schema_name}.{table_name} FOR DELETE
            USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """), table_name=table_name)
