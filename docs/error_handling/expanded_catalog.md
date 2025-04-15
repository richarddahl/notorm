# Expanded Error Catalog

This document provides a comprehensive catalog of error codes for all components of uno, expanding beyond the database-focused error codes to cover all application layers.

## Error Code Structure

All error codes in uno follow a consistent structure:

```
DOMAIN-NNNN
```

Where:
- `DOMAIN` is a short code identifying the component or domain (e.g., DB, API, AUTH)
- `NNNN` is a four-digit number starting from 0001

## Core Component Error Codes

### CORE: Core Framework Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| CORE-0001 | Unknown error occurred: {message} | INTERNAL | ERROR | 500 | An unexpected error occurred that doesn't match any known error type |
| CORE-0002 | Validation error: {message} | VALIDATION | ERROR | 400 | Input validation failed |
| CORE-0003 | Authorization error: {message} | AUTHORIZATION | ERROR | 403 | User does not have permission to perform the requested action |
| CORE-0004 | Authentication error: {message} | AUTHENTICATION | ERROR | 401 | User authentication failed |
| CORE-0005 | Resource not found: {resource} | RESOURCE | ERROR | 404 | The requested resource could not be found |
| CORE-0006 | Resource conflict: {message} | RESOURCE | ERROR | 409 | The request conflicts with the current state of the resource |
| CORE-0007 | Internal server error: {message} | INTERNAL | CRITICAL | 500 | An unexpected internal error occurred |
| CORE-0008 | Configuration error: {message} | CONFIGURATION | CRITICAL | 500 | System is improperly configured |
| CORE-0009 | Dependency error: {message} | INTERNAL | CRITICAL | 500 | A required dependency is unavailable |
| CORE-0010 | Timeout error: {message} | NETWORK | ERROR | 504 | Operation timed out |
| CORE-0011 | Serialization error: {message} | SERIALIZATION | ERROR | 400 | Failed to serialize or deserialize data |
| CORE-0012 | Rate limit exceeded: {message} | RESOURCE | ERROR | 429 | Application rate limit exceeded |
| CORE-0013 | Resource exhausted: {message} | RESOURCE | CRITICAL | 503 | Application is out of resources |
| CORE-0014 | Dependency cycle detected: {message} | DEPENDENCY | CRITICAL | 500 | Circular dependency detected |
| CORE-0015 | Startup failure: {message} | INITIALIZATION | FATAL | 500 | Failed to start application component |

### DI: Dependency Injection Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| DI-0001 | Service not registered: {service} | DEPENDENCY | CRITICAL | 500 | The requested service is not registered in the container |
| DI-0002 | Failed to resolve dependency: {dependency} | DEPENDENCY | CRITICAL | 500 | Unable to resolve a required dependency |
| DI-0003 | Invalid service registration: {message} | CONFIGURATION | CRITICAL | 500 | Service registration is invalid |
| DI-0004 | Scope resolution error: {message} | DEPENDENCY | ERROR | 500 | Error resolving service in current scope |
| DI-0005 | Circular dependency: {message} | DEPENDENCY | CRITICAL | 500 | Circular dependency detected in service resolution |

### SCHEMA: Schema Validation Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| SCHEMA-0001 | Schema validation error: {message} | VALIDATION | ERROR | 400 | General schema validation error |
| SCHEMA-0002 | Required field missing: {field} | VALIDATION | ERROR | 400 | A required field is missing |
| SCHEMA-0003 | Invalid field type: {field} expected {expected_type} | VALIDATION | ERROR | 400 | Field has invalid type |
| SCHEMA-0004 | Value out of range: {field} | VALIDATION | ERROR | 400 | Field value is outside allowed range |
| SCHEMA-0005 | Invalid pattern: {field} | VALIDATION | ERROR | 400 | Field value doesn't match required pattern |
| SCHEMA-0006 | Schema definition error: {message} | CONFIGURATION | ERROR | 500 | Error in schema definition |
| SCHEMA-0007 | Invalid enum value: {field} | VALIDATION | ERROR | 400 | Field value is not a valid enum value |
| SCHEMA-0008 | Length violation: {field} | VALIDATION | ERROR | 400 | Field length is invalid |
| SCHEMA-0009 | Relationship validation error: {message} | VALIDATION | ERROR | 400 | Error validating relationships |

