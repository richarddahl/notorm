# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import sys
import io
import importlib
import asyncio

from typing import AsyncGenerator

from psycopg.sql import SQL

from sqlalchemy import insert, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from fastapi import FastAPI

from uno.record.sql.sql_emitters import (
    SetRole,
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    GrantPrivilegesAndSetSearchPaths,
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
    async def create_db(self) -> None:
        # Redirect the stdout stream to a StringIO object when running tests
        # to prevent the print statements from being displayed in the test output.
        if settings.ENV == "test":
            output_stream = io.StringIO()
            # sys.stdout = output_stream
        await self.drop_db()
        await self.create_roles_and_database()
        await self.create_schemas_and_extensions()
        await self.set_privileges_and_paths()
        await self.create_functions_triggers_and_tables()
        await self.emit_table_sql()

        print(f"Database created: {settings.DB_NAME}\n")

        # Reset the stdout stream
        if settings.ENV == "test":
            sys.stdout = sys.__stdout__

    async def create_roles_and_database(self) -> None:

        engine = self.engine(
            db_role="postgres", db_password="postgreSQLR0ck%", db_name="postgres"
        )
        # with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        async with engine.connect() as conn:
            await conn.execute(text("SET ROLE postgres;"))
            CreateRolesAndDatabase().emit_sql(conn)
        print("Created the roles and the database\n")
        # conn.close()
        # eng.dispose()

    async def create_schemas_and_extensions(self) -> None:
        conn = await self.engine(db_role="postgres")
        # with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        CreateSchemasAndExtensions().emit_sql(conn)
        print("Created the schemas and extensions\n")
        # conn.close()
        # eng.dispose()

    async def set_privileges_and_paths(self) -> None:
        eng = await self.engine(db_role="postgres")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            GrantPrivilegesAndSetSearchPaths().emit_sql(conn)
            print("Configured the privileges set the search paths\n")
            conn.close()
        # eng.dispose()

    async def create_functions_triggers_and_tables(self) -> None:
        eng = await self.engine(db_role=f"{settings.DB_NAME}_login")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateTokenSecret().emit_sql(conn)
            print("Created the token_secret table\n")

            CreatePGULID().emit_sql(conn)
            print("Created the pgulid function\n")

            self.create_tables_functions_and_privileges(conn)

            conn.close()
        eng.dispose()

    async def create_tables_functions_and_privileges(self, conn) -> None:
        meta_data.create_all(bind=conn)
        print("Created the database tables\n")

        GrantPrivileges().emit_sql(conn)
        print("Set the table privileges\n")

        InsertMetaRecordFunction().emit_sql(conn)
        print("Created the insert_meta function\n")

    async def emit_table_sql(self) -> None:
        # Connect to the new database to emit the table specific SQL
        eng = await self.engine(db_role=f"{settings.DB_NAME}_login")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Must emit the sql for the meta type table first
            # So that the triggger function can be fired each time
            # a new table is created to add the corresponding permissions
            # and graph nodes, graph_edges, and properties as well as thier
            # corresponding Filter Records

            # The ordering of these operations are important

            meta_storage = UnoStorage.registry["MetaTypeStorage"]
            meta_storage().emit_sql(conn)
            for storage in UnoStorage.registry.values():
                if storage.__name__ == "MetaTypeStorage":
                    continue
                print(f"Emitting SQL for the table: {storage.__name__}")
                storage().emit_sql(conn)
            return

            for base in Base.registry.mappers:
                SetRole().emit_sql(conn, "admin")

                # Emit the SQL to create the graph property filters
                for property in base.class_.graph_properties.values():
                    property.emit_sql(conn)

                # Emit the SQL to create the graph graph_node
                if base.class_.graph_node:
                    base.class_.graph_node.emit_sql(conn)

                conn.commit()
            for base in Base.registry.mappers:
                print(f"Created the graph_edges for: {base.class_.__tablename__}")
                for edge in base.class_.graph_edges.values():
                    edge.emit_sql(conn)
                conn.commit()

            conn.close()
        eng.dispose()

    async def drop_db(self) -> None:

        # Redirect the stdout stream to a StringIO object when running tests
        # to prevent the print statements from being displayed in the test output.
        if settings.ENV == "test":
            output_stream = io.StringIO()
            sys.stdout = output_stream

        # Connect to the postgres database as the postgres user
        eng = self.engine(db_role="postgres", db_name="postgres")
        with eng.connect() as conn:
            print(
                f"\nDropping the db: {settings.DB_NAME} and all the roles for the application\n"
            )
            # Drop the Database
            DropDatabaseAndRoles().emit_sql(conn)
            print(f"Database {settings.DB_NAME} and all assocated roles dropped\n")

        # eng = self.engine(db_role="postgres", db_name="postgres")
        # with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        #    print(
        #        f"\nDropping the db: {settings.DB_NAME} and all the roles for the application\n"
        #    )
        #    # Drop the Database
        #    DropDatabaseAndRoles().emit_sql(eng)

        #
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
        db_driver: str = settings.DB_ASYNC_DRIVER,
        db_password: str = settings.DB_USER_PW,
        db_host: str = settings.DB_HOST,
        db_name: str = settings.DB_NAME,
    ) -> AsyncEngine:

        engine = create_async_engine(
            f"{db_driver}://{db_role}:{db_password}@{db_host}/{db_name}",
        )
        return engine
