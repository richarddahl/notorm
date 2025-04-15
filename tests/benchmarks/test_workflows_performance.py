import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, AsyncMock

# Import the Result class for proper return types
from src.uno.common.result import Result, Success, Failure

# Import models but avoid table redefinition
from src.uno.workflows.models import (
    WorkflowConditionType,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowDBEvent,
    User,
)


# Create model classes without SQLAlchemy table definitions
class MockWorkflowDef:
    def __init__(
        self,
        id,
        name,
        description,
        active=True,
        triggers=None,
        conditions=None,
        actions=None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.active = active
        self.triggers = triggers or []
        self.conditions = conditions or []
        self.actions = actions or []
        self.recipients = []
        self.status = "active" if active else "inactive"


class MockWorkflowTrigger:
    def __init__(self, id, event_type, entity_type, field_conditions=None):
        self.id = id
        self.event_type = event_type
        self.entity_type = entity_type
        self.field_conditions = field_conditions or {}
        self.is_active = True
        self.priority = 0


class MockWorkflowCondition:
    def __init__(
        self, id, field_path=None, condition_type=None, value=None, query_id=None
    ):
        self.id = id
        self.field_path = field_path
        self.condition_type = condition_type
        self.value = value
        self.query_id = query_id
        self.name = f"Condition {id}"
        self.condition_config = {"field": field_path, "operator": "eq", "value": value}


class MockWorkflowAction:
    def __init__(self, id, action_type, parameters=None, recipients=None):
        self.id = id
        self.action_type = action_type
        self.parameters = parameters or {}
        self.recipients = recipients or []
        self.name = f"Action {id}"
        self.is_active = True
        self.action_config = parameters or {}


class MockWorkflowRecipient:
    def __init__(self, id, recipient_type, recipient_id, action_id=None):
        self.id = id
        self.recipient_type = recipient_type
        self.recipient_id = recipient_id
        self.action_id = action_id


class MockWorkflowEventModel:
    def __init__(self, table_name, operation, payload, timestamp=None):
        self.table_name = table_name
        self.operation = operation
        self.payload = payload
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def dict(self):
        return {
            "table_name": self.table_name,
            "operation": self.operation,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class DomainEvent:
    def __init__(self, event_type, payload, entity_type, entity_id, timestamp=None):
        self.event_type = event_type
        self.payload = payload
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.timestamp = timestamp or datetime.utcnow()

        # Convert to workflow event model format
        self.table_name = entity_type
        self.operation = self._map_event_type_to_operation(event_type)

    def _map_event_type_to_operation(self, event_type):
        if "created" in event_type:
            return WorkflowDBEvent.INSERT
        elif "updated" in event_type:
            return WorkflowDBEvent.UPDATE
        elif "deleted" in event_type:
            return WorkflowDBEvent.DELETE
        else:
            return WorkflowDBEvent.UPDATE  # Default to update for other events


# Mock WorkflowEngine to avoid database interactions
class MockWorkflowEngine:
    def __init__(self):
        self.logger = MagicMock()
        self.logger.debug = MagicMock()
        self.logger.info = MagicMock()
        self.logger.warning = MagicMock()
        self.logger.error = MagicMock()

    async def process_event(self, event):
        # Convert domain event to workflow event model
        workflow_event = MockWorkflowEventModel(
            table_name=event.entity_type,
            operation=event.operation,
            payload=event.payload,
            timestamp=event.timestamp.isoformat(),
        )

        # Find matching workflows
        matching_workflows = await self._find_matching_workflows(workflow_event)

        if not matching_workflows:
            return Success(
                {"status": "no_matches", "message": "No matching workflows found"}
            )

        results = []

        # Execute each matching workflow
        for workflow, trigger in matching_workflows:
            # Evaluate conditions
            conditions_result = await self._evaluate_conditions(
                workflow.conditions, workflow_event
            )

            if conditions_result:
                # Execute actions
                action_count = await self._execute_actions(
                    workflow, workflow_event, workflow.conditions
                )
                results.append(
                    {
                        "workflow_id": workflow.id,
                        "workflow_name": workflow.name,
                        "status": "success",
                        "actions_executed": action_count,
                    }
                )
            else:
                results.append(
                    {
                        "workflow_id": workflow.id,
                        "workflow_name": workflow.name,
                        "status": "skipped",
                        "message": "Conditions not met",
                    }
                )

        return Success(
            {"status": "processed", "count": len(results), "results": results}
        )

    async def _find_matching_workflows(self, event):
        # This will be mocked in the fixture
        return []

    async def _evaluate_conditions(self, conditions, event):
        # Simple mock implementation
        for condition in conditions:
            if condition.condition_type == "QUERY_MATCH":
                result = await self._handle_query_match_condition(condition, event)
                if not result:
                    return False
            else:
                # For other conditions, check field path
                if condition.field_path:
                    value = self._resolve_field_path(
                        event.payload, condition.field_path
                    )
                    if value != condition.value:
                        return False

        return True

    def _resolve_field_path(self, data, path):
        """Resolve a field path in the data."""
        parts = path.split(".")
        current = data

        for part in parts:
            # Handle array indexing
            if "[" in part and "]" in part:
                array_name, index_str = part.split("[", 1)
                index = int(index_str.rstrip("]"))

                if array_name not in current:
                    return None

                array = current[array_name]
                if not isinstance(array, list) or index >= len(array):
                    return None

                current = array[index]
            else:
                # Regular property access
                if part not in current:
                    return None
                current = current[part]

        return current

    async def _handle_query_match_condition(self, condition, event):
        # Mock implementation
        return True

    async def _execute_actions(self, workflow, event, matching_conditions):
        # Count active actions
        active_actions = [a for a in workflow.actions if a.is_active]

        for action in active_actions:
            # Resolve recipients
            recipients = await self._resolve_recipients(action.recipients)

        return len(active_actions)

    async def _resolve_recipients(self, recipients):
        # Mock implementation
        resolved_users = []

        for recipient in recipients:
            if recipient.recipient_type == "USER":
                resolved_users.append(
                    User(
                        id=recipient.recipient_id,
                        username=f"user_{recipient.recipient_id}",
                        email=f"user_{recipient.recipient_id}@example.com",
                        is_active=True,
                    )
                )
            elif recipient.recipient_type == "ROLE":
                # Simulate resolving a role to multiple users
                for i in range(5):
                    resolved_users.append(
                        User(
                            id=f"role_user_{i}",
                            username=f"role_user_{i}",
                            email=f"role_user_{i}@example.com",
                            is_active=True,
                        )
                    )
            elif recipient.recipient_type == "GROUP":
                # Simulate resolving a group to multiple users
                for i in range(10):
                    resolved_users.append(
                        User(
                            id=f"group_user_{i}",
                            username=f"group_user_{i}",
                            email=f"group_user_{i}@example.com",
                            is_active=True,
                        )
                    )

        return resolved_users


# Define test fixtures
@pytest.fixture
def event_data():
    """Create various test events for benchmarking."""
    return {
        "small_event": DomainEvent(
            event_type="entity_created",
            payload={
                "id": str(uuid.uuid4()),
                "name": "Test Entity",
                "status": "active",
            },
            entity_type="test_entity",
            entity_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
        ),
        "medium_event": DomainEvent(
            event_type="entity_updated",
            payload={
                "id": str(uuid.uuid4()),
                "name": "Test Entity",
                "status": "active",
                "attributes": {
                    "color": "blue",
                    "size": "medium",
                    "price": 99.99,
                    "in_stock": True,
                    "tags": ["new", "featured", "sale"],
                },
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "created_by": "user_123",
                    "updated_by": "user_456",
                },
            },
            entity_type="test_entity",
            entity_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
        ),
        "large_event": DomainEvent(
            event_type="complex_operation",
            payload={
                "id": str(uuid.uuid4()),
                "operation": "complex_calculation",
                "parameters": {f"param_{i}": f"value_{i}" for i in range(50)},
                "nested_data": {
                    "level1": {
                        "level2": {"level3": {f"data_{i}": i for i in range(20)}}
                    }
                },
                "related_entities": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "related_entity",
                        "name": f"Related {i}",
                    }
                    for i in range(10)
                ],
            },
            entity_type="complex_entity",
            entity_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
        ),
    }


