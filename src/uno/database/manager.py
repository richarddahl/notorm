import os
from typing import Iterator, Dict, Type, Protocol
import contextlib
import io
import sys
import logging

from pydantic_settings import BaseSettings

from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects import postgresql

from uno.database.config import ConnectionConfig
from uno.database.engine import SyncEngineFactory, sync_connection
from uno.model import UnoModel

import uno.attributes.sqlconfigs
import uno.authorization.sqlconfigs
import uno.queries.sqlconfigs
import uno.meta.sqlconfigs
import uno.messaging.sqlconfigs
import uno.reports.sqlconfigs
import uno.values.sqlconfigs
import uno.workflows.sqlconfigs

from uno.utilities import import_from_path
from uno.settings import uno_settings

# Dynamic loading of models and sqlconfigs if APP_PATH is defined in the config
if uno_settings.APP_PATH:
    for pkg in uno_settings.LOAD_PACKAGES:
        models_path = f"{uno_settings.APP_PATH}/{pkg.replace('.', '/')}/models.py"
        if os.path.exists(models_path):
            import_from_path(pkg, models_path)
        else:
            logging.warning(f"File not found: {models_path}")

        sqlconfigs_path = (
            f"{uno_settings.APP_PATH}/{pkg.replace('.', '/')}/sqlconfigs.py"
        )
        if os.path.exists(sqlconfigs_path):
            import_from_path(pkg, sqlconfigs_path)
        else:
            logging.warning(f"File not found: {sqlconfigs_path}")


class SQLEmitterProtocol(Protocol):
    """Protocol defining the interface for SQL emitters."""

    def __init__(self, config: BaseSettings) -> None:
        """
        Initialize the SQL emitter with configuration.

        Args:
            config: Configuration settings for the emitter
        """
        ...

    def emit_sql(self, connection: Connection) -> None:
        """
        Emit SQL statements to the provided database connection.

        Args:
            connection: Active database connection
        """
        ...


class OutputSuppressor:
    """Utility class for suppressing standard output and logging."""

    @staticmethod
    @contextlib.contextmanager
    def suppress_stdout() -> Iterator[None]:
        """
        Context manager to temporarily suppress standard output (stdout).

        Yields:
            None
        """
        save_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            yield
        finally:
            sys.stdout = save_stdout

    @staticmethod
    @contextlib.contextmanager
    def suppress_logging() -> Iterator[None]:
        """
        Context manager to temporarily suppress logging by setting all loggers to ERROR level.

        This is particularly useful during tests to avoid excessive log output.

        Yields:
            None
        """
        # Store original log levels
        loggers = {}
        root = logging.getLogger()
        loggers[root] = root.level

        # Also get all existing loggers
        for name in logging.root.manager.loggerDict:
            logger = logging.getLogger(name)
            loggers[logger] = logger.level

        try:
            # Set all loggers to ERROR level
            for logger in loggers:
                logger.setLevel(logging.ERROR)
            yield
        finally:
            # Restore original log levels
            for logger, level in loggers.items():
                logger.setLevel(level)


