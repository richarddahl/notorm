# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Tests for the report domain repositories."""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, patch, MagicMock

from uno.core.errors.result import Result, Success, Failure
from uno.reports.domain_repositories import (
    ReportTemplateRepository,
    ReportFieldDefinitionRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)
from uno.reports.entities import (
    ReportTemplate,
    ReportFieldDefinition,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
    ReportExecutionStatus,
)


# Mock fixtures for testing
@pytest.fixture
def mock_db():
    """Create a mock database session."""
    mock = AsyncMock()
    mock.fetch_all = AsyncMock()
    mock.fetch_one = AsyncMock()
    return mock


@pytest.fixture
def field_definition_repo(mock_db):
    """Create a field definition repository with a mock DB."""
    return ReportFieldDefinitionRepository(mock_db)


@pytest.fixture
def template_repo(mock_db):
    """Create a template repository with a mock DB."""
    return ReportTemplateRepository(mock_db)


@pytest.fixture
def trigger_repo(mock_db):
    """Create a trigger repository with a mock DB."""
    return ReportTriggerRepository(mock_db)


@pytest.fixture
def output_repo(mock_db):
    """Create an output repository with a mock DB."""
    return ReportOutputRepository(mock_db)


@pytest.fixture
def execution_repo(mock_db):
    """Create an execution repository with a mock DB."""
    return ReportExecutionRepository(mock_db)


@pytest.fixture
def output_execution_repo(mock_db):
    """Create an output execution repository with a mock DB."""
    return ReportOutputExecutionRepository(mock_db)


# Entity fixture generators
@pytest.fixture
def create_field_definition():
    """Create a field definition entity for testing."""
    def _create_field(id_=None, name=None, field_type=None, parent_field_id=None):
        return ReportFieldDefinition(
            id=id_ or str(uuid.uuid4()),
            name=name or f"test_field_{uuid.uuid4().hex[:8]}",
            display_name="Test Field",
            field_type=field_type or ReportFieldType.DB_COLUMN,
            field_config={"table": "customer", "column": "name"},
            description="Field for testing",
            order=1,
            format_string=None,
            conditional_formats=None,
            is_visible=True,
            parent_field_id=parent_field_id
        )
    return _create_field


@pytest.fixture
def create_template():
    """Create a template entity for testing."""
    def _create_template(id_=None, name=None, base_object_type=None):
        return ReportTemplate(
            id=id_ or str(uuid.uuid4()),
            name=name or f"Test Template {uuid.uuid4()}",
            description="Template for testing",
            base_object_type=base_object_type or "customer",
            format_config={
                "title_format": "{name} - Generated on {date}",
                "show_footer": True
            },
            parameter_definitions={
                "start_date": {
                    "type": "date",
                    "required": True,
                    "default": "today-30d"
                }
            },
            cache_policy={
                "ttl_seconds": 3600,
                "invalidate_on_event": "customer_updated"
            },
            version="1.0.0"
        )
    return _create_template


@pytest.fixture
def create_trigger():
    """Create a trigger entity for testing."""
    def _create_trigger(id_=None, template_id=None, trigger_type=None):
        return ReportTrigger(
            id=id_ or str(uuid.uuid4()),
            report_template_id=template_id or str(uuid.uuid4()),
            trigger_type=trigger_type or ReportTriggerType.SCHEDULED,
            trigger_config={
                "timezone": "UTC",
                "run_on_holidays": False
            },
            schedule="interval:24:hours",
            is_active=True
        )
    return _create_trigger


@pytest.fixture
def create_output():
    """Create an output entity for testing."""
    def _create_output(id_=None, template_id=None, output_type=None):
        return ReportOutput(
            id=id_ or str(uuid.uuid4()),
            report_template_id=template_id or str(uuid.uuid4()),
            output_type=output_type or ReportOutputType.EMAIL,
            format=ReportFormat.PDF,
            output_config={
                "recipients": ["test@example.com"],
                "subject": "Test Report"
            },
            format_config={
                "page_size": "letter",
                "orientation": "portrait"
            },
            is_active=True
        )
    return _create_output


@pytest.fixture
def create_execution():
    """Create an execution entity for testing."""
    def _create_execution(id_=None, template_id=None, status=None):
        return ReportExecution(
            id=id_ or str(uuid.uuid4()),
            report_template_id=template_id or str(uuid.uuid4()),
            triggered_by="test_user",
            trigger_type=ReportTriggerType.MANUAL,
            parameters={
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            },
            status=status or ReportExecutionStatus.PENDING,
            started_at=datetime.utcnow()
        )
    return _create_execution