@pytest.fixture
def workflow_definitions():
    """Create various workflow definitions of different complexities."""
    workflows = {}

    # Simple workflow with one condition and one action
    workflows["simple_workflow"] = MockWorkflowDef(
        id=str(uuid.uuid4()),
        name="Simple Notification Workflow",
        description="Simple workflow with one condition and one action",
        active=True,
        triggers=[
            MockWorkflowTrigger(
                id=str(uuid.uuid4()),
                event_type="entity_created",
                entity_type="test_entity",
            )
        ],
        conditions=[
            MockWorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="status",
                condition_type=WorkflowConditionType.FIELD_VALUE,
                value="active",
            )
        ],
        actions=[
            MockWorkflowAction(
                id=str(uuid.uuid4()),
                action_type=WorkflowActionType.NOTIFICATION,
                parameters={"message": "New entity created", "priority": "normal"},
                recipients=[
                    MockWorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type=WorkflowRecipientType.USER,
                        recipient_id="user_123",
                    )
                ],
            )
        ],
    )

    # Medium workflow with multiple conditions and actions
    workflows["medium_workflow"] = MockWorkflowDef(
        id=str(uuid.uuid4()),
        name="Medium Complexity Workflow",
        description="Workflow with multiple conditions and actions",
        active=True,
        triggers=[
            MockWorkflowTrigger(
                id=str(uuid.uuid4()),
                event_type="entity_updated",
                entity_type="test_entity",
            )
        ],
        conditions=[
            MockWorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="status",
                condition_type=WorkflowConditionType.FIELD_VALUE,
                value="active",
            ),
            MockWorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="attributes.price",
                condition_type=WorkflowConditionType.FIELD_VALUE,
                value=50.0,
            ),
            MockWorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="attributes.in_stock",
                condition_type=WorkflowConditionType.FIELD_VALUE,
                value=True,
            ),
        ],
        actions=[
            MockWorkflowAction(
                id=str(uuid.uuid4()),
                action_type=WorkflowActionType.NOTIFICATION,
                parameters={"message": "Item price updated", "priority": "high"},
                recipients=[
                    MockWorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type=WorkflowRecipientType.USER,
                        recipient_id="user_123",
                    ),
                    MockWorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type=WorkflowRecipientType.ROLE,
                        recipient_id="sales_managers",
                    ),
                ],
            ),
            MockWorkflowAction(
                id=str(uuid.uuid4()),
                action_type=WorkflowActionType.EMAIL,
                parameters={
                    "subject": "Price Update Alert",
                    "template": "price_update_template",
                    "cc": "support@example.com",
                },
                recipients=[
                    MockWorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type=WorkflowRecipientType.USER,
                        recipient_id="user_456",
                    )
                ],
            ),
        ],
    )

    # Complex workflow with many conditions and actions
    workflows["complex_workflow"] = MockWorkflowDef(
        id=str(uuid.uuid4()),
        name="Complex Business Process Workflow",
        description="Complex workflow with many conditions and actions",
        active=True,
        triggers=[
            MockWorkflowTrigger(
                id=str(uuid.uuid4()),
                event_type="complex_operation",
                entity_type="complex_entity",
            )
        ],
        conditions=[
            MockWorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="operation",
                condition_type=WorkflowConditionType.FIELD_VALUE,
                value="complex_calculation",
            ),
            MockWorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="nested_data.level1.level2.level3.data_5",
                condition_type=WorkflowConditionType.FIELD_VALUE,
                value=0,
            ),
            MockWorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="related_entities[0].type",
                condition_type=WorkflowConditionType.FIELD_VALUE,
                value="related_entity",
            ),
            MockWorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="parameters.param_10",
                condition_type=WorkflowConditionType.FIELD_VALUE,
                value="value_10",
            ),
            MockWorkflowCondition(
                id=str(uuid.uuid4()),
                condition_type=WorkflowConditionType.QUERY_MATCH,
                value="complex_query_id_123",
                query_id="complex_query_id_123",
            ),
        ],
        actions=[
            MockWorkflowAction(
                id=str(uuid.uuid4()),
                action_type=WorkflowActionType.NOTIFICATION,
                parameters={
                    "message": "Complex process completed",
                    "priority": "critical",
                },
                recipients=[
                    MockWorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type=WorkflowRecipientType.USER,
                        recipient_id="user_123",
                    ),
                    MockWorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type=WorkflowRecipientType.ROLE,
                        recipient_id="administrators",
                    ),
                    MockWorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type=WorkflowRecipientType.GROUP,
                        recipient_id="data_analysts",
                    ),
                ],
            ),
            MockWorkflowAction(
                id=str(uuid.uuid4()),
                action_type=WorkflowActionType.EMAIL,
                parameters={
                    "subject": "Critical Process Alert",
                    "template": "complex_process_template",
                    "attachments": ["report.pdf", "data.csv"],
                },
                recipients=[
                    MockWorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type=WorkflowRecipientType.USER,
                        recipient_id="alerts@example.com",
                    )
                ],
            ),
            MockWorkflowAction(
                id=str(uuid.uuid4()),
                action_type=WorkflowActionType.WEBHOOK,
                parameters={
                    "url": "https://api.example.com/webhook",
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json",
                        "X-API-Key": "secret_key",
                    },
                    "body_template": "complex_api_template",
                },
            ),
        ],
    )

    return workflows


