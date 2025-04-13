# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Usage examples for the workflow module.

This file contains examples of how to set up and use the workflow module
for creating and managing user-defined notification workflows.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional

import inject

from uno.database.db_manager import DBManager
from uno.domain.events import DomainEvent
from uno.domain.event_dispatcher import EventDispatcher
from uno.enums import WorkflowDBEvent
from uno.settings import uno_settings

from uno.workflows.models import (
    WorkflowDefinition,
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowConditionType,
)
from uno.workflows.objs import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
)
from uno.workflows.engine import WorkflowEngine, WorkflowEventHandler
from uno.workflows.provider import WorkflowService, WorkflowRepository


# Example domain event that could trigger a workflow
class UserCreatedEvent(DomainEvent):
    def __init__(self, user_id: str, username: str, email: str):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.email = email
        self.aggregate_id = user_id
        self.aggregate_type = "user"


# Example domain event for order processing
class OrderPlacedEvent(DomainEvent):
    def __init__(self, order_id: str, user_id: str, total_amount: float, items: List[Dict[str, Any]]):
        super().__init__()
        self.order_id = order_id
        self.user_id = user_id
        self.total_amount = total_amount
        self.items = items
        self.aggregate_id = order_id
        self.aggregate_type = "order"


async def create_example_workflow() -> str:
    """Create an example workflow for user registration notifications."""
    # Get the workflow service from the dependency injector
    workflow_service = inject.instance(WorkflowService)
    
    # Create a new workflow definition
    workflow = WorkflowDef(
        name="User Registration Notification",
        description="Send notifications when new users register in the system",
        status=WorkflowStatus.ACTIVE,
        version="1.0.0",
    )
    
    # Add a trigger for the USER_CREATED event
    trigger = WorkflowTrigger(
        entity_type="user",
        operation=WorkflowDBEvent.INSERT,
        priority=100,
        is_active=True,
    )
    workflow.triggers.append(trigger)
    
    # Add a condition that only triggers for verified users
    condition = WorkflowCondition(
        condition_type=WorkflowConditionType.FIELD_VALUE,
        condition_config={
            "field": "is_verified",
            "operator": "eq",
            "value": True,
        },
        name="User is verified",
        description="Only notify for verified users",
        order=0,
    )
    workflow.conditions.append(condition)
    
    # Add an action to send a notification
    action = WorkflowAction(
        action_type=WorkflowActionType.NOTIFICATION,
        action_config={
            "title": "New User Registration",
            "message": "A new verified user has registered: {{ payload.username }}",
            "priority": "medium",
        },
        name="Send admin notification",
        description="Send notification to administrators",
        order=0,
        is_active=True,
    )
    workflow.actions.append(action)
    
    # Add recipients for the notification
    admin_recipient = WorkflowRecipient(
        recipient_type=WorkflowRecipientType.ROLE,
        recipient_id="admin",
        name="All administrators",
    )
    workflow.recipients.append(admin_recipient)
    
    # Create the workflow
    result = await workflow_service.create_workflow(workflow)
    
    if result.is_err():
        raise Exception(f"Failed to create workflow: {result.unwrap_err()}")
    
    workflow_id = result.unwrap()
    print(f"Created workflow with ID: {workflow_id}")
    
    return workflow_id


