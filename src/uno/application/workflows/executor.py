#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Workflow Action Executor module for executing different types of workflow actions.

This module provides the base ActionExecutor interface and specialized implementations
for different action types (notification, email, webhook, database).
"""

import logging
import json
import asyncio
import aiohttp
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import (
    Dict,
    Any,
    List,
    Optional,
    Protocol,
    ClassVar,
    Callable,
    Type,
    Union,
    runtime_checkable,
)
from pydantic import BaseModel

import inject

from uno.core.errors.result import Result
from uno.settings import uno_settings
from uno.database.db_manager import DBManager
from uno.workflows.errors import (
    WorkflowErrorCode,
    WorkflowExecutionError,
    WorkflowActionError,
)
from uno.core.events import EventBus, UnoEvent

from uno.workflows.models import WorkflowActionType
from uno.workflows.entities import WorkflowAction, User


class ActionExecutionContext(BaseModel):
    """Context data for action execution"""

    workflow_id: str
    workflow_name: str
    action_id: str
    action_name: str | None = None
    event_data: Dict[str, Any]
    execution_id: str
    timestamp: datetime = datetime.now(timezone.utc)
    variables: Dict[str, Any] = {}
    tenant_id: str | None = None

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable from the context by name with optional default value"""
        return self.variables.get(name, default)

    def add_variables(self, variables: Dict[str, Any]) -> None:
        """Add variables to the context"""
        self.variables.update(variables)

    def interpolate(self, template: str) -> str:
        """Simple template interpolation using {{variable}} syntax"""
        result = template
        for key, value in self.variables.items():
            placeholder = "{{" + key + "}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))

        # Also interpolate any event data directly
        for key, value in self.event_data.items():
            if isinstance(value, (str, int, float, bool)):
                placeholder = "{{event." + key + "}}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))

        return result


@runtime_checkable
class ActionExecutor(Protocol):
    """Interface for workflow action executors"""

    action_type: ClassVar[WorkflowActionType]

    async def execute(
        self,
        action: WorkflowAction,
        context: ActionExecutionContext,
        recipients: list[User],
    ) -> Result[Dict[str, Any]]:
        """Execute a workflow action"""
        ...


class NotificationExecutor:
    """Executor for notification actions"""

    action_type = WorkflowActionType.NOTIFICATION

    @inject.params(event_bus=EventBus, logger=logging.Logger)
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        logger: logging.Logger | None = None,
    ):
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger(__name__)

    async def execute(
        self,
        action: WorkflowAction,
        context: ActionExecutionContext,
        recipients: list[User],
    ) -> Result[Dict[str, Any]]:
        """Execute a notification action"""
        try:
            config = action.action_config

            # Get notification details from config
            title = config.get("title", f"Notification from {context.workflow_name}")
            message = config.get("message", "A workflow has been triggered")
            notification_type = config.get("type", "info")
            link = config.get("link")

            # Interpolate variables in the template
            title = context.interpolate(title)
            message = context.interpolate(message)
            if link:
                link = context.interpolate(link)

            # Send notification to each recipient
            if self.event_bus:
                for recipient in recipients:
                    # Create and dispatch notification event
                    notification_event = self._create_notification_event(
                        recipient=recipient,
                        title=title,
                        message=message,
                        notification_type=notification_type,
                        context=context,
                        link=link,
                    )
                    await self.event_bus.publish(notification_event)

            self.logger.info(
                f"Sent {notification_type} notification '{title}' to {len(recipients)} recipients"
            )

            return Success(
                {
                    "title": title,
                    "message": message,
                    "notification_type": notification_type,
                    "recipient_count": len(recipients),
                    "link": link,
                }
            )

        except Exception as e:
            self.logger.exception(f"Error executing notification action: {e}")
            return Failure(BaseError(f"Error executing notification action: {str(e)}"))

    def _create_notification_event(
        self,
        recipient: User,
        title: str,
        message: str,
        notification_type: str,
        context: ActionExecutionContext,
        link: str | None = None,
    ) -> UnoEvent:
        """Create a notification event for the event bus"""
        # Import here to avoid circular imports
        from uno.workflows.notifications import SystemNotificationCreated
        import uuid

        # Generate a unique notification ID
        notification_id = str(uuid.uuid4())

        # Extract priority from context if available
        priority = context.variables.get("notification_priority", "normal")

        # Create metadata with workflow context
        metadata = {
            "workflow_id": context.workflow_id,
            "workflow_name": context.workflow_name,
            "action_id": context.action_id,
            "execution_id": context.execution_id,
            "timestamp": context.timestamp.isoformat(),
            "event_type": context.event_data.get("event_type", "unknown"),
        }

        return SystemNotificationCreated(
            notification_id=notification_id,
            recipient_id=recipient.id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            link=link,
            workflow_id=context.workflow_id,
            action_id=context.action_id,
            metadata=metadata,
            tenant_id=context.tenant_id,
        )


