# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import logging
import json
import inspect
import asyncio
from typing import Dict, Any, List, Optional, Callable, Set, Union, Type, Tuple
from datetime import datetime

from pydantic import BaseModel

from uno.core.errors.result import Result, Ok, Err
from uno.domain.events import DomainEvent, EventHandler
from uno.errors import UnoError
from uno.settings import uno_settings
from uno.dependencies.interfaces import UnoRepositoryProtocol
from uno.database.db_manager import DBManager
from uno.authorization.objs import User, Group, Role

from uno.workflows.models import (
    WorkflowDefinition,
    WorkflowExecutionStatus,
    WorkflowDBEvent,
    WorkflowTriggerModel,
    WorkflowConditionModel,
    WorkflowConditionType,
    WorkflowActionType,
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


class WorkflowError(UnoError):
    """Base error class for workflow module errors."""
    pass


class WorkflowNotFoundError(WorkflowError):
    """Error raised when a workflow is not found."""
    pass


class WorkflowConditionError(WorkflowError):
    """Error raised when there's an issue evaluating workflow conditions."""
    pass


class WorkflowActionError(WorkflowError):
    """Error raised when there's an issue executing workflow actions."""
    pass


class WorkflowEventModel(BaseModel):
    """Model representing a database event that could trigger workflows."""
    table_name: str
    schema_name: str
    operation: WorkflowDBEvent
    timestamp: float
    payload: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class WorkflowEngine:
    """Core workflow engine responsible for executing workflows based on events."""
    
    def __init__(
        self,
        db_manager: DBManager,
        logger: Optional[logging.Logger] = None,
    ):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)
        self._condition_handlers: Dict[WorkflowConditionType, Callable] = {}
        self._action_handlers: Dict[WorkflowActionType, Callable] = {}
        self._recipient_resolvers: Dict[WorkflowRecipientType, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register the default condition, action, and recipient handlers."""
        # Register condition handlers
        self.register_condition_handler(
            WorkflowConditionType.FIELD_VALUE,
            self._handle_field_value_condition
        )
        self.register_condition_handler(
            WorkflowConditionType.TIME_BASED,
            self._handle_time_based_condition
        )
        self.register_condition_handler(
            WorkflowConditionType.ROLE_BASED,
            self._handle_role_based_condition
        )
        
        # Register action handlers
        self.register_action_handler(
            WorkflowActionType.NOTIFICATION,
            self._handle_notification_action
        )
        self.register_action_handler(
            WorkflowActionType.EMAIL,
            self._handle_email_action
        )
        self.register_action_handler(
            WorkflowActionType.WEBHOOK,
            self._handle_webhook_action
        )
        
        # Register recipient resolvers
        self.register_recipient_resolver(
            WorkflowRecipientType.USER,
            self._resolve_user_recipient
        )
        self.register_recipient_resolver(
            WorkflowRecipientType.ROLE,
            self._resolve_role_recipient
        )
        self.register_recipient_resolver(
            WorkflowRecipientType.GROUP,
            self._resolve_group_recipient
        )
    
    def register_condition_handler(
        self,
        condition_type: WorkflowConditionType,
        handler: Callable[[WorkflowCondition, WorkflowEventModel, Dict[str, Any]], Result[bool, WorkflowError]]
    ) -> None:
        """Register a handler for a specific condition type."""
        self._condition_handlers[condition_type] = handler
    
    def register_action_handler(
        self,
        action_type: WorkflowActionType,
        handler: Callable[[WorkflowAction, WorkflowEventModel, Dict[str, Any], List[User]], Result[Dict[str, Any], WorkflowError]]
    ) -> None:
        """Register a handler for a specific action type."""
        self._action_handlers[action_type] = handler
    
    def register_recipient_resolver(
        self,
        recipient_type: WorkflowRecipientType,
        resolver: Callable[[WorkflowRecipient, Dict[str, Any]], Result[List[User], WorkflowError]]
    ) -> None:
        """Register a resolver for a specific recipient type."""
        self._recipient_resolvers[recipient_type] = resolver
    
    async def process_event(self, event: WorkflowEventModel) -> Result[Dict[str, Any], WorkflowError]:
        """Process a database event and execute matching workflows."""
        self.logger.debug(f"Processing event: {event.table_name} {event.operation}")
        
        try:
            # Find matching workflows based on triggers
            matching_workflows = await self._find_matching_workflows(event)
            
            if not matching_workflows:
                self.logger.debug(f"No matching workflows found for {event.table_name} {event.operation}")
                return Ok({"status": "no_matches", "message": "No matching workflows found"})
            
            results = []
            
            # Execute each matching workflow
            for workflow_def, trigger in matching_workflows:
                workflow_result = await self._execute_workflow(workflow_def, trigger, event)
                results.append({
                    "workflow_id": workflow_def.id,
                    "workflow_name": workflow_def.name,
                    "status": (
                        workflow_result.unwrap().get("status")
                        if workflow_result.is_ok()
                        else "error"
                    ),
                    "message": (
                        workflow_result.unwrap().get("message")
                        if workflow_result.is_ok()
                        else str(workflow_result.unwrap_err())
                    ),
                })
            
            return Ok({
                "status": "processed",
                "count": len(results),
                "results": results
            })
            
        except Exception as e:
            self.logger.exception(f"Error processing event: {e}")
            return Err(WorkflowError(f"Error processing event: {str(e)}"))
    
    async def _find_matching_workflows(
        self,
        event: WorkflowEventModel
    ) -> List[Tuple[WorkflowDef, WorkflowTrigger]]:
        """Find workflows with triggers matching the given event."""
        async with self.db_manager.get_enhanced_session() as session:
            # Query for active workflows with matching triggers
            query = """
            SELECT 
                wd.id as workflow_id,
                wt.id as trigger_id
            FROM 
                workflow_definition wd
                JOIN workflow_trigger wt ON wd.id = wt.workflow_id
            WHERE 
                wd.status = 'active'
                AND wt.is_active = TRUE
                AND wt.entity_type = :entity_type
                AND wt.operation = :operation
            ORDER BY 
                wt.priority ASC
            """
            
            params = {
                "entity_type": event.table_name,
                "operation": event.operation,
            }
            
            result = await session.execute(query, params)
            matches = result.fetchall()
            
            if not matches:
                return []
            
            # Fetch complete workflow and trigger objects
            workflows_with_triggers = []
            
            for match in matches:
                workflow_id = match["workflow_id"]
                trigger_id = match["trigger_id"]
                
                # Fetch workflow with its components
                workflow = await self._get_workflow_with_components(session, workflow_id)
                
                # Find the matching trigger
                matching_trigger = next(
                    (t for t in workflow.triggers if t.id == trigger_id),
                    None
                )
                
                if matching_trigger and self._check_field_conditions(matching_trigger, event):
                    workflows_with_triggers.append((workflow, matching_trigger))
            
            return workflows_with_triggers
    
    def _check_field_conditions(self, trigger: WorkflowTrigger, event: WorkflowEventModel) -> bool:
        """Check if the event payload matches the trigger's field conditions."""
        if not trigger.field_conditions:
            return True
        
        payload = event.payload
        if event.operation == WorkflowDBEvent.UPDATE:
            # For updates, check against the new values
            payload = payload.get("new", payload)
        
        # Check each condition
        for field, condition in trigger.field_conditions.items():
            if field not in payload:
                return False
            
            field_value = payload[field]
            
            if isinstance(condition, dict):
                # Complex condition with operator
                operator = condition.get("operator", "eq")
                value = condition.get("value")
                
                if operator == "eq" and field_value != value:
                    return False
                elif operator == "neq" and field_value == value:
                    return False
                elif operator == "gt" and not (field_value > value):
                    return False
                elif operator == "gte" and not (field_value >= value):
                    return False
                elif operator == "lt" and not (field_value < value):
                    return False
                elif operator == "lte" and not (field_value <= value):
                    return False
                elif operator == "in" and field_value not in value:
                    return False
                elif operator == "nin" and field_value in value:
                    return False
            else:
                # Simple equality condition
                if field_value != condition:
                    return False
        
        return True
    
    async def _get_workflow_with_components(
        self,
        session,
        workflow_id: str
    ) -> WorkflowDef:
        """Fetch a workflow with all its components."""
        # Fetch the workflow definition
        workflow_query = """
        SELECT * FROM workflow_definition WHERE id = :workflow_id
        """
        workflow_result = await session.execute(workflow_query, {"workflow_id": workflow_id})
        workflow_data = workflow_result.fetchone()
        
        if not workflow_data:
            raise WorkflowNotFoundError(f"Workflow with ID {workflow_id} not found")
        
        # Create workflow object
        workflow = WorkflowDef.from_record(workflow_data)
        
        # Fetch triggers
        triggers_query = """
        SELECT * FROM workflow_trigger WHERE workflow_id = :workflow_id
        """
        triggers_result = await session.execute(triggers_query, {"workflow_id": workflow_id})
        for trigger_data in triggers_result.fetchall():
            trigger = WorkflowTrigger.from_record(trigger_data)
            workflow.triggers.append(trigger)
        
        # Fetch conditions
        conditions_query = """
        SELECT * FROM workflow_condition WHERE workflow_id = :workflow_id ORDER BY "order" ASC
        """
        conditions_result = await session.execute(conditions_query, {"workflow_id": workflow_id})
        for condition_data in conditions_result.fetchall():
            condition = WorkflowCondition.from_record(condition_data)
            workflow.conditions.append(condition)
        
        # Fetch actions
        actions_query = """
        SELECT * FROM workflow_action WHERE workflow_id = :workflow_id ORDER BY "order" ASC
        """
        actions_result = await session.execute(actions_query, {"workflow_id": workflow_id})
        for action_data in actions_result.fetchall():
            action = WorkflowAction.from_record(action_data)
            workflow.actions.append(action)
        
        # Fetch recipients
        recipients_query = """
        SELECT * FROM workflow_recipient WHERE workflow_id = :workflow_id
        """
        recipients_result = await session.execute(recipients_query, {"workflow_id": workflow_id})
        for recipient_data in recipients_result.fetchall():
            recipient = WorkflowRecipient.from_record(recipient_data)
            workflow.recipients.append(recipient)
            
            # Associate recipients with specific actions if applicable
            if recipient.action_id:
                for action in workflow.actions:
                    if action.id == recipient.action_id:
                        action.recipients.append(recipient)
                        break
        
        return workflow
    
    async def _execute_workflow(
        self,
        workflow: WorkflowDef,
        trigger: WorkflowTrigger,
        event: WorkflowEventModel
    ) -> Result[Dict[str, Any], WorkflowError]:
        """Execute a workflow based on an event."""
        self.logger.info(f"Executing workflow '{workflow.name}' (ID: {workflow.id}) for event {event.table_name} {event.operation}")
        
        # Create execution record
        execution_record = await self._create_execution_record(workflow.id, event)
        execution_context = {
            "workflow_id": workflow.id,
            "trigger_id": trigger.id,
            "event": event.dict(),
            "execution_id": execution_record.id,
            "start_time": datetime.utcnow().isoformat(),
        }
        
        try:
            start_time = datetime.utcnow()
            
            # Check if conditions are met
            conditions_result = await self._evaluate_conditions(workflow, event, execution_context)
            if conditions_result.is_err():
                error = conditions_result.unwrap_err()
                await self._update_execution_record(
                    execution_record.id,
                    WorkflowExecutionStatus.FAILURE,
                    {"error": str(error)},
                    str(error)
                )
                return Err(error)
            
            if not conditions_result.unwrap():
                await self._update_execution_record(
                    execution_record.id,
                    WorkflowExecutionStatus.SUCCESS,
                    {"message": "Conditions not met, workflow skipped"},
                    None
                )
                return Ok({
                    "status": "skipped",
                    "message": "Conditions not met",
                    "execution_id": execution_record.id
                })
            
            # Execute actions
            actions_result = await self._execute_actions(workflow, event, execution_context)
            if actions_result.is_err():
                error = actions_result.unwrap_err()
                await self._update_execution_record(
                    execution_record.id,
                    WorkflowExecutionStatus.FAILURE,
                    {"error": str(error)},
                    str(error)
                )
                return Err(error)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000  # in milliseconds
            
            # Update execution record
            action_results = actions_result.unwrap()
            await self._update_execution_record(
                execution_record.id,
                WorkflowExecutionStatus.SUCCESS,
                {"actions": action_results},
                None,
                execution_time
            )
            
            return Ok({
                "status": "success",
                "message": f"Workflow '{workflow.name}' executed successfully",
                "execution_id": execution_record.id,
                "actions": len(action_results),
                "execution_time_ms": execution_time
            })
            
        except Exception as e:
            self.logger.exception(f"Error executing workflow {workflow.id}: {e}")
            
            # Update execution record
            await self._update_execution_record(
                execution_record.id,
                WorkflowExecutionStatus.FAILURE,
                {"error": str(e)},
                str(e)
            )
            
            return Err(WorkflowError(f"Error executing workflow: {str(e)}"))
    
    async def _create_execution_record(
        self,
        workflow_id: str,
        event: WorkflowEventModel
    ) -> WorkflowExecutionRecord:
        """Create an execution record for a workflow run."""
        async with self.db_manager.get_enhanced_session() as session:
            execution_record = WorkflowExecutionRecord(
                workflow_id=workflow_id,
                trigger_event_id=str(event.timestamp),
                status=WorkflowExecutionStatus.PENDING,
                context=event.dict(),
            )
            
            # Save the execution record
            await session.add(execution_record)
            await session.flush()
            
            return execution_record
    
    async def _update_execution_record(
        self,
        execution_id: str,
        status: WorkflowExecutionStatus,
        result: Dict[str, Any],
        error: Optional[str] = None,
        execution_time: Optional[float] = None
    ) -> None:
        """Update an execution record with results."""
        async with self.db_manager.get_enhanced_session() as session:
            update_data = {
                "status": status,
                "completed_at": datetime.utcnow(),
                "result": result,
            }
            
            if error:
                update_data["error"] = error
                
            if execution_time is not None:
                update_data["execution_time"] = execution_time
            
            # Update the execution record
            await session.execute(
                """
                UPDATE workflow_execution_log 
                SET status = :status, 
                    completed_at = :completed_at, 
                    result = :result,
                    error = :error,
                    execution_time = :execution_time
                WHERE id = :id
                """,
                {
                    "id": execution_id,
                    "status": status,
                    "completed_at": datetime.utcnow(),
                    "result": json.dumps(result),
                    "error": error,
                    "execution_time": execution_time,
                }
            )
    
    async def _evaluate_conditions(
        self,
        workflow: WorkflowDef,
        event: WorkflowEventModel,
        context: Dict[str, Any]
    ) -> Result[bool, WorkflowError]:
        """Evaluate all conditions for a workflow."""
        if not workflow.conditions:
            return Ok(True)  # No conditions means the workflow should execute
        
        for condition in workflow.conditions:
            handler = self._condition_handlers.get(condition.condition_type)
            if not handler:
                self.logger.warning(f"No handler registered for condition type: {condition.condition_type}")
                continue
            
            result = handler(condition, event, context)
            if result.is_err():
                return result
            
            if not result.unwrap():
                # If any condition fails, the workflow should not execute
                self.logger.info(f"Condition {condition.id} ({condition.name or condition.condition_type}) not met")
                return Ok(False)
        
        return Ok(True)
    
    async def _execute_actions(
        self,
        workflow: WorkflowDef,
        event: WorkflowEventModel,
        context: Dict[str, Any]
    ) -> Result[List[Dict[str, Any]], WorkflowError]:
        """Execute all actions for a workflow."""
        if not workflow.actions:
            return Ok([])  # No actions to execute
        
        results = []
        
        for action in workflow.actions:
            if not action.is_active:
                continue
                
            handler = self._action_handlers.get(action.action_type)
            if not handler:
                self.logger.warning(f"No handler registered for action type: {action.action_type}")
                continue
            
            # Resolve recipients for this action
            recipients_result = await self._resolve_recipients(action, workflow, context)
            if recipients_result.is_err():
                self.logger.warning(f"Failed to resolve recipients for action {action.id}: {recipients_result.unwrap_err()}")
                recipients = []
            else:
                recipients = recipients_result.unwrap()
            
            # Execute the action
            action_result = handler(action, event, context, recipients)
            
            if action_result.is_err():
                self.logger.warning(f"Action {action.id} ({action.name or action.action_type}) failed: {action_result.unwrap_err()}")
                # Continue with next action even if this one failed
                results.append({
                    "action_id": action.id,
                    "action_type": action.action_type.value,
                    "status": "error",
                    "error": str(action_result.unwrap_err())
                })
            else:
                results.append({
                    "action_id": action.id,
                    "action_type": action.action_type.value,
                    "status": "success",
                    "result": action_result.unwrap()
                })
        
        return Ok(results)
    
    async def _resolve_recipients(
        self,
        action: WorkflowAction,
        workflow: WorkflowDef,
        context: Dict[str, Any]
    ) -> Result[List[User], WorkflowError]:
        """Resolve all recipients for an action."""
        recipients = []
        
        # First, get action-specific recipients
        for recipient in action.recipients:
            resolver = self._recipient_resolvers.get(recipient.recipient_type)
            if not resolver:
                self.logger.warning(f"No resolver for recipient type: {recipient.recipient_type}")
                continue
                
            result = resolver(recipient, context)
            if result.is_err():
                self.logger.warning(f"Failed to resolve recipient {recipient.id}: {result.unwrap_err()}")
                continue
                
            recipients.extend(result.unwrap())
        
        # If no action-specific recipients, get workflow-level recipients
        if not recipients:
            for recipient in workflow.recipients:
                if recipient.action_id and recipient.action_id != action.id:
                    continue  # Skip recipients that are specific to other actions
                    
                resolver = self._recipient_resolvers.get(recipient.recipient_type)
                if not resolver:
                    self.logger.warning(f"No resolver for recipient type: {recipient.recipient_type}")
                    continue
                    
                result = resolver(recipient, context)
                if result.is_err():
                    self.logger.warning(f"Failed to resolve recipient {recipient.id}: {result.unwrap_err()}")
                    continue
                    
                recipients.extend(result.unwrap())
        
        # Deduplicate recipients by ID
        unique_recipients = {}
        for recipient in recipients:
            unique_recipients[recipient.id] = recipient
            
        return Ok(list(unique_recipients.values()))

    # ===== Default condition handlers =====
    
    def _handle_field_value_condition(
        self,
        condition: WorkflowCondition,
        event: WorkflowEventModel,
        context: Dict[str, Any]
    ) -> Result[bool, WorkflowError]:
        """Handle a field value condition."""
        try:
            config = condition.condition_config
            if not config or not config.get("field"):
                return Err(WorkflowConditionError("Field value condition missing field configuration"))
            
            field = config["field"]
            operator = config.get("operator", "eq")
            expected_value = config.get("value")
            
            payload = event.payload
            if event.operation == WorkflowDBEvent.UPDATE:
                # For updates, check against the new values
                payload = payload.get("new", payload)
            
            # Check if the field exists
            if field not in payload:
                return Ok(False)
            
            actual_value = payload[field]
            
            # Perform the comparison based on the operator
            if operator == "eq":
                return Ok(actual_value == expected_value)
            elif operator == "neq":
                return Ok(actual_value != expected_value)
            elif operator == "gt":
                return Ok(actual_value > expected_value)
            elif operator == "gte":
                return Ok(actual_value >= expected_value)
            elif operator == "lt":
                return Ok(actual_value < expected_value)
            elif operator == "lte":
                return Ok(actual_value <= expected_value)
            elif operator == "in":
                return Ok(actual_value in expected_value)
            elif operator == "nin":
                return Ok(actual_value not in expected_value)
            elif operator == "contains":
                return Ok(expected_value in actual_value)
            elif operator == "startswith":
                return Ok(str(actual_value).startswith(str(expected_value)))
            elif operator == "endswith":
                return Ok(str(actual_value).endswith(str(expected_value)))
            else:
                return Err(WorkflowConditionError(f"Unsupported operator: {operator}"))
                
        except Exception as e:
            return Err(WorkflowConditionError(f"Error evaluating field value condition: {str(e)}"))
    
    def _handle_time_based_condition(
        self,
        condition: WorkflowCondition,
        event: WorkflowEventModel,
        context: Dict[str, Any]
    ) -> Result[bool, WorkflowError]:
        """Handle a time-based condition."""
        # This is a placeholder implementation
        # In a real implementation, you would check time constraints
        return Ok(True)
    
    def _handle_role_based_condition(
        self,
        condition: WorkflowCondition,
        event: WorkflowEventModel,
        context: Dict[str, Any]
    ) -> Result[bool, WorkflowError]:
        """Handle a role-based condition."""
        # This is a placeholder implementation
        # In a real implementation, you would check user roles
        return Ok(True)
    
    # ===== Default action handlers =====
    
    def _handle_notification_action(
        self,
        action: WorkflowAction,
        event: WorkflowEventModel,
        context: Dict[str, Any],
        recipients: List[User]
    ) -> Result[Dict[str, Any], WorkflowError]:
        """Handle a notification action."""
        try:
            config = action.action_config
            title = config.get("title", f"Notification from {action.workflow.name if action.workflow else 'workflow'}")
            message = config.get("message", "A workflow has been triggered")
            
            # This is a placeholder - in a real implementation,
            # you would send notifications via your notification system
            self.logger.info(f"Notification sent: {title} - {message}")
            self.logger.info(f"Recipients: {', '.join([r.username for r in recipients])}")
            
            return Ok({
                "title": title,
                "message": message,
                "recipient_count": len(recipients)
            })
            
        except Exception as e:
            return Err(WorkflowActionError(f"Error executing notification action: {str(e)}"))
    
    def _handle_email_action(
        self,
        action: WorkflowAction,
        event: WorkflowEventModel,
        context: Dict[str, Any],
        recipients: List[User]
    ) -> Result[Dict[str, Any], WorkflowError]:
        """Handle an email action."""
        # This is a placeholder implementation
        return Ok({"sent": len(recipients)})
    
    def _handle_webhook_action(
        self,
        action: WorkflowAction,
        event: WorkflowEventModel,
        context: Dict[str, Any],
        recipients: List[User]
    ) -> Result[Dict[str, Any], WorkflowError]:
        """Handle a webhook action."""
        # This is a placeholder implementation
        return Ok({"status": "sent"})
    
    # ===== Default recipient resolvers =====
    
    def _resolve_user_recipient(
        self,
        recipient: WorkflowRecipient,
        context: Dict[str, Any]
    ) -> Result[List[User], WorkflowError]:
        """Resolve a user recipient."""
        # This is a placeholder implementation
        # In a real implementation, you would fetch the user from the database
        user = User(
            id=recipient.recipient_id,
            username=f"user_{recipient.recipient_id}",
            email=f"user_{recipient.recipient_id}@example.com",
            is_active=True
        )
        return Ok([user])
    
    def _resolve_role_recipient(
        self,
        recipient: WorkflowRecipient,
        context: Dict[str, Any]
    ) -> Result[List[User], WorkflowError]:
        """Resolve a role recipient."""
        # This is a placeholder implementation
        # In a real implementation, you would fetch all users with this role
        return Ok([])
    
    def _resolve_group_recipient(
        self,
        recipient: WorkflowRecipient,
        context: Dict[str, Any]
    ) -> Result[List[User], WorkflowError]:
        """Resolve a group recipient."""
        # This is a placeholder implementation
        # In a real implementation, you would fetch all users in this group
        return Ok([])


class WorkflowEventHandler(EventHandler):
    """Event handler for domain events that can trigger workflows."""
    
    def __init__(
        self,
        db_manager: DBManager,
        workflow_engine: WorkflowEngine,
        logger: Optional[logging.Logger] = None,
    ):
        self.db_manager = db_manager
        self.workflow_engine = workflow_engine
        self.logger = logger or logging.getLogger(__name__)
    
    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event by finding and executing matching workflows."""
        self.logger.debug(f"Handling domain event: {event.__class__.__name__}")
        
        # Convert domain event to workflow event
        workflow_event = self._convert_domain_event_to_workflow_event(event)
        
        # Process the event
        result = await self.workflow_engine.process_event(workflow_event)
        
        if result.is_err():
            self.logger.error(f"Error processing workflow event: {result.unwrap_err()}")
        else:
            response = result.unwrap()
            self.logger.debug(f"Workflow processing result: {response}")
    
    def _convert_domain_event_to_workflow_event(self, event: DomainEvent) -> WorkflowEventModel:
        """Convert a domain event to a workflow event."""
        # Extract event metadata
        event_data = event.to_dict() if hasattr(event, "to_dict") else vars(event)
        
        # Determine operation type based on event class name
        operation = WorkflowDBEvent.INSERT
        if "Updated" in event.__class__.__name__:
            operation = WorkflowDBEvent.UPDATE
        elif "Deleted" in event.__class__.__name__:
            operation = WorkflowDBEvent.DELETE
        
        # Extract entity type from event class name
        # This is a simplistic approach - in a real implementation,
        # you might have a more sophisticated mapping
        entity_parts = event.__class__.__name__.replace("Event", "").split(".")
        entity_type = entity_parts[-1].lower()
        
        # Remove operation words from entity type
        for op in ["created", "updated", "deleted", "insert", "update", "delete"]:
            entity_type = entity_type.replace(op, "").strip()
        
        return WorkflowEventModel(
            table_name=entity_type,
            schema_name=uno_settings.DB_SCHEMA,
            operation=operation,
            timestamp=event.timestamp if hasattr(event, "timestamp") else datetime.utcnow().timestamp(),
            payload=event_data,
            context={
                "event_id": getattr(event, "id", None),
                "event_type": event.__class__.__name__,
                "aggregate_id": getattr(event, "aggregate_id", None),
            }
        )


class PostgresWorkflowEventListener:
    """Listener for database events that can trigger workflows."""
    
    def __init__(
        self,
        db_manager: DBManager,
        workflow_engine: WorkflowEngine,
        channel: str = "workflow_events",
        logger: Optional[logging.Logger] = None,
    ):
        self.db_manager = db_manager
        self.workflow_engine = workflow_engine
        self.channel = channel
        self.logger = logger or logging.getLogger(__name__)
        self._stop_requested = False
        self._listener_task = None
    
    async def start(self) -> None:
        """Start listening for database events."""
        self.logger.info(f"Starting PostgreSQL workflow event listener on channel '{self.channel}'")
        self._stop_requested = False
        self._listener_task = asyncio.create_task(self._listen_for_events())
    
    async def stop(self) -> None:
        """Stop listening for database events."""
        self.logger.info("Stopping PostgreSQL workflow event listener")
        self._stop_requested = True
        if self._listener_task:
            try:
                self._listener_task.cancel()
                await self._listener_task
            except asyncio.CancelledError:
                pass
            finally:
                self._listener_task = None
    
    async def _listen_for_events(self) -> None:
        """Listen for database events on the specified channel."""
        async with self.db_manager.get_enhanced_session() as session:
            conn = await session.connection()
            
            try:
                # Listen for notifications on the channel
                await conn.execute(f"LISTEN {self.channel};")
                self.logger.info(f"Listening for database events on channel '{self.channel}'")
                
                # Listen for notifications
                while not self._stop_requested:
                    # Wait for notifications
                    message = await conn.connection.driver_connection.notifies.get()
                    self.logger.debug(f"Received notification: {message.payload}")
                    
                    try:
                        # Parse the notification payload
                        payload = json.loads(message.payload)
                        
                        # Convert to workflow event
                        workflow_event = WorkflowEventModel(
                            table_name=payload["table_name"],
                            schema_name=payload["schema_name"],
                            operation=payload["operation"],
                            timestamp=payload["timestamp"],
                            payload=payload["payload"],
                        )
                        
                        # Process the event
                        await self.workflow_engine.process_event(workflow_event)
                        
                    except json.JSONDecodeError:
                        self.logger.error(f"Failed to parse notification payload: {message.payload}")
                    except Exception as e:
                        self.logger.exception(f"Error processing database event: {e}")
                
            except asyncio.CancelledError:
                self.logger.info("PostgreSQL workflow event listener task was cancelled")
                raise
            except Exception as e:
                self.logger.exception(f"Error in PostgreSQL workflow event listener: {e}")
            finally:
                # Stop listening
                await conn.execute(f"UNLISTEN {self.channel};")
                self.logger.info(f"Stopped listening for database events on channel '{self.channel}'")