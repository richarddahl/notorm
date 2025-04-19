# Logging Framework

The UNO Logging Framework provides a comprehensive solution for structured logging across your application with rich contextual information and integration with the error handling system.

## Overview

The logging framework is designed to provide:

- **Structured JSON logging**: All logs can be output in JSON format for easy parsing and integration with logging tools
- **Context propagation**: Logging context is maintained across async boundaries 
- **Error framework integration**: Seamless integration with the UNO error framework
- **HTTP request logging**: Middleware for automatic logging of HTTP requests and responses
- **Configurability**: Flexible configuration options for outputs, formats, and metadata

## Key Concepts

### Structured Logger

The `StructuredLogger` is the primary interface for logging. It wraps the standard Python logger with additional capabilities:

```python
from uno.core.logging import get_logger

logger = get_logger("my_module")
logger.info("This is an info message")
logger.error("This is an error", extra={"context": {"user_id": "123"}})
```

### Logging Context

Logging context provides additional information about the environment where a log was emitted. The context is maintained across async boundaries using `contextvars`.

```python
from uno.core.logging import add_context, get_context, clear_context

# Add context data
add_context(user_id="123", tenant_id="tenant-456")

# Get the current context
context = get_context()

# Clear the context
clear_context()
```

### Context Decorators

You can automatically add context using decorators:

```python
from uno.core.logging import with_logging_context

# Add function arguments to context
@with_logging_context
def process_user(user_id, action):
    # Both user_id and action will be in the logging context
    logger.info(f"Processing user action")

# Add static context
@with_logging_context(component="user_manager")
def create_user(user_data):
    # "component": "user_manager" will be in the context
    logger.info("Creating user")
```

### Error Integration

The logging framework integrates with the error framework:

```python
from uno.core.logging import log_error
from uno.core.errors.framework import ValidationError

try:
    # Some operation
    pass
except ValidationError as e:
    log_error(e)
```

## Configuration

Configure the logging system with `configure_logging()`:

```python
from uno.core.logging import configure_logging, LogConfig, LogLevel, LogFormat

# Using default configuration
configure_logging()

# Using custom configuration
config = LogConfig(
    level=LogLevel.DEBUG,
    format=LogFormat.JSON,
    console_output=True,
    file_output=True,
    file_path="/var/log/uno/app.log",
    service_name="my-service",
    environment="production"
)
configure_logging(config)

# From configuration provider
from uno.dependencies.service import get_config
config_provider = get_config()
log_config = LogConfig.from_config(config_provider)
configure_logging(log_config)
```

## HTTP Request Logging

The `LoggingMiddleware` logs HTTP requests and responses with context information:

```python
from fastapi import FastAPI
from uno.core.logging import LoggingMiddleware, get_logger

app = FastAPI()
logger = get_logger("http")

app.add_middleware(
    LoggingMiddleware,
    logger=logger,
    include_headers=True,
    include_query_params=True,
    exclude_paths=["/health", "/metrics"],
    sensitive_headers=["authorization", "cookie", "x-api-key"]
)
```

## Advanced Usage

### Binding Additional Context

You can create loggers with bound context:

```python
logger = get_logger("users")

# Create a new logger with bound context
user_logger = logger.bind(user_id="123", tenant_id="tenant-456")

# All log messages from user_logger will include the bound context
user_logger.info("User logged in")
```

### Logging in Middleware

Using logging in middleware to track request flow:

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from uno.core.logging import add_context, clear_context

class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate trace ID
        trace_id = str(uuid.uuid4())
        
        # Add to context
        add_context(trace_id=trace_id)
        
        # Add trace header to response
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_id
        
        # Clear context
        clear_context()
        
        return response
```

### Integration with Metrics

```python
from uno.core.logging import get_logger
from uno.core.monitoring.metrics import timed

logger = get_logger("performance")

@timed("process_data_operation")
async def process_data(data):
    logger.info("Processing data")
    # Operation is automatically timed and metrics collected
    # ...
```

## Best Practices

1. **Use structured logging**: Always prefer structured logs with context over string interpolation
2. **Be consistent with log levels**: Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
3. **Include relevant context**: Add user IDs, request IDs, and business context to logs
4. **Protect sensitive data**: Never log passwords, tokens, or personal information
5. **Use a naming convention**: Use consistent logger names (typically module name)
6. **Clear context when done**: Always clear context at the end of a request cycle

## Migration from Legacy Logging

If you're currently using the legacy logging module (`uno.core.errors.logging`), here's how to migrate:

```python
# Legacy usage
from uno.core.errors.logging import get_logger, with_logging_context

# New usage
from uno.core.logging import get_logger, with_logging_context
```

The new module maintains API compatibility while providing enhanced functionality.