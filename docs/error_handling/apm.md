# Application Performance Monitoring Integration

This document provides a comprehensive guide for integrating uno applications with Application Performance Monitoring (APM) tools for error tracing and performance analysis.

## Introduction to APM for uno

Application Performance Monitoring (APM) tools provide end-to-end visibility into your application's performance and error patterns. Key features include:

- **Distributed Tracing**: Track requests across service boundaries
- **Error Tracking**: Capture, analyze, and alert on errors
- **Transaction Monitoring**: Measure performance of critical paths
- **Infrastructure Metrics**: Correlate application issues with infrastructure
- **User Experience Monitoring**: Understand impact on end users

uno provides built-in support for integrating with various APM tools through:

1. **OpenTelemetry Integration**: Standardized telemetry collection
2. **Error Context Propagation**: Maintains error context across services
3. **Structured Error Reporting**: Detailed error information for APM tools
4. **Custom APM Adapters**: Pre-built integrations for popular APM platforms

## OpenTelemetry Integration

### Core Concepts

[OpenTelemetry](https://opentelemetry.io/) is an open source observability framework that provides a standardized way to collect telemetry data including traces, metrics, and logs.

uno uses OpenTelemetry as the foundation for APM integration:

```python
from uno.core.monitoring.tracing import configure_tracing, get_tracer
from opentelemetry.trace.status import Status, StatusCode

# Configure OpenTelemetry
configure_tracing(
    service_name="my-service",
    exporter="otlp",  # OpenTelemetry Protocol
    endpoint="https://otel-collector.example.com:4317"
)

# Get a tracer
tracer = get_tracer(__name__)

# Create a span for an operation
@tracer.start_as_current_span("process_order")
def process_order(order_id):
    # Current span is automatically set in context
    current_span = tracer.get_current_span()
    
    # Add attributes to the span
    current_span.set_attribute("order_id", order_id)
    
    # Operation code here
    result = do_processing(order_id)
    
    # Add result information
    current_span.set_attribute("order_status", result.status)
    
    return result
```

### Error Tracing with OpenTelemetry

Track errors with OpenTelemetry for comprehensive error tracing:

```python
from uno.core.errors import UnoError, ErrorCode, with_error_context
from uno.core.monitoring.tracing import get_tracer
from opentelemetry.trace.status import Status, StatusCode

tracer = get_tracer(__name__)

@tracer.start_as_current_span("process_payment")
@with_error_context
def process_payment(payment_id, amount, currency):
    span = tracer.get_current_span()
    span.set_attribute("payment_id", payment_id)
    span.set_attribute("amount", amount)
    span.set_attribute("currency", currency)
    
    try:
        # Payment processing logic
        result = payment_gateway.process(payment_id, amount, currency)
        span.set_attribute("transaction_id", result.transaction_id)
        return result
    except UnoError as e:
        # Record error in span
        span.record_exception(e)
        span.set_status(
            Status(StatusCode.ERROR, f"{e.error_code}: {e.message}")
        )
        
        # Add error details as span attributes
        span.set_attribute("error.code", e.error_code)
        if e.category:
            span.set_attribute("error.category", e.category.name)
        if e.severity:
            span.set_attribute("error.severity", e.severity.name)
        
        # Add error context as span attributes
        for key, value in e.context.items():
            if isinstance(value, (str, int, float, bool)):
                span.set_attribute(f"error.context.{key}", value)
        
        # Re-raise the error
        raise
    except Exception as e:
        # Handle unexpected errors
        span.record_exception(e)
        span.set_status(
            Status(StatusCode.ERROR, f"Unexpected error: {str(e)}")
        )
        
        # Wrap in UnoError
        error = UnoError(
            f"Unexpected payment processing error: {str(e)}",
            ErrorCode.INTERNAL_ERROR,
            payment_id=payment_id,
            amount=amount,
            currency=currency
        )
        
        # Add error details as span attributes
        span.set_attribute("error.code", error.error_code)
        
        # Re-raise as UnoError
        raise error
```

### Distributed Tracing for Errors

Track errors across service boundaries with distributed tracing:

```python
from uno.core.monitoring.tracing import get_tracer, inject_context, extract_context
import httpx
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

tracer = get_tracer(__name__)
propagator = TraceContextTextMapPropagator()

@tracer.start_as_current_span("call_payment_service")
async def call_payment_service(payment_id, amount):
    # Get current context
    headers = {}
    inject_context(headers)  # Injects trace context into headers
    
    # Make HTTP request with propagated context
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://payment-service.example.com/api/payments",
                headers=headers,
                json={"payment_id": payment_id, "amount": amount}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            # Extract error details from response if available
            error_data = {}
            try:
                if e.response and e.response.content:
                    error_data = e.response.json().get("error", {})
            except Exception:
                pass
            
            # Create UnoError with propagated error details
            raise UnoError(
                f"Payment service error: {str(e)}",
                error_data.get("code", ErrorCode.API_INTEGRATION_ERROR),
                payment_id=payment_id,
                amount=amount,
                status_code=getattr(e.response, "status_code", None),
                error_details=error_data
            )

# In the payment service API
@app.post("/api/payments")
async def create_payment(payment: dict, request: Request):
    # Extract trace context
    context = extract_context(request.headers)
    
    # Create span in the same trace
    with tracer.start_as_current_span("process_payment", context=context) as span:
        span.set_attribute("payment_id", payment["payment_id"])
        span.set_attribute("amount", payment["amount"])
        
        # Process payment and handle errors
        try:
            result = await payment_processor.process(payment)
            return {"status": "success", "transaction_id": result.transaction_id}
        except UnoError as e:
            # Record error in span
            span.record_exception(e)
            span.set_status(
                Status(StatusCode.ERROR, f"{e.error_code}: {e.message}")
            )
            
            # Return error response with details
            return JSONResponse(
                status_code=e.http_status_code,
                content={
                    "error": {
                        "code": e.error_code,
                        "message": e.message,
                        "category": e.category.name if e.category else None
                    }
                }
            )
```

## APM Tool Integration

### New Relic Integration

Integrate with New Relic for comprehensive error tracking:

```python
from uno.core.monitoring.apm.newrelic import (
    configure_new_relic,
    report_error,
    trace_function
)
from uno.core.errors import UnoError, ErrorCode

# Configure New Relic
configure_new_relic(
    app_name="my-uno-app",
    license_key="your-license-key",
    distributed_tracing=True,
    environment="production"
)

# Trace a function with New Relic
@trace_function(name="process_order", group="OrderProcessing")
def process_order(order_id):
    try:
        # Order processing logic
        return complete_order(order_id)
    except UnoError as e:
        # Report error to New Relic
        report_error(e, params={"order_id": order_id})
        raise
    except Exception as e:
        # Wrap unexpected errors
        error = UnoError(
            f"Unexpected error processing order: {str(e)}",
            ErrorCode.INTERNAL_ERROR,
            order_id=order_id
        )
        report_error(error)
        raise error

# Using custom transactions
from uno.core.monitoring.apm.newrelic import start_transaction, end_transaction

def batch_process_orders(order_ids):
    # Start custom transaction
    txn = start_transaction("BatchProcessing", "process_orders_batch")
    
    results = []
    errors = []
    
    for order_id in order_ids:
        try:
            result = process_order(order_id)
            results.append(result)
        except UnoError as e:
            errors.append(e)
    
    # Add custom attributes to transaction
    txn.add_custom_attributes({
        "orders_processed": len(results),
        "orders_failed": len(errors),
        "batch_size": len(order_ids)
    })
    
    # End transaction
    end_transaction(txn)
    
    return results, errors
```

### Datadog Integration

Integrate with Datadog for advanced error monitoring:

```python
from uno.core.monitoring.apm.datadog import (
    configure_datadog,
    trace,
    report_error,
    set_tag
)
from uno.core.errors import UnoError, ErrorCode

# Configure Datadog
configure_datadog(
    service="my-uno-app",
    env="production",
    version="1.2.3",
    sample_rate=1.0
)

# Trace a function with Datadog
@trace(name="process_order", service="order-service", resource="process_order")
def process_order(order_id):
    # Add tags to current span
    set_tag("order_id", order_id)
    
    try:
        # Order processing logic
        result = complete_order(order_id)
        set_tag("order_status", result.status)
        return result
    except UnoError as e:
        # Report error to Datadog
        report_error(e)
        raise
    except Exception as e:
        # Wrap unexpected errors
        error = UnoError(
            f"Unexpected error processing order: {str(e)}",
            ErrorCode.INTERNAL_ERROR,
            order_id=order_id
        )
        report_error(error)
        raise error

# Using custom spans
from uno.core.monitoring.apm.datadog import start_span, finish_span

def validate_order(order):
    # Start custom span
    with start_span("validate_order") as span:
        span.set_tag("order_id", order.id)
        
        try:
            # Validation logic
            validate_items(order.items)
            validate_shipping(order.shipping)
            validate_payment(order.payment)
            
            span.set_tag("validation_result", "success")
            return True
        except UnoError as e:
            # Report validation error
            span.set_tag("validation_result", "failure")
            span.set_tag("error_code", e.error_code)
            span.set_tag("error_field", e.context.get("field", "unknown"))
            report_error(e)
            raise
```

### Sentry Integration

Integrate with Sentry for detailed error reporting:

```python
from uno.core.monitoring.apm.sentry import (
    configure_sentry,
    capture_exception,
    configure_scope,
    start_transaction
)
from uno.core.errors import UnoError, ErrorCode

# Configure Sentry
configure_sentry(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
    environment="production",
    release="1.2.3",
    traces_sample_rate=0.2
)

# Report an error to Sentry
def process_payment(payment_id, amount):
    # Set context for this operation
    with configure_scope() as scope:
        scope.set_tag("payment_id", payment_id)
        scope.set_tag("amount", amount)
        
        # Create a transaction
        with start_transaction(name="process_payment", op="payment"):
            try:
                # Payment processing logic
                result = payment_gateway.process(payment_id, amount)
                
                # Add result information
                scope.set_tag("transaction_id", result.transaction_id)
                scope.set_tag("status", result.status)
                
                return result
            except UnoError as e:
                # Capture exception with Sentry
                capture_exception(e)
                raise
            except Exception as e:
                # Wrap unexpected errors
                error = UnoError(
                    f"Unexpected payment error: {str(e)}",
                    ErrorCode.INTERNAL_ERROR,
                    payment_id=payment_id,
                    amount=amount
                )
                capture_exception(error)
                raise error
```

### Elastic APM Integration

Integrate with Elastic APM for comprehensive monitoring:

```python
from uno.core.monitoring.apm.elastic import (
    configure_elastic_apm,
    capture_exception,
    start_transaction,
    start_span
)
from uno.core.errors import UnoError, ErrorCode

# Configure Elastic APM
configure_elastic_apm(
    service_name="my-uno-app",
    server_url="http://apm-server.example.com:8200",
    environment="production",
    sample_rate=1.0
)

# Using transactions and spans
def process_order(order_id):
    # Start a transaction
    transaction = start_transaction(name="process_order", type="order")
    
    try:
        # Add context
        transaction.context.custom.update({"order_id": order_id})
        
        # Start a span for a sub-operation
        with start_span("validate_order", span_type="validation") as span:
            span.context.custom.update({"order_id": order_id})
            # Validation logic
            validate_result = validate_order(order_id)
        
        # Start another span
        with start_span("process_payment", span_type="payment") as span:
            span.context.custom.update({
                "order_id": order_id,
                "amount": validate_result.amount
            })
            # Payment processing
            payment_result = process_payment(order_id, validate_result.amount)
        
        # Complete transaction
        transaction.result = "success"
        transaction.context.custom.update({
            "payment_id": payment_result.payment_id,
            "status": "completed"
        })
        
        return payment_result
    except UnoError as e:
        # Capture exception and add to transaction
        capture_exception(e)
        
        # Mark transaction as failed
        transaction.result = "error"
        transaction.context.custom.update({
            "error_code": e.error_code,
            "error_category": e.category.name if e.category else "unknown"
        })
        
        raise
    finally:
        # End transaction
        transaction.end()
```

## Custom APM Integration

### Creating a Custom APM Adapter

Create a custom adapter for integrating with other APM tools:

```python
from uno.core.monitoring.apm.base import APMAdapter
from uno.core.errors import UnoError
from typing import Any, Dict, Optional

class CustomAPMAdapter(APMAdapter):
    """Custom APM adapter for integration with a specific APM tool."""
    
    def __init__(self, app_name: str, api_key: str, **options):
        """Initialize the adapter with required configuration."""
        self.app_name = app_name
        self.api_key = api_key
        self.options = options
        self.client = None
        
    def initialize(self) -> None:
        """Initialize the APM client."""
        # Initialize client for your APM tool
        import custom_apm_client
        
        self.client = custom_apm_client.Client(
            app_name=self.app_name,
            api_key=self.api_key,
            **self.options
        )
        
    def start_transaction(self, name: str, transaction_type: str = "custom") -> Any:
        """Start a new transaction."""
        if not self.client:
            self.initialize()
        
        return self.client.start_transaction(name, transaction_type)
    
    def end_transaction(self, transaction: Any) -> None:
        """End a transaction."""
        if transaction:
            transaction.end()
    
    def start_span(self, name: str, span_type: str = "custom") -> Any:
        """Start a new span in the current transaction."""
        if not self.client:
            self.initialize()
        
        return self.client.start_span(name, span_type)
    
    def end_span(self, span: Any) -> None:
        """End a span."""
        if span:
            span.end()
    
    def capture_exception(self, exception: Exception, **context) -> None:
        """Capture an exception."""
        if not self.client:
            self.initialize()
        
        if isinstance(exception, UnoError):
            # Extract UnoError specific details
            error_details = {
                "error_code": exception.error_code,
                "category": exception.category.name if exception.category else "unknown",
                "severity": exception.severity.name if exception.severity else "unknown",
                "context": exception.context
            }
            context.update(error_details)
        
        self.client.capture_exception(exception, **context)
    
    def set_context(self, key: str, value: Dict[str, Any]) -> None:
        """Set context information for the current transaction."""
        if not self.client:
            self.initialize()
        
        self.client.set_context(key, value)
    
    def set_tag(self, key: str, value: Any) -> None:
        """Set a tag for the current transaction or span."""
        if not self.client:
            self.initialize()
        
        self.client.set_tag(key, value)
    
    def set_user(self, user_id: str, **user_info) -> None:
        """Set user information for the current transaction."""
        if not self.client:
            self.initialize()
        
        self.client.set_user(user_id, **user_info)

# Register the custom adapter
from uno.core.monitoring.apm import register_apm_adapter

register_apm_adapter("custom", CustomAPMAdapter)

# Use the custom adapter
from uno.core.monitoring.apm import configure_apm

configure_apm(
    provider="custom",
    app_name="my-app",
    api_key="your-api-key",
    environment="production"
)
```

## Configuring APM in Your Application

### FastAPI Integration

Configure APM with FastAPI for comprehensive monitoring:

```python
from fastapi import FastAPI, Request, Depends
from uno.core.monitoring.apm import configure_apm, get_apm_middleware, capture_request_errors
from uno.core.fastapi_error_handlers import setup_error_handlers
from uno.core.errors import UnoError, ErrorCode

# Create FastAPI app
app = FastAPI()

# Configure APM
configure_apm(
    provider="opentelemetry",
    service_name="api-service",
    environment="production",
    tracing_enabled=True,
    distributed_tracing=True,
    exporter_config={
        "type": "otlp",
        "endpoint": "https://otel-collector.example.com:4317"
    }
)

# Add APM middleware
app.add_middleware(get_apm_middleware())

# Configure error handlers
setup_error_handlers(app)

# Add request error capturing
app = capture_request_errors(app)

# Dependency for adding user context to APM
async def add_user_to_apm(request: Request):
    from uno.core.monitoring.apm import set_user
    
    # Get user from request (e.g., from JWT token)
    try:
        user = get_user_from_request(request)
        if user:
            set_user(user.id, email=user.email, username=user.username)
    except Exception:
        pass  # Skip if user cannot be determined
    return None

# Use in endpoints
@app.get("/orders/{order_id}")
async def get_order(order_id: str, _: None = Depends(add_user_to_apm)):
    from uno.core.monitoring.apm import set_tag, start_span
    
    # Add tag to current transaction
    set_tag("order_id", order_id)
    
    try:
        # Get order with span for database operation
        with start_span("db_get_order"):
            order = await order_repository.get_by_id(order_id)
        
        if not order:
            raise UnoError(
                f"Order not found: {order_id}",
                ErrorCode.RESOURCE_NOT_FOUND,
                resource_type="Order",
                resource_id=order_id
            )
        
        # Process order data with another span
        with start_span("process_order_data"):
            result = process_order_data(order)
        
        return result
    except UnoError:
        # Will be handled by error handlers and automatically reported to APM
        raise
```

### Configuration for Different Environments

Configure APM with environment-specific settings:

```python
from uno.core.config import Settings
from functools import lru_cache
from pydantic import Field
from typing import Literal, Optional, Dict, Any

class APMSettings(Settings):
    """APM configuration settings."""
    
    apm_enabled: bool = Field(True, env="APM_ENABLED")
    apm_provider: Literal["opentelemetry", "newrelic", "datadog", "sentry", "elastic", "custom"] = Field(
        "opentelemetry", env="APM_PROVIDER"
    )
    apm_service_name: str = Field("my-service", env="APM_SERVICE_NAME")
    apm_environment: str = Field("development", env="APM_ENVIRONMENT")
    apm_version: Optional[str] = Field(None, env="APM_VERSION")
    apm_trace_sample_rate: float = Field(1.0, env="APM_TRACE_SAMPLE_RATE")
    apm_distributed_tracing: bool = Field(True, env="APM_DISTRIBUTED_TRACING")
    apm_exporter_type: str = Field("otlp", env="APM_EXPORTER_TYPE")
    apm_exporter_endpoint: Optional[str] = Field(None, env="APM_EXPORTER_ENDPOINT")
    apm_api_key: Optional[str] = Field(None, env="APM_API_KEY")
    
    # Provider-specific settings
    apm_newrelic_license_key: Optional[str] = Field(None, env="APM_NEWRELIC_LICENSE_KEY")
    apm_sentry_dsn: Optional[str] = Field(None, env="APM_SENTRY_DSN")
    apm_datadog_agent_url: Optional[str] = Field(None, env="APM_DATADOG_AGENT_URL")
    apm_elastic_server_url: Optional[str] = Field(None, env="APM_ELASTIC_SERVER_URL")

@lru_cache
def get_apm_settings() -> APMSettings:
    """Get cached APM settings."""
    return APMSettings()

def configure_application_apm():
    """Configure APM based on settings."""
    from uno.core.monitoring.apm import configure_apm
    
    settings = get_apm_settings()
    
    if not settings.apm_enabled:
        return
    
    # Prepare exporter config
    exporter_config = {
        "type": settings.apm_exporter_type
    }
    
    if settings.apm_exporter_endpoint:
        exporter_config["endpoint"] = settings.apm_exporter_endpoint
    
    # Provider-specific configurations
    provider_config: Dict[str, Any] = {}
    
    if settings.apm_provider == "newrelic" and settings.apm_newrelic_license_key:
        provider_config["license_key"] = settings.apm_newrelic_license_key
    
    elif settings.apm_provider == "sentry" and settings.apm_sentry_dsn:
        provider_config["dsn"] = settings.apm_sentry_dsn
    
    elif settings.apm_provider == "datadog" and settings.apm_datadog_agent_url:
        provider_config["agent_url"] = settings.apm_datadog_agent_url
    
    elif settings.apm_provider == "elastic" and settings.apm_elastic_server_url:
        provider_config["server_url"] = settings.apm_elastic_server_url
    
    # API key if needed
    if settings.apm_api_key:
        provider_config["api_key"] = settings.apm_api_key
    
    # Configure APM
    configure_apm(
        provider=settings.apm_provider,
        service_name=settings.apm_service_name,
        environment=settings.apm_environment,
        version=settings.apm_version,
        sample_rate=settings.apm_trace_sample_rate,
        distributed_tracing=settings.apm_distributed_tracing,
        exporter_config=exporter_config,
        **provider_config
    )

# Call during application startup
def startup_event():
    configure_application_apm()
```

## Performance Impact and Sampling Strategies

### Understanding Performance Impacts

APM instrumentation adds overhead to your application. Manage this with:

```python
from uno.core.monitoring.apm import configure_apm

# Configure APM with appropriate sampling
configure_apm(
    provider="opentelemetry",
    service_name="high-traffic-api",
    environment="production",
    # Sample only 10% of requests in production
    sample_rate=0.1,
    # Only trace certain operations fully
    trace_filters={
        "include_paths": ["/api/critical/*", "/api/orders/*"],
        "exclude_paths": ["/api/health", "/api/metrics", "/static/*"],
        "include_operations": ["database", "external_api"],
        "exclude_operations": ["cache"]
    }
)
```

### Dynamic Sampling Strategies

Implement dynamic sampling for more intelligent trace collection:

```python
from uno.core.monitoring.apm.sampling import DynamicSampler, SamplingContext

class ErrorBasedSampler(DynamicSampler):
    """Sample more traces when errors are occurring."""
    
    def __init__(self, base_rate=0.1, error_rate=1.0, error_window_size=100):
        self.base_rate = base_rate
        self.error_rate = error_rate
        self.window_size = error_window_size
        self.request_results = []
    
    def should_sample(self, context: SamplingContext) -> bool:
        """Determine if this request should be sampled."""
        # Always sample specific endpoints
        if context.path.startswith("/api/critical/"):
            return True
        
        # Calculate current error rate
        if len(self.request_results) >= self.window_size:
            self.request_results.pop(0)
        
        # Get current error percentage
        if not self.request_results:
            current_error_rate = 0
        else:
            error_count = sum(1 for r in self.request_results if r is True)
            current_error_rate = error_count / len(self.request_results)
        
        # Adjust sampling rate based on error rate
        # Higher error rate = higher sampling rate
        adjusted_rate = self.base_rate + (current_error_rate * (self.error_rate - self.base_rate))
        
        # Apply the sampling rate
        import random
        return random.random() < adjusted_rate
    
    def record_result(self, context: SamplingContext, is_error: bool):
        """Record the result of a request to adjust future sampling."""
        self.request_results.append(is_error)

# Register and use the sampler
from uno.core.monitoring.apm import register_sampler, configure_apm

# Create and register the sampler
error_sampler = ErrorBasedSampler(base_rate=0.05, error_rate=0.8)
register_sampler("error_based", error_sampler)

# Configure APM with the custom sampler
configure_apm(
    provider="opentelemetry",
    service_name="api-service",
    environment="production",
    sampler="error_based"
)

# Update the sampler after request processing
from starlette.middleware.base import BaseHTTPMiddleware

class SamplerUpdateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Record if this was an error response
        is_error = response.status_code >= 400
        
        # Update sampler with result
        from uno.core.monitoring.apm import get_sampler
        sampler = get_sampler("error_based")
        if sampler:
            context = SamplingContext(
                path=request.url.path,
                method=request.method,
                status_code=response.status_code
            )
            sampler.record_result(context, is_error)
        
        return response
```

## Best Practices for APM Integration

### 1. Use Semantic Conventions

Follow OpenTelemetry semantic conventions for consistent data:

```python
from uno.core.monitoring.apm import set_tag, start_span

# Using semantic conventions for database operations
with start_span("database_query") as span:
    # Standard semantic conventions for databases
    span.set_tag("db.system", "postgresql")
    span.set_tag("db.name", "orders_db")
    span.set_tag("db.operation", "SELECT")
    span.set_tag("db.statement", "SELECT * FROM orders WHERE id = $1")
    
    # Execute query
    result = await db.fetchrow("SELECT * FROM orders WHERE id = $1", order_id)
```

### 2. Add Business Context

Include business context for better understanding:

```python
from uno.core.monitoring.apm import set_tag, set_context

def process_checkout(cart_id, user_id, payment_method):
    # Add business context to transaction
    set_tag("cart_id", cart_id)
    set_tag("user_id", user_id)
    set_tag("payment_method", payment_method)
    
    # Add detailed context data
    set_context("cart", {
        "id": cart_id,
        "item_count": len(cart.items),
        "total_amount": cart.total_amount,
        "currency": cart.currency,
        "has_discounts": len(cart.discounts) > 0
    })
    
    # Process checkout
    # ...
```

### 3. Integrate with Error Handling

Ensure errors are properly reported to APM:

```python
from uno.core.errors import UnoError, ErrorCode, with_error_context
from uno.core.monitoring.apm import capture_exception, set_tag

@with_error_context
def process_payment(payment_id, amount, currency):
    # Add context that will be included in errors
    set_tag("payment_id", payment_id)
    set_tag("amount", amount)
    set_tag("currency", currency)
    
    try:
        # Payment processing logic
        result = payment_gateway.process(payment_id, amount, currency)
        return result
    except ConnectionError as e:
        # Transform external errors to application errors
        error = UnoError(
            f"Payment gateway connection error: {str(e)}",
            ErrorCode.API_INTEGRATION_ERROR,
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            retry_allowed=True
        )
        # Capture transformed error
        capture_exception(error)
        raise error
```

### 4. Use Transactions for Business Processes

Define transactions based on business processes:

```python
from uno.core.monitoring.apm import start_transaction, end_transaction, start_span

def checkout_process(cart_id, user_id):
    # Start a transaction for the entire checkout process
    transaction = start_transaction(name="checkout_process", type="business")
    
    try:
        # Add transaction context
        transaction.add_context("cart_id", cart_id)
        transaction.add_context("user_id", user_id)
        
        # Step 1: Validate cart
        with start_span("validate_cart"):
            cart = validate_cart(cart_id)
        
        # Step 2: Apply promotions
        with start_span("apply_promotions"):
            apply_promotions(cart)
        
        # Step 3: Process payment
        with start_span("process_payment"):
            payment_result = process_payment(cart)
        
        # Step 4: Create order
        with start_span("create_order"):
            order = create_order(cart, payment_result)
        
        # Step 5: Send confirmation
        with start_span("send_confirmation"):
            send_confirmation(order, user_id)
        
        # Mark transaction as successful
        transaction.result = "success"
        transaction.add_context("order_id", order.id)
        
        return order
    except Exception as e:
        # Mark transaction as failed
        transaction.result = "error"
        
        # Capture exception
        from uno.core.monitoring.apm import capture_exception
        capture_exception(e)
        
        raise
    finally:
        # End transaction
        end_transaction(transaction)
```

### 5. Monitor Critical Paths

Identify and monitor critical paths in your application:

```python
from uno.core.monitoring.apm import mark_as_critical_path, add_custom_metric

@mark_as_critical_path  # Ensures 100% sampling and specialized monitoring
def process_payment(payment_id, amount):
    start_time = time.time()
    
    try:
        # Process payment
        result = payment_gateway.charge(payment_id, amount)
        
        # Record success metric
        processing_time = time.time() - start_time
        add_custom_metric("payment_processing_time", processing_time)
        add_custom_metric("payment_success", 1)
        
        return result
    except Exception as e:
        # Record failure metric
        add_custom_metric("payment_failure", 1)
        
        # Record specific error type metrics
        if isinstance(e, TimeoutError):
            add_custom_metric("payment_timeout", 1)
        elif isinstance(e, ValidationError):
            add_custom_metric("payment_validation_error", 1)
        
        raise
```

### 6. Configure APM for Your Error Types

Ensure your custom error types are properly handled:

```python
from uno.core.monitoring.apm import register_error_handler
from uno.core.errors import UnoError, ValidationError, AuthorizationError

# Register custom error handlers
def handle_validation_error(error, apm_client):
    """Custom handler for validation errors in APM."""
    # Set appropriate error type
    apm_client.set_error_type("ValidationError")
    
    # Add custom error attributes
    if isinstance(error, ValidationError):
        apm_client.add_error_attribute("field", error.context.get("field"))
        apm_client.add_error_attribute("value", error.context.get("value"))
    
    # Set appropriate error category
    apm_client.set_error_category("input_validation")
    
    # Return true to indicate we've handled this error type
    return True

# Register error handlers
register_error_handler(ValidationError, handle_validation_error)
register_error_handler(AuthorizationError, lambda e, c: c.set_error_category("security"))
```

### 7. Add Contextual Information

Enrich transactions with contextual information:

```python
from uno.core.monitoring.apm import set_context, set_user, set_tag

def handle_request(request):
    # Add request context
    set_context("request", {
        "path": request.path,
        "method": request.method,
        "remote_addr": request.client.host,
        "user_agent": request.headers.get("User-Agent")
    })
    
    # Add user info if available
    user = get_user_from_request(request)
    if user:
        set_user(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
        )
    
    # Add business context
    if "order_id" in request.path_params:
        set_tag("order_id", request.path_params["order_id"])
    
    # Handle request
    # ...
```

### 8. Distributed Tracing Across Services

Ensure proper context propagation across services:

```python
from uno.core.monitoring.apm import inject_context, extract_context
import httpx

async def call_service(service_url, method, data):
    # Get headers with tracing context
    headers = {}
    inject_context(headers)
    
    # Add authorization and other headers
    headers["Authorization"] = f"Bearer {get_auth_token()}"
    
    # Make request with propagated context
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            service_url,
            headers=headers,
            json=data
        )
    
    return response

# In the receiving service
from fastapi import Request

def handle_incoming_request(request: Request):
    # Extract tracing context from headers
    context = extract_context(request.headers)
    
    # Continue the trace in this service
    from uno.core.monitoring.apm import continue_trace
    with continue_trace(context):
        # Process the request in the context of the original trace
        # ...
```

## See Also

- [Error Handling Overview](overview.md) - Core error handling concepts
- [Expanded Error Catalog](expanded_catalog.md) - Comprehensive error code catalog
- [Error Monitoring](monitoring.md) - General error monitoring approaches
- [Consistent Error Handling](consistent_handling.md) - Guidelines for consistent error handling