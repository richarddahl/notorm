"""
Tests for SQL module repositories.

This module contains tests for repository implementations in the SQL module,
focusing on data access patterns and persistence.
"""

import uuid
import pytest
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import asyncio
from uno.core.result import Result, Success, Failure
from uno.domain.core import Entity, AggregateRoot, ValueObject
from uno.sql.entities import (
    SQLStatementId,
    SQLEmitterId,
    SQLConfigId,
    SQLStatementType,
    SQLStatement,
    SQLExecution,
    SQLEmitter,
    SQLFunction,
    SQLTrigger,
    DatabaseConnectionInfo,
    SQLConfiguration
)


# Define repository protocols
class SQLStatementRepositoryProtocol:
    """Protocol for SQLStatement repository."""
    
    async def get_by_id(self, statement_id: SQLStatementId) -> Result[SQLStatement, str]:
        """Get a SQL statement by ID."""
        pass
    
    async def get_by_name(self, name: str) -> Result[SQLStatement, str]:
        """Get a SQL statement by name."""
        pass
    
    async def list_by_type(self, statement_type: SQLStatementType) -> Result[List[SQLStatement], str]:
        """List SQL statements by type."""
        pass
    
    async def save(self, statement: SQLStatement) -> Result[SQLStatement, str]:
        """Save a SQL statement."""
        pass
    
    async def delete(self, statement_id: SQLStatementId) -> Result[bool, str]:
        """Delete a SQL statement."""
        pass


class SQLEmitterRepositoryProtocol:
    """Protocol for SQLEmitter repository."""
    
    async def get_by_id(self, emitter_id: SQLEmitterId) -> Result[SQLEmitter, str]:
        """Get a SQL emitter by ID."""
        pass
    
    async def get_by_name(self, name: str) -> Result[SQLEmitter, str]:
        """Get a SQL emitter by name."""
        pass
    
    async def list_by_statement_type(self, statement_type: SQLStatementType) -> Result[List[SQLEmitter], str]:
        """List SQL emitters by statement type."""
        pass
    
    async def save(self, emitter: SQLEmitter) -> Result[SQLEmitter, str]:
        """Save a SQL emitter."""
        pass
    
    async def delete(self, emitter_id: SQLEmitterId) -> Result[bool, str]:
        """Delete a SQL emitter."""
        pass


class SQLConfigurationRepositoryProtocol:
    """Protocol for SQLConfiguration repository."""
    
    async def get_by_id(self, config_id: SQLConfigId) -> Result[SQLConfiguration, str]:
        """Get a SQL configuration by ID."""
        pass
    
    async def get_by_name(self, name: str) -> Result[SQLConfiguration, str]:
        """Get a SQL configuration by name."""
        pass
    
    async def list_all(self) -> Result[List[SQLConfiguration], str]:
        """List all SQL configurations."""
        pass
    
    async def save(self, configuration: SQLConfiguration) -> Result[SQLConfiguration, str]:
        """Save a SQL configuration."""
        pass
    
    async def delete(self, config_id: SQLConfigId) -> Result[bool, str]:
        """Delete a SQL configuration."""
        pass


class MockSQLStatementRepository(SQLStatementRepositoryProtocol):
    """Mock implementation of SQLStatementRepository for testing."""
    
    def __init__(self):
        self.statements = {}
    
    async def get_by_id(self, statement_id: SQLStatementId) -> Result[SQLStatement, str]:
        statement = self.statements.get(statement_id.value)
        if statement:
            return Success(statement)
        return Failure(f"SQLStatement with ID {statement_id.value} not found")
    
    async def get_by_name(self, name: str) -> Result[SQLStatement, str]:
        for statement in self.statements.values():
            if statement.name == name:
                return Success(statement)
        return Failure(f"SQLStatement with name {name} not found")
    
    async def list_by_type(self, statement_type: SQLStatementType) -> Result[List[SQLStatement], str]:
        statements = [s for s in self.statements.values() if s.type == statement_type]
        return Success(statements)
    
    async def save(self, statement: SQLStatement) -> Result[SQLStatement, str]:
        self.statements[statement.id.value] = statement
        return Success(statement)
    
    async def delete(self, statement_id: SQLStatementId) -> Result[bool, str]:
        if statement_id.value in self.statements:
            del self.statements[statement_id.value]
            return Success(True)
        return Failure(f"SQLStatement with ID {statement_id.value} not found")


