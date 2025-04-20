#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example demonstrating advanced condition and recipient targeting features.

This example shows how to:
1. Create workflows with complex condition combinations
2. Use time-based conditions for scheduling
3. Define attribute-based recipient targeting
4. Implement custom dynamic recipient resolution
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

from uno.database.db_manager import DBManager
from uno.core.events import UnoEvent, EventDispatcher
from uno.enums import WorkflowDBEvent
from uno.dependencies.scoped_container import get_service

from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
)
from uno.workflows.conditions import (
    ExtendedWorkflowConditionType,
    LogicalOperator,
    ComparisonOperator,
    TimeOperator,
    Weekday,
)
from uno.workflows.recipients import (
    ExtendedRecipientType,
    DynamicRecipientResolver,
)
from uno.workflows.provider import WorkflowService


class ProductUpdateEvent(UnoEvent):
    """Example event for product updates."""

    def __init__(
        self,
        product_id: str,
        name: str,
        price: float,
        category: str,
        is_featured: bool,
        in_stock: bool,
        stock_level: int,
    ):
        super().__init__()
        self.product_id = product_id
        self.name = name
        self.price = price
        self.category = category
        self.is_featured = is_featured
        self.in_stock = in_stock
        self.stock_level = stock_level
        self.aggregate_id = product_id
        self.aggregate_type = "product"


async def create_composite_condition_workflow() -> str:
    """
    Create a workflow with composite conditions.

    This example demonstrates how to combine multiple conditions using logical
    operators (AND, OR, NOT) for complex condition evaluation.

    Returns:
        The ID of the created workflow
    """
    workflow_service = get_service(WorkflowService)

    # Create workflow for low stock featured products
    workflow = WorkflowDef(
        name="Featured Product Low Stock Alert",
        description="Send notification when featured products are running low on stock",
        status=WorkflowStatus.ACTIVE,
        version="1.0.0",
    )

    # Add trigger for product updates
    trigger = WorkflowTrigger(
        entity_type="product",
        operation=WorkflowDBEvent.UPDATE,
        is_active=True,
    )
    workflow.triggers.append(trigger)

    # Create a composite condition with logical operators
    condition = WorkflowCondition(
        condition_type=ExtendedWorkflowConditionType.COMPOSITE,
        name="Featured product with low stock",
        description="Product must be featured AND (stock level below 10 OR not in stock)",
        condition_config={
            "operator": LogicalOperator.AND,
            "conditions": [
                # First condition: Product must be featured
                {
                    "type": "field_value",
                    "config": {
                        "field": "is_featured",
                        "operator": ComparisonOperator.EQUAL,
                        "value": True,
                    },
                },
                # Second condition: Low stock OR not in stock (using OR operator)
                {
                    "type": "composite",
                    "config": {
                        "operator": LogicalOperator.OR,
                        "conditions": [
                            # Low stock condition
                            {
                                "type": "field_value",
                                "config": {
                                    "field": "stock_level",
                                    "operator": ComparisonOperator.LESS_THAN,
                                    "value": 10,
                                },
                            },
                            # Not in stock condition
                            {
                                "type": "field_value",
                                "config": {
                                    "field": "in_stock",
                                    "operator": ComparisonOperator.EQUAL,
                                    "value": False,
                                },
                            },
                        ],
                    },
                },
            ],
        },
    )
    workflow.conditions.append(condition)

    # Add notification action
    action = WorkflowAction(
        action_type=WorkflowActionType.NOTIFICATION,
        name="Send Low Stock Alert",
        action_config={
            "title": "Featured Product Low Stock Alert",
            "message": "Featured product '{{event.name}}' is running low on stock ({{event.stock_level}} remaining).",
            "type": "warning",
            "link": "/products/{{event.product_id}}",
        },
        is_active=True,
    )
    workflow.actions.append(action)

    # Add inventory management team as recipients
    recipient = WorkflowRecipient(
        recipient_type=ExtendedRecipientType.ATTRIBUTE,
        recipient_id="department:inventory",
        name="Inventory Management Team",
    )
    workflow.recipients.append(recipient)

    # Create the workflow
    result = await workflow_service.create_workflow(workflow)

    if result.is_failure:
        raise Exception(f"Failed to create workflow: {result.error}")

    workflow_id = result.value
    print(f"Created composite condition workflow with ID: {workflow_id}")

    return workflow_id


