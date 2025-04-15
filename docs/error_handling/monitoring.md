# Error Monitoring and Analysis

This document provides guidance on monitoring, analyzing, and responding to errors in applications built with uno.

## Core Concepts

Error monitoring in uno is built on these core principles:

1. **Centralized Collection**: Gather all errors in a central location
2. **Structured Data**: Store errors with consistent structure and metadata
3. **Contextual Information**: Preserve context for effective diagnosis
4. **Pattern Detection**: Identify trends and patterns in error occurrences
5. **Proactive Alerts**: Configure alerts for critical error conditions
6. **Performance Impact**: Understand how errors affect system performance

## Monitoring Components

### Error Metrics Collection

uno provides built-in error metrics collection through the monitoring framework:

```python
from uno.core.monitoring.metrics import MetricsManager, Counter, Histogram
from uno.core.errors import UnoError, ErrorCode

# Configure metrics
metrics = MetricsManager.get_instance()
error_counter = metrics.create_counter(
    name="errors_total",
    description="Total errors by code and category",
    labels=["error_code", "category", "severity"]
)
error_duration = metrics.create_histogram(
    name="error_handling_duration_seconds",
    description="Error handling duration in seconds",
    labels=["error_code"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Record metrics in exception handler
def handle_error(error: UnoError):
    error_counter.inc(
        labels={
            "error_code": error.error_code,
            "category": error.category.name if error.category else "UNKNOWN",
            "severity": error.severity.name if error.severity else "UNKNOWN"
        }
    )
    
    # Measure error handling time
    with error_duration.time(labels={"error_code": error.error_code}):
        # Error handling logic
        process_error(error)
```

### Error Logging

uno provides structured error logging that integrates with the error handling system:

```python
from uno.core.errors.logging import get_logger
from contextlib import contextmanager
import time

logger = get_logger(__name__)

@contextmanager
def log_errors(operation_name, **context):
    """Context manager to log errors with timing and context."""
    start_time = time.time()
    try:
        yield
    except UnoError as e:
        duration = time.time() - start_time
        logger.error(
            f"Error in {operation_name} after {duration:.3f}s: {e.message}",
            extra={
                "error_code": e.error_code,
                "category": e.category.name if e.category else None,
                "severity": e.severity.name if e.severity else None,
                "context": {**e.context, **context},
                "duration": duration
            }
        )
        raise
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Unexpected error in {operation_name} after {duration:.3f}s: {str(e)}",
            extra={
                "error_code": ErrorCode.UNKNOWN_ERROR,
                "context": context,
                "duration": duration
            },
            exc_info=True
        )
        raise
```

### Error Rate Monitoring

Monitor error rates over time to detect unusual patterns:

```python
from datetime import datetime, timedelta
from uno.core.monitoring.metrics import MetricsManager, Gauge

# Configure error rate gauge
metrics = MetricsManager.get_instance()
error_rate = metrics.create_gauge(
    name="error_rate",
    description="Error rate per minute",
    labels=["error_code", "endpoint"]
)

# Track errors in a time window
class ErrorRateTracker:
    def __init__(self, window_minutes=5):
        self.window_minutes = window_minutes
        self.errors = []
        
    def record_error(self, error_code, endpoint):
        """Record an error occurrence."""
        now = datetime.now()
        self.errors.append((now, error_code, endpoint))
        self._cleanup_old_errors(now)
        self._update_rates(now)
    
    def _cleanup_old_errors(self, now):
        """Remove errors outside the current window."""
        cutoff = now - timedelta(minutes=self.window_minutes)
        self.errors = [(ts, code, ep) for ts, code, ep in self.errors if ts >= cutoff]
    
    def _update_rates(self, now):
        """Update error rate metrics."""
        # Group errors by code and endpoint
        counts = {}
        for _, code, endpoint in self.errors:
            key = (code, endpoint)
            counts[key] = counts.get(key, 0) + 1
        
        # Update gauges
        for (code, endpoint), count in counts.items():
            rate_per_minute = count / self.window_minutes
            error_rate.set(
                value=rate_per_minute,
                labels={"error_code": code, "endpoint": endpoint}
            )

# Usage
tracker = ErrorRateTracker(window_minutes=5)

def record_api_error(error, request):
    endpoint = request.url.path
    tracker.record_error(error.error_code, endpoint)
```