class EmailExecutor:
    """Executor for email actions"""

    action_type = WorkflowActionType.EMAIL

    @inject.params(logger=logging.Logger)
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.smtp_host = uno_settings.SMTP_HOST
        self.smtp_port = uno_settings.SMTP_PORT
        self.smtp_user = uno_settings.SMTP_USER
        self.smtp_password = uno_settings.SMTP_PASSWORD
        self.default_sender = uno_settings.DEFAULT_EMAIL_SENDER
        self.templates_dir = uno_settings.EMAIL_TEMPLATES_DIR

    async def execute(
        self,
        action: WorkflowAction,
        context: ActionExecutionContext,
        recipients: list[User],
    ) -> Result[Dict[str, Any]]:
        """Execute an email action"""
        try:
            config = action.action_config

            # Get email details from config
            subject = config.get(
                "subject", f"Notification from {context.workflow_name}"
            )
            template_name = config.get("template")
            content = config.get("content")
            sender = config.get("sender", self.default_sender)
            is_html = config.get("is_html", True)

            # If no content provided but template specified, load the template
            if not content and template_name:
                content = await self._load_email_template(template_name)

            # If still no content, use a default message
            if not content:
                content = f"This is an automated notification from workflow '{context.workflow_name}'"

            # Interpolate variables in the subject and content
            subject = context.interpolate(subject)
            content = context.interpolate(content)

            # Send email to each recipient
            sent_count = 0
            failed_recipients = []

            for recipient in recipients:
                recipient_email = recipient.email
                if not recipient_email:
                    self.logger.warning(
                        f"No email address for recipient {recipient.id}"
                    )
                    failed_recipients.append(recipient.id)
                    continue

                try:
                    await self._send_email(
                        sender=sender,
                        recipient=recipient_email,
                        subject=subject,
                        content=content,
                        is_html=is_html,
                    )
                    sent_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to send email to {recipient_email}: {e}")
                    failed_recipients.append(recipient.id)

            self.logger.info(
                f"Sent email '{subject}' to {sent_count} out of {len(recipients)} recipients"
            )

            return Success(
                {
                    "subject": subject,
                    "sent_count": sent_count,
                    "failed_count": len(failed_recipients),
                    "failed_recipients": failed_recipients,
                }
            )

        except Exception as e:
            self.logger.exception(f"Error executing email action: {e}")
            return Failure(BaseError(f"Error executing email action: {str(e)}"))

    async def _load_email_template(self, template_name: str) -> str:
        """Load an email template from the templates directory"""
        try:
            template_path = f"{self.templates_dir}/{template_name}.html"

            try:
                with open(template_path, "r") as f:
                    return f.read()
            except FileNotFoundError:
                self.logger.warning(
                    f"Email template {template_name} not found at {template_path}"
                )
                return ""

        except Exception as e:
            self.logger.error(f"Error loading email template {template_name}: {e}")
            return ""

    async def _send_email(
        self,
        sender: str,
        recipient: str,
        subject: str,
        content: str,
        is_html: bool = True,
    ) -> None:
        """Send an email using SMTP"""
        # This is intentionally run in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self._send_email_sync, sender, recipient, subject, content, is_html
        )

    def _send_email_sync(
        self,
        sender: str,
        recipient: str,
        subject: str,
        content: str,
        is_html: bool = True,
    ) -> None:
        """Synchronous implementation of sending an email"""
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = subject

        if is_html:
            msg.attach(MIMEText(content, "html"))
        else:
            msg.attach(MIMEText(content, "plain"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)


class WebhookExecutor:
    """Executor for webhook actions"""

    action_type = WorkflowActionType.WEBHOOK

    @inject.params(logger=logging.Logger)
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

    async def execute(
        self,
        action: WorkflowAction,
        context: ActionExecutionContext,
        recipients: list[User],
    ) -> Result[Dict[str, Any]]:
        """Execute a webhook action"""
        try:
            config = action.action_config

            # Get webhook details from config
            url = config.get("url")
            if not url:
                return Failure(BaseError("No URL provided for webhook action"))

            method = config.get("method", "POST").upper()
            headers = config.get("headers", {})
            auth_type = config.get("auth_type")
            auth_config = config.get("auth_config", {})
            timeout = config.get("timeout", 30)

            # Apply context variables to URL
            url = context.interpolate(url)

            # Generate payload from the configured fields or use full event data
            payload_fields = config.get("payload_fields", None)
            if payload_fields:
                payload = {
                    field: context.event_data.get(field)
                    for field in payload_fields
                    if field in context.event_data
                }
            else:
                payload = context.event_data.copy()

            # Add workflow context to payload
            payload.update(
                {
                    "workflow_id": context.workflow_id,
                    "workflow_name": context.workflow_name,
                    "action_id": context.action_id,
                    "execution_id": context.execution_id,
                    "timestamp": context.timestamp.isoformat(),
                }
            )

            # Add authentication if configured
            if auth_type == "basic":
                username = auth_config.get("username", "")
                password = auth_config.get("password", "")
                auth = aiohttp.BasicAuth(username, password)
            elif auth_type == "bearer":
                token = auth_config.get("token", "")
                headers["Authorization"] = f"Bearer {token}"
                auth = None
            elif auth_type == "api_key":
                key_name = auth_config.get("key_name", "api_key")
                key_value = auth_config.get("key_value", "")
                key_in = auth_config.get("key_in", "header")

                if key_in == "header":
                    headers[key_name] = key_value
                elif key_in == "query":
                    if "?" in url:
                        url += f"&{key_name}={key_value}"
                    else:
                        url += f"?{key_name}={key_value}"
                auth = None
            else:
                auth = None

            # Send the webhook request
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers,
                    auth=auth,
                    timeout=timeout,
                ) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()

                    self.logger.info(
                        f"Webhook {method} to {url} completed with status {status}"
                    )

                    return Success(
                        {
                            "url": url,
                            "method": method,
                            "status": status,
                            "response": response_data,
                        }
                    )

        except Exception as e:
            self.logger.exception(f"Error executing webhook action: {e}")
            return Failure(BaseError(f"Error executing webhook action: {str(e)}"))


