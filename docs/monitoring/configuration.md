# Monitoring Configuration

The monitoring and observability framework provides flexible configuration options to adapt to different deployment environments and requirements.

## Basic Configuration

The monitoring system can be configured through a configuration object:

```python
from uno.core.monitoring.config import MonitoringConfig

config = MonitoringConfig(```

service_name="my-service",
environment="production",
metrics_enabled=True,
tracing_enabled=True,
health_checks_enabled=True,
resource_monitoring_enabled=True,
event_logging_enabled=True
```
)
```

## Configuration from Environment Variables

Load configuration from environment variables:

```python
from uno.core.monitoring.config import load_config_from_env

config = load_config_from_env()
```

Supported environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| UNO_MONITORING_ENABLED | Enable all monitoring components | True |
| UNO_METRICS_ENABLED | Enable metrics collection | True |
| UNO_TRACING_ENABLED | Enable distributed tracing | True |
| UNO_HEALTH_CHECKS_ENABLED | Enable health checks | True |
| UNO_RESOURCE_MONITORING_ENABLED | Enable resource monitoring | True |
| UNO_EVENT_LOGGING_ENABLED | Enable event logging | True |
| UNO_SERVICE_NAME | Service name for traces and metrics | "uno-service" |
| UNO_ENVIRONMENT | Deployment environment (production, staging, etc.) | "development" |
| UNO_OTLP_ENDPOINT | OpenTelemetry collector endpoint | None |
| UNO_PROMETHEUS_ENDPOINT | Prometheus metrics endpoint path | "/metrics" |
| UNO_LOG_LEVEL | Minimum log level | "INFO" |

## Configuration from Files

Load configuration from a file:

```python
from uno.core.monitoring.config import load_config_from_file

config = load_config_from_file("config/monitoring.json")
```

Example JSON configuration:

```json
{
  "service_name": "my-service",
  "environment": "production",
  "metrics": {```

"enabled": true,
"prometheus_export": true,
"export_interval_seconds": 15
```
  },
  "tracing": {```

"enabled": true,
"sampler": "always_on",
"max_attributes": 128
```
  },
  "health_checks": {```

"enabled": true,
"interval_seconds": 30
```
  },
  "resource_monitoring": {```

"enabled": true,
"collection_interval_seconds": 60
```
  },
  "event_logging": {```

"enabled": true,
"min_level": "INFO",
"console_output": true,
"file_output": "/var/log/application/events.log"
```
  },
  "exporters": {```

"otlp": {
  "endpoint": "http://otel-collector:4317",
  "protocol": "grpc"
},
"prometheus": {
  "endpoint": "/metrics",
  "push_gateway": null
}
```
  }
}
```

## Metrics Configuration

Configure metrics collection:

```python
from uno.core.monitoring.config import MetricsConfig

metrics_config = MetricsConfig(```

enabled=True,
prometheus_export=True,
export_interval_seconds=15,
default_labels={```

"service": "my-service",
"environment": "production"
```
}
```
)
```

## Tracing Configuration

Configure distributed tracing:

```python
from uno.core.monitoring.config import TracingConfig

tracing_config = TracingConfig(```

enabled=True,
sampler="parent_based_always_on",
max_attributes=128,
max_events=32,
max_links=32,
span_processors=[```

{"type": "batch", "max_queue_size": 1000, "max_export_batch_size": 100}
```
]
```
)
```

## Health Check Configuration

Configure health checks:

```python
from uno.core.monitoring.config import HealthCheckConfig

health_config = HealthCheckConfig(```

enabled=True,
interval_seconds=30,
timeout_seconds=5,
include_details=True
```
)
```

## Resource Monitoring Configuration

Configure resource monitoring:

```python
from uno.core.monitoring.config import ResourceMonitoringConfig

resource_config = ResourceMonitoringConfig(```

enabled=True,
collection_interval_seconds=60,
resource_types=["database", "http_client", "redis"],
default_thresholds={```

"utilization": {
    "warning": 0.7,
    "critical": 0.9
}
```
}
```
)
```

## Event Logging Configuration

Configure event logging:

```python
from uno.core.monitoring.config import EventLoggingConfig

event_config = EventLoggingConfig(```

enabled=True,
min_level="INFO",
include_context=True,
console_output=True,
file_output="/var/log/application/events.log",
processors=[```

{"type": "console", "colored": True},
{"type": "json_file", "path": "/var/log/application/events.json"}
```
]
```
)
```

## Exporter Configuration

Configure telemetry data exporters:

```python
from uno.core.monitoring.config import ExporterConfig

exporter_config = ExporterConfig(```

otlp={```

"endpoint": "http://otel-collector:4317",
"protocol": "grpc",
"certificate": "/path/to/cert.pem",
"headers": {"api-key": "${OTLP_API_KEY}"}
```
},
prometheus={```

"endpoint": "/metrics",
"push_gateway": "http://prometheus-pushgateway:9091",
"push_interval_seconds": 15
```
}
```
)
```

## Dynamic Configuration

Update configuration at runtime:

```python
from uno.core.monitoring.config import MonitoringConfigManager

# Create a config manager
config_manager = MonitoringConfigManager()

# Set initial configuration
config_manager.set_config(MonitoringConfig(...))

# Update specific components
config_manager.update_metrics_config(MetricsConfig(export_interval_seconds=30))
config_manager.update_tracing_config(TracingConfig(sampler="always_off"))

# Apply changes to components
config_manager.apply_changes()
```

## Configuration Validation

Validate configuration before applying:

```python
# Validate configuration
validation_result = config.validate()

if not validation_result.is_valid:```

for error in validation_result.errors:```

print(f"Configuration error: {error}")
```
```
```

## Environment-Specific Configuration

Create environment-specific configurations:

```python
from uno.core.monitoring.config import create_environment_config

# Create configs for different environments
dev_config = create_environment_config("development")
staging_config = create_environment_config("staging")
prod_config = create_environment_config("production")

# Use environment detection
current_config = create_environment_config()
```

## Integration with Application Configuration

Integrate with your application's configuration system:

```python
from uno.core.monitoring.config import MonitoringConfig
from your_app.config import AppConfig

def setup_monitoring_from_app_config(app_config: AppConfig) -> MonitoringConfig:```

"""Create monitoring config from application config."""
return MonitoringConfig(```

service_name=app_config.service_name,
environment=app_config.environment,
metrics_enabled=app_config.monitoring.metrics_enabled,
tracing_enabled=app_config.monitoring.tracing_enabled,
# Other settings...
```
)
```
```

## Secret Management

Handle sensitive configuration values:

```python
from uno.core.monitoring.config import ExporterConfig, SecretValue

# Define configuration with secrets
exporter_config = ExporterConfig(```

otlp={```

"headers": {
    "api-key": SecretValue("${OTLP_API_KEY}")
}
```
}
```
)

# Resolve secrets when applying configuration
resolved_config = exporter_config.resolve_secrets()
```

This configuration system provides the flexibility needed to adapt monitoring to different environments while maintaining consistency in your observability approach.