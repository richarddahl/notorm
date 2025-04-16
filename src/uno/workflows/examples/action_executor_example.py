#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example demonstrating the enhanced workflow action execution system.

This example shows how to:
1. Create workflows with different action types
2. Test the execution of different action types
3. Implement and register a custom action executor
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from uno.database.db_manager import DBManager
from uno.domain.events import DomainEvent, EventDispatcher
from uno.enums import WorkflowDBEvent
from uno.dependencies.scoped_container import get_service

from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
)
from uno.workflows.provider import WorkflowService
from uno.workflows.executor import (
    ActionExecutionContext,
    CustomExecutor,
    get_executor,
    register_executor,
)


class OrderCreatedEvent(DomainEvent):
    """Example event for order creation."""

    def __init__(
        self,
        order_id: str,
        customer_id: str,
        total_amount: float,
        items: List[Dict[str, Any]],
    ):
        super().__init__()
        self.order_id = order_id
        self.customer_id = customer_id
        self.total_amount = total_amount
        self.items = items
        self.created_at = datetime.utcnow().isoformat()
        self.aggregate_id = order_id
        self.aggregate_type = "order"


async def create_notification_workflow() -> str:
    """
    Create a workflow with a notification action.

    Returns:
        The ID of the created workflow
    """
    workflow_service = get_service(WorkflowService)

    # Create workflow for order notifications
    workflow = WorkflowDef(
        name="Order Notification Workflow",
        description="Send notification when a new order is created",
        status=WorkflowStatus.ACTIVE,
        version="1.0.0",
    )

    # Add trigger for order creation
    trigger = WorkflowTrigger(
        entity_type="order",
        operation=WorkflowDBEvent.INSERT,
        is_active=True,
    )
    workflow.triggers.append(trigger)

    # Add notification action
    action = WorkflowAction(
        action_type=WorkflowActionType.NOTIFICATION,
        name="Send Order Confirmation Notification",
        action_config={
            "title": "New Order Received",
            "message": "A new order has been placed for ${{event.total_amount}}. Order ID: {{event.order_id}}",
            "type": "success",
            "link": "/orders/{{event.order_id}}",
        },
        is_active=True,
    )
    workflow.actions.append(action)

    # Add sales team recipient
    recipient = WorkflowRecipient(
        recipient_type=WorkflowRecipientType.GROUP,
        recipient_id="sales_team",
        name="Sales Team",
    )
    workflow.recipients.append(recipient)

    # Create the workflow
    result = await workflow_service.create_workflow(workflow)

    if result.is_failure:
        raise Exception(f"Failed to create workflow: {result.error}")

    workflow_id = result.value
    print(f"Created notification workflow with ID: {workflow_id}")

    return workflow_id


async def create_email_workflow() -> str:
    """
    Create a workflow with an email action.

    Returns:
        The ID of the created workflow
    """
    workflow_service = get_service(WorkflowService)

    # Create workflow for order confirmation emails
    workflow = WorkflowDef(
        name="Order Email Workflow",
        description="Send email when a new order is created",
        status=WorkflowStatus.ACTIVE,
        version="1.0.0",
    )

    # Add trigger for order creation
    trigger = WorkflowTrigger(
        entity_type="order",
        operation=WorkflowDBEvent.INSERT,
        is_active=True,
        field_conditions={"total_amount": {"operator": "gt", "value": 100}},
    )
    workflow.triggers.append(trigger)

    # Add email action
    action = WorkflowAction(
        action_type=WorkflowActionType.EMAIL,
        name="Send Order Confirmation Email",
        action_config={
            "subject": "Your Order {{event.order_id}} Has Been Received",
            "content": """
                <h1>Thank you for your order!</h1>
                <p>We have received your order #{{event.order_id}} for ${{event.total_amount}}.</p>
                <p>Your order contains {{event.items|length}} items and will be processed shortly.</p>
                <p>You can view your order status <a href="https://example.com/orders/{{event.order_id}}">here</a>.</p>
            """,
            "is_html": True,
        },
        is_active=True,
    )
    workflow.actions.append(action)

    # Add customer as recipient
    recipient = WorkflowRecipient(
        recipient_type=WorkflowRecipientType.USER,
        recipient_id="{{event.customer_id}}",
        name="Customer",
    )
    workflow.recipients.append(recipient)

    # Create the workflow
    result = await workflow_service.create_workflow(workflow)

    if result.is_failure:
        raise Exception(f"Failed to create workflow: {result.error}")

    workflow_id = result.value
    print(f"Created email workflow with ID: {workflow_id}")

    return workflow_id


