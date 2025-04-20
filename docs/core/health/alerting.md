# Health Alerting

The health alerting system provides a framework for generating alerts based on health check results and delivering them through various channels.

## Overview

The health alerting system extends the health check framework with alerting capabilities. It provides:

1. Alert generation based on health check results
2. Configurable alert rules with throttling and filtering
3. Multiple alert delivery channels (logging, email, webhooks)
4. Alert history tracking
5. Alert acknowledgment workflow

## Key Components

### AlertLevel

The `AlertLevel` enum represents the severity of an alert:

```python
class AlertLevel(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()
```

### Alert

The `Alert` class represents a health check alert:

```python
class Alert(BaseModel):
    id: str
    timestamp: float
    level: AlertLevel
    title: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    source: str
    check_id: str | None = None
    check_name: str | None = None
    group: str | None = None
    status: HealthStatus
    acknowledged: bool = False
    acknowledged_at: Optional[float] = None
    acknowledged_by: str | None = None
    actions_taken: list[str] = Field(default_factory=list)
```

### AlertRule

The `AlertRule` class defines when alerts should be generated:

```python
class AlertRule(BaseModel):
    id: str
    name: str
    description: str | None = None
    enabled: bool = True
    level: AlertLevel
    
    # Targeting
    check_id: str | None = None
    check_name: str | None = None
    group: str | None = None
    tags: list[str] = Field(default_factory=list)
    status: Optional[HealthStatus] = None
    
    # Behavior
    auto_acknowledge: bool = False
    throttle_seconds: int = 300
```

### AlertAction

The `AlertAction` abstract base class defines how alerts are delivered:

```python
class AlertAction(ABC):
    def __init__(self, logger: logging.Logger | None = None): ...
    
    @abstractmethod
    async def send(self, alert: Alert) -> bool: ...
```

### AlertManager

The `AlertManager` class manages alert rules, generation, and delivery:

```python
class AlertManager:
    def __init__(
        self,
        config: Optional[AlertConfig] = None,
        logger: logging.Logger | None = None,
    ): ...
    
    async def add_rule(self, rule: AlertRule) -> None: ...
    async def remove_rule(self, rule_id: str) -> bool: ...
    async def add_action(self, action: AlertAction) -> None: ...
    async def process_health_report(self, report: dict[str, Any]) -> None: ...
    async def acknowledge_alert(self, alert_id: str, username: str | None = None) -> bool: ...
    async def get_recent_alerts(
        self,
        limit: int = 10,
        min_level: Optional[AlertLevel] = None,
        include_acknowledged: bool = False,
    ) -> list[Alert]: ...
```

## Alert Actions

The alerting system provides several built-in alert actions:

### LoggingAlertAction

Sends alerts to the application logs:

```python
class LoggingAlertAction(AlertAction):
    async def send(self, alert: Alert) -> bool: ...
```

### EmailAlertAction

Sends alerts via email:

```python
class EmailAlertAction(AlertAction):
    def __init__(
        self,
        config: AlertConfig,
        logger: logging.Logger | None = None,
    ): ...
    
    async def send(self, alert: Alert) -> bool: ...
```

### WebhookAlertAction

Sends alerts to webhook endpoints:

```python
class WebhookAlertAction(AlertAction):
    def __init__(
        self,
        config: AlertConfig,
        logger: logging.Logger | None = None,
    ): ...
    
    async def send(self, alert: Alert) -> bool: ...
```

## Usage Examples

### Setting Up Alerting

```python
from uno.core.health import setup_health_alerting, AlertConfig, AlertLevel

# Configure alerting
alert_config = AlertConfig(
    enabled=True,
    min_level=AlertLevel.WARNING,
    throttle_seconds=300,
    email_from="alerts@example.com",
    email_to=["ops@example.com", "admin@example.com"],
    smtp_server="smtp.example.com",
    smtp_port=587,
    smtp_user="alerts@example.com",
    smtp_password="your-password",
    smtp_use_tls=True,
    webhook_urls=["https://hooks.slack.com/services/your-webhook-url"],
    alert_history_size=100
)

# Setup alerting
alert_manager = await setup_health_alerting(config=alert_config)
```

### Adding Custom Alert Rules

```python
from uno.core.health import AlertRule, AlertLevel, HealthStatus, get_alert_manager

# Get alert manager
alert_manager = get_alert_manager()

# Add a custom rule for database checks
db_rule = AlertRule(
    id="database-degraded",
    name="Database Performance",
    description="Alert when database performance is degraded",
    enabled=True,
    level=AlertLevel.WARNING,
    group="database",
    status=HealthStatus.DEGRADED,
    throttle_seconds=600
)

await alert_manager.add_rule(db_rule)

# Add a rule for critical API checks
api_rule = AlertRule(
    id="api-failure",
    name="Critical API Failures",
    description="Alert on any critical API failure",
    enabled=True,
    level=AlertLevel.ERROR,
    check_name="api_*",  # Wildcard pattern
    tags=["critical", "api"],
    status=HealthStatus.UNHEALTHY,
    throttle_seconds=300
)

await alert_manager.add_rule(api_rule)
```

