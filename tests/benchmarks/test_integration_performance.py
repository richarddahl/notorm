import pytest
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.uno.attributes.services import AttributeTypeService, AttributeService
from src.uno.values.services import TextValueService, NumericValueService
from src.uno.authorization.services import UserService, RoleService, PermissionService
from src.uno.queries.executor import QueryExecutor
from src.uno.queries.filter_manager import UnoFilterManager
from src.uno.workflows.engine import WorkflowEngine
from src.uno.domain.events import DomainEvent


# Test fixtures for integration tests
@pytest.fixture
def integration_environment(request):
    """Create a comprehensive test environment with data across multiple modules."""
    # This would typically set up a complete environment with:
    # - Users, roles, permissions
    # - Attribute types and attributes
    # - Values of different types
    # - Queries and filters
    # - Workflows and triggers
    
    # For benchmark purposes, we'll simulate this with a dictionary
    # of mock objects and data that our tests can use
    return {
        "users": [
            {"id": f"user_{i}", "username": f"test_user_{i}", "email": f"user_{i}@example.com"}
            for i in range(100)
        ],
        "roles": [
            {"id": f"role_{i}", "name": f"Test Role {i}", "description": f"Role description {i}"}
            for i in range(10)
        ],
        "permissions": [
            {"id": f"perm_{i}", "name": f"test.permission.{i}", "description": f"Permission {i}"}
            for i in range(50)
        ],
        "attribute_types": [
            {"id": f"attr_type_{i}", "name": f"Test Type {i}", "description": f"Type description {i}"}
            for i in range(20)
        ],
        "attributes": [
            {
                "id": f"attr_{i}", 
                "name": f"Test Attribute {i}", 
                "attribute_type_id": f"attr_type_{i % 20}",
                "description": f"Attribute description {i}"
            }
            for i in range(200)
        ],
        "text_values": [
            {"id": f"text_val_{i}", "name": f"Text Value {i}", "value": f"Text content {i}"}
            for i in range(500)
        ],
        "numeric_values": [
            {"id": f"num_val_{i}", "name": f"Numeric Value {i}", "value": i * 10.5}
            for i in range(500)
        ],
        "queries": [
            {
                "id": f"query_{i}", 
                "name": f"Test Query {i}", 
                "description": f"Query description {i}",
                "query_path": f"test.path.{i % 10}"
            }
            for i in range(50)
        ],
        "workflows": [
            {
                "id": f"workflow_{i}", 
                "name": f"Test Workflow {i}", 
                "description": f"Workflow description {i}",
                "active": True
            }
            for i in range(25)
        ],
        "events": [
            DomainEvent(
                event_type=f"test.event.{i % 5}",
                payload={
                    "id": f"entity_{i}",
                    "name": f"Test Entity {i}",
                    "attributes": {k: f"value_{k}_{i}" for k in range(5)},
                    "metadata": {"created_at": datetime.now().isoformat()}
                },
                entity_type="test_entity",
                entity_id=f"entity_{i}",
                timestamp=datetime.now()
            )
            for i in range(100)
        ]
    }


