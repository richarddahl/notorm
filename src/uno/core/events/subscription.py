"""
Subscription management for the UNO event system.

This module provides interfaces and implementations for managing event subscriptions
persistently, with support for dynamic registration, monitoring, and configuration.
"""

import asyncio
import importlib
import inspect
import json
import logging
from datetime import UTC, datetime
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

from uno.core.errors import Error, NotFoundError, Result
from uno.core.monitoring.metrics import Counter, Gauge, Timer
from uno.domain.event_bus import EventBusProtocol
from uno.core.protocols.event import EventHandler, EventProtocol
from uno.core.resources import Disposable


class SubscriptionMetrics(BaseModel):
    """Metrics for an event subscription."""

    invocation_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_invoked_at: Optional[datetime] = None
    avg_processing_time_ms: float = 0
    p95_processing_time_ms: float = 0
    p99_processing_time_ms: float = 0
    min_processing_time_ms: float = 0
    max_processing_time_ms: float = 0


class SubscriptionConfig(BaseModel):
    """Configuration for an event subscription."""

    # Basic settings
    subscription_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    handler_name: str
    handler_module: str
    handler_function: str | None = None
    description: str = ""

    # Runtime settings
    is_active: bool = True
    is_async: bool = True
    max_retries: int = 3
    retry_delay_ms: int = 1000
    timeout_ms: int = 30000  # 30 seconds

    # Advanced settings
    filter_expression: str | None = (
        None  # Optional JSONATA or similar expression to filter events
    )
    batch_size: int = 1  # For batch handlers
    batch_interval_ms: int = 0  # For time-based batching, 0 = disabled

    # Security and permissions
    requires_permissions: list[str] = Field(default_factory=list)

    # Monitoring and alerting
    alert_on_failure: bool = False
    alert_threshold: float = 0.8  # Alert if failure rate exceeds this threshold


class SubscriptionInfo(SubscriptionConfig):
    """Event subscription information with runtime data."""

    # Status
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Metrics
    metrics: SubscriptionMetrics = Field(default_factory=SubscriptionMetrics)


class EventTypeInfo(BaseModel):
    """Information about an event type."""

    name: str
    description: str = ""
    schema: dict[str, Any] = Field(default_factory=dict)
    example: dict[str, Any] | None = None
    deprecated: bool = False
    domain: str | None = None


