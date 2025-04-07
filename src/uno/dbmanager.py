# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import io
import sys
import contextlib

from sqlalchemy.engine import create_engine, Engine

from uno.sqlemitter import (
    SQLConfig,
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    RevokeAndGrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    InsertMetaRecordFunction,
    SetRole,
    MergeRecord,
)
from uno.obj import UnoObj
from uno.model import meta_data
from uno.auth.objects import User
from uno.meta.sqlconfigs import MetaTypeSQLConfig
from uno.filter import UnoFilter
from uno.qry.models import QueryPathModel
from uno.qry.objects import QueryPath
import uno.attr.sqlconfigs
import uno.auth.sqlconfigs
import uno.qry.sqlconfigs
import uno.meta.sqlconfigs
import uno.msg.sqlconfigs
import uno.rprt.sqlconfigs
import uno.val.sqlconfigs

# import uno.wkflw.sqlconfigs
from uno.attr import objects
from uno.auth import objects
from uno.qry import objects
from uno.meta import objects
from uno.msg import objects
from uno.rprt import objects
from uno.val import objects

# from uno.wkflw import models

from uno.utilities import import_from_path
from uno.config import settings


# Check if the application path is defined in the settings
if settings.APP_PATH:

    # Iterate over the list of packages specified in the settings
    for pkg in settings.LOAD_PACKAGES:
        # Construct the file path for the `models.py` file in the package
        file_path = f"{settings.APP_PATH}/{pkg.replace('.', '/')}/models.py"

        # Dynamically import the `models.py` file from the constructed path
        import_from_path(pkg, file_path)

        # Construct the file path for the `sqlconfigs.py` file in the package
        file_path = f"{settings.APP_PATH}/{pkg.replace('.', '/')}/sqlconfigs.py"

        # Dynamically import the `sqlconfigs.py` file from the constructed path
        import_from_path(pkg, file_path)


@contextlib.contextmanager
def supress_stdout():
    """
    Context manager to suppress stdout output.
    This context manager temporarily redirects the standard output (stdout)
    to a StringIO object, effectively suppressing any print statements
    within the context. After exiting the context, it restores the original
    stdout stream.
    Usage:
        with supress_stdout():
            # Code that generates output
            print("This will not be printed to the console.")
    """

    # Save the current stdout (standard output) stream
    save_stdout = sys.stdout

    # Redirect stdout to a StringIO object to suppress output
    sys.stdout = io.StringIO()

    # Yield control back to the caller (used in a context manager)
    yield

    # Restore the original stdout stream after the context manager exits
    sys.stdout = save_stdout