class DatabaseExecutor:
    """Executor for database actions"""

    action_type = WorkflowActionType.DATABASE

    @inject.params(db_manager=DBManager, logger=logging.Logger)
    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: logging.Logger | None = None,
    ):
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def execute(
        self,
        action: WorkflowAction,
        context: ActionExecutionContext,
        recipients: list[User],
    ) -> Result[Dict[str, Any]]:
        """Execute a database action"""
        try:
            config = action.action_config

            # Get database action details from config
            operation = config.get("operation", "INSERT")
            target_table = config.get("table")
            if not target_table:
                return Failure(
                    BaseError("No target table provided for database action")
                )

            # Get field mappings from the config
            field_mappings = config.get("field_mappings", {})
            if not field_mappings:
                return Failure(
                    BaseError("No field mappings provided for database action")
                )

            # Prepare data to insert/update
            record_data = {}
            for target_field, source_expr in field_mappings.items():
                # If the source is a direct field reference
                if source_expr.startswith("{{") and source_expr.endswith("}}"):
                    field_name = source_expr[2:-2].strip()
                    record_data[target_field] = context.get_variable(field_name)
                # If the source is a template with variables
                elif "{{" in source_expr and "}}" in source_expr:
                    record_data[target_field] = context.interpolate(source_expr)
                # If the source is a static value
                else:
                    record_data[target_field] = source_expr

            # Add tenant ID if available and not already set
            if context.tenant_id and "tenant_id" not in record_data:
                record_data["tenant_id"] = context.tenant_id

            # Execute the database operation
            async with self.db_manager.get_enhanced_session() as session:
                if operation == "INSERT":
                    # Generate SQL for insert
                    fields = list(record_data.keys())
                    placeholders = [f":{field}" for field in fields]
                    sql = f"""
                        INSERT INTO {target_table} ({', '.join(fields)})
                        VALUES ({', '.join(placeholders)})
                        RETURNING id
                    """
                    result = await session.execute(sql, record_data)
                    returned_id = result.scalar()

                    self.logger.info(
                        f"Inserted record into {target_table} with ID {returned_id}"
                    )

                    return Success(
                        {
                            "operation": "INSERT",
                            "table": target_table,
                            "record_id": returned_id,
                        }
                    )

                elif operation == "UPDATE":
                    # Check for the record ID or filter condition
                    record_id = config.get("record_id")
                    filter_condition = config.get("filter_condition")

                    if not record_id and not filter_condition:
                        return Failure(
                            BaseError(
                                "No record ID or filter condition provided for UPDATE operation"
                            )
                        )

                    # Generate SQL for update
                    set_clause = ", ".join(
                        [f"{field} = :{field}" for field in record_data.keys()]
                    )

                    if record_id:
                        # If record_id is a template with variables, interpolate it
                        if (
                            isinstance(record_id, str)
                            and "{{" in record_id
                            and "}}" in record_id
                        ):
                            record_id = context.interpolate(record_id)

                        sql = f"""
                            UPDATE {target_table}
                            SET {set_clause}
                            WHERE id = :record_id
                        """
                        params = {**record_data, "record_id": record_id}
                    else:
                        # If filter_condition is a template with variables, interpolate it
                        if (
                            isinstance(filter_condition, str)
                            and "{{" in filter_condition
                            and "}}" in filter_condition
                        ):
                            filter_condition = context.interpolate(filter_condition)

                        sql = f"""
                            UPDATE {target_table}
                            SET {set_clause}
                            WHERE {filter_condition}
                        """
                        params = record_data

                    result = await session.execute(sql, params)
                    row_count = result.rowcount

                    self.logger.info(f"Updated {row_count} records in {target_table}")

                    return Success(
                        {
                            "operation": "UPDATE",
                            "table": target_table,
                            "row_count": row_count,
                        }
                    )

                else:
                    return Failure(
                        BaseError(f"Unsupported database operation: {operation}")
                    )

        except Exception as e:
            self.logger.exception(f"Error executing database action: {e}")
            return Failure(BaseError(f"Error executing database action: {str(e)}"))