### MODEL: Model Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| MODEL-0001 | Model validation error: {message} | VALIDATION | ERROR | 400 | Error validating model |
| MODEL-0002 | Invalid model state: {message} | VALIDATION | ERROR | 400 | Model is in invalid state |
| MODEL-0003 | Model type error: {message} | VALIDATION | ERROR | 400 | Type error in model definition |
| MODEL-0004 | Model relationship error: {message} | VALIDATION | ERROR | 400 | Error in model relationship |
| MODEL-0005 | Model field error: {message} | VALIDATION | ERROR | 400 | Field error in model |
| MODEL-0006 | Model constraint violation: {message} | VALIDATION | ERROR | 400 | Model constraint violation |
| MODEL-0007 | Model not found: {model} | RESOURCE | ERROR | 404 | Model definition not found |
| MODEL-0008 | Model definition error: {message} | CONFIGURATION | ERROR | 500 | Error in model definition |

### OBJ: UnoObj Business Logic Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| OBJ-0001 | Business rule violation: {message} | BUSINESS_RULE | ERROR | 400 | Business rule violated |
| OBJ-0002 | Invalid state transition: {message} | BUSINESS_RULE | ERROR | 400 | Invalid state transition |
| OBJ-0003 | Object validation error: {message} | VALIDATION | ERROR | 400 | Object validation failed |
| OBJ-0004 | Required field error: {message} | VALIDATION | ERROR | 400 | Required field missing or invalid |
| OBJ-0005 | Object relationship error: {message} | VALIDATION | ERROR | 400 | Error in object relationship |
| OBJ-0006 | Transaction boundary violation: {message} | BUSINESS_RULE | ERROR | 400 | Violation of transaction boundaries |
| OBJ-0007 | Object invariant violation: {message} | BUSINESS_RULE | ERROR | 400 | Object invariant violated |
| OBJ-0008 | Aggregate root constraint violation: {message} | BUSINESS_RULE | ERROR | 400 | Constraint violation in aggregate root |

### DOMAIN: Domain Model Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| DOMAIN-0001 | Domain validation error: {message} | BUSINESS_RULE | ERROR | 400 | Domain validation failed |
| DOMAIN-0002 | Entity not found: {entity_type} with id {entity_id} | RESOURCE | ERROR | 404 | Entity not found |
| DOMAIN-0003 | Aggregate root validation error: {message} | BUSINESS_RULE | ERROR | 400 | Aggregate root validation failed |
| DOMAIN-0004 | Value object validation error: {message} | BUSINESS_RULE | ERROR | 400 | Value object validation failed |
| DOMAIN-0005 | Domain invariant violation: {message} | BUSINESS_RULE | ERROR | 400 | Domain invariant violated |
| DOMAIN-0006 | Domain event error: {message} | EXECUTION | ERROR | 500 | Error handling domain event |
| DOMAIN-0007 | Command validation error: {message} | VALIDATION | ERROR | 400 | Command validation failed |
| DOMAIN-0008 | Query validation error: {message} | VALIDATION | ERROR | 400 | Query validation failed |

