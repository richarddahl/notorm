# Query Optimizer Metrics

The query optimizer metrics system provides tools to collect, aggregate, and monitor performance metrics from the query optimizer.

## Overview

Optimizing database queries is a continuous process that requires monitoring and measurement. The optimizer metrics system provides a comprehensive framework for collecting and analyzing performance data from the query optimizer, helping you track the effectiveness of optimizations and identify areas for improvement.

## Features

- **Metrics collection**: Capture detailed performance metrics from the query optimizer
- **Time-series tracking**: Store metrics over time to track trends and improvements
- **Reporting**: Generate comprehensive reports on query performance
- **Middleware integration**: Easily integrate with web frameworks like FastAPI
- **Monitoring integration**: Export metrics to monitoring systems
- **Decorators**: Track performance of specific query functions

## Components

### OptimizerMetricsSnapshot

Captures a point-in-time snapshot of query optimizer metrics.

```python
# Create a snapshot from an optimizer
snapshot = OptimizerMetricsSnapshot.from_optimizer(optimizer)

# Access metrics
print(f"Query count: {snapshot.query_count}")
print(f"Slow query count: {snapshot.slow_query_count}")
print(f"Avg execution time: {snapshot.avg_execution_time}")
print(f"95th percentile execution time: {snapshot.p95_execution_time}")
```

### OptimizerMetricsCollector

Collects and aggregates metrics from the query optimizer over time.

```python
# Create collector with metrics manager integration
metrics_collector = OptimizerMetricsCollector(
    metrics_manager=metrics_manager
)

# Collect metrics
snapshot = metrics_collector.collect_metrics(optimizer)

# Get historical snapshots
all_snapshots = metrics_collector.get_snapshots()
recent_snapshots = metrics_collector.get_snapshots(
    start_time=time.time() - 3600,  # Last hour
    end_time=time.time()
)

# Generate a report
report = metrics_collector.generate_report(optimizer)
```

### OptimizerMetricsMiddleware

Middleware for collecting query optimizer metrics in web applications.

```python
# Create middleware for FastAPI
app.add_middleware(
    OptimizerMetricsMiddleware,
    metrics_collector=metrics_collector,
    optimizer_factory=get_optimizer
)
```

## Usage Examples

### Basic Collection

```python
# Create session and optimizer
async with enhanced_pool_session() as session:
    optimizer = QueryOptimizer(session=session)
    
    # Create metrics collector
    metrics_collector = OptimizerMetricsCollector()
    
    # Use the optimizer
    # (execute queries, analyze plans, etc.)
    
    # Collect metrics
    snapshot = metrics_collector.collect_metrics(optimizer)
    
    # Display metrics
    print(f"Query count: {snapshot.query_count}")
    print(f"Avg execution time: {snapshot.avg_execution_time:.2f}s")
```

### Tracking Performance Over Time

```python
# Create metrics collector
metrics_collector = OptimizerMetricsCollector()

# Collect metrics at regular intervals
for _ in range(10):
    # Use the optimizer
    # (execute queries, analyze plans, etc.)
    
    # Collect a snapshot
    metrics_collector.collect_metrics(optimizer)
    
    # Wait for next interval
    await asyncio.sleep(300)  # Every 5 minutes

# Generate a report with trends
report = metrics_collector.generate_report()
```

### Tracking Specific Query Functions

```python
# Create metrics collector
metrics_collector = OptimizerMetricsCollector()

# Define a query function with metrics tracking
@with_query_metrics(optimizer, metrics_collector)
async def get_users(session, status=None):
    # Query logic
    query = select(User)
    if status:
        query = query.where(User.status == status)
    result = await session.execute(query)
    return result.scalars().all()

# Call the function
users = await get_users(session, status="active")
```

### Measuring Query Performance

```python
# Track query performance
@track_query_performance(metrics_collector, optimizer)
async def get_user_orders(session, user_id):
    query = select(Order).where(Order.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().all()

# Performance statistics are collected automatically
orders = await get_user_orders(session, user_id=123)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from uno.database.optimizer_metrics import OptimizerMetricsMiddleware

app = FastAPI()

# Configure middleware
app.add_middleware(
    OptimizerMetricsMiddleware,
    metrics_collector=metrics_collector,
    optimizer_factory=lambda: get_optimizer()
)

# Define your API endpoints
@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_session)):
    # Use the optimizer
    query = "SELECT * FROM users WHERE status = 'active'"
    result = await optimizer.execute_optimized_query(query)
    return result
```

### Generating Reports

```python
# Generate a comprehensive report
report = metrics_collector.generate_report(optimizer)

# Display report
print(f"Time range: {report['time_range']['start']} - {report['time_range']['end']}")
print(f"Query count: {report['latest']['query_count']}")
print(f"Slow query count: {report['latest']['slow_query_count']}")

# Check trends if available
if 'trends' in report:
    print(f"Query count change: {report['trends']['query_count_change']}")
    print(f"Execution time change: {report['trends']['avg_execution_time_change']:.2f}s")
```