@pytest.fixture
def create_output_execution():
    """Create an output execution entity for testing."""
    def _create_output_execution(id_=None, execution_id=None, output_id=None, status=None):
        return ReportOutputExecution(
            id=id_ or str(uuid.uuid4()),
            report_execution_id=execution_id or str(uuid.uuid4()),
            report_output_id=output_id or str(uuid.uuid4()),
            status=status or ReportExecutionStatus.PENDING
        )
    return _create_output_execution


# Test cases
class TestReportFieldDefinitionRepository:
    """Tests for the ReportFieldDefinitionRepository class."""

    async def test_find_by_name(self, field_definition_repo, create_field_definition):
        """Test finding a field definition by name."""
        # Arrange
        field = create_field_definition(name="test_field")
        expected_fields = [field]
        field_definition_repo._db.list.return_value = expected_fields
        
        # Act
        result = await field_definition_repo.find_by_name("test_field")
        
        # Assert
        field_definition_repo._db.list.assert_called_once()
        filters = field_definition_repo._db.list.call_args[1]["filters"]
        assert filters["name"]["lookup"] == "eq"
        assert filters["name"]["val"] == "test_field"
        assert result == field

    async def test_find_by_name_not_found(self, field_definition_repo):
        """Test finding a field definition by name when it doesn't exist."""
        # Arrange
        field_definition_repo._db.list.return_value = []
        
        # Act
        result = await field_definition_repo.find_by_name("non_existent_field")
        
        # Assert
        assert result is None

    async def test_find_by_field_type(self, field_definition_repo, create_field_definition):
        """Test finding field definitions by field type."""
        # Arrange
        fields = [
            create_field_definition(field_type=ReportFieldType.DB_COLUMN),
            create_field_definition(field_type=ReportFieldType.DB_COLUMN)
        ]
        field_definition_repo._db.list.return_value = fields
        
        # Act
        result = await field_definition_repo.find_by_field_type(ReportFieldType.DB_COLUMN)
        
        # Assert
        field_definition_repo._db.list.assert_called_once()
        filters = field_definition_repo._db.list.call_args[1]["filters"]
        assert filters["field_type"]["lookup"] == "eq"
        assert filters["field_type"]["val"] == ReportFieldType.DB_COLUMN
        assert result == fields

    async def test_find_by_parent_field_id(self, field_definition_repo, create_field_definition):
        """Test finding field definitions by parent field ID."""
        # Arrange
        parent_id = str(uuid.uuid4())
        fields = [
            create_field_definition(parent_field_id=parent_id),
            create_field_definition(parent_field_id=parent_id)
        ]
        field_definition_repo._db.list.return_value = fields
        
        # Act
        result = await field_definition_repo.find_by_parent_field_id(parent_id)
        
        # Assert
        field_definition_repo._db.list.assert_called_once()
        filters = field_definition_repo._db.list.call_args[1]["filters"]
        assert filters["parent_field_id"]["lookup"] == "eq"
        assert filters["parent_field_id"]["val"] == parent_id
        assert result == fields

    async def test_find_by_template_id(self, field_definition_repo, create_field_definition):
        """Test finding field definitions by template ID."""
        # Arrange
        template_id = str(uuid.uuid4())
        fields = [
            create_field_definition(),
            create_field_definition()
        ]
        field_definition_repo._db.fetch_all.return_value = [
            {"id": fields[0].id, "name": fields[0].name, "field_type": fields[0].field_type},
            {"id": fields[1].id, "name": fields[1].name, "field_type": fields[1].field_type}
        ]
        field_definition_repo._create_entity_from_row = MagicMock(side_effect=fields)
        
        # Act
        result = await field_definition_repo.find_by_template_id(template_id)
        
        # Assert
        field_definition_repo._db.fetch_all.assert_called_once()
        query_params = field_definition_repo._db.fetch_all.call_args[1]
        assert "template_id" in query_params
        assert query_params["template_id"] == template_id
        assert result == fields


