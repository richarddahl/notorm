"""
Event store manager for managing the event store schema.

This module provides a manager for creating and managing the event store schema
that leverages Uno's SQL generation capabilities for consistent database management.
"""

import logging
from typing import List, Optional

from uno.settings import uno_settings
from uno.sql.statement import SQLStatement
from uno.sql.emitters.event_store import CreateDomainEventsTable, CreateEventProcessorsTable
from uno.database.engine.factory import AsyncEngineFactory


class EventStoreManager:
    """
    Manager for creating and managing the event store schema.
    
    This class works with the SQLEmitters to generate and execute SQL for
    setting up the event store database objects.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the event store manager.
        
        Args:
            logger: Optional logger for diagnostic information
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = uno_settings
    
    def create_event_store_schema(self) -> None:
        """
        Create the event store schema in the database.
        
        This method generates and executes the SQL for creating the event store
        tables, functions, triggers, and grants needed for the event sourcing system.
        """
        self.logger.info("Creating event store schema...")
        
        # Collect all SQL statements
        statements = self._generate_event_store_sql()
        
        # Use a synchronous connection instead of async
        import psycopg
        from uno.database.config import ConnectionConfig
        
        # Create connection configuration
        conn_config = ConnectionConfig(
            db_role=f"{self.config.DB_NAME}_admin",  # Use admin role
            db_name=self.config.DB_NAME,
            db_host=self.config.DB_HOST,
            db_port=self.config.DB_PORT,
            db_user_pw=self.config.DB_USER_PW,
            db_driver=self.config.DB_SYNC_DRIVER,
            db_schema=self.config.DB_SCHEMA,
        )
        
        # Create direct connection string
        conn_string = (
            f"host={conn_config.db_host} "
            f"port={conn_config.db_port} "
            f"dbname={conn_config.db_name} "
            f"user={conn_config.db_role} "
            f"password={conn_config.db_user_pw}"
        )
        
        try:
            # Connect with autocommit for DDL statements
            with psycopg.connect(conn_string, autocommit=True) as conn:
                cursor = conn.cursor()
                
                # Execute each statement
                for statement in statements:
                    self.logger.debug(f"Executing SQL: {statement.name}")
                    cursor.execute(statement.sql)
                    
            self.logger.info("Event store schema created successfully")
        
        except Exception as e:
            self.logger.error(f"Error creating event store schema: {e}")
            raise
    
    def _generate_event_store_sql(self) -> List[SQLStatement]:
        """
        Generate SQL statements for creating the event store schema.
        
        Returns:
            List of SQL statements to execute
        """
        statements = []
        
        # Create emitters
        emitters = [
            CreateDomainEventsTable(self.config),
            CreateEventProcessorsTable(self.config)
        ]
        
        # Generate SQL from each emitter
        for emitter in emitters:
            statements.extend(emitter.generate_sql())
        
        return statements