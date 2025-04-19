# Tracing Integrations

This guide explains how to integrate the UNO tracing framework with other components of your application, including logging, metrics, error handling, HTTP requests, and database operations.

## Overview

The tracing framework is designed to work seamlessly with other UNO components, providing end-to-end visibility across your application. The integrations module provides ready-to-use utilities that connect tracing with:

- **Logging Framework**: Automatically include trace and span IDs in logs
- **Metrics Framework**: Collect metrics about traces and spans
- **Error Framework**: Add trace context to error information
- **HTTP Requests**: Trace incoming and outgoing HTTP requests
- **Database Operations**: Trace database queries and operations

## Logging Integration

Integrate tracing with the logging framework to include trace information in log messages:

```python
from uno.core.tracing import register_logging_integration

# Register the integration
register_logging_integration()

# Now all logs will include trace and span IDs when available
from uno.core.logging import get_logger
logger = get_logger("my_module")

# Logs will include trace_id, span_id, and parent_span_id when 
# executed within a traced context
logger.info("Processing request")
```

Example log output with trace information:
```json
{
  "timestamp": "2025-04-24T15:32:10.123456Z",
  "level": "INFO",
  "logger": "my_module",
  "message": "Processing request",
  "trace_id": "1234567890abcdef1234567890abcdef",
  "span_id": "abcdef1234567890",
  "parent_span_id": "9876543210fedcba"
}
```

## Metrics Integration

Collect metrics about your traces and spans:

```python
from uno.core.tracing import register_metrics_integration

# Register the integration
register_metrics_integration()
```

This integration automatically tracks:
- `tracing.spans.count`: Total number of spans created
- `tracing.spans.duration`: Histogram of span durations in milliseconds
- `tracing.spans.errors`: Count of spans with errors

These metrics can be viewed through your metrics dashboard or exported to Prometheus.

## Error Integration

Ensure errors include trace context:

```python
from uno.core.tracing import register_error_integration

# Register the integration
register_error_integration()

# Now when errors occur within a traced context, they will include trace information
from uno.core.errors import ValidationError

try:
    # Some operation within a traced context
    raise ValidationError("Invalid input")
except ValidationError as e:
    # The error will include trace_id and span_id
    pass
```

## HTTP Request Middleware

Add tracing to your FastAPI application:

```python
from fastapi import FastAPI
from uno.core.tracing import create_request_middleware

app = FastAPI()

# Create and add the middleware
middleware = create_request_middleware(
    app,
    excluded_paths=["/health", "/metrics"]
)
app.add_middleware(middleware)
```

This middleware:
1. Creates a span for each HTTP request
2. Extracts trace context from incoming request headers
3. Adds request information as span attributes (method, path, etc.)
4. Records response status code and timing
5. Adds the trace ID to response headers

## Database Integration

Trace database operations:

```python
from uno.core.tracing import create_database_integration
from sqlalchemy.ext.asyncio import AsyncSession

# Create the database tracing decorator
trace_db = create_database_integration()

# Apply to database operations
@trace_db
async def execute_query(session: AsyncSession, query: str, params: dict):
    return await session.execute(query, params)
```

The database integration:
1. Creates a span for each database operation
2. Records the query and parameters (safely truncated)
3. Measures execution time
4. Tracks row counts when available
5. Captures and records any database errors

## Combined Integration Example

Here's a complete example that sets up all integrations:

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.tracing import (
    configure_tracing,
    TracingConfig,
    register_logging_integration,
    register_metrics_integration,
    register_error_integration,
    create_request_middleware,
    create_database_integration,
    trace
)
from uno.core.logging import get_logger

# Configure tracing
config = TracingConfig(
    service_name="user-service",
    environment="production"
)
tracer = configure_tracing(config)

# Register all integrations
register_logging_integration(tracer)
register_metrics_integration(tracer)
register_error_integration(tracer)

# Set up the application
app = FastAPI()
app.add_middleware(create_request_middleware(app, tracer))

# Create database tracing
trace_db = create_database_integration(tracer)

# Get session dependency (example)
async def get_db_session():
    # ... create session ...
    yield session
    # ... close session ...

# Create a logger
logger = get_logger("user_service")