class TestReportTemplateRepository:
    """Tests for the ReportTemplateRepository class."""

    async def test_find_by_name(self, template_repo, create_template):
        """Test finding a template by name."""
        # Arrange
        template = create_template(name="test_template")
        expected_templates = [template]
        template_repo._db.list.return_value = expected_templates
        
        # Act
        result = await template_repo.find_by_name("test_template")
        
        # Assert
        template_repo._db.list.assert_called_once()
        filters = template_repo._db.list.call_args[1]["filters"]
        assert filters["name"]["lookup"] == "eq"
        assert filters["name"]["val"] == "test_template"
        assert result == template

    async def test_find_by_name_not_found(self, template_repo):
        """Test finding a template by name when it doesn't exist."""
        # Arrange
        template_repo._db.list.return_value = []
        
        # Act
        result = await template_repo.find_by_name("non_existent_template")
        
        # Assert
        assert result is None

    async def test_find_by_base_object_type(self, template_repo, create_template):
        """Test finding templates by base object type."""
        # Arrange
        templates = [
            create_template(base_object_type="customer"),
            create_template(base_object_type="customer")
        ]
        template_repo._db.list.return_value = templates
        
        # Act
        result = await template_repo.find_by_base_object_type("customer")
        
        # Assert
        template_repo._db.list.assert_called_once()
        filters = template_repo._db.list.call_args[1]["filters"]
        assert filters["base_object_type"]["lookup"] == "eq"
        assert filters["base_object_type"]["val"] == "customer"
        assert result == templates

    async def test_find_with_relationships_success(self, template_repo, create_template):
        """Test finding a template with all relationships loaded."""
        # Arrange
        template_id = str(uuid.uuid4())
        template = create_template(id_=template_id)
        template_repo.get.return_value = template
        template_repo.load_relationships = AsyncMock()
        
        # Act
        result = await template_repo.find_with_relationships(template_id)
        
        # Assert
        template_repo.get.assert_called_once_with(template_id)
        template_repo.load_relationships.assert_called_once_with(template)
        assert result.is_success
        assert result.value == template

    async def test_find_with_relationships_not_found(self, template_repo):
        """Test finding a template with relationships when it doesn't exist."""
        # Arrange
        template_id = str(uuid.uuid4())
        template_repo.get.return_value = None
        
        # Act
        result = await template_repo.find_with_relationships(template_id)
        
        # Assert
        template_repo.get.assert_called_once_with(template_id)
        assert result.is_failure
        assert f"Template with ID {template_id} not found" in str(result.error)

    async def test_find_with_relationships_error(self, template_repo, create_template):
        """Test finding a template with relationships when an error occurs."""
        # Arrange
        template_id = str(uuid.uuid4())
        template = create_template(id_=template_id)
        template_repo.get.return_value = template
        error_message = "Database error"
        template_repo.load_relationships.side_effect = Exception(error_message)
        
        # Act
        result = await template_repo.find_with_relationships(template_id)
        
        # Assert
        template_repo.get.assert_called_once_with(template_id)
        template_repo.load_relationships.assert_called_once_with(template)
        assert result.is_failure
        assert error_message in str(result.error)


class TestReportTriggerRepository:
    """Tests for the ReportTriggerRepository class."""

    async def test_find_by_template_id(self, trigger_repo, create_trigger):
        """Test finding triggers by template ID."""
        # Arrange
        template_id = str(uuid.uuid4())
        triggers = [
            create_trigger(template_id=template_id),
            create_trigger(template_id=template_id)
        ]
        trigger_repo._db.list.return_value = triggers
        
        # Act
        result = await trigger_repo.find_by_template_id(template_id)
        
        # Assert
        trigger_repo._db.list.assert_called_once()
        filters = trigger_repo._db.list.call_args[1]["filters"]
        assert filters["report_template_id"]["lookup"] == "eq"
        assert filters["report_template_id"]["val"] == template_id
        assert result == triggers

    async def test_find_by_trigger_type(self, trigger_repo, create_trigger):
        """Test finding triggers by trigger type."""
        # Arrange
        trigger_type = ReportTriggerType.SCHEDULED
        triggers = [
            create_trigger(trigger_type=trigger_type),
            create_trigger(trigger_type=trigger_type)
        ]
        trigger_repo._db.list.return_value = triggers
        
        # Act
        result = await trigger_repo.find_by_trigger_type(trigger_type)
        
        # Assert
        trigger_repo._db.list.assert_called_once()
        filters = trigger_repo._db.list.call_args[1]["filters"]
        assert filters["trigger_type"]["lookup"] == "eq"
        assert filters["trigger_type"]["val"] == trigger_type
        assert result == triggers

    async def test_find_active_triggers(self, trigger_repo, create_trigger):
        """Test finding all active triggers."""
        # Arrange
        triggers = [
            create_trigger(),
            create_trigger()
        ]
        trigger_repo._db.list.return_value = triggers
        
        # Act
        result = await trigger_repo.find_active_triggers()
        
        # Assert
        trigger_repo._db.list.assert_called_once()
        filters = trigger_repo._db.list.call_args[1]["filters"]
        assert filters["is_active"]["lookup"] == "eq"
        assert filters["is_active"]["val"] is True
        assert result == triggers

    async def test_find_active_scheduled_triggers(self, trigger_repo, create_trigger):
        """Test finding active scheduled triggers."""
        # Arrange
        triggers = [
            create_trigger(trigger_type=ReportTriggerType.SCHEDULED),
            create_trigger(trigger_type=ReportTriggerType.SCHEDULED)
        ]
        trigger_repo._db.list.return_value = triggers
        
        # Act
        result = await trigger_repo.find_active_scheduled_triggers()
        
        # Assert
        trigger_repo._db.list.assert_called_once()
        filters = trigger_repo._db.list.call_args[1]["filters"]
        assert filters["is_active"]["lookup"] == "eq"
        assert filters["is_active"]["val"] is True
        assert filters["trigger_type"]["lookup"] == "eq"
        assert filters["trigger_type"]["val"] == "scheduled"
        assert result == triggers


