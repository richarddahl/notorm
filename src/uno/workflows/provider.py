# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import logging
from typing import Optional, Callable, List, Dict, Any, Type
import inject
from uno.dependencies.scoped_container import get_service

from uno.dependencies.interfaces import UnoRepositoryProtocol, UnoServiceProtocol
from uno.database.db_manager import DBManager
from uno.database.repository import UnoBaseRepository
from uno.core.errors.result import Result, Success, Failure
from uno.errors import UnoError

from uno.workflows.models import (
    WorkflowDefinition,
    WorkflowTriggerModel,
    WorkflowConditionModel,
    WorkflowActionModel,
    WorkflowRecipientModel,
    WorkflowExecutionLog,
    WorkflowActionType,
    WorkflowConditionType,
    WorkflowRecipientType,
)
from uno.workflows.objs import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
    WorkflowExecutionRecord,
)
from uno.workflows.engine import (
    WorkflowEngine,
    WorkflowEventHandler,
    PostgresWorkflowEventListener,
    WorkflowEventModel,
)


class WorkflowRepository(UnoBaseRepository, UnoRepositoryProtocol):
    """Repository for workflow-related operations."""
    
    @inject.params(db_manager=DBManager)
    def __init__(self, db_manager: DBManager):
        super().__init__(db_manager)
    
    async def get_workflow_by_id(self, workflow_id: str) -> Optional[WorkflowDef]:
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
    
    async def get_active_workflows(self) -> List[WorkflowDef]:
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
        triggers_result = await session.execute(triggers_query, {"workflow_id": workflow.id})
        for trigger_data in triggers_result.fetchall():
            trigger = WorkflowTrigger.from_record(trigger_data)
            workflow.triggers.append(trigger)
        
        # Fetch conditions
        conditions_query = """
        SELECT * FROM workflow_condition WHERE workflow_id = :workflow_id ORDER BY "order" ASC
        """
        conditions_result = await session.execute(conditions_query, {"workflow_id": workflow.id})
        for condition_data in conditions_result.fetchall():
            condition = WorkflowCondition.from_record(condition_data)
            workflow.conditions.append(condition)
        
        # Fetch actions
        actions_query = """
        SELECT * FROM workflow_action WHERE workflow_id = :workflow_id ORDER BY "order" ASC
        """
        actions_result = await session.execute(actions_query, {"workflow_id": workflow.id})
        for action_data in actions_result.fetchall():
            action = WorkflowAction.from_record(action_data)
            workflow.actions.append(action)
        
        # Fetch recipients
        recipients_query = """
        SELECT * FROM workflow_recipient WHERE workflow_id = :workflow_id
        """
        recipients_result = await session.execute(recipients_query, {"workflow_id": workflow.id})
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
    
    async def update_workflow(self, workflow: WorkflowDef) -> Optional[str]:
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
                }
            )
            
            # Handle components (this is simplified - in a real implementation,
            # you would need to handle deletions and updates more carefully)
            
            # For triggers, conditions, actions, and recipients:
            # - If they have an ID, update them
            # - If they don't have an ID, create them
            # - If they exist in the database but not in the workflow object, delete them
            
            # For simplicity, we'll just delete all existing components and create new ones
            await session.execute("DELETE FROM workflow_trigger WHERE workflow_id = :workflow_id", {"workflow_id": workflow.id})
            await session.execute("DELETE FROM workflow_condition WHERE workflow_id = :workflow_id", {"workflow_id": workflow.id})
            await session.execute("DELETE FROM workflow_action WHERE workflow_id = :workflow_id", {"workflow_id": workflow.id})
            await session.execute("DELETE FROM workflow_recipient WHERE workflow_id = :workflow_id", {"workflow_id": workflow.id})
            
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
                {"workflow_id": workflow_id}
            )
            
            await session.commit()
            
            return True
    
    async def get_execution_logs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowExecutionRecord]:
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


