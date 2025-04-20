# Tracing Framework

The UNO Tracing Framework provides a comprehensive solution for distributed tracing, allowing you to track request flows across services and components with integration to logging, metrics, and error handling.

## Overview

The tracing framework is designed to provide:

- **Distributed tracing**: Track request flows across service boundaries
- **Context propagation**: Automatically propagate trace context between services
- **Integration with logging**: Include trace IDs in log messages
- **Integration with metrics**: Collect metrics about trace operations
- **Integration with error handling**: Include trace information in error context
- **HTTP middleware**: Automatic tracing of HTTP requests
- **Customizable sampling**: Control which spans are collected and exported

## Key Concepts

### Spans and Traces

In distributed tracing, a **trace** represents the complete journey of a request through your system, while a **span** represents a single unit of work within that trace:

```
Trace: |-------------------------------------|
Spans:  |---A---| |----B----| |------C------|
                          |----D----|
```

- Trace: A unique ID that groups all related spans
- Span: A unit of work with a name, start time, end time, and context
- Parent-Child Relationship: Spans can have parent spans, creating a hierarchical structure

### Tracing Context

The tracing context is automatically propagated through your application:

```python
from uno.core.tracing import get_current_span, get_current_trace_id

# Get information about the current trace
span = get_current_span()
trace_id = get_current_trace_id()

print(f"Current trace ID: {trace_id}")
print(f"Current span ID: {span.span_id}")
```

### Creating Spans

You can create spans in several ways:

#### Using Context Managers

```python
from uno.core.tracing import get_tracer

async def process_request():
    tracer = get_tracer()
    
    # Create a span using an async context manager
    async with tracer.create_span("process_data", attributes={"data_size": 1024}) as span:
        # Do some work
        result = await process_data()
        
        # Add an event to the span
        span.add_event("data_processed", attributes={"items": len(result)})
        
        # The span is automatically ended when exiting the context
        return result
```

#### Using Decorators

```python
from uno.core.tracing import trace, SpanKind

# Automatically create a span for this function
@trace(name="get_user_data", kind=SpanKind.CLIENT)
async def get_user_data(user_id: str):
    # Function arguments are automatically added to span attributes
    # Do some work
    return await fetch_user(user_id)
```

## Configuration

Configure the tracing system with `configure_tracing()`:

```python
from uno.core.tracing import configure_tracing, TracingConfig, LoggingSpanProcessor

# Using default configuration
configure_tracing()

# Using custom configuration
config = TracingConfig(
    enabled=True,
    service_name="my-service",
    environment="production",
    export_interval=5.0,
    console_export=True,
    sampling_rate=0.1  # Sample 10% of traces
)
tracer = configure_tracing(config)

# Add a custom processor
tracer.add_processor(LoggingSpanProcessor())
```

## HTTP Request Tracing

The `TracingMiddleware` provides automatic tracing of HTTP requests:

```python
from fastapi import FastAPI
from uno.core.tracing import TracingMiddleware

app = FastAPI()

# Add tracing middleware
app.add_middleware(
    TracingMiddleware,
    excluded_paths=["/health", "/metrics"]
)
```

This will:
1. Create a span for each HTTP request
2. Extract trace context from incoming request headers
3. Add trace ID to response headers
4. Record request method, path, status code, and duration

## Cross-Service Tracing

To propagate trace context across service boundaries:

### When Making HTTP Requests

```python
from uno.core.tracing import inject_context
import httpx

async def call_service():
    # Create headers dict
    headers = {}
    
    # Inject trace context
    inject_context(headers)
    
    # Make the request with trace context
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data", headers=headers)
        
    return response
```

### When Receiving HTTP Requests

The `TracingMiddleware` automatically extracts trace context from incoming requests.

## Database Operation Tracing

Trace database operations using the database integration:

```python
from uno.core.tracing import create_database_integration
from sqlalchemy.ext.asyncio import AsyncSession

# Create the database tracing decorator
trace_db = create_database_integration()

class UserRepository:
    @trace_db
    async def get_user(self, session: AsyncSession, user_id: str):
        # This operation will be traced
        result = await session.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})
        return result.fetchone()
```

## Integration with Logging and Metrics

The tracing framework integrates with logging and metrics:

```python
from uno.core.tracing import (
    register_logging_integration,
    register_metrics_integration,
    register_error_integration
)

# Set up integrations
register_logging_integration()
register_metrics_integration()
register_error_integration()
```

This enables:
- Logs to include trace and span IDs
- Metrics collection for spans (count, duration, errors)
- Error context to include trace information

## Custom Span Processors and Exporters

You can create custom processors and exporters:

```python
from uno.core.tracing import SpanProcessor, SpanExporter, Span, BatchSpanProcessor

# Custom processor
class MySpanProcessor(SpanProcessor):
    async def on_start(self, span: Span) -> None:
        print(f"Span started: {span.name}")
    
    async def on_end(self, span: Span) -> None:
        print(f"Span ended: {span.name}, duration: {span.duration}ms")

# Custom exporter
class MySpanExporter(SpanExporter):
    async def export_spans(self, spans: list[Span]) -> None:
        for span in spans:
            # Export span to your observability system
            pass

# Set up with batch processing
tracer = get_tracer()
exporter = MySpanExporter()
processor = BatchSpanProcessor(exporter, max_batch_size=100, export_interval=5.0)
tracer.add_processor(processor)
```

## Sampling Strategies

Control which spans are collected with custom sampling:

```python
from uno.core.tracing import get_tracer

def my_sampler(trace_id: str, parent_id: Optional[str], name: str) -> bool:
    # Always sample errors
    if "error" in name.lower():
        return True
    
    # Sample 10% of new traces (those without parent)
    if not parent_id:
        import random
        return random.random() < 0.1
    
    # Always sample child spans if parent was sampled
    return True

# Set up custom sampling
tracer = get_tracer()
tracer.set_sampler(my_sampler)
```

## Best Practices

1. **Use meaningful span names**: Choose descriptive names that indicate what operation is being performed
2. **Add relevant attributes**: Include information that helps identify and diagnose issues
3. **Create span hierarchies**: Structure spans to reflect the relationships between operations
4. **Set appropriate sampling rates**: Use higher rates in development and lower rates in production
5. **Include business context**: Add business-specific attributes when relevant
6. **Set error status**: Mark spans as errors when operations fail
7. **Use events for milestones**: Add events to mark important points within a span

## Migration from Legacy Tracing

If you're currently using the legacy tracing module (`uno.core.monitoring.tracing`), here's how to migrate:

```python
# Legacy usage
from uno.core.monitoring import (
    TracingContext, Span, SpanKind,
    trace, get_tracer, TracingMiddleware
)

# New usage
from uno.core.tracing import (
    TracingContext, Span, SpanKind,
    trace, get_tracer, TracingMiddleware,
    configure_tracing, TracingConfig
)
```

The new module maintains API compatibility while providing enhanced functionality and integration with the logging, error, and metrics frameworks.