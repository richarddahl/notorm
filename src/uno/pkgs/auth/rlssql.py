# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from pydantic import computed_field

from psycopg.sql import SQL, Literal

from uno.db.sql.sql import (
    SQLEmitter,
    DB_SCHEMA,
    ADMIN_ROLE,
    WRITER_ROLE,
    READER_ROLE,
)
from uno.config import settings


class RowLevelSecurity(SQLEmitter):
    @computed_field
    def enable_rls(self) -> str:
        """
        Emits the SQL statements to enable Row Level Security (RLS)
        on the table.

        Returns:
            str: A string containing the SQL statements to enable RLS for the table.
        """
        return (
            SQL(
                """
            -- Enable RLS for the table {table_name}
            SET ROLE {admin_role};
            ALTER TABLE {schema_name}.{table_name} ENABLE ROW LEVEL SECURITY;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                schema_name=DB_SCHEMA,
                table_name=SQL(self.table.name),
            )
            .as_string()
        )

    @computed_field
    def force_rls(self) -> str:
        """
        Emits the SQL statements to force Row Level Security (RLS)
        on the table for table owners and db superusers.

        ONLY APPLIED IF settings.FORCE_RLS is True.

        Returns:
            str: A string containing the SQL statements to force RLS for
            the table.
        """
        return (
            SQL(
                """
            -- FORCE RLS for the table {table_name}
            SET ROLE {admin_role};
            ALTER TABLE {schema_name}.{table_name} FORCE ROW LEVEL SECURITY;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                table_name=SQL(self.table.name),
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


class UserRowLevelSecurity(RowLevelSecurity):
    @computed_field
    def select_policy(self) -> str:
        return (
            SQL(
                """
            /* 
            The policy to allow:
                Superusers to select all records;
                All other users to select only records associated with their
                tenant;
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
                    WHERE relname = {rel_name}
                    AND relkind = 'r'
                )
            );
            """
            )
            .format(
                schema_name=DB_SCHEMA,
                table_name=SQL(self.table.name),
                rel_name=Literal(self.table.name),
                reader_role=READER_ROLE,
            )
            .as_string()
        )

    @computed_field
    def insert_policy(self) -> str:
        return (
            SQL(
                """
            /*
            The policy to allow:
                Superusers to insert records;
                Tenant Admins to insert records associated with the tenant;
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
                            WHERE relname = {rel_name}
                            AND relkind = 'r'
                         )
                    )
                )
            );
            """
            )
            .format(
                writer_role=WRITER_ROLE,
                schema_name=DB_SCHEMA,
                table_name=SQL(self.table.name),
                rel_name=Literal(self.table.name),
            )
            .as_string()
        )

    @computed_field
    def update_policy(self) -> str:
        return (
            SQL(
                """
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
            """
            )
            .format(
                table_name=SQL(self.table.name),
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )

    @computed_field
    def delete_policy(self) -> str:
        return (
            SQL(
                """
            /* 
            The policy to allow:
                Superusers to delete records;
                Tenant Admins to delete records associated with the tenant;
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
            """
            )
            .format(
                table_name=SQL(self.table.name),
                schema_name=DB_SCHEMA,
            )
            .as_string()
        )


'''
def tenant__emit_select_policy_sql(self):
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def tenant__emit_insert_policy_sql(self) -> str:
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def tenant_update_policy_sql(self) -> str:
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def tenant_delete_policy_sql(self) -> str:
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
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
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def admin__emit_insert_policy_sql(self):
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def admin_update_policy_sql(self):
    return (
        text(
            SQL(
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
            .format(table_name=SQL(self.table.name))
            .as_string()
        )
    )


def admin_delete_policy_sql(self):
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
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
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def def ault__emit_insert_policy_sql(self):
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def def ault_update_policy_sql(self):
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def def ault_delete_policy_sql(self):
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
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
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def superuser__emit_insert_policy_sql(self) -> str:
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def superuser_update_policy_sql(self) -> str:
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


def superuser_delete_policy_sql(self) -> str:
    return (
        text(
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
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
            SQL(
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
            .format(schema_name=DB_SCHEMA, table_name=SQL(self.table.name))
            .as_string()
        )
    )


class PublicReadSuperuserWriteRowLevelSecurity(RowLevelSecurity):
    _emit_select_policy: Callable = public__emit_select_policy_sql
    _emit_insert_policy: Callable = superuser__emit_insert_policy_sql
    _emit_update_policy: Callable = superuser_update_policy_sql
    _emit_delete_policy: Callable = superuser_delete_policy_sql

'''
