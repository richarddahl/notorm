# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT


from typing import Callable

from psycopg.sql import SQL

from pydantic import ConfigDict

from sqlalchemy import text
from sqlalchemy.engine import Engine


from uno.db.sql_emitters import (
    SQLEmitter,
    DB_SCHEMA,
    DB_NAME,
    ADMIN_ROLE,
    WRITER_ROLE,
    READER_ROLE,
    LOGIN_ROLE,
    BASE_ROLE,
    LIT_BASE_ROLE,
    LIT_READER_ROLE,
    LIT_WRITER_ROLE,
    LIT_ADMIN_ROLE,
    LIT_LOGIN_ROLE,
)
from uno.config import settings


class RLSSQL(SQLEmitter):
    insert_policy: Callable | str = "RETURN true"
    select_policy: Callable | str = "RETURN true"
    delete_policy: Callable | str = "RETURN true"
    update_policy: Callable | str = "RETURN true"
    force_rls: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def emit_sql(self) -> None:
        """
        Generates and returns the SQL statements for enabling RLS, forcing RLS,
        and applying select, insert, update, and delete policies.

        Returns:
            str: A string containing the concatenated SQL statements, separated by newlines.
        """
        sql = [
            self.emit_permissible_groups_sql(),
            self.emit_create_authorize_user_function_sql(),
            self.emit_enable_rls_sql(),
            self.emit_force_rls_sql() if self.force_rls else "",
            self.select_policy(self.table_name)
            if callable(self.select_policy)
            else self.select_policy,
            self.insert_policy(self.table_name)
            if callable(self.insert_policy)
            else self.insert_policy,
            self.update_policy(self.table_name)
            if callable(self.update_policy)
            else self.update_policy,
            self.delete_policy(self.table_name)
            if callable(self.delete_policy)
            else self.delete_policy,
        ]
        self.conn.execute(text("\n".join(sql)))

    def emit_permissible_groups_sql(self) -> str:
        return SQL(
            """
            CREATE OR REPLACE FUNCTION uno.permissible_groups(table_name TEXT, operation TEXT)
            /*
            Function to get the permissible groups for the user
            */
                RETURNS SETOF uno.group
                LANGUAGE plpgsql
            AS $$
            DECLARE
                user_id TEXT;
            BEGIN
                user_id := current_setting('s_var.id', true);
                RETURN QUERY
                SELECT g.*
                FROM uno.group g
                JOIN uno.user__group__role ugr ON ugr.group_id = g.id
                JOIN uno.user u ON u.id = ugr.user_email
                JOIN uno.permission tp ON ugr.role_id = tp.id
                WHERE u.id = session_user_id AND tp.is_active = TRUE;
            END $$;
            """
        )

    def emit_enable_rls_sql(self) -> str:
        """
        Emits the SQL statements to enable Row Level Security (RLS)
        on the table.

        Returns:
            str: A string containing the SQL statements to enable RLS for the table.
        """
        return (
            SQL(
                """
            -- Enable RLS for the table {db_schema}.{table_name}
            SET ROLE {db_name}_admin;
            ALTER TABLE {db_schema}.{table_name} ENABLE ROW LEVEL SECURITY;
            """
            )
            .format(db_schema=DB_SCHEMA, table_name=SQL(self.table_name))
            .as_string()
        )

    def emit_force_rls_sql(self) -> str:
        """
        Emits the SQL statements to force Row Level Security (RLS)
        on the table for table owners and db superusers.

        Returns:
            str: A string containing the SQL statements to force RLS for the table.
        """
        return (
            SQL(
                """
            -- FORCE RLS for the table {db_schema}.{table_name}
            SET ROLE {db_name}_admin;
            ALTER TABLE {db_schema}.{table_name} FORCE ROW LEVEL SECURITY;
            """
            )
            .format(db_schema=DB_SCHEMA, table_name=SQL(self.table_name))
            .as_string()
        )

    def emit_create_authorize_user_function_sql(self) -> str:
        return SQL(
            """
            CREATE OR REPLACE FUNCTION uno.authorize_user(token TEXT, role_name TEXT DEFAULT 'reader')
            /*
            Function to verify a JWT token and set the session variables necessary for enforcing RLS
            Ensures that:
                The token is valid or
                    raises an Exception (Invalid Token)
                The token contains a sub (which is an email address) or
                    raises an Exception (Token does not contain a sub)
                The email address provided in the sub is of a user in the user table or
                    raises an Exception (User not found)
                The user is active or  Raises an Exception (User is not active)
                The user is not deleted or Raises an Exception (User was deleted)
            If all checks pass, returns the information necessary to enforce RLS otherwise raises an Exception

            The information for RLS is:
                user_id: The ID of the user 
                is_superuser: Whether the user is a superuser
                tenant_id: The ID of the tenant to which the user is associated

            ::param token: The JWT token to verify
            ::param role_name: The role to set for the session
            */
                RETURNS BOOLEAN
                LANGUAGE plpgsql
            AS $$

            DECLARE
                token_header JSONB;
                token_payload JSONB;
                token_valid BOOLEAN;
                sub TEXT;
                expiration INT;
                user_email TEXT; 
                user_id TEXT;
                user_is_superuser TEXT;
                user_tenant_id TEXT;
                user_is_active BOOLEAN;
                user_is_deleted BOOLEAN;
                token_secret TEXT;
                full_role_name TEXT:= '{db_name}_' || role_name;
                admin_role_name TEXT:= '{db_name}_' || 'admin';
            BEGIN
                -- Set the role to the admin role to read from the token_secret table
                EXECUTE 'SET ROLE ' || admin_role_name;

                -- Get the secret from the token_secret table
                SELECT secret FROM uno.token_secret INTO token_secret;

                -- Verify the token
                SELECT header, payload, valid
                FROM uno.verify(token, token_secret)
                INTO token_header, token_payload, token_valid;

                IF token_valid THEN

                    -- Get the sub from the token payload
                    sub := token_payload ->> 'sub';

                    IF sub IS NULL THEN
                        RAISE EXCEPTION 'no sub in token';
                    END IF;

                    -- Get the expiration from the token payload
                    expiration := token_payload ->> 'exp';
                    IF expiration IS NULL THEN
                        RAISE EXCEPTION 'no exp in token';
                    END IF;

                    /*
                    Set the session variable for the user's email so that it can be used
                    in the query to get the user's information
                    */
                    PERFORM set_config('rls_var.email', sub, true);

                    -- Query the user table for the user to get the values for the session variables
                    SELECT id, email, is_superuser, tenant_id, is_active, is_deleted 
                    FROM uno.user
                    WHERE email = sub
                    INTO
                        user_id,
                        user_email,
                        user_is_superuser,
                        user_tenant_id,
                        user_is_active,
                        user_is_deleted;

                    IF user_id IS NULL THEN
                        RAISE EXCEPTION 'user not found';
                    END IF;

                    IF user_is_active = FALSE THEN 
                        RAISE EXCEPTION 'user is not active';
                    END IF; 

                    IF user_is_deleted = TRUE THEN
                        RAISE EXCEPTION 'user was deleted';
                    END IF; 

                    -- Set the session variables used for RLS
                    PERFORM set_config('rls_var.email', user_email, true);
                    PERFORM set_config('rls_var.user_id', user_id, true);
                    PERFORM set_config('rls_var.is_superuser', user_is_superuser, true);
                    PERFORM set_config('rls_var.tenant_id', user_tenant_id, true);

                    --Set the role to the role passed in
                    EXECUTE 'SET ROLE ' || full_role_name;

                ELSE
                    -- Token failed verification
                    RAISE EXCEPTION 'invalid token';
                END IF;
                -- Return the validity of the token
                RETURN token_valid;
            END;
            $$;
            """
        ).format(db_name=SQL(settings.DB_NAME))