# Create a traced endpoint
@app.get("/users/{user_id}")
@trace(name="get_user_endpoint")
async def get_user(user_id: str, session: AsyncSession = Depends(get_db_session)):
    logger.info(f"Getting user: {user_id}")  # Will include trace ID
    
    # Traced database query
    @trace_db
    async def fetch_user(session, user_id):
        return await session.execute(
            "SELECT * FROM users WHERE id = :id", 
            {"id": user_id}
        )
    
    result = await fetch_user(session, user_id)
    user = result.first()
    
    if not user:
        logger.warning(f"User not found: {user_id}")  # Will include trace ID
        return {"error": "User not found"}
    
    return {"user": user}
```

## Custom Integrations

You can also create your own integrations with the tracing framework:

```python
from uno.core.tracing import Tracer, Span, SpanProcessor, get_tracer

# Create a custom integration with another system
class MySystemIntegration(SpanProcessor):
    def __init__(self, my_system_client):
        self.client = my_system_client
    
    async def on_start(self, span: Span) -> None:
        # Notify my system when a span starts
        await self.client.notify_operation_start(
            operation_id=span.span_id,
            trace_id=span.trace_id,
            operation_name=span.name
        )
    
    async def on_end(self, span: Span) -> None:
        # Notify my system when a span ends
        await self.client.notify_operation_end(
            operation_id=span.span_id,
            duration_ms=span.duration,
            status=span.status_code
        )

# Register the custom integration
tracer = get_tracer()
my_client = MySystemClient()
tracer.add_processor(MySystemIntegration(my_client))
```

## Integration with Third-Party Systems

The tracing framework can also integrate with external tracing systems:

### OpenTelemetry Integration

```python
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from uno.core.tracing import SpanProcessor, Span, get_tracer

# Set up OpenTelemetry
provider = TracerProvider()
exporter = OTLPSpanExporter(endpoint="localhost:4317")
provider.add_span_processor(BatchSpanProcessor(exporter))
otel_trace.set_tracer_provider(provider)
otel_tracer = otel_trace.get_tracer("my-service")

# Create bridge from UNO tracing to OpenTelemetry
class OpenTelemetryBridge(SpanProcessor):
    async def on_start(self, span: Span) -> None:
        # Create OTEL span
        ctx = otel_trace.SpanContext(
            trace_id=int(span.trace_id, 16),
            span_id=int(span.span_id, 16),
            is_remote=False,
            trace_flags=otel_trace.TraceFlags.SAMPLED,
        )
        
        parent_ctx = None
        if span.parent_span_id:
            parent_ctx = otel_trace.SpanContext(
                trace_id=int(span.trace_id, 16),
                span_id=int(span.parent_span_id, 16),
                is_remote=False,
                trace_flags=otel_trace.TraceFlags.SAMPLED,
            )
        
        # Store OTEL span in attributes for later
        span.attributes["_otel_span"] = otel_tracer.start_span(
            span.name,
            context=otel_trace.set_span_in_context(parent_ctx) if parent_ctx else None,
            kind=otel_trace.SpanKind.INTERNAL
        )
    
    async def on_end(self, span: Span) -> None:
        # End OTEL span
        otel_span = span.attributes.get("_otel_span")
        if otel_span:
            otel_span.end()

# Register OpenTelemetry bridge
tracer = get_tracer()
tracer.add_processor(OpenTelemetryBridge())
```

## Best Practices

1. **Register integrations early**: Set up integrations during application startup
2. **Use multiple integrations**: Combine logging, metrics, and error integrations for comprehensive observability
3. **Set appropriate sampling**: In high-volume services, reduce sampling rate to control overhead
4. **Monitor overhead**: Be aware of the performance impact of tracing, especially in database operations
5. **Clean up trace data**: Implement span processors that filter out sensitive information
6. **Use named traces**: Give meaningful names to traced operations to make them easier to analyze

## Troubleshooting

If you're having issues with tracing integrations:

1. **Verify registration**: Ensure integration functions are called during startup
2. **Check context propagation**: Make sure trace context is being properly passed between services
3. **Look for context leaks**: Trace contexts should be properly cleaned up after operations complete
4. **Monitor log size**: Trace information can increase log volume; adjust log retention policies
5. **Check sampling rates**: If traces are missing, your sampling rate might be too low