"""
Tests for the Reports repositories.

This module contains tests for the repository implementations in the reports module.
"""

import pytest
import uuid
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from uno.core.errors.result import Result, Success, Failure
from uno.reports.entities import (
    # Enum values
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
    ReportExecutionStatus,
    
    # Domain entities
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution
)
from uno.reports.domain_repositories import (
    ReportFieldDefinitionRepository,
    ReportTemplateRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository
)


# Mock database session for testing
class MockDBSession:
    """Mock database session for testing."""

    def __init__(self):
        """Initialize with empty collections."""
        self.field_definitions = {}
        self.templates = {}
        self.triggers = {}
        self.outputs = {}
        self.executions = {}
        self.output_executions = {}
        
    async def fetch_one(self, query, params=None):
        """Fetch a single row based on query and parameters."""
        table_name = self._extract_table_name(query)
        if not table_name:
            return None
            
        if table_name == "report_field_definition" and "id" in params:
            return self.field_definitions.get(params["id"])
        elif table_name == "report_template" and "id" in params:
            return self.templates.get(params["id"])
        elif table_name == "report_trigger" and "id" in params:
            return self.triggers.get(params["id"])
        elif table_name == "report_output" and "id" in params:
            return self.outputs.get(params["id"])
        elif table_name == "report_execution" and "id" in params:
            return self.executions.get(params["id"])
        elif table_name == "report_output_execution" and "id" in params:
            return self.output_executions.get(params["id"])
        
        return None
    
    async def fetch_all(self, query, params=None):
        """Fetch multiple rows based on query and parameters."""
        table_name = self._extract_table_name(query)
        if not table_name:
            return []
            
        if "report_field_definition fd JOIN report_template__field" in query and "template_id" in params:
            # Handle the complex template-field relationship query
            template_id = params["template_id"]
            return [fd for fd in self.field_definitions.values() 
                     if hasattr(fd, "report_templates_ids") and template_id in fd.report_templates_ids]
        
        if table_name == "report_field_definition":
            results = list(self.field_definitions.values())
        elif table_name == "report_template":
            results = list(self.templates.values())
        elif table_name == "report_trigger":
            results = list(self.triggers.values())
        elif table_name == "report_output":
            results = list(self.outputs.values())
        elif table_name == "report_execution":
            results = list(self.executions.values())
        elif table_name == "report_output_execution":
            results = list(self.output_executions.values())
        else:
            return []
        
        # Filter results based on params if provided
        if params:
            filtered_results = []
            for row in results:
                include = True
                for key, val in params.items():
                    if hasattr(row, key) and getattr(row, key) != val:
                        include = False
                        break
                if include:
                    filtered_results.append(row)
            return filtered_results
        
        return results
    
    async def execute(self, query, params=None):
        """Execute a query that doesn't return results."""
        return MagicMock(rowcount=1)
    
    def _extract_table_name(self, query):
        """Extract table name from SQL query."""
        query = query.lower()
        if "from report_field_definition" in query:
            return "report_field_definition"
        elif "from report_template" in query:
            return "report_template"
        elif "from report_trigger" in query:
            return "report_trigger"
        elif "from report_output" in query:
            return "report_output"
        elif "from report_execution" in query:
            return "report_execution"
        elif "from report_output_execution" in query:
            return "report_output_execution"
        return None


# Test fixtures
@pytest.fixture
def db_session():
    """Create a mock database session."""
    return MockDBSession()


@pytest.fixture
def mock_db(db_session):
    """Create a mock database with the session."""
    db = MagicMock()
    db.fetch_one = db_session.fetch_one
    db.fetch_all = db_session.fetch_all
    db.execute = db_session.execute
    return db


@pytest.fixture
def field_definition_id():
    """Create a field definition ID."""
    return str(uuid.uuid4())


@pytest.fixture
def field_definition_dict(field_definition_id):
    """Create a field definition dictionary for the mock database."""
    return {
        "id": field_definition_id,
        "name": "customer_name",
        "display": "Customer Name",
        "field_type": ReportFieldType.DB_COLUMN,
        "field_config": {"table": "customers", "column": "name"},
        "description": "Customer full name",
        "order": 1,
        "format_string": "{0}",
        "conditional_formats": None,
        "is_visible": True,
        "parent_field_id": None
    }


