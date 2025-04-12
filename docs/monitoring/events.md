# Structured Event Logging

Structured event logging provides a consistent, searchable way to track and analyze significant events in your application.

## Overview

The event logging system in Uno goes beyond traditional logging by:

- Using structured data instead of unstructured text
- Categorizing events by type and severity
- Including context with each event
- Supporting correlation between related events
- Integrating with distributed tracing

## Basic Usage

```python
from uno.core.monitoring.events import EventLogger, EventType, EventSeverity

# Create a logger
logger = EventLogger()

# Log a simple event
logger.log_event(
    event_type=EventType.USER_ACTIVITY,
    severity=EventSeverity.INFO,
    message="User logged in",
    context={"user_id": "12345", "ip_address": "192.168.1.1"}
)

# Log an error event
try:
    # Some operation that might fail
    result = perform_operation()
except Exception as e:
    logger.log_exception(
        exception=e,
        event_type=EventType.SYSTEM_ERROR,
        message="Operation failed",
        context={"operation": "perform_operation", "params": {"id": "12345"}}
    )
```

## Event Types

The framework provides standard event types:

- `SYSTEM_STARTUP`: Application or component startup
- `SYSTEM_SHUTDOWN`: Application or component shutdown
- `SYSTEM_ERROR`: System-level errors
- `RESOURCE_CREATED`: Resource creation
- `RESOURCE_UPDATED`: Resource updates
- `RESOURCE_DELETED`: Resource deletion
- `USER_ACTIVITY`: User actions
- `SECURITY_EVENT`: Security-related events
- `PERFORMANCE_EVENT`: Performance-related events
- `INTEGRATION_EVENT`: Events related to external integrations

You can define custom event types by extending the `EventType` enum.

## Severity Levels

Events can have the following severity levels:

- `DEBUG`: Detailed information, typically useful only for diagnostic purposes
- `INFO`: Informational messages highlighting normal application operation
- `WARNING`: Potential issues that don't prevent normal operation
- `ERROR`: Error conditions that affect specific operations
- `CRITICAL`: Critical conditions requiring immediate attention

## Context and Correlation

Events include context information to provide a complete picture:

```python
# Creating a context
with EventContext(operation="user_registration", user_id="12345"):
    # All events logged within this context will include the context data
    logger.log_event(
        event_type=EventType.USER_ACTIVITY,
        severity=EventSeverity.INFO,
        message="Started user registration"
    )
    
    # Perform registration steps...
    
    logger.log_event(
        event_type=EventType.RESOURCE_CREATED,
        severity=EventSeverity.INFO,
        message="User registered successfully"
    )
```

## Tracing Integration

The event logging system integrates with distributed tracing:

```python
from uno.core.monitoring.tracing import tracer

# Create a span
with tracer.start_span("register_user") as span:
    # Events logged will be associated with this span
    logger.log_event(
        event_type=EventType.USER_ACTIVITY,
        severity=EventSeverity.INFO,
        message="Processing user registration",
        trace_id=span.trace_id,
        span_id=span.span_id
    )
```

## Event Processors

Events can be processed by various processors:

- `ConsoleEventProcessor`: Prints events to the console
- `FileEventProcessor`: Writes events to a log file
- `JSONEventProcessor`: Formats events as JSON
- `ElasticsearchEventProcessor`: Sends events to Elasticsearch
- `CloudWatchEventProcessor`: Sends events to AWS CloudWatch

Configure multiple processors:

```python
from uno.core.monitoring.events import (
    EventLogger, ConsoleEventProcessor, JSONFileEventProcessor
)

logger = EventLogger(
    processors=[
        ConsoleEventProcessor(),
        JSONFileEventProcessor("/var/log/application/events.log")
    ]
)
```

## FastAPI Integration

Integrate event logging with FastAPI:

```python
from fastapi import FastAPI, Request
from uno.core.monitoring.integration import setup_monitoring

app = FastAPI()
event_logger = EventLogger()

setup_monitoring(app, event_logger=event_logger)

@app.middleware("http")
async def log_request_events(request: Request, call_next):
    # Log request start
    event_logger.log_event(
        event_type=EventType.USER_ACTIVITY,
        severity=EventSeverity.INFO,
        message=f"Request started: {request.method} {request.url.path}",
        context={"client_ip": request.client.host}
    )
    
    # Process request
    response = await call_next(request)
    
    # Log request completion
    event_logger.log_event(
        event_type=EventType.USER_ACTIVITY,
        severity=EventSeverity.INFO,
        message=f"Request completed: {request.method} {request.url.path}",
        context={"status_code": response.status_code}
    )
    
    return response
```

## Filtering and Sampling

Control event volume with filtering and sampling:

```python
from uno.core.monitoring.events import EventFilter, SamplingStrategy

# Filter out DEBUG events
debug_filter = EventFilter(min_severity=EventSeverity.INFO)

# Sample performance events at 10% rate
sampling_strategy = SamplingStrategy(
    event_types=[EventType.PERFORMANCE_EVENT],
    sample_rate=0.1
)

logger = EventLogger(
    filters=[debug_filter],
    sampling_strategies=[sampling_strategy]
)
```

## Alerting Integration

Connect events to alerting systems:

```python
from uno.core.monitoring.events import AlertingEventProcessor

alerting_processor = AlertingEventProcessor(
    min_severity=EventSeverity.ERROR,
    alert_endpoint="https://alerts.example.com/api/v1/events"
)

logger = EventLogger(processors=[alerting_processor])
```

This enables automatic alerts for critical events, ensuring timely response to important issues in your application.