## Metrics Integration

The metrics system integrates with the core monitoring system:

```python
from uno.core.monitoring.metrics import MetricsManager

# Create metrics manager
metrics_manager = MetricsManager()

# Create metrics collector with manager
metrics_collector = OptimizerMetricsCollector(
    metrics_manager=metrics_manager
)

# Metrics are automatically registered and recorded
metrics_collector.collect_metrics(optimizer)
```

## Collecting Multiple Metric Types

The metrics system can collect various types of optimizer metrics:

```python
# Collect general optimizer metrics
snapshot = metrics_collector.collect_metrics(optimizer)

# Collect metrics specific to the PostgreSQL optimizer
pg_optimizer = create_pg_optimizer(session=session)
pg_snapshot = metrics_collector.collect_metrics(pg_optimizer)

# Enhanced snapshot with additional metadata
snapshot.metadata.update({
    "environment": "production",
    "database_size": db_size,
    "connection_count": connection_count,
})
```

## Report Types

The metrics system can generate various reports:

### Basic Report

```python
report = metrics_collector.generate_report(optimizer)
```

### Time Range Report

```python
# Report for the last hour
report = metrics_collector.generate_report(
    time_range=(time.time() - 3600, time.time())
)
```

### Custom Report

```python
# Custom reporting logic
def generate_custom_report(collector, optimizer):
    # Get snapshots
    snapshots = collector.get_snapshots()
    
    # Calculate custom metrics
    query_throughput = sum(s.query_count for s in snapshots) / len(snapshots)
    avg_slow_queries = sum(s.slow_query_count for s in snapshots) / len(snapshots)
    
    # Generate report
    return {
        "query_throughput": query_throughput,
        "avg_slow_queries": avg_slow_queries,
        "current_recommendations": len(optimizer._index_recommendations),
    }
```

## Monitoring Dashboard Integration

The metrics can be easily integrated with monitoring dashboards:

```python
# Export metrics to Prometheus
for metric_name, metric_value in report['latest'].items():
    prometheus.gauge(f"query_optimizer_{metric_name}", metric_value)

# Export metrics to Grafana
metrics_json = json.dumps(report)
with open("/var/metrics/query_optimizer.json", "w") as f:
    f.write(metrics_json)
```

## Performance Impact

The metrics collection system is designed to have minimal performance impact:

- Snapshots are lightweight and collected at configurable intervals
- Metrics are stored in memory with configurable retention
- Background collection via middleware avoids blocking requests
- Collectors can be disabled in performance-critical environments

## Best Practices

1. **Regular collection**: Collect metrics at regular intervals (e.g., every 5-15 minutes)
2. **Retention policy**: Keep snapshots for a reasonable period (e.g., 24 hours or 1 week)
3. **Focused tracking**: Use decorators to track specific query functions that are performance-critical
4. **Contextual metadata**: Add relevant metadata to snapshots for better analysis
5. **Alerting**: Set up alerts for significant changes in metrics (e.g., increase in slow queries)
6. **Incremental optimization**: Use metrics to guide incremental optimization efforts
7. **Before/after comparison**: Collect metrics before and after implementing optimizations to measure impact

## Advanced Configuration

The metrics system can be customized for specific needs:

```python
# Custom metrics collector configuration
metrics_collector = OptimizerMetricsCollector()
metrics_collector._snapshot_interval = 60  # 1 minute
metrics_collector._max_snapshots = 1440    # 24 hours at 1-minute intervals

# Custom middleware configuration
middleware = OptimizerMetricsMiddleware(
    metrics_collector=metrics_collector,
    optimizer_factory=get_optimizer
)
middleware.collection_interval = 300  # Collect every 5 minutes
```

## Complete Metrics Example

```python
# Import components
from uno.database.optimizer_metrics import (
    OptimizerMetricsCollector,
    OptimizerMetricsMiddleware,
    with_query_metrics,
    collect_optimizer_metrics,
)

# Create session and optimizer
async with enhanced_pool_session() as session:
    optimizer = QueryOptimizer(session=session)
    
    # Create metrics collector
    metrics_collector = OptimizerMetricsCollector()
    
    # Decorate query functions
    @with_query_metrics(optimizer, metrics_collector)
    async def get_users(session, status=None):
        # Query logic
        query = "SELECT * FROM users"
        if status:
            query += f" WHERE status = '{status}'"
        return await optimizer.execute_optimized_query(query)
    
    # Execute some queries
    all_users = await get_users(session)
    active_users = await get_users(session, "active")
    
    # Collect metrics
    snapshot = await collect_optimizer_metrics(optimizer, metrics_collector)
    
    # Generate report
    report = metrics_collector.generate_report()
    
    # Display key metrics
    print(f"Queries tracked: {snapshot.query_count}")
    print(f"Slow queries: {snapshot.slow_query_count}")
    print(f"Avg execution time: {snapshot.avg_execution_time:.2f}s")
    print(f"Recommendations: {snapshot.index_recommendations}")
```