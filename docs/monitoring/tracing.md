# Distributed Tracing

Distributed tracing in Uno allows you to track requests as they flow through your application and external services. It provides visibility into the full request lifecycle, helping you identify bottlenecks and troubleshoot issues.

## Key Concepts

- **Trace**: A distributed transaction that flows through multiple services
- **Span**: A single operation within a trace
- **Span Context**: Information that identifies a span, including trace ID and span ID
- **Propagation**: Transfer of span context between services
- **Sampling**: The process of deciding which traces to record

## Using Tracing

### Creating Spans

The simplest way to create spans is using the `trace` decorator:

```python
from uno.core.monitoring import trace, SpanKind

@trace(name="my_operation", kind=SpanKind.INTERNAL)
async def my_function(arg1, arg2):
    # Function to trace
    return arg1 + arg2
```

You can also create spans manually using the `Tracer` class:

```python
from uno.core.monitoring import get_tracer

async def my_function():
    tracer = get_tracer()
    
    async with await tracer.create_span(
        name="my_operation",
        attributes={"key": "value"},
        kind=SpanKind.INTERNAL
    ) as span:
        # Code to trace
        span.add_event("interesting_event", {"some_data": 123})
        
        # Set status based on result
        span.set_status("ok")
```

### Adding Context to Spans

You can add attributes and events to spans:

```python
async with await tracer.create_span("my_operation") as span:
    # Add attributes
    span.attributes["customer_id"] = "123"
    span.attributes["product_id"] = "456"
    
    # Add events
    span.add_event(
        name="cache_miss",
        attributes={"key": "user:123"}
    )
    
    # Set status based on result
    span.set_status("error", "Database connection failed")
```

### Accessing Current Span

You can access the current span from anywhere in your code:

```python
from uno.core.monitoring import get_current_span, get_current_trace_id, get_current_span_id

def some_function():
    # Get current span
    span = get_current_span()
    if span:
        span.add_event("something_happened")
    
    # Get current trace ID and span ID
    trace_id = get_current_trace_id()
    span_id = get_current_span_id()
    
    print(f"Trace ID: {trace_id}, Span ID: {span_id}")
```

## Propagating Context Between Services

To trace requests across service boundaries, you need to propagate the tracing context:

### HTTP Propagation

For HTTP requests, you can use the `inject_context` and `extract_context` functions:

```python
from uno.core.monitoring import inject_context, extract_context
import aiohttp

async def make_request(url):
    # Create headers
    headers = {"Content-Type": "application/json"}
    
    # Inject tracing context
    inject_context(headers)
    
    # Make request with propagated context
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.json()

# On the receiving end
def handle_request(headers):
    # Extract context
    context = extract_context(headers)
    
    # Use the extracted context (implementation depends on framework)
```

The `TracingMiddleware` handles this automatically for FastAPI applications.

## Integration with FastAPI

The tracing system integrates with FastAPI through the `TracingMiddleware`:

```python
from fastapi import FastAPI
from uno.core.monitoring import TracingMiddleware, get_tracer

app = FastAPI()

# Add tracing middleware
app.add_middleware(
    TracingMiddleware,
    tracer=get_tracer(),
    excluded_paths=["/health", "/metrics"]
)
```

The `setup_monitoring` function does this automatically if enabled in the configuration.

## Trace Processing and Export

Traces are processed by span processors and sent to exporters:

```python
from uno.core.monitoring import get_tracer, LoggingSpanProcessor, BatchSpanProcessor, LoggingSpanExporter

# Get the tracer
tracer = get_tracer()

# Add a processor for logging spans
tracer.add_processor(LoggingSpanProcessor())

# Add a batch processor with an exporter
tracer.add_processor(
    BatchSpanProcessor(
        exporter=LoggingSpanExporter(),
        max_batch_size=100,
        export_interval=5.0
    )
)
```

## Sampling

By default, all traces are sampled (recorded). You can configure sampling to reduce the volume of traces:

```python
from uno.core.monitoring import get_tracer

# Get the tracer
tracer = get_tracer()

# Set a sampler function
def my_sampler(trace_id, parent_id, name):
    # Always sample if parent is sampled
    if parent_id is not None:
        return True
    
    # Sample 10% of traces
    import random
    return random.random() < 0.1

tracer.set_sampler(my_sampler)
```

## Best Practices

1. **Use Descriptive Span Names**: Names should identify the operation being performed.
2. **Add Relevant Attributes**: Include useful information like user IDs, request parameters, etc.
3. **Record Significant Events**: Add events for important steps in the operation.
4. **Set Appropriate Kind**: Use the right `SpanKind` for the operation (SERVER, CLIENT, INTERNAL, etc.).
5. **Set Status Correctly**: Use "ok" for success and "error" for failures, with a message.
6. **Mind Sampling**: Sample appropriately to balance observability and overhead.
7. **Instrument Libraries**: Add tracing to libraries and frameworks you use.

## Advanced Usage

### Creating Child Spans

You can create child spans for nested operations:

```python
async def parent_operation():
    tracer = get_tracer()
    
    async with await tracer.create_span("parent") as parent_span:
        # The child span will automatically be linked to the parent
        async with await tracer.create_span("child") as child_span:
            # Child operation
            pass
```

### Linking Spans

You can link related spans that aren't in a parent-child relationship:

```python
async def operation():
    tracer = get_tracer()
    
    async with await tracer.create_span(
        name="operation",
        links=[
            {
                "trace_id": "trace-id-1",
                "span_id": "span-id-1",
                "attributes": {"reason": "related-work"}
            }
        ]
    ) as span:
        # Operation
        pass
```