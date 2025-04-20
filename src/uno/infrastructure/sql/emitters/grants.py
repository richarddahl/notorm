# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""SQL emitters for altering grants and permissions."""

from typing import List

from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement, SQLStatementType


class AlterGrants(SQLEmitter):
    """Emitter for altering grants on database objects.

    This emitter generates SQL statements for setting appropriate permissions
    on database tables and other objects.
    """

    def generate_sql(self) -> list[SQLStatement]:
        """Generate SQL statements for grants.

        Returns:
            List of SQL statements with metadata
        """
        statements = []

        if self.table is None:
            return statements

        # Get database schema and object information
        schema = self.connection_config.db_schema
        table_name = self.table.name

        # Generate grant statements
        admin_grants = self._generate_admin_grants(schema, table_name)
        writer_grants = self._generate_writer_grants(schema, table_name)
        reader_grants = self._generate_reader_grants(schema, table_name)

        # Create SQL statements with metadata
        statements.append(
            SQLStatement(
                name=f"{table_name}_admin_grants",
                type=SQLStatementType.GRANT,
                sql=admin_grants,
            )
        )

        statements.append(
            SQLStatement(
                name=f"{table_name}_writer_grants",
                type=SQLStatementType.GRANT,
                sql=writer_grants,
            )
        )

        statements.append(
            SQLStatement(
                name=f"{table_name}_reader_grants",
                type=SQLStatementType.GRANT,
                sql=reader_grants,
            )
        )

        return statements

    def _generate_admin_grants(self, schema: str, table_name: str) -> str:
        """Generate SQL for admin role grants.

        Args:
            schema: Database schema
            table_name: Table name

        Returns:
            SQL grant statement for admin role
        """
        admin_role = self.connection_config.admin_role

        return f"""
            GRANT ALL PRIVILEGES ON TABLE {schema}.{table_name} TO {admin_role};
            GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {schema} TO {admin_role};
        """

    def _generate_writer_grants(self, schema: str, table_name: str) -> str:
        """Generate SQL for writer role grants.

        Args:
            schema: Database schema
            table_name: Table name

        Returns:
            SQL grant statement for writer role
        """
        writer_role = self.connection_config.writer_role

        return f"""
            GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {schema}.{table_name} TO {writer_role};
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO {writer_role};
        """

    def _generate_reader_grants(self, schema: str, table_name: str) -> str:
        """Generate SQL for reader role grants.

        Args:
            schema: Database schema
            table_name: Table name

        Returns:
            SQL grant statement for reader role
        """
        reader_role = self.connection_config.reader_role

        return f"""
            GRANT SELECT ON TABLE {schema}.{table_name} TO {reader_role};
        """