class TestReportOutputRepository:
    """Tests for the ReportOutputRepository class."""

    async def test_find_by_template_id(self, output_repo, create_output):
        """Test finding outputs by template ID."""
        # Arrange
        template_id = str(uuid.uuid4())
        outputs = [
            create_output(template_id=template_id),
            create_output(template_id=template_id)
        ]
        output_repo._db.list.return_value = outputs
        
        # Act
        result = await output_repo.find_by_template_id(template_id)
        
        # Assert
        output_repo._db.list.assert_called_once()
        filters = output_repo._db.list.call_args[1]["filters"]
        assert filters["report_template_id"]["lookup"] == "eq"
        assert filters["report_template_id"]["val"] == template_id
        assert result == outputs

    async def test_find_by_output_type(self, output_repo, create_output):
        """Test finding outputs by output type."""
        # Arrange
        output_type = ReportOutputType.EMAIL
        outputs = [
            create_output(output_type=output_type),
            create_output(output_type=output_type)
        ]
        output_repo._db.list.return_value = outputs
        
        # Act
        result = await output_repo.find_by_output_type(output_type)
        
        # Assert
        output_repo._db.list.assert_called_once()
        filters = output_repo._db.list.call_args[1]["filters"]
        assert filters["output_type"]["lookup"] == "eq"
        assert filters["output_type"]["val"] == output_type
        assert result == outputs

    async def test_find_active_outputs(self, output_repo, create_output):
        """Test finding all active outputs."""
        # Arrange
        outputs = [
            create_output(),
            create_output()
        ]
        output_repo._db.list.return_value = outputs
        
        # Act
        result = await output_repo.find_active_outputs()
        
        # Assert
        output_repo._db.list.assert_called_once()
        filters = output_repo._db.list.call_args[1]["filters"]
        assert filters["is_active"]["lookup"] == "eq"
        assert filters["is_active"]["val"] is True
        assert result == outputs


