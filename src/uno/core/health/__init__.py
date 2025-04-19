"""
Health check framework for the Uno application.

This module provides a comprehensive health check system for monitoring
application components, services, dependencies, and resources.
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable, Union, Set

# Import and re-export main components for convenient access
from uno.core.health.framework import (
    # Main classes
    HealthStatus,
    HealthCheckResult,
    HealthCheck,
    HealthRegistry,
    HealthEndpoint,
    HealthConfig,
    ResourceHealth,
    
    # Functions
    health_check,
    register_health_check,
    get_health_registry,
    get_health_status,
    
    # Contexts
    health_context,
)

from uno.core.health.dashboard import (
    HealthDashboard,
    setup_health_dashboard,
)

from uno.core.health.alerting import (
    AlertLevel,
    AlertRule,
    AlertAction,
    AlertManager,
    EmailAlertAction,
    WebhookAlertAction,
    LoggingAlertAction,
    setup_health_alerting,
    get_alert_manager,
)

__all__ = [
    # Main classes
    "HealthStatus",
    "HealthCheckResult",
    "HealthCheck",
    "HealthRegistry",
    "HealthEndpoint",
    "HealthConfig",
    "ResourceHealth",
    "HealthDashboard",
    "AlertLevel",
    "AlertRule",
    "AlertAction",
    "AlertManager",
    "EmailAlertAction",
    "WebhookAlertAction",
    "LoggingAlertAction",
    
    # Functions
    "health_check",
    "register_health_check",
    "get_health_registry",
    "get_health_status",
    "setup_health_dashboard",
    "setup_health_alerting",
    "get_alert_manager",
    
    # Contexts
    "health_context",
]