def user_select_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to select all records;
            All other users to select only records associated with their tenant;
        */
        CREATE POLICY user_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (
            email = current_setting('rls_var.email', true)::TEXT OR
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def user_insert_policy_sql(table_name) -> str:
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
        ON {db_schema}.{table_name} FOR INSERT
        WITH CHECK (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            email = current_setting('rls_var.user_email', true)::TEXT OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def user_update_policy_sql(table_name) -> str:
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to select all records;
            All other users to select only records associated with their tenant;
        */
        CREATE POLICY user_update_policy
        ON {db_schema}.{table_name} FOR UPDATE
        USING (
            email = current_setting('rls_var.email', true)::TEXT OR
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def user_delete_policy_sql(table_name) -> str:
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
        ON {db_schema}.{table_name} FOR DELETE
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
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


class UserRLSSQL(RLSSQL):
    select_policy: Callable = user_select_policy_sql
    insert_policy: Callable = user_insert_policy_sql
    update_policy: Callable = user_update_policy_sql
    delete_policy: Callable = user_delete_policy_sql


def tenant_select_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to select all records;
            All other users to select only their tenant;
        */
        CREATE POLICY tenant_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            id = current_setting('rls_var.tenant_id', true)::TEXT
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def tenant_insert_policy_sql(table_name) -> str:
    return (
        SQL(
            """
        /*
        The policy to allow:
            Superusers to insert records;
            Tenant Admins to insert user records associated with the tenant;
        Regular users cannot insert user records.
        */
        CREATE POLICY tenant_insert_policy
        ON {db_schema}.{table_name} FOR INSERT
        WITH CHECK (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def tenant_update_policy_sql(table_name) -> str:
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to select all records;
            All other users to select only user records associated with their tenant;
        */
        CREATE POLICY tenant_update_policy
        ON {db_schema}.{table_name} FOR UPDATE
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def tenant_delete_policy_sql(table_name) -> str:
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to delete tenant records;
        */
        CREATE POLICY tenant_delete_policy
        ON {db_schema}.{table_name} FOR DELETE
        USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


class TenantRLSSQL(RLSSQL):
    select_policy: Callable = tenant_select_policy_sql
    insert_policy: Callable = tenant_insert_policy_sql
    update_policy: Callable = tenant_update_policy_sql
    delete_policy: Callable = tenant_delete_policy_sql


def admin_select_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
        */
        CREATE POLICY admin_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def admin_insert_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to insert a record;
            Tenant Admin users to insert a record associated with their tenant;
        */
        CREATE POLICY admin_insert_policy
        ON {db_schema}.{table_name} FOR INSERT
        WITH CHECK (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def admin_update_policy_sql(table_name):
    return SQL(
        """
        /* 
        The policy to allow:
            Superusers to update all records;
            Tenant Admin users to update all records associated with their tenant;
        */
        CREATE POLICY admin_update_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
    )


def admin_delete_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to delete all records;
            Tenant Admin users to delete all records associated with their tenant;
        */
        CREATE POLICY user_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            )
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


class AdminRLSSQL(RLSSQL):
    select_policy: Callable = admin_select_policy_sql
    insert_policy: Callable = admin_insert_policy_sql
    update_policy: Callable = admin_update_policy_sql
    delete_policy: Callable = admin_delete_policy_sql


def default_select_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
            Regular users to select only records associated with their Groups or that they own.;
        */
        CREATE POLICY user_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            ) OR
            (
                owned_by_id = current_setting('rls_var.user_id', true)::TEXT OR
                group_id IN (uno.permissible_groups('{db_schema}.{table_name}', 'SELECT')::TEXT[])
            )
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def default_insert_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
            Regular users to select only records associated with their Groups or that they own.;
        */
        CREATE POLICY user_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            ) OR
            (
                owned_by_id = current_setting('rls_var.user_id', true)::TEXT OR
                group_id IN (uno.permissible_groups('{db_schema}.{table_name}', 'INSERT')::TEXT[])
            )
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def default_update_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
            Regular users to select only records associated with their Groups or that they own.;
        */
        CREATE POLICY user_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            ) OR
            (
                owned_by_id = current_setting('rls_var.user_id', true)::TEXT OR
                group_id IN (uno.permissible_groups('{db_schema}.{table_name}', 'UPDATE')::TEXT[])
            )
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def default_delete_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to select all records;
            Tenant Admin users to select all records associated with their tenant;
            Regular users to select only records associated with their Groups or that they own.;
        */
        CREATE POLICY user_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (
            current_setting('rls_var.is_superuser', true)::BOOLEAN OR
            (
                current_setting('rls_var.is_tenant_admin', true)::BOOLEAN AND
                tenant_id = current_setting('rls_var.tenant_id', true)::TEXT
            ) OR
            (
                owned_by_id = current_setting('rls_var.user_id', true)::TEXT OR
                group_id IN (uno.permissible_groups('{db_schema}.{table_name}', 'DELETE')::TEXT[])
            )
        );
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


