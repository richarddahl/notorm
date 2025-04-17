# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example demonstrating the integration of QueryModel with WorkflowCondition.

This example shows how to use existing QueryModel definitions as conditions
in workflows, enabling complex filtering based on user-defined queries.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from uno.database.db_manager import DBManager
from uno.core.unified_events import UnoDomainEvent
from uno.domain.event_dispatcher import EventDispatcher
from uno.enums import WorkflowDBEvent, Include, Match
from uno.dependencies.scoped_container import get_service, get_scoped_service


from uno.workflows.models import (
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowConditionType,
)
from uno.workflows.provider import WorkflowService


class CustomerCreatedEvent(UnoDomainEvent):
    """Example event for customer creation."""

    def __init__(self, customer_id: str, name: str, region: str, segment: str):
        super().__init__()
        self.customer_id = customer_id
        self.name = name
        self.region = region
        self.segment = segment
        self.aggregate_id = customer_id
        self.aggregate_type = "customer"


async def create_premium_customer_query() -> str:
    """
    Create a query that filters customers by the premium segment.

    This demonstrates how to create a complex query that uses the graph database
    for filtering, which can then be used as a condition in workflows.

    Returns:
        The ID of the created query
    """
    # Get the customer meta type
    customer_meta_type = await MetaType.get_by_name("customer")
    if not customer_meta_type:
        # Create the meta type if it doesn't exist
        customer_meta_type = MetaType(
            name="customer",
            description="Customer records",
        )
        await customer_meta_type.save()

    # Create a query path for the customer segment field
    # This defines the graph path that will be used for querying the graph database,
    # which mirrors the relational data
    segment_path = QueryPath(
        source_meta_type_id=customer_meta_type.id,
        target_meta_type_id=customer_meta_type.id,
        cypher_path="(s:Customer)-[:HAS_SEGMENT]->(t:Segment)",
        data_type="str",
    )
    await segment_path.save()

    # Create a query path for the customer region
    region_path = QueryPath(
        source_meta_type_id=customer_meta_type.id,
        target_meta_type_id=customer_meta_type.id,
        cypher_path="(s:Customer)-[:IN_REGION]->(t:Region)",
        data_type="str",
    )
    await region_path.save()

    # Create a query value for "premium" segment
    segment_value = QueryValue(
        query_path_id=segment_path.id,
        include=Include.INCLUDE,
        match=Match.AND,
        lookup="equal",
    )
    # Assume we have a segment record with id "premium"
    segment_value.values = [{"id": "premium", "name": "Premium"}]
    await segment_value.save()

    # Create a query value for North America region
    region_value = QueryValue(
        query_path_id=region_path.id,
        include=Include.INCLUDE,
        match=Match.AND,
        lookup="equal",
    )
    # Assume we have a region record with id "na"
    region_value.values = [{"id": "na", "name": "North America"}]
    await region_value.save()

    # Create a query that combines both conditions
    # This represents a complex query that would be difficult to express
    # with simple field matching, but is easily represented in the graph DB
    premium_query = Query(
        name="Premium North American Customers",
        description="Customers in the premium segment from North America",
        query_meta_type_id=customer_meta_type.id,
        include_values=Include.INCLUDE,
        match_values=Match.AND,  # Both conditions must be met
    )
    premium_query.query_values = [segment_value, region_value]
    await premium_query.save()

    return premium_query.id


async def create_workflow_with_query_condition(query_id: str) -> str:
    """
    Create a workflow that uses a QueryModel as a condition.

    This demonstrates how to leverage saved complex queries as conditions in workflows,
    allowing administrators to define sophisticated targeting rules through the
    graph database.

    Args:
        query_id: The ID of the query to use as a condition

    Returns:
        The ID of the created workflow
    """
    # Get the workflow service
    workflow_service = await get_scoped_service(WorkflowService)

    # Create a workflow for premium North American customer welcome
    workflow = WorkflowDef(
        name="Premium NA Customer Welcome",
        description="Send a welcome email to new premium customers in North America",
        status=WorkflowStatus.ACTIVE,
        version="1.0.0",
    )

    # Add a trigger for customer creation
    trigger = WorkflowTrigger(
        entity_type="customer",
        operation=WorkflowDBEvent.INSERT,
        is_active=True,
        # Field conditions could be added here for simple matching,
        # but we're using a complex query condition instead
    )
    workflow.triggers.append(trigger)

    # Add a condition using the complex query that leverages the graph DB
    # This is much more powerful than simple field matching
    condition = WorkflowCondition(
        condition_type=WorkflowConditionType.QUERY_MATCH,
        name="Is Premium North American Customer",
        description="Only send welcome email to premium customers in North America",
        query_id=query_id,
        # The condition_config can contain additional parameters if needed
        condition_config={
            "description": "This condition uses a complex graph query to identify premium North American customers"
        },
    )
    workflow.conditions.append(condition)

    # Add an email action
    action = WorkflowAction(
        action_type=WorkflowActionType.EMAIL,
        name="Send Premium NA Welcome Email",
        action_config={
            "subject": "Welcome to Our North American Premium Program",
            "template": "premium_na_welcome",
            "variables": {
                "customer_name": "{{ payload.name }}",
                "region": "{{ payload.region }}",
                "segment": "{{ payload.segment }}",
            },
        },
        is_active=True,
    )
    workflow.actions.append(action)

    # Add specific regional sales team recipient
    recipient = WorkflowRecipient(
        recipient_type=WorkflowRecipientType.GROUP,
        recipient_id="na_sales_team",
        name="North America Sales Team",
    )
    workflow.recipients.append(recipient)

    # Add VIP service team recipient
    vip_recipient = WorkflowRecipient(
        recipient_type=WorkflowRecipientType.GROUP,
        recipient_id="vip_service_team",
        name="VIP Customer Service Team",
    )
    workflow.recipients.append(vip_recipient)

    # Create the workflow
    result = await workflow_service.create_workflow(workflow)

    if result.is_failure:
        raise Exception(f"Failed to create workflow: {result.error}")

    workflow_id = result.value
    print(f"Created workflow with ID: {workflow_id}")

    return workflow_id


