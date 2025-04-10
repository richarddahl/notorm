import os
from typing import Optional, Iterator, Dict, Type, Protocol
import contextlib
import io
import sys
import logging

from pydantic_settings import BaseSettings

from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from uno.database.config import ConnectionConfig
from uno.database.engine import sync_connection, SyncEngineFactory
from uno.sql.registry import SQLConfigRegistry
from uno.sql.emitters.database import (
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    RevokeAndGrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    SetRole,
)
from uno.sql.emitters.table import (
    InsertMetaRecordFunction,
)
from uno.model import UnoModel
from uno.meta.sqlconfigs import MetaTypeSQLConfig

import uno.attributes.sqlconfigs
import uno.authorization.sqlconfigs
import uno.queries.sqlconfigs
import uno.meta.sqlconfigs
import uno.messaging.sqlconfigs
import uno.reports.sqlconfigs
import uno.values.sqlconfigs

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
    """Utility class for suppressing standard output."""

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
        Centralized ConnectionConfig for connections targeting the "postgres" database.

        Returns:
            A ConnectionConfig instance.
        """
        return ConnectionConfig(
            db_role="postgres",
            db_name="postgres",
            db_driver=self.config.DB_SYNC_DRIVER,
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
        the environment configuration.
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
            with OutputSuppressor.suppress_stdout():
                _create_db_internal()
        else:
            _create_db_internal()

    def create_roles_and_database(self) -> None:
        """
        Creates database roles and the database itself.

        Uses the CreateRolesAndDatabase emitter to generate and execute
        the necessary SQL statements.

        Raises:
            SQLAlchemyError: If database operations fail
        """
        conn_config = ConnectionConfig(
            db_role="postgres",
            db_name="postgres",
            db_driver=self.config.DB_SYNC_DRIVER,
        )
        stack, conn = self._get_connection(conn_config)
        try:
            self.logger.info(
                f"Creating the db: {self.config.DB_NAME} and all associated roles."
            )
            self._execute_emitter(
                "create_roles_and_database", conn, "Created the roles and the database"
            )
        finally:
            stack.close()

    def create_schemas_and_extensions(self) -> None:
        """
        Creates schemas and extensions in the database.

        Uses the CreateSchemasAndExtensions emitter to generate and execute
        the necessary SQL statements, and also sets up the set_role function.

        Raises:
            SQLAlchemyError: If database operations fail
        """
        conn_config = self.get_common_conn_config()
        stack, conn = self._get_connection(conn_config, isolation_level="AUTOCOMMIT")
        try:
            self.logger.info(
                f"Creating schemas and extensions for the db: {self.config.DB_NAME}."
            )
            self._execute_emitter(
                "create_schemas_and_extensions",
                conn,
                "Created the schemas and extensions",
            )
            self._execute_emitter("set_role", conn, "Created the set_role function")
        finally:
            stack.close()

    def set_privileges_and_paths(self) -> None:
        """
        Configures privileges and sets search paths for the database.

        Uses the RevokeAndGrantPrivilegesAndSetSearchPaths emitter to generate
        and execute the necessary SQL statements.

        Raises:
            SQLAlchemyError: If database operations fail
        """
        conn_config = self.get_common_conn_config()
        stack, conn = self._get_connection(conn_config)
        try:
            self.logger.info(
                f"Configuring privileges and setting search paths for the db: {self.config.DB_NAME}."
            )
            self._execute_emitter(
                "revoke_and_grant_privileges",
                conn,
                "Configured privileges and set search paths",
            )
        finally:
            stack.close()

    def create_functions_triggers_and_tables(self) -> None:
        """
        Creates functions, triggers, and tables in the database.

        Performs the following operations:
        1. Creates the token_secret table
        2. Creates the pgulid function
        3. Creates all database tables from UnoModel metadata
        4. Sets table privileges
        5. Creates the insert_meta function

        Raises:
            SQLAlchemyError: If database operations fail
            KeyError: If a required SQL emitter is not found
        """
        conn_config = self.get_login_conn_config()
        stack, conn = self._get_connection(conn_config)
        try:
            self.logger.info(
                f"Creating functions, triggers, and tables for the db: {self.config.DB_NAME}."
            )
            self._execute_emitter(
                "create_token_secret", conn, "Created the token_secret table"
            )
            self._execute_emitter("create_pgulid", conn, "Created the pgulid function")

            # Create all database tables
            UnoModel.metadata.create_all(bind=conn)
            self.logger.info("Created the database tables")

            self._execute_emitter("grant_privileges", conn, "Set the table privileges")
            self._execute_emitter(
                "insert_meta_record", conn, "Created the insert_meta function"
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create tables and set privileges: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"SQL emitter not found: {e}")
            raise
        finally:
            stack.close()

    def emit_table_sql(self) -> None:
        """
        Emits SQL for table-specific configurations.

        Processes MetaType first then iterates over SQLConfig registry.

        Raises:
            SQLAlchemyError: If database connection or SQL execution fails
        """
        conn_config = self.get_login_conn_config()
        stack, conn = self._get_connection(conn_config)
        try:
            self.logger.info("Emitting SQL for: MetaType")
            self._execute_emitter("meta_type", conn, "Emitted SQL for MetaType")
            for name, config_cls in SQLConfigRegistry.all().items():
                if name == "MetaTypeSQLConfig":
                    continue
                self.logger.info(f"Emitting SQL for: {name}")
                emitter_instance = config_cls(config=self.config)
                emitter_instance.emit_sql(connection=conn)
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to emit table SQL: {e}")
            raise
        finally:
            stack.close()

    def drop_db(self) -> None:
        """
        Drops the database and all associated roles.

        This method uses an ExitStack to manage multiple context managers, ensuring
        proper cleanup of resources. If the environment is set to "test", it suppresses
        standard output during execution. It establishes a connection to the database
        using the provided configuration, logs the operation, and emits the necessary
        SQL commands to drop the database and its associated roles.

        Raises:
            SQLAlchemyError: If database operations fail
        """
        conn_config = self.get_postgres_conn_config()
        with contextlib.ExitStack() as stack:
            if self.config.ENV == "test":
                stack.enter_context(OutputSuppressor.suppress_stdout())
            conn = stack.enter_context(sync_connection(config=conn_config))
            self.logger.info(
                f"Dropping the db: {self.config.DB_NAME} and all associated roles."
            )
            emitter_cls = self.get_emitter("drop_database_and_roles")
            emitter_instance = emitter_cls(config=self.config)
            emitter_instance.emit_sql(connection=conn)
            self.logger.info("Dropped the database and the associated roles")