@pytest.fixture
def mock_workflow_engine(workflow_definitions):
    """Create a workflow engine with pre-loaded workflow definitions."""
    engine = MockWorkflowEngine()

    # Mock the _find_matching_workflows method to return the predefined workflows
    async def mock_find_matching_workflows(event):
        if (
            event.operation == WorkflowDBEvent.INSERT
            and event.table_name == "test_entity"
        ):
            return [
                (
                    workflow_definitions["simple_workflow"],
                    workflow_definitions["simple_workflow"].triggers[0],
                )
            ]
        elif (
            event.operation == WorkflowDBEvent.UPDATE
            and event.table_name == "test_entity"
        ):
            return [
                (
                    workflow_definitions["medium_workflow"],
                    workflow_definitions["medium_workflow"].triggers[0],
                )
            ]
        elif event.table_name == "complex_entity":
            return [
                (
                    workflow_definitions["complex_workflow"],
                    workflow_definitions["complex_workflow"].triggers[0],
                )
            ]
        return []

    engine._find_matching_workflows = mock_find_matching_workflows

    return engine


# Benchmarks
@pytest.mark.asyncio
async def test_workflow_event_processing_simple(
    mock_workflow_engine, event_data, benchmark
):
    """Benchmark the performance of processing simple events with simple workflows."""
    event = event_data["small_event"]

    # Define the benchmark function
    async def process_simple_event():
        return await mock_workflow_engine.process_event(event)

    # Run the benchmark
    result = await benchmark.pedantic(process_simple_event, iterations=1, rounds=100)

    # Verify result for debugging
    assert result is not None


