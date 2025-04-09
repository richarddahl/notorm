@asynccontextmanager
async def async_connection(
    db_driver: str = uno_settings.DB_ASYNC_DRIVER,
    db_name: str = uno_settings.DB_NAME,
    db_user_pw: str = uno_settings.DB_USER_PW,
    db_role: str = f"{uno_settings.DB_NAME}_login",
    config: Optional[ConnectionConfig] = None,
    isolation_level: str = "AUTOCOMMIT",
    factory: Optional[AsyncEngineFactory] = None,
    max_retries: int = 3,
    retry_delay: int = 2,
    logger: Optional[Logger] = None,
    **kwargs,
) -> AsyncIterator[AsyncConnection]:
    """
    Async context manager for database connections.

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
        AsyncConnection: Active database connection

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
    engine_factory = factory or AsyncEngineFactory(logger=logger)
    log = logger or logging.getLogger(__name__)

    attempt = 0
    engine = None
    last_error = None

    while attempt < max_retries:
        try:
            # Create engine with the configuration
            engine = engine_factory.create_engine(connection_config)

            # Create connection with specified isolation level
            async with engine.connect().execution_options(
                isolation_level=isolation_level
            ) as conn:
                # Execute callbacks
                await engine_factory.execute_callbacks(conn)

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