class TestReportExecutionRepository:
    """Tests for the ReportExecutionRepository class."""

    async def test_find_by_template_id(self, execution_repo, create_execution):
        """Test finding executions by template ID."""
        # Arrange
        template_id = str(uuid.uuid4())
        executions = [
            create_execution(template_id=template_id),
            create_execution(template_id=template_id)
        ]
        execution_repo._db.list.return_value = executions
        
        # Act
        result = await execution_repo.find_by_template_id(template_id)
        
        # Assert
        execution_repo._db.list.assert_called_once()
        filters = execution_repo._db.list.call_args[1]["filters"]
        assert filters["report_template_id"]["lookup"] == "eq"
        assert filters["report_template_id"]["val"] == template_id
        assert result == executions

    async def test_find_by_status(self, execution_repo, create_execution):
        """Test finding executions by status."""
        # Arrange
        status = ReportExecutionStatus.PENDING
        executions = [
            create_execution(status=status),
            create_execution(status=status)
        ]
        execution_repo._db.list.return_value = executions
        
        # Act
        result = await execution_repo.find_by_status(status)
        
        # Assert
        execution_repo._db.list.assert_called_once()
        filters = execution_repo._db.list.call_args[1]["filters"]
        assert filters["status"]["lookup"] == "eq"
        assert filters["status"]["val"] == status
        assert result == executions

    async def test_find_by_triggered_by(self, execution_repo, create_execution):
        """Test finding executions by triggered by."""
        # Arrange
        executions = [create_execution(), create_execution()]
        execution_repo._db.list.return_value = executions
        
        # Act
        result = await execution_repo.find_by_triggered_by("test_user")
        
        # Assert
        execution_repo._db.list.assert_called_once()
        filters = execution_repo._db.list.call_args[1]["filters"]
        assert filters["triggered_by"]["lookup"] == "eq"
        assert filters["triggered_by"]["val"] == "test_user"
        assert result == executions

    async def test_find_with_output_executions_success(self, execution_repo, create_execution):
        """Test finding an execution with output executions loaded."""
        # Arrange
        execution_id = str(uuid.uuid4())
        execution = create_execution(id_=execution_id)
        execution_repo.get.return_value = execution
        execution_repo.load_relationships = AsyncMock()
        
        # Act
        result = await execution_repo.find_with_output_executions(execution_id)
        
        # Assert
        execution_repo.get.assert_called_once_with(execution_id)
        execution_repo.load_relationships.assert_called_once_with(execution, ["output_executions"])
        assert result.is_success
        assert result.value == execution

    async def test_find_with_output_executions_not_found(self, execution_repo):
        """Test finding an execution with output executions when it doesn't exist."""
        # Arrange
        execution_id = str(uuid.uuid4())
        execution_repo.get.return_value = None
        
        # Act
        result = await execution_repo.find_with_output_executions(execution_id)
        
        # Assert
        execution_repo.get.assert_called_once_with(execution_id)
        assert result.is_failure
        assert f"Execution with ID {execution_id} not found" in str(result.error)

    async def test_find_with_output_executions_error(self, execution_repo, create_execution):
        """Test finding an execution with output executions when an error occurs."""
        # Arrange
        execution_id = str(uuid.uuid4())
        execution = create_execution(id_=execution_id)
        execution_repo.get.return_value = execution
        error_message = "Database error"
        execution_repo.load_relationships.side_effect = Exception(error_message)
        
        # Act
        result = await execution_repo.find_with_output_executions(execution_id)
        
        # Assert
        execution_repo.get.assert_called_once_with(execution_id)
        execution_repo.load_relationships.assert_called_once_with(execution, ["output_executions"])
        assert result.is_failure
        assert error_message in str(result.error)

    async def test_find_recent_executions(self, execution_repo, create_execution):
        """Test finding recent executions."""
        # Arrange
        executions = [create_execution(), create_execution()]
        execution_repo._db.list.return_value = executions
        
        # Act
        result = await execution_repo.find_recent_executions(limit=10)
        
        # Assert
        execution_repo._db.list.assert_called_once()
        assert execution_repo._db.list.call_args[1]["order_by"] == "started_at"
        assert execution_repo._db.list.call_args[1]["order_dir"] == "desc"
        assert execution_repo._db.list.call_args[1]["limit"] == 10
        assert result == executions


class TestReportOutputExecutionRepository:
    """Tests for the ReportOutputExecutionRepository class."""

    async def test_find_by_execution_id(self, output_execution_repo, create_output_execution):
        """Test finding output executions by execution ID."""
        # Arrange
        execution_id = str(uuid.uuid4())
        output_executions = [
            create_output_execution(execution_id=execution_id),
            create_output_execution(execution_id=execution_id)
        ]
        output_execution_repo._db.list.return_value = output_executions
        
        # Act
        result = await output_execution_repo.find_by_execution_id(execution_id)
        
        # Assert
        output_execution_repo._db.list.assert_called_once()
        filters = output_execution_repo._db.list.call_args[1]["filters"]
        assert filters["report_execution_id"]["lookup"] == "eq"
        assert filters["report_execution_id"]["val"] == execution_id
        assert result == output_executions

    async def test_find_by_output_id(self, output_execution_repo, create_output_execution):
        """Test finding output executions by output ID."""
        # Arrange
        output_id = str(uuid.uuid4())
        output_executions = [
            create_output_execution(output_id=output_id),
            create_output_execution(output_id=output_id)
        ]
        output_execution_repo._db.list.return_value = output_executions
        
        # Act
        result = await output_execution_repo.find_by_output_id(output_id)
        
        # Assert
        output_execution_repo._db.list.assert_called_once()
        filters = output_execution_repo._db.list.call_args[1]["filters"]
        assert filters["report_output_id"]["lookup"] == "eq"
        assert filters["report_output_id"]["val"] == output_id
        assert result == output_executions

    async def test_find_by_status(self, output_execution_repo, create_output_execution):
        """Test finding output executions by status."""
        # Arrange
        status = ReportExecutionStatus.PENDING
        output_executions = [
            create_output_execution(status=status),
            create_output_execution(status=status)
        ]
        output_execution_repo._db.list.return_value = output_executions
        
        # Act
        result = await output_execution_repo.find_by_status(status)
        
        # Assert
        output_execution_repo._db.list.assert_called_once()
        filters = output_execution_repo._db.list.call_args[1]["filters"]
        assert filters["status"]["lookup"] == "eq"
        assert filters["status"]["val"] == status
        assert result == output_executions