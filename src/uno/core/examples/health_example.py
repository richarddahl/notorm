# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example usage of the health check framework.

This module demonstrates how to use the health check framework to monitor
the health of services and resources in a FastAPI application.
"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, Optional, List

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from uno.core.health import (
    # Main health framework
    health_check,
    HealthStatus,
    HealthCheckResult,
    HealthRegistry,
    get_health_registry,
    register_health_check,
    HealthEndpoint,
    HealthConfig,
    # Dashboard
    HealthDashboard,
    setup_health_dashboard,
    HealthDashboardConfig,
    # Alerting
    AlertConfig,
    AlertLevel,
    AlertRule,
    Alert,
    setup_health_alerting,
    get_alert_manager,
)
from uno.core.logging import get_logger

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = get_logger("health_example")

# Create FastAPI application
app = FastAPI(title="Health Check Example")

# Health check registry
health_registry = get_health_registry()


# Example database connection
class MockDatabase:
    """Mock database for demonstration purposes."""

    def __init__(self):
        self.connected = True
        self.latency = 0.01
        self.error_rate = 0.0

    async def ping(self) -> float:
        """
        Ping the database.

        Returns:
            Latency in seconds

        Raises:
            Exception: If connection fails
        """
        # Simulate random errors
        if random.random() < self.error_rate:
            raise Exception("Database connection error")

        # Simulate latency
        await asyncio.sleep(self.latency)
        return self.latency

    async def simulate_degraded(self):
        """Simulate degraded performance."""
        self.latency = 0.2

    async def simulate_failure(self):
        """Simulate connection failure."""
        self.connected = False
        self.error_rate = 0.8

    async def restore(self):
        """Restore normal operation."""
        self.connected = True
        self.latency = 0.01
        self.error_rate = 0.0


# Example cache service
class MockCache:
    """Mock cache service for demonstration purposes."""

    def __init__(self):
        self.connected = True
        self.hit_rate = 0.9
        self.latency = 0.005

    async def ping(self) -> dict[str, Any]:
        """
        Ping the cache.

        Returns:
            Cache metrics

        Raises:
            Exception: If connection fails
        """
        if not self.connected:
            raise Exception("Cache connection error")

        # Simulate latency
        await asyncio.sleep(self.latency)

        return {"hit_rate": self.hit_rate, "latency": self.latency}

    async def simulate_degraded(self):
        """Simulate degraded performance."""
        self.hit_rate = 0.5
        self.latency = 0.05

    async def simulate_failure(self):
        """Simulate connection failure."""
        self.connected = False

    async def restore(self):
        """Restore normal operation."""
        self.connected = True
        self.hit_rate = 0.9
        self.latency = 0.005


# Example API service
class MockApiService:
    """Mock API service for demonstration purposes."""

    def __init__(self):
        self.available = True
        self.latency = 0.05
        self.error_rate = 0.0

    async def check_status(self) -> dict[str, Any]:
        """
        Check API status.

        Returns:
            API metrics

        Raises:
            Exception: If API is unavailable
        """
        # Simulate random errors
        if random.random() < self.error_rate:
            raise Exception("API service error")

        # Simulate unavailability
        if not self.available:
            raise Exception("API service unavailable")

        # Simulate latency
        await asyncio.sleep(self.latency)

        return {"latency": self.latency, "requests_per_second": random.randint(10, 100)}

    async def simulate_degraded(self):
        """Simulate degraded performance."""
        self.latency = 0.3
        self.error_rate = 0.2

    async def simulate_failure(self):
        """Simulate service failure."""
        self.available = False

    async def restore(self):
        """Restore normal operation."""
        self.available = True
        self.latency = 0.05
        self.error_rate = 0.0


# Create mock services
db = MockDatabase()
cache = MockCache()
api_service = MockApiService()


# Define health checks using decorator
@health_check(
    name="database_connection",
    description="Checks if database connection is healthy",
    tags=["database", "critical"],
    timeout=2.0,
    critical=True,
    group="database",
)
async def check_database():
    """Check database connection health."""
    try:
        latency = await db.ping()

        # Determine status based on latency
        if latency > 0.1:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Database response time is slow: {latency:.3f}s",
                details={"latency": latency},
            )
        else:
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Database connection is healthy",
                details={"latency": latency},
            )

    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}",
            details={"error": str(e)},
        )


@health_check(
    name="cache_connection",
    description="Checks if cache service is healthy",
    tags=["cache"],
    timeout=1.0,
    group="cache",
)
async def check_cache():
    """Check cache service health."""
    try:
        metrics = await cache.ping()

        # Determine status based on hit rate
        hit_rate = metrics["hit_rate"]
        if hit_rate < 0.7:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"Cache hit rate is low: {hit_rate:.2f}",
                details=metrics,
            )
        else:
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Cache service is healthy",
                details=metrics,
            )

    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"Cache service failed: {str(e)}",
            details={"error": str(e)},
        )


