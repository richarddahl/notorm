# Workflow System Custom Extensions

This guide explains how to extend the workflow system with custom components to meet specific business requirements beyond the built-in functionality.

## Extension Points

The workflow system supports three main extension points:

1. **Action Executors** - Define new types of actions (beyond notifications, emails, webhooks)
2. **Condition Evaluators** - Create custom condition logic (beyond field, time, role conditions)
3. **Recipient Resolvers** - Implement custom logic for determining notification recipients

## Prerequisites

Before creating custom extensions, ensure:

1. Basic familiarity with the workflow system concepts
2. Understanding of Python async programming (all extension interfaces use async methods)
3. Knowledge of dependency injection patterns used in the project

## Custom Action Executors

Action executors are responsible for performing specific actions when a workflow is triggered and its conditions are met.

### Action Executor Interface

All action executors must implement the `ActionExecutorBase` interface:

```python
from uno.workflows.executor import ActionExecutorBase, register_executor
from uno.core.errors.result import Result, Success, Failure
from typing import Dict, Any

class CustomActionExecutor(ActionExecutorBase):```

"""Custom action executor implementation."""
``````

```
```

async def execute(self, action: Dict[str, Any], context: Dict[str, Any]) -> Result[Dict[str, Any]]:```

"""
Execute the custom action.
``````

```
```

Args:
    action: The action configuration from the workflow definition
    context: The execution context containing entity data and metadata
    
Returns:
    Result with execution details on success or error information on failure
"""
try:
    # Extract configuration from the action
    config = action.get("config", {})```

```
```

# Extract data from the context
entity_data = context.get("entity_data", {})
```
    entity_id = context.get("entity_id")
    
    # Custom execution logic here
    # ...
    
    # Return success result with execution details
    return Success({
        "status": "success",
        "details": "Custom action executed successfully",
        # Additional result data...
    })
    
except Exception as e:
    # Return failure result with error details
    return Failure(str(e))
```
```
```

### Registering an Action Executor

Once you've implemented your custom action executor, register it with the workflow system:

```python
from uno.workflows.executor import register_executor

# Create an instance of your executor
custom_executor = CustomActionExecutor()

# Register it with a unique type name
register_executor("custom_action", custom_executor)
```

### Example: Integration with External CRM

Here's a complete example of an action executor that integrates with an external CRM system:

```python
import httpx
from uno.workflows.executor import ActionExecutorBase, register_executor
from uno.core.errors.result import Result, Success, Failure
from typing import Dict, Any
from pydantic import BaseSettings

class CrmSettings(BaseSettings):```

"""Settings for the CRM integration."""
crm_api_url: str
crm_api_key: str
``````

```
```

class Config:```

env_prefix = "CRM_"
```
```

class CrmActionExecutor(ActionExecutorBase):```

"""Action executor for CRM integration."""
``````

```
```

def __init__(self):```

"""Initialize with settings."""
self.settings = CrmSettings()
```
``````

```
```

async def execute(self, action: Dict[str, Any], context: Dict[str, Any]) -> Result[Dict[str, Any]]:```

"""Execute a CRM action."""
try:
    # Extract configuration
    config = action.get("config", {})
    crm_action = config.get("crm_action", "update_contact")
    
    # Extract entity data
    entity_data = context.get("entity_data", {})
    
    # Map entity data to CRM fields
    crm_data = {
        "contact_id": entity_data.get("id"),
        "email": entity_data.get("email"),
        "name": entity_data.get("name"),
        "status": config.get("status", "active")
    }
    
    # Make API request to CRM
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{self.settings.crm_api_url}/{crm_action}",
            json=crm_data,
            headers={"Authorization": f"Bearer {self.settings.crm_api_key}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return Success({
                "status": "success",
                "details": f"CRM action '{crm_action}' executed successfully",
                "crm_reference": result.get("reference_id")
            })
        else:
            return Failure(f"CRM API error: {response.status_code} - {response.text}")
        
except Exception as e:
    return Failure(f"CRM action error: {str(e)}")
```
```

# Register the executor
register_executor("crm", CrmActionExecutor())
```

## Custom Condition Evaluators

Condition evaluators determine whether a workflow should execute based on specific criteria.

### Condition Evaluator Interface

All condition evaluators must implement the `ConditionEvaluatorBase` interface:

```python
from uno.workflows.conditions import ConditionEvaluatorBase, register_evaluator
from typing import Dict, Any

class CustomConditionEvaluator(ConditionEvaluatorBase):```

"""Custom condition evaluator implementation."""
``````

```
```