# Mock services for integration testing
@pytest.fixture
def mock_services():
    """Create mock services for integration testing."""
    
    class MockUserService:
        async def get_user_with_roles(self, user_id):
            return {"id": user_id, "roles": [f"role_{i}" for i in range(3)]}
            
        async def get_user_permissions(self, user_id):
            return [f"perm_{i}" for i in range(10)]
    
    class MockAttributeService:
        async def get_attributes_by_type(self, type_id, limit=50):
            return [
                {"id": f"attr_{i}", "name": f"Attr {i}", "attribute_type_id": type_id}
                for i in range(limit)
            ]
            
        async def get_attribute_with_values(self, attr_id):
            return {
                "id": attr_id,
                "name": f"Attribute {attr_id}",
                "values": [
                    {"id": f"val_{i}", "name": f"Value {i}", "value": f"Content {i}"}
                    for i in range(10)
                ]
            }
    
    class MockQueryExecutor:
        async def execute_query(self, query_id, params=None):
            return [
                {"id": f"result_{i}", "name": f"Result {i}"}
                for i in range(20)
            ]
            
        async def match_entity(self, query_id, entity):
            # Simulate some processing
            await asyncio.sleep(0.001)
            return query_id.endswith(str(hash(entity["id"]) % 10))
    
    class MockWorkflowEngine:
        async def process_event(self, event):
            # Simulate event processing
            await asyncio.sleep(0.002)
            matched_workflows = [f"workflow_{i}" for i in range(5) if i % 3 == 0]
            return {"matched_workflows": matched_workflows, "actions_executed": len(matched_workflows) * 2}
    
    return {
        "user_service": MockUserService(),
        "attribute_service": MockAttributeService(),
        "query_executor": MockQueryExecutor(),
        "workflow_engine": MockWorkflowEngine()
    }


# Integration benchmarks
@pytest.mark.asyncio
async def test_user_attribute_values_lookup(mock_services, integration_environment, benchmark):
    """
    Benchmark an end-to-end flow: 
    1. Get a user
    2. Get user's permissions
    3. Find attributes they can access
    4. Load attribute values
    """
    user_service = mock_services["user_service"]
    attribute_service = mock_services["attribute_service"]
    
    users = integration_environment["users"]
    
    async def user_attribute_lookup():
        # 1. Select a random user
        user_id = users[hash(datetime.now().microsecond) % len(users)]["id"]
        
        # 2. Get user's permissions
        permissions = await user_service.get_user_permissions(user_id)
        
        # 3. Find attributes they can access (simulate permission check)
        accessible_attr_types = [
            integration_environment["attribute_types"][i]["id"]
            for i in range(len(integration_environment["attribute_types"]))
            if f"perm_{i % 10}" in permissions
        ]
        
        # 4. For each attribute type, get attributes
        attribute_results = {}
        for attr_type_id in accessible_attr_types[:3]:  # Limit to 3 for benchmark
            attributes = await attribute_service.get_attributes_by_type(attr_type_id, limit=10)
            
            # 5. For each attribute, get values
            for attr in attributes[:2]:  # Limit to 2 for benchmark
                attr_with_values = await attribute_service.get_attribute_with_values(attr["id"])
                attribute_results[attr["id"]] = attr_with_values
                
        return {
            "user_id": user_id,
            "accessible_types": len(accessible_attr_types),
            "attributes_loaded": len(attribute_results)
        }
    
    # Run the benchmark
    result = await benchmark.pedantic(
        user_attribute_lookup,
        iterations=1,
        rounds=50
    )
    
    # Verify we got results
    assert "user_id" in result
    assert "attributes_loaded" in result


@pytest.mark.asyncio
async def test_query_workflow_trigger_flow(mock_services, integration_environment, benchmark):
    """
    Benchmark a query-to-workflow flow:
    1. Execute a query to find entities
    2. For each entity, generate an event
    3. Process the events through the workflow engine
    """
    query_executor = mock_services["query_executor"]
    workflow_engine = mock_services["workflow_engine"]
    
    queries = integration_environment["queries"]
    
    async def query_workflow_flow():
        # 1. Select a random query
        query_id = queries[hash(datetime.now().microsecond) % len(queries)]["id"]
        
        # 2. Execute the query
        query_results = await query_executor.execute_query(query_id)
        
        # 3. For each result, generate an event
        events = []
        for result in query_results:
            event = DomainEvent(
                event_type="entity.updated",
                payload=result,
                entity_type="test_entity",
                entity_id=result["id"],
                timestamp=datetime.now()
            )
            events.append(event)
        
        # 4. Process events through workflow engine
        workflow_results = []
        for event in events[:5]:  # Limit to 5 for benchmark
            result = await workflow_engine.process_event(event)
            workflow_results.append(result)
            
        return {
            "query_id": query_id,
            "results_count": len(query_results),
            "events_processed": len(workflow_results),
            "workflows_executed": sum(r["actions_executed"] for r in workflow_results)
        }
    
    # Run the benchmark
    result = await benchmark.pedantic(
        query_workflow_flow,
        iterations=1,
        rounds=30
    )
    
    # Verify we got results
    assert "query_id" in result
    assert "events_processed" in result