@pytest.fixture
def field_definition_repository(mock_db):
    """Create a field definition repository with the mock DB."""
    repo = ReportFieldDefinitionRepository(db=mock_db)
    # Patch the _create_entity_from_row method to convert dict to entity
    repo._create_entity_from_row = lambda row: ReportFieldDefinition(**row)
    return repo


@pytest.fixture
def template_id():
    """Create a template ID."""
    return str(uuid.uuid4())


@pytest.fixture
def template_dict(template_id):
    """Create a template dictionary for the mock database."""
    return {
        "id": template_id,
        "name": "Customer Report",
        "description": "Report showing customer information",
        "base_object_type": "customer",
        "format_config": {"title": "Customer Information Report"},
        "parameter_definitions": {
            "start_date": {"type": "date", "display": "Start Date", "required": True},
            "end_date": {"type": "date", "display": "End Date", "required": True}
        },
        "version": "1.0.0"
    }


@pytest.fixture
def template_repository(mock_db):
    """Create a template repository with the mock DB."""
    repo = ReportTemplateRepository(db=mock_db)
    # Patch the _create_entity_from_row method to convert dict to entity
    repo._create_entity_from_row = lambda row: ReportTemplate(**row)
    return repo


@pytest.fixture
def trigger_id():
    """Create a trigger ID."""
    return str(uuid.uuid4())


@pytest.fixture
def trigger_dict(trigger_id, template_id):
    """Create a trigger dictionary for the mock database."""
    return {
        "id": trigger_id,
        "report_template_id": template_id,
        "trigger_type": ReportTriggerType.SCHEDULED,
        "trigger_config": {"timezone": "UTC"},
        "schedule": "0 9 * * 1",  # Every Monday at 9am
        "is_active": True,
        "event_type": None,
        "entity_type": None,
        "query_id": None,
        "last_triggered": None
    }


@pytest.fixture
def trigger_repository(mock_db):
    """Create a trigger repository with the mock DB."""
    repo = ReportTriggerRepository(db=mock_db)
    # Patch the _create_entity_from_row method to convert dict to entity
    repo._create_entity_from_row = lambda row: ReportTrigger(**row)
    return repo


@pytest.fixture
def output_id():
    """Create an output ID."""
    return str(uuid.uuid4())


@pytest.fixture
def output_dict(output_id, template_id):
    """Create an output dictionary for the mock database."""
    return {
        "id": output_id,
        "report_template_id": template_id,
        "output_type": ReportOutputType.EMAIL,
        "format": ReportFormat.PDF,
        "output_config": {
            "recipients": ["user@example.com"],
            "subject": "Customer Report for {start_date} to {end_date}"
        },
        "format_config": {
            "page_size": "A4",
            "orientation": "portrait"
        },
        "is_active": True
    }


@pytest.fixture
def output_repository(mock_db):
    """Create an output repository with the mock DB."""
    repo = ReportOutputRepository(db=mock_db)
    # Patch the _create_entity_from_row method to convert dict to entity
    repo._create_entity_from_row = lambda row: ReportOutput(**row)
    return repo


@pytest.fixture
def execution_id():
    """Create an execution ID."""
    return str(uuid.uuid4())


@pytest.fixture
def execution_dict(execution_id, template_id):
    """Create an execution dictionary for the mock database."""
    return {
        "id": execution_id,
        "report_template_id": template_id,
        "triggered_by": "user1",
        "trigger_type": ReportTriggerType.MANUAL,
        "parameters": {
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        },
        "status": ReportExecutionStatus.PENDING,
        "started_at": datetime.now(timezone.utc),
        "completed_at": None,
        "error_details": None,
        "row_count": None,
        "execution_time_ms": None,
        "result_hash": None
    }


@pytest.fixture
def execution_repository(mock_db):
    """Create an execution repository with the mock DB."""
    repo = ReportExecutionRepository(db=mock_db)
    # Patch the _create_entity_from_row method to convert dict to entity
    repo._create_entity_from_row = lambda row: ReportExecution(**row)
    return repo


@pytest.fixture
def output_execution_id():
    """Create an output execution ID."""
    return str(uuid.uuid4())


@pytest.fixture
def output_execution_dict(output_execution_id, execution_id, output_id):
    """Create an output execution dictionary for the mock database."""
    return {
        "id": output_execution_id,
        "report_execution_id": execution_id,
        "report_output_id": output_id,
        "status": ReportExecutionStatus.PENDING,
        "completed_at": None,
        "error_details": None,
        "output_location": None,
        "output_size_bytes": None
    }


