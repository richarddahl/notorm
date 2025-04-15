# Performance Profiling Tools

The Uno framework includes a comprehensive set of performance profiling tools that help you identify and resolve performance bottlenecks in your applications. These tools provide insights into SQL query performance, endpoint responsiveness, memory usage, and CPU utilization.

## Profiling Dashboard

The profiling dashboard provides a visual interface for monitoring and analyzing performance metrics in real-time.

### Starting the Dashboard

To start the profiling dashboard:

```bash
python -m uno.devtools.cli.main profile dashboard
```

By default, the dashboard starts at `http://localhost:8765`. You can customize the host and port:

```bash
python -m uno.devtools.cli.main profile dashboard --host 0.0.0.0 --port 9000
```

### Profiling an Application

To profile a specific FastAPI application:

```bash
python -m uno.devtools.cli.main profile dashboard --app "myapp.main:app"
```

This will load your application and apply profiling middleware to collect metrics.

### Dashboard Features

The profiling dashboard provides several powerful features:

1. **Overview**: A comprehensive summary of all metrics and identified performance issues across your application. Get a quick visual snapshot of your application's health and identify areas that need attention.

2. **SQL Queries Analysis**:
   - **Slow Query Detection**: Identify queries that exceed performance thresholds
   - **Query Pattern Analysis**: Group similar queries to detect inefficient patterns
   - **N+1 Query Detection**: Automatically detect N+1 query anti-patterns that can severely impact performance
   - **Query Statistics**: View detailed statistics including average duration, max duration, and 95th percentile timing

3. **Endpoint Performance Analysis**:
   - **Slow Endpoint Detection**: Identify endpoints with slow response times
   - **Error Rate Monitoring**: Detect endpoints with high error rates
   - **Status Code Distribution**: Analyze HTTP status code patterns across endpoints
   - **Request Volume Tracking**: Monitor which endpoints receive the most traffic

4. **Resource Utilization Monitoring**:
   - **Real-time Graphs**: Visual representation of CPU and memory usage over time
   - **System vs. Process Metrics**: Compare application resource usage against overall system metrics
   - **Configurable Time Windows**: View resource utilization across different time spans
   - **Peak Usage Tracking**: Identify resource usage spikes and patterns

5. **Function Performance Analysis**:
   - **Hotspot Detection**: Identify functions consuming disproportionate CPU time
   - **Slow Function Tracking**: Monitor individual function execution times
   - **Call Frequency Analysis**: See which functions are called most frequently
   - **Statistical Breakdowns**: View detailed timing statistics for all monitored functions

Each dashboard module includes detailed recommendations for optimizing the identified issues and improving your application's performance.

## Profiling Middleware

You can also integrate the profiling middleware directly into your FastAPI application:

```python
from fastapi import FastAPI
from uno.devtools.profiler.middleware.profiling_middleware import ProfilerMiddleware

app = FastAPI()

# Add profiling middleware
app.add_middleware(```

ProfilerMiddleware,
enabled=True,  # Only enable in development
collect_sql=True,
collect_resources=True,
slow_request_threshold=1.0,  # 1 second
slow_query_threshold=0.5,    # 0.5 seconds
```
)
```

## Function Profiling

### Profiling Individual Functions

You can profile individual functions using the CLI:

```bash
python -m uno.devtools.cli.main profile run "myapp.utils:process_data"
```

Options:

- `--output`: Output format (text, json, html)
- `--output-file`: Save results to file
- `--detailed`: Enable detailed profiling with cProfile
- `--use-yappi`: Use yappi for multi-threaded profiling
- `--max-depth`: Maximum call depth to display

### Memory Profiling

For memory profiling of functions:

```bash
python -m uno.devtools.cli.main profile memory "myapp.utils:process_data"
```

Options:

- `--use-tracemalloc`: Use tracemalloc for detailed tracking
- `--interval`: Interval between memory snapshots

### Finding Hotspots

To identify performance hotspots in a module:

```bash
python -m uno.devtools.cli.main profile hotspots "myapp.models"
```

## Programmatic Usage

### Function Decorator

The profiler can be used as a decorator:

```python
from uno.devtools.profiler.core.collector import FunctionCollector

profiler = FunctionCollector()

@profiler.profile_function
def my_function():```

# Function code
pass
```
```

### Context Manager

For profiling specific blocks of code:

```python
from uno.devtools.profiling.profiler import Profiler

with Profiler("operation_name") as profiler:```

# Code to profile
result = perform_operation()
```
```

### Memory Tracking

For tracking memory usage:

```python
from uno.devtools.profiling.memory import MemoryProfiler

with MemoryProfiler() as profiler:```

# Code to track memory usage
result = process_large_dataset()
```
```

## Best Practices

1. **Enable Profiling Only in Development**: The profiling tools add overhead, so enable them only in development or staging environments.

2. **Focus on Hotspots**: Use the dashboard to identify the most significant performance issues rather than trying to optimize everything.

3. **Profile with Production-Like Data**: Use realistic data volumes to identify scaling issues.

4. **Monitor Over Time**: Check the dashboard periodically as your application grows to catch performance regressions early.

5. **N+1 Query Detection**: Pay special attention to N+1 query warnings, as they often indicate significant performance opportunities.

## Common Performance Issues

The profiling tools can help identify several common performance issues:

### SQL Performance Issues

- **N+1 Queries**: Multiple similar queries executed in a loop
- **Slow Queries**: Individual queries taking too long to execute
- **Missing Indexes**: Queries not using appropriate indexes

### Endpoint Performance Issues

- **Slow Endpoints**: Endpoints with high average response times
- **Error-Prone Endpoints**: Endpoints with high error rates

### Function Performance Issues

- **Hotspots**: Functions consuming disproportionate CPU time
- **Memory Leaks**: Functions with increasing memory usage over time

## Troubleshooting

### Dashboard Not Starting

If the dashboard fails to start:

1. Ensure you have installed the required dependencies:
   ```bash
   pip install fastapi uvicorn psutil
   ```

2. Check if the specified port is already in use:
   ```bash
   lsof -i :8765
   ```

### Missing SQL Metrics

If SQL metrics are not appearing:

1. Ensure your database operations are using supported drivers (psycopg2, psycopg3, asyncpg, or SQLAlchemy)
2. Check that the middleware is correctly configured with `collect_sql=True`

### Memory Profiling Issues

For issues with memory profiling:

1. Ensure psutil is installed:
   ```bash
   pip install psutil
   ```

2. For tracemalloc features, ensure you're using Python 3.6 or later

## Integration with Other Tools

The profiling dashboard can be used alongside other performance tools:

- **APM Systems**: Application Performance Monitoring systems like New Relic or Datadog
- **Database Monitoring**: Tools like PgHero for PostgreSQL monitoring
- **System Monitoring**: Tools like Prometheus and Grafana

By combining Uno's profiling tools with these external tools, you can gain comprehensive insights into your application's performance at all levels.