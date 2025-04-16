"""
Tests for SQL module domain services.

This module contains tests for domain services in the SQL module,
verifying business logic implementation.
"""

import uuid
import pytest
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch, Mock

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
from uno.sql.domain_services import (
    SQLStatementService,
    SQLEmitterService,
    SQLConfigurationService
)

# Import from test_sql_repositories.py to reuse mock repositories
from tests.unit.sql.test_sql_repositories import (
    SQLStatementRepositoryProtocol,
    SQLEmitterRepositoryProtocol, 
    SQLConfigurationRepositoryProtocol,
    MockSQLStatementRepository,
    MockSQLEmitterRepository,
    MockSQLConfigurationRepository
)


class TestSQLStatementService:
    """Tests for SQLStatementService."""
    
    @pytest.fixture
    def repository(self):
        """Create and return a mock repository."""
        return MockSQLStatementRepository()
    
    @pytest.fixture
    def service(self, repository):
        """Create and return the service with mock repository."""
        return SQLStatementService(statement_repository=repository)
    
    @pytest.mark.asyncio
    async def test_create_statement(self, service):
        """Test creating a new statement."""
        result = await service.create_statement(
            name="test_function",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;",
            depends_on=["another_function"]
        )
        
        assert isinstance(result, Success)
        statement = result.value
        assert statement.name == "test_function"
        assert statement.type == SQLStatementType.FUNCTION
        assert "CREATE FUNCTION test_function()" in statement.sql
        assert statement.depends_on == ["another_function"]
    
    @pytest.mark.asyncio
    async def test_create_statement_duplicate_name(self, service):
        """Test creating a statement with a duplicate name."""
        # Create first statement
        await service.create_statement(
            name="duplicate_name",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION duplicate_name() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
        )
        
        # Try to create second statement with same name
        result = await service.create_statement(
            name="duplicate_name",
            type=SQLStatementType.TRIGGER,
            sql="CREATE TRIGGER duplicate_name AFTER INSERT ON users FOR EACH ROW EXECUTE PROCEDURE audit_function();"
        )
        
        assert isinstance(result, Failure)
        assert "already exists" in result.error
    
    @pytest.mark.asyncio
    async def test_update_statement(self, service):
        """Test updating a statement."""
        # Create statement
        create_result = await service.create_statement(
            name="test_function",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
        )
        
        statement = create_result.value
        
        # Update statement
        update_result = await service.update_statement(
            statement_id=statement.id,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN RETURN; END; $$ LANGUAGE PLPGSQL;",
            depends_on=["new_dependency"]
        )
        
        assert isinstance(update_result, Success)
        updated = update_result.value
        assert updated.id == statement.id
        assert updated.name == statement.name
        assert updated.type == statement.type
        assert "BEGIN RETURN;" in updated.sql
        assert updated.depends_on == ["new_dependency"]
    
    @pytest.mark.asyncio
    async def test_update_statement_not_found(self, service):
        """Test updating a non-existent statement."""
        non_existent_id = SQLStatementId(value=str(uuid.uuid4()))
        
        result = await service.update_statement(
            statement_id=non_existent_id,
            sql="NEW SQL"
        )
        
        assert isinstance(result, Failure)
        assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_delete_statement(self, service):
        """Test deleting a statement."""
        # Create statement
        create_result = await service.create_statement(
            name="test_function",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
        )
        
        statement = create_result.value
        
        # Delete statement
        delete_result = await service.delete_statement(statement.id)
        
        assert isinstance(delete_result, Success)
        assert delete_result.value is True
        
        # Verify it's deleted
        get_result = await service.get_statement(statement.id)
        assert isinstance(get_result, Failure)
    
    @pytest.mark.asyncio
    async def test_execute_statement(self, service):
        """Test executing a statement."""
        # Create statement
        create_result = await service.create_statement(
            name="test_function",
            type=SQLStatementType.FUNCTION,
            sql="CREATE FUNCTION test_function() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
        )
        
        statement = create_result.value
        
        # Mock the execute_sql method
        service.sql_executor.execute_sql = AsyncMock(return_value=Success({
            "rows_affected": 1,
            "duration_ms": 10.5
        }))
        
        # Execute statement
        params = {"param1": "value1", "param2": 42}
        exec_result = await service.execute_statement(statement.id, params)
        
        assert isinstance(exec_result, Success)
        execution = exec_result.value
        assert execution.statement_id == statement.id
        assert execution.success is True
        assert execution.duration_ms == 10.5  # From our mock
        assert "param1" in execution.metadata
        assert "param2" in execution.metadata
        assert execution.metadata["rows_affected"] == 1  # From our mock
        
        # Verify mock was called correctly
        service.sql_executor.execute_sql.assert_called_once_with(statement.sql, params)
    
    @pytest.mark.asyncio
    async def test_execute_statement_not_found(self, service):
        """Test executing a non-existent statement."""
        non_existent_id = SQLStatementId(value=str(uuid.uuid4()))
        
        result = await service.execute_statement(non_existent_id)
        
        assert isinstance(result, Failure)
        assert "Cannot execute statement" in result.error


