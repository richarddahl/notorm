"""
Domain repositories for the Workflows module.

This module provides domain repositories for persisting and retrieving
workflow entities from the database following the repository pattern.
"""

from typing import List, Dict, Any, Optional, TypeVar, Generic, cast
import logging
from uuid import uuid4

from uno.domain.repository import UnoDBRepository
from uno.core.errors.result import Result, Success, Failure
from uno.workflows.entities import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
    WorkflowExecutionRecord,
)
from uno.workflows.errors import WorkflowNotFoundError, WorkflowExecutionError

# Type variables
T = TypeVar("T")


class WorkflowRepositoryError(Exception):
    """Base error class for workflow repository errors."""

    pass


class WorkflowDefRepository(UnoDBRepository[WorkflowDef]):
    """Repository for workflow definition entities."""

    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=WorkflowDef, db_factory=db_factory)
        self.logger = logging.getLogger(__name__)

    async def create_workflow(
        self, name: str, description: str, **kwargs
    ) -> Result[WorkflowDef]:
        """
        Create a new workflow definition.

        Args:
            name: The name of the workflow
            description: The description of the workflow
            **kwargs: Additional workflow properties

        Returns:
            Result containing the created workflow
        """
        try:
            workflow = WorkflowDef(
                id=str(uuid4()), name=name, description=description, **kwargs
            )

            # Validate the workflow
            workflow.validate()

            # Save to database
            saved_workflow = await self.add(workflow)
            return Success(saved_workflow)
        except Exception as e:
            self.logger.error(f"Error creating workflow: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error creating workflow: {str(e)}")
            )

    async def find_active_workflows(self) -> Result[List[WorkflowDef]]:
        """
        Find all active workflows.

        Returns:
            Result containing active workflows
        """
        try:
            from uno.workflows.models import WorkflowStatus

            filters = {"status": {"lookup": "eq", "val": WorkflowStatus.ACTIVE}}
            workflows = await self.list(filters=filters)
            return Success(workflows)
        except Exception as e:
            self.logger.error(f"Error finding active workflows: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error finding active workflows: {str(e)}")
            )

    async def get_with_relationships(self, id: str) -> Result[WorkflowDef]:
        """
        Get a workflow with all its relationships loaded.

        Args:
            id: The ID of the workflow

        Returns:
            Result containing the workflow with relationships
        """
        try:
            # First get the basic workflow
            workflow = await self.get(id)
            if not workflow:
                return Failure(WorkflowNotFoundError(f"Workflow {id} not found"))

            # Load triggers, conditions, actions, and recipients
            # In a real implementation, these would be loaded using the appropriate repositories
            # For now, just initialize the lists
            workflow.triggers = []
            workflow.conditions = []
            workflow.actions = []
            workflow.recipients = []
            workflow.logs = []

            return Success(workflow)
        except Exception as e:
            self.logger.error(f"Error getting workflow with relationships: {e}")
            return Failure(WorkflowRepositoryError(f"Error getting workflow: {str(e)}"))


class WorkflowTriggerRepository(UnoDBRepository[WorkflowTrigger]):
    """Repository for workflow trigger entities."""

    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=WorkflowTrigger, db_factory=db_factory)
        self.logger = logging.getLogger(__name__)

    async def find_by_workflow(self, workflow_id: str) -> Result[List[WorkflowTrigger]]:
        """
        Find triggers for a specific workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the workflow triggers
        """
        try:
            filters = {"workflow_id": {"lookup": "eq", "val": workflow_id}}
            triggers = await self.list(filters=filters)
            return Success(triggers)
        except Exception as e:
            self.logger.error(f"Error finding workflow triggers: {e}")
            return Failure(WorkflowRepositoryError(f"Error finding triggers: {str(e)}"))

    async def create_trigger(
        self,
        workflow_id: str,
        entity_type: str,
        operation: str,
        field_conditions: Dict[str, Any] = None,
        **kwargs,
    ) -> Result[WorkflowTrigger]:
        """
        Create a new workflow trigger.

        Args:
            workflow_id: The ID of the workflow
            entity_type: The type of entity that triggers the workflow
            operation: The operation that triggers the workflow
            field_conditions: Optional conditions on fields
            **kwargs: Additional trigger properties

        Returns:
            Result containing the created trigger
        """
        try:
            trigger = WorkflowTrigger(
                id=str(uuid4()),
                workflow_id=workflow_id,
                entity_type=entity_type,
                operation=operation,
                field_conditions=field_conditions or {},
                **kwargs,
            )

            # Validate the trigger
            trigger.validate()

            # Save to database
            saved_trigger = await self.add(trigger)
            return Success(saved_trigger)
        except Exception as e:
            self.logger.error(f"Error creating workflow trigger: {e}")
            return Failure(WorkflowRepositoryError(f"Error creating trigger: {str(e)}"))


