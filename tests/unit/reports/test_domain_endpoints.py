# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Tests for the report domain endpoints."""

import pytest
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, cast
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from uno.core.errors.result import Result, Success, Failure
from uno.reports.domain_endpoints import (
    field_definition_router,
    template_router,
    trigger_router,
    output_router,
    execution_router,
    output_execution_router,
    
    # Import schemas for type hinting
    ReportFieldDefinitionResponse,
    ReportTemplateResponse,
    ReportTriggerResponse,
    ReportOutputResponse,
    ReportExecutionResponse,
    ReportOutputExecutionResponse,
)
from uno.reports.domain_services import (
    ReportFieldDefinitionService,
    ReportTemplateService,
    ReportTriggerService,
    ReportOutputService,
    ReportExecutionService,
    ReportOutputExecutionService,
)
from uno.reports.entities import (
    ReportFieldDefinition,
    ReportTemplate,
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


# Create a test app and client fixture
@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    app = FastAPI()
    app.include_router(field_definition_router.router)
    app.include_router(template_router.router)
    app.include_router(trigger_router.router)
    app.include_router(output_router.router)
    app.include_router(execution_router.router)
    app.include_router(output_execution_router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# Mock service fixtures
@pytest.fixture
def mock_field_definition_service():
    """Create a mock field definition service."""
    service = AsyncMock(spec=ReportFieldDefinitionService)
    return service


@pytest.fixture
def mock_template_service():
    """Create a mock template service."""
    service = AsyncMock(spec=ReportTemplateService)
    return service


@pytest.fixture
def mock_trigger_service():
    """Create a mock trigger service."""
    service = AsyncMock(spec=ReportTriggerService)
    return service


@pytest.fixture
def mock_output_service():
    """Create a mock output service."""
    service = AsyncMock(spec=ReportOutputService)
    return service


@pytest.fixture
def mock_execution_service():
    """Create a mock execution service."""
    service = AsyncMock(spec=ReportExecutionService)
    return service


@pytest.fixture
def mock_output_execution_service():
    """Create a mock output execution service."""
    service = AsyncMock(spec=ReportOutputExecutionService)
    return service


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


class TestReportFieldDefinitionEndpoints:
    """Tests for the ReportFieldDefinition endpoints."""

    @patch("uno.reports.domain_endpoints.get_report_field_definition_service")
    def test_find_fields_by_template(self, mock_get_service, client, mock_field_definition_service, create_field_definition):
        """Test the find_fields_by_template endpoint."""
        # Arrange
        template_id = str(uuid.uuid4())
        fields = [
            create_field_definition(),
            create_field_definition()
        ]
        
        # Mock service
        mock_get_service.return_value = mock_field_definition_service
        mock_field_definition_service.find_by_template_id.return_value = Success(fields)
        
        # Act
        response = client.get(f"/report-field-definitions/by-template/{template_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        mock_field_definition_service.find_by_template_id.assert_called_once_with(template_id)


class TestReportTemplateEndpoints:
    """Tests for the ReportTemplate endpoints."""
    
    @patch("uno.reports.domain_endpoints.get_report_template_service")
    def test_find_templates_by_object_type(self, mock_get_service, client, mock_template_service, create_template):
        """Test the find_templates_by_object_type endpoint."""
        # Arrange
        object_type = "customer"
        templates = [
            create_template(base_object_type=object_type),
            create_template(base_object_type=object_type)
        ]
        
        # Mock service
        mock_get_service.return_value = mock_template_service
        mock_template_service.find_by_base_object_type.return_value = Success(templates)
        
        # Act
        response = client.get(f"/report-templates/by-object-type/{object_type}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        mock_template_service.find_by_base_object_type.assert_called_once_with(object_type)

    @patch("uno.reports.domain_endpoints.get_report_template_service")
    def test_get_template_with_relationships(self, mock_get_service, client, mock_template_service, create_template):
        """Test the get_template_with_relationships endpoint."""
        # Arrange
        template_id = str(uuid.uuid4())
        template = create_template(id_=template_id)
        
        # Mock service
        mock_get_service.return_value = mock_template_service
        mock_template_service.get_with_relationships.return_value = Success(template)
        
        # Act
        response = client.get(f"/report-templates/{template_id}/with-relationships")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        mock_template_service.get_with_relationships.assert_called_once_with(template_id)

    @patch("uno.reports.domain_endpoints.get_report_template_service")
    def test_execute_template(self, mock_get_service, client, mock_template_service, create_execution):
        """Test the execute_template endpoint."""
        # Arrange
        template_id = str(uuid.uuid4())
        parameters = {"param1": "value1"}
        execution = create_execution(template_id=template_id)
        
        # Mock service
        mock_get_service.return_value = mock_template_service
        mock_template_service.execute_template.return_value = Success(execution)
        
        # Act
        response = client.post(
            f"/report-templates/{template_id}/execute",
            json=parameters
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["report_template_id"] == template_id
        mock_template_service.execute_template.assert_called_once()
        call_args = mock_template_service.execute_template.call_args[1]
        assert call_args["template_id"] == template_id
        assert call_args["triggered_by"] == "api"
        assert call_args["trigger_type"] == ReportTriggerType.MANUAL
        assert call_args["parameters"] == parameters

    @patch("uno.reports.domain_endpoints.get_report_template_service")
    def test_update_template_fields(self, mock_get_service, client, mock_template_service, create_template):
        """Test the update_template_fields endpoint."""
        # Arrange
        template_id = str(uuid.uuid4())
        template = create_template(id_=template_id)
        
        # Field IDs
        field_ids_to_add = [str(uuid.uuid4())]
        field_ids_to_remove = [str(uuid.uuid4())]
        
        # Update data
        update_data = {
            "field_ids_to_add": field_ids_to_add,
            "field_ids_to_remove": field_ids_to_remove
        }
        
        # Mock service
        mock_get_service.return_value = mock_template_service
        mock_template_service.update_fields.return_value = Success(template)
        
        # Act
        response = client.patch(
            f"/report-templates/{template_id}/fields",
            json=update_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        mock_template_service.update_fields.assert_called_once_with(
            template_id=template_id,
            field_ids_to_add=field_ids_to_add,
            field_ids_to_remove=field_ids_to_remove
        )


class TestReportTriggerEndpoints:
    """Tests for the ReportTrigger endpoints."""
    
    @patch("uno.reports.domain_endpoints.get_report_trigger_service")
    def test_find_active_triggers(self, mock_get_service, client, mock_trigger_service, create_trigger):
        """Test the find_active_triggers endpoint."""
        # Arrange
        triggers = [
            create_trigger(),
            create_trigger()
        ]
        
        # Mock service
        mock_get_service.return_value = mock_trigger_service
        mock_trigger_service.find_active_triggers.return_value = Success(triggers)
        
        # Act
        response = client.get("/report-triggers/active")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        mock_trigger_service.find_active_triggers.assert_called_once()

    @patch("uno.reports.domain_endpoints.get_report_trigger_service")
    def test_find_active_scheduled_triggers(self, mock_get_service, client, mock_trigger_service, create_trigger):
        """Test the find_active_scheduled_triggers endpoint."""
        # Arrange
        triggers = [
            create_trigger(trigger_type=ReportTriggerType.SCHEDULED),
            create_trigger(trigger_type=ReportTriggerType.SCHEDULED)
        ]
        
        # Mock service
        mock_get_service.return_value = mock_trigger_service
        mock_trigger_service.find_active_scheduled_triggers.return_value = Success(triggers)
        
        # Act
        response = client.get("/report-triggers/scheduled")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        mock_trigger_service.find_active_scheduled_triggers.assert_called_once()

    @patch("uno.reports.domain_endpoints.get_report_trigger_service")
    def test_process_due_triggers(self, mock_get_service, client, mock_trigger_service):
        """Test the process_due_triggers endpoint."""
        # Arrange
        processed_count = 3
        
        # Mock service
        mock_get_service.return_value = mock_trigger_service
        mock_trigger_service.process_due_triggers.return_value = Success(processed_count)
        
        # Act
        response = client.post("/report-triggers/process-due")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["processed_count"] == processed_count
        mock_trigger_service.process_due_triggers.assert_called_once()


class TestReportExecutionEndpoints:
    """Tests for the ReportExecution endpoints."""
    
    @patch("uno.reports.domain_endpoints.get_report_execution_service")
    def test_find_recent_executions(self, mock_get_service, client, mock_execution_service, create_execution):
        """Test the find_recent_executions endpoint."""
        # Arrange
        limit = 5
        executions = [
            create_execution(),
            create_execution()
        ]
        
        # Mock service
        mock_get_service.return_value = mock_execution_service
        mock_execution_service.find_recent_executions.return_value = Success(executions)
        
        # Act
        response = client.get(f"/report-executions/recent?limit={limit}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        mock_execution_service.find_recent_executions.assert_called_once_with(limit)

    @patch("uno.reports.domain_endpoints.get_report_execution_service")
    def test_find_execution_with_outputs(self, mock_get_service, client, mock_execution_service, create_execution):
        """Test the find_execution_with_outputs endpoint."""
        # Arrange
        execution_id = str(uuid.uuid4())
        execution = create_execution(id_=execution_id)
        
        # Mock service
        mock_get_service.return_value = mock_execution_service
        mock_execution_service.find_with_output_executions.return_value = Success(execution)
        
        # Act
        response = client.get(f"/report-executions/{execution_id}/with-outputs")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == execution_id
        mock_execution_service.find_with_output_executions.assert_called_once_with(execution_id)

    @patch("uno.reports.domain_endpoints.get_report_execution_service")
    def test_update_execution_status(self, mock_get_service, client, mock_execution_service, create_execution):
        """Test the update_execution_status endpoint."""
        # Arrange
        execution_id = str(uuid.uuid4())
        execution = create_execution(id_=execution_id)
        new_status = ReportExecutionStatus.COMPLETED
        status_update = {
            "status": new_status,
            "error_details": None
        }
        
        # Mock service
        mock_get_service.return_value = mock_execution_service
        mock_execution_service.update_execution_status.return_value = Success(execution)
        
        # Act
        response = client.patch(
            f"/report-executions/{execution_id}/status",
            json=status_update
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == execution_id
        mock_execution_service.update_execution_status.assert_called_once_with(
            execution_id=execution_id,
            status=new_status,
            error_details=None
        )


class TestReportOutputExecutionEndpoints:
    """Tests for the ReportOutputExecution endpoints."""
    
    @patch("uno.reports.domain_endpoints.get_report_output_execution_service")
    def test_get_output_execution(self, mock_get_service, client, mock_output_execution_service, create_output_execution):
        """Test the get_output_execution endpoint."""
        # Arrange
        output_execution_id = str(uuid.uuid4())
        output_execution = create_output_execution(id_=output_execution_id)
        
        # Mock service
        mock_get_service.return_value = mock_output_execution_service
        mock_output_execution_service.get.return_value = Success(output_execution)
        
        # Act
        response = client.get(f"/report-output-executions/{output_execution_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == output_execution_id
        mock_output_execution_service.get.assert_called_once_with(output_execution_id)

    @patch("uno.reports.domain_endpoints.get_report_output_execution_service")
    def test_find_output_executions_by_execution(self, mock_get_service, client, mock_output_execution_service, create_output_execution):
        """Test the find_output_executions_by_execution endpoint."""
        # Arrange
        execution_id = str(uuid.uuid4())
        output_executions = [
            create_output_execution(execution_id=execution_id),
            create_output_execution(execution_id=execution_id)
        ]
        
        # Mock service
        mock_get_service.return_value = mock_output_execution_service
        mock_output_execution_service.find_by_execution_id.return_value = Success(output_executions)
        
        # Act
        response = client.get(f"/report-output-executions/by-execution/{execution_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        mock_output_execution_service.find_by_execution_id.assert_called_once_with(execution_id)

    @patch("uno.reports.domain_endpoints.get_report_output_execution_service")
    def test_update_output_execution_status(self, mock_get_service, client, mock_output_execution_service, create_output_execution):
        """Test the update_output_execution_status endpoint."""
        # Arrange
        output_execution_id = str(uuid.uuid4())
        output_execution = create_output_execution(id_=output_execution_id)
        new_status = ReportExecutionStatus.COMPLETED
        status_update = {
            "status": new_status,
            "error_details": None,
            "output_location": "/path/to/output.pdf",
            "output_size_bytes": 1024
        }
        
        # Mock service
        mock_get_service.return_value = mock_output_execution_service
        mock_output_execution_service.update_output_execution_status.return_value = Success(output_execution)
        
        # Act
        response = client.patch(
            f"/report-output-executions/{output_execution_id}/status",
            json=status_update
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == output_execution_id
        mock_output_execution_service.update_output_execution_status.assert_called_once_with(
            output_execution_id=output_execution_id,
            status=new_status,
            error_details=None
        )