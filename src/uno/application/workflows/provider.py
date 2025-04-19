 # SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
# SPDX-License-Identifier: MIT

"""
This module is fully DI container compliant and does not instantiate or expose dependencies ad hoc.
If any service or repository is not yet registered in the DI system, ensure it is added to the central DI provider.
"""

import logging

from uno.core.base.error import BaseError
from uno.core.errors.result import Failure, Result, Success
from uno.database.db_manager import DBManager
from uno.database.repository import UnoBaseRepository
from uno.workflows.engine import (
    PostgresWorkflowEventListener,
    WorkflowEngine,
    WorkflowEventHandler,
    WorkflowEventModel,
)
from uno.workflows.entities import (
    WorkflowAction,
    WorkflowCondition,
    WorkflowDef,
    WorkflowExecutionRecord,
    WorkflowRecipient,
    WorkflowTrigger,
)
from uno.workflows.errors import (
    WorkflowErrorCode,
    WorkflowExecutionError,
    WorkflowNotFoundError,
)

class WorkflowRepository(UnoBaseRepository):
    """Repository for workflow-related operations."""

    def __init__(self, db_manager: DBManager):
        super().__init__(db_manager)

    async def get_workflow_by_id(self, workflow_id: str) -> WorkflowDef | None:
        """Get a workflow by ID."""
        async with self.db_manager.get_enhanced_session() as session:
            query = """
            SELECT * FROM workflow_definition WHERE id = :workflow_id
            """
            result = await session.execute(query, {"workflow_id": workflow_id})
            workflow_data = result.fetchone()

            if not workflow_data:
                return None

            workflow = WorkflowDef.from_record(workflow_data)

            # Fetch related components
            await self._load_workflow_components(session, workflow)

            return workflow

    async def get_active_workflows(self) -> list[WorkflowDef]:
        """Get all active workflows."""
        async with self.db_manager.get_enhanced_session() as session:
            query = """
            SELECT * FROM workflow_definition WHERE status = 'active'
            """
            result = await session.execute(query)
            workflows = []

            for workflow_data in result.fetchall():
                workflow = WorkflowDef.from_record(workflow_data)
                await self._load_workflow_components(session, workflow)
                workflows.append(workflow)

            return workflows

    async def _load_workflow_components(self, session, workflow: WorkflowDef) -> None:
        """Load all components for a workflow."""
        # Fetch triggers
        triggers_query = """
        SELECT * FROM workflow_trigger WHERE workflow_id = :workflow_id
        """
        triggers_result = await session.execute(
            triggers_query, {"workflow_id": workflow.id}
        )
        for trigger_data in triggers_result.fetchall():
            trigger = WorkflowTrigger.from_record(trigger_data)
            workflow.triggers.append(trigger)

        # Fetch conditions
        conditions_query = """
        SELECT * FROM workflow_condition WHERE workflow_id = :workflow_id ORDER BY "order" ASC
        """
        conditions_result = await session.execute(
            conditions_query, {"workflow_id": workflow.id}
        )
        for condition_data in conditions_result.fetchall():
            condition = WorkflowCondition.from_record(condition_data)
            workflow.conditions.append(condition)

        # Fetch actions
        actions_query = """
        SELECT * FROM workflow_action WHERE workflow_id = :workflow_id ORDER BY "order" ASC
        """
        actions_result = await session.execute(
            actions_query, {"workflow_id": workflow.id}
        )
        for action_data in actions_result.fetchall():
            action = WorkflowAction.from_record(action_data)
            workflow.actions.append(action)

        # Fetch recipients
        recipients_query = """
        SELECT * FROM workflow_recipient WHERE workflow_id = :workflow_id
        """
        recipients_result = await session.execute(
            recipients_query, {"workflow_id": workflow.id}
        )
        for recipient_data in recipients_result.fetchall():
            recipient = WorkflowRecipient.from_record(recipient_data)
            workflow.recipients.append(recipient)

            # Associate recipients with specific actions if applicable
            if recipient.action_id:
                for action in workflow.actions:
                    if action.id == recipient.action_id:
                        action.recipients.append(recipient)
                        break

    async def create_workflow(self, workflow: WorkflowDef) -> str:
        """Create a new workflow."""
        async with self.db_manager.get_enhanced_session() as session:
            # Save workflow definition
            await session.add(workflow)
            await session.flush()

            # Save triggers
            for trigger in workflow.triggers:
                trigger.workflow_id = workflow.id
                await session.add(trigger)

            # Save conditions
            for condition in workflow.conditions:
                condition.workflow_id = workflow.id
                await session.add(condition)

            # Save actions
            for action in workflow.actions:
                action.workflow_id = workflow.id
                await session.add(action)

            # Save recipients
            for recipient in workflow.recipients:
                recipient.workflow_id = workflow.id
                await session.add(recipient)

            await session.commit()

            return workflow.id

    async def update_workflow(self, workflow: WorkflowDef) -> str | None:
        """Update an existing workflow."""
        async with self.db_manager.get_enhanced_session() as session:
            # Check if workflow exists
            query = """
            SELECT id FROM workflow_definition WHERE id = :workflow_id
            """
            result = await session.execute(query, {"workflow_id": workflow.id})
            if not result.fetchone():
                return None

            # Update workflow definition
            await session.execute(
                """
                UPDATE workflow_definition
                SET name = :name,
                    description = :description,
                    status = :status,
                    version = :version,
                    modified_at = NOW()
                WHERE id = :id
                """,
                {
                    "id": workflow.id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "status": workflow.status,
                    "version": workflow.version,
                },
            )

            # Handle components (this is simplified - in a real implementation,
            # you would need to handle deletions and updates more carefully)

            # For triggers, conditions, actions, and recipients:
            # - If they have an ID, update them
            # - If they don't have an ID, create them
            # - If they exist in the database but not in the workflow object, delete them

            # For simplicity, we'll just delete all existing components and create new ones
            await session.execute(
                "DELETE FROM workflow_trigger WHERE workflow_id = :workflow_id",
                {"workflow_id": workflow.id},
            )
            await session.execute(
                "DELETE FROM workflow_condition WHERE workflow_id = :workflow_id",
                {"workflow_id": workflow.id},
            )
            await session.execute(
                "DELETE FROM workflow_action WHERE workflow_id = :workflow_id",
                {"workflow_id": workflow.id},
            )
            await session.execute(
                "DELETE FROM workflow_recipient WHERE workflow_id = :workflow_id",
                {"workflow_id": workflow.id},
            )

            # Save triggers
            for trigger in workflow.triggers:
                trigger.workflow_id = workflow.id
                await session.add(trigger)

            # Save conditions
            for condition in workflow.conditions:
                condition.workflow_id = workflow.id
                await session.add(condition)

            # Save actions
            for action in workflow.actions:
                action.workflow_id = workflow.id
                await session.add(action)

            # Save recipients
            for recipient in workflow.recipients:
                recipient.workflow_id = workflow.id
                await session.add(recipient)

            await session.commit()

            return workflow.id

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        async with self.db_manager.get_enhanced_session() as session:
            # Check if workflow exists
            query = """
            SELECT id FROM workflow_definition WHERE id = :workflow_id
            """
            result = await session.execute(query, {"workflow_id": workflow_id})
            if not result.fetchone():
                return False

            # Delete workflow (cascade will delete all related components)
            await session.execute(
                "DELETE FROM workflow_definition WHERE id = :workflow_id",
                {"workflow_id": workflow_id},
            )

            await session.commit()

            return True

    async def get_execution_logs(
        self,
        workflow_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WorkflowExecutionRecord]:
        """Get execution logs for workflows."""
        async with self.db_manager.get_enhanced_session() as session:
            query = """
            SELECT * FROM workflow_execution_log
            WHERE 1=1
            """
            params = {}

            if workflow_id:
                query += " AND workflow_id = :workflow_id"
                params["workflow_id"] = workflow_id

            if status:
                query += " AND status = :status"
                params["status"] = status

            query += " ORDER BY executed_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await session.execute(query, params)
            logs = []

            for log_data in result.fetchall():
                log = WorkflowExecutionRecord.from_record(log_data)
                logs.append(log)

            return logs