@pytest.mark.asyncio
async def test_attribute_change_permission_flow(mock_services, integration_environment, benchmark):
    """
    Benchmark an attribute change with permission check flow:
    1. Get a user with roles
    2. Check permissions for attribute modification
    3. Update attribute values
    4. Generate an event for the change
    5. Process the event through the workflow engine
    """
    user_service = mock_services["user_service"]
    attribute_service = mock_services["attribute_service"]
    workflow_engine = mock_services["workflow_engine"]
    
    users = integration_environment["users"]
    attributes = integration_environment["attributes"]
    
    async def attribute_change_flow():
        # 1. Select a random user and attribute
        user_id = users[hash(datetime.now().microsecond) % len(users)]["id"]
        attr_id = attributes[hash(datetime.now().microsecond) % len(attributes)]["id"]
        
        # 2. Get user's roles and permissions
        user_with_roles = await user_service.get_user_with_roles(user_id)
        permissions = await user_service.get_user_permissions(user_id)
        
        # 3. Check if user has permission to modify the attribute (simulate check)
        has_permission = "perm_5" in permissions  # Arbitrary permission check
        
        # 4. If permitted, update attribute values
        result = {"user_id": user_id, "attribute_id": attr_id, "permitted": has_permission}
        
        if has_permission:
            # Get attribute with current values
            attr_with_values = await attribute_service.get_attribute_with_values(attr_id)
            
            # Simulate updating values
            new_values = [{"id": f"new_val_{i}", "value": f"New content {i}"} for i in range(3)]
            
            # 5. Generate change event
            event = DomainEvent(
                event_type="attribute.updated",
                payload={
                    "id": attr_id,
                    "previous_values": attr_with_values["values"],
                    "new_values": new_values,
                    "modified_by": user_id
                },
                entity_type="attribute",
                entity_id=attr_id,
                timestamp=datetime.now()
            )
            
            # 6. Process event through workflow engine
            workflow_result = await workflow_engine.process_event(event)
            result["workflows_triggered"] = len(workflow_result["matched_workflows"])
        
        return result
    
    # Run the benchmark
    result = await benchmark.pedantic(
        attribute_change_flow,
        iterations=1,
        rounds=40
    )
    
    # Verify we got results
    assert "user_id" in result
    assert "attribute_id" in result