async def create_custom_workflow() -> str:
    """
    Create a workflow with a custom action.

    Returns:
        The ID of the created workflow
    """
    # Register a custom executor
    custom_executor = get_executor(WorkflowActionType.CUSTOM)
    if custom_executor and isinstance(custom_executor, CustomExecutor):
        custom_executor.register_custom_executor(
            "order_analytics", track_order_analytics
        )

    workflow_service = get_service(WorkflowService)

    # Create workflow for order analytics
    workflow = WorkflowDef(
        name="Order Analytics Workflow",
        description="Track analytics when a new order is created",
        status=WorkflowStatus.ACTIVE,
        version="1.0.0",
    )

    # Add trigger for order creation
    trigger = WorkflowTrigger(
        entity_type="order",
        operation=WorkflowDBEvent.INSERT,
        is_active=True,
    )
    workflow.triggers.append(trigger)

    # Add custom action
    action = WorkflowAction(
        action_type=WorkflowActionType.CUSTOM,
        name="Track Order Analytics",
        action_config={
            "executor_type": "order_analytics",
            "track_items": True,
            "track_customer": True,
            "analytics_category": "sales",
        },
        is_active=True,
    )
    workflow.actions.append(action)

    # Create the workflow
    result = await workflow_service.create_workflow(workflow)

    if result.is_failure:
        raise Exception(f"Failed to create workflow: {result.error}")

    workflow_id = result.value
    print(f"Created custom workflow with ID: {workflow_id}")

    return workflow_id


async def track_order_analytics(
    action: WorkflowAction, context: ActionExecutionContext, recipients: List[User]
) -> Dict[str, Any]:
    """
    Custom executor function for order analytics.

    This demonstrates how to implement a custom action executor
    that can be registered with the workflow system.
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"Tracking order analytics for order {context.event_data.get('order_id')}"
    )

    # Extract configuration from the action
    config = action.action_config
    track_items = config.get("track_items", False)
    track_customer = config.get("track_customer", False)
    category = config.get("analytics_category", "general")

    # Extract data from event
    order_id = context.event_data.get("order_id")
    customer_id = context.event_data.get("customer_id")
    total_amount = context.event_data.get("total_amount", 0)
    items = context.event_data.get("items", [])

    # Simulate tracking analytics
    analytics_event = {
        "event_type": "order_created",
        "category": category,
        "order_id": order_id,
        "timestamp": datetime.utcnow().isoformat(),
        "total_amount": total_amount,
        "workflow_id": context.workflow_id,
    }

    if track_customer:
        analytics_event["customer_id"] = customer_id

    if track_items:
        analytics_event["item_count"] = len(items)
        analytics_event["items"] = [item.get("id") for item in items]

    # In a real implementation, you might send this to an analytics service
    logger.info(f"Analytics event: {analytics_event}")

    # Simulate an async operation
    await asyncio.sleep(0.1)

    return {
        "tracked": True,
        "event_type": "order_created",
        "category": category,
        "timestamp": analytics_event["timestamp"],
    }


async def trigger_workflows() -> None:
    """
    Trigger the workflows with an order created event.

    This demonstrates how the workflow engine processes events and executes
    different types of actions using the action executor system.
    """
    event_dispatcher = get_service(EventDispatcher)

    # Create a sample order event
    order_event = OrderCreatedEvent(
        order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        customer_id="CUST-12345",
        total_amount=249.99,
        items=[
            {"id": "PROD-1", "name": "Product 1", "price": 99.99, "quantity": 2},
            {"id": "PROD-2", "name": "Product 2", "price": 49.99, "quantity": 1},
        ],
    )

    # Dispatch the event
    await event_dispatcher.dispatch(order_event)
    print(f"Dispatched OrderCreatedEvent for order {order_event.order_id}")

    # Wait for event processing
    await asyncio.sleep(2)

    # Create a smaller order to test field conditions
    small_order_event = OrderCreatedEvent(
        order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        customer_id="CUST-67890",
        total_amount=49.99,
        items=[
            {"id": "PROD-3", "name": "Product 3", "price": 49.99, "quantity": 1},
        ],
    )

    # Dispatch the event
    await event_dispatcher.dispatch(small_order_event)
    print(f"Dispatched OrderCreatedEvent for order {small_order_event.order_id}")

    # Wait for event processing
    await asyncio.sleep(2)


async def run_workflow_executor_example() -> None:
    """
    Run the complete workflow executor example.

    This demonstrates:
    1. Creating workflows with different action types
    2. Implementing a custom action executor
    3. Triggering events to execute the workflows
    4. Using the action executor system to handle different action types
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Create different types of workflows
        logger.info("Creating notification workflow...")
        notification_workflow_id = await create_notification_workflow()

        logger.info("Creating email workflow...")
        email_workflow_id = await create_email_workflow()

        logger.info("Creating custom workflow...")
        custom_workflow_id = await create_custom_workflow()

        # Trigger the workflows
        logger.info("Triggering workflows with order events...")
        await trigger_workflows()

        logger.info("Action Executor Example Summary:")
        logger.info("1. Created workflows with notification, email, and custom actions")
        logger.info("2. Implemented and registered a custom action executor")
        logger.info("3. Triggered events to execute the workflows")
        logger.info(
            "4. Demonstrated the action executor system handling different action types"
        )

    except Exception as e:
        logger.exception(f"Error in workflow executor example: {e}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(run_workflow_executor_example())