# Define a health check manually
async def check_api_service():
    """Check API service health."""
    try:
        metrics = await api_service.check_status()

        # Determine status based on latency
        latency = metrics["latency"]
        if latency > 0.2:
            return HealthCheckResult(
                status=HealthStatus.DEGRADED,
                message=f"API service is slow: {latency:.3f}s",
                details=metrics,
            )
        else:
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="API service is healthy",
                details=metrics,
            )

    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message=f"API service failed: {str(e)}",
            details={"error": str(e)},
        )


# Register health check manually
async def register_api_check():
    """Register API service health check."""
    await register_health_check(
        name="api_service",
        check_func=check_api_service,
        description="Checks if API service is available",
        tags=["api", "external"],
        timeout=3.0,
        critical=True,
        group="api",
    )


# Health check with custom logic
@health_check(
    name="system_resources",
    description="Checks system resource usage",
    tags=["system"],
    group="system",
)
async def check_system_resources():
    """Check system resource usage."""
    # Simulate resource check
    cpu_usage = random.uniform(0.0, 100.0)
    memory_usage = random.uniform(0.0, 100.0)
    disk_usage = random.uniform(0.0, 100.0)

    # Determine status based on resource usage
    status = HealthStatus.HEALTHY
    message = "System resources are healthy"

    if cpu_usage > 80 or memory_usage > 80 or disk_usage > 90:
        status = HealthStatus.DEGRADED
        message = "System resources are under pressure"

    if cpu_usage > 90 or memory_usage > 90 or disk_usage > 95:
        status = HealthStatus.UNHEALTHY
        message = "System resources are critically low"

    return HealthCheckResult(
        status=status,
        message=message,
        details={
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
        },
    )


# Example of a custom health check that returns a boolean
@health_check(
    name="simple_check",
    description="A simple boolean health check",
    tags=["example"],
    group="example",
)
async def simple_check():
    """Simple boolean health check."""
    # Just return True or False - will be converted to HealthCheckResult
    return random.random() > 0.1


# Example of a custom health check that returns a tuple
@health_check(
    name="tuple_check",
    description="A health check that returns a tuple",
    tags=["example"],
    group="example",
)
async def tuple_check():
    """Health check that returns a tuple."""
    # Return (success, message) - will be converted to HealthCheckResult
    success = random.random() > 0.1
    message = "Check passed" if success else "Check failed"
    return success, message


# Setup alerting
async def setup_alerts():
    """Set up health check alerting."""
    # Configure alerting
    alert_config = AlertConfig(
        enabled=True,
        min_level=AlertLevel.WARNING,
        throttle_seconds=30,  # short throttle for demo
        email_from="alerts@example.com",
        email_to=["ops@example.com"],
        smtp_server="smtp.example.com",  # not actually used in this example
        webhook_urls=[],  # no real webhooks in this example
    )

    # Setup alerting
    alert_manager = await setup_health_alerting(config=alert_config)

    # Add custom rules
    db_rule = AlertRule(
        id="critical-db-failure",
        name="Critical Database Failure",
        description="Alert on database failures",
        enabled=True,
        level=AlertLevel.CRITICAL,
        check_name="database_connection",
        status=HealthStatus.UNHEALTHY,
    )

    api_rule = AlertRule(
        id="api-degraded",
        name="API Service Degraded",
        description="Alert when API service is degraded",
        enabled=True,
        level=AlertLevel.WARNING,
        check_name="api_service",
        status=HealthStatus.DEGRADED,
    )

    system_rule = AlertRule(
        id="system-resources",
        name="System Resources",
        description="Alert on system resource issues",
        enabled=True,
        level=AlertLevel.WARNING,
        group="system",
        status=HealthStatus.DEGRADED,
    )

    await alert_manager.add_rule(db_rule)
    await alert_manager.add_rule(api_rule)
    await alert_manager.add_rule(system_rule)


# Configure health dashboard
def configure_dashboard():
    """Configure health dashboard."""
    dashboard_config = HealthDashboardConfig(
        enabled=True,
        route_prefix="/dashboard/health",
        api_prefix="/dashboard/health/api",
        require_auth=False,
        update_interval=5.0,
        history_size=100,
        auto_refresh=True,
    )

    # Setup dashboard
    return setup_health_dashboard(app=app, config=dashboard_config)


# Setup health check endpoints
def setup_health_endpoints():
    """Set up health check endpoints."""
    HealthEndpoint.setup(
        app=app,
        prefix="/health",
        tags=["health"],
        include_details=True,
        register_resource_checks=True,
    )


# API endpoints to simulate service issues


class ServiceAction(BaseModel):
    """Service action request."""

    action: str  # "degrade", "fail", "restore"
    service: str  # "database", "cache", "api"