class DefaultRLSSQL(RLSSQL):
    select_policy: Callable = default_select_policy_sql
    insert_policy: Callable = default_insert_policy_sql
    update_policy: Callable = default_update_policy_sql
    delete_policy: Callable = default_delete_policy_sql


def superuser_select_policy_sql(table_name):
    return SQL(
        """
        /* 
        The policy to allow:
            Superusers to select all records;
        */
        CREATE POLICY tenant_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
    )


def superuser_insert_policy_sql(table_name) -> str:
    return (
        SQL(
            """
        /*
        The policy to allow:
            Superusers to insert records;
        */
        CREATE POLICY tenant_insert_policy
        ON {db_schema}.{table_name} FOR INSERT
        WITH CHECK (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def superuser_update_policy_sql(table_name) -> str:
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to update records;
        */
        CREATE POLICY tenant_update_policy
        ON {db_schema}.{table_name} FOR UPDATE
        USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


def superuser_delete_policy_sql(table_name) -> str:
    return (
        SQL(
            """
        /* 
        The policy to allow:
            Superusers to delete records;
        */
        CREATE POLICY tenant_delete_policy
        ON {db_schema}.{table_name} FOR DELETE
        USING (current_setting('rls_var.is_superuser', true)::BOOLEAN);
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


class SuperuserRLSSQL(RLSSQL):
    select_policy: Callable = superuser_select_policy_sql
    insert_policy: Callable = superuser_insert_policy_sql
    update_policy: Callable = superuser_update_policy_sql
    delete_policy: Callable = superuser_delete_policy_sql


def public_select_policy_sql(table_name):
    return (
        SQL(
            """
        /* 
        The policy to allow:
            All users to select all records;
        */
        CREATE POLICY tenant_select_policy
        ON {db_schema}.{table_name} FOR SELECT
        USING (true);
        """
        )
        .format(db_schema=DB_SCHEMA, table_name=SQL(table_name))
        .as_string()
    )


class PublicReadSuperuserWriteRLSSQL(RLSSQL):
    select_policy: Callable = public_select_policy_sql
    insert_policy: Callable = superuser_insert_policy_sql
    update_policy: Callable = superuser_update_policy_sql
    delete_policy: Callable = superuser_delete_policy_sql