class DBManager:
    """
    DBManager is a class responsible for managing database operations, including
    creating, dropping, and configuring the database, as well as managing roles,
    schemas, extensions, privileges, functions, triggers, and tables. It also
    provides functionality for creating a superuser and managing query paths.

    Methods:
        create_db() -> None:
            Creates the database by invoking a series of setup methods. Redirects
            stdout during tests to suppress output.

        create_db_() -> None:
            Executes the full database creation process, including dropping the
            database, creating roles, schemas, extensions, privileges, functions,
            triggers, and tables, and emitting table-specific SQL.

        create_roles_and_database() -> None:
            Creates roles and the database using a connection with elevated
            privileges.

        create_schemas_and_extensions() -> None:
            Creates schemas and extensions in the database.

        set_privileges_and_paths() -> None:
            Configures privileges and search paths for the database.

        create_functions_triggers_and_tables() -> None:
            Creates database functions, triggers, and tables, and sets privileges.

        create_tables_functions_and_privileges(conn) -> None:
            Creates database tables, sets table privileges, and creates additional
            functions.

        emit_table_sql() -> None:
            Emits SQL for table-specific configurations, including meta types and
            other registered SQL configurations.

        drop_db() -> None:
            Drops the database and associated roles. Redirects stdout during tests
            to suppress output.

        drop_db_() -> None:
            Executes the database and role deletion process.

        engine(db_role: str, db_driver: str = settings.DB_SYNC_DRIVER,
               db_password: str = settings.DB_USER_PW, db_host: str = settings.DB_HOST,
               db_name: str = settings.DB_NAME) -> Engine:
            Creates and returns a SQLAlchemy engine for database connections.

        async create_superuser(email: str = settings.SUPERUSER_EMAIL,
                               full_name: str = settings.SUPERUSER_FULL_NAME) -> str:
            Asynchronously creates a superuser with elevated privileges.

        async create_query_paths() -> None:
            Asynchronously generates and persists query paths for database
            operations based on filters defined in the UnoObj registry.

    Helper Functions (within create_query_paths):
        add_query_path(filter: UnoFilter, parent: UnoFilter = None) -> QueryPathModel:

        process_filters(fltr: UnoFilter) -> None:
            Processes a hierarchy of filters and applies query paths for each
            filter.

    Attributes:
        None explicitly defined in the class, but relies on external settings
        such as `settings.DB_NAME`, `settings.ENV`, and others for configuration.
    """

    def create_db(self) -> None:
        """
        Creates the database based on the current environment.

        If the environment is set to "test", suppresses standard output
        while creating the database. Otherwise, creates the database
        with standard output enabled.

        Returns:
            None
        """
        if settings.ENV == "test":
            with supress_stdout():
                self.create_db_()
        else:
            self.create_db_()

    def create_db_(self) -> None:
        """
        Creates the database by performing a series of operations in sequence.

        This method performs the following steps:
        1. Drops the existing database, if any.
        2. Creates roles and the database.
        3. Creates schemas and installs necessary extensions.
        4. Sets privileges and configures paths.
        5. Creates functions, triggers, and tables.
        6. Emits the SQL for the created tables.

        Finally, it prints a confirmation message indicating the database creation.

        Returns:
            None
        """
        # Drop the existing database and associated roles, if any
        self.drop_db()

        # Create the necessary roles and the database
        self.create_roles_and_database()

        # Set up schemas and install required extensions in the database
        self.create_schemas_and_extensions()

        # Configure privileges and set search paths for the database
        self.set_privileges_and_paths()

        # Create database functions, triggers, and tables
        self.create_functions_triggers_and_tables()

        # Emit SQL for table-specific configurations and registered SQL configurations
        self.emit_table_sql()

        # Print a confirmation message indicating successful database creation
        print(f"Database created: {settings.DB_NAME}\n")

    def create_roles_and_database(self) -> None:
        """
        Creates roles and a database using the specified engine configuration.

        This method establishes a connection to the database engine with the
        provided credentials and emits SQL commands to create roles and a database.
        The connection is configured with an isolation level of "AUTOCOMMIT" to
        ensure immediate execution of the SQL commands.

        Steps:
        1. Initializes the database engine with the specified role, password, and database name.
        2. Opens a connection to the engine with "AUTOCOMMIT" isolation level.
        3. Executes the SQL commands to create roles and the database.
        4. Closes the connection and disposes of the engine.

        Note:
            - Ensure that the `CreateRolesAndDatabase` class is properly implemented
              to emit the required SQL commands.
            - The database credentials (role, password, and database name) should
              be securely managed and not hardcoded in production environments.

        Raises:
            Any exceptions raised during the connection or SQL execution process.

        Returns:
            None
        """
        # Create a database engine using the "postgres" role, a specified password, and the "postgres" database
        engine = self.engine(
            db_role="postgres",  # Role with elevated privileges to create roles and databases
            db_password="postgreSQLR0ck%",  # Password for the "postgres" role
            db_name="postgres",  # Connect to the default "postgres" database
        )

        # Establish a connection to the engine with "AUTOCOMMIT" isolation level
        # This ensures that SQL commands are executed immediately without requiring explicit commits
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Emit SQL commands to create roles and the database
            # The `CreateRolesAndDatabase` class is responsible for generating and executing these commands
            CreateRolesAndDatabase().emit_sql(connection=conn)

            # Print a confirmation message indicating that roles and the database have been created
            print("Created the roles and the database\n")

        # Dispose of the engine to release resources
        engine.dispose()

    def create_schemas_and_extensions(self) -> None:
        """
        Creates the necessary schemas and extensions in the database.

        This method establishes a connection to the database using the "postgres"
        role, sets the isolation level to "AUTOCOMMIT", and executes the SQL
        commands required to create schemas and extensions. After execution,
        the connection is closed, and the engine is disposed of.

        Raises:
            Any exceptions that occur during the execution of the SQL commands
            or database connection issues.
        """
        # Create a database engine using the "postgres" role
        engine = self.engine(db_role="postgres")

        # Establish a connection to the engine with "AUTOCOMMIT" isolation level
        # This ensures that SQL commands are executed immediately without requiring explicit commits
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Emit SQL commands to create schemas and extensions in the database
            # The `CreateSchemasAndExtensions` class is responsible for generating and executing these commands
            CreateSchemasAndExtensions().emit_sql(connection=conn)
            # Print a confirmation message indicating that schemas and extensions have been created
            print("Created the schemas and extensions\n")

            # Emit SQL commands create the set_role function
            SetRole().emit_sql(connection=conn)
            print("Created the set_role function\n")

            # Emit SQL commands to create the merge_record function
            MergeRecord().emit_sql(connection=conn)
            print("Created the merge_record function\n")

        # Dispose of the engine to release resources
        engine.dispose()

    def set_privileges_and_paths(self) -> None:
        """
        Configures database privileges and search paths for the PostgreSQL engine.

        This method establishes a connection to the database engine with the role
        "postgres" and executes SQL commands to revoke and grant privileges, as well
        as set the search paths. The connection is configured with an isolation level
        of "AUTOCOMMIT" to ensure immediate execution of the SQL commands. After the
        operations are completed, the connection and engine are properly closed and
        disposed of to release resources.

        Raises:
            Any exceptions raised during the database connection or SQL execution.
        """
        # Create a database engine with the role "postgres"
        engine = self.engine(db_role="postgres")

        # Open a connection with AUTOCOMMIT isolation level
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Execute SQL commands to configure privileges and search paths
            RevokeAndGrantPrivilegesAndSetSearchPaths().emit_sql(connection=conn)
            print("Configured the privileges set the search paths\n")

        # Dispose of the engine to release resources
        engine.dispose()

    def create_functions_triggers_and_tables(self) -> None:
        """
        Creates database functions, triggers, and tables required for the application.

        This method establishes a connection to the database engine with the specified
        role, executes SQL commands to create necessary database components, and ensures
        proper cleanup of resources.

        Steps performed:
        1. Connects to the database engine with the role defined by the login database name.
        2. Creates the `token_secret` table by emitting the corresponding SQL.
        3. Creates the `pgulid` function by emitting the corresponding SQL.
        4. Calls `create_tables_functions_and_privileges` to create additional tables,
           functions, and assign privileges.
        5. Closes the connection and disposes of the engine.

        Raises:
            Any exceptions raised during the execution of SQL commands or database
            connection issues.

        Returns:
            None
        """
        # Create a database engine using the login role for the current database
        engine = self.engine(db_role=f"{settings.DB_NAME}_login")

        # Establish a connection to the engine with "AUTOCOMMIT" isolation level
        # This ensures that SQL commands are executed immediately without requiring explicit commits
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Emit SQL commands to create the `token_secret` table
            CreateTokenSecret().emit_sql(connection=conn)
            print("Created the token_secret table\n")

            # Emit SQL commands to create the `pgulid` function
            CreatePGULID().emit_sql(connection=conn)
            print("Created the pgulid function\n")

            # Create additional tables, functions, and set privileges using the provided connection
            self.create_tables_functions_and_privileges(conn)

        # Dispose of the engine to release resources
        engine.dispose()

    def create_tables_functions_and_privileges(self, conn) -> None:
        """
        Creates database tables, sets table privileges, and defines a function for inserting metadata.

        This method performs the following actions:
        1. Creates all database tables using the provided connection.
        2. Grants necessary privileges on the tables.
        3. Creates a database function for inserting metadata records.

        Args:
            conn: The database connection object used to execute the operations.

        Returns:
            None
        """
        # Create all database tables defined in the metadata using the provided connection
        meta_data.create_all(bind=conn)
        print("Created the database tables\n")

        # Emit SQL commands to grant necessary privileges on the created tables
        GrantPrivileges().emit_sql(connection=conn)
        print("Set the table privileges\n")

        # Emit SQL commands to create a function for inserting metadata records
        InsertMetaRecordFunction().emit_sql(connection=conn)
        print("Created the insert_meta function\n")

    def emit_table_sql(self) -> None:
        """
        Emit SQL statements for creating and configuring database tables.

        This method connects to a database engine with a specific role and emits
        the necessary SQL statements for setting up tables and their associated
        configurations. It ensures that the SQL for the `MetaType` table is emitted
        first, as it is required for triggering functions that handle permissions
        for newly created tables.

        Steps:
        1. Connect to the database using the specified role with AUTOCOMMIT isolation level.
        2. Emit SQL for the `MetaType` table.
        3. Iterate through the registered SQL configurations and emit SQL for each,
           skipping the `MetaTypeSQLConfig` as it is already processed.
        4. Close the connection and dispose of the engine.

        Note:
        - The `MetaType` table must be processed first to ensure proper functionality
          of trigger functions.
        - The method uses the `SQLConfig.registry` to retrieve configurations for
          emitting SQL.

        Raises:
            Any exceptions raised during database connection or SQL execution.

        Returns:
            None
        """
        # Connect to the new database using the login role for the current database
        engine = self.engine(db_role=f"{settings.DB_NAME}_login")

        # Establish a connection to the engine with "AUTOCOMMIT" isolation level
        # This ensures that SQL commands are executed immediately without requiring explicit commits
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:

            # Emit SQL for the MetaType table first
            # The MetaType table must be processed first to ensure that the trigger function
            # is fired for adding permissions whenever a new table is created
            print("\nEmitting sql.SQL for: MetaType")
            MetaTypeSQLConfig.emit_sql(connection=conn)

            # Iterate through all registered SQL configurations in the SQLConfig registry
            for name, config in SQLConfig.registry.items():
                # Skip the MetaTypeSQLConfig since it has already been processed
                if name == "MetaTypeSQLConfig":
                    continue

                # Emit SQL for the current configuration and log its name
                print(f"\nEmitting sql.SQL for: {name}")
                config.emit_sql(connection=conn)

        # Dispose of the engine to release resources
        engine.dispose()

    def drop_db(self) -> None:
        """
        Drops the database by invoking the `drop_db_` method.

        If the environment is set to "test", suppresses standard output to avoid
        displaying print statements during testing. Otherwise, directly calls
        the `drop_db_` method.

        This method is intended to manage database teardown operations in
        different environments.

        Returns:
            None
        """
        # Check if the environment is set to "test"
        if settings.ENV == "test":
            # If in the "test" environment, suppress standard output
            # while dropping the database to avoid unnecessary print statements
            with supress_stdout():
                self.drop_db_()
        else:
            # If not in the "test" environment, drop the database normally
            # without suppressing standard output
            self.drop_db_()

    def drop_db_(self) -> None:
        """
        Drops the specified database and all associated roles.

        This method connects to the PostgreSQL database as the "postgres" user
        and executes the necessary SQL commands to drop the database and
        associated roles. It uses an engine with "AUTOCOMMIT" isolation level
        to ensure the operations are executed immediately.

        Steps:
        1. Establishes a connection to the PostgreSQL database.
        2. Executes SQL to drop the database and associated roles.
        3. Disposes of the database engine after the operation.

        Note:
            The database name and roles to be dropped are defined in the
            application settings.

        Raises:
            Any exceptions raised during the connection or SQL execution
            will propagate to the caller.

        """
        # Connect to the postgres database as the postgres user
        # Create a database engine using the "postgres" role and connect to the default "postgres" database
        engine = self.engine(db_role="postgres", db_name="postgres")

        # Establish a connection to the engine with "AUTOCOMMIT" isolation level
        # This ensures that SQL commands are executed immediately without requiring explicit commits
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            # Log a message indicating the database and roles being dropped
            print(
                f"\nDropping the db: {settings.DB_NAME} and all the roles for the application\n"
            )

            # Emit SQL commands to drop the database and associated roles
            # The `DropDatabaseAndRoles` class is responsible for generating and executing these commands
            DropDatabaseAndRoles().emit_sql(connection=conn)

            # Log a message indicating that the database and roles have been successfully dropped
            print("Dropped the database and the roles associated with it\n")

        # Dispose of the engine to release resources
        engine.dispose()

    def engine(
        self,
        db_role: str,
        db_driver: str = settings.DB_SYNC_DRIVER,
        db_password: str = settings.DB_USER_PW,
        db_host: str = settings.DB_HOST,
        db_name: str = settings.DB_NAME,
    ) -> Engine:
        """
        Creates and returns a SQLAlchemy Engine instance for database connections.

        Args:
            db_role (str): The database role or username to use for authentication.
            db_driver (str, optional): The database driver to use for the connection.
                Defaults to the value of `settings.DB_SYNC_DRIVER`.
            db_password (str, optional): The password for the database role.
                Defaults to the value of `settings.DB_USER_PW`.
            db_host (str, optional): The hostname or IP address of the database server.
                Defaults to the value of `settings.DB_HOST`.
            db_name (str, optional): The name of the database to connect to.
                Defaults to the value of `settings.DB_NAME`.

        Returns:
            Engine: A SQLAlchemy Engine instance configured with the provided parameters.
        """

        engine = create_engine(
            f"{db_driver}://{db_role}:{db_password}@{db_host}/{db_name}",
        )
        return engine

    async def create_superuser(
        self,
        email: str = settings.SUPERUSER_EMAIL,
        handle: str = settings.SUPERUSER_HANDLE,
        full_name: str = settings.SUPERUSER_FULL_NAME,
    ) -> str:
        """
        Asynchronously creates a superuser with the specified email, handle, and full name.

        Args:
            email (str): The email address of the superuser. Defaults to the value of `settings.SUPERUSER_EMAIL`.
            handle (str): The unique handle/username for the superuser. Defaults to the value of `settings.SUPERUSER_HANDLE`.
            full_name (str): The full name of the superuser. Defaults to the value of `settings.SUPERUSER_FULL_NAME`.

        Returns:
            str: The handle of the created superuser.

        Raises:
            Exception: If an error occurs during the creation or saving of the superuser.

        Side Effects:
            Prints a success message if the superuser is created successfully.
            Prints an error message if an exception occurs.
        """

        user = User(
            email=email,
            handle=handle,
            full_name=full_name,
            is_superuser=True,
        )
        try:
            await user.save()
            print(f"Superuser created: {user.handle} with email: {user.email}")
            return user.handle
        except Exception as e:
            print(f"Error creating superuser: {e}")

    async def create_query_paths(self) -> None:
        """
        Asynchronously creates and manages query paths for database operations.

        This method processes filters defined in the `UnoObj` registry to generate
        query paths, ensuring that each cypher_path is unique. It then interacts with the
        database to persist these query paths, creating new entries if they do not
        already exist.

        Steps:
        1. Iterates through all models in the `UnoObj` registry.
        2. Configures each obj with the provided application context.
        3. Processes filters to build a set of unique query paths.
        4. Persists the query paths to the database using an asynchronous session.

        Helper Functions:
        - `add_query_path(filter, parent)`: Adds a query cypher_path to the `query_paths` dictionary.

        Database Interaction:
        - Uses a scoped session to execute SQL commands and interact with the database.
        - Sets the database role to `{db_name}_admin` for the session.
        - Uses `QueryPath.db.get_or_create` to persist query paths.

        Prints:
        - Logs whether a query cypher_path was created or already exists.

        Raises:
        - Any exceptions related to database operations or filter processing.

        Returns:
        None
        """

        def add_query_path(
            filter: UnoFilter, parent: UnoFilter = None
        ) -> QueryPathModel:
            """
            Adds a query cypher_path to the collection of query paths.

            This function creates a `QueryPath` object based on the provided `filter`
            and optionally a `parent` filter. It determines the source meta type ID
            from the parent if provided, otherwise from the filter itself. The
            resulting `QueryPath` object is added to the `query_paths` collection
            if its cypher_path is not already present.

            Args:
                filter (UnoFilter): The filter object containing the target meta type ID,
                cypher_path generation logic, and data type.
                parent (UnoFilter, optional): The parent filter object to derive the
                source meta type ID. Defaults to None.

            Returns:
                QueryPathModel: The created `QueryPath` object.
            """
            # Determine the source meta type ID for the query cypher_path.
            # If a parent filter is provided, use its source meta type ID;
            # otherwise, use the source meta type ID of the current filter.
            source_meta_type = (
                parent.source_meta_type_id if parent else filter.source_meta_type_id
            )

            # Create a new QueryPath object with the source and target meta type IDs,
            # the cypher_path generated by the filter (optionally using the parent), and the data type.
            query_path = QueryPath(
                source_meta_type_id=source_meta_type,
                target_meta_type_id=filter.target_meta_type_id,
                cypher_path=filter.cypher_path(parent=parent),
                data_type=filter.data_type,
            )

            # Check if the generated query cypher_path is not already in the query_paths dictionary.
            # If it is not present, add it to the dictionary using the cypher_path as the key.
            if query_path.cypher_path not in query_paths:
                query_paths[query_path.cypher_path] = query_path

        def process_filters(fltr: UnoFilter) -> None:
            """
            Processes a hierarchy of filters and applies query paths for each filter.

            This function traverses a tree of `UnoFilter` objects using a depth-first
            search approach. It ensures that each filter's query cypher_path is added only once
            by maintaining a set of visited paths. For each filter, it determines the
            corresponding child obj and recursively processes its child filters.

            Args:
                fltr (UnoFilter): The root filter to start processing from.

            Returns:
                None
            """
            # Initialize a stack with the root filter and no parent
            stack = [(fltr, None)]

            # Create a set to keep track of visited filter paths to avoid processing duplicates
            visited = set()

            # Process the stack of filters using a depth-first search approach
            while stack:
                # Pop the current filter and its parent from the stack
                current_filter, parent = stack.pop()

                # Skip processing if the current filter's cypher_path has already been visited
                if current_filter.cypher_path(parent=parent) in visited:
                    continue

                # Mark the current filter's cypher_path as visited
                visited.add(current_filter.cypher_path(parent=parent))

                # Add the current filter's query cypher_path to the collection
                add_query_path(current_filter, parent)

                # Check if the source and target meta type IDs of the current filter are different.
                # If they are the same, there is no need to process child filters.
                if (
                    current_filter.source_meta_type_id
                    != current_filter.target_meta_type_id
                ):
                    # Retrieve the obj corresponding to the target meta type ID of the current filter.
                    child_obj = UnoObj.registry[current_filter.target_meta_type_id]

                    # Iterate over the child filters of the current filter, using the child obj.
                    for child_fltr in current_filter.children(obj=child_obj):
                        # Add each child filter and its parent (current filter) to the stack
                        # for further processing in the depth-first search.
                        stack.append((child_fltr, current_filter))

        # Initialize an empty dictionary to store query paths
        query_paths = {}
        # existing_query_paths = await QueryPath.filter()
        # print(f"Existing query paths: {existing_query_paths}")

        # Iterate over all models registered in the UnoObj registry
        for obj in UnoObj.registry.values():
            # Configure the obj with the application context
            obj.set_filters()

            # Iterate over all filters defined for the current obj
            for fltr in obj.filters.values():
                # Process each filter to generate and add query paths
                process_filters(fltr)

        # Iterate over all values in the `query_paths` dictionary
        for query_path in query_paths.values():
            # Skip any `query_path` that is `None`
            if query_path is None:
                continue

            # Attempt to retrieve or create a `QueryPath` object in the database
            # `query_path.to_model(schema_name="edit_schema")` converts the `query_path` to its obj representation
            # with the specified schema name.
            query_path, action = await query_path.merge()
            print(f"QueryPath: {query_path.cypher_path}, _action: {action}")
            # query_path, created = await query_path.get_or_create()
            continue

            # If the `QueryPath` object was newly created, log that it was created
            if created:
                print(f"Created QueryPath: {query_path.cypher_path}")
            # Otherwise, log that the `QueryPath` object already exists
            else:
                print(f"QueryPath already exists: {query_path.cypher_path}")
