# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import sys
import io
import importlib

from psycopg.sql import SQL

from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from uno.record.sql.sql_statements import (
    SetRole,
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    RevokeAndGrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    InsertMetaRecordFunction,
)
from uno.record.record import meta_data
from uno.record.db import scoped_session
from uno.record.storage import UnoStorage
from uno.config import settings

# Import all the modules in the settings.LOAD_MODULES list
for module in settings.LOAD_MODULES:
    globals()[f"{module.split('.')[1]}_storage"] = importlib.import_module(
        f"{module}.storage"
    )

for module in settings.LOAD_MODULES:
    globals()[f"{module.split('.')[2]}_records"] = importlib.import_module(
        f"{module}.records"
    )


class DBManager:
    def create_db(self) -> None:
        # Redirect the stdout stream to a StringIO object when running tests
        # to prevent the print statements from being displayed in the test output.
        if settings.ENV == "test":
            output_stream = io.StringIO()
            # sys.stdout = output_stream
        self.drop_db()
        self.create_roles_and_database()
        self.create_schemas_and_extensions()
        self.set_privileges_and_paths()
        self.create_functions_triggers_and_tables()
        self.emit_table_sql()

        print(f"Database created: {settings.DB_NAME}\n")

        # Reset the stdout stream
        if settings.ENV == "test":
            sys.stdout = sys.__stdout__

    def create_roles_and_database(self) -> None:
        engine = self.engine(
            db_role="postgres",
            db_password="postgreSQLR0ck%",
            db_name="postgres",
        )
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateRolesAndDatabase().emit_sql(connection=conn)
            print("Created the roles and the database\n")
            conn.close()
        engine.dispose()

    def create_schemas_and_extensions(self) -> None:
        engine = self.engine(db_role="postgres")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateSchemasAndExtensions().emit_sql(connection=conn)
            print("Created the schemas and extensions\n")
            conn.close()
        engine.dispose()

    def set_privileges_and_paths(self) -> None:
        engine = self.engine(db_role="postgres")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            RevokeAndGrantPrivilegesAndSetSearchPaths().emit_sql(connection=conn)
            print("Configured the privileges set the search paths\n")
            conn.close()
        engine.dispose()

    def create_functions_triggers_and_tables(self) -> None:
        engine = self.engine(db_role=f"{settings.DB_NAME}_login")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateTokenSecret().emit_sql(connection=conn)
            print("Created the token_secret table\n")

            CreatePGULID().emit_sql(connection=conn)
            print("Created the pgulid function\n")

            self.create_tables_functions_and_privileges(conn)
            conn.close()
        engine.dispose()

    def create_tables_functions_and_privileges(self, conn) -> None:
        meta_data.create_all(bind=conn)
        print("Created the database tables\n")

        GrantPrivileges().emit_sql(connection=conn)
        print("Set the table privileges\n")

        InsertMetaRecordFunction().emit_sql(connection=conn)
        print("Created the insert_meta function\n")

    def emit_table_sql(self) -> None:
        # Connect to the new database to emit the table specific SQL
        engine = self.engine(db_role=f"{settings.DB_NAME}_login")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Must emit the sql for the meta type table first
            # So that the triggger function can be fired each time
            # a new table is created to add the corresponding permissions
            # and graph nodes, graph_edges, and properties as well as thier
            # corresponding Filter Records

            # The ordering of these operations are important

            meta_type_storage = UnoStorage.registry["MetaTypeStorage"]()
            for sql_emitter in meta_type_storage.emit_sql():
                sql_emitter(table_name="meta_type").emit_sql(connection=conn)
            for storage in UnoStorage.registry.values():
                storage = storage()
                if storage.table_name == "meta_type":
                    continue
                print(f"Emitting SQL for the table: {storage.table_name}")
                for sql_emitter in storage.emit_sql():
                    sql_emitter(table_name=storage.table_name).emit_sql(connection=conn)
            conn.close()
        engine.dispose()
        return

    def do_later(self) -> None:
        if 1 == 1:

            for base in Base.registry.mappers:
                SetRole().emit_sql(conn, "admin")

                # Emit the SQL to create the graph property filters
                for property in base.class_.graph_properties.values():
                    property.emit_sql()

                # Emit the SQL to create the graph graph_node
                if base.class_.graph_node:
                    base.class_.graph_node.emit_sql()

                conn.commit()
            for base in Base.registry.mappers:
                print(f"Created the graph_edges for: {base.class_.__tablename__}")
                for edge in base.class_.graph_edges.values():
                    edge.emit_sql()
                conn.commit()

            conn.close()
        eng.dispose()

    def drop_db(self) -> None:
        # Redirect the stdout stream to a StringIO object when running tests
        # to prevent the print statements from being displayed in the test output.
        if settings.ENV == "test":
            output_stream = io.StringIO()
            sys.stdout = output_stream

        # Connect to the postgres database as the postgres user
        engine = self.engine(db_role="postgres", db_name="postgres")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print(
                f"\nDropping the db: {settings.DB_NAME} and all the roles for the application\n"
            )
            # Drop the Database
            DropDatabaseAndRoles().emit_sql(connection=conn)
            print("Dropped the database and the roles associated with it\n")
        engine.dispose()

        # Reset the stdout stream
        if settings.ENV == "test":
            sys.stdout = sys.__stdout__

    async def create_superuser(
        self,
        email: str = settings.SUPERUSER_EMAIL,
        handle: str = settings.SUPERUSER_HANDLE,
        full_name: str = settings.SUPERUSER_FULL_NAME,
    ) -> str:
        user = auth_records.UserRecord(
            email=email,
            handle=handle,
            full_name=full_name,
            is_superuser=True,
        )
        async with scoped_session() as session:
            await session.execute(
                text(
                    SQL("SET ROLE {db_name}_admin;")
                    .format(
                        db_name=SQL(settings.DB_NAME),
                    )
                    .as_string()
                )
            )
            session.add(user)
            await session.commit()
            await session.close()
        return user

    def engine(
        self,
        db_role: str,
        db_driver: str = settings.DB_SYNC_DRIVER,
        db_password: str = settings.DB_USER_PW,
        db_host: str = settings.DB_HOST,
        db_name: str = settings.DB_NAME,
    ) -> AsyncEngine:

        engine = create_engine(
            f"{db_driver}://{db_role}:{db_password}@{db_host}/{db_name}",
        )
        return engine