@pytest.fixture
def output_execution_repository(mock_db):
    """Create an output execution repository with the mock DB."""
    repo = ReportOutputExecutionRepository(db=mock_db)
    # Patch the _create_entity_from_row method to convert dict to entity
    repo._create_entity_from_row = lambda row: ReportOutputExecution(**row)
    return repo


class TestReportFieldDefinitionRepository:
    """Tests for the ReportFieldDefinitionRepository."""
    
    @pytest.mark.asyncio
    async def test_find_by_name(self, field_definition_repository, db_session, field_definition_dict):
        """Test finding a field definition by name."""
        # Arrange
        db_session.field_definitions[field_definition_dict["id"]] = field_definition_dict
        
        # Act
        field = await field_definition_repository.find_by_name("customer_name")
        
        # Assert
        assert field is not None
        assert field.id == field_definition_dict["id"]
        assert field.name == "customer_name"
    
    @pytest.mark.asyncio
    async def test_find_by_name_not_found(self, field_definition_repository):
        """Test finding a field definition by name when it doesn't exist."""
        # Act
        field = await field_definition_repository.find_by_name("non_existent")
        
        # Assert
        assert field is None
    
    @pytest.mark.asyncio
    async def test_find_by_field_type(self, field_definition_repository, db_session, field_definition_dict):
        """Test finding field definitions by field type."""
        # Arrange
        db_session.field_definitions[field_definition_dict["id"]] = field_definition_dict
        # Add another field definition with the same type
        field2_id = str(uuid.uuid4())
        field2_dict = field_definition_dict.copy()
        field2_dict.update({
            "id": field2_id,
            "name": "customer_email",
            "display": "Customer Email"
        })
        db_session.field_definitions[field2_id] = field2_dict
        
        # Act
        fields = await field_definition_repository.find_by_field_type(ReportFieldType.DB_COLUMN)
        
        # Assert
        assert len(fields) == 2
        assert any(f.id == field_definition_dict["id"] for f in fields)
        assert any(f.id == field2_id for f in fields)
    
    @pytest.mark.asyncio
    async def test_find_by_parent_field_id(self, field_definition_repository, db_session, field_definition_dict):
        """Test finding field definitions by parent field ID."""
        # Arrange
        parent_id = field_definition_dict["id"]
        db_session.field_definitions[parent_id] = field_definition_dict
        # Add a child field
        child_id = str(uuid.uuid4())
        child_dict = {
            "id": child_id,
            "name": "customer_email",
            "display": "Customer Email",
            "field_type": ReportFieldType.DB_COLUMN,
            "field_config": {"table": "customers", "column": "email"},
            "parent_field_id": parent_id
        }
        db_session.field_definitions[child_id] = child_dict
        
        # Act
        fields = await field_definition_repository.find_by_parent_field_id(parent_id)
        
        # Assert
        assert len(fields) == 1
        assert fields[0].id == child_id
        assert fields[0].parent_field_id == parent_id


class TestReportTemplateRepository:
    """Tests for the ReportTemplateRepository."""
    
    @pytest.mark.asyncio
    async def test_find_by_name(self, template_repository, db_session, template_dict):
        """Test finding a template by name."""
        # Arrange
        db_session.templates[template_dict["id"]] = template_dict
        
        # Act
        template = await template_repository.find_by_name("Customer Report")
        
        # Assert
        assert template is not None
        assert template.id == template_dict["id"]
        assert template.name == "Customer Report"
    
    @pytest.mark.asyncio
    async def test_find_by_name_not_found(self, template_repository):
        """Test finding a template by name when it doesn't exist."""
        # Act
        template = await template_repository.find_by_name("non_existent")
        
        # Assert
        assert template is None
    
    @pytest.mark.asyncio
    async def test_find_by_base_object_type(self, template_repository, db_session, template_dict):
        """Test finding templates by base object type."""
        # Arrange
        db_session.templates[template_dict["id"]] = template_dict
        # Add another template with the same base object type
        template2_id = str(uuid.uuid4())
        template2_dict = template_dict.copy()
        template2_dict.update({
            "id": template2_id,
            "name": "Customer Details Report"
        })
        db_session.templates[template2_id] = template2_dict
        
        # Act
        templates = await template_repository.find_by_base_object_type("customer")
        
        # Assert
        assert len(templates) == 2
        assert any(t.id == template_dict["id"] for t in templates)
        assert any(t.id == template2_id for t in templates)


