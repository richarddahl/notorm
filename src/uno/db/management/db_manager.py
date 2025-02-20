# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import sys
import io

from psycopg.sql import SQL, Literal

from sqlalchemy import text, create_engine, Engine

from fastapi import FastAPI

from uno.db.sql_emitters import (
    SetRoleSQL,
    DB_SCHEMA,
)

from uno.db.management.sql_emitters import (
    DropDatabaseSQL,
    DropRolesSQL,
    CreateRolesSQL,
    CreateDatabaseSQL,
    CreateSchemasAndExtensionsSQL,
    PrivilegeAndSearchPathSQL,
    PGULIDSQLSQL,
    CreateTokenSecretSQL,
    TablePrivilegeSQL,
    InsertMetaFunctionSQL,
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

        self.create_roles_and_db()
        self.create_schemas_extensions_and_tables()
        self.create_auth_functions_and_triggers()

        # Connect to the new database to create the Graph functions and triggers
        eng = self.engine(db_role=f"{settings.DB_NAME}_login")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Must emit the sql for the object type table first
            # So that the triggger function can be fired each time
            # a new table is created to add the corresponding permissions
            # and graph nodes, edges, and properties as well as thier
            # corresponding Filter Records

            # The ordering of these operations are important

            SetRoleSQL().emit_sql(conn, "admin")
            MetaType.emit_sql(conn)

            for base in Base.registry.mappers:
                if base.class_.__name__ == MetaType:
                    continue  # Already emitted above
                print(f"Creating the table: {base.class_.__tablename__}\n")
                SetRoleSQL().emit_sql(conn, "admin")
                # Emit the SQL for the table
                for sql_emitter in base.class_.sql_emitters:
                    sql_emitter(table_name=base.class_.__tablename__).emit_sql(conn)

            for base in Base.registry.mappers:
                base.class_.configure_base(app)
                SetRoleSQL().emit_sql(conn, "admin")

                # Emit the SQL to create the graph property filters
                for property in base.class_.graph_properties.values():
                    property.emit_sql(conn)

                # Emit the SQL to create the graph node
                if base.class_.graph_node:
                    base.class_.graph_node.emit_sql(conn)

                conn.commit()
            for base in Base.registry.mappers:
                if not base.class_.include_in_graph:
                    continue
                print(f"Creating the edges for: {base.class_.__tablename__}")
                for edge in base.class_.graph_edges.values():
                    edge.emit_sql(conn)
                conn.commit()

            # if base.class_.graph_node:
            #    base.class_.set_filters()
            #    print(f"Filters for {base.class_.__tablename__}")
            #    for filter in base.class_.filters.values():
            #        print(filter)
            #        print("")

            conn.close()
        eng.dispose()

        print(f"Database created: {settings.DB_NAME}\n")

        # Reset the stdout stream
        if settings.ENV == "test":
            sys.stdout = sys.__stdout__

    def drop_db(self) -> None:
        """
        Drops the database and all associated roles.

        This method connects to the PostgreSQL database as the 'postgres' user and
        performs the following actions:
        1. Drops the specified database.
        2. Drops all roles associated with the application.

        If the environment is set to 'test', the stdout stream is redirected to a
        StringIO object to prevent print statements from being displayed in the test
        output.

        After the operations are completed, the stdout stream is reset to its original
        state if it was redirected.

        Returns:
            None
        """
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
            DropDatabaseSQL().emit_sql(conn)
            print(f"Database dropped: {settings.DB_NAME} \n")
            DropRolesSQL().emit_sql(conn)
            print(f"All Roles dropped for database: {settings.DB_NAME} \n")
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
            UpdateRecordOfFirstUser(user_id=superuser_id).emit_sql(conn)
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

    def create_roles_and_db(self) -> None:
        """
        Creates roles and a database.

        This method establishes a connection to the PostgreSQL database using the provided
        engine configuration. It then executes SQL commands to create roles and a database
        as specified by the `CreateRolesSQL` and `CreateDatabaseSQL` classes.

        Steps performed:
        1. Connects to the PostgreSQL database with the role 'postgres'.
        2. Executes SQL to create roles.
        3. Executes SQL to create the database.
        4. Closes the connection and disposes of the engine.

        Note:
            The database connection is set to use the 'AUTOCOMMIT' isolation level.

        Raises:
            SQLAlchemyError: If there is an error executing the SQL commands.
        """
        eng = self.engine(
            db_role="postgres", db_password="postgreSQLR0ck%", db_name="postgres"
        )
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print(
                f"\nCreating the db: {settings.DB_NAME}, and roles, users, and app schema.\n"
            )
            print("Creating the roles and the database\n")
            CreateRolesSQL().emit_sql(conn)
            CreateDatabaseSQL().emit_sql(conn)
            conn.close()
        eng.dispose()

    def create_schemas_extensions_and_tables(self) -> None:
        """
        Creates schemas, extensions, functions, triggers, and sets privileges and paths in the database.

        This method connects to the new database as the postgres user and performs the following actions:
        1. Creates the necessary schemas and extensions.
        2. Configures the privileges for the schemas.
        3. Sets the search paths for the schemas.

        The method uses an engine with AUTOCOMMIT isolation level to execute the SQL commands.
        """
        # Connect to the new database as the postgres user
        print("Connect to new db")
        print(
            "Create schemas, functions, and triggers, then set privileges and paths.\n"
        )
        eng = self.engine(db_role="postgres")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print("Creating the schemas and extensions\n")
            CreateSchemasAndExtensionsSQL().emit_sql(conn)

            print("Configuring the privileges for the schemas and setting the paths\n")
            PrivilegeAndSearchPathSQL().emit_sql(conn)

            conn.close()
        eng.dispose()

    def create_auth_functions_and_triggers(self) -> None:
        """
        Creates authentication functions and triggers in the database.

        This method performs the following actions:
        1. Connects to the database using a specific role.
        2. Creates the token_secret table, function, and trigger.
        3. Creates the pgulid function.
        4. Creates the necessary database tables.
        5. Sets the table privileges.

        The connection is established with AUTOCOMMIT isolation level to ensure
        that each command is executed immediately. After all operations are
        completed, the connection and engine are properly closed and disposed.

        Returns:
            None
        """
        # Connect to the new database to create the Auth functions and triggers
        eng = self.engine(db_role=f"{settings.DB_NAME}_login")
        with eng.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            print("Creating the token_secret table, function, and trigger\n")
            CreateTokenSecretSQL().emit_sql(conn)

            print("Creating the pgulid function\n")
            PGULIDSQLSQL().emit_sql(conn)

            # Create the tables
            self.create_tables(conn)

            conn.close()
        eng.dispose()

    def create_tables(self, conn) -> None:
        """
        Returns:
            None
        """
        # Connect to the new database to create the Auth functions and triggers
        # Create the tables
        print("Creating the database tables\n")

        Base.metadata.create_all(bind=conn)

        print("Setting the table privileges\n")
        TablePrivilegeSQL().emit_sql(conn)
        InsertMetaFunctionSQL().emit_sql(conn)
