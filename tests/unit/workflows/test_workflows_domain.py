"""
Tests for the Workflows module domain components.

This module contains comprehensive tests for the Workflows module domain entities,
repositories, and services to ensure proper functionality and compliance with 
domain-driven design principles.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid
from typing import List, Dict, Any, Optional
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
from uno.workflows.domain_repositories import (
    WorkflowDefRepository, WorkflowTriggerRepository, WorkflowConditionRepository,
    WorkflowActionRepository, WorkflowRecipientRepository, WorkflowExecutionRepository
)
from uno.workflows.domain_services import (
    WorkflowDefService, WorkflowTriggerService, WorkflowConditionService,
    WorkflowActionService, WorkflowRecipientService, WorkflowExecutionService
)

# Test Data
TEST_WORKFLOW_ID = "test_workflow"
TEST_TRIGGER_ID = "test_trigger"
TEST_CONDITION_ID = "test_condition"
TEST_ACTION_ID = "test_action"
TEST_RECIPIENT_ID = "test_recipient"
TEST_EXECUTION_ID = "test_execution"
TEST_USER_ID = "test_user"
TEST_EVENT_ID = "test_event"


class TestUserEntity:
    """Tests for the User domain entity."""

    def test_create_user(self):
        """Test creating a user entity."""
        # Arrange
        user_id = TEST_USER_ID
        username = "testuser"
        email = "test@example.com"
        
        # Act
        user = User(
            id=user_id,
            username=username,
            email=email
        )
        
        # Assert
        assert user.id == user_id
        assert user.username == username
        assert user.email == email
        assert user.is_active is True
        assert user.display_name is None
        assert user.roles == []

    def test_validate_user_valid(self):
        """Test validation with a valid user."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            username="testuser",
            email="test@example.com"
        )
        
        # Act & Assert
        user.validate()  # Should not raise an exception

    def test_validate_user_invalid_empty_id(self):
        """Test validation with empty ID."""
        # Arrange
        user = User(
            id="",  # Empty ID
            username="testuser",
            email="test@example.com"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="User ID is required"):
            user.validate()

    def test_validate_user_invalid_empty_username(self):
        """Test validation with empty username."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            username="",  # Empty username
            email="test@example.com"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Username is required"):
            user.validate()

    def test_validate_user_invalid_empty_email(self):
        """Test validation with empty email."""
        # Arrange
        user = User(
            id=TEST_USER_ID,
            username="testuser",
            email=""  # Empty email
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email is required"):
            user.validate()


class TestWorkflowTriggerEntity:
    """Tests for the WorkflowTrigger domain entity."""

    def test_create_workflow_trigger(self):
        """Test creating a workflow trigger entity."""
        # Arrange
        trigger_id = TEST_TRIGGER_ID
        workflow_id = TEST_WORKFLOW_ID
        entity_type = "User"
        operation = "INSERT"
        field_conditions = {"status": "ACTIVE"}
        
        # Act
        trigger = WorkflowTrigger(
            id=trigger_id,
            workflow_id=workflow_id,
            entity_type=entity_type,
            operation=operation,
            field_conditions=field_conditions
        )
        
        # Assert
        assert trigger.id == trigger_id
        assert trigger.workflow_id == workflow_id
        assert trigger.entity_type == entity_type
        assert trigger.operation == operation
        assert trigger.field_conditions == field_conditions
        assert trigger.priority == 100
        assert trigger.is_active is True
        assert trigger.__uno_model__ == "WorkflowTriggerModel"

    def test_validate_workflow_trigger_valid(self):
        """Test validation with a valid workflow trigger."""
        # Arrange
        trigger = WorkflowTrigger(
            id=TEST_TRIGGER_ID,
            workflow_id=TEST_WORKFLOW_ID,
            entity_type="User",
            operation="INSERT"
        )
        
        # Act & Assert
        trigger.validate()  # Should not raise an exception

    def test_validate_workflow_trigger_invalid_empty_entity_type(self):
        """Test validation with empty entity type."""
        # Arrange
        trigger = WorkflowTrigger(
            id=TEST_TRIGGER_ID,
            workflow_id=TEST_WORKFLOW_ID,
            entity_type="",  # Empty entity type
            operation="INSERT"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Entity type is required"):
            trigger.validate()

    def test_validate_workflow_trigger_invalid_empty_operation(self):
        """Test validation with empty operation."""
        # Arrange
        trigger = WorkflowTrigger(
            id=TEST_TRIGGER_ID,
            workflow_id=TEST_WORKFLOW_ID,
            entity_type="User",
            operation=""  # Empty operation
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Operation is required"):
            trigger.validate()

    def test_from_record(self):
        """Test creating a workflow trigger from a record."""
        # Arrange
        record = {
            "id": TEST_TRIGGER_ID,
            "workflow_id": TEST_WORKFLOW_ID,
            "entity_type": "User",
            "operation": "INSERT",
            "field_conditions": {"status": "ACTIVE"},
            "priority": 50,
            "is_active": False
        }
        
        # Act
        trigger = WorkflowTrigger.from_record(record)
        
        # Assert
        assert trigger.id == record["id"]
        assert trigger.workflow_id == record["workflow_id"]
        assert trigger.entity_type == record["entity_type"]
        assert trigger.operation == record["operation"]
        assert trigger.field_conditions == record["field_conditions"]
        assert trigger.priority == record["priority"]
        assert trigger.is_active == record["is_active"]


class TestWorkflowConditionEntity:
    """Tests for the WorkflowCondition domain entity."""

    def test_create_workflow_condition(self):
        """Test creating a workflow condition entity."""
        # Arrange
        condition_id = TEST_CONDITION_ID
        workflow_id = TEST_WORKFLOW_ID
        condition_type = WorkflowConditionType.FIELD_VALUE
        condition_config = {"field": "status", "value": "ACTIVE", "operator": "equals"}
        
        # Act
        condition = WorkflowCondition(
            id=condition_id,
            workflow_id=workflow_id,
            condition_type=condition_type,
            condition_config=condition_config
        )
        
        # Assert
        assert condition.id == condition_id
        assert condition.workflow_id == workflow_id
        assert condition.condition_type == condition_type
        assert condition.condition_config == condition_config
        assert condition.query_id is None
        assert condition.name == ""
        assert condition.description is None
        assert condition.order == 0
        assert condition.__uno_model__ == "WorkflowConditionModel"

    def test_validate_workflow_condition_valid_field_value(self):
        """Test validation with a valid field value condition."""
        # Arrange
        condition = WorkflowCondition(
            id=TEST_CONDITION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            condition_type=WorkflowConditionType.FIELD_VALUE,
            condition_config={"field": "status", "value": "ACTIVE", "operator": "equals"}
        )
        
        # Act & Assert
        condition.validate()  # Should not raise an exception

    def test_validate_workflow_condition_valid_query_match(self):
        """Test validation with a valid query match condition."""
        # Arrange
        condition = WorkflowCondition(
            id=TEST_CONDITION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            condition_type=WorkflowConditionType.QUERY_MATCH,
            query_id="query123"
        )
        
        # Act & Assert
        condition.validate()  # Should not raise an exception

    def test_validate_workflow_condition_invalid_empty_condition_type(self):
        """Test validation with empty condition type."""
        # Arrange
        condition = WorkflowCondition(
            id=TEST_CONDITION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            condition_type=None,  # Empty condition type
            condition_config={"field": "status"}
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Condition type is required"):
            condition.validate()

    def test_validate_workflow_condition_invalid_field_value_missing_field(self):
        """Test validation with field value condition missing field."""
        # Arrange
        condition = WorkflowCondition(
            id=TEST_CONDITION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            condition_type=WorkflowConditionType.FIELD_VALUE,
            condition_config={"value": "ACTIVE"}  # Missing field
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Field is required for field value conditions"):
            condition.validate()

    def test_validate_workflow_condition_invalid_query_match_missing_query_id(self):
        """Test validation with query match condition missing query ID."""
        # Arrange
        condition = WorkflowCondition(
            id=TEST_CONDITION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            condition_type=WorkflowConditionType.QUERY_MATCH,
            query_id=None  # Missing query ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Query ID is required for query match conditions"):
            condition.validate()

    def test_from_record(self):
        """Test creating a workflow condition from a record."""
        # Arrange
        record = {
            "id": TEST_CONDITION_ID,
            "workflow_id": TEST_WORKFLOW_ID,
            "condition_type": WorkflowConditionType.FIELD_VALUE,
            "condition_config": {"field": "status", "value": "ACTIVE"},
            "query_id": None,
            "name": "Status Check",
            "description": "Check if status is active",
            "order": 1
        }
        
        # Act
        condition = WorkflowCondition.from_record(record)
        
        # Assert
        assert condition.id == record["id"]
        assert condition.workflow_id == record["workflow_id"]
        assert condition.condition_type == record["condition_type"]
        assert condition.condition_config == record["condition_config"]
        assert condition.query_id == record["query_id"]
        assert condition.name == record["name"]
        assert condition.description == record["description"]
        assert condition.order == record["order"]


class TestWorkflowRecipientEntity:
    """Tests for the WorkflowRecipient domain entity."""

    def test_create_workflow_recipient(self):
        """Test creating a workflow recipient entity."""
        # Arrange
        recipient_id = TEST_RECIPIENT_ID
        workflow_id = TEST_WORKFLOW_ID
        recipient_type = WorkflowRecipientType.USER
        user_id = TEST_USER_ID
        
        # Act
        recipient = WorkflowRecipient(
            id=recipient_id,
            workflow_id=workflow_id,
            recipient_type=recipient_type,
            recipient_id=user_id
        )
        
        # Assert
        assert recipient.id == recipient_id
        assert recipient.workflow_id == workflow_id
        assert recipient.recipient_type == recipient_type
        assert recipient.recipient_id == user_id
        assert recipient.name is None
        assert recipient.action_id is None
        assert recipient.notification_config == {}
        assert recipient.__uno_model__ == "WorkflowRecipientModel"

    def test_validate_workflow_recipient_valid(self):
        """Test validation with a valid workflow recipient."""
        # Arrange
        recipient = WorkflowRecipient(
            id=TEST_RECIPIENT_ID,
            workflow_id=TEST_WORKFLOW_ID,
            recipient_type=WorkflowRecipientType.USER,
            recipient_id=TEST_USER_ID
        )
        
        # Act & Assert
        recipient.validate()  # Should not raise an exception

    def test_validate_workflow_recipient_invalid_empty_recipient_type(self):
        """Test validation with empty recipient type."""
        # Arrange
        recipient = WorkflowRecipient(
            id=TEST_RECIPIENT_ID,
            workflow_id=TEST_WORKFLOW_ID,
            recipient_type=None,  # Empty recipient type
            recipient_id=TEST_USER_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Recipient type is required"):
            recipient.validate()

    def test_validate_workflow_recipient_invalid_empty_recipient_id(self):
        """Test validation with empty recipient ID."""
        # Arrange
        recipient = WorkflowRecipient(
            id=TEST_RECIPIENT_ID,
            workflow_id=TEST_WORKFLOW_ID,
            recipient_type=WorkflowRecipientType.USER,
            recipient_id=""  # Empty recipient ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Recipient ID is required"):
            recipient.validate()

    def test_from_record(self):
        """Test creating a workflow recipient from a record."""
        # Arrange
        record = {
            "id": TEST_RECIPIENT_ID,
            "workflow_id": TEST_WORKFLOW_ID,
            "recipient_type": WorkflowRecipientType.USER,
            "recipient_id": TEST_USER_ID,
            "name": "Test User",
            "action_id": TEST_ACTION_ID,
            "notification_config": {"email": True, "sms": False}
        }
        
        # Act
        recipient = WorkflowRecipient.from_record(record)
        
        # Assert
        assert recipient.id == record["id"]
        assert recipient.workflow_id == record["workflow_id"]
        assert recipient.recipient_type == record["recipient_type"]
        assert recipient.recipient_id == record["recipient_id"]
        assert recipient.name == record["name"]
        assert recipient.action_id == record["action_id"]
        assert recipient.notification_config == record["notification_config"]


class TestWorkflowActionEntity:
    """Tests for the WorkflowAction domain entity."""

    def test_create_workflow_action(self):
        """Test creating a workflow action entity."""
        # Arrange
        action_id = TEST_ACTION_ID
        workflow_id = TEST_WORKFLOW_ID
        action_type = WorkflowActionType.EMAIL
        action_config = {"subject": "Test Subject", "body": "Test Body"}
        
        # Act
        action = WorkflowAction(
            id=action_id,
            workflow_id=workflow_id,
            action_type=action_type,
            action_config=action_config
        )
        
        # Assert
        assert action.id == action_id
        assert action.workflow_id == workflow_id
        assert action.action_type == action_type
        assert action.action_config == action_config
        assert action.name == ""
        assert action.description is None
        assert action.order == 0
        assert action.is_active is True
        assert action.retry_policy is None
        assert action.recipients == []
        assert action.workflow is None
        assert action.__uno_model__ == "WorkflowActionModel"

    def test_validate_workflow_action_valid_email(self):
        """Test validation with a valid email action."""
        # Arrange
        action = WorkflowAction(
            id=TEST_ACTION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            action_type=WorkflowActionType.EMAIL,
            action_config={"subject": "Test Subject", "body": "Test Body"}
        )
        
        # Act & Assert
        action.validate()  # Should not raise an exception

    def test_validate_workflow_action_valid_webhook(self):
        """Test validation with a valid webhook action."""
        # Arrange
        action = WorkflowAction(
            id=TEST_ACTION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            action_type=WorkflowActionType.WEBHOOK,
            action_config={"url": "https://example.com/webhook", "method": "POST"}
        )
        
        # Act & Assert
        action.validate()  # Should not raise an exception

    def test_validate_workflow_action_invalid_empty_action_type(self):
        """Test validation with empty action type."""
        # Arrange
        action = WorkflowAction(
            id=TEST_ACTION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            action_type=None,  # Empty action type
            action_config={"subject": "Test Subject"}
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Action type is required"):
            action.validate()

    def test_validate_workflow_action_invalid_email_missing_subject(self):
        """Test validation with email action missing subject."""
        # Arrange
        action = WorkflowAction(
            id=TEST_ACTION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            action_type=WorkflowActionType.EMAIL,
            action_config={"body": "Test Body"}  # Missing subject
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Subject is required for email actions"):
            action.validate()

    def test_validate_workflow_action_invalid_webhook_missing_url(self):
        """Test validation with webhook action missing URL."""
        # Arrange
        action = WorkflowAction(
            id=TEST_ACTION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            action_type=WorkflowActionType.WEBHOOK,
            action_config={"method": "POST"}  # Missing URL
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="URL is required for webhook actions"):
            action.validate()

    def test_from_record(self):
        """Test creating a workflow action from a record."""
        # Arrange
        record = {
            "id": TEST_ACTION_ID,
            "workflow_id": TEST_WORKFLOW_ID,
            "action_type": WorkflowActionType.EMAIL,
            "action_config": {"subject": "Test Subject", "body": "Test Body"},
            "name": "Send Email",
            "description": "Send an email notification",
            "order": 1,
            "is_active": True,
            "retry_policy": {"max_retries": 3, "retry_delay": 60}
        }
        
        # Act
        action = WorkflowAction.from_record(record)
        
        # Assert
        assert action.id == record["id"]
        assert action.workflow_id == record["workflow_id"]
        assert action.action_type == record["action_type"]
        assert action.action_config == record["action_config"]
        assert action.name == record["name"]
        assert action.description == record["description"]
        assert action.order == record["order"]
        assert action.is_active == record["is_active"]
        assert action.retry_policy == record["retry_policy"]
        assert action.recipients == []


class TestWorkflowExecutionRecordEntity:
    """Tests for the WorkflowExecutionRecord domain entity."""

    def test_create_workflow_execution_record(self):
        """Test creating a workflow execution record entity."""
        # Arrange
        execution_id = TEST_EXECUTION_ID
        workflow_id = TEST_WORKFLOW_ID
        trigger_event_id = TEST_EVENT_ID
        
        # Act
        execution = WorkflowExecutionRecord(
            id=execution_id,
            workflow_id=workflow_id,
            trigger_event_id=trigger_event_id
        )
        
        # Assert
        assert execution.id == execution_id
        assert execution.workflow_id == workflow_id
        assert execution.trigger_event_id == trigger_event_id
        assert execution.status == WorkflowExecutionStatus.PENDING
        assert execution.executed_at is not None
        assert execution.completed_at is None
        assert execution.result is None
        assert execution.error is None
        assert execution.context is None
        assert execution.execution_time is None
        assert execution.__uno_model__ == "WorkflowExecutionLog"

    def test_validate_workflow_execution_record_valid(self):
        """Test validation with a valid workflow execution record."""
        # Arrange
        execution = WorkflowExecutionRecord(
            id=TEST_EXECUTION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            trigger_event_id=TEST_EVENT_ID
        )
        
        # Act & Assert
        execution.validate()  # Should not raise an exception

    def test_validate_workflow_execution_record_invalid_empty_workflow_id(self):
        """Test validation with empty workflow ID."""
        # Arrange
        execution = WorkflowExecutionRecord(
            id=TEST_EXECUTION_ID,
            workflow_id="",  # Empty workflow ID
            trigger_event_id=TEST_EVENT_ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Workflow ID is required"):
            execution.validate()

    def test_validate_workflow_execution_record_invalid_empty_trigger_event_id(self):
        """Test validation with empty trigger event ID."""
        # Arrange
        execution = WorkflowExecutionRecord(
            id=TEST_EXECUTION_ID,
            workflow_id=TEST_WORKFLOW_ID,
            trigger_event_id=""  # Empty trigger event ID
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Trigger event ID is required"):
            execution.validate()

    def test_from_record(self):
        """Test creating a workflow execution record from a record."""
        # Arrange
        now = datetime.now(UTC)
        completed = now.replace(microsecond=now.microsecond + 1000)
        record = {
            "id": TEST_EXECUTION_ID,
            "workflow_id": TEST_WORKFLOW_ID,
            "trigger_event_id": TEST_EVENT_ID,
            "status": WorkflowExecutionStatus.COMPLETED,
            "executed_at": now,
            "completed_at": completed,
            "result": {"success": True},
            "error": None,
            "context": {"user_id": TEST_USER_ID},
            "execution_time": 0.12
        }
        
        # Act
        execution = WorkflowExecutionRecord.from_record(record)
        
        # Assert
        assert execution.id == record["id"]
        assert execution.workflow_id == record["workflow_id"]
        assert execution.trigger_event_id == record["trigger_event_id"]
        assert execution.status == record["status"]
        assert execution.executed_at == record["executed_at"]
        assert execution.completed_at == record["completed_at"]
        assert execution.result == record["result"]
        assert execution.error == record["error"]
        assert execution.context == record["context"]
        assert execution.execution_time == record["execution_time"]


class TestWorkflowDefEntity:
    """Tests for the WorkflowDef domain entity."""

    def test_create_workflow_def(self):
        """Test creating a workflow definition entity."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        name = "Test Workflow"
        description = "A test workflow"
        
        # Act
        workflow = WorkflowDef(
            id=workflow_id,
            name=name,
            description=description
        )
        
        # Assert
        assert workflow.id == workflow_id
        assert workflow.name == name
        assert workflow.description == description
        assert workflow.status == WorkflowStatus.DRAFT
        assert workflow.version == "1.0.0"
        assert workflow.triggers == []
        assert workflow.conditions == []
        assert workflow.actions == []
        assert workflow.recipients == []
        assert workflow.logs == []
        assert workflow.__uno_model__ == "WorkflowDefinition"

    def test_validate_workflow_def_valid(self):
        """Test validation with a valid workflow definition."""
        # Arrange
        workflow = WorkflowDef(
            id=TEST_WORKFLOW_ID,
            name="Test Workflow",
            description="A test workflow"
        )
        
        # Act & Assert
        workflow.validate()  # Should not raise an exception

    def test_validate_workflow_def_invalid_empty_name(self):
        """Test validation with empty name."""
        # Arrange
        workflow = WorkflowDef(
            id=TEST_WORKFLOW_ID,
            name="",  # Empty name
            description="A test workflow"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Name is required"):
            workflow.validate()

    def test_validate_workflow_def_invalid_empty_description(self):
        """Test validation with empty description."""
        # Arrange
        workflow = WorkflowDef(
            id=TEST_WORKFLOW_ID,
            name="Test Workflow",
            description=""  # Empty description
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Description is required"):
            workflow.validate()

    def test_validate_workflow_def_invalid_status(self):
        """Test validation with invalid status."""
        # Arrange
        workflow = WorkflowDef(
            id=TEST_WORKFLOW_ID,
            name="Test Workflow",
            description="A test workflow",
            status="INVALID"  # Invalid status
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid status"):
            workflow.validate()

    def test_from_record(self):
        """Test creating a workflow definition from a record."""
        # Arrange
        record = {
            "id": TEST_WORKFLOW_ID,
            "name": "Test Workflow",
            "description": "A test workflow",
            "status": WorkflowStatus.ACTIVE,
            "version": "2.0.0"
        }
        
        # Act
        workflow = WorkflowDef.from_record(record)
        
        # Assert
        assert workflow.id == record["id"]
        assert workflow.name == record["name"]
        assert workflow.description == record["description"]
        assert workflow.status == record["status"]
        assert workflow.version == record["version"]
        assert workflow.triggers == []
        assert workflow.conditions == []
        assert workflow.actions == []
        assert workflow.recipients == []
        assert workflow.logs == []


# Repository Tests

class TestWorkflowDefRepository:
    """Tests for the WorkflowDefRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a WorkflowDefRepository instance."""
        return WorkflowDefRepository()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_session):
        """Test getting a workflow by ID successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        mock_session.get.return_value = WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow"
        )

        # Act
        result = await repository.get_by_id(workflow_id, mock_session)

        # Assert
        assert result.is_success
        workflow = result.value
        assert workflow.id == workflow_id
        assert workflow.name == "Test Workflow"
        mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_with_relationships(self, repository, mock_session):
        """Test getting a workflow with relationships."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        workflow = WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow"
        )
        
        # Mock DB models as needed
        mock_session.get.return_value = workflow
        
        # Mock joined load execution
        mock_query = AsyncMock()
        mock_session.execute.return_value.scalar.return_value = workflow
        
        # Act
        result = await repository.get_with_relationships(workflow_id, mock_session)
        
        # Assert
        assert result.id == workflow_id
        assert result.name == "Test Workflow"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_status(self, repository, mock_session):
        """Test finding workflows by status."""
        # Arrange
        status = WorkflowStatus.ACTIVE
        workflows = [
            WorkflowDef(id="workflow1", name="Workflow 1", description="Description 1", status=status),
            WorkflowDef(id="workflow2", name="Workflow 2", description="Description 2", status=status)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = workflows
        
        # Act
        result = await repository.find_by_status(status, mock_session)
        
        # Assert
        assert len(result) == 2
        assert all(workflow.status == status for workflow in result)
        mock_session.execute.assert_called_once()


class TestWorkflowTriggerRepository:
    """Tests for the WorkflowTriggerRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock session."""
        return AsyncMock()

    @pytest.fixture
    def repository(self):
        """Create a WorkflowTriggerRepository instance."""
        return WorkflowTriggerRepository()

    @pytest.mark.asyncio
    async def test_find_by_workflow(self, repository, mock_session):
        """Test finding triggers by workflow ID."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        triggers = [
            WorkflowTrigger(id="trigger1", workflow_id=workflow_id, entity_type="User", operation="INSERT"),
            WorkflowTrigger(id="trigger2", workflow_id=workflow_id, entity_type="Order", operation="UPDATE")
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = triggers
        
        # Act
        result = await repository.find_by_workflow(workflow_id, mock_session)
        
        # Assert
        assert len(result) == 2
        assert all(trigger.workflow_id == workflow_id for trigger in result)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_entity_and_operation(self, repository, mock_session):
        """Test finding triggers by entity type and operation."""
        # Arrange
        entity_type = "User"
        operation = "INSERT"
        triggers = [
            WorkflowTrigger(id="trigger1", workflow_id="workflow1", entity_type=entity_type, operation=operation),
            WorkflowTrigger(id="trigger2", workflow_id="workflow2", entity_type=entity_type, operation=operation)
        ]
        mock_session.execute.return_value.scalars.return_value.all.return_value = triggers
        
        # Act
        result = await repository.find_by_entity_and_operation(entity_type, operation, mock_session)
        
        # Assert
        assert len(result) == 2
        assert all(trigger.entity_type == entity_type for trigger in result)
        assert all(trigger.operation == operation for trigger in result)
        mock_session.execute.assert_called_once()


# Service Tests

class TestWorkflowDefService:
    """Tests for the WorkflowDefService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock(spec=WorkflowDefRepository)

    @pytest.fixture
    def mock_trigger_repository(self):
        """Create a mock trigger repository."""
        return AsyncMock(spec=WorkflowTriggerRepository)

    @pytest.fixture
    def mock_condition_repository(self):
        """Create a mock condition repository."""
        return AsyncMock(spec=WorkflowConditionRepository)

    @pytest.fixture
    def mock_action_repository(self):
        """Create a mock action repository."""
        return AsyncMock(spec=WorkflowActionRepository)

    @pytest.fixture
    def mock_recipient_repository(self):
        """Create a mock recipient repository."""
        return AsyncMock(spec=WorkflowRecipientRepository)

    @pytest.fixture
    def service(self, mock_repository, mock_trigger_repository, mock_condition_repository, 
                mock_action_repository, mock_recipient_repository):
        """Create a WorkflowDefService instance."""
        service = WorkflowDefService(repository=mock_repository)
        service.trigger_repository = mock_trigger_repository
        service.condition_repository = mock_condition_repository
        service.action_repository = mock_action_repository
        service.recipient_repository = mock_recipient_repository
        return service

    @pytest.mark.asyncio
    async def test_create_workflow_success(self, service, mock_repository):
        """Test creating a workflow successfully."""
        # Arrange
        workflow = WorkflowDef(
            id=TEST_WORKFLOW_ID,
            name="Test Workflow",
            description="A test workflow"
        )
        mock_repository.save.return_value = Success(workflow)
        
        # Act
        result = await service.create(
            id=TEST_WORKFLOW_ID,
            name="Test Workflow",
            description="A test workflow"
        )
        
        # Assert
        assert result.is_success
        assert result.value.id == TEST_WORKFLOW_ID
        assert result.value.name == "Test Workflow"
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_workflow_validation_error(self, service):
        """Test creating a workflow with validation error."""
        # Act - Missing required description
        result = await service.create(
            id=TEST_WORKFLOW_ID,
            name="Test Workflow",
            description=""  # Empty description
        )
        
        # Assert
        assert result.is_failure
        assert "Description is required" in str(result.error)

    @pytest.mark.asyncio
    async def test_get_with_relationships_success(self, service, mock_repository):
        """Test getting a workflow with relationships successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        workflow = WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow"
        )
        mock_repository.get_with_relationships.return_value = workflow
        
        # Act
        result = await service.get_with_relationships(workflow_id)
        
        # Assert
        assert result.is_success
        assert result.value.id == workflow_id
        mock_repository.get_with_relationships.assert_called_once_with(workflow_id, None)

    @pytest.mark.asyncio
    async def test_get_with_relationships_not_found(self, service, mock_repository):
        """Test getting a workflow with relationships when not found."""
        # Arrange
        workflow_id = "nonexistent"
        mock_repository.get_with_relationships.return_value = None
        
        # Act
        result = await service.get_with_relationships(workflow_id)
        
        # Assert
        assert result.is_failure
        assert f"Workflow {workflow_id} not found" in str(result.error)
        mock_repository.get_with_relationships.assert_called_once_with(workflow_id, None)

    @pytest.mark.asyncio
    async def test_find_by_status_success(self, service, mock_repository):
        """Test finding workflows by status successfully."""
        # Arrange
        status = WorkflowStatus.ACTIVE
        workflows = [
            WorkflowDef(id="workflow1", name="Workflow 1", description="Description 1", status=status),
            WorkflowDef(id="workflow2", name="Workflow 2", description="Description 2", status=status)
        ]
        mock_repository.find_by_status.return_value = workflows
        
        # Act
        result = await service.find_by_status(status)
        
        # Assert
        assert result.is_success
        assert len(result.value) == 2
        assert all(workflow.status == status for workflow in result.value)
        mock_repository.find_by_status.assert_called_once_with(status, None)

    @pytest.mark.asyncio
    async def test_activate_workflow_success(self, service, mock_repository):
        """Test activating a workflow successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        workflow = WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow",
            status=WorkflowStatus.DRAFT
        )
        
        # Mock get and save
        mock_repository.get.return_value = workflow
        mock_repository.save.return_value = Success(WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow",
            status=WorkflowStatus.ACTIVE
        ))
        
        # Act
        result = await service.activate_workflow(workflow_id)
        
        # Assert
        assert result.is_success
        assert result.value.status == WorkflowStatus.ACTIVE
        mock_repository.get.assert_called_once()
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_workflow_success(self, service, mock_repository):
        """Test deactivating a workflow successfully."""
        # Arrange
        workflow_id = TEST_WORKFLOW_ID
        workflow = WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow",
            status=WorkflowStatus.ACTIVE
        )
        
        # Mock get and save
        mock_repository.get.return_value = workflow
        mock_repository.save.return_value = Success(WorkflowDef(
            id=workflow_id,
            name="Test Workflow",
            description="A test workflow",
            status=WorkflowStatus.INACTIVE
        ))
        
        # Act
        result = await service.deactivate_workflow(workflow_id)
        
        # Assert
        assert result.is_success
        assert result.value.status == WorkflowStatus.INACTIVE
        mock_repository.get.assert_called_once()
        mock_repository.save.assert_called_once()