"""
Service implementations for SQL generation.

This module provides services for creating and managing SQL emitters
through dependency injection.
"""

import logging
from typing import Dict, Type, Optional, List, Any

from uno.dependencies.interfaces import UnoConfigProtocol
from uno.database.config import ConnectionConfig
from uno.sql.emitter import SQLEmitter
from uno.sql.statement import SQLStatement


class SQLEmitterFactoryService:
    """
    Factory service for creating SQL emitters.
    
    This service provides a centralized way to create SQL emitters
    with proper configuration and logging, making them easier to
    use and test.
    """
    
    def __init__(
        self,
        config: UnoConfigProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SQL emitter factory service.
        
        Args:
            config: Configuration provider
            logger: Optional logger
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._emitter_registry: Dict[str, Type[SQLEmitter]] = {}
        
    def register_emitter(self, name: str, emitter_class: Type[SQLEmitter]) -> None:
        """
        Register an SQL emitter class with the factory.
        
        Args:
            name: Name to register the emitter under
            emitter_class: The emitter class to register
        """
        self.logger.debug(f"Registering SQL emitter: {name}")
        self._emitter_registry[name] = emitter_class
        
    def get_emitter(
        self, 
        name: str, 
        connection_config: Optional[ConnectionConfig] = None,
        **kwargs
    ) -> SQLEmitter:
        """
        Create a new instance of a registered SQL emitter.
        
        Args:
            name: Name of the emitter to create
            connection_config: Optional connection configuration
            **kwargs: Additional arguments to pass to the emitter constructor
            
        Returns:
            A configured SQL emitter instance
            
        Raises:
            ValueError: If the emitter is not registered
        """
        if name not in self._emitter_registry:
            raise ValueError(f"SQL emitter not registered: {name}")
            
        # Create connection config if not provided
        if connection_config is None:
            connection_config = ConnectionConfig(
                db_name=self.config.get_value("DB_NAME"),
                db_role=self.config.get_value("DB_ROLE", f"{self.config.get_value('DB_NAME')}_admin"),
                db_user_pw=self.config.get_value("DB_USER_PW"),
                db_host=self.config.get_value("DB_HOST"),
                db_port=self.config.get_value("DB_PORT"),
                db_driver=self.config.get_value("DB_SYNC_DRIVER"),
                db_schema=self.config.get_value("DB_SCHEMA")
            )
            
        # Create the emitter
        emitter_class = self._emitter_registry[name]
        emitter = emitter_class(
            connection_config=connection_config,
            logger=self.logger,
            **kwargs
        )
        
        self.logger.debug(f"Created SQL emitter: {name}")
        return emitter
        
    def create_emitter_instance(
        self,
        emitter_class: Type[SQLEmitter],
        connection_config: Optional[ConnectionConfig] = None,
        **kwargs
    ) -> SQLEmitter:
        """
        Create a new emitter instance from a class.
        
        Args:
            emitter_class: The emitter class to instantiate
            connection_config: Optional connection configuration
            **kwargs: Additional arguments to pass to the emitter constructor
            
        Returns:
            A configured SQL emitter instance
        """
        # Create connection config if not provided
        if connection_config is None:
            connection_config = ConnectionConfig(
                db_name=self.config.get_value("DB_NAME"),
                db_role=self.config.get_value("DB_ROLE", f"{self.config.get_value('DB_NAME')}_admin"),
                db_user_pw=self.config.get_value("DB_USER_PW"),
                db_host=self.config.get_value("DB_HOST"),
                db_port=self.config.get_value("DB_PORT"),
                db_driver=self.config.get_value("DB_SYNC_DRIVER"),
                db_schema=self.config.get_value("DB_SCHEMA")
            )
            
        # Create the emitter
        emitter = emitter_class(
            connection_config=connection_config,
            logger=self.logger,
            **kwargs
        )
        
        self.logger.debug(f"Created SQL emitter: {emitter_class.__name__}")
        return emitter
        
    def register_core_emitters(self) -> None:
        """
        Register all core SQL emitters with the factory.
        
        This registers the standard emitters that ship with Uno.
        """
        # Import emitters only when needed
        from uno.sql.emitters.database import (
            CreateRolesAndDatabase,
            CreateSchemasAndExtensions,
            RevokeAndGrantPrivilegesAndSetSearchPaths,
            DropDatabaseAndRoles,
            CreatePGULID,
            CreateTokenSecret
        )
        from uno.sql.emitters.table import InsertMetaRecordFunction
        from uno.sql.emitters.triggers import RecordUserAuditFunction
        
        # Register database emitters
        self.register_emitter("create_roles_and_database", CreateRolesAndDatabase)
        self.register_emitter("create_schemas_and_extensions", CreateSchemasAndExtensions)
        self.register_emitter("revoke_and_grant_privileges", RevokeAndGrantPrivilegesAndSetSearchPaths)
        self.register_emitter("drop_database_and_roles", DropDatabaseAndRoles)
        self.register_emitter("create_pgulid", CreatePGULID)
        self.register_emitter("create_token_secret", CreateTokenSecret)
        
        # Register table emitters
        self.register_emitter("insert_meta_record", InsertMetaRecordFunction)
        
        # Register trigger emitters
        self.register_emitter("record_user_audit", RecordUserAuditFunction)
        
    def execute_emitter(
        self,
        emitter: SQLEmitter,
        dry_run: bool = False
    ) -> Optional[List[SQLStatement]]:
        """
        Execute an SQL emitter using the DBManager.
        
        Args:
            emitter: The emitter to execute
            dry_run: If True, return statements without executing
            
        Returns:
            List of SQL statements if dry_run is True, None otherwise
        """
        from uno.dependencies.database import get_db_manager
        
        if dry_run:
            # Just generate SQL without executing
            return emitter.generate_sql()
            
        # Execute using the DBManager
        db_manager = get_db_manager()
        db_manager.execute_from_emitter(emitter)
        return None


class SQLExecutionService:
    """
    Service for executing SQL statements and scripts.
    
    This service provides a higher-level interface for executing
    SQL statements using the DBManager with additional features
    like validation and logging.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SQL execution service.
        
        Args:
            logger: Optional logger
        """
        self.logger = logger or logging.getLogger(__name__)
        
    def execute_ddl(self, ddl: str) -> None:
        """
        Execute a DDL statement.
        
        Args:
            ddl: The DDL statement to execute
        """
        from uno.dependencies.database import get_db_manager
        db_manager = get_db_manager()
        db_manager.execute_ddl(ddl)
        
    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script.
        
        Args:
            script: The SQL script to execute
        """
        from uno.dependencies.database import get_db_manager
        db_manager = get_db_manager()
        db_manager.execute_script(script)
        
    def execute_emitter(
        self,
        emitter: SQLEmitter,
        dry_run: bool = False
    ) -> Optional[List[SQLStatement]]:
        """
        Execute an SQL emitter.
        
        Args:
            emitter: The emitter to execute
            dry_run: If True, return statements without executing
            
        Returns:
            List of SQL statements if dry_run is True, None otherwise
        """
        from uno.dependencies.database import get_db_manager
        
        if dry_run:
            # Just generate SQL without executing
            return emitter.generate_sql()
            
        # Execute using the DBManager
        db_manager = get_db_manager()
        db_manager.execute_from_emitter(emitter)
        return None