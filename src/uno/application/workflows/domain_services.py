"""
Domain services for the Workflows module.

This module provides domain services that implement business logic for workflow entities,
coordinating entity validation and persistence through repositories.
"""

from typing import List, Dict, Any, Optional, TypeVar, Generic, cast
import logging
from uuid import uuid4
from datetime import datetime

from uno.core.errors.result import Result
from uno.domain.service import UnoEntityService
from uno.workflows.entities import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
    WorkflowExecutionRecord,
    User,
)
from uno.workflows.domain_repositories import (
    WorkflowDefRepository,
    WorkflowTriggerRepository,
    WorkflowConditionRepository,
    WorkflowActionRepository,
    WorkflowRecipientRepository,
    WorkflowExecutionRepository,
)
from uno.workflows.errors import (
    WorkflowNotFoundError,
    WorkflowExecutionError,
    WorkflowActionError,
)
from uno.workflows.models import (
    WorkflowStatus,
    WorkflowExecutionStatus,
)


class WorkflowServiceError(Exception):
    """Base error class for workflow service errors."""

    pass


class WorkflowDefService(UnoEntityService[WorkflowDef]):
    """Service for workflow definition entities."""

    def __init__(
        self,
        repository: Optional[WorkflowDefRepository] = None,
        trigger_repository: Optional[WorkflowTriggerRepository] = None,
        condition_repository: Optional[WorkflowConditionRepository] = None,
        action_repository: Optional[WorkflowActionRepository] = None,
        recipient_repository: Optional[WorkflowRecipientRepository] = None,
        execution_repository: Optional[WorkflowExecutionRepository] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the workflow definition service.

        Args:
            repository: The repository for workflow definitions
            trigger_repository: The repository for workflow triggers
            condition_repository: The repository for workflow conditions
            action_repository: The repository for workflow actions
            recipient_repository: The repository for workflow recipients
            execution_repository: The repository for workflow execution records
            logger: Optional logger
        """
        if repository is None:
            repository = WorkflowDefRepository()

        super().__init__(WorkflowDef, repository, logger or logging.getLogger(__name__))

        self.trigger_repository = trigger_repository
        self.condition_repository = condition_repository
        self.action_repository = action_repository
        self.recipient_repository = recipient_repository
        self.execution_repository = execution_repository

    async def create_workflow(
        self,
        name: str,
        description: str,
        status: WorkflowStatus = WorkflowStatus.DRAFT,
        version: str = "1.0.0",
    ) -> Result[WorkflowDef]:
        """
        Create a new workflow definition.

        Args:
            name: The name of the workflow
            description: The description of the workflow
            status: The initial status of the workflow
            version: The version of the workflow

        Returns:
            Result containing the created workflow
        """
        try:
            repository = cast(WorkflowDefRepository, self.repository)
            result = await repository.create_workflow(
                name=name, description=description, status=status, version=version
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating workflow: {e}")
            return Failure(WorkflowServiceError(f"Error creating workflow: {str(e)}"))

    async def find_active_workflows(self) -> Result[list[WorkflowDef]]:
        """
        Find all active workflows.

        Returns:
            Result containing active workflows
        """
        try:
            repository = cast(WorkflowDefRepository, self.repository)
            return await repository.find_active_workflows()
        except Exception as e:
            self.logger.error(f"Error finding active workflows: {e}")
            return Failure(
                WorkflowServiceError(f"Error finding active workflows: {str(e)}")
            )

    async def get_workflow_with_relationships(
        self, workflow_id: str
    ) -> Result[WorkflowDef]:
        """
        Get a workflow with all its relationships loaded.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the workflow with relationships
        """
        try:
            repository = cast(WorkflowDefRepository, self.repository)
            workflow_result = await repository.get_with_relationships(workflow_id)

            if workflow_result.is_failure:
                return workflow_result

            workflow = workflow_result.value

            # Load triggers if repository is available
            if self.trigger_repository:
                triggers_result = await self.trigger_repository.find_by_workflow(
                    workflow_id
                )
                if triggers_result.is_success:
                    workflow.triggers = triggers_result.value

            # Load conditions if repository is available
            if self.condition_repository:
                conditions_result = await self.condition_repository.find_by_workflow(
                    workflow_id
                )
                if conditions_result.is_success:
                    workflow.conditions = conditions_result.value

            # Load actions if repository is available
            if self.action_repository:
                actions_result = await self.action_repository.find_by_workflow(
                    workflow_id
                )
                if actions_result.is_success:
                    workflow.actions = actions_result.value

            # Load recipients if repository is available
            if self.recipient_repository:
                recipients_result = await self.recipient_repository.find_by_workflow(
                    workflow_id
                )
                if recipients_result.is_success:
                    workflow.recipients = recipients_result.value

                    # Group recipients by action_id and attach to actions
                    action_recipients = {}
                    for recipient in workflow.recipients:
                        if recipient.action_id:
                            if recipient.action_id not in action_recipients:
                                action_recipients[recipient.action_id] = []
                            action_recipients[recipient.action_id].append(recipient)

                    # Attach recipients to actions
                    for action in workflow.actions:
                        if action.id in action_recipients:
                            action.recipients = action_recipients[action.id]

            # Load execution logs if repository is available
            if self.execution_repository:
                logs_result = await self.execution_repository.find_by_workflow(
                    workflow_id
                )
                if logs_result.is_success:
                    workflow.logs = logs_result.value

            return Success(workflow)
        except Exception as e:
            self.logger.error(f"Error getting workflow with relationships: {e}")
            return Failure(WorkflowServiceError(f"Error getting workflow: {str(e)}"))

    async def activate_workflow(self, workflow_id: str) -> Result[WorkflowDef]:
        """
        Activate a workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the activated workflow
        """
        try:
            workflow_result = await self.get_by_id(workflow_id)
            if workflow_result.is_failure:
                return workflow_result

            workflow = workflow_result.value
            if not workflow:
                return Failure(
                    WorkflowNotFoundError(f"Workflow {workflow_id} not found")
                )

            # Update status
            workflow.status = WorkflowStatus.ACTIVE

            # Save changes
            update_result = await self.update(workflow)
            return update_result
        except Exception as e:
            self.logger.error(f"Error activating workflow: {e}")
            return Failure(WorkflowServiceError(f"Error activating workflow: {str(e)}"))

    async def deactivate_workflow(self, workflow_id: str) -> Result[WorkflowDef]:
        """
        Deactivate a workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the deactivated workflow
        """
        try:
            workflow_result = await self.get_by_id(workflow_id)
            if workflow_result.is_failure:
                return workflow_result

            workflow = workflow_result.value
            if not workflow:
                return Failure(
                    WorkflowNotFoundError(f"Workflow {workflow_id} not found")
                )

            # Update status
            workflow.status = WorkflowStatus.INACTIVE

            # Save changes
            update_result = await self.update(workflow)
            return update_result
        except Exception as e:
            self.logger.error(f"Error deactivating workflow: {e}")
            return Failure(
                WorkflowServiceError(f"Error deactivating workflow: {str(e)}")
            )


class WorkflowTriggerService(UnoEntityService[WorkflowTrigger]):
    """Service for workflow trigger entities."""

    def __init__(
        self,
        repository: Optional[WorkflowTriggerRepository] = None,
        workflow_service: Optional[WorkflowDefService] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the workflow trigger service.

        Args:
            repository: The repository for workflow triggers
            workflow_service: The service for workflow definitions
            logger: Optional logger
        """
        if repository is None:
            repository = WorkflowTriggerRepository()

        super().__init__(
            WorkflowTrigger, repository, logger or logging.getLogger(__name__)
        )
        self.workflow_service = workflow_service

    async def create_trigger(
        self,
        workflow_id: str,
        entity_type: str,
        operation: str,
        field_conditions: dict[str, Any] = None,
        priority: int = 100,
        is_active: bool = True,
    ) -> Result[WorkflowTrigger]:
        """
        Create a new workflow trigger.

        Args:
            workflow_id: The ID of the workflow
            entity_type: The type of entity that triggers the workflow
            operation: The operation that triggers the workflow
            field_conditions: Optional conditions on fields
            priority: The priority of the trigger
            is_active: Whether the trigger is active

        Returns:
            Result containing the created trigger
        """
        try:
            # Verify workflow exists if service is available
            if self.workflow_service:
                workflow_result = await self.workflow_service.get_by_id(workflow_id)
                if workflow_result.is_failure:
                    return Failure(workflow_result.error)
                if not workflow_result.value:
                    return Failure(
                        WorkflowNotFoundError(f"Workflow {workflow_id} not found")
                    )

            repository = cast(WorkflowTriggerRepository, self.repository)
            result = await repository.create_trigger(
                workflow_id=workflow_id,
                entity_type=entity_type,
                operation=operation,
                field_conditions=field_conditions,
                priority=priority,
                is_active=is_active,
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating workflow trigger: {e}")
            return Failure(WorkflowServiceError(f"Error creating trigger: {str(e)}"))

    async def find_by_workflow(self, workflow_id: str) -> Result[list[WorkflowTrigger]]:
        """
        Find triggers for a specific workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the workflow triggers
        """
        try:
            repository = cast(WorkflowTriggerRepository, self.repository)
            return await repository.find_by_workflow(workflow_id)
        except Exception as e:
            self.logger.error(f"Error finding workflow triggers: {e}")
            return Failure(WorkflowServiceError(f"Error finding triggers: {str(e)}"))


class WorkflowConditionService(UnoEntityService[WorkflowCondition]):
    """Service for workflow condition entities."""

    def __init__(
        self,
        repository: Optional[WorkflowConditionRepository] = None,
        workflow_service: Optional[WorkflowDefService] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the workflow condition service.

        Args:
            repository: The repository for workflow conditions
            workflow_service: The service for workflow definitions
            logger: Optional logger
        """
        if repository is None:
            repository = WorkflowConditionRepository()

        super().__init__(
            WorkflowCondition, repository, logger or logging.getLogger(__name__)
        )
        self.workflow_service = workflow_service

    async def create_condition(
        self,
        workflow_id: str,
        condition_type,
        condition_config: dict[str, Any] = None,
        query_id: str | None = None,
        name: str = "",
        description: str | None = None,
        order: int = 0,
    ) -> Result[WorkflowCondition]:
        """
        Create a new workflow condition.

        Args:
            workflow_id: The ID of the workflow
            condition_type: The type of condition
            condition_config: The configuration for the condition
            query_id: Optional query ID for query match conditions
            name: Optional name for the condition
            description: Optional description
            order: The order of the condition

        Returns:
            Result containing the created condition
        """
        try:
            # Verify workflow exists if service is available
            if self.workflow_service:
                workflow_result = await self.workflow_service.get_by_id(workflow_id)
                if workflow_result.is_failure:
                    return Failure(workflow_result.error)
                if not workflow_result.value:
                    return Failure(
                        WorkflowNotFoundError(f"Workflow {workflow_id} not found")
                    )

            repository = cast(WorkflowConditionRepository, self.repository)
            result = await repository.create_condition(
                workflow_id=workflow_id,
                condition_type=condition_type,
                condition_config=condition_config,
                query_id=query_id,
                name=name,
                description=description,
                order=order,
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating workflow condition: {e}")
            return Failure(WorkflowServiceError(f"Error creating condition: {str(e)}"))

    async def find_by_workflow(
        self, workflow_id: str
    ) -> Result[list[WorkflowCondition]]:
        """
        Find conditions for a specific workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the workflow conditions
        """
        try:
            repository = cast(WorkflowConditionRepository, self.repository)
            return await repository.find_by_workflow(workflow_id)
        except Exception as e:
            self.logger.error(f"Error finding workflow conditions: {e}")
            return Failure(WorkflowServiceError(f"Error finding conditions: {str(e)}"))


class WorkflowActionService(UnoEntityService[WorkflowAction]):
    """Service for workflow action entities."""

    def __init__(
        self,
        repository: Optional[WorkflowActionRepository] = None,
        workflow_service: Optional[WorkflowDefService] = None,
        recipient_service: Optional["WorkflowRecipientService"] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the workflow action service.

        Args:
            repository: The repository for workflow actions
            workflow_service: The service for workflow definitions
            recipient_service: The service for workflow recipients
            logger: Optional logger
        """
        if repository is None:
            repository = WorkflowActionRepository()

        super().__init__(
            WorkflowAction, repository, logger or logging.getLogger(__name__)
        )
        self.workflow_service = workflow_service
        self.recipient_service = recipient_service

    async def create_action(
        self,
        workflow_id: str,
        action_type,
        action_config: dict[str, Any] = None,
        name: str = "",
        description: str | None = None,
        order: int = 0,
        is_active: bool = True,
        retry_policy: dict[str, Any] | None = None,
    ) -> Result[WorkflowAction]:
        """
        Create a new workflow action.

        Args:
            workflow_id: The ID of the workflow
            action_type: The type of action
            action_config: The configuration for the action
            name: Optional name for the action
            description: Optional description
            order: The order of the action
            is_active: Whether the action is active
            retry_policy: Optional retry policy

        Returns:
            Result containing the created action
        """
        try:
            # Verify workflow exists if service is available
            if self.workflow_service:
                workflow_result = await self.workflow_service.get_by_id(workflow_id)
                if workflow_result.is_failure:
                    return Failure(workflow_result.error)
                if not workflow_result.value:
                    return Failure(
                        WorkflowNotFoundError(f"Workflow {workflow_id} not found")
                    )

            repository = cast(WorkflowActionRepository, self.repository)
            result = await repository.create_action(
                workflow_id=workflow_id,
                action_type=action_type,
                action_config=action_config,
                name=name,
                description=description,
                order=order,
                is_active=is_active,
                retry_policy=retry_policy,
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating workflow action: {e}")
            return Failure(WorkflowServiceError(f"Error creating action: {str(e)}"))

    async def find_by_workflow(self, workflow_id: str) -> Result[list[WorkflowAction]]:
        """
        Find actions for a specific workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the workflow actions
        """
        try:
            repository = cast(WorkflowActionRepository, self.repository)
            actions_result = await repository.find_by_workflow(workflow_id)

            if actions_result.is_failure:
                return actions_result

            actions = actions_result.value

            # Load recipients for each action if recipient service is available
            if self.recipient_service:
                for action in actions:
                    recipients_result = await self.recipient_service.find_by_action(
                        action.id
                    )
                    if recipients_result.is_success:
                        action.recipients = recipients_result.value

            return Success(actions)
        except Exception as e:
            self.logger.error(f"Error finding workflow actions: {e}")
            return Failure(WorkflowServiceError(f"Error finding actions: {str(e)}"))

    async def get_with_recipients(self, action_id: str) -> Result[WorkflowAction]:
        """
        Get an action with its recipients loaded.

        Args:
            action_id: The ID of the action

        Returns:
            Result containing the action with recipients
        """
        try:
            action_result = await self.get_by_id(action_id)
            if action_result.is_failure:
                return action_result

            action = action_result.value
            if not action:
                return Failure(WorkflowActionError(f"Action {action_id} not found"))

            # Load recipients if service is available
            if self.recipient_service:
                recipients_result = await self.recipient_service.find_by_action(
                    action_id
                )
                if recipients_result.is_success:
                    action.recipients = recipients_result.value

            return Success(action)
        except Exception as e:
            self.logger.error(f"Error getting action with recipients: {e}")
            return Failure(WorkflowServiceError(f"Error getting action: {str(e)}"))


class WorkflowRecipientService(UnoEntityService[WorkflowRecipient]):
    """Service for workflow recipient entities."""

    def __init__(
        self,
        repository: Optional[WorkflowRecipientRepository] = None,
        workflow_service: Optional[WorkflowDefService] = None,
        action_service: Optional[WorkflowActionService] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the workflow recipient service.

        Args:
            repository: The repository for workflow recipients
            workflow_service: The service for workflow definitions
            action_service: The service for workflow actions
            logger: Optional logger
        """
        if repository is None:
            repository = WorkflowRecipientRepository()

        super().__init__(
            WorkflowRecipient, repository, logger or logging.getLogger(__name__)
        )
        self.workflow_service = workflow_service
        self.action_service = action_service

    async def create_recipient(
        self,
        workflow_id: str,
        recipient_type,
        recipient_id: str,
        name: str | None = None,
        action_id: str | None = None,
        notification_config: dict[str, Any] = None,
    ) -> Result[WorkflowRecipient]:
        """
        Create a new workflow recipient.

        Args:
            workflow_id: The ID of the workflow
            recipient_type: The type of recipient
            recipient_id: The ID of the recipient
            name: Optional name for the recipient
            action_id: Optional action ID if this recipient is for a specific action
            notification_config: Optional notification configuration

        Returns:
            Result containing the created recipient
        """
        try:
            # Verify workflow exists if service is available
            if self.workflow_service:
                workflow_result = await self.workflow_service.get_by_id(workflow_id)
                if workflow_result.is_failure:
                    return Failure(workflow_result.error)
                if not workflow_result.value:
                    return Failure(
                        WorkflowNotFoundError(f"Workflow {workflow_id} not found")
                    )

            # Verify action exists if provided and service is available
            if action_id and self.action_service:
                action_result = await self.action_service.get_by_id(action_id)
                if action_result.is_failure:
                    return Failure(action_result.error)
                if not action_result.value:
                    return Failure(WorkflowActionError(f"Action {action_id} not found"))

            repository = cast(WorkflowRecipientRepository, self.repository)
            result = await repository.create_recipient(
                workflow_id=workflow_id,
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                name=name,
                action_id=action_id,
                notification_config=notification_config,
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating workflow recipient: {e}")
            return Failure(WorkflowServiceError(f"Error creating recipient: {str(e)}"))

    async def find_by_workflow(
        self, workflow_id: str
    ) -> Result[list[WorkflowRecipient]]:
        """
        Find recipients for a specific workflow.

        Args:
            workflow_id: The ID of the workflow

        Returns:
            Result containing the workflow recipients
        """
        try:
            repository = cast(WorkflowRecipientRepository, self.repository)
            return await repository.find_by_workflow(workflow_id)
        except Exception as e:
            self.logger.error(f"Error finding workflow recipients: {e}")
            return Failure(WorkflowServiceError(f"Error finding recipients: {str(e)}"))

    async def find_by_action(self, action_id: str) -> Result[list[WorkflowRecipient]]:
        """
        Find recipients for a specific action.

        Args:
            action_id: The ID of the action

        Returns:
            Result containing the action recipients
        """
        try:
            repository = cast(WorkflowRecipientRepository, self.repository)
            return await repository.find_by_action(action_id)
        except Exception as e:
            self.logger.error(f"Error finding action recipients: {e}")
            return Failure(WorkflowServiceError(f"Error finding recipients: {str(e)}"))


class WorkflowExecutionService(UnoEntityService[WorkflowExecutionRecord]):
    """Service for workflow execution record entities."""

    def __init__(
        self,
        repository: Optional[WorkflowExecutionRepository] = None,
        workflow_service: Optional[WorkflowDefService] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the workflow execution service.

        Args:
            repository: The repository for workflow execution records
            workflow_service: The service for workflow definitions
            logger: Optional logger
        """
        if repository is None:
            repository = WorkflowExecutionRepository()

        super().__init__(
            WorkflowExecutionRecord, repository, logger or logging.getLogger(__name__)
        )
        self.workflow_service = workflow_service

    async def create_execution_record(
        self,
        workflow_id: str,
        trigger_event_id: str,
        status: WorkflowExecutionStatus = WorkflowExecutionStatus.PENDING,
        context: dict[str, Any] | None = None,
    ) -> Result[WorkflowExecutionRecord]:
        """
        Create a new workflow execution record.

        Args:
            workflow_id: The ID of the workflow
            trigger_event_id: The ID of the trigger event
            status: The initial status of the execution
            context: Optional execution context

        Returns:
            Result containing the created execution record
        """
        try:
            # Verify workflow exists if service is available
            if self.workflow_service:
                workflow_result = await self.workflow_service.get_by_id(workflow_id)
                if workflow_result.is_failure:
                    return Failure(workflow_result.error)
                if not workflow_result.value:
                    return Failure(
                        WorkflowNotFoundError(f"Workflow {workflow_id} not found")
                    )

            repository = cast(WorkflowExecutionRepository, self.repository)
            result = await repository.create_execution_record(
                workflow_id=workflow_id,
                trigger_event_id=trigger_event_id,
                status=status,
                executed_at=datetime.now(),
                context=context,
            )
            return result
        except Exception as e:
            self.logger.error(f"Error creating workflow execution record: {e}")
            return Failure(
                WorkflowServiceError(f"Error creating execution record: {str(e)}")
            )

    async def update_execution_status(
        self,
        execution_id: str,
        status: WorkflowExecutionStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
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
            repository = cast(WorkflowExecutionRepository, self.repository)
            return await repository.update_execution_status(
                execution_id=execution_id, status=status, result=result, error=error
            )
        except Exception as e:
            self.logger.error(f"Error updating workflow execution status: {e}")
            return Failure(
                WorkflowServiceError(f"Error updating execution status: {str(e)}")
            )

    async def find_by_workflow(
        self, workflow_id: str, limit: int = 100
    ) -> Result[list[WorkflowExecutionRecord]]:
        """
        Find execution records for a specific workflow.

        Args:
            workflow_id: The ID of the workflow
            limit: Maximum number of records to return

        Returns:
            Result containing the workflow execution records
        """
        try:
            repository = cast(WorkflowExecutionRepository, self.repository)
            return await repository.find_by_workflow(workflow_id, limit)
        except Exception as e:
            self.logger.error(f"Error finding workflow execution records: {e}")
            return Failure(
                WorkflowServiceError(f"Error finding execution records: {str(e)}")
            )