class CustomExecutor:
    """Executor for custom actions"""

    action_type = WorkflowActionType.CUSTOM

    @inject.params(logger=logging.Logger)
    def __init__(
        self,
        logger: logging.Logger | None = None,
        custom_executors: Dict[str, Callable] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.custom_executors = custom_executors or {}

    def register_custom_executor(
        self, executor_type: str, executor_func: Callable
    ) -> None:
        """Register a custom executor function for a specific type"""
        self.custom_executors[executor_type] = executor_func

    async def execute(
        self,
        action: WorkflowAction,
        context: ActionExecutionContext,
        recipients: list[User],
    ) -> Result[Dict[str, Any]]:
        """Execute a custom action"""
        try:
            config = action.action_config

            # Get custom executor type
            executor_type = config.get("executor_type")
            if not executor_type:
                return Failure(BaseError("No executor type provided for custom action"))

            # Find the corresponding executor function
            executor_func = self.custom_executors.get(executor_type)
            if not executor_func:
                return Failure(
                    BaseError(
                        f"No executor found for custom action type: {executor_type}"
                    )
                )

            # Execute the custom function
            result = executor_func(action, context, recipients)

            # Handle both synchronous and asynchronous functions
            if asyncio.iscoroutine(result):
                result = await result

            self.logger.info(f"Executed custom action '{executor_type}'")

            # If the result is already a Result object, return it
            if isinstance(result, Result):
                return result

            # Otherwise, wrap it in a Success
            return Success({"executor_type": executor_type, "result": result})

        except Exception as e:
            self.logger.exception(f"Error executing custom action: {e}")
            return Failure(BaseError(f"Error executing custom action: {str(e)}"))


class ActionExecutorRegistry:
    """Registry for action executors"""

    def __init__(self):
        self.executors: Dict[WorkflowActionType, ActionExecutor] = {}

    def register(self, executor: ActionExecutor) -> None:
        """Register an action executor"""
        self.executors[executor.action_type] = executor

    def get(self, action_type: WorkflowActionType) -> Optional[ActionExecutor]:
        """Get an action executor by action type"""
        return self.executors.get(action_type)

    def has(self, action_type: WorkflowActionType) -> bool:
        """Check if an executor exists for the action type"""
        return action_type in self.executors


# Singleton registry instance
_registry = ActionExecutorRegistry()


def get_executor_registry() -> ActionExecutorRegistry:
    """Get the global action executor registry"""
    return _registry


def register_executor(executor: ActionExecutor) -> None:
    """Register an action executor in the global registry"""
    _registry.register(executor)


def get_executor(action_type: WorkflowActionType) -> Optional[ActionExecutor]:
    """Get an action executor from the global registry"""
    return _registry.get(action_type)


# Initialize standard executors
def init_executors() -> None:
    """Initialize and register the standard executors"""
    register_executor(NotificationExecutor())
    register_executor(EmailExecutor())
    register_executor(WebhookExecutor())
    register_executor(DatabaseExecutor())
    register_executor(CustomExecutor())
