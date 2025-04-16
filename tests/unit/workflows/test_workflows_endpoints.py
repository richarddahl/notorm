"""
Tests for the Workflows module API endpoints.

This module contains comprehensive tests for the Workflows module API endpoints
to ensure proper functionality and compliance with domain-driven design principles.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime, UTC
import json

from uno.core.result import Success, Failure
from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowExecutionStatus,
    WorkflowConditionType,
)
from uno.workflows.entities import (
    User, WorkflowTrigger, WorkflowCondition, WorkflowRecipient,
    WorkflowAction, WorkflowExecutionRecord, WorkflowDef
)
from uno.workflows.domain_services import (
    WorkflowDefService, WorkflowTriggerService, WorkflowConditionService,
    WorkflowActionService, WorkflowRecipientService, WorkflowExecutionService
)
from uno.workflows.domain_endpoints import (
    register_workflow_endpoints
)

# Test data
TEST_WORKFLOW_ID = "test_workflow"
TEST_TRIGGER_ID = "test_trigger"
TEST_CONDITION_ID = "test_condition"
TEST_ACTION_ID = "test_action"
TEST_RECIPIENT_ID = "test_recipient"
TEST_EXECUTION_ID = "test_execution"
TEST_USER_ID = "test_user"
TEST_EVENT_ID = "test_event"


class TestWorkflowsEndpoints:
    """Tests for the Workflows module endpoints."""

    @pytest.fixture
    def mock_workflow_service(self):
        """Create a mock workflow service."""
        return AsyncMock(spec=WorkflowDefService)

    @pytest.fixture
    def mock_trigger_service(self):
        """Create a mock trigger service."""
        return AsyncMock(spec=WorkflowTriggerService)

    @pytest.fixture
    def mock_condition_service(self):
        """Create a mock condition service."""
        return AsyncMock(spec=WorkflowConditionService)

    @pytest.fixture
    def mock_action_service(self):
        """Create a mock action service."""
        return AsyncMock(spec=WorkflowActionService)

    @pytest.fixture
    def mock_recipient_service(self):
        """Create a mock recipient service."""
        return AsyncMock(spec=WorkflowRecipientService)

    @pytest.fixture
    def mock_execution_service(self):
        """Create a mock execution service."""
        return AsyncMock(spec=WorkflowExecutionService)

    @pytest.fixture
    def app(self, mock_workflow_service, mock_trigger_service, mock_condition_service,
            mock_action_service, mock_recipient_service, mock_execution_service):
        """Create a FastAPI test application with workflow routers."""
        app = FastAPI()
        
        # Patch dependency injection to use mock services
        with patch("uno.workflows.domain_endpoints.get_service") as mock_get_service:
            # Configure the mock to return appropriate service based on type
            def get_service_side_effect(service_type):
                if service_type == WorkflowDefService:
                    return mock_workflow_service
                elif service_type == WorkflowTriggerService:
                    return mock_trigger_service
                elif service_type == WorkflowConditionService:
                    return mock_condition_service
                elif service_type == WorkflowActionService:
                    return mock_action_service
                elif service_type == WorkflowRecipientService:
                    return mock_recipient_service
                elif service_type == WorkflowExecutionService:
                    return mock_execution_service
                return None
                
            mock_get_service.side_effect = get_service_side_effect
            
            # Register routers with the app
            register_workflow_endpoints(app)
            
            yield app

    @pytest.fixture
    def client(self, app):
        """Create a test client for the FastAPI application."""
        return TestClient(app)

    # WorkflowDef endpoint tests
    
    def test_create_workflow_success(self, client, mock_workflow_service):
        """Test creating a workflow successfully."""
        # Arrange
        new_workflow = WorkflowDef(
            id=TEST_WORKFLOW_ID,
            name="Test Workflow",
            description="A test workflow"
        )
        mock_workflow_service.create.return_value = Success(new_workflow)
        
        # Act
        response = client.post(
            "/api/workflows/",
            json={
                "id": TEST_WORKFLOW_ID,
                "name": "Test Workflow",
                "description": "A test workflow"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_WORKFLOW_ID
        assert response.json()["name"] == "Test Workflow"
        assert response.json()["description"] == "A test workflow"
        mock_workflow_service.create.assert_called_once()

    def test_create_workflow_validation_error(self, client, mock_workflow_service):
        """Test creating a workflow with validation error."""
        # Arrange
        error_msg = "Description is required"
        mock_workflow_service.create.return_value = Failure(ValueError(error_msg))
        
        # Act
        response = client.post(
            "/api/workflows/",
            json={
                "id": TEST_WORKFLOW_ID,
                "name": "Test Workflow",
                "description": ""  # Empty description will cause validation error
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert error_msg in response.json()["detail"]
        mock_workflow_service.create.assert_called_once()

    def test_get_workflow_by_id_success(self, client, mock_workflow_service):
        """Test getting a workflow by ID successfully."""
        # Arrange
        workflow = WorkflowDef(
            id=TEST_WORKFLOW_ID,
            name="Test Workflow",
            description="A test workflow"
        )
        mock_workflow_service.get_by_id.return_value = Success(workflow)
        
        # Act
        response = client.get(f"/api/workflows/{TEST_WORKFLOW_ID}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_WORKFLOW_ID
        assert response.json()["name"] == "Test Workflow"
        mock_workflow_service.get_by_id.assert_called_once_with(TEST_WORKFLOW_ID)

    def test_get_workflow_by_id_not_found(self, client, mock_workflow_service):
        """Test getting a workflow by ID when not found."""
        # Arrange
        mock_workflow_service.get_by_id.return_value = Success(None)
        
        # Act
        response = client.get(f"/api/workflows/{TEST_WORKFLOW_ID}")
        
        # Assert
        assert response.status_code == 404
        mock_workflow_service.get_by_id.assert_called_once_with(TEST_WORKFLOW_ID)

    def test_get_workflows_list_success(self, client, mock_workflow_service):
        """Test listing workflows successfully."""
        # Arrange
        workflows = [
            WorkflowDef(id="workflow1", name="Workflow 1", description="Description 1"),
            WorkflowDef(id="workflow2", name="Workflow 2", description="Description 2")
        ]
        mock_workflow_service.list.return_value = Success(workflows)
        
        # Act
        response = client.get("/api/workflows/")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["id"] == "workflow1"
        assert response.json()[1]["id"] == "workflow2"
        mock_workflow_service.list.assert_called_once()

    def test_get_active_workflows_success(self, client, mock_workflow_service):
        """Test getting active workflows successfully."""
        # Arrange
        active_workflows = [
            WorkflowDef(id="workflow1", name="Workflow 1", description="Description 1", status=WorkflowStatus.ACTIVE),
            WorkflowDef(id="workflow2", name="Workflow 2", description="Description 2", status=WorkflowStatus.ACTIVE)
        ]
        mock_workflow_service.find_by_status.return_value = Success(active_workflows)
        
        # Act
        response = client.get("/api/workflows/active")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(workflow["status"] == WorkflowStatus.ACTIVE.value for workflow in response.json())
        mock_workflow_service.find_by_status.assert_called_once_with(WorkflowStatus.ACTIVE)

    def test_get_workflow_with_relationships_success(self, client, mock_workflow_service):
        """Test getting a workflow with relationships successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        workflow = WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow"
        )
        
        # Add relationships
        trigger = WorkflowTrigger(id=TEST_TRIGGER_ID, workflow_id=workflow_id, entity_type="User", operation="INSERT")
        condition = WorkflowCondition(id=TEST_CONDITION_ID, workflow_id=workflow_id, condition_type=WorkflowConditionType.FIELD_VALUE)
        action = WorkflowAction(id=TEST_ACTION_ID, workflow_id=workflow_id, action_type=WorkflowActionType.EMAIL)
        recipient = WorkflowRecipient(id=TEST_RECIPIENT_ID, workflow_id=workflow_id, recipient_type=WorkflowRecipientType.USER, recipient_id=TEST_USER_ID)
        
        workflow.triggers = [trigger]
        workflow.conditions = [condition]
        workflow.actions = [action]
        workflow.recipients = [recipient]
        
        mock_workflow_service.get_with_relationships.return_value = Success(workflow)
        
        # Act
        response = client.get(f"/api/workflows/{workflow_id}/with-relationships")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == workflow_id
        assert len(response.json()["triggers"]) == 1
        assert len(response.json()["conditions"]) == 1
        assert len(response.json()["actions"]) == 1
        assert len(response.json()["recipients"]) == 1
        mock_workflow_service.get_with_relationships.assert_called_once_with(workflow_id)

    def test_activate_workflow_success(self, client, mock_workflow_service):
        """Test activating a workflow successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        workflow = WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow",
            status=WorkflowStatus.ACTIVE
        )
        mock_workflow_service.activate_workflow.return_value = Success(workflow)
        
        # Act
        response = client.post(f"/api/workflows/{workflow_id}/activate")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == workflow_id
        assert response.json()["status"] == WorkflowStatus.ACTIVE.value
        mock_workflow_service.activate_workflow.assert_called_once_with(workflow_id)

    def test_deactivate_workflow_success(self, client, mock_workflow_service):
        """Test deactivating a workflow successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        workflow = WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow",
            status=WorkflowStatus.INACTIVE
        )
        mock_workflow_service.deactivate_workflow.return_value = Success(workflow)
        
        # Act
        response = client.post(f"/api/workflows/{workflow_id}/deactivate")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == workflow_id
        assert response.json()["status"] == WorkflowStatus.INACTIVE.value
        mock_workflow_service.deactivate_workflow.assert_called_once_with(workflow_id)

    # WorkflowTrigger endpoint tests
    
    def test_create_trigger_success(self, client, mock_trigger_service):
        """Test creating a trigger successfully."""
        # Arrange
        new_trigger = WorkflowTrigger(
            id=TEST_TRIGGER_ID,
            workflow_id=TEST_WORKFLOW_ID,
            entity_type="User",
            operation="INSERT"
        )
        mock_trigger_service.create.return_value = Success(new_trigger)
        
        # Act
        response = client.post(
            "/api/workflow-triggers/",
            json={
                "id": TEST_TRIGGER_ID,
                "workflow_id": TEST_WORKFLOW_ID,
                "entity_type": "User",
                "operation": "INSERT"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_TRIGGER_ID
        assert response.json()["workflow_id"] == TEST_WORKFLOW_ID
        assert response.json()["entity_type"] == "User"
        assert response.json()["operation"] == "INSERT"
        mock_trigger_service.create.assert_called_once()

    def test_get_triggers_by_workflow_success(self, client, mock_trigger_service):
        """Test getting triggers by workflow ID successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        triggers = [
            WorkflowTrigger(id="trigger1", workflow_id=workflow_id, entity_type="User", operation="INSERT"),
            WorkflowTrigger(id="trigger2", workflow_id=workflow_id, entity_type="Order", operation="UPDATE")
        ]
        mock_trigger_service.find_by_workflow.return_value = Success(triggers)
        
        # Act
        response = client.get(f"/api/workflow-triggers/by-workflow/{workflow_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(trigger["workflow_id"] == workflow_id for trigger in response.json())
        mock_trigger_service.find_by_workflow.assert_called_once_with(workflow_id)

    # WorkflowCondition endpoint tests
    
    def test_create_condition_success(self, client, mock_condition_service):
        """Test creating a condition successfully."""
        # Arrange
        new_condition = WorkflowCondition(
            id=TEST_CONDITION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            condition_type=WorkflowConditionType.FIELD_VALUE,
            condition_config={"field": "status", "value": "ACTIVE", "operator": "equals"}
        )
        mock_condition_service.create.return_value = Success(new_condition)
        
        # Act
        response = client.post(
            "/api/workflow-conditions/",
            json={
                "id": TEST_CONDITION_ID,
                "workflow_id": TEST_WORKFLOW_ID,
                "condition_type": WorkflowConditionType.FIELD_VALUE.value,
                "condition_config": {"field": "status", "value": "ACTIVE", "operator": "equals"}
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_CONDITION_ID
        assert response.json()["workflow_id"] == TEST_WORKFLOW_ID
        assert response.json()["condition_type"] == WorkflowConditionType.FIELD_VALUE.value
        mock_condition_service.create.assert_called_once()

    def test_get_conditions_by_workflow_success(self, client, mock_condition_service):
        """Test getting conditions by workflow ID successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        conditions = [
            WorkflowCondition(id="condition1", workflow_id=workflow_id, condition_type=WorkflowConditionType.FIELD_VALUE),
            WorkflowCondition(id="condition2", workflow_id=workflow_id, condition_type=WorkflowConditionType.QUERY_MATCH)
        ]
        mock_condition_service.find_by_workflow.return_value = Success(conditions)
        
        # Act
        response = client.get(f"/api/workflow-conditions/by-workflow/{workflow_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(condition["workflow_id"] == workflow_id for condition in response.json())
        mock_condition_service.find_by_workflow.assert_called_once_with(workflow_id)

    # WorkflowAction endpoint tests
    
    def test_create_action_success(self, client, mock_action_service):
        """Test creating an action successfully."""
        # Arrange
        new_action = WorkflowAction(
            id=TEST_ACTION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            action_type=WorkflowActionType.EMAIL,
            action_config={"subject": "Test Subject", "body": "Test Body"}
        )
        mock_action_service.create.return_value = Success(new_action)
        
        # Act
        response = client.post(
            "/api/workflow-actions/",
            json={
                "id": TEST_ACTION_ID,
                "workflow_id": TEST_WORKFLOW_ID,
                "action_type": WorkflowActionType.EMAIL.value,
                "action_config": {"subject": "Test Subject", "body": "Test Body"}
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_ACTION_ID
        assert response.json()["workflow_id"] == TEST_WORKFLOW_ID
        assert response.json()["action_type"] == WorkflowActionType.EMAIL.value
        mock_action_service.create.assert_called_once()

    def test_get_actions_by_workflow_success(self, client, mock_action_service):
        """Test getting actions by workflow ID successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        actions = [
            WorkflowAction(id="action1", workflow_id=workflow_id, action_type=WorkflowActionType.EMAIL),
            WorkflowAction(id="action2", workflow_id=workflow_id, action_type=WorkflowActionType.WEBHOOK)
        ]
        mock_action_service.find_by_workflow.return_value = Success(actions)
        
        # Act
        response = client.get(f"/api/workflow-actions/by-workflow/{workflow_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(action["workflow_id"] == workflow_id for action in response.json())
        mock_action_service.find_by_workflow.assert_called_once_with(workflow_id)

    def test_get_action_with_recipients_success(self, client, mock_action_service):
        """Test getting an action with its recipients successfully."""
        # Arrange
        action_id = TEST_ACTION_ID
        action = WorkflowAction(
            id=action_id,
            workflow_id=TEST_WORKFLOW_ID,
            action_type=WorkflowActionType.EMAIL,
            action_config={"subject": "Test Subject", "body": "Test Body"}
        )
        
        # Add recipients
        recipients = [
            WorkflowRecipient(id="recipient1", workflow_id=TEST_WORKFLOW_ID, recipient_type=WorkflowRecipientType.USER, recipient_id="user1"),
            WorkflowRecipient(id="recipient2", workflow_id=TEST_WORKFLOW_ID, recipient_type=WorkflowRecipientType.GROUP, recipient_id="group1")
        ]
        action.recipients = recipients
        
        mock_action_service.get_with_recipients.return_value = Success(action)
        
        # Act
        response = client.get(f"/api/workflow-actions/{action_id}/with-recipients")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == action_id
        assert len(response.json()["recipients"]) == 2
        mock_action_service.get_with_recipients.assert_called_once_with(action_id)

    # WorkflowRecipient endpoint tests
    
    def test_create_recipient_success(self, client, mock_recipient_service):
        """Test creating a recipient successfully."""
        # Arrange
        new_recipient = WorkflowRecipient(
            id=TEST_RECIPIENT_ID,
            workflow_id=TEST_WORKFLOW_ID,
            recipient_type=WorkflowRecipientType.USER,
            recipient_id=TEST_USER_ID
        )
        mock_recipient_service.create.return_value = Success(new_recipient)
        
        # Act
        response = client.post(
            "/api/workflow-recipients/",
            json={
                "id": TEST_RECIPIENT_ID,
                "workflow_id": TEST_WORKFLOW_ID,
                "recipient_type": WorkflowRecipientType.USER.value,
                "recipient_id": TEST_USER_ID
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_RECIPIENT_ID
        assert response.json()["workflow_id"] == TEST_WORKFLOW_ID
        assert response.json()["recipient_type"] == WorkflowRecipientType.USER.value
        assert response.json()["recipient_id"] == TEST_USER_ID
        mock_recipient_service.create.assert_called_once()

    def test_get_recipients_by_workflow_success(self, client, mock_recipient_service):
        """Test getting recipients by workflow ID successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        recipients = [
            WorkflowRecipient(id="recipient1", workflow_id=workflow_id, recipient_type=WorkflowRecipientType.USER, recipient_id="user1"),
            WorkflowRecipient(id="recipient2", workflow_id=workflow_id, recipient_type=WorkflowRecipientType.GROUP, recipient_id="group1")
        ]
        mock_recipient_service.find_by_workflow.return_value = Success(recipients)
        
        # Act
        response = client.get(f"/api/workflow-recipients/by-workflow/{workflow_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(recipient["workflow_id"] == workflow_id for recipient in response.json())
        mock_recipient_service.find_by_workflow.assert_called_once_with(workflow_id)

    def test_get_recipients_by_action_success(self, client, mock_recipient_service):
        """Test getting recipients by action ID successfully."""
        # Arrange
        action_id = TEST_ACTION_ID
        recipients = [
            WorkflowRecipient(id="recipient1", workflow_id=TEST_WORKFLOW_ID, action_id=action_id, recipient_type=WorkflowRecipientType.USER, recipient_id="user1"),
            WorkflowRecipient(id="recipient2", workflow_id=TEST_WORKFLOW_ID, action_id=action_id, recipient_type=WorkflowRecipientType.GROUP, recipient_id="group1")
        ]
        mock_recipient_service.find_by_action.return_value = Success(recipients)
        
        # Act
        response = client.get(f"/api/workflow-recipients/by-action/{action_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(recipient["action_id"] == action_id for recipient in response.json())
        mock_recipient_service.find_by_action.assert_called_once_with(action_id)

    # WorkflowExecution endpoint tests
    
    def test_create_execution_success(self, client, mock_execution_service):
        """Test creating an execution record successfully."""
        # Arrange
        new_execution = WorkflowExecutionRecord(
            id=TEST_EXECUTION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            trigger_event_id=TEST_EVENT_ID
        )
        mock_execution_service.create.return_value = Success(new_execution)
        
        # Act
        response = client.post(
            "/api/workflow-executions/",
            json={
                "id": TEST_EXECUTION_ID,
                "workflow_id": TEST_WORKFLOW_ID,
                "trigger_event_id": TEST_EVENT_ID
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == TEST_EXECUTION_ID
        assert response.json()["workflow_id"] == TEST_WORKFLOW_ID
        assert response.json()["trigger_event_id"] == TEST_EVENT_ID
        assert response.json()["status"] == WorkflowExecutionStatus.PENDING.value
        mock_execution_service.create.assert_called_once()

    def test_update_execution_status_success(self, client, mock_execution_service):
        """Test updating execution status successfully."""
        # Arrange
        execution_id = TEST_EXECUTION_ID
        updated_execution = WorkflowExecutionRecord(
            id=execution_id,
            workflow_id=TEST_WORKFLOW_ID,
            trigger_event_id=TEST_EVENT_ID,
            status=WorkflowExecutionStatus.COMPLETED,
            result={"success": True}
        )
        mock_execution_service.update_status.return_value = Success(updated_execution)
        
        # Act
        response = client.post(
            f"/api/workflow-executions/{execution_id}/update-status",
            json={
                "status": WorkflowExecutionStatus.COMPLETED.value,
                "result": {"success": True}
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == execution_id
        assert response.json()["status"] == WorkflowExecutionStatus.COMPLETED.value
        assert response.json()["result"] == {"success": True}
        mock_execution_service.update_status.assert_called_once()

    def test_get_executions_by_workflow_success(self, client, mock_execution_service):
        """Test getting executions by workflow ID successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        executions = [
            WorkflowExecutionRecord(id="exec1", workflow_id=workflow_id, trigger_event_id="event1", status=WorkflowExecutionStatus.COMPLETED),
            WorkflowExecutionRecord(id="exec2", workflow_id=workflow_id, trigger_event_id="event2", status=WorkflowExecutionStatus.FAILED)
        ]
        mock_execution_service.find_by_workflow.return_value = Success(executions)
        
        # Act
        response = client.get(f"/api/workflow-executions/by-workflow/{workflow_id}")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert all(execution["workflow_id"] == workflow_id for execution in response.json())
        mock_execution_service.find_by_workflow.assert_called_once_with(workflow_id)