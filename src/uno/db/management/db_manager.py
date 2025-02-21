# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import sys
import io

from psycopg.sql import SQL, Literal

from sqlalchemy import text, create_engine, Engine

from fastapi import FastAPI

from uno.db.sql.sql_emitter import (
    DB_SCHEMA,
)

from uno.db.management.sql_emitters import (
    SetRole,
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    GrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    InsertMetaFunction,
)
from uno.auth.sql_emitters import (
    AlterTablesBeforeInsertFirstUser,
    UpdateRecordOfFirstUser,
    AlterTablesAfterInsertFirstUser,
)


from uno.db.tables import Base, MetaType

import uno.attr.tables as attrs_tables
import uno.auth.tables as auth_tables
import uno.msg.tables as msgs_tables
import uno.fltr.tables as fltrs_tables
import uno.rprt.tables as rprts_tables
import uno.val.tables as vals_tables
import uno.wkflw.tables as wrkflws_tables

from uno.config import settings


tags_metadata = [
    {
        "name": "0KUI",
        "description": "Zero Knowledge User Interface.",
        "externalDocs": {
            "description": "uno 0kui docs",
            "url": "http://localhost:8001/okui/",
        },
    },
    {
        "name": "auth",
        "description": "Manage Users, Roles, Groups etc...",
        "externalDocs": {
            "description": "uno auth docs",
            "url": "http://localhost:8001/auth/models",
        },
    },
]
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
            CreateRolesAndDatabase().emit_sql(conn)
            print("Created the roles and the database\n")
            conn.close()
        eng.dispose()

    def create_schemas_and_extensions(self) -> None:
        eng = self.engine(db_role="postgres")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            CreateSchemasAndExtensions().emit_sql(conn)
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
        Base.metadata.create_all(bind=conn)
        print("Created the database tables\n")

        GrantPrivileges().emit_sql(conn)
        print("Set the table privileges\n")

        InsertMetaFunction().emit_sql(conn)
        print("Created the insert_meta function\n")

    def emit_table_sql(self) -> None:
        # Connect to the new database to emit the table specific SQL
        eng = self.engine(db_role=f"{settings.DB_NAME}_login")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Must emit the sql for the object type table first
            # So that the triggger function can be fired each time
            # a new table is created to add the corresponding permissions
            # and graph nodes, edges, and properties as well as thier
            # corresponding Filter Records

            # The ordering of these operations are important

            SetRole().emit_sql(conn, "admin")
            MetaType.emit_sql(conn)

            for base in Base.registry.mappers:
                if base.class_.__name__ == MetaType:
                    continue  # Already emitted above
                print(f"Created the table: {base.class_.__tablename__}\n")
                SetRole().emit_sql(conn, "admin")
                # Emit the SQL for the table
                base.class_.emit_sql(conn)

            for base in Base.registry.mappers:
                base.class_.configure_base(app)
                SetRole().emit_sql(conn, "admin")

                # Emit the SQL to create the graph property filters
                for property in base.class_.graph_properties.values():
                    property.emit_sql(conn)

                # Emit the SQL to create the graph node
                if base.class_.node:
                    base.class_.node.emit_sql(conn)

                conn.commit()
            for base in Base.registry.mappers:
                if not base.class_.include_in_graph:
                    continue
                print(f"Created the edges for: {base.class_.__tablename__}")
                for edge in base.class_.edges.values():
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
        """
        Generates an SQL statement to create a new user in the database.

        Args:
            email (str): The email address of the user.
            handle (str): The handle or username of the user.
            full_name (str): The full name of the user.
            is_superuser (bool): A flag indicating if the user is a superuser.

        Returns:
            str: The SQL statement to insert a new user into the database.
        """
        return (
            SQL(
                """
            /*
            Creates the superuser for the application.
            */
            INSERT INTO {schema}.user (email, handle, full_name, is_superuser)
            VALUES({email}, {handle}, {full_name}, {is_superuser})
            RETURNING id;
            """
            )
            .format(
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
        """Create a new user in the database.

        This method creates a new user with specified details, performing necessary table alterations
        before and after the user creation. It uses a specific database role for login operations.

        Args:
            email (str, optional): User's email address. Defaults to settings.SUPERUSER_EMAIL.
            handle (str, optional): User's handle/username. Defaults to settings.SUPERUSER_HANDLE.
            full_name (str, optional): User's full name. Defaults to settings.SUPERUSER_FULL_NAME.
            is_superuser (bool, optional): Flag indicating if user is a superuser. Defaults to False.

        Returns:
            str: The ID of the newly created user.

        Note:
            This method performs database operations in AUTOCOMMIT isolation level and
            includes pre and post user creation table alterations:
                Disables Row Level Security (RLS) for the user table.
                Drops NOT NULL constraints on the meta created_by_id and modified_by_id columns.
                Inserts the new user into the user table.
                Updates the meta record of the first user.
                Enables Row Level Security (RLS) for the user table.
                Sets the NOT NULL constraints on the meta created_by_id and modified_by_id columns.
            Returns the ID of the newly created user.
        """
        eng = self.engine(db_role=f"{settings.DB_NAME}_login")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            AlterTablesBeforeInsertFirstUser().emit_sql(conn)
            superuser = conn.execute(
                text(self.create_user_sql(email, handle, full_name, is_superuser))
            )
            superuser_id = superuser.scalar()
            UpdateRecordOfFirstUser().emit_sql(conn, superuser_id)
            AlterTablesAfterInsertFirstUser().emit_sql(conn)
            conn.close()
        eng.dispose()
        return superuser_id

    def engine(
        self,
        db_role: str,
        db_driver: str = settings.DB_DRIVER,
        db_password: str = settings.DB_USER_PW,
        db_host: str = settings.DB_HOST,
        db_name: str = settings.DB_NAME,
    ) -> Engine:
        """
        Creates a SQLAlchemy engine instance.

        Args:
            db_role (str): The role of the database user.
            db_driver (str, optional): The database driver to use. Defaults to settings.DB_DRIVER.
            db_password (str, optional): The password for the database user. Defaults to settings.DB_USER_PW.
            db_host (str, optional): The host of the database. Defaults to settings.DB_HOST.
            db_name (str, optional): The name of the database. Defaults to settings.DB_NAME.

        Returns:
            Engine: A SQLAlchemy Engine instance.
        """
        return create_engine(
            f"{db_driver}://{db_role}:{db_password}@{db_host}/{db_name}"
        )