class WorkflowConditionRepository(UnoDBRepository[WorkflowCondition]):
    """Repository for workflow condition entities."""

    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=WorkflowCondition, db_factory=db_factory)
        self.logger = logging.getLogger(__name__)

    async def find_by_workflow(
        self, workflow_id: str
    ) -> Result[List[WorkflowCondition]]:
        """
        Find conditions for a specific workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the workflow conditions
        """
        try:
            filters = {"workflow_id": {"lookup": "eq", "val": workflow_id}}
            conditions = await self.list(filters=filters)
            return Success(conditions)
        except Exception as e:
            self.logger.error(f"Error finding workflow conditions: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error finding conditions: {str(e)}")
            )

    async def create_condition(
        self,
        workflow_id: str,
        condition_type,
        condition_config: Dict[str, Any] = None,
        **kwargs,
    ) -> Result[WorkflowCondition]:
        """
        Create a new workflow condition.

        Args:
            workflow_id: The ID of the workflow
            condition_type: The type of condition
            condition_config: The configuration for the condition
            **kwargs: Additional condition properties

        Returns:
            Result containing the created condition
        """
        try:
            condition = WorkflowCondition(
                id=str(uuid4()),
                workflow_id=workflow_id,
                condition_type=condition_type,
                condition_config=condition_config or {},
                **kwargs,
            )

            # Validate the condition
            condition.validate()

            # Save to database
            saved_condition = await self.add(condition)
            return Success(saved_condition)
        except Exception as e:
            self.logger.error(f"Error creating workflow condition: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error creating condition: {str(e)}")
            )


class WorkflowActionRepository(UnoDBRepository[WorkflowAction]):
    """Repository for workflow action entities."""

    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=WorkflowAction, db_factory=db_factory)
        self.logger = logging.getLogger(__name__)

    async def find_by_workflow(self, workflow_id: str) -> Result[List[WorkflowAction]]:
        """
        Find actions for a specific workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the workflow actions
        """
        try:
            filters = {"workflow_id": {"lookup": "eq", "val": workflow_id}}
            actions = await self.list(filters=filters)
            return Success(actions)
        except Exception as e:
            self.logger.error(f"Error finding workflow actions: {e}")
            return Failure(WorkflowRepositoryError(f"Error finding actions: {str(e)}"))

    async def create_action(
        self,
        workflow_id: str,
        action_type,
        action_config: Dict[str, Any] = None,
        **kwargs,
    ) -> Result[WorkflowAction]:
        """
        Create a new workflow action.

        Args:
            workflow_id: The ID of the workflow
            action_type: The type of action
            action_config: The configuration for the action
            **kwargs: Additional action properties

        Returns:
            Result containing the created action
        """
        try:
            action = WorkflowAction(
                id=str(uuid4()),
                workflow_id=workflow_id,
                action_type=action_type,
                action_config=action_config or {},
                **kwargs,
            )

            # Validate the action
            action.validate()

            # Save to database
            saved_action = await self.add(action)
            return Success(saved_action)
        except Exception as e:
            self.logger.error(f"Error creating workflow action: {e}")
            return Failure(WorkflowRepositoryError(f"Error creating action: {str(e)}"))