async def trigger_workflow_with_event() -> None:
    """
    Trigger the workflow with customer created events.

    This demonstrates how the workflow engine processes events and uses
    the QueryExecutor to evaluate complex conditions leveraging the graph database.
    """
    # Get the event dispatcher
    event_dispatcher = await get_scoped_service(EventDispatcher)

    # Create a customer created event for a premium North American customer
    # This should match our complex query condition
    premium_na_event = CustomerCreatedEvent(
        customer_id="customer456",
        name="Jane Smith",
        region="North America",
        segment="premium",
    )

    # Dispatch the event
    await event_dispatcher.dispatch(premium_na_event)
    print(
        f"Dispatched CustomerCreatedEvent for premium NA customer {premium_na_event.name}"
    )

    # Wait a moment for event processing
    await asyncio.sleep(1)

    # Create a customer created event for a standard North American customer
    # This should NOT match our complex query condition because it's not premium
    standard_na_event = CustomerCreatedEvent(
        customer_id="customer789",
        name="Bob Johnson",
        region="North America",
        segment="standard",
    )

    # Dispatch the event
    await event_dispatcher.dispatch(standard_na_event)
    print(
        f"Dispatched CustomerCreatedEvent for standard NA customer {standard_na_event.name}"
    )

    # Wait a moment for event processing
    await asyncio.sleep(1)

    # Create a customer created event for a premium European customer
    # This should NOT match our complex query condition because it's not North American
    premium_eu_event = CustomerCreatedEvent(
        customer_id="customer101",
        name="Maria Garcia",
        region="Europe",
        segment="premium",
    )

    # Dispatch the event
    await event_dispatcher.dispatch(premium_eu_event)
    print(
        f"Dispatched CustomerCreatedEvent for premium EU customer {premium_eu_event.name}"
    )

    # Wait a moment for event processing
    await asyncio.sleep(2)


async def run_query_integration_example() -> None:
    """
    Run the complete query integration example.

    This demonstrates the full workflow of:
    1. Creating complex queries that leverage the graph database
    2. Using these queries as conditions in workflows
    3. Triggering events that are evaluated against these query conditions

    The example shows how the workflow engine can selectively process events
    based on complex conditions that would be difficult to express with
    simple field matching.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Create a premium North American customer query that uses graph paths
        logger.info(
            "Creating complex graph query for premium North American customers..."
        )
        query_id = await create_premium_customer_query()
        logger.info(f"Created complex query with ID: {query_id}")

        # Create a workflow that uses the complex query as a condition
        logger.info("Creating workflow with complex query condition...")
        workflow_id = await create_workflow_with_query_condition(query_id)
        logger.info(f"Created workflow with ID: {workflow_id}")

        # Trigger the workflow with different events to test condition evaluation
        logger.info("Triggering workflow with various customer events...")
        logger.info(
            "This will demonstrate how the QueryExecutor evaluates records against complex conditions"
        )
        await trigger_workflow_with_event()
        logger.info("All test events processed")

        logger.info("Query Integration Example Summary:")
        logger.info("1. Created a complex query leveraging graph database paths")
        logger.info("2. Used the query as a condition in a workflow")
        logger.info(
            "3. Demonstrated selective event processing based on query execution"
        )
        logger.info("4. Showed integration between QueryModel and WorkflowCondition")

    except Exception as e:
        logger.exception(f"Error in query integration example: {e}")


if __name__ == "__main__":
    # Run the example
    asyncio.run(run_query_integration_example())
