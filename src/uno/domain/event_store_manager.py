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
from uno.database.engine.factory import create_engine


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
        
        # Create an engine for executing the statements
        engine = create_engine(self.config)
        connection = engine.connect()
        
        try:
            # Execute each statement in a transaction
            with connection.begin():
                for statement in statements:
                    self.logger.debug(f"Executing SQL: {statement.name}")
                    connection.execute(statement.sql)
            
            self.logger.info("Event store schema created successfully")
        
        except Exception as e:
            self.logger.error(f"Error creating event store schema: {e}")
            raise
        
        finally:
            connection.close()
    
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