@pytest.mark.asyncio
async def test_workflow_event_processing_medium(
    mock_workflow_engine, event_data, benchmark
):
    """Benchmark the performance of processing medium complexity events with medium workflows."""
    event = event_data["medium_event"]

    # Define the benchmark function
    async def process_medium_event():
        return await mock_workflow_engine.process_event(event)

    # Run the benchmark
    result = await benchmark.pedantic(process_medium_event, iterations=1, rounds=100)

    # Verify result for debugging
    assert result is not None


@pytest.mark.asyncio
async def test_workflow_event_processing_complex(
    mock_workflow_engine, event_data, benchmark
):
    """Benchmark the performance of processing complex events with complex workflows."""
    event = event_data["large_event"]

    # Define the benchmark function
    async def process_complex_event():
        return await mock_workflow_engine.process_event(event)

    # Run the benchmark
    result = await benchmark.pedantic(process_complex_event, iterations=1, rounds=100)

    # Verify result for debugging
    assert result is not None


@pytest.mark.asyncio
async def test_condition_evaluation_performance(
    mock_workflow_engine, workflow_definitions, event_data, benchmark
):
    """Benchmark the performance of evaluating conditions of different complexities."""
    # Get workflows with different condition complexities
    simple_workflow = workflow_definitions["simple_workflow"]
    medium_workflow = workflow_definitions["medium_workflow"]
    complex_workflow = workflow_definitions["complex_workflow"]

    # Map events to workflows
    workflow_event_pairs = [
        (
            simple_workflow,
            MockWorkflowEventModel(
                table_name="test_entity",
                operation=WorkflowDBEvent.INSERT,
                payload=event_data["small_event"].payload,
            ),
        ),
        (
            medium_workflow,
            MockWorkflowEventModel(
                table_name="test_entity",
                operation=WorkflowDBEvent.UPDATE,
                payload=event_data["medium_event"].payload,
            ),
        ),
        (
            complex_workflow,
            MockWorkflowEventModel(
                table_name="complex_entity",
                operation=WorkflowDBEvent.UPDATE,
                payload=event_data["large_event"].payload,
            ),
        ),
    ]

    results = {}

    for workflow, event in workflow_event_pairs:
        workflow_name = workflow.name

        # Define benchmark function for this workflow
        async def evaluate_conditions():
            return await mock_workflow_engine._evaluate_conditions(
                workflow.conditions, event
            )

        # Run benchmark
        result = await benchmark.pedantic(
            evaluate_conditions, iterations=1, rounds=50, warmup_rounds=5
        )

        # Store results
        results[workflow_name] = result

    # Verify we have results for all workflows
    assert len(results) == 3