### Error Dashboards

uno provides integration with monitoring dashboards to visualize error metrics:

```python
from uno.core.monitoring.dashboard import Dashboard, Panel, Query

# Create error dashboard
dashboard = Dashboard(
    title="Error Monitoring",
    description="Error rates and patterns",
    refresh_interval_seconds=60
)

# Add panels to dashboard
dashboard.add_panel(
    Panel(
        title="Errors by Category",
        type="pie",
        query=Query(
            metric="errors_total",
            aggregation="sum",
            group_by=["category"],
            time_range="last_24h"
        )
    )
)

dashboard.add_panel(
    Panel(
        title="Error Rate Over Time",
        type="line",
        query=Query(
            metric="error_rate",
            aggregation="avg",
            group_by=["error_code"],
            time_range="last_24h"
        )
    )
)

dashboard.add_panel(
    Panel(
        title="Top Error Endpoints",
        type="table",
        query=Query(
            metric="error_rate",
            aggregation="avg",
            group_by=["endpoint"],
            time_range="last_24h",
            order_by="value",
            limit=10
        )
    )
)

# Register dashboard
from uno.core.monitoring.dashboard import DashboardRegistry
DashboardRegistry.register(dashboard)
```

## APM Integration

Application Performance Monitoring (APM) provides comprehensive error tracking and performance insights.

### OpenTelemetry Integration

uno integrates with OpenTelemetry to provide distributed tracing and error tracking:

```python
from uno.core.monitoring.tracing import configure_tracing, get_tracer
from opentelemetry.trace.status import Status, StatusCode
from uno.core.errors import UnoError, ErrorCode

# Configure OpenTelemetry
configure_tracing(
    service_name="my-service",
    exporter="otlp",  # OpenTelemetry Protocol
    endpoint="https://otel-collector.example.com:4317"
)

# Get a tracer
tracer = get_tracer(__name__)

# Use in code
@tracer.start_as_current_span("process_order")
def process_order(order_id):
    current_span = tracer.get_current_span()
    current_span.set_attribute("order_id", order_id)
    
    try:
        # Process order logic
        validate_order(order_id)
        apply_payment(order_id)
        fulfill_order(order_id)
    except UnoError as e:
        # Record error in span
        current_span.record_exception(e)
        current_span.set_status(
            Status(StatusCode.ERROR, f"{e.error_code}: {e.message}")
        )
        
        # Add error details to span
        current_span.set_attribute("error.code", e.error_code)
        current_span.set_attribute("error.category", e.category.name if e.category else "UNKNOWN")
        current_span.set_attribute("error.severity", e.severity.name if e.severity else "UNKNOWN")
        
        # Add context as attributes
        for key, value in e.context.items():
            if isinstance(value, (str, int, float, bool)):
                current_span.set_attribute(f"error.context.{key}", value)
        
        raise
```

### FastAPI Integration

Integrate APM with FastAPI for comprehensive API error tracking:

```python
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from uno.core.monitoring.tracing import configure_tracing
from uno.core.errors.fastapi_error_handlers import setup_error_handlers
from uno.core.errors import UnoError

# Create FastAPI app
app = FastAPI()

# Set up OpenTelemetry tracing
configure_tracing(
    service_name="api-service",
    exporter="otlp",
    endpoint="https://otel-collector.example.com:4317"
)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(
    app,
    excluded_urls="health,metrics",
    tracer_provider=None,
)

# Configure error handlers that integrate with tracing
setup_error_handlers(app, include_tracebacks=False)

# Middleware for tracking and reporting errors
@app.middleware("http")
async def error_tracking_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            # Track API errors from response status
            track_error_from_response(request, response)
        return response
    except UnoError as e:
        # Will be caught by error handlers
        raise
    except Exception as e:
        # Unexpected errors
        track_unexpected_error(request, e)
        raise
```

### Prometheus Integration

Integrate with Prometheus for error metrics collection and alerting:

