def create_engine(self, config: ConnectionConfig) -> AsyncEngine:
    """
    Create a SQLAlchemy async engine with the given configuration.

    Args:
        config: Connection configuration

    Returns:
        AsyncEngine: SQLAlchemy async engine
    """
    # Construct the connection URL
    url = URL.create(
        drivername=config.db_driver,
        username=config.db_role,
        password=config.db_user_pw,
        host=config.db_host,
        port=config.db_port,
        database=config.db_name,
    )

    # Create the engine with the specified parameters
    engine = create_async_engine(
        url,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
        pool_recycle=config.pool_recycle,
        connect_args=config.connect_args or {},
    )

    # Store the engine for later use
    self.engine = engine
    return engine