@app.post("/simulate")
async def simulate_service_issue(action: ServiceAction):
    """
    Simulate service issues.

    Args:
        action: Service action to perform

    Returns:
        Result of the action
    """
    service_map = {"database": db, "cache": cache, "api": api_service}

    if action.service not in service_map:
        raise HTTPException(
            status_code=400, detail=f"Unknown service: {action.service}"
        )

    service = service_map[action.service]

    if action.action == "degrade":
        await service.simulate_degraded()
        return {"status": "ok", "message": f"{action.service} service degraded"}

    elif action.action == "fail":
        await service.simulate_failure()
        return {"status": "ok", "message": f"{action.service} service failed"}

    elif action.action == "restore":
        await service.restore()
        return {"status": "ok", "message": f"{action.service} service restored"}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action.action}")


@app.get("/alerts")
async def get_alerts(
    limit: int = 10, min_level: str = "WARNING", include_acknowledged: bool = False
):
    """
    Get recent alerts.

    Args:
        limit: Maximum number of alerts to return
        min_level: Minimum alert level
        include_acknowledged: Whether to include acknowledged alerts

    Returns:
        Recent alerts
    """
    alert_manager = get_alert_manager()

    # Convert string level to enum
    try:
        level = AlertLevel[min_level.upper()]
    except KeyError:
        level = AlertLevel.WARNING

    # Get alerts
    alerts = await alert_manager.get_recent_alerts(
        limit=limit, min_level=level, include_acknowledged=include_acknowledged
    )

    # Convert to dict
    return {"alerts": [alert.to_dict() for alert in alerts]}


@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """
    Acknowledge an alert.

    Args:
        alert_id: ID of the alert to acknowledge

    Returns:
        Acknowledgment result
    """
    alert_manager = get_alert_manager()

    # Acknowledge alert
    acknowledged = await alert_manager.acknowledge_alert(
        alert_id=alert_id, username="admin"
    )

    if not acknowledged:
        raise HTTPException(
            status_code=404, detail="Alert not found or already acknowledged"
        )

    return {"status": "acknowledged", "alert_id": alert_id}


@app.get("/")
async def index():
    """Main page - redirect to dashboard."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Health Check Example</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
            }
            .card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .links {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 20px;
            }
            .link {
                background-color: #f0f0f0;
                border-radius: 4px;
                padding: 10px 15px;
                text-decoration: none;
                color: #333;
            }
            .link:hover {
                background-color: #e0e0e0;
            }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }
        </style>
    </head>
    <body>
        <h1>Health Check Example</h1>
        
        <div class="card">
            <h2>Health Check Endpoints</h2>
            <div class="links">
                <a class="link" href="/health">Health Status</a>
                <a class="link" href="/health/details">Health Details</a>
                <a class="link" href="/dashboard/health">Health Dashboard</a>
            </div>
        </div>
        
        <div class="card">
            <h2>Simulate Service Issues</h2>
            <p>Use these controls to simulate service issues for testing health checks:</p>
            
            <h3>Database</h3>
            <div class="links">
                <a class="link" href="#" onclick="simulateIssue('database', 'degrade')">Degrade</a>
                <a class="link" href="#" onclick="simulateIssue('database', 'fail')">Fail</a>
                <a class="link" href="#" onclick="simulateIssue('database', 'restore')">Restore</a>
            </div>
            
            <h3>Cache</h3>
            <div class="links">
                <a class="link" href="#" onclick="simulateIssue('cache', 'degrade')">Degrade</a>
                <a class="link" href="#" onclick="simulateIssue('cache', 'fail')">Fail</a>
                <a class="link" href="#" onclick="simulateIssue('cache', 'restore')">Restore</a>
            </div>
            
            <h3>API Service</h3>
            <div class="links">
                <a class="link" href="#" onclick="simulateIssue('api', 'degrade')">Degrade</a>
                <a class="link" href="#" onclick="simulateIssue('api', 'fail')">Fail</a>
                <a class="link" href="#" onclick="simulateIssue('api', 'restore')">Restore</a>
            </div>
        </div>
        
        <div class="card">
            <h2>Alert Management</h2>
            <div class="links">
                <a class="link" href="/alerts">View Alerts</a>
            </div>
        </div>
        
        <script>
            async function simulateIssue(service, action) {
                try {
                    const response = await fetch('/simulate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            service: service,
                            action: action
                        }),
                    });
                    
                    const data = await response.json();
                    alert(data.message);
                } catch (error) {
                    alert('Error: ' + error);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    # Register health checks
    await register_api_check()

    # Setup health checks
    setup_health_endpoints()

    # Configure dashboard
    configure_dashboard()

    # Setup alerting
    await setup_alerts()

    logger.info("Health check example started")


def main():
    """Run the example application."""
    # Run the FastAPI app
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