```python
from uno.core.monitoring.metrics import PrometheusExporter
from uno.core.monitoring.metrics import MetricsManager
from prometheus_client import Counter, Histogram

# Configure Prometheus metrics
metrics = MetricsManager.get_instance()
metrics.configure_exporter(PrometheusExporter(port=8000, path="/metrics"))

# Define error metrics
error_counter = Counter(
    "app_errors_total",
    "Total errors by code and category",
    ["error_code", "category", "severity"]
)

error_duration = Histogram(
    "app_error_handling_duration_seconds",
    "Error handling duration in seconds",
    ["error_code"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Use in error handler
def handle_error(error: UnoError):
    error_counter.labels(
        error_code=error.error_code,
        category=error.category.name if error.category else "UNKNOWN",
        severity=error.severity.name if error.severity else "UNKNOWN"
    ).inc()
    
    # Measure error handling time
    with error_duration.labels(error_code=error.error_code).time():
        # Error handling logic
        process_error(error)
```

## Error Analysis Techniques

### Pattern Detection

Detect patterns in error occurrences to identify systemic issues:

```python
from uno.core.monitoring.analysis import ErrorAnalyzer, ErrorPattern
from datetime import timedelta

# Configure error analyzer
analyzer = ErrorAnalyzer()

# Define patterns to detect
analyzer.add_pattern(
    ErrorPattern(
        name="Database Connection Spikes",
        error_code=ErrorCode.DB_CONNECTION_ERROR,
        threshold=5,  # Errors per minute
        window=timedelta(minutes=5),
        description="Spike in database connection errors"
    )
)

analyzer.add_pattern(
    ErrorPattern(
        name="Authentication Failures",
        error_code=ErrorCode.AUTHENTICATION_ERROR,
        threshold=10,  # Errors per minute
        window=timedelta(minutes=10),
        context_pattern={"user_ip": lambda ip: ip.startswith("192.168.")},
        description="Multiple authentication failures from internal network"
    )
)

# Analyze error patterns
detected_patterns = analyzer.analyze()
for pattern in detected_patterns:
    print(f"Detected: {pattern.name} - {pattern.description}")
    print(f"Count: {pattern.count} in last {pattern.window}")
    print(f"Latest instances: {pattern.latest_instances}")
```

### Error Correlation

Correlate errors with system metrics to identify root causes:

```python
from uno.core.monitoring.analysis import ErrorCorrelator
from datetime import datetime, timedelta

# Configure error correlator
correlator = ErrorCorrelator()

# Add metrics to correlate with errors
correlator.add_metric("cpu_usage_percent")
correlator.add_metric("memory_usage_percent")
correlator.add_metric("disk_io_utilization")
correlator.add_metric("db_connections_active")
correlator.add_metric("http_requests_per_second")

# Analyze correlations for a specific error code
correlations = correlator.analyze(
    error_code=ErrorCode.DB_QUERY_ERROR,
    time_range=(datetime.now() - timedelta(hours=24), datetime.now()),
    window=timedelta(minutes=5)
)

# Print correlations
for metric, correlation in correlations.items():
    print(f"Correlation with {metric}: {correlation.coefficient}")
    print(f"Statistical significance: {correlation.p_value}")
    if correlation.is_significant:
        print(f"SIGNIFICANT CORRELATION: {correlation.interpretation}")
```

### Predictive Error Detection

Use machine learning to predict errors before they occur:

```python
from uno.core.monitoring.prediction import ErrorPredictor
from datetime import timedelta

# Configure error predictor
predictor = ErrorPredictor(
    error_code=ErrorCode.API_RATE_LIMIT_ERROR,
    prediction_window=timedelta(minutes=10),
    features=[
        "http_requests_per_second",
        "api_latency_p95",
        "unique_clients_count",
        "cache_hit_ratio"
    ]
)

# Train the predictor
predictor.train(time_range=("2023-01-01", "2023-06-01"))

# Make predictions
predictions = predictor.predict()
if predictions.probability > 0.8:
    print(f"High probability of {ErrorCode.API_RATE_LIMIT_ERROR} in next "
          f"{predictor.prediction_window}!")
    print(f"Probability: {predictions.probability:.2f}")
    print(f"Contributing factors: {predictions.factors}")
```