async def create_time_based_workflow() -> str:
    """
    Create a workflow with time-based conditions.

    This example demonstrates how to use time-based conditions for scheduling
    workflow execution at specific times or intervals.

    Returns:
        The ID of the created workflow
    """
    workflow_service = get_service(WorkflowService)

    # Create workflow for after-hours price changes
    workflow = WorkflowDef(
        name="After-Hours Price Change Notification",
        description="Send notification when prices are changed outside business hours",
        status=WorkflowStatus.ACTIVE,
        version="1.0.0",
    )

    # Add trigger for product updates
    trigger = WorkflowTrigger(
        entity_type="product",
        operation=WorkflowDBEvent.UPDATE,
        field_conditions={
            # Only trigger when price is changed
            "price": {"operator": "neq", "value": None}
        },
        is_active=True,
    )
    workflow.triggers.append(trigger)

    # Add time-based condition for outside business hours
    condition = WorkflowCondition(
        condition_type="time_based",
        name="Outside Business Hours",
        description="Only notify if price is changed outside normal business hours",
        condition_config={
            "operator": TimeOperator.IN_BUSINESS_HOURS,
            "business_hours": {
                "start": "09:00:00",  # 9:00 AM
                "end": "17:00:00",  # 5:00 PM
                "weekdays": [
                    Weekday.MONDAY,
                    Weekday.TUESDAY,
                    Weekday.WEDNESDAY,
                    Weekday.THURSDAY,
                    Weekday.FRIDAY,
                ],
            },
        },
    )
    workflow.conditions.append(condition)

    # Add notification action
    action = WorkflowAction(
        action_type=WorkflowActionType.NOTIFICATION,
        name="Send After-Hours Price Change Alert",
        action_config={
            "title": "After-Hours Price Change",
            "message": "Product '{{event.name}}' price was changed to ${{event.price}} outside business hours.",
            "type": "warning",
            "link": "/products/{{event.product_id}}",
        },
        is_active=True,
    )
    workflow.actions.append(action)

    # Add pricing team manager as recipient
    recipient = WorkflowRecipient(
        recipient_type=ExtendedRecipientType.ROLE,
        recipient_id="pricing_manager",
        name="Pricing Team Manager",
    )
    workflow.recipients.append(recipient)

    # Create the workflow
    result = await workflow_service.create_workflow(workflow)

    if result.is_failure:
        raise Exception(f"Failed to create workflow: {result.error}")

    workflow_id = result.value
    print(f"Created time-based workflow with ID: {workflow_id}")

    return workflow_id


async def setup_dynamic_recipient_resolver():
    """
    Set up a custom dynamic recipient resolver.

    This example demonstrates how to implement and register a custom dynamic
    recipient resolver for complex recipient targeting logic.
    """
    # Get the DynamicRecipientResolver instance
    from uno.workflows.recipients import get_resolver, ExtendedRecipientType

    dynamic_resolver = get_resolver(ExtendedRecipientType.DYNAMIC)
    if not dynamic_resolver or not isinstance(
        dynamic_resolver, DynamicRecipientResolver
    ):
        raise Exception("Dynamic recipient resolver not available")

    # Register a custom resolver for category-based product notifications
    # This resolver returns product category managers based on the product category
    dynamic_resolver.register_dynamic_resolver(
        "category_manager", resolve_category_manager
    )

    print("Registered custom category manager recipient resolver")


async def resolve_category_manager(context: Dict[str, Any]) -> list[User]:
    """
    Custom dynamic resolver function that returns category managers.

    This function would typically query a database to find users with
    responsibility for a specific product category.
    """
    # Extract category from event data
    event_data = context.get("event_data", {})
    category = event_data.get("category")

    if not category:
        return []

    # In a real implementation, we would query the database
    # For this example, we'll create dummy users based on category
    category_managers = []

    # Create a dummy user based on the category
    category_managers.append(
        User(
            id=f"manager_{category}",
            username=f"{category}_manager",
            email=f"{category}.manager@example.com",
            first_name="Category",
            last_name=f"Manager ({category.title()})",
            is_active=True,
        )
    )

    return category_managers


async def create_dynamic_recipient_workflow() -> str:
    """
    Create a workflow with dynamic recipient targeting.

    This example demonstrates how to use custom dynamic recipient resolution
    for advanced targeting based on complex business rules.

    Returns:
        The ID of the created workflow
    """
    # First set up our custom dynamic resolver
    await setup_dynamic_recipient_resolver()

    workflow_service = get_service(WorkflowService)

    # Create workflow for price change notifications
    workflow = WorkflowDef(
        name="Category Manager Price Change Alert",
        description="Notify category managers when prices change significantly in their category",
        status=WorkflowStatus.ACTIVE,
        version="1.0.0",
    )

    # Add trigger for product updates
    trigger = WorkflowTrigger(
        entity_type="product",
        operation=WorkflowDBEvent.UPDATE,
        is_active=True,
    )
    workflow.triggers.append(trigger)

    # Add condition for significant price change (>10%)
    condition = WorkflowCondition(
        condition_type=ExtendedWorkflowConditionType.COMPOSITE,
        name="Significant price change",
        description="Price has changed by more than 10%",
        condition_config={
            "operator": LogicalOperator.AND,
            "conditions": [
                # Ensure old price exists
                {
                    "type": "field_value",
                    "config": {
                        "field": "old.price",
                        "operator": ComparisonOperator.IS_NOT_NULL,
                    },
                },
                # Ensure new price exists
                {
                    "type": "field_value",
                    "config": {
                        "field": "price",
                        "operator": ComparisonOperator.IS_NOT_NULL,
                    },
                },
                # Custom comparison to check percent change
                # In reality, we might use a custom evaluator for this
                {
                    "type": "custom",
                    "config": {
                        "evaluator_type": "expression",
                        "expression": "abs((new.price - old.price) / old.price) > 0.1",
                    },
                },
            ],
        },
    )
    workflow.conditions.append(condition)

    # Add notification action
    action = WorkflowAction(
        action_type=WorkflowActionType.EMAIL,
        name="Send Price Change Email",
        action_config={
            "subject": "Significant Price Change in Your Category",
            "content": """
                <h1>Price Change Alert</h1>
                <p>A significant price change has occurred in your product category:</p>
                <ul>
                    <li><strong>Product:</strong> {{event.name}}</li>
                    <li><strong>Category:</strong> {{event.category}}</li>
                    <li><strong>Old Price:</strong> ${{event.old.price}}</li>
                    <li><strong>New Price:</strong> ${{event.price}}</li>
                    <li><strong>Change:</strong> {{(event.price - event.old.price) / event.old.price * 100}}%</li>
                </ul>
                <p>Please review this change and ensure it aligns with our pricing strategy.</p>
            """,
            "is_html": True,
        },
        is_active=True,
    )
    workflow.actions.append(action)

    # Add dynamic category manager recipient
    recipient = WorkflowRecipient(
        recipient_type=ExtendedRecipientType.DYNAMIC,
        recipient_id="category_manager",
        name="Product Category Manager",
        notification_config={
            "description": "Dynamically resolves to the manager responsible for this product category"
        },
    )
    workflow.recipients.append(recipient)

    # Create the workflow
    result = await workflow_service.create_workflow(workflow)

    if result.is_failure:
        raise Exception(f"Failed to create workflow: {result.error}")

    workflow_id = result.value
    print(f"Created dynamic recipient workflow with ID: {workflow_id}")

    return workflow_id