@pytest.mark.asyncio
async def test_concurrency_integrated_operations(mock_services, integration_environment, benchmark):
    """
    Benchmark concurrent integrated operations:
    1. Multiple user permission checks
    2. Multiple attribute value lookups
    3. Multiple query executions
    4. Multiple workflow event processing
    All happening concurrently, simulating a busy system
    """
    user_service = mock_services["user_service"]
    attribute_service = mock_services["attribute_service"]
    query_executor = mock_services["query_executor"]
    workflow_engine = mock_services["workflow_engine"]
    
    users = integration_environment["users"]
    attributes = integration_environment["attributes"]
    queries = integration_environment["queries"]
    events = integration_environment["events"]
    
    async def concurrent_operations():
        # 1. Create tasks for user permission checks
        user_tasks = [
            user_service.get_user_permissions(users[i]["id"])
            for i in range(10)  # 10 concurrent user permission checks
        ]
        
        # 2. Create tasks for attribute value lookups
        attribute_tasks = [
            attribute_service.get_attribute_with_values(attributes[i]["id"])
            for i in range(15)  # 15 concurrent attribute lookups
        ]
        
        # 3. Create tasks for query executions
        query_tasks = [
            query_executor.execute_query(queries[i]["id"])
            for i in range(5)  # 5 concurrent query executions
        ]
        
        # 4. Create tasks for workflow event processing
        workflow_tasks = [
            workflow_engine.process_event(events[i])
            for i in range(8)  # 8 concurrent event processing
        ]
        
        # Execute all tasks concurrently
        user_results = await asyncio.gather(*user_tasks)
        attribute_results = await asyncio.gather(*attribute_tasks)
        query_results = await asyncio.gather(*query_tasks)
        workflow_results = await asyncio.gather(*workflow_tasks)
        
        # Return statistics
        return {
            "user_permissions_count": sum(len(perms) for perms in user_results),
            "attribute_values_count": sum(len(attr["values"]) for attr in attribute_results),
            "query_results_count": sum(len(results) for results in query_results),
            "workflow_actions_count": sum(result["actions_executed"] for result in workflow_results)
        }
    
    # Run the benchmark
    result = await benchmark.pedantic(
        concurrent_operations,
        iterations=1,
        rounds=20
    )
    
    # Verify we got results
    assert "user_permissions_count" in result
    assert "attribute_values_count" in result
    assert "query_results_count" in result
    assert "workflow_actions_count" in result


@pytest.mark.asyncio
async def test_complex_business_process_flow(mock_services, integration_environment, benchmark):
    """
    Benchmark a complex business process flow that touches multiple modules:
    1. User authentication and permission checks
    2. Attribute and value validation
    3. Query execution for business rules
    4. Workflow triggering based on results
    5. Cascading updates across related entities
    """
    user_service = mock_services["user_service"]
    attribute_service = mock_services["attribute_service"]
    query_executor = mock_services["query_executor"]
    workflow_engine = mock_services["workflow_engine"]
    
    users = integration_environment["users"]
    attributes = integration_environment["attributes"]
    queries = integration_environment["queries"]
    
    async def complex_business_process():
        # 1. Start with user authentication and permissions
        user_id = users[hash(datetime.now().microsecond) % len(users)]["id"]
        permissions = await user_service.get_user_permissions(user_id)
        
        if "perm_0" not in permissions:
            return {"status": "unauthorized", "user_id": user_id}
        
        # 2. Get attributes that define the business rules
        business_rule_attrs = []
        for i in range(3):  # Get 3 business rule attributes
            attr_id = attributes[i]["id"]
            attr_with_values = await attribute_service.get_attribute_with_values(attr_id)
            business_rule_attrs.append(attr_with_values)
        
        # 3. Execute queries based on business rules
        query_results = []
        for i in range(2):  # Execute 2 business rule queries
            query_id = queries[i]["id"]
            # Simulate params based on attribute values
            params = {
                f"param_{j}": business_rule_attrs[j % len(business_rule_attrs)]["values"][0]["value"]
                for j in range(3)
            }
            results = await query_executor.execute_query(query_id)
            query_results.extend(results)
        
        # 4. For each result, check if it matches other business rules
        matching_entities = []
        for entity in query_results[:5]:  # Limit to 5 for benchmark
            # Check against another business rule query
            validation_query_id = queries[2]["id"]
            is_match = await query_executor.match_entity(validation_query_id, entity)
            if is_match:
                matching_entities.append(entity)
        
        # 5. For each matching entity, trigger workflow
        workflow_results = []
        for entity in matching_entities:
            # Create a business process event
            event = DomainEvent(
                event_type="business.process.executed",
                payload={
                    "entity": entity,
                    "business_rules": [attr["id"] for attr in business_rule_attrs],
                    "validation_result": True,
                    "executed_by": user_id
                },
                entity_type="business_process",
                entity_id=f"process_{uuid.uuid4()}",
                timestamp=datetime.now()
            )
            
            # Process through workflow engine
            result = await workflow_engine.process_event(event)
            workflow_results.append(result)
        
        # 6. Simulate cascading updates to related entities
        related_updates = []
        for entity in matching_entities:
            # For each matching entity, update 2 related attributes
            for i in range(2):
                related_attr_id = attributes[(hash(entity["id"]) + i) % len(attributes)]["id"]
                related_attr = await attribute_service.get_attribute_with_values(related_attr_id)
                
                # Simulate update
                updated_values = [
                    {"id": v["id"], "value": f"Updated {v['value']}"}
                    for v in related_attr["values"][:2]  # Update first 2 values
                ]
                
                related_updates.append({
                    "attribute_id": related_attr_id,
                    "updated_values": len(updated_values)
                })
        
        # Return process summary
        return {
            "user_id": user_id,
            "business_rules_evaluated": len(business_rule_attrs),
            "entities_processed": len(query_results),
            "matching_entities": len(matching_entities),
            "workflows_triggered": len(workflow_results),
            "related_updates": len(related_updates),
            "total_value_updates": sum(u["updated_values"] for u in related_updates)
        }
    
    # Run the benchmark
    result = await benchmark.pedantic(
        complex_business_process,
        iterations=1,
        rounds=10
    )
    
    # Verify we got results
    assert "user_id" in result
    assert "business_rules_evaluated" in result
    assert "matching_entities" in result


