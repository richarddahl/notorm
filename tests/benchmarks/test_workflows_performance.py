import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from src.uno.workflows.engine import WorkflowEngine
from src.uno.workflows.models import (
    WorkflowDef, WorkflowTrigger, WorkflowCondition, 
    WorkflowAction, WorkflowRecipient
)
from src.uno.domain.events import DomainEvent


# Define test fixtures
@pytest.fixture
def event_data():
    """Create various test events for benchmarking."""
    return {
        "small_event": DomainEvent(
            event_type="entity_created",
            payload={"id": str(uuid.uuid4()), "name": "Test Entity", "status": "active"},
            entity_type="test_entity",
            entity_id=str(uuid.uuid4()),
            timestamp=datetime.now()
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
                    "tags": ["new", "featured", "sale"]
                },
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "created_by": "user_123",
                    "updated_by": "user_456"
                }
            },
            entity_type="test_entity",
            entity_id=str(uuid.uuid4()),
            timestamp=datetime.now()
        ),
        "large_event": DomainEvent(
            event_type="complex_operation",
            payload={
                "id": str(uuid.uuid4()),
                "operation": "complex_calculation",
                "parameters": {f"param_{i}": f"value_{i}" for i in range(50)},
                "nested_data": {
                    "level1": {
                        "level2": {
                            "level3": {f"data_{i}": i for i in range(20)}
                        }
                    }
                },
                "related_entities": [
                    {"id": str(uuid.uuid4()), "type": "related_entity", "name": f"Related {i}"}
                    for i in range(10)
                ]
            },
            entity_type="complex_entity",
            entity_id=str(uuid.uuid4()),
            timestamp=datetime.now()
        )
    }


@pytest.fixture
def workflow_definitions():
    """Create various workflow definitions of different complexities."""
    workflows = {}
    
    # Simple workflow with one condition and one action
    workflows["simple_workflow"] = WorkflowDef(
        id=str(uuid.uuid4()),
        name="Simple Notification Workflow",
        description="Simple workflow with one condition and one action",
        active=True,
        triggers=[
            WorkflowTrigger(
                id=str(uuid.uuid4()),
                event_type="entity_created",
                entity_type="test_entity"
            )
        ],
        conditions=[
            WorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="status",
                condition_type="EQUALS",
                value="active"
            )
        ],
        actions=[
            WorkflowAction(
                id=str(uuid.uuid4()),
                action_type="NOTIFICATION",
                parameters={"message": "New entity created", "priority": "normal"},
                recipients=[
                    WorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type="USER",
                        recipient_id="user_123"
                    )
                ]
            )
        ]
    )
    
    # Medium workflow with multiple conditions and actions
    workflows["medium_workflow"] = WorkflowDef(
        id=str(uuid.uuid4()),
        name="Medium Complexity Workflow",
        description="Workflow with multiple conditions and actions",
        active=True,
        triggers=[
            WorkflowTrigger(
                id=str(uuid.uuid4()),
                event_type="entity_updated",
                entity_type="test_entity"
            )
        ],
        conditions=[
            WorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="status",
                condition_type="EQUALS",
                value="active"
            ),
            WorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="attributes.price",
                condition_type="GREATER_THAN",
                value="50.0"
            ),
            WorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="attributes.in_stock",
                condition_type="EQUALS",
                value="true"
            )
        ],
        actions=[
            WorkflowAction(
                id=str(uuid.uuid4()),
                action_type="NOTIFICATION",
                parameters={"message": "Item price updated", "priority": "high"},
                recipients=[
                    WorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type="USER",
                        recipient_id="user_123"
                    ),
                    WorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type="ROLE",
                        recipient_id="sales_managers"
                    )
                ]
            ),
            WorkflowAction(
                id=str(uuid.uuid4()),
                action_type="EMAIL",
                parameters={
                    "subject": "Price Update Alert",
                    "template": "price_update_template",
                    "cc": "support@example.com"
                },
                recipients=[
                    WorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type="USER",
                        recipient_id="user_456"
                    )
                ]
            )
        ]
    )
    
    # Complex workflow with many conditions and actions
    workflows["complex_workflow"] = WorkflowDef(
        id=str(uuid.uuid4()),
        name="Complex Business Process Workflow",
        description="Complex workflow with many conditions and actions",
        active=True,
        triggers=[
            WorkflowTrigger(
                id=str(uuid.uuid4()),
                event_type="complex_operation",
                entity_type="complex_entity"
            )
        ],
        conditions=[
            WorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="operation",
                condition_type="EQUALS",
                value="complex_calculation"
            ),
            WorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="nested_data.level1.level2.level3.data_5",
                condition_type="GREATER_THAN",
                value="0"
            ),
            WorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="related_entities[0].type",
                condition_type="EQUALS",
                value="related_entity"
            ),
            WorkflowCondition(
                id=str(uuid.uuid4()),
                field_path="parameters.param_10",
                condition_type="CONTAINS",
                value="value"
            ),
            WorkflowCondition(
                id=str(uuid.uuid4()),
                condition_type="QUERY_MATCH",
                value="complex_query_id_123"  # Reference to a stored query
            )
        ],
        actions=[
            WorkflowAction(
                id=str(uuid.uuid4()),
                action_type="NOTIFICATION",
                parameters={"message": "Complex process completed", "priority": "critical"},
                recipients=[
                    WorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type="USER",
                        recipient_id="user_123"
                    ),
                    WorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type="ROLE",
                        recipient_id="administrators"
                    ),
                    WorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type="GROUP",
                        recipient_id="data_analysts"
                    )
                ]
            ),
            WorkflowAction(
                id=str(uuid.uuid4()),
                action_type="EMAIL",
                parameters={
                    "subject": "Critical Process Alert",
                    "template": "complex_process_template",
                    "attachments": ["report.pdf", "data.csv"]
                },
                recipients=[
                    WorkflowRecipient(
                        id=str(uuid.uuid4()),
                        recipient_type="EMAIL",
                        recipient_id="alerts@example.com"
                    )
                ]
            ),
            WorkflowAction(
                id=str(uuid.uuid4()),
                action_type="API_CALL",
                parameters={
                    "url": "https://api.example.com/webhook",
                    "method": "POST",
                    "headers": {"Content-Type": "application/json", "X-API-Key": "secret_key"},
                    "body_template": "complex_api_template"
                }
            ),
            WorkflowAction(
                id=str(uuid.uuid4()),
                action_type="RECORD_AUDIT",
                parameters={
                    "audit_level": "CRITICAL",
                    "audit_message": "Complex operation completed",
                    "include_payload": True
                }
            )
        ]
    }
    
    return workflows