### Adding Custom Alert Actions

```python
from uno.core.health import AlertAction, Alert, get_alert_manager
import asyncio

# Create a custom alert action
class SlackAlertAction(AlertAction):
    def __init__(self, webhook_url: str, logger: logging.Logger | None = None):
        super().__init__(logger)
        self.webhook_url = webhook_url
    
    async def send(self, alert: Alert) -> bool:
        try:
            # Format alert for Slack
            message = {
                "text": f"*{alert.title}*",
                "attachments": [
                    {
                        "color": self._get_color(alert.level),
                        "fields": [
                            {"title": "Status", "value": alert.status.name, "short": True},
                            {"title": "Level", "value": alert.level.name, "short": True},
                            {"title": "Check", "value": alert.check_name or "N/A", "short": True},
                            {"title": "Group", "value": alert.group or "N/A", "short": True},
                        ],
                        "text": alert.message,
                        "footer": f"Alert ID: {alert.id}",
                        "ts": alert.timestamp
                    }
                ]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as response:
                    return response.status == 200
        
        except Exception as e:
            self.logger.error(f"Error sending Slack alert: {str(e)}")
            return False
    
    def _get_color(self, level: AlertLevel) -> str:
        colors = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ffcc00",
            AlertLevel.ERROR: "#ff0000",
            AlertLevel.CRITICAL: "#7b0000"
        }
        return colors.get(level, "#cccccc")

# Get alert manager
alert_manager = get_alert_manager()

# Add the custom action
slack_action = SlackAlertAction(webhook_url="https://hooks.slack.com/services/your-webhook-url")
await alert_manager.add_action(slack_action)
```

### Acknowledging Alerts

```python
from uno.core.health import get_alert_manager

# Get alert manager
alert_manager = get_alert_manager()

# Get recent alerts
alerts = await alert_manager.get_recent_alerts(
    limit=10,
    min_level=AlertLevel.WARNING,
    include_acknowledged=False
)

# Acknowledge an alert
if alerts:
    alert_id = alerts[0].id
    acknowledged = await alert_manager.acknowledge_alert(
        alert_id=alert_id,
        username="admin"
    )
    
    if acknowledged:
        print(f"Alert {alert_id} acknowledged")
    else:
        print(f"Failed to acknowledge alert {alert_id}")
```

### Processing Health Reports Manually

```python
from uno.core.health import get_alert_manager, get_health_registry

# Get registry and alert manager
registry = get_health_registry()
alert_manager = get_alert_manager()

# Get health report
report = await registry.get_health_report(force=True)

# Process for alerts
await alert_manager.process_health_report(report)
```

## Integration with FastAPI

The alerting system can be integrated with FastAPI to provide alert management endpoints:

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from uno.core.health import get_alert_manager, AlertLevel

app = FastAPI()
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    # This is just an example - use your actual auth system
    if credentials.username == "admin" and credentials.password == "password":
        return credentials.username
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/alerts")
async def get_alerts(
    limit: int = 10,
    min_level: str = "WARNING",
    include_acknowledged: bool = False,
    username: str = Depends(get_current_user)
):
    """Get recent alerts."""
    alert_manager = get_alert_manager()
    
    # Convert string level to enum
    try:
        level = AlertLevel[min_level.upper()]
    except KeyError:
        level = AlertLevel.WARNING
    
    # Get alerts
    alerts = await alert_manager.get_recent_alerts(
        limit=limit,
        min_level=level,
        include_acknowledged=include_acknowledged
    )
    
    # Convert to dict
    return {"alerts": [alert.to_dict() for alert in alerts]}

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    username: str = Depends(get_current_user)
):
    """Acknowledge an alert."""
    alert_manager = get_alert_manager()
    
    # Acknowledge alert
    acknowledged = await alert_manager.acknowledge_alert(
        alert_id=alert_id,
        username=username
    )
    
    if not acknowledged:
        raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")
    
    return {"status": "acknowledged", "alert_id": alert_id, "username": username}
```

## Creating Custom Alert Rules Dynamically

```python
from fastapi import FastAPI, Depends, HTTPException
from uno.core.health import get_alert_manager, AlertRule, AlertLevel, HealthStatus

app = FastAPI()

@app.post("/alert-rules")
async def create_alert_rule(rule: AlertRule):
    """Create a new alert rule."""
    alert_manager = get_alert_manager()
    
    # Add rule
    await alert_manager.add_rule(rule)
    
    return {"status": "created", "rule_id": rule.id}

@app.delete("/alert-rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule."""
    alert_manager = get_alert_manager()
    
    # Remove rule
    removed = await alert_manager.remove_rule(rule_id)
    
    if not removed:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return {"status": "deleted", "rule_id": rule_id}
```

## Conclusion

The health alerting system provides a powerful way to monitor system health and respond to issues promptly. By configuring appropriate alert rules and actions, you can ensure that the right people are notified when problems occur, enabling faster response and resolution.