class WorkflowService(UnoServiceProtocol):
    """Service for workflow-related operations."""
    
    @inject.params(
        repository=WorkflowRepository,
        workflow_engine=WorkflowEngine,
        db_manager=DBManager,
        logger=logging.Logger
    )
    def __init__(
        self,
        repository: WorkflowRepository,
        workflow_engine: WorkflowEngine,
        db_manager: DBManager,
        logger: Optional[logging.Logger] = None,
    ):
        self.repository = repository
        self.workflow_engine = workflow_engine
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)
        self.event_listener = None
    
    async def get_workflow_by_id(self, workflow_id: str) -> Result[WorkflowDef]:
        """Get a workflow by ID."""
        try:
            workflow = await self.repository.get_workflow_by_id(workflow_id)
            if not workflow:
                return Failure(UnoError(f"Workflow with ID {workflow_id} not found"))
            
            return Success(workflow)
        except Exception as e:
            self.logger.exception(f"Error getting workflow {workflow_id}: {e}")
            return Failure(UnoError(f"Error getting workflow: {str(e)}"))
    
    async def get_active_workflows(self) -> Result[List[WorkflowDef]]:
        """Get all active workflows."""
        try:
            workflows = await self.repository.get_active_workflows()
            return Success(workflows)
        except Exception as e:
            self.logger.exception(f"Error getting active workflows: {e}")
            return Failure(UnoError(f"Error getting active workflows: {str(e)}"))
    
    async def create_workflow(self, workflow: WorkflowDef) -> Result[str]:
        """Create a new workflow."""
        try:
            workflow_id = await self.repository.create_workflow(workflow)
            return Success(workflow_id)
        except Exception as e:
            self.logger.exception(f"Error creating workflow: {e}")
            return Failure(UnoError(f"Error creating workflow: {str(e)}"))
    
    async def update_workflow(self, workflow: WorkflowDef) -> Result[str]:
        """Update an existing workflow."""
        try:
            workflow_id = await self.repository.update_workflow(workflow)
            if not workflow_id:
                return Failure(UnoError(f"Workflow with ID {workflow.id} not found"))
            
            return Success(workflow_id)
        except Exception as e:
            self.logger.exception(f"Error updating workflow {workflow.id}: {e}")
            return Failure(UnoError(f"Error updating workflow: {str(e)}"))
    
    async def delete_workflow(self, workflow_id: str) -> Result[bool]:
        """Delete a workflow."""
        try:
            success = await self.repository.delete_workflow(workflow_id)
            if not success:
                return Failure(UnoError(f"Workflow with ID {workflow_id} not found"))
            
            return Success(True)
        except Exception as e:
            self.logger.exception(f"Error deleting workflow {workflow_id}: {e}")
            return Failure(UnoError(f"Error deleting workflow: {str(e)}"))
    
    async def get_execution_logs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Result[List[WorkflowExecutionRecord]]:
        """Get execution logs for workflows."""
        try:
            logs = await self.repository.get_execution_logs(
                workflow_id=workflow_id,
                status=status,
                limit=limit,
                offset=offset
            )
            return Success(logs)
        except Exception as e:
            self.logger.exception(f"Error getting execution logs: {e}")
            return Failure(UnoError(f"Error getting execution logs: {str(e)}"))
    
    async def start_event_listener(self) -> Result[bool]:
        """Start the PostgreSQL event listener."""
        try:
            if self.event_listener is None:
                self.event_listener = PostgresWorkflowEventListener(
                    self.db_manager,
                    self.workflow_engine,
                    logger=self.logger
                )
            
            await self.event_listener.start()
            return Success(True)
        except Exception as e:
            self.logger.exception(f"Error starting event listener: {e}")
            return Failure(UnoError(f"Error starting event listener: {str(e)}"))
    
    async def stop_event_listener(self) -> Result[bool]:
        """Stop the PostgreSQL event listener."""
        try:
            if self.event_listener:
                await self.event_listener.stop()
                return Success(True)
            
            return Success(False)
        except Exception as e:
            self.logger.exception(f"Error stopping event listener: {e}")
            return Failure(UnoError(f"Error stopping event listener: {str(e)}"))
    
    async def process_event(self, event: Dict[str, Any]) -> Result[Dict[str, Any]]:
        """Process a workflow event."""
        try:
            # Convert to WorkflowEventModel
            workflow_event = WorkflowEventModel(**event)
            
            # Process the event
            result = await self.workflow_engine.process_event(workflow_event)
            
            if result.is_failure:
                return Failure(UnoError(f"Error processing workflow event: {result.error}"))
            
            return Success(result.value)
        except Exception as e:
            self.logger.exception(f"Error processing workflow event: {e}")
            return Failure(UnoError(f"Error processing workflow event: {str(e)}"))


def configure_workflow_module(binder):
    """Configure dependency injection for the workflow module."""
    # Create and bind workflow engine
    db_manager = get_service(DBManager)
    logger = get_service(logging.Logger)
    
    workflow_engine = WorkflowEngine(db_manager, logger)
    binder.bind(WorkflowEngine, workflow_engine)
    
    # Create and bind workflow repository
    binder.bind(WorkflowRepository, WorkflowRepository(db_manager))
    
    # Create and bind workflow service
    binder.bind(
        WorkflowService,
        WorkflowService(
            get_service(WorkflowRepository),
            workflow_engine,
            db_manager,
            logger
        )
    )
    
    # Create and bind workflow event handler
    event_handler = WorkflowEventHandler(
        db_manager,
        workflow_engine,
        logger
    )
    binder.bind(WorkflowEventHandler, event_handler)