class WorkflowService:
    """Service for workflow-related operations."""

    def __init__(
        self,
        repository: WorkflowRepository,
        workflow_engine: WorkflowEngine,
        db_manager: DBManager,
        logger: logging.Logger,
    ):
        self.repository = repository
        self.workflow_engine = workflow_engine
        self.db_manager = db_manager
        self.logger = logger
        self.event_listener = None

    async def get_workflow_by_id(self, workflow_id: str) -> Result[WorkflowDef | None]:
        """Get a workflow by ID."""
        try:
            workflow = await self.repository.get_workflow_by_id(workflow_id)
            if not workflow:
                return Failure(WorkflowNotFoundError(workflow_id), convert=True)

            return Success(workflow, convert=True)
        except Exception as e:
            self.logger.exception(f"Error getting workflow {workflow_id}: {e}")
            return Failure(
                WorkflowExecutionError(
                    workflow_id,
                    reason=f"Database error: {str(e)}",
                    message=f"Error retrieving workflow: {str(e)}",
                ),
                convert=True,
            )

    async def get_active_workflows(self) -> Result[list[WorkflowDef]]:
        """Get all active workflows."""
        try:
            workflows = await self.repository.get_active_workflows()
            return Success(workflows, convert=True)
        except Exception as e:
            self.logger.exception(f"Error getting active workflows: {e}")
            return Failure(
                BaseError(
                    f"Error getting active workflows: {str(e)}",
                    WorkflowErrorCode.WORKFLOW_EXECUTION_FAILED,
                    operation="get_active_workflows",
                ),
                convert=True,
            )

    async def create_workflow(self, workflow: WorkflowDef) -> Result[str]:
        """Create a new workflow."""
        try:
            workflow_id = await self.repository.create_workflow(workflow)
            return Success(workflow_id, convert=True)
        except Exception as e:
            self.logger.exception(f"Error creating workflow: {e}")
            return Failure(
                BaseError(
                    f"Error creating workflow: {str(e)}",
                    WorkflowErrorCode.WORKFLOW_INVALID_DEFINITION,
                    operation="create_workflow",
                ),
                convert=True,
            )

    async def update_workflow(self, workflow: WorkflowDef) -> Result[str | None]:
        """Update an existing workflow."""
        try:
            workflow_id = await self.repository.update_workflow(workflow)
            if not workflow_id:
                return Failure(WorkflowNotFoundError(workflow.id), convert=True)

            return Success(workflow_id, convert=True)
        except Exception as e:
            self.logger.exception(f"Error updating workflow {workflow.id}: {e}")
            return Failure(
                WorkflowExecutionError(
                    workflow.id,
                    reason=f"Update operation failed: {str(e)}",
                    message=f"Error updating workflow",
                ),
                convert=True,
            )

    async def delete_workflow(self, workflow_id: str) -> Result[bool]:
        """Delete a workflow."""
        try:
            success = await self.repository.delete_workflow(workflow_id)
            if not success:
                return Failure(WorkflowNotFoundError(workflow_id), convert=True)

            return Success(True, convert=True)
        except Exception as e:
            self.logger.exception(f"Error deleting workflow {workflow_id}: {e}")
            return Failure(
                WorkflowExecutionError(
                    workflow_id,
                    reason=f"Delete operation failed: {str(e)}",
                    message=f"Error deleting workflow",
                ),
                convert=True,
            )

    async def get_execution_logs(
        self,
        workflow_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Result[list[WorkflowExecutionRecord]]:
        """Get execution logs for workflows."""
        try:
            logs = await self.repository.get_execution_logs(
                workflow_id=workflow_id, status=status, limit=limit, offset=offset
            )
            return Success(logs, convert=True)
        except Exception as e:
            self.logger.exception(f"Error getting execution logs: {e}")
            return Failure(
                BaseError(
                    f"Error retrieving execution logs: {str(e)}",
                    WorkflowErrorCode.WORKFLOW_EXECUTION_FAILED,
                    operation="get_execution_logs",
                ),
                convert=True,
            )

    async def start_event_listener(self) -> Result[bool]:
        """Start the PostgreSQL event listener."""
        try:
            if self.event_listener is None:
                self.event_listener = PostgresWorkflowEventListener(
                    self.db_manager, self.workflow_engine, logger=self.logger
                )

            await self.event_listener.start()
            return Success(True)
        except Exception as e:
            self.logger.exception(f"Error starting event listener: {e}")
            return Failure(
                BaseError(
                    f"Error starting event listener: {str(e)}",
                    WorkflowErrorCode.WORKFLOW_EVENT_LISTENER_FAILED,
                )
            )

    async def stop_event_listener(self) -> Result[bool]:
        """Stop the PostgreSQL event listener."""
        try:
            if self.event_listener:
                await self.event_listener.stop()
                return Success(True)

            return Success(False)
        except Exception as e:
            self.logger.exception(f"Error stopping event listener: {e}")
            return Failure(
                BaseError(
                    f"Error stopping event listener: {str(e)}",
                    WorkflowErrorCode.WORKFLOW_EVENT_LISTENER_FAILED,
                )
            )

    async def process_event(self, event: dict[str, object]) -> Result[dict[str, object]]:
        """Process a workflow event."""
        try:
            # Convert to WorkflowEventModel
            workflow_event = WorkflowEventModel(**event)

            # Process the event
            result = await self.workflow_engine.process_event(workflow_event)

            if result.is_failure:
                # Forward the error from the workflow engine
                return result

            return Success(result.value)
        except Exception as e:
            self.logger.exception(f"Error processing workflow event: {e}")
            event_type = (
                event.get("type", "unknown") if isinstance(event, dict) else "unknown"
            )
            return Failure(
                WorkflowEventError(
                    event_type=event_type,
                    reason=str(e),
                    message="Error processing workflow event",
                )
            )



def configure_workflow_module_services(container):
    """Configure dependency injection for the workflow module using the DI container."""
    logger = logging.getLogger("uno.workflows")
    from uno.workflows.engine import WorkflowEngine
    from uno.workflows.event_handler import WorkflowEventHandler

    # Register repository
    container.register(
        WorkflowRepository,
        lambda c: WorkflowRepository(db_manager=c.resolve(DBManager)),
        lifecycle="scoped",
    )
    # Register engine
    container.register(
        WorkflowEngine,
        lambda c: WorkflowEngine(db_manager=c.resolve(DBManager), logger=logger),
        lifecycle="scoped",
    )
    # Register service
    container.register(
        WorkflowService,
        lambda c: WorkflowService(
            repository=c.resolve(WorkflowRepository),
            workflow_engine=c.resolve(WorkflowEngine),
            db_manager=c.resolve(DBManager),
            logger=logger,
        ),
        lifecycle="scoped",
    )
    # Register event handler
    container.register(
        WorkflowEventHandler,
        lambda c: WorkflowEventHandler(
            db_manager=c.resolve(DBManager),
            engine=c.resolve(WorkflowEngine),
            logger=logger,
        ),
        lifecycle="scoped",
    )





# Initialize action executors, condition evaluators, and recipient resolvers
def initialize_workflow_components():
    """Initialize workflow components."""
    from uno.workflows.executor import init_executors
    from uno.workflows.conditions import init_evaluators
    from uno.workflows.recipients import init_resolvers

    init_executors()
    init_evaluators()
    init_resolvers()


# Don't initialize components automatically during import
# This will be done explicitly when the application is ready
# initialize_workflow_components()