class MockSQLEmitterRepository(SQLEmitterRepositoryProtocol):
    """Mock implementation of SQLEmitterRepository for testing."""
    
    def __init__(self):
        self.emitters = {}
    
    async def get_by_id(self, emitter_id: SQLEmitterId) -> Result[SQLEmitter, str]:
        emitter = self.emitters.get(emitter_id.value)
        if emitter:
            return Success(emitter)
        return Failure(f"SQLEmitter with ID {emitter_id.value} not found")
    
    async def get_by_name(self, name: str) -> Result[SQLEmitter, str]:
        for emitter in self.emitters.values():
            if emitter.name == name:
                return Success(emitter)
        return Failure(f"SQLEmitter with name {name} not found")
    
    async def list_by_statement_type(self, statement_type: SQLStatementType) -> Result[List[SQLEmitter], str]:
        emitters = [
            e for e in self.emitters.values() 
            if any(st == statement_type for st in e.statement_types)
        ]
        return Success(emitters)
    
    async def save(self, emitter: SQLEmitter) -> Result[SQLEmitter, str]:
        self.emitters[emitter.id.value] = emitter
        return Success(emitter)
    
    async def delete(self, emitter_id: SQLEmitterId) -> Result[bool, str]:
        if emitter_id.value in self.emitters:
            del self.emitters[emitter_id.value]
            return Success(True)
        return Failure(f"SQLEmitter with ID {emitter_id.value} not found")


class MockSQLConfigurationRepository(SQLConfigurationRepositoryProtocol):
    """Mock implementation of SQLConfigurationRepository for testing."""
    
    def __init__(self):
        self.configurations = {}
    
    async def get_by_id(self, config_id: SQLConfigId) -> Result[SQLConfiguration, str]:
        config = self.configurations.get(config_id.value)
        if config:
            return Success(config)
        return Failure(f"SQLConfiguration with ID {config_id.value} not found")
    
    async def get_by_name(self, name: str) -> Result[SQLConfiguration, str]:
        for config in self.configurations.values():
            if config.name == name:
                return Success(config)
        return Failure(f"SQLConfiguration with name {name} not found")
    
    async def list_all(self) -> Result[List[SQLConfiguration], str]:
        return Success(list(self.configurations.values()))
    
    async def save(self, configuration: SQLConfiguration) -> Result[SQLConfiguration, str]:
        self.configurations[configuration.id.value] = configuration
        return Success(configuration)
    
    async def delete(self, config_id: SQLConfigId) -> Result[bool, str]:
        if config_id.value in self.configurations:
            del self.configurations[config_id.value]
            return Success(True)
        return Failure(f"SQLConfiguration with ID {config_id.value} not found")


class TestSQLStatementRepository:
    """Tests for SQLStatementRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create and return a mock repository."""
        return MockSQLStatementRepository()
    
    @pytest.fixture
    def statement(self):
        """Create and return a test SQLStatement."""
        return SQLStatement(
            id=SQLStatementId(value=str(uuid.uuid4())),
            name="test_statement",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
        )
    
    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository, statement):
        """Test saving a statement and retrieving it by ID."""
        # Save the statement
        result = await repository.save(statement)
        assert isinstance(result, Success)
        assert result.value == statement
        
        # Retrieve by ID
        result = await repository.get_by_id(statement.id)
        assert isinstance(result, Success)
        assert result.value == statement
        assert result.value.id == statement.id
        assert result.value.name == statement.name
        assert result.value.type == statement.type
        assert result.value.sql == statement.sql
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository):
        """Test retrieving a non-existent statement by ID."""
        non_existent_id = SQLStatementId(value=str(uuid.uuid4()))
        result = await repository.get_by_id(non_existent_id)
        
        assert isinstance(result, Failure)
        assert f"SQLStatement with ID {non_existent_id.value} not found" in result.error
    
    @pytest.mark.asyncio
    async def test_get_by_name(self, repository, statement):
        """Test retrieving a statement by name."""
        # Save the statement
        await repository.save(statement)
        
        # Retrieve by name
        result = await repository.get_by_name(statement.name)
        assert isinstance(result, Success)
        assert result.value == statement
    
    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, repository):
        """Test retrieving a non-existent statement by name."""
        result = await repository.get_by_name("non_existent_name")
        
        assert isinstance(result, Failure)
        assert "SQLStatement with name non_existent_name not found" in result.error
    
    @pytest.mark.asyncio
    async def test_list_by_type(self, repository):
        """Test listing statements by type."""
        # Create and save statements of different types
        statement1 = SQLStatement(
            id=SQLStatementId(value=str(uuid.uuid4())),
            name="function1",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION function1() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
        )
        statement2 = SQLStatement(
            id=SQLStatementId(value=str(uuid.uuid4())),
            name="function2",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION function2() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
        )
        statement3 = SQLStatement(
            id=SQLStatementId(value=str(uuid.uuid4())),
            name="trigger1",
            type=SQLStatementType.TRIGGER,
            sql="CREATE TRIGGER trigger1 AFTER INSERT ON users FOR EACH ROW EXECUTE PROCEDURE audit_function();"
        )
        
        await repository.save(statement1)
        await repository.save(statement2)
        await repository.save(statement3)
        
        # List by function type
        result = await repository.list_by_type(SQLStatementType.FUNCTION)
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert all(s.type == SQLStatementType.FUNCTION for s in result.value)
        
        # List by trigger type
        result = await repository.list_by_type(SQLStatementType.TRIGGER)
        assert isinstance(result, Success)
        assert len(result.value) == 1
        assert all(s.type == SQLStatementType.TRIGGER for s in result.value)
        
        # List by type with no statements
        result = await repository.list_by_type(SQLStatementType.VIEW)
        assert isinstance(result, Success)
        assert len(result.value) == 0
    
    @pytest.mark.asyncio
    async def test_delete(self, repository, statement):
        """Test deleting a statement."""
        # Save the statement
        await repository.save(statement)
        
        # Delete the statement
        result = await repository.delete(statement.id)
        assert isinstance(result, Success)
        assert result.value is True
        
        # Verify it's deleted
        result = await repository.get_by_id(statement.id)
        assert isinstance(result, Failure)
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository):
        """Test deleting a non-existent statement."""
        non_existent_id = SQLStatementId(value=str(uuid.uuid4()))
        result = await repository.delete(non_existent_id)
        
        assert isinstance(result, Failure)
        assert f"SQLStatement with ID {non_existent_id.value} not found" in result.error