class WorkflowRecipientRepository(UnoDBRepository[WorkflowRecipient]):
    """Repository for workflow recipient entities."""

    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=WorkflowRecipient, db_factory=db_factory)
        self.logger = logging.getLogger(__name__)

    async def find_by_workflow(
        self, workflow_id: str
    ) -> Result[List[WorkflowRecipient]]:
        """
        Find recipients for a specific workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the workflow recipients
        """
        try:
            filters = {"workflow_id": {"lookup": "eq", "val": workflow_id}}
            recipients = await self.list(filters=filters)
            return Success(recipients)
        except Exception as e:
            self.logger.error(f"Error finding workflow recipients: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error finding recipients: {str(e)}")
            )

    async def find_by_action(self, action_id: str) -> Result[List[WorkflowRecipient]]:
        """
        Find recipients for a specific action.

        Args:
            action_id: The ID of the action

        Returns:
            Result containing the action recipients
        """
        try:
            filters = {"action_id": {"lookup": "eq", "val": action_id}}
            recipients = await self.list(filters=filters)
            return Success(recipients)
        except Exception as e:
            self.logger.error(f"Error finding action recipients: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error finding recipients: {str(e)}")
            )

    async def create_recipient(
        self,
        workflow_id: str,
        recipient_type,
        recipient_id: str,
        action_id: Optional[str] = None,
        **kwargs,
    ) -> Result[WorkflowRecipient]:
        """
        Create a new workflow recipient.

        Args:
            workflow_id: The ID of the workflow
            recipient_type: The type of recipient
            recipient_id: The ID of the recipient
            action_id: Optional action ID if this recipient is for a specific action
            **kwargs: Additional recipient properties

        Returns:
            Result containing the created recipient
        """
        try:
            recipient = WorkflowRecipient(
                id=str(uuid4()),
                workflow_id=workflow_id,
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                action_id=action_id,
                **kwargs,
            )

            # Validate the recipient
            recipient.validate()

            # Save to database
            saved_recipient = await self.add(recipient)
            return Success(saved_recipient)
        except Exception as e:
            self.logger.error(f"Error creating workflow recipient: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error creating recipient: {str(e)}")
            )


class WorkflowExecutionRepository(UnoDBRepository[WorkflowExecutionRecord]):
    """Repository for workflow execution record entities."""

    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=WorkflowExecutionRecord, db_factory=db_factory)
        self.logger = logging.getLogger(__name__)

    async def find_by_workflow(
        self, workflow_id: str, limit: int = 100
    ) -> Result[List[WorkflowExecutionRecord]]:
        """
        Find execution records for a specific workflow.

        Args:
            workflow_id: The ID of the workflow
            limit: Maximum number of records to return

        Returns:
            Result containing the workflow execution records
        """
        try:
            filters = {"workflow_id": {"lookup": "eq", "val": workflow_id}}
            records = await self.list(filters=filters, limit=limit)
            return Success(records)
        except Exception as e:
            self.logger.error(f"Error finding workflow execution records: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error finding execution records: {str(e)}")
            )

    async def create_execution_record(
        self, workflow_id: str, trigger_event_id: str, **kwargs
    ) -> Result[WorkflowExecutionRecord]:
        """
        Create a new workflow execution record.

        Args:
            workflow_id: The ID of the workflow
            trigger_event_id: The ID of the trigger event
            **kwargs: Additional execution record properties

        Returns:
            Result containing the created execution record
        """
        try:
            record = WorkflowExecutionRecord(
                id=str(uuid4()),
                workflow_id=workflow_id,
                trigger_event_id=trigger_event_id,
                **kwargs,
            )

            # Validate the record
            record.validate()

            # Save to database
            saved_record = await self.add(record)
            return Success(saved_record)
        except Exception as e:
            self.logger.error(f"Error creating workflow execution record: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error creating execution record: {str(e)}")
            )

    async def update_execution_status(
        self,
        execution_id: str,
        status,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Result[WorkflowExecutionRecord]:
        """
        Update the status of a workflow execution.

        Args:
            execution_id: The ID of the execution record
            status: The new status
            result: Optional result data
            error: Optional error message

        Returns:
            Result containing the updated execution record
        """
        try:
            record = await self.get(execution_id)
            if not record:
                return Failure(
                    WorkflowExecutionError(f"Execution record {execution_id} not found")
                )

            # Update the record
            record.status = status
            if result is not None:
                record.result = result
            if error is not None:
                record.error = error

            # Set completion time if terminal status
            from uno.workflows.models import WorkflowExecutionStatus

            terminal_statuses = [
                WorkflowExecutionStatus.COMPLETED,
                WorkflowExecutionStatus.FAILED,
                WorkflowExecutionStatus.CANCELLED,
            ]
            if status in terminal_statuses:
                from datetime import datetime

                record.completed_at = datetime.now()

                # Calculate execution time
                if record.executed_at and record.completed_at:
                    record.execution_time = (
                        record.completed_at - record.executed_at
                    ).total_seconds()

            # Save changes
            updated_record = await self.update(record)
            return Success(updated_record)
        except Exception as e:
            self.logger.error(f"Error updating workflow execution status: {e}")
            return Failure(
                WorkflowRepositoryError(f"Error updating execution status: {str(e)}")
            )
