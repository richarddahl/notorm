from typing import Protocol, Any, Mapping, Sequence
from datetime import datetime

class EventBusProtocol(Protocol):
    async def publish(
        self,
        event: Any,
        *,
        metadata: Mapping[str, Any] | None = None,
        timestamp: datetime | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """
        Publish a single domain event asynchronously with optional metadata.

        Args:
            event: The domain event to publish.
            metadata: Arbitrary metadata (e.g., user, source, tracing info).
            timestamp: Event occurrence time (defaults to now if None).
            correlation_id: Optional correlation or causation ID.
        """
        ...

    async def publish_many(
        self,
        events: Sequence[Any],
        *,
        metadata: Mapping[str, Any] | None = None,
        timestamp: datetime | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """
        Publish multiple domain events asynchronously with optional metadata.

        Args:
            events: A sequence of domain events to publish.
            metadata: Arbitrary metadata applied to all events.
            timestamp: Event occurrence time (applied to all events if specified).
            correlation_id: Optional correlation or causation ID.
        """
        ...
