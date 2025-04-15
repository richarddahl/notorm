# Resource Monitoring

Resource monitoring provides visibility into the health, performance, and utilization of your application's resources.

## Overview

The resource monitoring system integrates with the resource management framework to:

- Track resource usage and performance metrics
- Monitor resource health and availability
- Generate alerts for resource issues
- Visualize resource utilization over time

## Basic Usage

```python
from uno.core.monitoring.resources import ResourceMonitor
from uno.core.resources import ResourceManager

# Create a resource monitor
resource_manager = ResourceManager()
resource_monitor = ResourceMonitor(resource_manager)

# Start monitoring
resource_monitor.start()

# Later in your application shutdown
resource_monitor.stop()
```

## Monitored Resources

The monitoring system can track various resource types:

- **Database Connections**: Connection pool usage, query performance
- **HTTP Clients**: Request rates, latency, error rates
- **Redis Connections**: Connection health, operation latency
- **Thread Pools**: Utilization, queue depth, task completion time
- **Task Queues**: Queue depth, processing time, failure rates
- **File Handles**: Open handles, I/O operations, throughput
- **Message Brokers**: Queue depths, message rates, consumer lag
- **Custom Resources**: Any resource registered with the resource manager

## Metrics Collection

For each resource, the system collects relevant metrics:

```python
# Database connection metrics example
resource_monitor.add_metric(```

resource_id="main-db",
metric=Gauge(```

name="connection_pool_usage",
description="Current usage of the database connection pool",
labels=["database_name", "pool_id"]
```
)
```
)
```

## Resource Health Integration

The resource monitor integrates with the health check system:

```python
from uno.core.monitoring.health import HealthRegistry
from uno.core.monitoring.resources import ResourceHealthAdapter

health_registry = HealthRegistry()
health_adapter = ResourceHealthAdapter(resource_manager, resource_monitor)
health_registry.register_adapter(health_adapter)
```

## Automatic Resource Discovery

The system can automatically discover and monitor resources:

```python
# Auto-detect and monitor all database connections
resource_monitor.discover_resources(resource_type="database")

# Auto-detect and monitor all resources
resource_monitor.discover_all_resources()
```

## Resource Thresholds and Alerts

Configure thresholds for resource metrics:

```python
from uno.core.monitoring.resources import Threshold, AlertLevel

# Set a threshold for connection pool usage
resource_monitor.set_threshold(```

resource_id="main-db",
metric_name="connection_pool_usage",
threshold=Threshold(```

warning=0.7,  # 70% usage triggers warning
critical=0.9,  # 90% usage triggers critical alert
alert_message="Database connection pool utilization high"
```
)
```
)
```

## Resource Utilization Reports

Generate resource utilization reports:

```python
# Get a report for all database resources
report = resource_monitor.generate_report(resource_type="database")

# Get a report for a specific time range
import datetime
report = resource_monitor.generate_report(```

start_time=datetime.datetime.now() - datetime.timedelta(hours=24),
end_time=datetime.datetime.now()
```
)

# Export the report
report.export_csv("/path/to/report.csv")
```

## Dashboard Integration

The resource monitor integrates with monitoring dashboards:

```python
from uno.core.monitoring.integration import setup_monitoring

app = FastAPI()
setup_monitoring(```

app, 
resource_monitor=resource_monitor,
enable_dashboard=True,
dashboard_path="/monitoring/dashboard"
```
)
```

## Prometheus Integration

Export resource metrics to Prometheus:

```python
from uno.core.monitoring.integration import setup_prometheus_exporter

# Setup the exporter
exporter = setup_prometheus_exporter(resource_monitor)

# In FastAPI
app = FastAPI()
app.include_router(exporter.router, prefix="/metrics", tags=["monitoring"])
```

## Resource Anomaly Detection

The system can detect anomalies in resource behavior:

```python
from uno.core.monitoring.resources import AnomalyDetector

# Create an anomaly detector
detector = AnomalyDetector()

# Register with resource monitor
resource_monitor.set_anomaly_detector(detector)

# Configure anomaly detection for a specific resource
resource_monitor.configure_anomaly_detection(```

resource_id="main-db",
metric_name="query_duration",
sensitivity=0.8,  # Higher values detect more subtle anomalies
training_period=datetime.timedelta(days=7)  # Use 7 days of data for training
```
)
```

## Resource Dependency Mapping

Visualize dependencies between resources:

```python
# Generate a dependency graph
dependency_graph = resource_monitor.generate_dependency_graph()

# Export as various formats
dependency_graph.export_dot("/path/to/dependencies.dot")
dependency_graph.export_json("/path/to/dependencies.json")
```

## Custom Resource Monitors

Create custom monitors for specific resource types:

```python
from uno.core.monitoring.resources import ResourceTypeMonitor

class DatabaseMonitor(ResourceTypeMonitor):```

"""Custom monitor for database connections"""
``````

```
```

def __init__(self, resource_manager):```

super().__init__(resource_manager, resource_type="database")
```
    
def setup_metrics(self):```

"""Setup database-specific metrics"""
self.add_metric(
    name="query_count",
    description="Number of queries executed",
    metric_type="counter",
    labels=["query_type", "database_name"]
)
self.add_metric(
    name="slow_queries",
    description="Number of slow queries",
    metric_type="counter",
    labels=["database_name"]
)
```
    
async def collect_metrics(self, resource):```

"""Collect metrics for a specific database resource"""
stats = await resource.get_statistics()
self.update_metric(
    "query_count", 
    stats["total_queries"],
    labels={"database_name": resource.name, "query_type": "all"}
)
self.update_metric(
    "slow_queries",
    stats["slow_queries"],
    labels={"database_name": resource.name}
)
```
```

# Register the custom monitor
db_monitor = DatabaseMonitor(resource_manager)
resource_monitor.register_type_monitor(db_monitor)
```

This integration ensures that your application's resources are thoroughly monitored, allowing you to detect and address issues before they impact users.