### REPO: Repository Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| REPO-0001 | Entity not found: {entity_type} with id {entity_id} | RESOURCE | ERROR | 404 | Entity not found in repository |
| REPO-0002 | Optimistic concurrency conflict: {message} | CONFLICT | ERROR | 409 | Optimistic concurrency conflict |
| REPO-0003 | Repository operation failed: {message} | EXECUTION | ERROR | 500 | General repository operation failure |
| REPO-0004 | Invalid query specification: {message} | VALIDATION | ERROR | 400 | Invalid query specification |
| REPO-0005 | Repository configuration error: {message} | CONFIGURATION | ERROR | 500 | Repository configuration error |
| REPO-0006 | Entity already exists: {entity_type} with id {entity_id} | CONFLICT | ERROR | 409 | Entity already exists |
| REPO-0007 | Batch operation error: {message} | EXECUTION | ERROR | 500 | Error during batch operation |
| REPO-0008 | Transaction error: {message} | EXECUTION | ERROR | 500 | Error during transaction |

### EVENT: Event Handling Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| EVENT-0001 | Event handling error: {message} | EXECUTION | ERROR | 500 | Error handling event |
| EVENT-0002 | Event not found: {event_type} | RESOURCE | ERROR | 404 | Event not found |
| EVENT-0003 | Event store error: {message} | EXECUTION | ERROR | 500 | Error accessing event store |
| EVENT-0004 | Event validation error: {message} | VALIDATION | ERROR | 400 | Event validation failed |
| EVENT-0005 | Event publishing error: {message} | EXECUTION | ERROR | 500 | Error publishing event |
| EVENT-0006 | Event serialization error: {message} | SERIALIZATION | ERROR | 500 | Error serializing/deserializing event |
| EVENT-0007 | Event subscription error: {message} | EXECUTION | ERROR | 500 | Error with event subscription |
| EVENT-0008 | Event sourcing error: {message} | EXECUTION | ERROR | 500 | Error during event sourcing |

### FILTER: Query Filter Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| FILTER-0001 | Filter error: {message} | FILTER | ERROR | 400 | Error in filter expression |
| FILTER-0002 | Invalid filter field: {field} | FILTER | ERROR | 400 | Invalid field in filter |
| FILTER-0003 | Invalid filter operator: {operator} | FILTER | ERROR | 400 | Invalid operator in filter |
| FILTER-0004 | Invalid filter value: {value} | FILTER | ERROR | 400 | Invalid value in filter |
| FILTER-0005 | Filter parsing error: {message} | FILTER | ERROR | 400 | Error parsing filter expression |
| FILTER-0006 | Filter combination error: {message} | FILTER | ERROR | 400 | Error combining filters |
| FILTER-0007 | Complex filter validation error: {message} | FILTER | ERROR | 400 | Error validating complex filter |
| FILTER-0008 | Filter security violation: {message} | SECURITY | ERROR | 403 | Security violation in filter |

### AUTH: Authentication and Authorization Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| AUTH-0001 | Authentication failed: {message} | AUTHENTICATION | ERROR | 401 | General authentication failure |
| AUTH-0002 | Invalid credentials: {message} | AUTHENTICATION | ERROR | 401 | Invalid credentials provided |
| AUTH-0003 | Token expired: {message} | AUTHENTICATION | ERROR | 401 | Authentication token expired |
| AUTH-0004 | Invalid token: {message} | AUTHENTICATION | ERROR | 401 | Invalid authentication token |
| AUTH-0005 | Authorization failed: {message} | AUTHORIZATION | ERROR | 403 | General authorization failure |
| AUTH-0006 | Insufficient permissions: {message} | AUTHORIZATION | ERROR | 403 | User lacks required permissions |
| AUTH-0007 | Role not found: {role} | RESOURCE | ERROR | 404 | Role not found |
| AUTH-0008 | Permission not found: {permission} | RESOURCE | ERROR | 404 | Permission not found |
| AUTH-0009 | User not found: {user_id} | RESOURCE | ERROR | 404 | User not found |
| AUTH-0010 | Account locked: {message} | SECURITY | ERROR | 403 | User account is locked |
| AUTH-0011 | Account disabled: {message} | SECURITY | ERROR | 403 | User account is disabled |
| AUTH-0012 | Password expired: {message} | SECURITY | ERROR | 403 | Password has expired |