async def trigger_workflows_with_events():
    """
    Trigger all example workflows with sample events.

    This demonstrates how the advanced conditions and recipient targeting
    features work in practice.
    """
    event_dispatcher = get_service(EventDispatcher)

    # Create a featured product with low stock
    low_stock_event = ProductUpdateEvent(
        product_id=f"PROD-{uuid.uuid4().hex[:8].upper()}",
        name="Featured Gadget X",
        price=99.99,
        category="electronics",
        is_featured=True,
        in_stock=True,
        stock_level=5,
    )

    # Dispatch the event
    await event_dispatcher.dispatch(low_stock_event)
    print(f"Dispatched low stock event for featured product '{low_stock_event.name}'")

    # Wait a moment for event processing
    await asyncio.sleep(1)

    # Create an after-hours price change event
    price_change_event = ProductUpdateEvent(
        product_id=f"PROD-{uuid.uuid4().hex[:8].upper()}",
        name="Premium Widget Y",
        price=149.99,  # New price
        category="home",
        is_featured=False,
        in_stock=True,
        stock_level=50,
    )

    # Add "old" data to simulate an update
    price_change_event.old = {"price": 129.99}

    # Dispatch the event
    await event_dispatcher.dispatch(price_change_event)
    print(f"Dispatched price change event for product '{price_change_event.name}'")

    # Wait a moment for event processing
    await asyncio.sleep(1)

    # Create a significant price change event
    big_price_change_event = ProductUpdateEvent(
        product_id=f"PROD-{uuid.uuid4().hex[:8].upper()}",
        name="Luxury Item Z",
        price=999.99,  # New price
        category="luxury",
        is_featured=True,
        in_stock=True,
        stock_level=25,
    )

    # Add "old" data to simulate an update with a big price change
    big_price_change_event.old = {"price": 799.99}

    # Dispatch the event
    await event_dispatcher.dispatch(big_price_change_event)
    print(
        f"Dispatched significant price change event for product '{big_price_change_event.name}'"
    )

    # Wait a moment for event processing
    await asyncio.sleep(2)


async def run_advanced_targeting_example():
    """
    Run the complete advanced targeting example.

    This demonstrates:
    1. Creating workflows with complex composite conditions
    2. Using time-based conditions for scheduling
    3. Implementing custom dynamic recipient resolution
    4. Triggering workflows with various events to test condition evaluation
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Create different types of workflow examples
        logger.info("Creating composite condition workflow...")
        composite_workflow_id = await create_composite_condition_workflow()

        logger.info("Creating time-based condition workflow...")
        time_workflow_id = await create_time_based_workflow()

        logger.info("Creating dynamic recipient workflow...")
        dynamic_workflow_id = await create_dynamic_recipient_workflow()

        # Trigger the workflows with events
        logger.info("Triggering workflows with various events...")
        await trigger_workflows_with_events()

        logger.info("Advanced Targeting Example Summary:")
        logger.info("1. Created workflow with composite logical conditions (AND, OR)")
        logger.info("2. Created workflow with time-based scheduling conditions")
        logger.info("3. Implemented and registered a custom dynamic recipient resolver")
        logger.info("4. Created workflow with dynamic recipient targeting")
        logger.info(
            "5. Triggered workflows with events to demonstrate advanced condition evaluation"
        )

    except Exception as e:
        logger.exception(f"Error in advanced targeting example: {e}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(run_advanced_targeting_example())
