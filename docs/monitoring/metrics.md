# Metrics Collection

The metrics collection system in Uno helps you track numerical values about your application's behavior and performance. It provides counters, gauges, histograms, and timers for measuring different aspects of your application.

## Types of Metrics

The metrics system supports four types of metrics:

1. **Counter**: A value that can only increase (e.g., request count)
2. **Gauge**: A value that can increase or decrease (e.g., active connections)
3. **Histogram**: Distribution of values (e.g., request durations)
4. **Timer**: Special case of histogram for measuring durations

## Using Metrics

### Creating Metrics

To create and use metrics, use the helper functions:

```python
from uno.core.monitoring import counter, gauge, histogram, timer, MetricUnit

# Create a counter
request_counter = await counter(
    name="http_requests_total",
    description="Total number of HTTP requests",
    tags={"handler": "items"}
)

# Create a gauge
active_connections = await gauge(
    name="active_connections",
    description="Number of active connections",
    unit=MetricUnit.COUNT
)

# Create a histogram
request_size = await histogram(
    name="http_request_size_bytes",
    description="HTTP request size in bytes",
    unit=MetricUnit.BYTES
)

# Create a timer
request_duration = await timer(
    name="http_request_duration_milliseconds",
    description="HTTP request duration in milliseconds"
)
```

### Using Metrics

Once created, you can use metrics to record values:

```python
# Increment a counter
await request_counter.increment()

# Set a gauge
await active_connections.set(42)

# Track in-progress operations with a gauge
async with await active_connections.track_inprogress():
    # Do something while incrementing the gauge
    pass

# Record a value in a histogram
await request_size.observe(1024)

# Time an operation
async with await request_duration.time():
    # Operation to time
    await asyncio.sleep(0.1)

# Record a duration directly
await request_duration.record(42.0)
```

### Timing Functions

You can easily time functions using the `timed` decorator:

```python
from uno.core.monitoring import timed

@timed(timer_name="function_duration", description="Duration of my function")
async def my_function():
    # Function to time
    await asyncio.sleep(0.1)
    return "result"
```

## Metrics in FastAPI

The metrics system integrates with FastAPI through the `MetricsMiddleware` and a Prometheus endpoint:

```python
from fastapi import FastAPI
from uno.core.monitoring import MetricsMiddleware, get_metrics_registry

app = FastAPI()

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    registry = get_metrics_registry()
    return Response(
        content=registry.get_prometheus_metrics(),
        media_type="text/plain"
    )
```

The `setup_monitoring` function does this automatically if enabled in the configuration.

## Metrics Exporters

The metrics system supports different exporters for sending metrics to monitoring systems:

### Prometheus Exporter

The Prometheus exporter formats metrics for scraping by Prometheus:

```python
from uno.core.monitoring import PrometheusExporter, get_metrics_registry

# Create exporter
exporter = PrometheusExporter(namespace="my_service")

# Set up metrics registry with exporter
registry = get_metrics_registry()
await registry.setup(
    export_interval=60.0,
    exporters=[exporter]
)
```

### Logging Exporter

The logging exporter logs metrics at regular intervals for debugging:

```python
from uno.core.monitoring import LoggingExporter, get_metrics_registry

# Create exporter
exporter = LoggingExporter()

# Set up metrics registry with exporter
registry = get_metrics_registry()
await registry.setup(
    export_interval=60.0,
    exporters=[exporter]
)
```

## Best Practices

1. **Use Descriptive Names**: Use consistent naming for metrics, with clear prefixes.
2. **Add Tags**: Tags (labels) help filter and group metrics.
3. **Mind Cardinality**: Avoid high-cardinality labels that create too many time series.
4. **Document Units**: Use the `unit` parameter to document the unit of measurement.
5. **Use Appropriate Metric Types**: Use counters for things that increase, gauges for values that go up and down, histograms for distributions.
6. **Batch Operations**: Use the metrics registry to batch operations.

## Advanced Usage

### Getting Histogram Statistics

For histograms and timers, you can get statistical summaries:

```python
# Get statistics for a histogram
stats = await my_histogram.get_statistics()
print(f"Count: {stats['count']}")
print(f"Min: {stats['min']}")
print(f"Max: {stats['max']}")
print(f"Mean: {stats['mean']}")
print(f"Median: {stats['median']}")
print(f"95th percentile: {stats['p95']}")
print(f"99th percentile: {stats['p99']}")
```

### Custom Metric Registry

You can create a custom metrics registry for specific subsystems:

```python
from uno.core.monitoring import MetricsRegistry

# Create a custom registry
my_registry = MetricsRegistry()

# Set up exporters
await my_registry.setup(
    export_interval=30.0,
    exporters=[PrometheusExporter(namespace="my_subsystem")]
)

# Create metrics with this registry
my_counter = await counter(
    name="my_counter",
    registry=my_registry
)
```