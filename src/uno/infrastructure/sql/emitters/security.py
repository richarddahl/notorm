# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL emitters for security-related operations including Row-Level Security."""

import textwrap
from typing import List

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType
from uno.sql.builders import SQLFunctionBuilder


class RowLevelSecurity(SQLEmitter):
    """Base emitter for row-level security policies.

    This emitter generates SQL statements for enabling row-level security
    on a table and defining access policies.
    """

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for row-level security.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Generate enable RLS SQL
        admin_role = f"{self.config.DB_NAME}_admin"

        enable_rls_sql = textwrap.dedent(
            f"""
            -- Enable RLS for the table {self.table.name}
            SET ROLE {admin_role};
            ALTER TABLE {self.config.DB_SCHEMA}.{self.table.name} ENABLE ROW LEVEL SECURITY;
            """
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="enable_rls", type=SQLStatementType.FUNCTION, sql=enable_rls_sql
            )
        )

        # Generate force RLS SQL
        force_rls_sql = textwrap.dedent(
            f"""
            -- FORCE RLS for the table {self.table.name}
            SET ROLE {admin_role};
            ALTER TABLE {self.config.DB_SCHEMA}.{self.table.name} FORCE ROW LEVEL SECURITY;
            """
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="force_rls", type=SQLStatementType.FUNCTION, sql=force_rls_sql
            )
        )

        return statements


class UserRowLevelSecurity(RowLevelSecurity):
    """Emitter for user-specific row-level security policies.

    This emitter generates SQL statements for enabling row-level security
    on user tables and defining access policies for different operations.
    """

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for user row-level security.

        Returns:
            List of SQL statements with metadata
        """
        # Get base RLS statements
        statements = super().generate_sql()

        if self.table is None:
            return statements

        # Generate select policy SQL
        select_policy_sql = textwrap.dedent(
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

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="select_policy",
                type=SQLStatementType.FUNCTION,
                sql=select_policy_sql,
            )
        )

        # Generate insert policy SQL
        insert_policy_sql = textwrap.dedent(
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

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="insert_policy",
                type=SQLStatementType.FUNCTION,
                sql=insert_policy_sql,
            )
        )

        # Generate update policy SQL
        update_policy_sql = textwrap.dedent(
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

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="update_policy",
                type=SQLStatementType.FUNCTION,
                sql=update_policy_sql,
            )
        )

        # Generate delete policy SQL
        delete_policy_sql = textwrap.dedent(
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

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="delete_policy",
                type=SQLStatementType.FUNCTION,
                sql=delete_policy_sql,
            )
        )

        return statements


class CreateRLSFunctions(SQLEmitter):
    """Emitter for RLS authentication and authorization functions."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for RLS functions.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate authorize user function SQL
        db_name = self.config.DB_NAME
        schema_name = self.config.DB_SCHEMA
        admin_role = f"{db_name}_admin"

        # Use the function builder for the authorize_user function
        function_body = f"""
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
            SELECT secret FROM {schema_name}.token_secret INTO token_secret;

            -- Verify the token
            SELECT header, payload, valid
            FROM {schema_name}.verify(token, token_secret)
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
                FROM {schema_name}.user
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
        """

        authorize_user_sql = (
            SQLFunctionBuilder()
            .with_schema(schema_name)
            .with_name("authorize_user")
            .with_args("token TEXT, role_name TEXT DEFAULT 'reader'")
            .with_return_type("BOOLEAN")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="create_authorize_user_function",
                type=SQLStatementType.FUNCTION,
                sql=authorize_user_sql,
            )
        )

        # Generate permissible groups function SQL
        function_body = """
        DECLARE
            user_id TEXT;
        BEGIN
            user_id := current_setting('s_var.id', true);
            RETURN QUERY
            SELECT g.*
            FROM {schema_name}.group g
            JOIN {schema_name}.user__group__role ugr ON ugr.group_id = g.id
            JOIN {schema_name}.user u ON u.id = ugr.user_email
            JOIN {schema_name}.permission tp ON ugr.role_id = tp.id
            WHERE u.id = session_user_id AND tp.is_active = TRUE;
        END;
        """.format(
            schema_name=schema_name
        )

        permissible_groups_sql = (
            SQLFunctionBuilder()
            .with_schema(schema_name)
            .with_name("permissible_groups")
            .with_args("table_name TEXT, operation TEXT")
            .with_return_type(f"SETOF {schema_name}.group")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="permissible_groups",
                type=SQLStatementType.FUNCTION,
                sql=permissible_groups_sql,
            )
        )

        return statements


class GetPermissibleGroupsFunction(SQLEmitter):
    """Emitter for retrieving permissible groups based on user permissions."""

    def generate_sql(self) -> List[SQLStatement]:
        """Generate SQL statements for permissible groups function.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        # Generate select permissible groups function
        schema_name = self.config.DB_SCHEMA

        function_body = """
        DECLARE
            user_id TEXT := current_setting('rls_var.user_id', true)::TEXT;
            permissible_groups VARCHAR(26)[];
        BEGIN
            SELECT id
            FROM group g
            JOIN user__group__role ugr ON ugr.group_id = g.id AND ugr.user_id = user_id
            JOIN role on ugr.role_id = role.id
            JOIN role__permission rp ON rp.role_id = role.id
            JOIN permission p ON p.id = rp.permission_id
            JOIN meta_type mt ON mt.id = tp.meta_type_id
            WHERE mt.name = meta_type
            INTO permissible_groups;
            RETURN permissible_groups;
        END;
        """

        select_permissible_groups_sql = (
            SQLFunctionBuilder()
            .with_schema(schema_name)
            .with_name("select_permissible_groups")
            .with_args("meta_type TEXT")
            .with_return_type("VARCHAR[]")
            .with_body(function_body)
            .build()
        )

        # Add the statement to the list
        statements.append(
            SQLStatement(
                name="select_permissible_groups",
                type=SQLStatementType.FUNCTION,
                sql=select_permissible_groups_sql,
            )
        )

        return statements