### VECTOR: Vector Search Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| VECTOR-0001 | Embedding generation error: {message} | EXECUTION | ERROR | 500 | Error generating embeddings |
| VECTOR-0002 | Vector search error: {message} | EXECUTION | ERROR | 500 | Error during vector search |
| VECTOR-0003 | Vector index error: {message} | RESOURCE | ERROR | 500 | Error with vector index |
| VECTOR-0004 | Dimension mismatch: {message} | VALIDATION | ERROR | 400 | Vector dimension mismatch |
| VECTOR-0005 | Invalid vector operation: {message} | VALIDATION | ERROR | 400 | Invalid vector operation |
| VECTOR-0006 | Vector similarity calculation error: {message} | EXECUTION | ERROR | 500 | Error calculating vector similarity |
| VECTOR-0007 | Vector storage error: {message} | EXECUTION | ERROR | 500 | Error storing vector data |
| VECTOR-0008 | pgvector extension error: {message} | DEPENDENCY | ERROR | 500 | Error with pgvector extension |

### GRAPH: Graph Database Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| GRAPH-0001 | Graph query error: {message} | EXECUTION | ERROR | 500 | Error executing graph query |
| GRAPH-0002 | Node not found: {node_id} | RESOURCE | ERROR | 404 | Graph node not found |
| GRAPH-0003 | Edge not found: {edge_id} | RESOURCE | ERROR | 404 | Graph edge not found |
| GRAPH-0004 | Graph traversal error: {message} | EXECUTION | ERROR | 500 | Error during graph traversal |
| GRAPH-0005 | Invalid graph pattern: {message} | VALIDATION | ERROR | 400 | Invalid graph pattern |
| GRAPH-0006 | Graph synchronization error: {message} | EXECUTION | ERROR | 500 | Error synchronizing graph data |
| GRAPH-0007 | AGE extension error: {message} | DEPENDENCY | ERROR | 500 | Error with Apache AGE extension |
| GRAPH-0008 | Graph property validation error: {message} | VALIDATION | ERROR | 400 | Invalid graph property |

### CACHE: Caching Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| CACHE-0001 | Cache operation failed: {message} | EXECUTION | ERROR | 500 | General cache operation failure |
| CACHE-0002 | Cache key not found: {key} | RESOURCE | INFO | 404 | Cache key not found |
| CACHE-0003 | Cache provider error: {message} | DEPENDENCY | ERROR | 500 | Error with cache provider |
| CACHE-0004 | Cache serialization error: {message} | SERIALIZATION | ERROR | 500 | Error serializing/deserializing cache data |
| CACHE-0005 | Cache invalidation error: {message} | EXECUTION | ERROR | 500 | Error invalidating cache |
| CACHE-0006 | Cache configuration error: {message} | CONFIGURATION | ERROR | 500 | Cache configuration error |
| CACHE-0007 | Cache eviction error: {message} | EXECUTION | WARNING | 500 | Error evicting cache entries |
| CACHE-0008 | Cache size limit exceeded: {message} | RESOURCE | WARNING | 500 | Cache size limit exceeded |

### ASYNC: Asynchronous Processing Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| ASYNC-0001 | Task execution error: {message} | EXECUTION | ERROR | 500 | Error executing async task |
| ASYNC-0002 | Task timeout: {message} | NETWORK | ERROR | 504 | Async task timed out |
| ASYNC-0003 | Task cancellation: {message} | EXECUTION | INFO | 500 | Async task was cancelled |
| ASYNC-0004 | Task not found: {task_id} | RESOURCE | ERROR | 404 | Async task not found |
| ASYNC-0005 | Task queue full: {message} | RESOURCE | ERROR | 429 | Async task queue is full |
| ASYNC-0006 | Invalid task state: {message} | VALIDATION | ERROR | 400 | Invalid async task state |
| ASYNC-0007 | Task scheduling error: {message} | EXECUTION | ERROR | 500 | Error scheduling async task |
| ASYNC-0008 | Concurrency limit exceeded: {message} | RESOURCE | ERROR | 429 | Concurrency limit exceeded |