class TestSQLEmitterRepository:
    """Tests for SQLEmitterRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create and return a mock repository."""
        return MockSQLEmitterRepository()
    
    @pytest.fixture
    def emitter(self):
        """Create and return a test SQLEmitter."""
        return SQLEmitter(
            id=SQLEmitterId(value=str(uuid.uuid4())),
            name="test_emitter",
            description="Test emitter for functions",
            statement_types=[SQLStatementType.FUNCTION, SQLStatementType.PROCEDURE]
        )
    
    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository, emitter):
        """Test saving an emitter and retrieving it by ID."""
        # Save the emitter
        result = await repository.save(emitter)
        assert isinstance(result, Success)
        assert result.value == emitter
        
        # Retrieve by ID
        result = await repository.get_by_id(emitter.id)
        assert isinstance(result, Success)
        assert result.value == emitter
        assert result.value.id == emitter.id
        assert result.value.name == emitter.name
        assert result.value.description == emitter.description
        assert result.value.statement_types == emitter.statement_types
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository):
        """Test retrieving a non-existent emitter by ID."""
        non_existent_id = SQLEmitterId(value=str(uuid.uuid4()))
        result = await repository.get_by_id(non_existent_id)
        
        assert isinstance(result, Failure)
        assert f"SQLEmitter with ID {non_existent_id.value} not found" in result.error
    
    @pytest.mark.asyncio
    async def test_get_by_name(self, repository, emitter):
        """Test retrieving an emitter by name."""
        # Save the emitter
        await repository.save(emitter)
        
        # Retrieve by name
        result = await repository.get_by_name(emitter.name)
        assert isinstance(result, Success)
        assert result.value == emitter
    
    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, repository):
        """Test retrieving a non-existent emitter by name."""
        result = await repository.get_by_name("non_existent_name")
        
        assert isinstance(result, Failure)
        assert "SQLEmitter with name non_existent_name not found" in result.error
    
    @pytest.mark.asyncio
    async def test_list_by_statement_type(self, repository):
        """Test listing emitters by statement type."""
        # Create and save emitters with different statement types
        emitter1 = SQLEmitter(
            id=SQLEmitterId(value=str(uuid.uuid4())),
            name="function_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        emitter2 = SQLEmitter(
            id=SQLEmitterId(value=str(uuid.uuid4())),
            name="trigger_emitter",
            statement_types=[SQLStatementType.TRIGGER]
        )
        emitter3 = SQLEmitter(
            id=SQLEmitterId(value=str(uuid.uuid4())),
            name="multi_emitter",
            statement_types=[SQLStatementType.FUNCTION, SQLStatementType.TRIGGER, SQLStatementType.VIEW]
        )
        
        await repository.save(emitter1)
        await repository.save(emitter2)
        await repository.save(emitter3)
        
        # List by function type
        result = await repository.list_by_statement_type(SQLStatementType.FUNCTION)
        assert isinstance(result, Success)
        assert len(result.value) == 2  # emitter1 and emitter3
        
        # List by trigger type
        result = await repository.list_by_statement_type(SQLStatementType.TRIGGER)
        assert isinstance(result, Success)
        assert len(result.value) == 2  # emitter2 and emitter3
        
        # List by view type
        result = await repository.list_by_statement_type(SQLStatementType.VIEW)
        assert isinstance(result, Success)
        assert len(result.value) == 1  # only emitter3
        
        # List by type with no emitters
        result = await repository.list_by_statement_type(SQLStatementType.ROLE)
        assert isinstance(result, Success)
        assert len(result.value) == 0
    
    @pytest.mark.asyncio
    async def test_delete(self, repository, emitter):
        """Test deleting an emitter."""
        # Save the emitter
        await repository.save(emitter)
        
        # Delete the emitter
        result = await repository.delete(emitter.id)
        assert isinstance(result, Success)
        assert result.value is True
        
        # Verify it's deleted
        result = await repository.get_by_id(emitter.id)
        assert isinstance(result, Failure)
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository):
        """Test deleting a non-existent emitter."""
        non_existent_id = SQLEmitterId(value=str(uuid.uuid4()))
        result = await repository.delete(non_existent_id)
        
        assert isinstance(result, Failure)
        assert f"SQLEmitter with ID {non_existent_id.value} not found" in result.error