async def create_high_value_order_workflow() -> str:
    """Create an example workflow for high-value order notifications."""
    # Get the workflow service from the dependency injector
    workflow_service = inject.instance(WorkflowService)
    
    # Create a new workflow definition
    workflow = WorkflowDef(
        name="High-Value Order Notification",
        description="Send notifications when orders with high value are placed",
        status=WorkflowStatus.ACTIVE,
        version="1.0.0",
    )
    
    # Add a trigger for the ORDER_CREATED event
    trigger = WorkflowTrigger(
        entity_type="order",
        operation=WorkflowDBEvent.INSERT,
        priority=100,
        is_active=True,
    )
    workflow.triggers.append(trigger)
    
    # Add a condition for high-value orders (over $1000)
    condition = WorkflowCondition(
        condition_type=WorkflowConditionType.FIELD_VALUE,
        condition_config={
            "field": "total_amount",
            "operator": "gt",
            "value": 1000,
        },
        name="High-value order",
        description="Order total is over $1000",
        order=0,
    )
    workflow.conditions.append(condition)
    
    # Add an action to send an email notification
    email_action = WorkflowAction(
        action_type=WorkflowActionType.EMAIL,
        action_config={
            "subject": "High-Value Order Alert",
            "template": "high_value_order",
            "variables": {
                "order_id": "{{ payload.order_id }}",
                "amount": "{{ payload.total_amount }}",
                "user_id": "{{ payload.user_id }}",
            },
        },
        name="Send email alert",
        description="Send email alert to sales team",
        order=0,
        is_active=True,
    )
    workflow.actions.append(email_action)
    
    # Add an action to send an in-app notification
    notification_action = WorkflowAction(
        action_type=WorkflowActionType.NOTIFICATION,
        action_config={
            "title": "High-Value Order Placed",
            "message": "Order #{{ payload.order_id }} for ${{ payload.total_amount }} was placed by user {{ payload.user_id }}",
            "priority": "high",
        },
        name="Send in-app notification",
        description="Send in-app notification to sales team",
        order=1,
        is_active=True,
    )
    workflow.actions.append(notification_action)
    
    # Add recipients for the notifications
    sales_team_recipient = WorkflowRecipient(
        recipient_type=WorkflowRecipientType.GROUP,
        recipient_id="sales_team",
        name="Sales Team",
    )
    workflow.recipients.append(sales_team_recipient)
    
    # Add a specific recipient for the email only
    manager_recipient = WorkflowRecipient(
        recipient_type=WorkflowRecipientType.USER,
        recipient_id="sales_manager",
        name="Sales Manager",
        action_id=email_action.id,  # This recipient only gets the email, not the notification
    )
    workflow.recipients.append(manager_recipient)
    
    # Create the workflow
    result = await workflow_service.create_workflow(workflow)
    
    if result.is_err():
        raise Exception(f"Failed to create workflow: {result.unwrap_err()}")
    
    workflow_id = result.unwrap()
    print(f"Created workflow with ID: {workflow_id}")
    
    return workflow_id


async def example_trigger_workflow_with_domain_event():
    """Example of triggering a workflow using a domain event."""
    # Get the event dispatcher and workflow event handler
    event_dispatcher = inject.instance(EventDispatcher)
    workflow_event_handler = inject.instance(WorkflowEventHandler)
    
    # Register the workflow event handler with the event dispatcher
    event_dispatcher.register_handler(UserCreatedEvent, workflow_event_handler)
    
    # Create a user created event
    user_event = UserCreatedEvent(
        user_id="user123",
        username="johndoe",
        email="john@example.com"
    )
    
    # Publish the event
    await event_dispatcher.dispatch(user_event)
    
    print(f"Dispatched UserCreatedEvent for user {user_event.username}")


async def example_start_postgres_listener():
    """Example of starting the PostgreSQL event listener."""
    # Get the workflow service
    workflow_service = inject.instance(WorkflowService)
    
    # Start the PostgreSQL event listener
    result = await workflow_service.start_event_listener()
    
    if result.is_err():
        print(f"Failed to start event listener: {result.unwrap_err()}")
        return
    
    print("PostgreSQL event listener started")
    
    # Keep the listener running for a while
    try:
        print("Listening for database events (press Ctrl+C to stop)...")
        await asyncio.sleep(60)  # Run for 60 seconds
    except asyncio.CancelledError:
        print("Listener task cancelled")
    finally:
        # Stop the listener
        await workflow_service.stop_event_listener()
        print("PostgreSQL event listener stopped")


async def example_manual_event_processing():
    """Example of manually processing a workflow event."""
    # Get the workflow service
    workflow_service = inject.instance(WorkflowService)
    
    # Create a mock event
    event = {
        "table_name": "user",
        "schema_name": uno_settings.DB_SCHEMA,
        "operation": WorkflowDBEvent.INSERT,
        "timestamp": 1650000000.0,
        "payload": {
            "id": "user456",
            "username": "janedoe",
            "email": "jane@example.com",
            "is_verified": True,
        }
    }
    
    # Process the event
    print(f"Processing event: {json.dumps(event, indent=2)}")
    result = await workflow_service.process_event(event)
    
    if result.is_err():
        print(f"Failed to process event: {result.unwrap_err()}")
        return
    
    print(f"Event processed: {json.dumps(result.unwrap(), indent=2)}")


async def run_examples():
    """Run all the workflow examples."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create example workflows
    user_workflow_id = await create_example_workflow()
    order_workflow_id = await create_high_value_order_workflow()
    
    # List all active workflows
    workflow_service = inject.instance(WorkflowService)
    workflows_result = await workflow_service.get_active_workflows()
    
    if workflows_result.is_ok():
        workflows = workflows_result.unwrap()
        print(f"Active workflows ({len(workflows)}):")
        for workflow in workflows:
            print(f"  - {workflow.name} (ID: {workflow.id})")
    
    # Trigger workflows with different methods
    await example_trigger_workflow_with_domain_event()
    await example_manual_event_processing()
    
    # Uncomment to start the PostgreSQL event listener
    # await example_start_postgres_listener()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(run_examples())