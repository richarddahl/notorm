# Cache Monitoring

The Uno caching framework includes comprehensive monitoring capabilities to help track cache performance, diagnose issues, and optimize cache configuration. This document provides an overview of the monitoring features and how to use them effectively.

## Overview

The cache monitoring system collects metrics on all cache operations, including:

- Cache hits and misses
- Operation durations (get, set, delete)
- Error rates and types
- Cache evictions and expirations
- Invalidation events

These metrics can be used to analyze cache effectiveness, identify performance bottlenecks, and alert on potential issues.

## Using the Cache Monitor

### Basic Monitoring

The `CacheMonitor` is automatically initialized when you create a `CacheManager`. You can access it through the manager:

```python
from uno.caching import CacheManager
from uno.caching.monitoring import CacheEventType

# Get the monitor through the cache manager
cache_manager = CacheManager.get_instance()
monitor = cache_manager.monitor

# Get current metrics
metrics = monitor.get_metrics()
print(f"Overall hit rate: {metrics['default'].hit_rate:.1f}%")

# Check cache health
health = monitor.check_health()
if not health['healthy']:```

print(f"Cache health issues: {health['status']}")
for cache_name, cache_health in health['caches'].items():```

if cache_health['issues']:
    print(f"Issues with {cache_name}: {cache_health['issues']}")
```
```
```

### Filtering Metrics

You can filter metrics by cache name and time window:

```python
# Get metrics for a specific cache
user_cache_metrics = monitor.get_metrics(cache_name="user_cache")

# Get metrics for the last minute
recent_metrics = monitor.get_metrics(time_window=60)  # 60 seconds

# Get metrics for a specific cache in the last hour
metrics = monitor.get_metrics(cache_name="product_cache", time_window=3600)
```

### Background Monitoring

You can enable automatic background monitoring that periodically checks cache health and logs issues:

```python
# Start background monitoring that checks every 30 seconds
monitor.start_background_monitoring(interval=30)

# Later, stop background monitoring
monitor.stop_background_monitoring()
```

## Prometheus Integration

The cache monitor can export metrics to Prometheus for advanced monitoring and alerting. To enable this:

```python
from uno.caching.config import CacheConfig, MonitoringConfig

monitoring_config = MonitoringConfig(```

enable_prometheus=True,
prometheus_port=9090  # Default port
```
)

cache_config = CacheConfig(```

monitoring=monitoring_config
```
)

# Create cache manager with prometheus enabled
cache_manager = CacheManager(config=cache_config)
```

This exposes the following Prometheus metrics:

- `cache_hits_total` - Counter of cache hits by cache name
- `cache_misses_total` - Counter of cache misses by cache name
- `cache_operations_total` - Counter of operations by cache name and operation type
- `cache_errors_total` - Counter of errors by cache name
- `cache_operation_duration_seconds` - Histogram of operation durations

## Analyzing Cache Performance

Here are some common metrics to analyze:

### Hit Rate

The hit rate is the percentage of cache lookups that found a value (cache hits divided by total lookups). A higher hit rate indicates better cache effectiveness.

- **High hit rate (>80%)**: Good cache efficiency
- **Medium hit rate (50-80%)**: Acceptable but could be improved
- **Low hit rate (<50%)**: Consider adjusting cache strategies or TTL values

### Response Times

Monitor the average and 95th percentile response times for get operations:

- **p95 get time < 10ms**: Excellent performance
- **p95 get time 10-50ms**: Good performance
- **p95 get time > 50ms**: May indicate cache overloading or infrastructure issues

### Cache Churn

High rates of evictions or expirations compared to the total number of items in the cache can indicate cache thrashing or inefficient TTL settings.

## Metrics Export

For integration with external monitoring systems, you can export cache metrics in JSON format:

```python
metrics_json = monitor.export_metrics_json()

# Example: Write to a file for external processing
import json
with open("cache_metrics.json", "w") as f:```

json.dump(metrics_json, f, indent=2)
```
```

## Practical Tips

1. **Set appropriate alert thresholds** based on your application's requirements. For example, alert if the hit rate drops below 50% or if p95 get time exceeds 100ms.

2. **Monitor error rates** to detect cache connectivity or availability issues. Error rates above 1% should be investigated.

3. **Use time-based analysis** to detect patterns of cache performance throughout the day.

4. **Compare cache metrics before and after changes** to evaluate the impact of cache configuration changes.

5. **Correlate cache performance with application performance** to understand the overall impact of caching on your system.