## Setting Up Error Alerting

Configure alerts for critical error conditions:

```python
from uno.core.monitoring.alerts import AlertManager, AlertRule, AlertChannel
from datetime import timedelta

# Configure alert manager
alerts = AlertManager.get_instance()

# Define alert channels
alerts.add_channel(
    AlertChannel(
        name="ops_email",
        type="email",
        recipients=["ops@example.com"]
    )
)

alerts.add_channel(
    AlertChannel(
        name="critical_slack",
        type="slack",
        webhook_url="https://hooks.slack.com/services/XXX/YYY/ZZZ",
        channel="#alerts-critical"
    )
)

# Define alert rules
alerts.add_rule(
    AlertRule(
        name="high_error_rate",
        description="High rate of errors",
        query="error_rate > 5",
        duration=timedelta(minutes=5),
        severity="warning",
        channels=["ops_email"]
    )
)

alerts.add_rule(
    AlertRule(
        name="critical_errors",
        description="Critical severity errors",
        query='errors_total{severity="CRITICAL"} > 0',
        duration=timedelta(minutes=1),
        severity="critical",
        channels=["ops_email", "critical_slack"]
    )
)

alerts.add_rule(
    AlertRule(
        name="authentication_failures",
        description="Multiple authentication failures from same source",
        query='errors_total{error_code="AUTH-0002"} > 5',
        group_by=["user_ip"],
        duration=timedelta(minutes=5),
        severity="warning",
        channels=["ops_email"]
    )
)
```

## Error Health Checks

Implement health checks to monitor error status:

```python
from fastapi import FastAPI
from uno.core.monitoring.health import HealthCheck, Status
from uno.core.errors import ErrorCatalog

app = FastAPI()

# Create health check endpoint
health_check = HealthCheck()

# Add error-related checks
@health_check.check("recent_errors")
async def check_recent_errors():
    # Get error counts for last 5 minutes
    from uno.core.monitoring.metrics import query_metrics
    
    error_count = await query_metrics(
        metric="errors_total",
        aggregation="sum",
        time_range="last_5m"
    )
    
    if error_count > 100:
        return Status.UNHEALTHY, f"High error rate: {error_count} errors in last 5m"
    elif error_count > 20:
        return Status.DEGRADED, f"Elevated error rate: {error_count} errors in last 5m"
    return Status.HEALTHY, "Normal error rate"

@health_check.check("critical_errors")
async def check_critical_errors():
    # Check for any critical errors in last 15 minutes
    from uno.core.monitoring.metrics import query_metrics
    
    critical_count = await query_metrics(
        metric="errors_total",
        aggregation="sum",
        filters={"severity": "CRITICAL"},
        time_range="last_15m"
    )
    
    if critical_count > 0:
        return Status.UNHEALTHY, f"{critical_count} critical errors in last 15m"
    return Status.HEALTHY, "No critical errors"

# Register health check
app.add_api_route("/health", health_check.endpoint)
```

## Common Error Monitoring Patterns

### Circuit Breaker Pattern

Implement a circuit breaker to prevent cascading failures:

