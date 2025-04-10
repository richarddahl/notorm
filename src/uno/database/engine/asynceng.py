from typing import Optional, AsyncIterator
import contextlib
import logging
import asyncio

from logging import Logger


from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection
from sqlalchemy import URL

from uno.database.config import ConnectionConfig
from uno.database.engine.base import EngineFactory


class AsyncEngineFactory(EngineFactory[AsyncEngine, AsyncConnection]):
    """Factory for asynchronous database engines."""

    def create_engine(self, config: ConnectionConfig) -> AsyncEngine:
        """Create an asynchronous SQLAlchemy engine."""
        # Validate configuration
        self._validate_config(config)

        # Prepare engine keyword arguments
        engine_kwargs = self._prepare_engine_kwargs(config)

        # Create the async engine
        engine = create_async_engine(
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
            f"Created async engine for {config.db_role}@{config.db_host}/{config.db_name}"
        )

        return engine

    def _validate_config(self, config: ConnectionConfig) -> None:
        """Validate connection configuration."""
        if not config.db_driver:
            raise ValueError("Database driver must be specified")
        if not config.db_host:
            raise ValueError("Database host must be specified")
        if not config.db_name:
            raise ValueError("Database name must be specified")

    def _prepare_engine_kwargs(self, config: ConnectionConfig) -> dict:
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


@contextlib.asynccontextmanager
async def async_connection(
    db_role: str,
    db_name: Optional[str] = None,
    db_host: Optional[str] = None,
    db_user_pw: Optional[str] = None,
    db_driver: Optional[str] = None,
    db_port: Optional[int] = None,
    config: Optional[ConnectionConfig] = None,
    isolation_level: str = "AUTOCOMMIT",
    factory: Optional[AsyncEngineFactory] = None,
    max_retries: int = 3,
    retry_delay: int = 2,
    logger: Optional[Logger] = None,
    **kwargs,
) -> AsyncIterator[AsyncConnection]:
    """Context manager for asynchronous database connections."""
    # Use provided ConnectionConfig or create one from parameters
    connection_config = config
    if connection_config is None:
        connection_config = ConnectionConfig(
            db_role=db_role,
            db_name=db_name,
            db_host=db_host,
            db_user_pw=db_user_pw,
            db_driver=db_driver,
            db_port=db_port,
            **kwargs,
        )

    # Use provided factory or create a new one
    engine_factory = factory or AsyncEngineFactory(logger=logger)
    log = logger or logging.getLogger(__name__)

    attempt = 0
    engine = None
    last_error = None

    while attempt < max_retries:
        try:
            # Create engine with the configuration
            engine = engine_factory.create_engine(connection_config)

            # Create async connection with specified isolation level
            async with engine.connect().execution_options(
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
                await asyncio.sleep(delay)
            else:
                log.error(
                    f"Failed to connect after {max_retries} attempts. "
                    f"Last error: {e}"
                )

        finally:
            # Always dispose of the engine
            if engine:
                await engine.dispose()

    # If we've exhausted all attempts, raise the last error
    if attempt >= max_retries and last_error is not None:
        raise last_error
