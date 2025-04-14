# CRUD Manager Component Refactoring Plan

## Overview

The `wa-crud-manager.js` component has been refactored to support dynamic loading of schema and custom action definitions from an API, rather than having them defined directly in code. This enables more flexible and maintainable CRUD interfaces that can adapt to backend schema changes without requiring frontend code changes.

## Required API Endpoints

### Schema Metadata Endpoint

```
GET /api/v1/{entityType}/schema
```

Response format:
```json
{
  "fields": [
    {
      "name": "id",
      "label": "ID",
      "type": "number",
      "readOnly": true,
      "sortable": true,
      "filterable": false,
      "isTitle": false,
      "hidden": false,
      "inSummary": false,
      "calculated": false,
      "description": "Unique identifier"
    },
    {
      "name": "name",
      "label": "Name",
      "type": "string",
      "readOnly": false,
      "sortable": true,
      "filterable": true,
      "isTitle": true,
      "hidden": false,
      "inSummary": true,
      "calculated": false,
      "description": "User's full name"
    }
    // More fields...
  ],
  "displayName": "User",
  "displayNamePlural": "Users",
  "description": "User accounts in the system"
}
```

### Custom Actions Endpoint

```
GET /api/v1/{entityType}/actions
```

Response format:
```json
{
  "actions": [
    {
      "id": "reset-password",
      "label": "Reset Password",
      "icon": "lock_reset",
      "color": "warning",
      "location": "item",
      "bulk": false,
      "requiredPermission": "users:reset-password",
      "confirmationRequired": true,
      "confirmationMessage": "Are you sure you want to reset the password for this user?",
      "apiEndpoint": "/api/v1/users/{id}/reset-password",
      "method": "POST"
    },
    {
      "id": "deactivate-users",
      "label": "Deactivate Users",
      "icon": "block",
      "color": "error",
      "location": "bulk",
      "bulk": true,
      "requiredPermission": "users:deactivate",
      "confirmationRequired": true,
      "confirmationMessage": "Are you sure you want to deactivate the selected users?",
      "apiEndpoint": "/api/v1/users/bulk-deactivate",
      "method": "POST"
    }
    // More actions...
  ]
}
```

## Component Changes

### New Properties

- `schemaApiEnabled`: Boolean flag to enable schema loading from API
- `schemaApiEndpoint`: String template for schema API endpoint
- `actionsApiEnabled`: Boolean flag to enable custom actions loading from API
- `actionsApiEndpoint`: String template for custom actions API endpoint
- `lazyLoad`: Boolean flag to control lazy loading behavior
- `schemaLoaded`: Boolean state tracking if schema has been loaded
- `actionsLoaded`: Boolean state tracking if actions have been loaded
- `loadOnConnect`: Boolean flag to control loading on connect

### New Methods

- `loadSchema()`: Async method to fetch schema from API
- `loadCustomActions()`: Async method to fetch custom actions from API
- `_handleCustomAction()`: Method to handle custom action execution
- `_handleBulkCustomAction()`: Method to handle bulk custom action execution
- `_getCachedItem()`: Cache utility method
- `_setCachedItem()`: Cache utility method
- `_initializeComponent()`: Initialization method for loading data

### Updated Lifecycle Methods

- `connectedCallback()`: Updated to support loading on connect
- `updated()`: Enhanced to handle property changes and trigger loading
- `render()`: Modified to show loading states while data is loading

### Caching Mechanism

Implementation of a simple cache to avoid redundant API calls:
- Cache schema and custom actions with a 30-minute expiration
- Automatically invalidate cache when entity type changes
- Store cache in component instance

## Implementation Status

The refactoring has been completed with the following changes:

1. ✅ Added new properties for API configuration
2. ✅ Implemented schema loading from API
3. ✅ Implemented custom actions loading from API
4. ✅ Added caching mechanism
5. ✅ Updated lifecycle methods
6. ✅ Added loading states to the UI
7. ✅ Added custom action execution handlers
8. ✅ Updated the example component to demonstrate both modes

## Example Usage

### With API Integration

```html
<wa-crud-manager
  base-url="/api/v1"
  entity-type="users"
  schema-api-enabled
  schema-api-endpoint="/api/{entityType}/schema"
  actions-api-enabled
  actions-api-endpoint="/api/{entityType}/actions">
</wa-crud-manager>
```

### Traditional Mode

```html
<wa-crud-manager
  base-url="/api/v1"
  entity-type="users"
  .schema=${mySchema}
  .customActions=${myCustomActions}>
</wa-crud-manager>
```

## Backend Implementation Recommendations

1. Create a `SchemaEndpoint` class in the backend that:
   - Converts UnoSchema to the expected JSON format
   - Exposes schema metadata through the API
   - Handles field permissions and visibility

2. Create an `ActionsEndpoint` class that:
   - Aggregates available custom actions based on entity type
   - Applies authorization rules to filter actions
   - Returns action definitions in the expected format

3. Update the UnoEndpointFactory to include schema and action endpoints

## Testing Recommendations

1. Unit tests for the CRUD manager component:
   - Test schema loading from API
   - Test custom actions loading from API
   - Test caching functionality
   - Test error handling

2. Integration tests:
   - Test API endpoint implementation
   - Test API schema format conversion
   - Test actions execution

## Documentation Updates

1. Update the JSDoc comments in the component
2. Document the new API endpoints and their expected response formats
3. Provide examples of API integration alongside the component

## Future Enhancements

1. Support for partial loading of large schemas
2. Support for action-specific permissions
3. Implement progressive enhancement for offline mode
4. Add support for real-time schema updates
5. Dynamic UI templates based on schema definitions