```python
from uno.core.errors import UnoError, ErrorCode
from datetime import datetime, timedelta

class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold=5, reset_timeout=timedelta(minutes=1)):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def execute(self, func, *args, **kwargs):
        """Execute function with circuit breaker pattern."""
        # Check if circuit is OPEN (tripped)
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise UnoError(
                    "Circuit breaker is open",
                    ErrorCode.DEPENDENCY_ERROR,
                    circuit_state=self.state,
                    failure_count=self.failure_count,
                    last_failure=self.last_failure_time
                )
        
        try:
            result = func(*args, **kwargs)
            
            # If successful and HALF_OPEN, reset circuit
            if self.state == "HALF_OPEN":
                self._reset()
            
            return result
            
        except Exception as e:
            # Record failure
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            # Check if threshold exceeded
            if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            # Re-open circuit if still failing in HALF_OPEN state
            if self.state == "HALF_OPEN":
                self.state = "OPEN"
            
            # Wrap in UnoError if needed
            if not isinstance(e, UnoError):
                raise UnoError(
                    f"Service call failed: {str(e)}",
                    ErrorCode.DEPENDENCY_ERROR,
                    circuit_state=self.state,
                    failure_count=self.failure_count,
                    original_error=str(e),
                    circuit_tripped=(self.state == "OPEN")
                )
            raise
    
    def _should_attempt_reset(self):
        """Check if enough time has passed to try resetting circuit."""
        if not self.last_failure_time:
            return True
        
        time_since_last_failure = datetime.now() - self.last_failure_time
        return time_since_last_failure >= self.reset_timeout
    
    def _reset(self):
        """Reset the circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"

# Usage example
payment_circuit = CircuitBreaker(failure_threshold=3, reset_timeout=timedelta(minutes=5))

def process_payment(payment_id):
    return payment_circuit.execute(
        payment_service.process,
        payment_id=payment_id
    )
```

### Error Budget Pattern

Monitor error budgets to track service reliability:

```python
from uno.core.monitoring.metrics import MetricsManager, Gauge
from datetime import datetime, timedelta

class ErrorBudget:
    """Error budget implementation for service reliability tracking."""
    
    def __init__(self, service_name, error_threshold_percent=0.1, window_days=30):
        self.service_name = service_name
        self.error_threshold = error_threshold_percent  # 0.1 = 99.9% availability
        self.window = timedelta(days=window_days)
        
        # Set up metrics
        metrics = MetricsManager.get_instance()
        self.budget_remaining_gauge = metrics.create_gauge(
            name="error_budget_remaining_percent",
            description="Percent of error budget remaining",
            labels=["service"]
        )
        self.budget_consumed_gauge = metrics.create_gauge(
            name="error_budget_consumed_percent",
            description="Percent of error budget consumed",
            labels=["service"]
        )
    
    async def update(self):
        """Update error budget metrics based on current error rates."""
        # Get total requests and errors in the window
        from uno.core.monitoring.metrics import query_metrics
        
        total_requests = await query_metrics(
            metric="http_requests_total",
            aggregation="sum",
            filters={"service": self.service_name},
            time_range=f"last_{self.window.days}d"
        )
        
        total_errors = await query_metrics(
            metric="errors_total",
            aggregation="sum",
            filters={"service": self.service_name},
            time_range=f"last_{self.window.days}d"
        )
        
        if total_requests == 0:
            error_rate = 0
        else:
            error_rate = total_errors / total_requests
        
        # Calculate budget metrics
        budget_consumed_percent = (error_rate / self.error_threshold) * 100
        budget_remaining_percent = max(0, 100 - budget_consumed_percent)
        
        # Update gauges
        self.budget_consumed_gauge.set(
            value=budget_consumed_percent,
            labels={"service": self.service_name}
        )
        self.budget_remaining_gauge.set(
            value=budget_remaining_percent,
            labels={"service": self.service_name}
        )
        
        return {
            "error_rate": error_rate,
            "threshold": self.error_threshold,
            "budget_consumed_percent": budget_consumed_percent,
            "budget_remaining_percent": budget_remaining_percent,
            "total_requests": total_requests,
            "total_errors": total_errors
        }

# Usage
budget_tracker = ErrorBudget(
    service_name="payment-api",
    error_threshold_percent=0.001,  # 99.9% availability
    window_days=30
)

# Schedule regular updates
import asyncio
async def update_budgets():
    while True:
        await budget_tracker.update()
        await asyncio.sleep(300)  # Every 5 minutes

asyncio.create_task(update_budgets())
```

## Integrating with External APM Tools

### New Relic Integration

Integrate with New Relic for comprehensive error tracking:

```python
from newrelic.agent import initialize, register_application, record_exception
from uno.core.errors import UnoError

# Initialize New Relic
initialize('newrelic.ini')
app = register_application()

def report_error_to_new_relic(error: UnoError, request=None):
    """Report an error to New Relic."""
    # Add custom attributes
    params = {
        "error_code": error.error_code,
        "category": error.category.name if error.category else "UNKNOWN",
        "severity": error.severity.name if error.severity else "UNKNOWN",
    }
    
    # Add context as attributes
    for key, value in error.context.items():
        if isinstance(value, (str, int, float, bool)):
            params[f"context.{key}"] = value
    
    # Record exception with New Relic
    record_exception(error, params=params)
```

