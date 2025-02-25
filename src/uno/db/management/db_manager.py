# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import sys
import io
import importlib

from psycopg.sql import SQL, Literal

from sqlalchemy import text, create_engine, Engine, func, select, insert

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.asyncio import create_async_engine

from fastapi import FastAPI

from uno.db.sql.sql_emitter import DB_SCHEMA, WRITER_ROLE, ADMIN_ROLE
from uno.db.management.sql_emitters import (
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
from uno.auth.sql_emitters import (
    AlterTablesBeforeInsertFirstUser,
    UpdateRecordOfFirstUser,
    AlterTablesAfterInsertFirstUser,
)
from uno.db.obj import meta_data, UnoObj
from uno.meta.objs import MetaType
from uno.app.tags import tags_metadata
from uno.config import settings

for module in settings.LOAD_MODULES:
    importlib.import_module(module) as f"{module}_objs"


app = FastAPI(
    openapi_tags=tags_metadata,
    title="Uno is not an ORM",
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
        eng.dispose()
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateRolesAndDatabase().emit_sql(conn)
            print("Created the roles and the database\n")
            conn.close()
        eng.dispose()

    def create_schemas_and_extensions(self) -> None:
        eng = self.engine(db_role="postgres")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            InsertSchemasAndExtensions().emit_sql(conn)
            print("Created the schemas and extensions\n")
            conn.close()
        eng.dispose()

    def set_privileges_and_paths(self) -> None:
        eng = self.engine(db_role="postgres")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            GrantPrivilegesAndSetSearchPaths().emit_sql(conn)
            print("Configured the privileges set the search paths\n")
            conn.close()
        eng.dispose()

    def create_functions_triggers_and_tables(self) -> None:
        eng = self.engine(db_role=f"{settings.DB_NAME}_login")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateTokenSecret().emit_sql(conn)
            print("Created the token_secret table\n")

            CreatePGULID().emit_sql(conn)
            print("Created the pgulid function\n")

            self.create_tables_functions_and_privileges(conn)

            conn.close()
        eng.dispose()

    def create_tables_functions_and_privileges(self, conn) -> None:
        # Base.metadata.create_all(bind=conn)
        meta_data.create_all(bind=conn)
        print("Created the database tables\n")

        GrantPrivileges().emit_sql(conn)
        print("Set the table privileges\n")

        InsertMetaRecordFunction().emit_sql(conn)
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

            SetRole().emit_sql(conn, "admin")
            MetaType.emit_sql(conn)

            for uno in UnoObj.registry.values():
                if issubclass(uno, MetaType):
                    continue  # Already emitted above
                SetRole().emit_sql(conn, "admin")
                # Emit the SQL for the table
                uno.emit_sql(conn)
                uno.configure_base(app)
            return

            for base in Base.registry.mappers:
                base.class_.configure_base(app)
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
            DropDatabaseAndRoles().emit_sql(conn)
            print(f"Database {settings.DB_NAME} and all assocated roles dropped\n")
            conn.close()
        eng.dispose()

        # Reset the stdout stream
        if settings.ENV == "test":
            sys.stdout = sys.__stdout__

    def create_user_sql(
        self,
        email: str,
        handle: str,
        full_name: str,
        is_superuser: bool,
    ) -> str:

        return (
            SQL(
                """
            /*
            Creates the superuser for the application.
            */
            SET ROLE {admin_role};

            INSERT INTO {schema}.user (email, handle, full_name, is_superuser)
            VALUES({email}, {handle}, {full_name}, {is_superuser})
            RETURNING id;
            """
            )
            .format(
                admin_role=ADMIN_ROLE,
                schema=DB_SCHEMA,
                email=Literal(email),
                handle=Literal(handle),
                full_name=Literal(full_name),
                is_superuser=Literal(is_superuser),
            )
            .as_string()
        )

    def create_user(
        self,
        email: str = settings.SUPERUSER_EMAIL,
        handle: str = settings.SUPERUSER_HANDLE,
        full_name: str = settings.SUPERUSER_FULL_NAME,
        is_superuser: bool = False,
    ) -> str:
        eng = self.engine(db_role=f"{settings.DB_NAME}_login")
        # with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        user = auth_objs.User(
            email=email,
            handle=handle,
            full_name=full_name,
            is_superuser=True,
        )
        user_insert = user.insert_schema(**user.model_dump())
        with eng.connect() as conn:
            AlterTablesBeforeInsertFirstUser().emit_sql(conn)
            result = conn.execute(
                insert(user.db.db_table)
                .values(**user_insert.model_dump())
                .returning(user.db.db_table.c.id)
            )
            user_id = result.scalar()
            print(f"Created the superuser: {user_id}\n")
            conn.commit()

            AlterTablesAfterInsertFirstUser().emit_sql(conn)
            conn.close()
        eng.dispose()
        return user_id

    def engine(
        self,
        db_role: str,
        db_driver: str = settings.DB_DRIVER,
        db_password: str = settings.DB_USER_PW,
        db_host: str = settings.DB_HOST,
        db_name: str = settings.DB_NAME,
    ) -> Engine:

        return create_engine(
            f"{db_driver}://{db_role}:{db_password}@{db_host}/{db_name}"
        )
