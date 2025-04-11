# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import logging
from contextlib import contextmanager

from uno.settings import uno_settings
from uno.database.engine import SyncEngineFactory
from uno.database.manager import DBManager as InitDBManager  # Renamed to avoid confusion
from uno.database.db_manager import DBManager  # Our new DBManager for DDL operations
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
from uno.sql.emitters.table import InsertMetaRecordFunction
from uno.meta.sqlconfigs import MetaTypeSQLConfig
from uno.database.config import ConnectionConfig

# Initialize a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize the engine factory with the logger
engine_factory = SyncEngineFactory(logger=logger)

# Import vector emitters
from uno.sql.emitters.vector import VectorSQLEmitter, VectorIntegrationEmitter, CreateVectorTables

# Define all needed SQL emitters
sql_emitters = {
    "drop_database_and_roles": DropDatabaseAndRoles,
    "create_roles_and_database": CreateRolesAndDatabase,
    "create_schemas_and_extensions": CreateSchemasAndExtensions,
    "revoke_and_grant_privileges": RevokeAndGrantPrivilegesAndSetSearchPaths,
    "set_role": SetRole,
    "create_token_secret": CreateTokenSecret,
    "create_pgulid": CreatePGULID,
    "grant_privileges": GrantPrivileges,
    "insert_meta_record": InsertMetaRecordFunction,
    "meta_type": MetaTypeSQLConfig,
    "vector_extension": VectorSQLEmitter,
    "vector_integration": VectorIntegrationEmitter,
    "vector_tables": CreateVectorTables,
}

# Instantiate InitDBManager for database initialization
init_db_manager = InitDBManager(
    config=uno_settings,
    logger=logger,
    engine_factory=engine_factory,
    sql_emitters=sql_emitters,
)

# Function to provide a connection for the new DBManager
@contextmanager
def get_db_connection():
    """Provide a connection for the DBManager."""
    conn_config = ConnectionConfig(
        db_role=uno_settings.DB_USER,  # Use the configured user
        db_user_pw=uno_settings.DB_USER_PW,
        db_host=uno_settings.DB_HOST,
        db_port=uno_settings.DB_PORT,
        db_name=uno_settings.DB_NAME, 
        db_driver=uno_settings.DB_SYNC_DRIVER,
    )
    with engine_factory.create_sync_connection(conn_config) as conn:
        yield conn

# The new DBManager for post-initialization DDL operations
# This is optional and can be used for additional DDL operations after initialization
ddl_manager = DBManager(
    connection_provider=get_db_connection,
    logger=logger
)

if __name__ == "__main__":
    import psycopg
    
    # Check if the user has adequate permissions
    logger.info(f"Running as database user: {uno_settings.DB_USER}")
    
    # Check if the user has createdb privileges
    has_superuser = False
    try:
        conn_string = f"host={uno_settings.DB_HOST} port={uno_settings.DB_PORT} dbname=postgres user={uno_settings.DB_USER} password={uno_settings.DB_USER_PW}"
        with psycopg.connect(conn_string) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT usesuper FROM pg_user WHERE usename = current_user")
            result = cursor.fetchone()
            has_superuser = result and result[0]
            
        if not has_superuser:
            logger.warning(f"User '{uno_settings.DB_USER}' is not a superuser. Some operations may fail.")
            logger.warning("Consider using a superuser account or granting appropriate privileges.")
    except Exception as e:
        logger.warning(f"Could not check superuser status: {e}")
    
    try:
        # First, create the database using the initialization manager
        logger.info("Creating database using initialization manager...")
        init_db_manager.create_db()
        
        logger.info("Database initialization complete.")
        
        # Set up vector search functionality
        logger.info("Setting up vector search functionality...")
        
        try:
            # Connect to the database and set up vector functions
            with get_db_connection() as connection:
                # Execute vector extension setup
                logger.info("Setting up vector extension and functions...")
                vector_extension = VectorSQLEmitter(config=uno_settings, logger=logger)
                for statement in vector_extension.generate_sql():
                    logger.info(f"Executing {statement.name}...")
                    ddl_manager.execute_ddl(statement.sql)
                
                # Create vector tables
                logger.info("Creating vector tables...")
                vector_tables = CreateVectorTables(config=uno_settings, logger=logger)
                for statement in vector_tables.generate_sql():
                    logger.info(f"Executing {statement.name}...")
                    ddl_manager.execute_ddl(statement.sql)
                    
                # Set up vector integration with other database features
                logger.info("Setting up vector integration...")
                vector_integration = VectorIntegrationEmitter(config=uno_settings, logger=logger)
                for statement in vector_integration.generate_sql():
                    logger.info(f"Executing {statement.name}...")
                    ddl_manager.execute_ddl(statement.sql)
                    
            logger.info("Vector search setup complete. Database is ready for use.")
        except Exception as e:
            logger.error(f"Error setting up vector search: {e}")
            logger.error("Please install the pgvector extension first. See INSTALL_PGVECTOR.md for instructions.")
    except Exception as e:
        logger.error(f"Database creation failed: {e}")
        
        if not has_superuser:
            logger.error("This is likely because your user lacks superuser privileges.")
            logger.error("Options:")
            logger.error("1. Run PostgreSQL commands as a superuser to create the database")
            logger.error("2. Grant createdb privileges to your user")
            logger.error("3. Use the Docker setup which handles permissions automatically")
            logger.error("See docker/README.md for Docker setup instructions")