class TestSQLConfigurationRepository:
    """Tests for SQLConfigurationRepository."""
    
    @pytest.fixture
    def repository(self):
        """Create and return a mock repository."""
        return MockSQLConfigurationRepository()
    
    @pytest.fixture
    def configuration(self):
        """Create and return a test SQLConfiguration."""
        connection_info = DatabaseConnectionInfo(
            db_name="testdb",
            db_user="testuser",
            db_host="localhost"
        )
        emitter = SQLEmitter(
            id=SQLEmitterId(value=str(uuid.uuid4())),
            name="test_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        return SQLConfiguration(
            id=SQLConfigId(value=str(uuid.uuid4())),
            name="test_config",
            description="Test configuration",
            connection_info=connection_info,
            emitters=[emitter],
            metadata={"version": "1.0"}
        )
    
    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repository, configuration):
        """Test saving a configuration and retrieving it by ID."""
        # Save the configuration
        result = await repository.save(configuration)
        assert isinstance(result, Success)
        assert result.value == configuration
        
        # Retrieve by ID
        result = await repository.get_by_id(configuration.id)
        assert isinstance(result, Success)
        assert result.value == configuration
        assert result.value.id == configuration.id
        assert result.value.name == configuration.name
        assert result.value.description == configuration.description
        assert result.value.connection_info == configuration.connection_info
        assert len(result.value.emitters) == 1
        assert result.value.metadata == configuration.metadata
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository):
        """Test retrieving a non-existent configuration by ID."""
        non_existent_id = SQLConfigId(value=str(uuid.uuid4()))
        result = await repository.get_by_id(non_existent_id)
        
        assert isinstance(result, Failure)
        assert f"SQLConfiguration with ID {non_existent_id.value} not found" in result.error
    
    @pytest.mark.asyncio
    async def test_get_by_name(self, repository, configuration):
        """Test retrieving a configuration by name."""
        # Save the configuration
        await repository.save(configuration)
        
        # Retrieve by name
        result = await repository.get_by_name(configuration.name)
        assert isinstance(result, Success)
        assert result.value == configuration
    
    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, repository):
        """Test retrieving a non-existent configuration by name."""
        result = await repository.get_by_name("non_existent_name")
        
        assert isinstance(result, Failure)
        assert "SQLConfiguration with name non_existent_name not found" in result.error
    
    @pytest.mark.asyncio
    async def test_list_all(self, repository):
        """Test listing all configurations."""
        # Create and save multiple configurations
        config1 = SQLConfiguration(
            id=SQLConfigId(value=str(uuid.uuid4())),
            name="config1",
            description="First configuration"
        )
        config2 = SQLConfiguration(
            id=SQLConfigId(value=str(uuid.uuid4())),
            name="config2",
            description="Second configuration"
        )
        
        await repository.save(config1)
        await repository.save(config2)
        
        # List all configurations
        result = await repository.list_all()
        assert isinstance(result, Success)
        assert len(result.value) == 2
        assert any(c.name == "config1" for c in result.value)
        assert any(c.name == "config2" for c in result.value)
    
    @pytest.mark.asyncio
    async def test_delete(self, repository, configuration):
        """Test deleting a configuration."""
        # Save the configuration
        await repository.save(configuration)
        
        # Delete the configuration
        result = await repository.delete(configuration.id)
        assert isinstance(result, Success)
        assert result.value is True
        
        # Verify it's deleted
        result = await repository.get_by_id(configuration.id)
        assert isinstance(result, Failure)
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository):
        """Test deleting a non-existent configuration."""
        non_existent_id = SQLConfigId(value=str(uuid.uuid4()))
        result = await repository.delete(non_existent_id)
        
        assert isinstance(result, Failure)
        assert f"SQLConfiguration with ID {non_existent_id.value} not found" in result.error