# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Health alerting for the Uno application.

This module provides a framework for generating alerts based on health
check results. It includes:

1. Alert level definitions
2. Alert rule management
3. Alert action implementations (email, webhook, logging)
4. Alert history tracking
5. Integration with the health check framework
"""

from typing import Dict, List, Any, Optional, Callable, Union, Set, Awaitable
import asyncio
import time
import logging
import json
import datetime
import smtplib
import traceback
import ssl
from enum import Enum, auto
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from functools import wraps
from abc import ABC, abstractmethod

import aiohttp
from pydantic import BaseModel, Field, EmailStr, HttpUrl

from uno.core.logging import get_logger
from uno.core.health.framework import (
    HealthRegistry,
    HealthStatus,
    get_health_registry,
    HealthConfig,
    HealthCheckResult,
)


class AlertLevel(Enum):
    """Alert severity level."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

    @classmethod
    def from_health_status(cls, status: HealthStatus) -> "AlertLevel":
        """
        Convert HealthStatus to AlertLevel.

        Args:
            status: HealthStatus value

        Returns:
            Equivalent AlertLevel value
        """
        mapping = {
            HealthStatus.HEALTHY: AlertLevel.INFO,
            HealthStatus.DEGRADED: AlertLevel.WARNING,
            HealthStatus.UNHEALTHY: AlertLevel.ERROR,
            HealthStatus.UNKNOWN: AlertLevel.WARNING,
        }
        return mapping.get(status, AlertLevel.WARNING)


class AlertConfig(BaseModel):
    """Configuration for health alerts."""

    enabled: bool = True
    min_level: AlertLevel = AlertLevel.WARNING
    throttle_seconds: int = 300  # 5 minutes
    email_from: str | None = None
    email_to: list[str] = Field(default_factory=list)
    smtp_server: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    webhook_urls: list[str] = Field(default_factory=list)
    webhook_custom_headers: dict[str, str] = Field(default_factory=dict)
    alert_history_size: int = 100