async def evaluate(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:```

"""
Evaluate the custom condition.
``````

```
```

Args:
    condition: The condition configuration from the workflow definition
    context: The execution context containing entity data and metadata
    
Returns:
    Boolean indicating whether the condition is met
"""
# Extract configuration from the condition
config = condition.get("config", {})
``````

```
```

# Extract data from the context
entity_data = context.get("entity_data", {})
``````

```
```

# Custom evaluation logic here
# ...
``````

```
```

# Return True if condition is met, False otherwise
return True  # Replace with actual evaluation logic
```
```
```

### Registering a Condition Evaluator

Register your custom condition evaluator with the workflow system:

```python
from uno.workflows.conditions import register_evaluator

# Create an instance of your evaluator
custom_evaluator = CustomConditionEvaluator()

# Register it with a unique type name
register_evaluator("custom_condition", custom_evaluator)
```

### Example: Geo-Location Condition

Here's an example of a condition evaluator that checks whether an entity's location is within a specific geographic region:

```python
import math
from uno.workflows.conditions import ConditionEvaluatorBase, register_evaluator
from typing import Dict, Any, Tuple

class GeoLocationConditionEvaluator(ConditionEvaluatorBase):```

"""Evaluates if a location is within a specific radius of a point."""
``````

```
```

def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:```

"""Calculate distance between two points in kilometers using the Haversine formula."""
R = 6371  # Earth radius in kilometers
``````

```
```

dlat = math.radians(lat2 - lat1)
dlon = math.radians(lon2 - lon1)
a = (math.sin(dlat/2) * math.sin(dlat/2) +
     math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
     math.sin(dlon/2) * math.sin(dlon/2))
c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
distance = R * c
``````

```
```

return distance
```
``````

```
```

def _get_coordinates(self, data: Dict[str, Any], ```

                config: Dict[str, Any]) -> Tuple[float, float]:
"""Extract coordinates from entity data based on configuration."""
# Check if we have direct lat/lon fields
if config.get("lat_field") and config.get("lon_field"):
    lat = data.get(config["lat_field"])
    lon = data.get(config["lon_field"])
    if lat is not None and lon is not None:
        return float(lat), float(lon)
``````

```
```

# Check if we have a single location field with a specific format
if config.get("location_field"):
    location = data.get(config["location_field"])
    if location and isinstance(location, str) and "," in location:
        parts = location.split(",")
        if len(parts) == 2:
            try:
                return float(parts[0].strip()), float(parts[1].strip())
            except ValueError:
                pass
``````

```
```

# Default to center of the US if not found
return None, None
```
``````

```
```

async def evaluate(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:```

"""Evaluate if the entity location is within the specified radius."""
try:
    config = condition.get("config", {})
    entity_data = context.get("entity_data", {})
    
    # Get target coordinates
    target_lat = float(config.get("target_lat", 0))
    target_lon = float(config.get("target_lon", 0))
    radius_km = float(config.get("radius_km", 10))
    
    # Get entity coordinates
    entity_lat, entity_lon = self._get_coordinates(entity_data, config)
    
    # If coordinates couldn't be determined, condition fails
    if entity_lat is None or entity_lon is None:
        return False
    
    # Calculate distance
    distance = self._calculate_distance(
        entity_lat, entity_lon, target_lat, target_lon
    )
    
    # Check if within radius
    return distance <= radius_km
    
except Exception:
    # If any error occurs, the condition is not met
    return False
```
```

# Register the evaluator
register_evaluator("geo_location", GeoLocationConditionEvaluator())
```

## Custom Recipient Resolvers

Recipient resolvers determine who should receive notifications generated by workflow actions.

### Recipient Resolver Interface

All recipient resolvers must implement the `RecipientResolverBase` interface:

```python
from uno.workflows.recipients import RecipientResolverBase, register_resolver
from typing import Dict, Any, List

class CustomRecipientResolver(RecipientResolverBase):```

"""Custom recipient resolver implementation."""
``````

```
```

async def resolve(self, recipient: Dict[str, Any], context: Dict[str, Any]) -> List[str]:```

"""
Resolve recipients based on custom logic.
``````

```
```

Args:
    recipient: The recipient configuration from the workflow definition
    context: The execution context containing entity data and metadata
    
Returns:
    List of user IDs who should receive the notification
"""
# Extract configuration from the recipient
config = recipient.get("config", {})
value = recipient.get("value", "")
``````

```
```

# Extract data from the context
entity_data = context.get("entity_data", {})
``````

```
```

# Custom resolution logic here
# ...
``````

```
```

# Return list of user IDs
return ["user1", "user2"]  # Replace with actual resolution logic
```
```
```

### Registering a Recipient Resolver

Register your custom recipient resolver with the workflow system:

```python
from uno.workflows.recipients import register_resolver

# Create an instance of your resolver
custom_resolver = CustomRecipientResolver()

# Register it with a unique type name
register_resolver("custom_recipient", custom_resolver)
```

### Example: Team Hierarchy Resolver

Here's an example of a recipient resolver that notifies a user's manager and team members:

```python
import inject
from uno.workflows.recipients import RecipientResolverBase, register_resolver
from uno.dependencies.interfaces import UnoRepositoryProtocol
from typing import Dict, Any, List

class TeamRepository:```

"""Repository for team and organization structure."""
``````

```
```

async def get_manager_id(self, user_id: str) -> str:```

"""Get the manager ID for a user."""
# Implementation would query the database
pass
```
``````

```
```

async def get_team_members(self, user_id: str) -> List[str]:```

"""Get all team members for a user's team."""
# Implementation would query the database
pass
```
```

class TeamHierarchyResolver(RecipientResolverBase):```

"""Resolves recipients based on team hierarchy."""
``````

```
```

def __init__(self):```

"""Initialize with repository."""
self.team_repository = inject.instance(TeamRepository)
```
``````

```
```

async def resolve(self, recipient: Dict[str, Any], context: Dict[str, Any]) -> List[str]:```

"""Resolve recipients based on team hierarchy."""
try:
    value = recipient.get("value", "")
    config = recipient.get("config", {})
    entity_data = context.get("entity_data", {})
    
    # Get the user ID from the entity data
    user_id = entity_data.get("user_id") or entity_data.get("created_by_id")
    if not user_id:
        return []
        
    # Determine which hierarchy members to include
    include_manager = config.get("include_manager", True)
    include_team = config.get("include_team", False)
    
    recipients = []
    
    # Add manager if specified
    if include_manager:
        manager_id = await self.team_repository.get_manager_id(user_id)
        if manager_id:
            recipients.append(manager_id)
    
    # Add team members if specified
    if include_team:
        team_members = await self.team_repository.get_team_members(user_id)
        recipients.extend(team_members)
    
    # Ensure we don't have duplicates
    return list(set(recipients))
    
except Exception as e:
    # Log the error but return empty list to avoid breaking the workflow
    print(f"Error resolving team hierarchy recipients: {str(e)}")
    return []
```
```

# Register the resolver
register_resolver("team_hierarchy", TeamHierarchyResolver())
```

## Integration with WebAwesome UI

To make your custom extensions available in the visual workflow designer, you need to register them with the UI configuration.

### Registering UI Configurations

The workflow designer UI reads extension configurations from the API. You can extend these configurations by adding your custom components to the workflow service:

```python
from uno.workflows.provider import WorkflowService

# Patch the WorkflowService to include your custom extensions
original_get_action_types = WorkflowService.get_action_types

async def patched_get_action_types(self):```

"""Get available action types including custom ones."""
result = await original_get_action_types(self)
``````

```
```

if result.is_success:```

# Add your custom action type
result.value.append({
    "id": "crm",
    "label": "CRM Integration",
    "config_schema": {
        "crm_action": {
            "type": "string", 
            "required": True,
            "options": ["update_contact", "create_lead", "update_opportunity"]
        },
        "status": {
            "type": "string",
            "required": False,
            "default": "active"
        }
    },
    "requires_recipients": False
})
```
``````

```
```

return result
```

# Apply the patch
WorkflowService.get_action_types = patched_get_action_types
```

Similar patches can be applied for custom condition types and recipient types.

## Testing Custom Extensions

It's important to thoroughly test your custom extensions before deploying them.

### Unit Testing

Here's an example of unit testing a custom action executor:

```python
import pytest
from unittest.mock import AsyncMock, patch
from uno.core.errors.result import Success, Failure

from your_module import CrmActionExecutor

@pytest.fixture
def crm_executor():```

"""Create a CRM executor instance with mocked settings."""
with patch('your_module.CrmSettings') as MockSettings:```

mock_settings = MockSettings.return_value
mock_settings.crm_api_url = "https://api.example.com/crm"
mock_settings.crm_api_key = "fake-api-key"
``````

```
```

executor = CrmActionExecutor()
executor.settings = mock_settings
return executor
```
```

@pytest.mark.asyncio
async def test_crm_executor_success(crm_executor):```

"""Test successful CRM action execution."""
# Mock the HTTP client
with patch('httpx.AsyncClient') as MockClient:```

mock_client = AsyncMock()
MockClient.return_value.__aenter__.return_value = mock_client
``````

```
```

# Mock successful response
mock_response = AsyncMock()
mock_response.status_code = 200
mock_response.json.return_value = {"reference_id": "CRM-123"}
mock_client.post.return_value = mock_response
``````

```
```

# Test data
action = {
    "type": "crm",
    "config": {
        "crm_action": "update_contact",
        "status": "active"
    }
}
``````

```
```

context = {
    "entity_data": {
        "id": "user-123",
        "email": "user@example.com",
        "name": "Test User"
    },
    "entity_id": "user-123"
}
``````

```
```

# Execute and verify
result = await crm_executor.execute(action, context)
``````

```
```

assert isinstance(result, Success)
assert result.value["status"] == "success"
assert "CRM action 'update_contact' executed successfully" in result.value["details"]
assert result.value["crm_reference"] == "CRM-123"
``````

```
```

# Verify API call
mock_client.post.assert_called_once()
call_args = mock_client.post.call_args[0]
assert call_args[0] == "https://api.example.com/crm/update_contact"
```
```

@pytest.mark.asyncio
async def test_crm_executor_api_error(crm_executor):```

"""Test CRM action with API error."""
# Mock the HTTP client with error response
with patch('httpx.AsyncClient') as MockClient:```

mock_client = AsyncMock()
MockClient.return_value.__aenter__.return_value = mock_client
``````

```
```

# Mock failed response
mock_response = AsyncMock()
mock_response.status_code = 400
mock_response.text = "Invalid request"
mock_client.post.return_value = mock_response
``````

```
```

# Test data
action = {
    "type": "crm",
    "config": {
        "crm_action": "update_contact"
    }
}
``````

```
```

context = {
    "entity_data": {
        "id": "user-123"
    }
}
``````

```
```

# Execute and verify
result = await crm_executor.execute(action, context)
``````

```
```

assert isinstance(result, Failure)
assert "CRM API error: 400" in result.error
```
```
```

### Integration Testing

Integration testing should verify that your extensions work correctly with the entire workflow system:

```python
import pytest
from uno.workflows.engine import WorkflowEngine
from uno.workflows.executor import register_executor
from your_module import CrmActionExecutor

@pytest.fixture(scope="module")
def workflow_engine():```

"""Set up a workflow engine with custom extensions for testing."""
# Register your custom extensions
register_executor("crm", CrmActionExecutor())
``````

```
```

# Create and return a workflow engine
engine = WorkflowEngine()
return engine
```

@pytest.mark.asyncio
async def test_workflow_with_custom_action(workflow_engine):```

"""Test a workflow that uses a custom action."""
# Create a test workflow definition
workflow = {```

"id": "test-workflow",
"name": "Test Workflow",
"status": "active",
"trigger": {
    "entity_type": "user",
    "operations": ["create"]
},
"actions": [
    {
        "type": "crm",
        "config": {
            "crm_action": "create_contact"
        }
    }
]
```
}
``````

```
```

# Mock the execute method of the CRM executor
# [Add mocking code here]
``````

```
```

# Create test execution context
context = {```

"workflow": workflow,
"entity_type": "user",
"entity_id": "user-123",
"operation": "create",
"entity_data": {
    "id": "user-123",
    "name": "Test User",
    "email": "test@example.com"
}
```
}
``````

```
```

# Execute the workflow
result = await workflow_engine.execute(context)
``````

```
```

# Assert results
assert result.is_success
assert len(result.value["action_results"]) == 1
assert result.value["action_results"][0]["type"] == "crm"
assert result.value["action_results"][0]["status"] == "success"
```
```

## Deployment Considerations

When deploying custom extensions, consider the following:

1. **Registration Timing**: Ensure extensions are registered early in the application startup process
2. **Error Handling**: Implement robust error handling in extensions to avoid breaking workflows
3. **Logging**: Add detailed logging to help troubleshoot issues
4. **Performance**: Consider the performance impact, especially for extensions that call external APIs
5. **Configuration**: Use environment variables or configuration files for external integration settings

## Best Practices

Follow these best practices when creating custom extensions:

1. **Single Responsibility**: Each extension should do one thing well
2. **Error Isolation**: Extensions should handle their own errors without crashing the workflow
3. **Performance Awareness**: Consider the impact on workflow execution performance
4. **Security**: Be careful with sensitive data in extension logic
5. **Documentation**: Document your extensions thoroughly for other developers
6. **Testing**: Create comprehensive tests for your extensions
7. **UI Integration**: Make your extensions easily usable in the visual designer

## Conclusion

Custom extensions provide a powerful way to integrate the workflow system with external systems and implement specialized business logic. By following the patterns and interfaces described in this guide, you can extend the workflow system to meet your organization's specific needs.