class TestReportTriggerRepository:
    """Tests for the ReportTriggerRepository."""
    
    @pytest.mark.asyncio
    async def test_find_by_template_id(self, trigger_repository, db_session, trigger_dict, template_id):
        """Test finding triggers by template ID."""
        # Arrange
        db_session.triggers[trigger_dict["id"]] = trigger_dict
        
        # Act
        triggers = await trigger_repository.find_by_template_id(template_id)
        
        # Assert
        assert len(triggers) == 1
        assert triggers[0].id == trigger_dict["id"]
        assert triggers[0].report_template_id == template_id
    
    @pytest.mark.asyncio
    async def test_find_by_trigger_type(self, trigger_repository, db_session, trigger_dict):
        """Test finding triggers by trigger type."""
        # Arrange
        db_session.triggers[trigger_dict["id"]] = trigger_dict
        
        # Act
        triggers = await trigger_repository.find_by_trigger_type(ReportTriggerType.SCHEDULED)
        
        # Assert
        assert len(triggers) == 1
        assert triggers[0].id == trigger_dict["id"]
        assert triggers[0].trigger_type == ReportTriggerType.SCHEDULED
    
    @pytest.mark.asyncio
    async def test_find_active_triggers(self, trigger_repository, db_session, trigger_dict):
        """Test finding active triggers."""
        # Arrange
        db_session.triggers[trigger_dict["id"]] = trigger_dict
        # Add an inactive trigger
        inactive_id = str(uuid.uuid4())
        inactive_dict = trigger_dict.copy()
        inactive_dict.update({
            "id": inactive_id,
            "is_active": False
        })
        db_session.triggers[inactive_id] = inactive_dict
        
        # Act
        triggers = await trigger_repository.find_active_triggers()
        
        # Assert
        assert len(triggers) == 1
        assert triggers[0].id == trigger_dict["id"]
        assert triggers[0].is_active is True
    
    @pytest.mark.asyncio
    async def test_find_active_scheduled_triggers(self, trigger_repository, db_session, trigger_dict):
        """Test finding active scheduled triggers."""
        # Arrange
        db_session.triggers[trigger_dict["id"]] = trigger_dict
        # Add an active event trigger
        event_id = str(uuid.uuid4())
        event_dict = trigger_dict.copy()
        event_dict.update({
            "id": event_id,
            "trigger_type": ReportTriggerType.EVENT,
            "event_type": "user.created"
        })
        db_session.triggers[event_id] = event_dict
        
        # Act
        triggers = await trigger_repository.find_active_scheduled_triggers()
        
        # Assert
        assert len(triggers) == 1
        assert triggers[0].id == trigger_dict["id"]
        assert triggers[0].trigger_type == ReportTriggerType.SCHEDULED


class TestReportOutputRepository:
    """Tests for the ReportOutputRepository."""
    
    @pytest.mark.asyncio
    async def test_find_by_template_id(self, output_repository, db_session, output_dict, template_id):
        """Test finding outputs by template ID."""
        # Arrange
        db_session.outputs[output_dict["id"]] = output_dict
        
        # Act
        outputs = await output_repository.find_by_template_id(template_id)
        
        # Assert
        assert len(outputs) == 1
        assert outputs[0].id == output_dict["id"]
        assert outputs[0].report_template_id == template_id
    
    @pytest.mark.asyncio
    async def test_find_by_output_type(self, output_repository, db_session, output_dict):
        """Test finding outputs by output type."""
        # Arrange
        db_session.outputs[output_dict["id"]] = output_dict
        
        # Act
        outputs = await output_repository.find_by_output_type(ReportOutputType.EMAIL)
        
        # Assert
        assert len(outputs) == 1
        assert outputs[0].id == output_dict["id"]
        assert outputs[0].output_type == ReportOutputType.EMAIL
    
    @pytest.mark.asyncio
    async def test_find_active_outputs(self, output_repository, db_session, output_dict):
        """Test finding active outputs."""
        # Arrange
        db_session.outputs[output_dict["id"]] = output_dict
        # Add an inactive output
        inactive_id = str(uuid.uuid4())
        inactive_dict = output_dict.copy()
        inactive_dict.update({
            "id": inactive_id,
            "is_active": False
        })
        db_session.outputs[inactive_id] = inactive_dict
        
        # Act
        outputs = await output_repository.find_active_outputs()
        
        # Assert
        assert len(outputs) == 1
        assert outputs[0].id == output_dict["id"]
        assert outputs[0].is_active is True


