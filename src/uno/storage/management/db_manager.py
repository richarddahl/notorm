# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import sys
import io
import importlib

from sqlalchemy import create_engine, Engine, insert

from fastapi import FastAPI

from uno.storage.management.sql_emitters import (
    SetRole,
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    InsertSchemasAndExtensions,
    GrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    InsertMetaRecordFunction,
)
from uno.record.record import meta_data, UnoRecord
from uno.apps.meta.models import MetaType
from uno.api.app import app
from uno.config import settings

# Import all the modules in the settings.LOAD_MODULES list
for module in settings.LOAD_MODULES:
    globals()[f"{module.split('.')[1]}_records"] = importlib.import_module(
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

        eng = self.engine(
            db_role="postgres", db_password="postgreSQLR0ck%", db_name="postgres"
        )
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateRolesAndDatabase()._emit_sql(conn)
            print("Created the roles and the database\n")
            conn.close()
        eng.dispose()

    def create_schemas_and_extensions(self) -> None:
        eng = self.engine(db_role="postgres")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            InsertSchemasAndExtensions()._emit_sql(conn)
            print("Created the schemas and extensions\n")
            conn.close()
        eng.dispose()

    def set_privileges_and_paths(self) -> None:
        eng = self.engine(db_role="postgres")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            GrantPrivilegesAndSetSearchPaths()._emit_sql(conn)
            print("Configured the privileges set the search paths\n")
            conn.close()
        eng.dispose()

    def create_functions_triggers_and_tables(self) -> None:
        eng = self.engine(db_role=f"{settings.DB_NAME}_login")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateTokenSecret()._emit_sql(conn)
            print("Created the token_secret table\n")

            CreatePGULID()._emit_sql(conn)
            print("Created the pgulid function\n")

            self.create_tables_functions_and_privileges(conn)

            conn.close()
        eng.dispose()

    def create_tables_functions_and_privileges(self, conn) -> None:
        # Base.metadata.create_all(bind=conn)
        meta_data.create_all(bind=conn)
        print("Created the database tables\n")

        GrantPrivileges()._emit_sql(conn)
        print("Set the table privileges\n")

        InsertMetaRecordFunction()._emit_sql(conn)
        print("Created the insert_meta function\n")

    def emit_table_sql(self) -> None:
        # Connect to the new database to emit the table specific SQL
        eng = self.engine(db_role=f"{settings.DB_NAME}_login")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Must emit the sql for the object type table first
            # So that the triggger function can be fired each time
            # a new table is created to add the corresponding permissions
            # and graph nodes, graph_edges, and properties as well as thier
            # corresponding Filter Records

            # The ordering of these operations are important

            MetaType.configure()
            SetRole()._emit_sql(conn, "admin")
            MetaType._emit_sql(conn)

            for uno in UnoRecord.registry.values():
                if issubclass(uno, MetaType):
                    continue  # Already emitted above
                uno.configure(alter_db=True)
                SetRole()._emit_sql(conn, "admin")
                # Emit the SQL for the table
                uno._emit_sql(conn)
            return

            for base in Base.registry.mappers:
                SetRole()._emit_sql(conn, "admin")

                # Emit the SQL to create the graph property filters
                for property in base.class_.graph_properties.values():
                    property._emit_sql(conn)

                # Emit the SQL to create the graph graph_node
                if base.class_.graph_node:
                    base.class_.graph_node._emit_sql(conn)

                conn.commit()
            for base in Base.registry.mappers:
                print(f"Created the graph_edges for: {base.class_.__tablename__}")
                for edge in base.class_.graph_edges.values():
                    edge._emit_sql(conn)
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
        eng = self.engine(db_role="postgres", db_name="postgres")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print(
                f"\nDropping the db: {settings.DB_NAME} and all the roles for the application\n"
            )
            # Drop the Database
            DropDatabaseAndRoles()._emit_sql(conn)
            print(f"Database {settings.DB_NAME} and all assocated roles dropped\n")
            conn.close()
        eng.dispose()

        # Reset the stdout stream
        if settings.ENV == "test":
            sys.stdout = sys.__stdout__

    async def create_superuser(
        self,
        email: str = settings.SUPERUSER_EMAIL,
        handle: str = settings.SUPERUSER_HANDLE,
        full_name: str = settings.SUPERUSER_FULL_NAME,
    ) -> str:
        user = auth_models.User(
            email=email,
            handle=handle,
            full_name=full_name,
            is_superuser=True,
        )
        await user.save()
        return user

    def engine(
        self,
        db_role: str,
        db_sync_driver: str = settings.DB_SYNC_DRIVER,
        db_password: str = settings.DB_USER_PW,
        db_host: str = settings.DB_HOST,
        db_name: str = settings.DB_NAME,
    ) -> Engine:

        return create_engine(
            f"{db_sync_driver}://{db_role}:{db_password}@{db_host}/{db_name}"
        )