@pytest.fixture
def mock_workflow_engine(workflow_definitions):
    """Create a workflow engine with pre-loaded workflow definitions."""
    engine = WorkflowEngine()
    
    # Mock the _find_matching_workflows method to return the predefined workflows
    async def mock_find_matching_workflows(event):
        if event.event_type == "entity_created":
            return [workflow_definitions["simple_workflow"]]
        elif event.event_type == "entity_updated":
            return [workflow_definitions["medium_workflow"]]
        elif event.event_type == "complex_operation":
            return [workflow_definitions["complex_workflow"]]
        return []
    
    engine._find_matching_workflows = mock_find_matching_workflows
    
    # Mock action execution to avoid actual side effects
    async def mock_execute_actions(workflow, event, matching_conditions):
        # Just count the actions that would be executed
        return len(workflow.actions)
    
    engine._execute_actions = mock_execute_actions
    
    # Mock query match condition to avoid actual database queries
    async def mock_handle_query_match_condition(condition, event):
        # For benchmark purposes, simulate a query match for complex workflows
        return condition.value == "complex_query_id_123"
    
    engine._handle_query_match_condition = mock_handle_query_match_condition
    
    return engine


# Benchmarks
@pytest.mark.asyncio
async def test_workflow_event_processing_simple(mock_workflow_engine, event_data, benchmark):
    """Benchmark the performance of processing simple events with simple workflows."""
    event = event_data["small_event"]
    
    # Define the benchmark function
    async def process_simple_event():
        return await mock_workflow_engine.process_event(event)
    
    # Run the benchmark
    result = await benchmark.pedantic(
        process_simple_event,
        iterations=1,
        rounds=100
    )
    
    # Verify result for debugging
    assert result is not None


@pytest.mark.asyncio
async def test_workflow_event_processing_medium(mock_workflow_engine, event_data, benchmark):
    """Benchmark the performance of processing medium complexity events with medium workflows."""
    event = event_data["medium_event"]
    
    # Define the benchmark function
    async def process_medium_event():
        return await mock_workflow_engine.process_event(event)
    
    # Run the benchmark
    result = await benchmark.pedantic(
        process_medium_event,
        iterations=1,
        rounds=100
    )
    
    # Verify result for debugging
    assert result is not None


@pytest.mark.asyncio
async def test_workflow_event_processing_complex(mock_workflow_engine, event_data, benchmark):
    """Benchmark the performance of processing complex events with complex workflows."""
    event = event_data["large_event"]
    
    # Define the benchmark function
    async def process_complex_event():
        return await mock_workflow_engine.process_event(event)
    
    # Run the benchmark
    result = await benchmark.pedantic(
        process_complex_event,
        iterations=1,
        rounds=100
    )
    
    # Verify result for debugging
    assert result is not None


