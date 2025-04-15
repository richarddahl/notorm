# Structured Logging

The Uno framework provides a structured logging system that integrates with the error handling framework, allowing for consistent and contextual logging throughout the application.

## Core Concepts

- **Structured Logging**: Logs are structured as JSON objects with consistent fields
- **Context Propagation**: Logging context follows execution flow
- **Integration with Error Handling**: Error details are automatically included in logs
- **Consistent Formatting**: Standardized log format across the application

## Getting Started

### Configuring Logging

```python
from uno.core.errors import configure_logging, LogConfig

# Default configuration
configure_logging()

# Custom configuration
configure_logging(LogConfig(```

level="INFO",
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
date_format="%Y-%m-%d %H:%M:%S",
json_format=True,
console_output=True,
file_output=True,
file_path="/var/log/myapp.log",
backup_count=5,
max_bytes=10 * 1024 * 1024,  # 10 MB
include_logger_context=True,
include_exception_traceback=True
```
))
```

### Getting a Logger

```python
from uno.core.errors import get_logger

# Get a logger for the current module
logger = get_logger(__name__)
```

### Basic Logging

```python
# Basic logging
logger.info("User logged in")
logger.warning("Database connection slow")
logger.error("Failed to process request")
```

### Logging with Context

```python
from uno.core.errors import add_logging_context, get_logging_context

# Add context information
add_logging_context(user_id="user123", request_id="req456")

# Log with context
logger.info("User logged in")  # Will include user_id and request_id

# Get current context
context = get_logging_context()

# Clear context
clear_logging_context()
```

### Using Context Decorator

```python
from uno.core.errors import with_logging_context

@with_logging_context
def process_user(user_id, action):```

# The decorator adds user_id and action to the logging context
logger.info("Processing user")
# ...
```

# When called, the function parameters will be added to the context
process_user("user123", "update")
# Log: {"message": "Processing user", "function": "process_user", "args": {"user_id": "user123", "action": "update"}, ...}
```

### Logging Exceptions

```python
try:```

# Some operation that might fail
result = some_function()
```
except Exception as e:```

# The error will be logged with the full context and traceback
logger.exception("Failed to execute operation", exc_info=e)
```
```

### Structured JSON Logging

When `json_format=True`, logs will be formatted as JSON objects:

```python
configure_logging(LogConfig(json_format=True))
logger = get_logger(__name__)
add_logging_context(user_id="user123")

try:```

1 / 0
```
except Exception as e:```

logger.exception("Error", exc_info=e)
```
```

Will produce a log entry like:

```json
{
  "timestamp": "2023-06-01T12:34:56.789Z",
  "level": "ERROR",
  "logger": "my_module",
  "message": "Error",
  "module": "my_module",
  "function": "some_function",
  "line": 42,
  "context": {```

"user_id": "user123"
```
  },
  "exception": {```

"type": "ZeroDivisionError",
"message": "division by zero",
"traceback": "Traceback (most recent call last):\n  File \"app.py\", line 42, in some_function\n    1 / 0\nZeroDivisionError: division by zero"
```
  }
}
```

## Integration with Error Handling

The logging system integrates with the error framework to provide consistent error logging:

```python
from uno.core.errors import UnoError, ErrorCode, get_logger

logger = get_logger(__name__)

try:```

# Some operation that might fail
raise UnoError("User not found", ErrorCode.RESOURCE_NOT_FOUND, user_id="123")
```
except UnoError as e:```

# The error code, message, and context will be included in the log
logger.error(f"Operation failed: {e.message}", exc_info=e)
```
```

## Using Both Context Systems

The error context and logging context can be used together:

```python
from uno.core.errors import add_error_context, add_logging_context, with_error_context, with_logging_context

@with_error_context
@with_logging_context
def process_user(user_id, action):```

# Both decorators add context from parameters
``````

```
```

# Add more context
add_error_context(process_id="proc123")
add_logging_context(operation="update")
``````

```
```

# Both error and logging contexts are now available
logger.info("Processing user")
``````

```
```

try:```

# Some operation
if not user_exists(user_id):
    raise UnoError("User not found", "USER-0001", user_id=user_id)
```
except UnoError as e:```

# Error will include both contexts
logger.error(f"Failed to {action} user", exc_info=e)
raise
```
```
```

## Best Practices

1. **Configure logging at application startup**: Call `configure_logging()` early in your application lifecycle
2. **Use structured logging**: Enable JSON format for better log processing
3. **Add context information**: Use context decorators and functions to add relevant information
4. **Use appropriate log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
5. **Include exceptions**: Use `logger.exception()` or `exc_info` parameter to include exception details
6. **Be consistent**: Use the same logging pattern throughout your application
7. **Don't log sensitive information**: Be careful not to log passwords, tokens, or personal data
8. **Include request IDs**: Add request IDs to trace requests across services
9. **Use hierarchical loggers**: Use the module name as the logger name for better organization