### REPORTS: Reporting Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| REPORT-0001 | Report generation error: {message} | EXECUTION | ERROR | 500 | Error generating report |
| REPORT-0002 | Report template not found: {template_id} | RESOURCE | ERROR | 404 | Report template not found |
| REPORT-0003 | Report parameter validation error: {message} | VALIDATION | ERROR | 400 | Invalid report parameter |
| REPORT-0004 | Report data access error: {message} | RESOURCE | ERROR | 500 | Error accessing report data |
| REPORT-0005 | Report rendering error: {message} | EXECUTION | ERROR | 500 | Error rendering report |
| REPORT-0006 | Report scheduling error: {message} | EXECUTION | ERROR | 500 | Error scheduling report |
| REPORT-0007 | Report export error: {message} | EXECUTION | ERROR | 500 | Error exporting report |
| REPORT-0008 | Report storage error: {message} | EXECUTION | ERROR | 500 | Error storing report |

### WORKFLOW: Workflow Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| WORKFLOW-0001 | Workflow execution error: {message} | EXECUTION | ERROR | 500 | Error executing workflow |
| WORKFLOW-0002 | Workflow definition not found: {workflow_id} | RESOURCE | ERROR | 404 | Workflow definition not found |
| WORKFLOW-0003 | Workflow step error: {message} | EXECUTION | ERROR | 500 | Error executing workflow step |
| WORKFLOW-0004 | Workflow transition error: {message} | EXECUTION | ERROR | 500 | Error transitioning workflow state |
| WORKFLOW-0005 | Workflow validation error: {message} | VALIDATION | ERROR | 400 | Invalid workflow definition |
| WORKFLOW-0006 | Workflow state validation error: {message} | VALIDATION | ERROR | 400 | Invalid workflow state |
| WORKFLOW-0007 | Workflow timeout: {message} | EXECUTION | ERROR | 504 | Workflow execution timed out |
| WORKFLOW-0008 | Workflow permission error: {message} | AUTHORIZATION | ERROR | 403 | Insufficient workflow permissions |

### MT: Multi-tenancy Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| MT-0001 | Tenant not found: {tenant_id} | RESOURCE | ERROR | 404 | Tenant not found |
| MT-0002 | Tenant creation error: {message} | EXECUTION | ERROR | 500 | Error creating tenant |
| MT-0003 | Tenant configuration error: {message} | CONFIGURATION | ERROR | 500 | Tenant configuration error |
| MT-0004 | Tenant access error: {message} | AUTHORIZATION | ERROR | 403 | Tenant access denied |
| MT-0005 | Tenant isolation error: {message} | SECURITY | ERROR | 500 | Tenant isolation violation |
| MT-0006 | Tenant limit exceeded: {message} | RESOURCE | ERROR | 429 | Tenant resource limit exceeded |
| MT-0007 | Tenant migration error: {message} | EXECUTION | ERROR | 500 | Error migrating tenant data |
| MT-0008 | Tenant data validation error: {message} | VALIDATION | ERROR | 400 | Invalid tenant data |

## Database Error Codes