@pytest.mark.asyncio
async def test_condition_evaluation_performance(mock_workflow_engine, workflow_definitions, event_data, benchmark):
    """Benchmark the performance of evaluating conditions of different complexities."""
    # Get workflows with different condition complexities
    simple_workflow = workflow_definitions["simple_workflow"]
    medium_workflow = workflow_definitions["medium_workflow"]
    complex_workflow = workflow_definitions["complex_workflow"]
    
    # Map events to workflows
    workflow_event_pairs = [
        (simple_workflow, event_data["small_event"]),
        (medium_workflow, event_data["medium_event"]),
        (complex_workflow, event_data["large_event"])
    ]
    
    results = {}
    
    for workflow, event in workflow_event_pairs:
        workflow_name = workflow.name
        
        # Define benchmark function for this workflow
        async def evaluate_conditions():
            return await mock_workflow_engine._evaluate_conditions(workflow.conditions, event)
        
        # Run benchmark
        result = await benchmark.pedantic(
            evaluate_conditions,
            iterations=1,
            rounds=50,
            warmup_rounds=5
        )
        
        # Store results
        results[workflow_name] = result
    
    # Verify we have results for all workflows
    assert len(results) == 3


@pytest.mark.asyncio
async def test_action_execution_performance(mock_workflow_engine, workflow_definitions, event_data, benchmark):
    """Benchmark the performance of executing actions of different complexities."""
    # Get workflows with different action complexities
    simple_workflow = workflow_definitions["simple_workflow"]
    medium_workflow = workflow_definitions["medium_workflow"]
    complex_workflow = workflow_definitions["complex_workflow"]
    
    # Map events to workflows
    workflow_event_pairs = [
        (simple_workflow, event_data["small_event"]),
        (medium_workflow, event_data["medium_event"]),
        (complex_workflow, event_data["large_event"])
    ]
    
    results = {}
    
    for workflow, event in workflow_event_pairs:
        workflow_name = workflow.name
        # Mock matching conditions - assume all conditions matched
        matching_conditions = workflow.conditions
        
        # Define benchmark function for this workflow
        async def execute_actions():
            return await mock_workflow_engine._execute_actions(workflow, event, matching_conditions)
        
        # Run benchmark
        result = await benchmark.pedantic(
            execute_actions,
            iterations=1,
            rounds=50,
            warmup_rounds=5
        )
        
        # Store results
        results[workflow_name] = result
    
    # Verify we have results for all workflows
    assert len(results) == 3


@pytest.mark.asyncio
async def test_field_path_resolution_performance(mock_workflow_engine, event_data, benchmark):
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
        result = benchmark.pedantic(
            resolve_field_path,
            iterations=100,
            rounds=10
        )
        
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
        event_data["small_event"]
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
        result = await benchmark.pedantic(
            process_event_batch,
            iterations=1,
            rounds=20
        )
        
        # Store results
        results[f"batch_size_{batch_size}"] = result
    
    # Verify we have results for all batch sizes
    assert len(results) == len(batch_sizes)


@pytest.mark.asyncio
async def test_recipient_resolution_performance(mock_workflow_engine, workflow_definitions, benchmark):
    """Benchmark the performance of resolving different types and numbers of recipients."""
    # Extract recipients from different workflows
    simple_recipients = workflow_definitions["simple_workflow"].actions[0].recipients  # 1 user
    medium_recipients = workflow_definitions["medium_workflow"].actions[0].recipients  # 1 user, 1 role
    complex_recipients = workflow_definitions["complex_workflow"].actions[0].recipients  # 1 user, 1 role, 1 group
    
    # Create a mock recipient resolution method
    async def mock_resolve_recipients(recipients):
        resolved_users = []
        
        for recipient in recipients:
            if recipient.recipient_type == "USER":
                resolved_users.append(f"user_{recipient.recipient_id}")
            elif recipient.recipient_type == "ROLE":
                # Simulate resolving a role to multiple users
                resolved_users.extend([f"role_user_{i}" for i in range(5)])
            elif recipient.recipient_type == "GROUP":
                # Simulate resolving a group to multiple users
                resolved_users.extend([f"group_user_{i}" for i in range(10)])
            elif recipient.recipient_type == "EMAIL":
                # Direct email doesn't need resolution
                resolved_users.append(recipient.recipient_id)
        
        return resolved_users
    
    # Add the mock method to the engine for testing
    mock_workflow_engine._resolve_recipients = mock_resolve_recipients
    
    recipient_sets = [
        ("simple", simple_recipients),
        ("medium", medium_recipients),
        ("complex", complex_recipients)
    ]
    
    results = {}
    
    for name, recipients in recipient_sets:
        # Define benchmark function
        async def resolve_recipients_benchmark():
            return await mock_workflow_engine._resolve_recipients(recipients)
        
        # Run benchmark
        result = await benchmark.pedantic(
            resolve_recipients_benchmark,
            iterations=1,
            rounds=50
        )
        
        # Store results
        results[name] = result
    
    # Verify we have results for all recipient sets
    assert len(results) == len(recipient_sets)