@pytest.mark.asyncio
async def test_action_execution_performance(
    mock_workflow_engine, workflow_definitions, event_data, benchmark
):
    """Benchmark the performance of executing actions of different complexities."""
    # Get workflows with different action complexities
    simple_workflow = workflow_definitions["simple_workflow"]
    medium_workflow = workflow_definitions["medium_workflow"]
    complex_workflow = workflow_definitions["complex_workflow"]

    # Map events to workflows
    workflow_event_pairs = [
        (
            simple_workflow,
            MockWorkflowEventModel(
                table_name="test_entity",
                operation=WorkflowDBEvent.INSERT,
                payload=event_data["small_event"].payload,
            ),
        ),
        (
            medium_workflow,
            MockWorkflowEventModel(
                table_name="test_entity",
                operation=WorkflowDBEvent.UPDATE,
                payload=event_data["medium_event"].payload,
            ),
        ),
        (
            complex_workflow,
            MockWorkflowEventModel(
                table_name="complex_entity",
                operation=WorkflowDBEvent.UPDATE,
                payload=event_data["large_event"].payload,
            ),
        ),
    ]

    results = {}

    for workflow, event in workflow_event_pairs:
        workflow_name = workflow.name

        # Define benchmark function for this workflow
        async def execute_actions():
            return await mock_workflow_engine._execute_actions(
                workflow, event, workflow.conditions
            )

        # Run benchmark
        result = await benchmark.pedantic(
            execute_actions, iterations=1, rounds=50, warmup_rounds=5
        )

        # Store results
        results[workflow_name] = result

    # Verify we have results for all workflows
    assert len(results) == 3


@pytest.mark.asyncio
async def test_field_path_resolution_performance(
    mock_workflow_engine, event_data, benchmark
):
    """Benchmark the performance of resolving field paths of different complexities."""
    # Create field paths of varying complexity
    field_paths = [
        "id",  # Simple path
        "name",  # Simple path
        "attributes.color",  # Nested path
        "attributes.tags[1]",  # Array access
        "nested_data.level1.level2.level3.data_10",  # Deeply nested path
        "related_entities[5].name",  # Array access with nested property
        "nonexistent.path.that.does.not.exist",  # Path that doesn't resolve
    ]

    # Use the complex event as it has all the required fields
    event = event_data["large_event"]

    results = {}

    for path in field_paths:
        # Define benchmark function for this path
        def resolve_field_path():
            try:
                # Access the mock_workflow_engine's internal method for resolving paths
                return mock_workflow_engine._resolve_field_path(event.payload, path)
            except Exception:
                return None

        # Run benchmark
        result = benchmark.pedantic(resolve_field_path, iterations=100, rounds=10)

        # Store results
        results[path] = result

    # Verify we have results for all paths
    assert len(results) == len(field_paths)


@pytest.mark.asyncio
async def test_concurrent_event_processing(mock_workflow_engine, event_data, benchmark):
    """Benchmark the performance of processing multiple events concurrently."""
    # Create a mix of events
    events = [
        event_data["small_event"],
        event_data["medium_event"],
        event_data["large_event"],
        # Add some duplicates to simulate real-world patterns
        event_data["small_event"],
        event_data["medium_event"],
        event_data["small_event"],
    ]

    # Define batch sizes to test
    batch_sizes = [1, 5, 10, 20]

    results = {}

    for batch_size in batch_sizes:
        # Create a batch of events of the specified size
        event_batch = events * (batch_size // len(events) + 1)
        event_batch = event_batch[:batch_size]

        # Define benchmark function for this batch size
        async def process_event_batch():
            tasks = [mock_workflow_engine.process_event(event) for event in event_batch]
            return await asyncio.gather(*tasks)

        # Run benchmark
        result = await benchmark.pedantic(process_event_batch, iterations=1, rounds=20)

        # Store results
        results[f"batch_size_{batch_size}"] = result

    # Verify we have results for all batch sizes
    assert len(results) == len(batch_sizes)


@pytest.mark.asyncio
async def test_recipient_resolution_performance(
    mock_workflow_engine, workflow_definitions, benchmark
):
    """Benchmark the performance of resolving different types and numbers of recipients."""
    # Extract recipients from different workflows
    simple_recipients = (
        workflow_definitions["simple_workflow"].actions[0].recipients
    )  # 1 user
    medium_recipients = (
        workflow_definitions["medium_workflow"].actions[0].recipients
    )  # 1 user, 1 role
    complex_recipients = (
        workflow_definitions["complex_workflow"].actions[0].recipients
    )  # 1 user, 1 role, 1 group

    recipient_sets = [
        ("simple", simple_recipients),
        ("medium", medium_recipients),
        ("complex", complex_recipients),
    ]

    results = {}

    for name, recipients in recipient_sets:
        # Define benchmark function
        async def resolve_recipients_benchmark():
            return await mock_workflow_engine._resolve_recipients(recipients)

        # Run benchmark
        result = await benchmark.pedantic(
            resolve_recipients_benchmark, iterations=1, rounds=50
        )

        # Store results
        results[name] = result

    # Verify we have results for all recipient sets
    assert len(results) == len(recipient_sets)