### Datadog Integration

Integrate with Datadog for advanced error monitoring:

```python
from ddtrace import tracer, config
from uno.core.errors import UnoError

# Configure Datadog
config.service = "my-service"
config.env = "production"
config.version = "1.2.3"

def report_error_to_datadog(error: UnoError):
    """Report an error to Datadog."""
    # Get current span if in a traced context
    span = tracer.current_span()
    if span:
        # Add error to span
        span.set_tag("error", True)
        span.set_tag("error.msg", error.message)
        span.set_tag("error.code", error.error_code)
        span.set_tag("error.category", error.category.name if error.category else "UNKNOWN")
        span.set_tag("error.severity", error.severity.name if error.severity else "UNKNOWN")
        
        # Add context as tags
        for key, value in error.context.items():
            if isinstance(value, (str, int, float, bool)):
                span.set_tag(f"error.context.{key}", value)
```

### Sentry Integration

Integrate with Sentry for detailed error reporting:

```python
import sentry_sdk
from sentry_sdk import configure_scope
from uno.core.errors import UnoError

# Configure Sentry
sentry_sdk.init(
    dsn="https://examplePublicKey@o0.ingest.sentry.io/0",
    environment="production",
    release="1.2.3",
)

def report_error_to_sentry(error: UnoError):
    """Report an error to Sentry."""
    with configure_scope() as scope:
        # Set tags
        scope.set_tag("error_code", error.error_code)
        
        if error.category:
            scope.set_tag("error_category", error.category.name)
        
        if error.severity:
            scope.set_tag("error_severity", error.severity.name)
        
        # Add context data
        scope.set_context("error_context", error.context)
        
        # Set extras
        scope.set_extra("http_status_code", error.http_status_code)
        scope.set_extra("retry_allowed", error.retry_allowed)
        
        # Report the exception
        sentry_sdk.capture_exception(error)
```

## Best Practices for Error Monitoring

1. **Collect Comprehensive Metrics**:
   - Track error counts by code, category, severity
   - Monitor error rates over time
   - Measure impact of errors on response times
   - Collect context information with each error

2. **Set Up Appropriate Alerts**:
   - Alert on critical errors immediately
   - Set thresholds for error rates
   - Configure different notification channels based on severity
   - Avoid alert fatigue with proper grouping and throttling

3. **Use Structured Error Logging**:
   - Log errors in machine-parseable format (JSON)
   - Include consistent context with every error
   - Use appropriate log levels based on error severity
   - Correlate logs with traces using trace IDs

4. **Implement Health Checks**:
   - Include error status in health check endpoints
   - Expose error rate metrics for monitoring systems
   - Implement status pages with error information
   - Use circuit breakers to prevent cascading failures

5. **Review Error Reports Regularly**:
   - Schedule regular reviews of error reports
   - Look for patterns and trends
   - Track error rates against thresholds
   - Correlate with system changes and deployments

6. **Automate Error Analysis**:
   - Set up automated error classification
   - Use anomaly detection for unusual error patterns
   - Correlate errors with system metrics
   - Implement predictive error detection where possible

7. **Integrate with APM Tools**:
   - Use OpenTelemetry for standardized instrumentation
   - Integrate with your preferred APM platform
   - Configure comprehensive dashboards
   - Link errors to traces and logs

8. **Establish Error Budgets**:
   - Define acceptable error rates for services
   - Track budget consumption over time
   - Use error budgets to guide development priorities
   - Alert when error budget is being depleted too quickly

## See Also

- [Error Handling Overview](overview.md) - Core error handling concepts
- [Expanded Error Catalog](expanded_catalog.md) - Comprehensive error code catalog
- [Consistent Error Handling](consistent_handling.md) - Guidelines for error handling across layers
- [APM Integration](apm.md) - Detailed APM integration guide