class DBManager:
    """
    Database management service handling creation, configuration, and teardown.

    This class is responsible for managing database lifecycle operations including
    creating databases, schemas, tables, and functions, configuring privileges,
    and handling database teardown. It uses dependency injection for configuration,
    logging, and SQL emitters to enhance testability and maintainability.

    Attributes:
        config: Settings for database configuration
        logger: Logger for recording operations
        engine_factory: Factory for creating database engines
        sql_emitters: Dictionary of SQL emitter classes by operation name
    """

    def __init__(
        self,
        config: BaseSettings,
        logger: logging.Logger,
        engine_factory: SyncEngineFactory,
        sql_emitters: Dict[str, Type[SQLEmitterProtocol]],
    ) -> None:
        """
        Initialize the DBManager.

        Args:
            config: Settings containing database configuration
            logger: Logger for recording operations
            engine_factory: Factory for creating database engines
            sql_emitters: Dictionary of SQL emitter classes to use
        """
        self.config = config
        self.logger = logger
        self.engine_factory = engine_factory
        self.sql_emitters = sql_emitters

    def _get_connection(
        self, conn_config: ConnectionConfig, **sync_kwargs
    ) -> tuple[contextlib.ExitStack, Connection]:
        """
        Helper function to acquire a database connection using sync_connection
        and an ExitStack for proper resource management.

        Args:
            conn_config: ConnectionConfig object for this connection.
            sync_kwargs: Additional keyword arguments to pass to sync_connection.

        Returns:
            A tuple of (ExitStack, Connection).
        """
        stack = contextlib.ExitStack()
        conn = stack.enter_context(sync_connection(config=conn_config, **sync_kwargs))
        return stack, conn

    def _execute_emitter(
        self, emitter_name: str, connection: Connection, success_msg: str
    ) -> None:
        """
        Helper method to retrieve and execute an SQL emitter.

        Args:
            emitter_name: The key name of the emitter.
            connection: Active database connection.
            success_msg: Log message to report on successful execution.

        Raises:
            Exception: Propagates any exception raised during the emitter execution.
        """
        try:
            emitter_cls = self.get_emitter(emitter_name)
            emitter_instance = emitter_cls(config=self.config)
            emitter_instance.emit_sql(connection=connection)
            self.logger.info(success_msg)
        except Exception as e:
            self.logger.error(f"Failed executing {emitter_name}: {e}")
            raise

    def get_common_conn_config(self) -> ConnectionConfig:
        """
        Centralized ConnectionConfig for connections targeting the current DB_NAME
        with role "postgres".

        Returns:
            A ConnectionConfig instance.
        """
        return ConnectionConfig(
            db_role="postgres",
            db_name=self.config.DB_NAME,
            db_driver=self.config.DB_SYNC_DRIVER,
        )

    def get_login_conn_config(self) -> ConnectionConfig:
        """
        Centralized ConnectionConfig for connections targeting the current DB_NAME
        with a login role.

        Returns:
            A ConnectionConfig instance.
        """
        return ConnectionConfig(
            db_role=f"{self.config.DB_NAME}_login",
            db_name=self.config.DB_NAME,
            db_driver=self.config.DB_SYNC_DRIVER,
        )

    def get_postgres_conn_config(self) -> ConnectionConfig:
        """
        Centralized ConnectionConfig for connections targeting the "postgres" database
        using the postgres superuser role.

        Returns:
            A ConnectionConfig instance.
        """
        return ConnectionConfig(
            db_role="postgres",
            db_name="postgres",
            db_user_pw=self.config.DB_USER_PW,
            db_host=self.config.DB_HOST,
            db_port=self.config.DB_PORT,
            db_driver=self.config.DB_SYNC_DRIVER,
            db_schema="public",
        )

    def get_emitter(self, emitter_name: str) -> Type[SQLEmitterProtocol]:
        """
        Retrieve the SQL emitter class for the given name.

        Args:
            emitter_name: The key name of the emitter

        Returns:
            The SQL emitter class

        Raises:
            KeyError: If the emitter key is not found in the registry
        """
        try:
            return self.sql_emitters[emitter_name]
        except KeyError as e:
            self.logger.error(f"SQL emitter not found: {emitter_name}")
            raise

    def create_db(self) -> None:
        """
        Creates the database, suppressing stdout if in test environment.

        This is a wrapper method that handles output suppression based on
        the environment configuration. Uses non-transactional connections
        with AUTOCOMMIT isolation level for database creation operations.

        After creating the database, this method initializes Alembic for migrations.
        """

        def _create_db_internal() -> None:
            """
            Executes the full database creation process.

            Process includes:
            - Dropping existing database and roles
            - Creating roles and the database
            - Setting up schemas, extensions, privileges
            - Creating functions, triggers, and tables
            - Emitting table-specific SQL
            - Initializing Alembic migrations

            Raises:
                SQLAlchemyError: If database operations fail
            """
            try:
                self.drop_db()
                self.create_roles_and_database()
                self.create_schemas_and_extensions()
                self.set_privileges_and_paths()
                self.create_functions_triggers_and_tables()
                self.emit_table_sql()
                self.initialize_migrations()
                masked_pw = (
                    "*" * len(self.config.DB_USER_PW)
                    if getattr(self.config, "DB_USER_PW", None)
                    else "None"
                )
                self.logger.info(
                    f"Database created: {self.config.DB_NAME} with user {masked_pw}"
                )
            except SQLAlchemyError as e:
                self.logger.error(f"Database creation failed: {e}")
                raise

        if self.config.ENV == "test":
            # Use multiple context managers to suppress both stdout and logging
            with contextlib.ExitStack() as stack:
                stack.enter_context(OutputSuppressor.suppress_stdout())
                stack.enter_context(OutputSuppressor.suppress_logging())
                _create_db_internal()
        else:
            _create_db_internal()

    def create_roles_and_database(self) -> None:
        """
        Creates database roles and the database itself.

        Uses direct psycopg connection with autocommit mode to avoid
        transaction issues with CREATE DATABASE commands.

        Raises:
            SQLAlchemyError: If database operations fail
        """
        # Using psycopg directly to bypass SQLAlchemy's transaction management
        import psycopg

        # Log what we're about to do
        self.logger.info(
            f"Creating the db: {self.config.DB_NAME} and all associated roles."
        )

        # Create connection string for postgres database
        conn_string = f"host={self.config.DB_HOST} port={self.config.DB_PORT} dbname=postgres user={self.config.DB_USER} password={self.config.DB_USER_PW}"

        # Connect with autocommit mode
        with psycopg.connect(conn_string, autocommit=True) as conn:
            cursor = conn.cursor()

            # Use the SQL emitter to generate the SQL statements
            emitter_cls = self.get_emitter("create_roles_and_database")
            emitter_instance = emitter_cls(config=self.config)
            statements = emitter_instance.generate_sql()

            # Execute each statement
            for statement in statements:
                self.logger.debug(f"Executing: {statement.name}")
                cursor.execute(statement.sql)

            self.logger.info("Created the roles and the database")

    def create_schemas_and_extensions(self) -> None:
        """
        Creates schemas and extensions in the database.

        Uses direct psycopg connection with superuser privileges to ensure
        proper permissions for extension creation.

        Raises:
            SQLAlchemyError: If database operations fail
        """
        # Using psycopg directly with the configured user to ensure proper permissions
        import psycopg

        # Log what we're about to do
        self.logger.info(
            f"Creating schemas and extensions for db: {self.config.DB_NAME}"
        )

        # Create connection string for the target database, connecting as configured user
        conn_string = f"host={self.config.DB_HOST} port={self.config.DB_PORT} dbname={self.config.DB_NAME} user={self.config.DB_USER} password={self.config.DB_USER_PW}"

        # Connect with autocommit mode
        with psycopg.connect(conn_string, autocommit=True) as conn:
            cursor = conn.cursor()

            # Get and execute schemas and extensions SQL from the emitter
            emitter_cls = self.get_emitter("create_schemas_and_extensions")
            emitter_instance = emitter_cls(config=self.config)
            statements = emitter_instance.generate_sql()

            # Execute each statement
            for statement in statements:
                self.logger.debug(f"Executing: {statement.name}")
                cursor.execute(statement.sql)

            # Execute set_role function creation (from separate emitter)
            emitter_cls = self.get_emitter("set_role")
            emitter_instance = emitter_cls(config=self.config)
            statements = emitter_instance.generate_sql()

            # Execute each statement
            for statement in statements:
                self.logger.debug(f"Executing: {statement.name}")
                cursor.execute(statement.sql)

            self.logger.info("Created the schemas, extensions, and set_role function")

    def set_privileges_and_paths(self) -> None:
        """
        Configures privileges and sets search paths for the database.

        Uses direct psycopg connection with superuser privileges to ensure
        proper permissions for privilege management.

        Raises:
            SQLAlchemyError: If database operations fail
        """
        # Using psycopg directly with the configured user to ensure proper permissions
        import psycopg

        # Log what we're about to do
        self.logger.info(
            f"Configuring privileges and setting search paths for db: {self.config.DB_NAME}"
        )

        # Create connection string for the target database, connecting as configured user
        conn_string = f"host={self.config.DB_HOST} port={self.config.DB_PORT} dbname={self.config.DB_NAME} user={self.config.DB_USER} password={self.config.DB_USER_PW}"

        # Connect with autocommit mode
        with psycopg.connect(conn_string, autocommit=True) as conn:
            cursor = conn.cursor()

            # Create audit schema and record_version table
            self.logger.debug("Creating audit schema and record_version table")
            cursor.execute(
                f"""
            CREATE SCHEMA IF NOT EXISTS audit;
            
            -- Create record_version table in audit schema if it doesn't exist
            CREATE TABLE IF NOT EXISTS audit.record_version (
                id SERIAL PRIMARY KEY,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                changed_fields JSONB,
                changed_by TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Set owner and permissions
            ALTER TABLE audit.record_version OWNER TO {self.config.DB_NAME}_admin;
            """
            )

            # Create graph schema if not exists
            self.logger.debug("Creating graph schema if not exists")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS graph;")

            # Apply privileges and search paths from SQL emitter
            emitter_cls = self.get_emitter("revoke_and_grant_privileges")
            emitter_instance = emitter_cls(config=self.config)
            statements = emitter_instance.generate_sql()

            # Execute each statement
            for statement in statements:
                self.logger.debug(f"Executing: {statement.name}")
                cursor.execute(statement.sql)

            self.logger.info("Configured privileges and set search paths")

    def create_functions_triggers_and_tables(self) -> None:
        """
        Creates functions, triggers, and tables in the database.

        Uses a combination of direct psycopg connections and SQLAlchemy
        to perform the following operations:
        1. Creates the token_secret table
        2. Creates the pgulid function
        3. Creates all database tables from UnoModel metadata
        4. Sets table privileges
        5. Creates the insert_meta function

        Raises:
            SQLAlchemyError: If database operations fail
        """
        # Using psycopg directly to create token_secret table and pgulid function
        import psycopg

        # Using postgres superuser for operations that require high privileges
        self.logger.info(
            f"Creating functions, triggers, and tables for db: {self.config.DB_NAME}"
        )

        # Connect to database as postgres superuser
        conn_string = f"host={self.config.DB_HOST} port={self.config.DB_PORT} dbname={self.config.DB_NAME} user={self.config.DB_USER} password={self.config.DB_USER_PW}"

        with psycopg.connect(conn_string, autocommit=True) as conn:
            cursor = conn.cursor()
            db_name = self.config.DB_NAME
            admin_role = f"{db_name}_admin"
            db_schema = self.config.DB_SCHEMA

            # Create token_secret table using emitter
            self.logger.debug("Creating token_secret table")
            emitter_cls = self.get_emitter("create_token_secret")
            emitter_instance = emitter_cls(config=self.config)
            token_statements = emitter_instance.generate_sql()

            for statement in token_statements:
                self.logger.debug(f"Executing: {statement.name}")
                cursor.execute(statement.sql)

            # Create pgulid function using emitter
            self.logger.debug("Creating pgulid function")
            emitter_cls = self.get_emitter("create_pgulid")
            emitter_instance = emitter_cls(config=self.config)
            pgulid_statements = emitter_instance.generate_sql()

            for statement in pgulid_statements:
                self.logger.debug(f"Executing: {statement.name}")
                cursor.execute(statement.sql)

            # Grant schema permissions to login role before table creation
            login_role = f"{db_name}_login"
            self.logger.debug("Granting schema permissions for table creation")
            cursor.execute(
                f"""
            ALTER SCHEMA {db_schema} OWNER TO {admin_role};
            GRANT ALL PRIVILEGES ON SCHEMA {db_schema} TO {admin_role};
            GRANT USAGE, CREATE ON SCHEMA {db_schema} TO {login_role};
            
            -- Create types in schema with superuser privileges
            --CREATE TYPE {db_schema}.include AS ENUM ('INCLUDE', 'EXCLUDE');
            --CREATE TYPE {db_schema}.constraint_type AS ENUM ('PRIMARY', 'UNIQUE', 'FOREIGN', 'CHECK');
            --CREATE TYPE {db_schema}.direction AS ENUM ('IN', 'OUT', 'INOUT');
            --CREATE TYPE {db_schema}.status AS ENUM ('ACTIVE', 'PENDING', 'INACTIVE', 'DELETED');
            """
            )

        # Replace the raw psycopg connection with an SQLAlchemy engine connection for table creation
        from sqlalchemy import text

        # Create a connection config for the target database but connect as superuser (postgres)
        engine_config = ConnectionConfig(
            db_role="postgres",
            db_name=self.config.DB_NAME,
            db_user_pw=self.config.DB_USER_PW,
            db_host=self.config.DB_HOST,
            db_port=self.config.DB_PORT,
            db_driver=self.config.DB_SYNC_DRIVER,
            db_schema=self.config.DB_SCHEMA,
        )

        # Create the engine and establish a connection
        self.logger.debug(
            "Creating tables with SQLAlchemy engine to ensure proper ownership"
        )
        engine = self.engine_factory.create_engine(engine_config)

        with engine.connect() as sa_conn:
            # Set autocommit and admin role for proper ownership
            sa_conn.execution_options(isolation_level="AUTOCOMMIT")
            sa_conn.execute(text(f"SET ROLE {admin_role}"))

            # Create all tables using SQLAlchemy metadata
            UnoModel.metadata.create_all(sa_conn)
            self.logger.debug("Created all tables in the database")

            # Get sequences and set their ownership using the SQLAlchemy connection
            result = sa_conn.execute(
                text(
                    f"""
                SELECT sequence_schema, sequence_name
                FROM information_schema.sequences
                WHERE sequence_schema = '{db_schema}'
                """
                )
            )

            sequences = result.fetchall()
            for seq_schema, seq_name in sequences:
                sa_conn.execute(
                    text(
                        f"ALTER SEQUENCE {seq_schema}.{seq_name} OWNER TO {admin_role};"
                    )
                )

            self.logger.info("Created the database tables with admin ownership")

        # Set table privileges and create insert_meta function as postgres superuser
        with psycopg.connect(conn_string, autocommit=True) as conn:
            cursor = conn.cursor()

            # Grant privileges using emitter
            self.logger.debug("Setting table privileges")
            emitter_cls = self.get_emitter("grant_privileges")
            emitter_instance = emitter_cls(config=self.config)
            privilege_statements = emitter_instance.generate_sql()

            for statement in privilege_statements:
                self.logger.debug(f"Executing: {statement.name}")
                cursor.execute(statement.sql)

            # Create insert_meta function
            emitter_cls = self.get_emitter("insert_meta_record")
            emitter_instance = emitter_cls(config=self.config)
            meta_statements = emitter_instance.generate_sql()

            for statement in meta_statements:
                cursor.execute(statement.sql)

            self.logger.info("Created insert_meta function and set table privileges")

    def emit_table_sql(self) -> None:
        """
        Emits SQL for table-specific configurations.

        Uses psycopg with postgres superuser privileges to process MetaType
        first then iterates over SQLConfig registry.

        Raises:
            SQLAlchemyError: If database connection or SQL execution fails
        """
        import psycopg
        from uno.meta.sqlconfigs import MetaTypeSQLConfig
        from uno.sql.registry import SQLConfigRegistry

        # Log what we're about to do
        self.logger.info("Emitting SQL for table-specific configurations")

        # Connect to database as postgres superuser
        conn_string = f"host={self.config.DB_HOST} port={self.config.DB_PORT} dbname={self.config.DB_NAME} user={self.config.DB_USER} password={self.config.DB_USER_PW}"

        with psycopg.connect(conn_string, autocommit=True) as conn:
            cursor = conn.cursor()
            db_name = self.config.DB_NAME
            admin_role = f"{db_name}_admin"

            # Set role to admin for proper permissions
            cursor.execute(f"SET ROLE {admin_role};")

            # Process MetaType first
            self.logger.info("Emitting SQL for: MetaType")

            # First verify all tables have correct ownership
            self.logger.debug("Verifying table ownership before SQL emission")
            cursor.execute(
                f"""
            -- List tables in the schema
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{self.config.DB_SCHEMA}'
            """
            )

            tables = cursor.fetchall()
            for (table_name,) in tables:
                # Set owner to admin role for each table
                cursor.execute(
                    f"ALTER TABLE {self.config.DB_SCHEMA}.{table_name} OWNER TO {admin_role};"
                )
                self.logger.debug(
                    f"Set owner of {self.config.DB_SCHEMA}.{table_name} to {admin_role}"
                )

            # Get individual emitters from MetaTypeSQLConfig
            meta_type_config = MetaTypeSQLConfig(config=self.config)

            # Execute SQL for each emitter in MetaTypeSQLConfig
            for emitter in meta_type_config.emitters:
                self.logger.debug(f"Processing emitter: {emitter.__class__.__name__}")
                statements = emitter.generate_sql()

                for statement in statements:
                    try:
                        cursor.execute(statement.sql)
                    except Exception as e:
                        self.logger.error(f"Error executing SQL: {e}")
                        self.logger.error(f"SQL was: {statement.sql}")
                        # Continue with other statements

            # Then process other SQL configs
            for name, config_cls in SQLConfigRegistry.all().items():
                if name == "MetaTypeSQLConfig":
                    continue

                self.logger.info(f"Emitting SQL for: {name}")
                config_instance = config_cls(config=self.config)

                # Process each emitter in the SQLConfig
                for emitter in config_instance.emitters:
                    self.logger.debug(
                        f"Processing emitter: {emitter.__class__.__name__}"
                    )
                    try:
                        statements = emitter.generate_sql()

                        for statement in statements:
                            try:
                                cursor.execute(statement.sql)
                            except Exception as e:
                                self.logger.error(f"Error executing SQL: {e}")
                                self.logger.error(f"SQL was: {statement.sql}")
                                # Continue with other statements
                    except Exception as e:
                        self.logger.error(
                            f"Error processing emitter {emitter.__class__.__name__}: {e}"
                        )
                        # Continue with other emitters instead of failing the entire process

            self.logger.info("Completed emitting table-specific SQL")

    def drop_db(self) -> None:
        """
        Drops the database and all associated roles.

        This method uses an ExitStack to manage multiple context managers, ensuring
        proper cleanup of resources. If the environment is set to "test", it suppresses
        standard output during execution. It establishes a connection to the postgres
        database using the 'postgres' superuser role with AUTOCOMMIT isolation level,
        logs the operation, and emits the necessary SQL commands to drop the database
        and its associated roles.

        Raises:
            SQLAlchemyError: If database operations fail
        """
        # Using direct connection parameters for the superuser connection to postgres database
        with contextlib.ExitStack() as stack:
            if self.config.ENV == "test":
                stack.enter_context(OutputSuppressor.suppress_stdout())
                stack.enter_context(OutputSuppressor.suppress_logging())

            # Create a direct connection to postgres as the postgres superuser
            # Using psycopg directly to bypass SQLAlchemy's transaction management
            import psycopg

            # Log what we're about to do
            self.logger.info(
                f"Dropping the db: {self.config.DB_NAME} and all associated roles."
            )

            # Create connection string for postgres database
            conn_string = f"host={self.config.DB_HOST} port={self.config.DB_PORT} dbname=postgres user={self.config.DB_USER} password={self.config.DB_USER_PW}"

            # Connect with autocommit mode
            with psycopg.connect(conn_string, autocommit=True) as conn:
                cursor = conn.cursor()

                # Use the SQL emitter to get and execute drop statements
                emitter_cls = self.get_emitter("drop_database_and_roles")
                emitter_instance = emitter_cls(config=self.config)
                drop_statements = emitter_instance.generate_sql()

                # Execute each statement
                for statement in drop_statements:
                    self.logger.debug(f"Executing: {statement.name}")
                    cursor.execute(statement.sql)

            self.logger.info("Dropped the database and the associated roles")

    def initialize_migrations(self) -> None:
        """
        Initialize Alembic migrations for this database.

        This method stamps the database with the 'base' migration to set
        up the Alembic version table without applying any migrations.
        The table will then be used to track future schema changes.

        Raises:
            RuntimeError: If migration initialization fails and we're not in test mode
        """
        try:
            # Import here to avoid circular imports
            import subprocess
            from pathlib import Path

            self.logger.info("Initializing Alembic migrations")

            # Ensure migrations directory exists
            migrations_dir = Path(__file__).parent.parent / "migrations"
            migrations_dir.mkdir(exist_ok=True)
            versions_dir = migrations_dir / "versions"
            versions_dir.mkdir(exist_ok=True)

            # Get path to migration script
            script_path = (
                Path(__file__).parent.parent.parent.parent
                / "src"
                / "scripts"
                / "migrations.py"
            )

            if not script_path.exists():
                self.logger.error(f"Migration script not found at {script_path}")
                alternate_paths = [
                    Path(__file__).parent.parent.parent.parent
                    / "scripts"
                    / "migrations.py",
                    Path(__file__).parent.parent.parent / "scripts" / "migrations.py",
                ]

                for alt_path in alternate_paths:
                    if alt_path.exists():
                        self.logger.info(
                            f"Found migrations script at alternative path: {alt_path}"
                        )
                        script_path = alt_path
                        break
                else:
                    self.logger.error(
                        "Could not find migrations script at any known location"
                    )
                    if self.config.ENV == "test":
                        self.logger.warning(
                            "Test environment detected, skipping migration initialization"
                        )
                        return
                    raise FileNotFoundError("Could not find migrations script")

            # Run the initialization command
            env = os.environ.copy()
            if self.config.ENV:
                env["ENV"] = self.config.ENV

            try:
                # Suppress output in test environment
                if self.config.ENV == "test":
                    with contextlib.ExitStack() as stack:
                        stack.enter_context(OutputSuppressor.suppress_stdout())
                        stack.enter_context(OutputSuppressor.suppress_logging())
                        result = subprocess.run(
                            [sys.executable, str(script_path), "init"],
                            env=env,
                            check=False,  # Don't raise exception on non-zero exit
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                else:
                    result = subprocess.run(
                        [sys.executable, str(script_path), "init"],
                        env=env,
                        check=False,  # Don't raise exception on non-zero exit
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )

                if result.returncode == 0:
                    self.logger.info("Alembic migrations initialized successfully")
                else:
                    error_msg = result.stderr.decode("utf-8")
                    self.logger.error(
                        f"Failed to initialize Alembic migrations: {error_msg}"
                    )
                    # Only raise error in non-test environments
                    if self.config.ENV != "test":
                        raise RuntimeError(
                            f"Failed to initialize Alembic migrations: {error_msg}"
                        )
                    else:
                        self.logger.warning(
                            "Test environment detected, continuing despite migration error"
                        )

            except subprocess.SubprocessError as se:
                self.logger.error(
                    f"Subprocess error during migration initialization: {se}"
                )
                if self.config.ENV != "test":
                    raise

        except Exception as e:
            self.logger.error(f"Migration initialization error: {e}")
            # Only raise error in non-test environments
            if self.config.ENV != "test":
                raise RuntimeError(f"Failed to initialize Alembic migrations: {e}")
            else:
                self.logger.warning(
                    "Test environment detected, continuing despite migration error"
                )
