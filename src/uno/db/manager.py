import os
from typing import Optional, Iterator, Dict, Type, Protocol, Tuple, List, AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncConnection

# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import io
import sys
import contextlib
import logging

from pydantic_settings import BaseSettings

from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from uno.db.config import ConnectionConfig
from uno.db.engine import sync_connection, SyncEngineFactory
from uno.db.sql.classes import SQLConfig
from uno.db.sql.dbsql import (
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    RevokeAndGrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    SetRole,
)
from uno.db.sql.tablesql import (
    InsertMetaRecordFunction,
)
from uno.model import UnoModel
from uno.meta.sqlconfigs import MetaTypeSQLConfig

import uno.attr.sqlconfigs
import uno.auth.sqlconfigs
import uno.qry.sqlconfigs
import uno.meta.sqlconfigs
import uno.msg.sqlconfigs
import uno.rprt.sqlconfigs
import uno.val.sqlconfigs

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
            config: Configuration uno_settings for the emitter
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
        config: Optional[BaseSettings] = None,
        logger: Optional[logging.Logger] = None,
        engine_factory: Optional[SyncEngineFactory] = None,
        sql_emitters: Optional[Dict[str, Type[SQLEmitterProtocol]]] = None,
    ) -> None:
        """
        Initialize the DBManager.

        Args:
            config: Settings containing database configuration
            logger: Logger for recording operations
            engine_factory: Factory for creating database engines
            sql_emitters: Dictionary of SQL emitter classes to use
        """
        self.config = config or uno_settings
        self.logger = logger or logging.getLogger(__name__)
        self.engine_factory = engine_factory or SyncEngineFactory(self.config)

        # Default SQL emitters if none provided
        self.sql_emitters = sql_emitters or {
            "drop_database_and_roles": DropDatabaseAndRoles,
            "create_roles_and_database": CreateRolesAndDatabase,
            "create_schemas_and_extensions": CreateSchemasAndExtensions,
            "revoke_and_grant_privileges": RevokeAndGrantPrivilegesAndSetSearchPaths,
            "create_pgulid": CreatePGULID,
            "create_token_secret": CreateTokenSecret,
            "grant_privileges": GrantPrivileges,
            "set_role": SetRole,
            "insert_meta_record": InsertMetaRecordFunction,
            "meta_type": MetaTypeSQLConfig,
        }

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
                # Execute the creation steps in sequence
                self.drop_db()
                self.create_roles_and_database()
                self.create_schemas_and_extensions()
                self.set_privileges_and_paths()
                self.create_functions_triggers_and_tables()
                self.emit_table_sql()

                self.logger.info(f"Database created: {self.config.DB_NAME}")
            except SQLAlchemyError as e:
                self.logger.error(f"Database creation failed: {e}")
                raise

        if self.config.ENV == "test":
            with OutputSuppressor.suppress_stdout():
                _create_db_internal()
        else:
            _create_db_internal()

    def create_roles_and_database(self) -> None:
        conn_config = ConnectionConfig(
            db_role="postgres",
            db_name="postgres",
            db_driver=self.config.DB_SYNC_DRIVER,
        )

        with contextlib.ExitStack() as stack:
            conn = stack.enter_context(
                sync_connection(
                    config=conn_config,
                )
            )
            self.logger.info(
                f"Creating the db: {self.config.DB_NAME} and all associated roles."
            )
            emitter_cls = self.get_emitter("create_roles_and_database")
            emitter_cls(config=self.config).emit_sql(connection=conn)
            self.logger.info("Created the roles and the database")

    def create_schemas_and_extensions(self) -> None:
        conn_config = ConnectionConfig(
            db_role="postgres",
            db_name=self.config.DB_NAME,
            db_driver=self.config.DB_SYNC_DRIVER,
        )

        with contextlib.ExitStack() as stack:
            conn = stack.enter_context(
                sync_connection(
                    config=conn_config,
                    isolation_level="AUTOCOMMIT",
                )
            )
            self.logger.info(
                f"Creating schemas and extensions for the db: {self.config.DB_NAME}."
            )
            emitter_cls = self.get_emitter("create_schemas_and_extensions")
            emitter_cls(config=self.config).emit_sql(connection=conn)
            self.logger.info("Created the schemas and extensions")

            emitter_cls = self.get_emitter("set_role")
            emitter_cls(config=self.config).emit_sql(connection=conn)
            self.logger.info("Created the set_role function")

    def set_privileges_and_paths(self) -> None:
        conn_config = ConnectionConfig(
            db_role="postgres",
            db_name=self.config.DB_NAME,
            db_driver=self.config.DB_SYNC_DRIVER,
        )

        with contextlib.ExitStack() as stack:
            conn = stack.enter_context(
                sync_connection(
                    config=conn_config,
                )
            )
            self.logger.info(
                f"Configuring privileges and setting search paths for the db: {self.config.DB_NAME}."
            )
            emitter_cls = self.get_emitter("revoke_and_grant_privileges")
            emitter_cls(config=self.config).emit_sql(connection=conn)
            self.logger.info("Configured privileges and set search paths")

    def create_functions_triggers_and_tables(self) -> None:
        conn_config = ConnectionConfig(
            db_role=f"{self.config.DB_NAME}_login",
            db_name=self.config.DB_NAME,
            db_driver=self.config.DB_SYNC_DRIVER,
        )

        with contextlib.ExitStack() as stack:
            conn = stack.enter_context(
                sync_connection(
                    config=conn_config,
                )
            )
            self.logger.info(
                f"Creating functions, triggers, and tables for the db: {self.config.DB_NAME}."
            )

            # Create token_secret table
            emitter_cls = self.get_emitter("create_token_secret")
            emitter_cls(config=self.config).emit_sql(connection=conn)
            self.logger.info("Created the token_secret table")

            # Create pgulid function
            emitter_cls = self.get_emitter("create_pgulid")
            emitter_cls(config=self.config).emit_sql(connection=conn)
            self.logger.info("Created the pgulid function")

            # Create tables and setup privileges
            try:
                # Create all database tables
                UnoModel.metadata.create_all(bind=conn)
                self.logger.info("Created the database tables")

                # Set table privileges
                emitter_cls = self.get_emitter("grant_privileges")
                emitter_cls(config=self.config).emit_sql(connection=conn)
                self.logger.info("Set the table privileges")

                # Create insert_meta function
                emitter_cls = self.get_emitter("insert_meta_record")
                emitter_cls(config=self.config).emit_sql(connection=conn)
                self.logger.info("Created the insert_meta function")
            except SQLAlchemyError as e:
                self.logger.error(f"Failed to create tables and set privileges: {e}")
                raise
            except KeyError as e:
                self.logger.error(f"SQL emitter not found: {e}")
                raise

    def emit_table_sql(self) -> None:
        """
        Emits SQL for table-specific configurations.

        Processes MetaType first then iterates over SQLConfig registry.

        Raises:
            SQLAlchemyError: If database connection or SQL execution fails
        """
        conn_config = ConnectionConfig(
            db_role=f"{self.config.DB_NAME}_login",
            db_name=self.config.DB_NAME,
            db_driver=self.config.DB_SYNC_DRIVER,
        )

        with contextlib.ExitStack() as stack:
            conn = stack.enter_context(
                sync_connection(
                    config=conn_config,
                )
            )
            try:
                # Process MetaType first
                self.logger.info("Emitting SQL for: MetaType")
                emitter_cls = self.get_emitter("meta_type")
                emitter_cls(config=self.config).emit_sql(connection=conn)

                # Process remaining SQLConfig registry entries
                for name, config_cls in SQLConfig.registry.items():
                    if name == "MetaTypeSQLConfig":
                        continue
                    self.logger.info(f"Emitting SQL for: {name}")
                    config_cls(config=self.config).emit_sql(connection=conn)
            except SQLAlchemyError as e:
                self.logger.error(f"Failed to emit table SQL: {e}")
                raise

    def drop_db(self) -> None:
        """
        Drops the database and all associated roles.

        This method uses an ExitStack to manage multiple context managers, ensuring
        proper cleanup of resources. If the environment is set to "test", it suppresses
        standard output during execution. It establishes a connection to the database
        using the provided configuration, logs the operation, and emits the necessary
        SQL commands to drop the database and its associated roles.

        Returns:
            None
        """

        # Using ExitStack to manage multiple context managers, allowing dynamic
        # addition of context managers and ensuring proper cleanup.
        conn_config = ConnectionConfig(
            db_role="postgres",
            db_name="postgres",
            db_driver=self.config.DB_SYNC_DRIVER,
        )
        with contextlib.ExitStack() as stack:
            if self.config.ENV == "test":
                stack.enter_context(OutputSuppressor.suppress_stdout())
            conn = stack.enter_context(sync_connection(config=conn_config))
            self.logger.info(
                f"Dropping the db: {self.config.DB_NAME} and all associated roles."
            )
            emitter_cls = self.get_emitter("drop_database_and_roles")
            emitter_cls(config=self.config).emit_sql(connection=conn)
            self.logger.info("Dropped the database and the associated roles")