class TestReportExecutionRepository:
    """Tests for the ReportExecutionRepository."""
    
    @pytest.mark.asyncio
    async def test_find_by_template_id(self, execution_repository, db_session, execution_dict, template_id):
        """Test finding executions by template ID."""
        # Arrange
        db_session.executions[execution_dict["id"]] = execution_dict
        
        # Act
        executions = await execution_repository.find_by_template_id(template_id)
        
        # Assert
        assert len(executions) == 1
        assert executions[0].id == execution_dict["id"]
        assert executions[0].report_template_id == template_id
    
    @pytest.mark.asyncio
    async def test_find_by_status(self, execution_repository, db_session, execution_dict):
        """Test finding executions by status."""
        # Arrange
        db_session.executions[execution_dict["id"]] = execution_dict
        
        # Act
        executions = await execution_repository.find_by_status(ReportExecutionStatus.PENDING)
        
        # Assert
        assert len(executions) == 1
        assert executions[0].id == execution_dict["id"]
        assert executions[0].status == ReportExecutionStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_find_by_triggered_by(self, execution_repository, db_session, execution_dict):
        """Test finding executions by triggered by."""
        # Arrange
        db_session.executions[execution_dict["id"]] = execution_dict
        
        # Act
        executions = await execution_repository.find_by_triggered_by("user1")
        
        # Assert
        assert len(executions) == 1
        assert executions[0].id == execution_dict["id"]
        assert executions[0].triggered_by == "user1"
    
    @pytest.mark.asyncio
    async def test_find_recent_executions(self, execution_repository, db_session, execution_dict):
        """Test finding recent executions."""
        # Arrange
        db_session.executions[execution_dict["id"]] = execution_dict
        # Add another execution
        execution2_id = str(uuid.uuid4())
        execution2_dict = execution_dict.copy()
        execution2_dict.update({
            "id": execution2_id
        })
        db_session.executions[execution2_id] = execution2_dict
        
        # Act
        # Note: This test doesn't verify ordering as that would require complex mocking
        executions = await execution_repository.find_recent_executions(limit=2)
        
        # Assert
        assert len(executions) == 2


class TestReportOutputExecutionRepository:
    """Tests for the ReportOutputExecutionRepository."""
    
    @pytest.mark.asyncio
    async def test_find_by_execution_id(self, output_execution_repository, db_session, 
                                        output_execution_dict, execution_id):
        """Test finding output executions by execution ID."""
        # Arrange
        db_session.output_executions[output_execution_dict["id"]] = output_execution_dict
        
        # Act
        output_executions = await output_execution_repository.find_by_execution_id(execution_id)
        
        # Assert
        assert len(output_executions) == 1
        assert output_executions[0].id == output_execution_dict["id"]
        assert output_executions[0].report_execution_id == execution_id
    
    @pytest.mark.asyncio
    async def test_find_by_output_id(self, output_execution_repository, db_session, 
                                     output_execution_dict, output_id):
        """Test finding output executions by output ID."""
        # Arrange
        db_session.output_executions[output_execution_dict["id"]] = output_execution_dict
        
        # Act
        output_executions = await output_execution_repository.find_by_output_id(output_id)
        
        # Assert
        assert len(output_executions) == 1
        assert output_executions[0].id == output_execution_dict["id"]
        assert output_executions[0].report_output_id == output_id
    
    @pytest.mark.asyncio
    async def test_find_by_status(self, output_execution_repository, db_session, output_execution_dict):
        """Test finding output executions by status."""
        # Arrange
        db_session.output_executions[output_execution_dict["id"]] = output_execution_dict
        
        # Act
        output_executions = await output_execution_repository.find_by_status(ReportExecutionStatus.PENDING)
        
        # Assert
        assert len(output_executions) == 1
        assert output_executions[0].id == output_execution_dict["id"]
        assert output_executions[0].status == ReportExecutionStatus.PENDING