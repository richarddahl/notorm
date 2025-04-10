"""Alembic environment script for Uno database migrations."""

import os
import sys
import logging
import urllib.parse
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine, text
from alembic import context

# Import Uno configuration and model base
from uno.settings import uno_settings
from uno.model import UnoModel
from uno.database.config import ConnectionConfig
from uno.database.engine import sync_connection, SyncEngineFactory
import uno.attributes.models  # noqa: F401
import uno.authorization.models  # noqa: F401
import uno.meta.models  # noqa: F401
import uno.messaging.models  # noqa: F401
import uno.queries.models  # noqa: F401
import uno.reports.models  # noqa: F401
import uno.values.models  # noqa: F401
import uno.workflows.models  # noqa: F401

# Setup logging - Alembic's default logging might be too verbose
logger = logging.getLogger("alembic.env")

# Load any application models if APP_PATH is defined
if uno_settings.APP_PATH:
    # Add app path to Python path
    sys.path.insert(0, uno_settings.APP_PATH)
    for pkg in uno_settings.LOAD_PACKAGES:
        try:
            __import__(f"{pkg}.models")
        except ImportError:
            logger.warning(f"Could not import models from {pkg}")

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Add model's MetaData object for 'autogenerate' support
target_metadata = UnoModel.metadata

# Build connection URI with properly encoded password
def get_connection_url():
    """Build a SQLAlchemy connection URL with proper encoding."""
    # Use login role with connect permission
    db_role = f"{uno_settings.DB_NAME}_login"
    
    # URL encode the password to handle special characters
    encoded_pw = urllib.parse.quote_plus(uno_settings.DB_USER_PW)
    
    # Determine driver to use
    driver = uno_settings.DB_SYNC_DRIVER
    if driver.startswith("postgresql+"):
        driver = driver.replace("postgresql+", "")
    
    # Build the connection string
    url = f"postgresql+{driver}://{db_role}:{encoded_pw}@{uno_settings.DB_HOST}:{uno_settings.DB_PORT}/{uno_settings.DB_NAME}"
    
    logger.info(f"Using database URL: {url.replace(encoded_pw, '********')}")
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the script output.
    """
    # Get connection URL with properly encoded password
    url = get_connection_url()
    
    def include_set_role(conn, sql):
        # For offline mode, prepend SET ROLE command to each SQL statement
        admin_role = f"{uno_settings.DB_NAME}_admin"
        return f"SET ROLE {admin_role}; {sql}"
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=uno_settings.DB_SCHEMA,
        process_revision_directives=None,
        output_buffer=None,
        starting_rev=None,
        tag=None,
        process_statement=include_set_role  # Process each SQL statement to set role
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a connection with the context.
    We connect with the login role, then switch to admin role for DDL statements.
    """
    try:
        # Get connection URL with properly encoded password
        url = get_connection_url()
        
        # Create engine directly
        engine = create_engine(url, echo=False)
        
        with engine.connect() as connection:
            try:
                # Set role to admin before running migrations
                admin_role = f"{uno_settings.DB_NAME}_admin"
                logger.info(f"Setting role to {admin_role}")
                connection.execute(text(f"SET ROLE {admin_role};"))
                
                # Create a custom migration context that logs each statement
                def process_statement(statement):
                    # For debugging
                    logger.info(f"Executing SQL: {statement[:80]}...")
                    return statement
                
                context.configure(
                    connection=connection,
                    target_metadata=target_metadata,
                    include_schemas=True,
                    version_table_schema=uno_settings.DB_SCHEMA,
                    process_statement=process_statement,  # Optional: for debugging
                )

                with context.begin_transaction():
                    context.run_migrations()
            except Exception as e:
                logger.error(f"Error during migration: {e}")
                raise
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()