### DB: Database Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| DB-0001 | Database connection error: {message} | DATABASE | CRITICAL | 503 | Failed to connect to the database |
| DB-0002 | Database query error: {message} | DATABASE | ERROR | 500 | Error executing database query |
| DB-0003 | Database integrity error: {message} | DATABASE | ERROR | 409 | Database integrity constraint violation |
| DB-0004 | Database transaction error: {message} | DATABASE | ERROR | 500 | Error in database transaction |
| DB-0005 | Database deadlock error: {message} | DATABASE | ERROR | 409 | Database deadlock detected |
| DB-0006 | Database schema error: {message} | DATABASE | ERROR | 500 | Error with database schema |
| DB-0007 | Database migration error: {message} | DATABASE | ERROR | 500 | Error during database migration |
| DB-0008 | Database timeout: {message} | DATABASE | ERROR | 504 | Database operation timed out |
| DB-0009 | Database permission error: {message} | DATABASE | ERROR | 403 | Insufficient database permissions |
| DB-0010 | Database resource limit: {message} | DATABASE | ERROR | 429 | Database resource limit exceeded |
| DB-0011 | Database configuration error: {message} | DATABASE | CRITICAL | 500 | Database configuration error |
| DB-0012 | Database connection pool error: {message} | DATABASE | CRITICAL | 500 | Connection pool error |
| DB-0013 | Database query limit exceeded: {message} | DATABASE | ERROR | 429 | Query limit exceeded |
| DB-0014 | Database data validation error: {message} | DATABASE | ERROR | 400 | Data validation failed at database level |
| DB-0015 | Database replication error: {message} | DATABASE | CRITICAL | 500 | Database replication error |

## API Error Codes

### API: API Errors

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| API-0001 | API request error: {message} | INTEGRATION | ERROR | 400 | Error in API request |
| API-0002 | API response error: {message} | INTEGRATION | ERROR | 502 | Error in API response |
| API-0003 | API rate limit error: {message} | INTEGRATION | ERROR | 429 | API rate limit exceeded |
| API-0004 | API integration error: {message} | INTEGRATION | ERROR | 502 | Error integrating with external API |
| API-0005 | API authentication error: {message} | INTEGRATION | ERROR | 401 | Error authenticating with external API |
| API-0006 | API timeout: {message} | INTEGRATION | ERROR | 504 | API request timed out |
| API-0007 | API validation error: {message} | VALIDATION | ERROR | 400 | API request validation failed |
| API-0008 | API resource not found: {resource} | RESOURCE | ERROR | 404 | API resource not found |
| API-0009 | API configuration error: {message} | CONFIGURATION | ERROR | 500 | API configuration error |
| API-0010 | API versioning error: {message} | COMPATIBILITY | ERROR | 400 | API version compatibility error |

## Registering Custom Error Codes

You can register custom error codes for your application using the `register_error` function:

```python
from uno.core.errors import register_error, ErrorCategory, ErrorSeverity

register_error(
    code="USER-0001",
    message_template="User validation error: {message}",
    category=ErrorCategory.VALIDATION,
    severity=ErrorSeverity.ERROR,
    description="Error validating user data",
    http_status_code=400,
    retry_allowed=True
)
```

## Best Practices for Custom Error Codes

1. **Use consistent naming**: Follow the established pattern of `DOMAIN-NNNN` 
2. **Choose appropriate categories**: Use the predefined error categories
3. **Set correct severity**: Match the severity to the impact of the error
4. **Provide descriptive templates**: Make error messages clear and actionable
5. **Include context parameters**: Design messages with placeholders for dynamic context
6. **Set appropriate HTTP status codes**: For errors that might reach API clients
7. **Document your error codes**: Maintain documentation for all custom error codes
8. **Register at application startup**: Initialize all error codes when the application starts

## Using Error Codes in Application Code

Use the predefined error codes from the ErrorCode class:

```python
from uno.core.errors import UnoError, ErrorCode

# Using predefined error codes
raise UnoError("User not found", ErrorCode.RESOURCE_NOT_FOUND, user_id=user_id)

# Using custom error codes
raise UnoError("Invalid profile data", "USER-0001", field="profile", value=data)
```

## See Also

- [Error Handling Overview](overview.md) - Core error handling concepts
- [Result Pattern](result.md) - Functional error handling
- [Error Monitoring](monitoring.md) - Monitoring and analyzing errors
- [Application Performance Monitoring](apm.md) - Error tracing with APM tools