@pytest.mark.asyncio
async def test_authorization_attribute_filtering_flow(mock_services, integration_environment, benchmark):
    """
    Benchmark the flow of applying authorization filters to attributes:
    1. Get user permissions
    2. Create filter conditions based on permissions
    3. Apply filters to attribute queries
    4. Validate filtered results against permission checks
    """
    user_service = mock_services["user_service"]
    attribute_service = mock_services["attribute_service"]
    query_executor = mock_services["query_executor"]
    
    users = integration_environment["users"]
    attribute_types = integration_environment["attribute_types"]
    
    async def authorization_filtering_flow():
        # 1. Select a user
        user_id = users[hash(datetime.now().microsecond) % len(users)]["id"]
        
        # 2. Get user permissions
        permissions = await user_service.get_user_permissions(user_id)
        
        # 3. Create filter conditions based on permissions
        # Simulate creating a filter manager with permission filters
        allowed_type_ids = [
            attribute_types[i]["id"]
            for i in range(len(attribute_types))
            if f"perm_{i % permissions[0]}" in permissions  # Use first permission as a mock filter
        ]
        
        # 4. Apply filters to get attributes
        filtered_attributes = []
        for type_id in allowed_type_ids[:3]:  # Limit to 3 types for benchmark
            attributes = await attribute_service.get_attributes_by_type(type_id, limit=5)
            filtered_attributes.extend(attributes)
        
        # 5. For each attribute, validate against a query (simulating a complex permission check)
        validation_query_id = integration_environment["queries"][0]["id"]
        validated_attributes = []
        
        for attr in filtered_attributes[:5]:  # Limit to 5 attributes for benchmark
            # Convert attribute to entity format for query matching
            attr_entity = {
                "id": attr["id"],
                "name": attr["name"],
                "type_id": attr["attribute_type_id"]
            }
            
            # Check if attribute passes the validation query
            is_valid = await query_executor.match_entity(validation_query_id, attr_entity)
            if is_valid:
                validated_attributes.append(attr)
        
        # Return results
        return {
            "user_id": user_id,
            "permission_count": len(permissions),
            "allowed_types": len(allowed_type_ids),
            "filtered_attributes": len(filtered_attributes),
            "validated_attributes": len(validated_attributes)
        }
    
    # Run the benchmark
    result = await benchmark.pedantic(
        authorization_filtering_flow,
        iterations=1,
        rounds=30
    )
    
    # Verify we got results
    assert "user_id" in result
    assert "permission_count" in result
    assert "validated_attributes" in result