class Alert(BaseModel):
    """Health check alert."""

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

    model_config = ConfigDict(
        use_enum_values=False,
        json_encoders={
            AlertLevel: lambda v: v.name.lower(),
            HealthStatus: lambda v: v.name.lower(),
        },
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert alert to dictionary.

        Returns:
            Dictionary representation of the alert
        """
        result = self.model_dump()
        result["level"] = self.level.name.lower()
        result["status"] = self.status.name.lower()
        return result


class AlertRule(BaseModel):
    """Rule for generating alerts from health checks."""

    id: str
    name: str
    description: str | None = None
    enabled: bool = True
    level: AlertLevel

    # Targeting
    check_id: str | None = None  # Specific check ID
    check_name: str | None = None  # Check name (supports wildcard patterns)
    group: str | None = None  # Check group
    tags: list[str] = Field(default_factory=list)  # Check tags
    status: Optional[HealthStatus] = None  # Status to alert on

    # Behavior
    auto_acknowledge: bool = False
    throttle_seconds: int = 300  # 5 minutes between alerts
    last_alert_time: Optional[float] = None

    def matches(
        self, check_id: str, check: dict[str, Any], result: HealthCheckResult
    ) -> bool:
        """
        Check if this rule matches a health check result.

        Args:
            check_id: ID of the health check
            check: Health check information
            result: Health check result

        Returns:
            Whether the rule matches
        """
        # Check if rule is enabled
        if not self.enabled:
            return False

        # Check specific ID
        if self.check_id and self.check_id != check_id:
            return False

        # Check name (supports wildcards with *)
        if self.check_name:
            name = check.get("name", "")
            if "*" in self.check_name:
                import fnmatch

                if not fnmatch.fnmatch(name, self.check_name):
                    return False
            elif self.check_name != name:
                return False

        # Check group
        if self.group and self.group != check.get("group"):
            return False

        # Check tags
        if self.tags:
            check_tags = check.get("tags", [])
            if not set(self.tags).intersection(set(check_tags)):
                return False

        # Check status
        if self.status and self.status != result.status:
            return False

        # Check throttle
        if self.throttle_seconds > 0 and self.last_alert_time:
            now = time.time()
            if now - self.last_alert_time < self.throttle_seconds:
                return False

        return True


class AlertAction(ABC):
    """Base class for alert actions."""

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the alert action.

        Args:
            logger: Logger to use
        """
        self.logger = logger or get_logger("uno.health.alerting")

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        """
        Send an alert.

        Args:
            alert: Alert to send

        Returns:
            Whether the alert was sent successfully
        """
        pass


class LoggingAlertAction(AlertAction):
    """Alert action that logs the alert."""

    async def send(self, alert: Alert) -> bool:
        """
        Log an alert.

        Args:
            alert: Alert to log

        Returns:
            Whether the alert was logged successfully
        """
        try:
            # Map alert level to log level
            level_map = {
                AlertLevel.INFO: logging.INFO,
                AlertLevel.WARNING: logging.WARNING,
                AlertLevel.ERROR: logging.ERROR,
                AlertLevel.CRITICAL: logging.CRITICAL,
            }
            log_level = level_map.get(alert.level, logging.WARNING)

            # Log the alert
            self.logger.log(
                log_level,
                f"HEALTH ALERT: {alert.title} - {alert.message}",
                extra={
                    "alert_id": alert.id,
                    "alert_level": alert.level.name,
                    "source": alert.source,
                    "check_name": alert.check_name,
                    "group": alert.group,
                    "status": alert.status.name,
                    "details": alert.details,
                },
            )

            return True

        except Exception as e:
            self.logger.error(f"Error logging alert: {str(e)}")
            return False


class EmailAlertAction(AlertAction):
    """Alert action that sends an email."""

    def __init__(
        self,
        config: AlertConfig,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the email alert action.

        Args:
            config: Alert configuration
            logger: Logger to use
        """
        super().__init__(logger)
        self.config = config

    async def send(self, alert: Alert) -> bool:
        """
        Send an email alert.

        Args:
            alert: Alert to send

        Returns:
            Whether the alert was sent successfully
        """
        # Skip if email is not configured
        if (
            not self.config.smtp_server
            or not self.config.email_from
            or not self.config.email_to
        ):
            self.logger.warning("Email alerts not configured")
            return False

        try:
            # Set alert level in subject
            level_text = alert.level.name.upper()

            # Create message
            msg = MIMEMultipart()
            msg["Subject"] = f"[{level_text}] Health Alert: {alert.title}"
            msg["From"] = self.config.email_from
            msg["To"] = ", ".join(self.config.email_to)

            # Create HTML message
            html = f"""
            <html>
              <head></head>
              <body>
                <h2>{alert.title}</h2>
                <p><strong>Level:</strong> {level_text}</p>
                <p><strong>Status:</strong> {alert.status.name}</p>
                <p><strong>Source:</strong> {alert.source}</p>
                <p><strong>Check:</strong> {alert.check_name or 'N/A'}</p>
                <p><strong>Group:</strong> {alert.group or 'N/A'}</p>
                <p><strong>Time:</strong> {datetime.datetime.fromtimestamp(alert.timestamp).isoformat()}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                
                <h3>Details:</h3>
                <pre>{json.dumps(alert.details, indent=2)}</pre>
              </body>
            </html>
            """

            # Attach HTML part
            msg.attach(MIMEText(html, "html"))

            # Create connection and send
            context = None
            if self.config.smtp_use_tls:
                context = ssl.create_default_context()

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls(context=context)

                if self.config.smtp_user and self.config.smtp_password:
                    server.login(self.config.smtp_user, self.config.smtp_password)

                server.send_message(msg)

            return True

        except Exception as e:
            self.logger.error(f"Error sending email alert: {str(e)}")
            return False


class WebhookAlertAction(AlertAction):
    """Alert action that sends a webhook."""

    def __init__(
        self,
        config: AlertConfig,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the webhook alert action.

        Args:
            config: Alert configuration
            logger: Logger to use
        """
        super().__init__(logger)
        self.config = config

    async def send(self, alert: Alert) -> bool:
        """
        Send a webhook alert.

        Args:
            alert: Alert to send

        Returns:
            Whether the alert was sent successfully
        """
        # Skip if no webhook URLs
        if not self.config.webhook_urls:
            return False

        # Prepare payload
        payload = alert.to_dict()

        # Add timestamp in ISO format for easier consumption
        payload["timestamp_iso"] = datetime.datetime.fromtimestamp(
            alert.timestamp
        ).isoformat()

        # Add headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Uno-Health-Alerting/1.0",
        }

        # Add custom headers
        if self.config.webhook_custom_headers:
            headers.update(self.config.webhook_custom_headers)

        # Send to all webhook URLs
        success = True

        async with aiohttp.ClientSession() as session:
            for url in self.config.webhook_urls:
                try:
                    async with session.post(
                        url, json=payload, headers=headers, timeout=10
                    ) as response:
                        if response.status < 200 or response.status >= 300:
                            self.logger.warning(
                                f"Webhook alert failed: HTTP {response.status} to {url}"
                            )
                            success = False

                except Exception as e:
                    self.logger.error(f"Error sending webhook alert to {url}: {str(e)}")
                    success = False

        return success


class AlertManager:
    """
    Manager for health check alerts.

    This class handles alert generation, delivery, and tracking.
    """

    def __init__(
        self,
        config: Optional[AlertConfig] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the alert manager.

        Args:
            config: Alert configuration
            logger: Logger to use
        """
        self.config = config or AlertConfig()
        self.logger = logger or get_logger("uno.health.alerting")
        self.rules: list[AlertRule] = []
        self.actions: list[AlertAction] = []
        self.alert_history: list[Alert] = []
        self.health_registry = get_health_registry()
        self._lock = asyncio.Lock()

        # Add default actions
        self.actions.append(LoggingAlertAction(self.logger))

        # Add email action if configured
        if self.config.email_from and self.config.smtp_server:
            self.actions.append(EmailAlertAction(self.config, self.logger))

        # Add webhook action if configured
        if self.config.webhook_urls:
            self.actions.append(WebhookAlertAction(self.config, self.logger))

    async def add_rule(self, rule: AlertRule) -> None:
        """
        Add an alert rule.

        Args:
            rule: Alert rule to add
        """
        async with self._lock:
            self.rules.append(rule)
            self.logger.debug(f"Added alert rule: {rule.name}")

    async def remove_rule(self, rule_id: str) -> bool:
        """
        Remove an alert rule.

        Args:
            rule_id: ID of the rule to remove

        Returns:
            Whether the rule was removed
        """
        async with self._lock:
            for i, rule in enumerate(self.rules):
                if rule.id == rule_id:
                    self.rules.pop(i)
                    self.logger.debug(f"Removed alert rule: {rule.name}")
                    return True

            return False

    async def add_action(self, action: AlertAction) -> None:
        """
        Add an alert action.

        Args:
            action: Alert action to add
        """
        async with self._lock:
            self.actions.append(action)

    async def process_health_report(self, report: dict[str, Any]) -> None:
        """
        Process a health report and generate alerts.

        Args:
            report: Health report dictionary
        """
        if not self.config.enabled:
            return

        try:
            # Get overall status
            overall_status = report.get("status", "").upper()
            if overall_status:
                try:
                    overall_status = HealthStatus[overall_status]
                except KeyError:
                    overall_status = HealthStatus.UNKNOWN
            else:
                overall_status = HealthStatus.UNKNOWN

            # Check all health checks for alert conditions
            checks_by_status = report.get("checks", {})
            for status_name, checks in checks_by_status.items():
                try:
                    status = HealthStatus[status_name.upper()]
                except KeyError:
                    status = HealthStatus.UNKNOWN

                for check_info in checks:
                    check_id = check_info.get("id")
                    if not check_id:
                        continue

                    # Convert result dict to HealthCheckResult
                    result_dict = check_info.get("result", {})
                    if result_dict:
                        result = HealthCheckResult(
                            status=status,
                            message=result_dict.get("message", ""),
                            details=result_dict.get("details", {}),
                            timestamp=result_dict.get("timestamp", time.time()),
                            check_duration_ms=result_dict.get("check_duration_ms"),
                        )
                    else:
                        result = HealthCheckResult(
                            status=status,
                            message="No result available",
                            timestamp=time.time(),
                        )

                    # Skip healthy checks unless a rule specifically targets them
                    if status == HealthStatus.HEALTHY:
                        has_matching_rule = False
                        for rule in self.rules:
                            if rule.status == HealthStatus.HEALTHY and (
                                rule.check_id == check_id
                                or rule.check_name == check_info.get("name")
                                or rule.group == check_info.get("group")
                                or set(rule.tags).intersection(
                                    set(check_info.get("tags", []))
                                )
                            ):
                                has_matching_rule = True
                                break

                        if not has_matching_rule:
                            continue

                    # Process check against rules
                    await self._process_check(check_id, check_info, result)

            # Generate overall system alert if needed
            if overall_status in (HealthStatus.UNHEALTHY, HealthStatus.DEGRADED):
                # Skip if we've already generated alerts for individual checks
                if (
                    self.alert_history
                    and time.time() - self.alert_history[0].timestamp < 60
                ):
                    return

                # Create system-wide alert
                level = AlertLevel.from_health_status(overall_status)

                if level.value >= self.config.min_level.value:
                    alert = Alert(
                        id=f"system-{int(time.time())}",
                        timestamp=time.time(),
                        level=level,
                        title=f"System Health: {overall_status.name}",
                        message=f"System health status is {overall_status.name.lower()}",
                        details={
                            "overall_status": overall_status.name.lower(),
                            "checks_total": report.get("checks_total", 0),
                            "checks_by_status": report.get("checks_by_status", {}),
                        },
                        source="system",
                        status=overall_status,
                    )

                    await self._send_alert(alert)

        except Exception as e:
            self.logger.error(
                f"Error processing health report: {str(e)}\n{traceback.format_exc()}"
            )

    async def _process_check(
        self, check_id: str, check_info: dict[str, Any], result: HealthCheckResult
    ) -> None:
        """
        Process a single health check against alert rules.

        Args:
            check_id: ID of the health check
            check_info: Health check information
            result: Health check result
        """
        async with self._lock:
            # Check each rule
            for rule in self.rules:
                if rule.matches(check_id, check_info, result):
                    # Create alert
                    alert = Alert(
                        id=f"{check_id}-{int(time.time())}",
                        timestamp=time.time(),
                        level=rule.level,
                        title=f"{check_info.get('name', 'Health Check')}: {result.status.name}",
                        message=result.message,
                        details=result.details,
                        source="health_check",
                        check_id=check_id,
                        check_name=check_info.get("name"),
                        group=check_info.get("group"),
                        status=result.status,
                    )

                    # Send alert
                    await self._send_alert(alert)

                    # Update rule's last alert time
                    rule.last_alert_time = time.time()

    async def _send_alert(self, alert: Alert) -> None:
        """
        Send an alert to all configured actions.

        Args:
            alert: Alert to send
        """
        # Skip if alert level is below minimum
        if alert.level.value < self.config.min_level.value:
            return

        # Skip if throttling is enabled
        if (
            self.config.throttle_seconds > 0
            and self.alert_history
            and alert.check_id == self.alert_history[0].check_id
            and time.time() - self.alert_history[0].timestamp
            < self.config.throttle_seconds
        ):
            return

        # Send to all actions
        for action in self.actions:
            try:
                success = await action.send(alert)
                if success:
                    alert.actions_taken.append(action.__class__.__name__)
            except Exception as e:
                self.logger.error(
                    f"Error sending alert with {action.__class__.__name__}: {str(e)}"
                )

        # Add to history
        self.alert_history.insert(0, alert)

        # Trim history if needed
        while len(self.alert_history) > self.config.alert_history_size:
            self.alert_history.pop()

    async def acknowledge_alert(
        self, alert_id: str, username: str | None = None
    ) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of the alert to acknowledge
            username: Name of the user acknowledging the alert

        Returns:
            Whether the alert was acknowledged
        """
        async with self._lock:
            for alert in self.alert_history:
                if alert.id == alert_id and not alert.acknowledged:
                    alert.acknowledged = True
                    alert.acknowledged_at = time.time()
                    alert.acknowledged_by = username
                    return True

            return False

    async def get_recent_alerts(
        self,
        limit: int = 10,
        min_level: Optional[AlertLevel] = None,
        include_acknowledged: bool = False,
    ) -> list[Alert]:
        """
        Get recent alerts.

        Args:
            limit: Maximum number of alerts to return
            min_level: Minimum alert level to include
            include_acknowledged: Whether to include acknowledged alerts

        Returns:
            List of recent alerts
        """
        async with self._lock:
            # Filter alerts
            filtered = []
            for alert in self.alert_history:
                # Skip acknowledged alerts if not requested
                if not include_acknowledged and alert.acknowledged:
                    continue

                # Skip alerts below minimum level
                if min_level and alert.level.value < min_level.value:
                    continue

                filtered.append(alert)

                # Check limit
                if len(filtered) >= limit:
                    break

            return filtered

    async def start(self) -> None:
        """
        Start the alert manager.

        This initializes default rules and starts monitoring.
        """
        # Add default critical status rule
        critical_rule = AlertRule(
            id="default-critical",
            name="Critical Checks",
            description="Alert on any critical health check failures",
            enabled=True,
            level=AlertLevel.ERROR,
            status=HealthStatus.UNHEALTHY,
            tags=["critical"],
        )

        await self.add_rule(critical_rule)

        # Add default group failure rule
        group_rule = AlertRule(
            id="default-group",
            name="Group Failures",
            description="Alert when an entire group of health checks fails",
            enabled=True,
            level=AlertLevel.ERROR,
            status=HealthStatus.UNHEALTHY,
        )

        await self.add_rule(group_rule)

        self.logger.info("Alert manager started")

    async def stop(self) -> None:
        """Stop the alert manager."""
        self.logger.info("Alert manager stopped")


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """
    Get the global alert manager.

    Returns:
        The global alert manager
    """
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


async def setup_health_alerting(config: Optional[AlertConfig] = None) -> AlertManager:
    """
    Set up health alerting.

    Args:
        config: Alert configuration

    Returns:
        The configured AlertManager
    """
    # Create alert manager
    alert_manager = get_alert_manager()

    # Update configuration
    if config:
        alert_manager.config = config

    # Start the manager
    await alert_manager.start()

    # Setup webhook to monitor health status changes
    registry = get_health_registry()

    # Hook into the health check system
    original_get_health_report = registry.get_health_report

    @wraps(original_get_health_report)
    async def wrapped_get_health_report(*args, **kwargs):
        # Get the report
        report = await original_get_health_report(*args, **kwargs)

        # Process for alerts
        asyncio.create_task(alert_manager.process_health_report(report))

        # Return the original report
        return report

    # Replace the method
    registry.get_health_report = wrapped_get_health_report

    return alert_manager
