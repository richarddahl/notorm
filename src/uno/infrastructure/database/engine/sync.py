# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import time
from typing import Optional, Iterator
import contextlib
import logging
from logging import Logger

from sqlalchemy import create_engine, URL, Engine, Connection
from sqlalchemy.exc import SQLAlchemyError

from uno.database.config import ConnectionConfig
from uno.database.engine.base import EngineFactory
from uno.settings import uno_settings


class SyncEngineFactory(EngineFactory[Engine, Connection]):
    """Factory for synchronous database engines."""

    def create_engine(self, config: ConnectionConfig) -> Engine:
        """Create a synchronous SQLAlchemy engine."""

        def validate_config(config: ConnectionConfig) -> None:
            """Validate connection configuration."""
            if not config.db_driver:
                raise ValueError("Database driver must be specified")
            if not config.db_host:
                raise ValueError("Database host must be specified")
            if not config.db_name:
                raise ValueError("Database name must be specified")

        def prepare_engine_kwargs(config: ConnectionConfig) -> dict:
            """Prepare engine kwargs from configuration."""
            engine_kwargs = {}

            # Add connection pooling parameters if provided
            if config.pool_size is not None:
                engine_kwargs["pool_size"] = config.pool_size
            if config.max_overflow is not None:
                engine_kwargs["max_overflow"] = config.max_overflow
            if config.pool_timeout is not None:
                engine_kwargs["pool_timeout"] = config.pool_timeout
            if config.pool_recycle is not None:
                engine_kwargs["pool_recycle"] = config.pool_recycle
            if config.connect_args:
                engine_kwargs["connect_args"] = config.connect_args

            return engine_kwargs

        # Validate configuration
        validate_config(config)

        # Prepare engine keyword arguments
        engine_kwargs = prepare_engine_kwargs(config)

        # Create the engine
        engine = create_engine(
            URL.create(
                drivername=config.db_driver,
                username=config.db_role,
                password=config.db_user_pw,
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
            ),
            **engine_kwargs,
        )

        self.logger.debug(
            f"Created sync engine for {config.db_role}@{config.db_host}/{config.db_name}"
        )

        return engine


@contextlib.contextmanager
def sync_connection(
    db_driver: str = uno_settings.DB_SYNC_DRIVER,
    db_name: str = uno_settings.DB_NAME,
    db_user_pw: str = uno_settings.DB_USER_PW,
    db_role: str = f"{uno_settings.DB_NAME}_login",
    config: Optional[ConnectionConfig] = None,
    isolation_level: str = "AUTOCOMMIT",
    factory: Optional[SyncEngineFactory] = None,
    max_retries: int = 3,
    retry_delay: int = 2,
    logger: Optional[Logger] = None,
    **kwargs,
) -> Iterator[Connection]:
    """
    Context manager for synchronous database connections.

    Args:
        db_driver: Database driver to use
        db_name: Database name
        db_user_pw: Database user password
        db_role: Database role
        config: ConnectionConfig object (takes precedence over individual params)
        isolation_level: Transaction isolation level
        factory: Optional engine factory
        max_retries: Maximum connection retry attempts
        retry_delay: Base delay between retries (used for exponential backoff)
        logger: Optional logger
        **kwargs: Additional connection parameters

    Yields:
        Connection: Active database connection

    Raises:
        SQLAlchemyError: If connection fails after max retry attempts
    """
    # Use the provided ConnectionConfig or create one from settings defaults
    connection_config = config
    if connection_config is None:
        connection_config = ConnectionConfig(
            db_role=db_role,
            db_name=db_name,
            db_host=uno_settings.DB_HOST,
            db_user_pw=db_user_pw,
            db_driver=db_driver,
            db_port=uno_settings.DB_PORT,
            **kwargs,
        )

    # Use provided factory or create a new one
    engine_factory = factory or SyncEngineFactory(logger=logger)
    log = logger or logging.getLogger(__name__)

    attempt = 0
    engine = None
    last_error = None

    while attempt < max_retries:
        try:
            # Create engine with the configuration
            engine = engine_factory.create_engine(connection_config)

            # Create connection with specified isolation level
            with engine.connect().execution_options(
                isolation_level=isolation_level
            ) as conn:
                # Execute callbacks
                engine_factory.execute_callbacks(conn)

                # Yield the connection
                yield conn

            # Break out of the retry loop on success
            break

        except SQLAlchemyError as e:
            last_error = e
            attempt += 1

            # Log and retry if attempts remain
            if attempt < max_retries:
                delay = retry_delay**attempt
                log.warning(
                    f"Database connection attempt {attempt}/{max_retries} "
                    f"failed. Retrying in {delay}s... Error: {e}"
                )
                time.sleep(delay)
            else:
                log.error(
                    f"Failed to connect after {max_retries} attempts. "
                    f"Last error: {e}"
                )

        finally:
            # Always dispose of the engine
            if engine:
                engine.dispose()

    # If we've exhausted all attempts, raise the last error
    if attempt >= max_retries and last_error is not None:
        raise last_error