class TestSQLEmitterService:
    """Tests for SQLEmitterService."""
    
    @pytest.fixture
    def emitter_repository(self):
        """Create and return a mock emitter repository."""
        return MockSQLEmitterRepository()
    
    @pytest.fixture
    def config_repository(self):
        """Create and return a mock configuration repository."""
        return MockSQLConfigurationRepository()
    
    @pytest.fixture
    def statement_repository(self):
        """Create and return a mock statement repository."""
        return MockSQLStatementRepository()
    
    @pytest.fixture
    def service(self, emitter_repository, config_repository, statement_repository):
        """Create and return the service with mock repositories."""
        return SQLEmitterService(
            emitter_repository=emitter_repository,
            config_repository=config_repository,
            statement_repository=statement_repository
        )
    
    @pytest.fixture
    def config_service(self, config_repository, emitter_repository):
        """Create and return a configuration service for testing."""
        return SQLConfigurationService(
            config_repository=config_repository,
            emitter_repository=emitter_repository
        )
    
    @pytest.mark.asyncio
    async def test_create_emitter(self, service):
        """Test creating a new emitter."""
        result = await service.create_emitter(
            name="function_emitter",
            description="Emits SQL functions",
            statement_types=[SQLStatementType.FUNCTION, SQLStatementType.PROCEDURE],
            configuration={"schema": "public"}
        )
        
        assert isinstance(result, Success)
        emitter = result.value
        assert emitter.name == "function_emitter"
        assert emitter.description == "Emits SQL functions"
        assert SQLStatementType.FUNCTION in emitter.statement_types
        assert SQLStatementType.PROCEDURE in emitter.statement_types
        assert emitter.configuration == {"schema": "public"}
    
    @pytest.mark.asyncio
    async def test_create_emitter_duplicate_name(self, service):
        """Test creating an emitter with a duplicate name."""
        # Create first emitter
        await service.create_emitter(
            name="duplicate_name",
            statement_types=[SQLStatementType.FUNCTION]
        )
        
        # Try to create second emitter with same name
        result = await service.create_emitter(
            name="duplicate_name",
            statement_types=[SQLStatementType.TRIGGER]
        )
        
        assert isinstance(result, Failure)
        assert "already exists" in result.error
    
    @pytest.mark.asyncio
    async def test_update_emitter(self, service):
        """Test updating an emitter."""
        # Create emitter
        create_result = await service.create_emitter(
            name="function_emitter",
            description="Emits SQL functions",
            statement_types=[SQLStatementType.FUNCTION],
            configuration={"schema": "public"}
        )
        
        emitter = create_result.value
        
        # Update emitter
        update_result = await service.update_emitter(
            emitter_id=emitter.id,
            name="updated_emitter",
            description="Updated description",
            statement_types=[SQLStatementType.FUNCTION, SQLStatementType.TRIGGER],
            configuration={"schema": "custom", "new_setting": True}
        )
        
        assert isinstance(update_result, Success)
        updated = update_result.value
        assert updated.id == emitter.id
        assert updated.name == "updated_emitter"
        assert updated.description == "Updated description"
        assert SQLStatementType.FUNCTION in updated.statement_types
        assert SQLStatementType.TRIGGER in updated.statement_types
        assert updated.configuration == {"schema": "custom", "new_setting": True}
    
    @pytest.mark.asyncio
    async def test_update_emitter_duplicate_name(self, service):
        """Test updating an emitter with a duplicate name."""
        # Create first emitter
        await service.create_emitter(
            name="first_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        
        # Create second emitter
        create_result = await service.create_emitter(
            name="second_emitter",
            statement_types=[SQLStatementType.TRIGGER]
        )
        
        emitter = create_result.value
        
        # Try to update second emitter with name of first
        result = await service.update_emitter(
            emitter_id=emitter.id,
            name="first_emitter"
        )
        
        assert isinstance(result, Failure)
        assert "already exists" in result.error
    
    @pytest.mark.asyncio
    async def test_generate_statements(self, service, config_service):
        """Test generating statements with an emitter."""
        # Create emitter
        emitter_result = await service.create_emitter(
            name="function_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        
        emitter = emitter_result.value
        
        # Create configuration
        config_result = await config_service.create_configuration(
            name="test_config"
        )
        
        config = config_result.value
        
        # Mock the generator service
        service.statement_generator.generate = AsyncMock(return_value=Success([
            SQLStatement(
                id=SQLStatementId(value=str(uuid.uuid4())),
                name=f"generated_{emitter.name}_1",
                type=SQLStatementType.FUNCTION,
                sql=f"-- Generated statement 1\nCREATE FUNCTION test_1() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
            ),
            SQLStatement(
                id=SQLStatementId(value=str(uuid.uuid4())),
                name=f"generated_{emitter.name}_2",
                type=SQLStatementType.FUNCTION,
                sql=f"-- Generated statement 2\nCREATE FUNCTION test_2() RETURNS VOID AS $$ BEGIN NULL; END; $$ LANGUAGE PLPGSQL;"
            )
        ]))
        
        # Generate statements
        params = {"schema": "public", "prefix": "test"}
        result = await service.generate_statements(
            emitter_id=emitter.id,
            config_id=config.id,
            parameters=params
        )
        
        assert isinstance(result, Success)
        statements = result.value
        assert len(statements) == 2
        assert all(isinstance(s, SQLStatement) for s in statements)
        assert all(s.type == SQLStatementType.FUNCTION for s in statements)
        assert all("generated_" in s.name for s in statements)
        
        # Verify mock was called correctly
        service.statement_generator.generate.assert_called_once_with(emitter, config, params)
    
    @pytest.mark.asyncio
    async def test_generate_statements_invalid_emitter(self, service, config_service):
        """Test generating statements with an invalid emitter."""
        # Create configuration
        config_result = await config_service.create_configuration(
            name="test_config"
        )
        
        config = config_result.value
        
        # Try to generate statements with invalid emitter
        non_existent_id = SQLEmitterId(value=str(uuid.uuid4()))
        result = await service.generate_statements(
            emitter_id=non_existent_id,
            config_id=config.id
        )
        
        assert isinstance(result, Failure)
        assert "Cannot generate statements" in result.error


class TestSQLConfigurationService:
    """Tests for SQLConfigurationService."""
    
    @pytest.fixture
    def config_repository(self):
        """Create and return a mock configuration repository."""
        return MockSQLConfigurationRepository()
    
    @pytest.fixture
    def emitter_repository(self):
        """Create and return a mock emitter repository."""
        return MockSQLEmitterRepository()
    
    @pytest.fixture
    def service(self, config_repository, emitter_repository):
        """Create and return the service with mock repositories."""
        return SQLConfigurationService(
            config_repository=config_repository,
            emitter_repository=emitter_repository
        )
    
    @pytest.fixture
    def emitter_service(self, emitter_repository, config_repository, statement_repository):
        """Create an emitter service for testing."""
        return SQLEmitterService(
            emitter_repository=emitter_repository,
            config_repository=config_repository,
            statement_repository=statement_repository
        )
    
    @pytest.fixture
    def statement_repository(self):
        """Create and return a mock statement repository."""
        return MockSQLStatementRepository()
    
    @pytest.mark.asyncio
    async def test_create_configuration(self, service):
        """Test creating a new configuration."""
        result = await service.create_configuration(
            name="test_config",
            description="Test configuration",
            metadata={"version": "1.0"}
        )
        
        assert isinstance(result, Success)
        config = result.value
        assert config.name == "test_config"
        assert config.description == "Test configuration"
        assert config.metadata == {"version": "1.0"}
        assert config.connection_info is not None
        assert config.connection_info.db_name == "test_config"
        assert len(config.emitters) == 0
    
    @pytest.mark.asyncio
    async def test_create_configuration_with_connection_info(self, service):
        """Test creating a configuration with connection info."""
        connection_info = DatabaseConnectionInfo(
            db_name="custom_db",
            db_user="custom_user",
            db_host="custom_host",
            db_port=5433
        )
        
        result = await service.create_configuration(
            name="test_config",
            connection_info=connection_info
        )
        
        assert isinstance(result, Success)
        config = result.value
        assert config.connection_info == connection_info
        assert config.connection_info.db_name == "custom_db"
        assert config.connection_info.db_user == "custom_user"
        assert config.connection_info.db_host == "custom_host"
        assert config.connection_info.db_port == 5433
    
    @pytest.mark.asyncio
    async def test_create_configuration_duplicate_name(self, service):
        """Test creating a configuration with a duplicate name."""
        # Create first configuration
        await service.create_configuration(
            name="duplicate_name"
        )
        
        # Try to create second configuration with same name
        result = await service.create_configuration(
            name="duplicate_name"
        )
        
        assert isinstance(result, Failure)
        assert "already exists" in result.error
    
    @pytest.mark.asyncio
    async def test_update_configuration(self, service):
        """Test updating a configuration."""
        # Create configuration
        create_result = await service.create_configuration(
            name="test_config",
            description="Original description",
            metadata={"version": "1.0"}
        )
        
        config = create_result.value
        
        # New connection info
        new_connection = DatabaseConnectionInfo(
            db_name="updated_db",
            db_user="updated_user",
            db_host="updated_host"
        )
        
        # Update configuration
        update_result = await service.update_configuration(
            config_id=config.id,
            name="updated_config",
            description="Updated description",
            connection_info=new_connection,
            metadata={"version": "1.1", "updated": True}
        )
        
        assert isinstance(update_result, Success)
        updated = update_result.value
        assert updated.id == config.id
        assert updated.name == "updated_config"
        assert updated.description == "Updated description"
        assert updated.connection_info == new_connection
        assert updated.metadata == {"version": "1.1", "updated": True}
    
    @pytest.mark.asyncio
    async def test_add_emitter_to_configuration(self, service, emitter_service):
        """Test adding an emitter to a configuration."""
        # Create configuration
        config_result = await service.create_configuration(
            name="test_config"
        )
        
        config = config_result.value
        
        # Create emitter
        emitter_result = await emitter_service.create_emitter(
            name="test_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        
        emitter = emitter_result.value
        
        # Add emitter to configuration
        result = await service.add_emitter_to_configuration(
            config_id=config.id,
            emitter_id=emitter.id
        )
        
        assert isinstance(result, Success)
        updated_config = result.value
        assert len(updated_config.emitters) == 1
        assert updated_config.emitters[0].id == emitter.id
    
    @pytest.mark.asyncio
    async def test_add_emitter_duplicate(self, service, emitter_service):
        """Test adding the same emitter twice."""
        # Create configuration
        config_result = await service.create_configuration(
            name="test_config"
        )
        
        config = config_result.value
        
        # Create emitter
        emitter_result = await emitter_service.create_emitter(
            name="test_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        
        emitter = emitter_result.value
        
        # Add emitter to configuration
        await service.add_emitter_to_configuration(
            config_id=config.id,
            emitter_id=emitter.id
        )
        
        # Add same emitter again
        result = await service.add_emitter_to_configuration(
            config_id=config.id,
            emitter_id=emitter.id
        )
        
        assert isinstance(result, Success)
        updated_config = result.value
        assert len(updated_config.emitters) == 1  # Still only 1 emitter
    
    @pytest.mark.asyncio
    async def test_remove_emitter_from_configuration(self, service, emitter_service):
        """Test removing an emitter from a configuration."""
        # Create configuration
        config_result = await service.create_configuration(
            name="test_config"
        )
        
        config = config_result.value
        
        # Create emitter
        emitter_result = await emitter_service.create_emitter(
            name="test_emitter",
            statement_types=[SQLStatementType.FUNCTION]
        )
        
        emitter = emitter_result.value
        
        # Add emitter to configuration
        await service.add_emitter_to_configuration(
            config_id=config.id,
            emitter_id=emitter.id
        )
        
        # Remove emitter from configuration
        result = await service.remove_emitter_from_configuration(
            config_id=config.id,
            emitter_id=emitter.id
        )
        
        assert isinstance(result, Success)
        updated_config = result.value
        assert len(updated_config.emitters) == 0
    
    @pytest.mark.asyncio
    async def test_remove_emitter_not_found(self, service):
        """Test removing a non-existent emitter from a configuration."""
        # Create configuration
        config_result = await service.create_configuration(
            name="test_config"
        )
        
        config = config_result.value
        
        # Try to remove non-existent emitter
        non_existent_id = SQLEmitterId(value=str(uuid.uuid4()))
        result = await service.remove_emitter_from_configuration(
            config_id=config.id,
            emitter_id=non_existent_id
        )
        
        assert isinstance(result, Failure)
        assert "not found in configuration" in result.error