class SubscriptionRepository(Generic[EventProtocol]):
    """
    Repository for persisting and retrieving event subscription configurations.

    This repository provides CRUD operations for event subscriptions and
    handles the persistence of subscription status and metrics.
    """

    def __init__(self, config_path: str | None = None):
        """
        Initialize the subscription repository.

        Args:
            config_path: Optional path to the configuration file
        """
        self.logger = structlog.get_logger("uno.events.subscriptions")
        self.config_path = config_path
        self._subscriptions: dict[str, SubscriptionInfo] = {}
        self._event_types: dict[str, EventTypeInfo] = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the repository, loading existing configurations."""
        async with self._lock:
            if self.config_path:
                try:
                    with open(self.config_path, "r") as f:
                        data = json.load(f)

                        # Load subscriptions
                        subscriptions = data.get("subscriptions", [])
                        for sub_data in subscriptions:
                            sub = SubscriptionInfo.model_validate(sub_data)
                            self._subscriptions[sub.subscription_id] = sub

                        # Load event types
                        event_types = data.get("event_types", [])
                        for et_data in event_types:
                            et = EventTypeInfo.model_validate(et_data)
                            self._event_types[et.name] = et

                        self.logger.info(
                            "Loaded subscription configurations",
                            path=self.config_path,
                            subscription_count=len(self._subscriptions),
                            event_type_count=len(self._event_types),
                        )
                except FileNotFoundError:
                    self.logger.info(
                        "No existing configuration file found, starting with empty repository",
                        path=self.config_path,
                    )
                except Exception as e:
                    self.logger.error(
                        "Error loading subscription configurations",
                        path=self.config_path,
                        error=str(e),
                        exc_info=True,
                    )

    async def save(self):
        """Save the current configurations to the config file."""
        if not self.config_path:
            return

        async with self._lock:
            try:
                data = {
                    "subscriptions": [
                        sub.model_dump() for sub in self._subscriptions.values()
                    ],
                    "event_types": [
                        et.model_dump() for et in self._event_types.values()
                    ],
                }

                with open(self.config_path, "w") as f:
                    json.dump(data, f, indent=2, default=str)

                self.logger.debug(
                    "Saved subscription configurations",
                    path=self.config_path,
                    subscription_count=len(self._subscriptions),
                    event_type_count=len(self._event_types),
                )
            except Exception as e:
                self.logger.error(
                    "Error saving subscription configurations",
                    path=self.config_path,
                    error=str(e),
                    exc_info=True,
                )

    async def create_subscription(self, config: SubscriptionConfig) -> SubscriptionInfo:
        """
        Create a new subscription.

        Args:
            config: The subscription configuration

        Returns:
            The created subscription information
        """
        async with self._lock:
            # Create subscription info
            subscription = SubscriptionInfo(
                **config.model_dump(),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            # Store in repository
            self._subscriptions[subscription.subscription_id] = subscription

            await self.save()

            self.logger.info(
                "Created subscription",
                subscription_id=subscription.subscription_id,
                event_type=subscription.event_type,
                handler=f"{subscription.handler_module}.{subscription.handler_name}",
            )

            return subscription

    async def update_subscription(
        self, subscription_id: str, config: SubscriptionConfig
    ) -> Result[SubscriptionInfo]:
        """
        Update an existing subscription.

        Args:
            subscription_id: The ID of the subscription to update
            config: The updated configuration

        Returns:
            Result containing the updated subscription or an error
        """
        async with self._lock:
            if subscription_id not in self._subscriptions:
                return Error(
                    NotFoundError(f"Subscription with ID {subscription_id} not found")
                )

            # Get existing subscription
            subscription = self._subscriptions[subscription_id]

            # Update fields from config
            update_data = config.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if key not in ["subscription_id", "created_at", "metrics"]:
                    setattr(subscription, key, value)

            # Update timestamp
            subscription.updated_at = datetime.now(UTC)

            await self.save()

            self.logger.info(
                "Updated subscription",
                subscription_id=subscription_id,
                event_type=subscription.event_type,
                is_active=subscription.is_active,
            )

            return subscription

    async def delete_subscription(self, subscription_id: str) -> Result[bool]:
        """
        Delete a subscription.

        Args:
            subscription_id: The ID of the subscription to delete

        Returns:
            Result containing True if successful or an error
        """
        async with self._lock:
            if subscription_id not in self._subscriptions:
                return Error(
                    NotFoundError(f"Subscription with ID {subscription_id} not found")
                )

            # Remove subscription
            del self._subscriptions[subscription_id]

            await self.save()

            self.logger.info("Deleted subscription", subscription_id=subscription_id)

            return True

    async def get_subscription(self, subscription_id: str) -> Result[SubscriptionInfo]:
        """
        Get a subscription by ID.

        Args:
            subscription_id: The ID of the subscription

        Returns:
            Result containing the subscription or an error
        """
        if subscription_id not in self._subscriptions:
            return Error(
                NotFoundError(f"Subscription with ID {subscription_id} not found")
            )

        return self._subscriptions[subscription_id]

    async def get_subscriptions(
        self, event_type: str | None = None
    ) -> list[SubscriptionInfo]:
        """
        Get all subscriptions, optionally filtered by event type.

        Args:
            event_type: Optional event type to filter by

        Returns:
            List of subscription information
        """
        if event_type:
            return [
                sub
                for sub in self._subscriptions.values()
                if sub.event_type == event_type
            ]
        else:
            return list(self._subscriptions.values())

    async def update_metrics(
        self, subscription_id: str, metrics: SubscriptionMetrics
    ) -> Result[bool]:
        """
        Update the metrics for a subscription.

        Args:
            subscription_id: The ID of the subscription
            metrics: The updated metrics

        Returns:
            Result containing True if successful or an error
        """
        async with self._lock:
            if subscription_id not in self._subscriptions:
                return Error(
                    NotFoundError(f"Subscription with ID {subscription_id} not found")
                )

            # Update metrics
            self._subscriptions[subscription_id].metrics = metrics

            # Don't save metrics to disk on every update
            # await self.save()

            return True

    async def register_event_type(self, event_type: EventTypeInfo) -> EventTypeInfo:
        """
        Register an event type.

        Args:
            event_type: The event type information

        Returns:
            The registered event type information
        """
        async with self._lock:
            self._event_types[event_type.name] = event_type

            await self.save()

            self.logger.info(
                "Registered event type",
                event_type=event_type.name,
                domain=event_type.domain,
            )

            return event_type

    async def get_event_types(self) -> list[EventTypeInfo]:
        """
        Get all registered event types.

        Returns:
            List of event type information
        """
        return list(self._event_types.values())

    async def get_event_type(self, name: str) -> Result[EventTypeInfo]:
        """
        Get an event type by name.

        Args:
            name: The name of the event type

        Returns:
            Result containing the event type or an error
        """
        if name not in self._event_types:
            return Error(NotFoundError(f"Event type {name} not found"))

        return self._event_types[name]


class SubscriptionManager(Disposable):
    """
    Manager for event subscriptions.

    This class provides a high-level API for managing event subscriptions,
    with support for dynamic registration, monitoring, and configuration.
    """

    def __init__(
        self,
        event_bus: EventBusProtocol,
        repository: SubscriptionRepository,
        auto_load: bool = True,
    ):
        """
        Initialize the subscription manager.

        Args:
            event_bus: The event bus to manage subscriptions for
            repository: The repository for persisting subscriptions
            auto_load: Whether to automatically load and register subscriptions on startup
        """
        self.event_bus = event_bus
        self.repository = repository
        self.auto_load = auto_load
        self.logger = structlog.get_logger("uno.events.subscription_manager")

        # Runtime tracking of handlers and metrics
        self._handlers: dict[str, EventHandler] = {}
        self._metrics_counters: dict[str, Counter] = {}
        self._metrics_timers: dict[str, Timer] = {}

        # Monitoring
        self._subscription_gauge = Gauge(
            name="event_subscriptions_active",
            description="Number of active event subscriptions",
            labels=["event_type"],
        )
        self._events_processed_counter = Counter(
            name="events_processed_total",
            description="Total number of events processed",
            labels=["event_type", "handler", "status"],
        )
        self._processing_time_timer = Timer(
            name="event_processing_time",
            description="Time taken to process events",
            labels=["event_type", "handler"],
        )

    async def initialize(self):
        """Initialize the subscription manager."""
        # Initialize the repository
        await self.repository.initialize()

        # Load and register subscriptions if auto_load is enabled
        if self.auto_load:
            await self.load_subscriptions()

    async def load_subscriptions(self):
        """Load and register all active subscriptions."""
        subscriptions = await self.repository.get_subscriptions()
        active_subscriptions = [sub for sub in subscriptions if sub.is_active]

        self.logger.info(
            "Loading subscriptions",
            total=len(subscriptions),
            active=len(active_subscriptions),
        )

        for subscription in active_subscriptions:
            await self.register_handler(subscription)

    async def register_handler(self, subscription: SubscriptionInfo) -> Result[bool]:
        """
        Register a handler from a subscription configuration.

        Args:
            subscription: The subscription configuration

        Returns:
            Result containing True if successful or an error
        """
        try:
            # Try to import the handler module
            module = importlib.import_module(subscription.handler_module)

            # Get the handler function
            if subscription.handler_function:
                handler_name = subscription.handler_function
            else:
                handler_name = subscription.handler_name

            if not hasattr(module, handler_name):
                return Error(
                    NotFoundError(
                        f"Handler function '{handler_name}' not found in module '{subscription.handler_module}'"
                    )
                )

            handler = getattr(module, handler_name)

            # Create a wrapper that tracks metrics
            @wraps(handler)
            async def metrics_wrapper(event: EventProtocol):
                # Track invocation
                subscription.metrics.invocation_count += 1
                subscription.metrics.last_invoked_at = datetime.now(UTC)

                # Track metrics using monitoring
                self._events_processed_counter.inc(
                    labels={
                        "event_type": event.event_type,
                        "handler": subscription.handler_name,
                        "status": "started",
                    }
                )

                start_time = datetime.now(UTC)

                try:
                    # Use async or sync call depending on handler type
                    if asyncio.iscoroutinefunction(handler):
                        with self._processing_time_timer.time(
                            labels={
                                "event_type": event.event_type,
                                "handler": subscription.handler_name,
                            }
                        ):
                            await handler(event)
                    else:
                        with self._processing_time_timer.time(
                            labels={
                                "event_type": event.event_type,
                                "handler": subscription.handler_name,
                            }
                        ):
                            handler(event)

                    # Track success
                    subscription.metrics.success_count += 1
                    self._events_processed_counter.inc(
                        labels={
                            "event_type": event.event_type,
                            "handler": subscription.handler_name,
                            "status": "success",
                        }
                    )
                except Exception as e:
                    # Track failure
                    subscription.metrics.failure_count += 1
                    self._events_processed_counter.inc(
                        labels={
                            "event_type": event.event_type,
                            "handler": subscription.handler_name,
                            "status": "failure",
                        }
                    )

                    # Log the error
                    self.logger.error(
                        "Error in event handler",
                        subscription_id=subscription.subscription_id,
                        event_type=event.event_type,
                        handler=f"{subscription.handler_module}.{subscription.handler_name}",
                        error=str(e),
                        exc_info=True,
                    )

                    # Re-raise for the event bus to handle
                    raise
                finally:
                    # Calculate processing time
                    end_time = datetime.now(UTC)
                    processing_time_ms = (end_time - start_time).total_seconds() * 1000

                    # Update metrics
                    if subscription.metrics.invocation_count == 1:
                        subscription.metrics.avg_processing_time_ms = processing_time_ms
                        subscription.metrics.min_processing_time_ms = processing_time_ms
                        subscription.metrics.max_processing_time_ms = processing_time_ms
                        subscription.metrics.p95_processing_time_ms = processing_time_ms
                        subscription.metrics.p99_processing_time_ms = processing_time_ms
                    else:
                        # Update rolling average
                        n = subscription.metrics.invocation_count
                        subscription.metrics.avg_processing_time_ms = (
                            subscription.metrics.avg_processing_time_ms * (n - 1) / n
                            + processing_time_ms / n
                        )

                        # Update min/max
                        subscription.metrics.min_processing_time_ms = min(
                            subscription.metrics.min_processing_time_ms,
                            processing_time_ms,
                        )
                        subscription.metrics.max_processing_time_ms = max(
                            subscription.metrics.max_processing_time_ms,
                            processing_time_ms,
                        )

                        # Simple approximation for p95/p99 (more accurate would use a sliding window)
                        if (
                            processing_time_ms
                            > subscription.metrics.p95_processing_time_ms
                        ):
                            subscription.metrics.p95_processing_time_ms = (
                                0.95 * subscription.metrics.p95_processing_time_ms
                                + 0.05 * processing_time_ms
                            )
                        if (
                            processing_time_ms
                            > subscription.metrics.p99_processing_time_ms
                        ):
                            subscription.metrics.p99_processing_time_ms = (
                                0.99 * subscription.metrics.p99_processing_time_ms
                                + 0.01 * processing_time_ms
                            )

                    # Periodically update metrics in repository
                    if subscription.metrics.invocation_count % 10 == 0:
                        asyncio.create_task(
                            self.repository.update_metrics(
                                subscription.subscription_id, subscription.metrics
                            )
                        )

            # Store the wrapped handler
            wrapped_handler = metrics_wrapper
            self._handlers[subscription.subscription_id] = wrapped_handler

            # Subscribe the handler to the event bus
            await self.event_bus.subscribe(subscription.event_type, wrapped_handler)

            # Update the gauge
            self._subscription_gauge.set(
                len(
                    [
                        s
                        for s in await self.repository.get_subscriptions(
                            subscription.event_type
                        )
                        if s.is_active
                    ]
                ),
                labels={"event_type": subscription.event_type},
            )

            self.logger.info(
                "Registered event handler",
                subscription_id=subscription.subscription_id,
                event_type=subscription.event_type,
                handler=f"{subscription.handler_module}.{subscription.handler_name}",
            )

            return True
        except Exception as e:
            self.logger.error(
                "Error registering event handler",
                subscription_id=subscription.subscription_id,
                event_type=subscription.event_type,
                handler=f"{subscription.handler_module}.{subscription.handler_name}",
                error=str(e),
                exc_info=True,
            )
            return Error(e)

    async def unregister_handler(self, subscription_id: str) -> Result[bool]:
        """
        Unregister a handler.

        Args:
            subscription_id: The ID of the subscription to unregister

        Returns:
            Result containing True if successful or an error
        """
        if subscription_id not in self._handlers:
            return Error(
                NotFoundError(f"No active handler for subscription {subscription_id}")
            )

        try:
            # Get the subscription and handler
            result = await self.repository.get_subscription(subscription_id)
            if isinstance(result, Error):
                return result

            subscription = result
            handler = self._handlers[subscription_id]

            # Unsubscribe from event bus
            await self.event_bus.unsubscribe(subscription.event_type, handler)

            # Remove from handler registry
            del self._handlers[subscription_id]

            # Update the gauge
            self._subscription_gauge.set(
                len(
                    [
                        s
                        for s in await self.repository.get_subscriptions(
                            subscription.event_type
                        )
                        if s.is_active
                    ]
                ),
                labels={"event_type": subscription.event_type},
            )

            self.logger.info(
                "Unregistered event handler",
                subscription_id=subscription_id,
                event_type=subscription.event_type,
                handler=f"{subscription.handler_module}.{subscription.handler_name}",
            )

            return True
        except Exception as e:
            self.logger.error(
                "Error unregistering event handler",
                subscription_id=subscription_id,
                error=str(e),
                exc_info=True,
            )
            return Error(e)

    async def create_subscription(
        self, config: SubscriptionConfig
    ) -> Result[SubscriptionInfo]:
        """
        Create a new subscription.

        Args:
            config: The subscription configuration

        Returns:
            Result containing the created subscription or an error
        """
        # Create in repository
        subscription = await self.repository.create_subscription(config)

        # Register handler if active
        if subscription.is_active:
            result = await self.register_handler(subscription)
            if isinstance(result, Error):
                self.logger.warning(
                    "Created subscription but failed to register handler",
                    subscription_id=subscription.subscription_id,
                    error=str(result),
                )

        return subscription

    async def update_subscription(
        self, subscription_id: str, config: SubscriptionConfig
    ) -> Result[SubscriptionInfo]:
        """
        Update an existing subscription.

        Args:
            subscription_id: The ID of the subscription to update
            config: The updated configuration

        Returns:
            Result containing the updated subscription or an error
        """
        # Get current subscription
        current_result = await self.repository.get_subscription(subscription_id)
        if isinstance(current_result, Error):
            return current_result

        current = current_result
        was_active = current.is_active

        # Update in repository
        result = await self.repository.update_subscription(subscription_id, config)
        if isinstance(result, Error):
            return result

        updated = result
        is_active = updated.is_active

        # Handle activation state changes
        if not was_active and is_active:
            # Subscription was activated
            await self.register_handler(updated)
        elif was_active and not is_active:
            # Subscription was deactivated
            await self.unregister_handler(subscription_id)
        elif (
            was_active
            and is_active
            and (
                updated.event_type != current.event_type
                or updated.handler_module != current.handler_module
                or updated.handler_name != current.handler_name
                or updated.handler_function != current.handler_function
            )
        ):
            # Handler details changed, re-register
            await self.unregister_handler(subscription_id)
            await self.register_handler(updated)

        return updated

    async def delete_subscription(self, subscription_id: str) -> Result[bool]:
        """
        Delete a subscription.

        Args:
            subscription_id: The ID of the subscription to delete

        Returns:
            Result containing True if successful or an error
        """
        # Get current subscription
        current_result = await self.repository.get_subscription(subscription_id)
        if isinstance(current_result, Error):
            return current_result

        current = current_result

        # Unregister if active
        if current.is_active and subscription_id in self._handlers:
            await self.unregister_handler(subscription_id)

        # Delete from repository
        return await self.repository.delete_subscription(subscription_id)

    async def get_active_subscriptions(self) -> list[SubscriptionInfo]:
        """
        Get all active subscriptions.

        Returns:
            List of active subscription information
        """
        subscriptions = await self.repository.get_subscriptions()
        return [sub for sub in subscriptions if sub.is_active]

    async def get_metrics(self) -> dict[str, Any]:
        """
        Get overall metrics for all subscriptions.

        Returns:
            Dictionary containing aggregated metrics
        """
        subscriptions = await self.repository.get_subscriptions()

        total_invocations = 0
        total_success = 0
        total_failure = 0
        processing_times = []

        event_types = {}
        handlers = {}

        for sub in subscriptions:
            metrics = sub.metrics
            total_invocations += metrics.invocation_count
            total_success += metrics.success_count
            total_failure += metrics.failure_count

            if metrics.invocation_count > 0:
                processing_times.append(metrics.avg_processing_time_ms)

            # Group by event type
            if sub.event_type not in event_types:
                event_types[sub.event_type] = {
                    "name": sub.event_type,
                    "subscription_count": 0,
                    "invocation_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                }

            event_types[sub.event_type]["subscription_count"] += 1
            event_types[sub.event_type]["invocation_count"] += metrics.invocation_count
            event_types[sub.event_type]["success_count"] += metrics.success_count
            event_types[sub.event_type]["failure_count"] += metrics.failure_count

            # Group by handler
            handler_key = f"{sub.handler_module}.{sub.handler_name}"
            if handler_key not in handlers:
                handlers[handler_key] = {
                    "name": handler_key,
                    "subscription_count": 0,
                    "invocation_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "avg_processing_time_ms": 0,
                }

            handlers[handler_key]["subscription_count"] += 1
            handlers[handler_key]["invocation_count"] += metrics.invocation_count
            handlers[handler_key]["success_count"] += metrics.success_count
            handlers[handler_key]["failure_count"] += metrics.failure_count

            if metrics.invocation_count > 0:
                # Weighted average for processing time
                handlers[handler_key]["avg_processing_time_ms"] = (
                    handlers[handler_key]["avg_processing_time_ms"]
                    * (
                        handlers[handler_key]["invocation_count"]
                        - metrics.invocation_count
                    )
                    + metrics.avg_processing_time_ms * metrics.invocation_count
                ) / handlers[handler_key]["invocation_count"]

        # Calculate overall average processing time
        avg_processing_time_ms = (
            sum(processing_times) / len(processing_times) if processing_times else 0
        )

        return {
            "total_subscriptions": len(subscriptions),
            "active_subscriptions": len(
                [sub for sub in subscriptions if sub.is_active]
            ),
            "event_types_count": len(event_types),
            "handlers_count": len(handlers),
            "invocations": {
                "total": total_invocations,
                "success": total_success,
                "failure": total_failure,
                "success_rate": (
                    total_success / total_invocations if total_invocations > 0 else 1.0
                ),
            },
            "avg_processing_time_ms": avg_processing_time_ms,
            "by_event_type": list(event_types.values()),
            "by_handler": list(handlers.values()),
        }

    async def dispose(self) -> None:
        """
        Dispose of the subscription manager, unregistering all handlers.

        This is called when the application is shutting down.
        """
        # Unregister all handlers
        active_subscriptions = list(self._handlers.keys())

        for subscription_id in active_subscriptions:
            await self.unregister_handler(subscription_id)

        self.logger.info(
            "Subscription manager disposed",
            unregistered_handlers=len(active_subscriptions),
        )


def wraps(wrapped):
    """Simple decorator to mimic functools.wraps."""

    def decorator(wrapper):
        wrapper.__name__ = wrapped.__name__
        wrapper.__doc__ = wrapped.__doc__
        wrapper.__module__ = wrapped.__module__
        return wrapper

    return decorator
