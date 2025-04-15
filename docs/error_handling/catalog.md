# Error Catalog

The Error Catalog is a central registry of all error codes used in uno. It provides metadata for each error code, including error messages, categories, severity levels, and HTTP status codes.

## Core Concepts

- **Error Code**: A unique identifier for an error (e.g., "DB-0001")
- **Message Template**: A template for error messages with this code
- **Category**: The category of the error (validation, authorization, etc.)
- **Severity**: The severity level of the error (info, warning, error, critical, fatal)
- **Description**: A detailed description of what the error means
- **HTTP Status Code**: The HTTP status code associated with this error
- **Retry Allowed**: Whether retry is allowed for this error

## Standard Error Codes

### Core Error Codes

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

### Database Error Codes

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| DB-0001 | Database connection error: {message} | DATABASE | CRITICAL | 503 | Failed to connect to the database |
| DB-0002 | Database query error: {message} | DATABASE | ERROR | 500 | Error executing database query |
| DB-0003 | Database integrity error: {message} | DATABASE | ERROR | 409 | Database integrity constraint violation |
| DB-0004 | Database transaction error: {message} | DATABASE | ERROR | 500 | Error in database transaction |
| DB-0005 | Database deadlock error: {message} | DATABASE | ERROR | 409 | Database deadlock detected |

### API Error Codes

| Code | Message Template | Category | Severity | HTTP Status | Description |
|------|-----------------|----------|----------|-------------|-------------|
| API-0001 | API request error: {message} | INTEGRATION | ERROR | 400 | Error in API request |
| API-0002 | API response error: {message} | INTEGRATION | ERROR | 502 | Error in API response |
| API-0003 | API rate limit error: {message} | INTEGRATION | ERROR | 429 | API rate limit exceeded |
| API-0004 | API integration error: {message} | INTEGRATION | ERROR | 502 | Error integrating with external API |

## Registering Custom Error Codes

You can register custom error codes for your application using the `register_error` function:

```python
from uno.core.errors import register_error, ErrorCategory, ErrorSeverity

register_error(```

code="USER-0001",
message_template="User validation error: {message}",
category=ErrorCategory.VALIDATION,
severity=ErrorSeverity.ERROR,
description="Error validating user data",
http_status_code=400,
retry_allowed=True
```
)
```

## Working with Error Codes

### Checking if an Error Code is Valid

```python
from uno.core.errors import ErrorCode

if ErrorCode.is_valid("DB-0001"):```

print("Valid error code")
```
```

### Getting HTTP Status Code for an Error Code

```python
from uno.core.errors import ErrorCode

status_code = ErrorCode.get_http_status("DB-0001")
print(f"HTTP status code: {status_code}")  # HTTP status code: 503
```

### Getting Error Code Information

```python
from uno.core.errors import get_error_code_info

info = get_error_code_info("DB-0001")
if info:```

print(f"Message template: {info.message_template}")
print(f"Category: {info.category}")
print(f"Severity: {info.severity}")
print(f"HTTP status code: {info.http_status_code}")
```
```

### Getting All Error Codes

```python
from uno.core.errors import get_all_error_codes

all_codes = get_all_error_codes()
for info in all_codes:```

print(f"{info.code}: {info.description}")
```
```

## Best Practices

1. **Use consistent error codes**: Follow the pattern `DOMAIN-NNNN` (e.g., "DB-0001", "USER-0001")
2. **Provide meaningful message templates**: Include placeholders for dynamic parts of the message
3. **Categorize errors appropriately**: Use appropriate categories to help with error handling
4. **Set severity levels correctly**: This helps prioritize error handling
5. **Include HTTP status codes for API errors**: This ensures consistent HTTP responses
6. **Document all error codes**: Keep a catalog of all error codes for reference
7. **Initialize the catalog at application startup**: Call `ErrorCatalog.initialize()` during startup