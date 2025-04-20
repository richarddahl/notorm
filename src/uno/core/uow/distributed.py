# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Distributed Unit of Work implementation.

This module defines a distributed implementation of the Unit of Work pattern
that can coordinate transactions across multiple services, databases, and
other resources to ensure consistency in distributed systems.
"""

import asyncio
import logging
import uuid
from datetime import datetime, UTC
from enum import Enum, auto
from typing import (
    Dict,
    List,
    Any,
    Optional,
    Set,
    Type,
    Callable,
    Awaitable,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Field

from uno.core.uow.base import AbstractUnitOfWork
from uno.core.events import Event, AsyncEventBus
from uno.core.logging import get_logger
from uno.core.errors import Result, Error

# Type variables
T = TypeVar("T")


class TwoPhaseStatus(Enum):
    """Status of a two-phase commit participant."""

    INIT = auto()
    PREPARING = auto()
    PREPARED = auto()
    COMMITTING = auto()
    COMMITTED = auto()
    ROLLING_BACK = auto()
    ROLLED_BACK = auto()
    FAILED = auto()


class ResourceStatus(BaseModel):
    """Status of a resource in a distributed transaction."""

    resource_id: str
    resource_type: str
    status: TwoPhaseStatus = TwoPhaseStatus.INIT
    prepare_time: Optional[datetime] = None
    commit_time: Optional[datetime] = None
    rollback_time: Optional[datetime] = None
    error: str | None = None


class Participant(BaseModel):
    """A participant in a distributed transaction."""

    participant_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    resource_type: str
    status: TwoPhaseStatus = TwoPhaseStatus.INIT


class DistributedTransaction(BaseModel):
    """Represents a distributed transaction across multiple services."""

    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    coordinator_id: str
    status: TwoPhaseStatus = TwoPhaseStatus.INIT
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    prepare_time: Optional[datetime] = None
    commit_time: Optional[datetime] = None
    rollback_time: Optional[datetime] = None
    participants: Dict[str, Participant] = Field(default_factory=dict)
    prepared_participants: Set[str] = Field(default_factory=set)
    committed_participants: Set[str] = Field(default_factory=set)
    rolled_back_participants: Set[str] = Field(default_factory=set)


class TransactionParticipant:
    """
    Interface for transaction participants in the two-phase commit protocol.

    Participants in a two-phase commit must implement this interface to
    participate in distributed transactions.
    """

    async def prepare(self, transaction_id: str) -> Result[bool, Error]:
        """
        Prepare the resource for a transaction (phase 1).

        This should do all the work up to the point of actually committing,
        and should guarantee that commit will succeed if prepare succeeds.

        Args:
            transaction_id: ID of the distributed transaction

        Returns:
            Result indicating success or failure
        """
        raise NotImplementedError("prepare() must be implemented by subclasses")

    async def commit(self, transaction_id: str) -> Result[bool, Error]:
        """
        Commit the transaction (phase 2).

        This should finalize the changes prepared in phase 1.

        Args:
            transaction_id: ID of the distributed transaction

        Returns:
            Result indicating success or failure
        """
        raise NotImplementedError("commit() must be implemented by subclasses")

    async def rollback(self, transaction_id: str) -> Result[bool, Error]:
        """
        Rollback the transaction.

        This should undo any changes made during prepare.

        Args:
            transaction_id: ID of the distributed transaction

        Returns:
            Result indicating success or failure
        """
        raise NotImplementedError("rollback() must be implemented by subclasses")


class UnitOfWorkParticipant(TransactionParticipant):
    """
    Adapter that allows a Unit of Work to participate in distributed transactions.

    This class adapts the Unit of Work interface to the TransactionParticipant interface,
    allowing Units of Work to be used in distributed transactions.
    """

    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        name: str,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the Unit of Work participant.

        Args:
            unit_of_work: The Unit of Work to adapt
            name: Name of this participant
            logger: Optional logger for diagnostics
        """
        self.unit_of_work = unit_of_work
        self.name = name
        self.logger = logger or get_logger(f"uno.uow.participant.{name}")
        self._prepared_transactions: Dict[str, Any] = {}

    async def prepare(self, transaction_id: str) -> Result[bool, Error]:
        """
        Prepare the Unit of Work for a transaction.

        Args:
            transaction_id: ID of the distributed transaction

        Returns:
            Result indicating success or failure
        """
        try:
            # Begin the transaction
            await self.unit_of_work.begin()

            # Store the transaction for later
            self._prepared_transactions[transaction_id] = self.unit_of_work

            self.logger.debug(f"Prepared transaction {transaction_id}")
            return Result.ok(True)
        except Exception as e:
            self.logger.error(f"Failed to prepare transaction {transaction_id}: {e}")
            return Result.err(
                Error(
                    message=f"Failed to prepare transaction: {str(e)}",
                    error_code="PREPARE_FAILED",
                    context={"transaction_id": transaction_id},
                )
            )

    async def commit(self, transaction_id: str) -> Result[bool, Error]:
        """
        Commit the prepared Unit of Work transaction.

        Args:
            transaction_id: ID of the distributed transaction

        Returns:
            Result indicating success or failure
        """
        if transaction_id not in self._prepared_transactions:
            return Result.err(
                Error(
                    message=f"Transaction {transaction_id} not prepared",
                    error_code="TRANSACTION_NOT_PREPARED",
                    context={"transaction_id": transaction_id},
                )
            )

        try:
            # Commit the transaction
            await self.unit_of_work.commit()

            # Publish any events
            await self.unit_of_work.publish_events()

            # Remove the transaction
            del self._prepared_transactions[transaction_id]

            self.logger.debug(f"Committed transaction {transaction_id}")
            return Result.ok(True)
        except Exception as e:
            self.logger.error(f"Failed to commit transaction {transaction_id}: {e}")
            return Result.err(
                Error(
                    message=f"Failed to commit transaction: {str(e)}",
                    error_code="COMMIT_FAILED",
                    context={"transaction_id": transaction_id},
                )
            )

    async def rollback(self, transaction_id: str) -> Result[bool, Error]:
        """
        Rollback the prepared Unit of Work transaction.

        Args:
            transaction_id: ID of the distributed transaction

        Returns:
            Result indicating success or failure
        """
        if transaction_id not in self._prepared_transactions:
            return Result.err(
                Error(
                    message=f"Transaction {transaction_id} not prepared",
                    error_code="TRANSACTION_NOT_PREPARED",
                    context={"transaction_id": transaction_id},
                )
            )

        try:
            # Rollback the transaction
            await self.unit_of_work.rollback()

            # Remove the transaction
            del self._prepared_transactions[transaction_id]

            self.logger.debug(f"Rolled back transaction {transaction_id}")
            return Result.ok(True)
        except Exception as e:
            self.logger.error(f"Failed to rollback transaction {transaction_id}: {e}")
            return Result.err(
                Error(
                    message=f"Failed to rollback transaction: {str(e)}",
                    error_code="ROLLBACK_FAILED",
                    context={"transaction_id": transaction_id},
                )
            )


class EventStoreParticipant(TransactionParticipant):
    """
    Transaction participant for event stores.

    This participant allows event stores to participate in distributed
    transactions, ensuring that events are only committed when the entire
    distributed transaction succeeds.
    """

    def __init__(
        self,
        event_store: Any,
        name: str,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the event store participant.

        Args:
            event_store: The event store to use
            name: Name of this participant
            logger: Optional logger for diagnostics
        """
        self.event_store = event_store
        self.name = name
        self.logger = logger or get_logger(f"uno.uow.participant.{name}")
        self._pending_events: Dict[str, list[Event]] = {}

    def add_events(self, transaction_id: str, events: list[Event]) -> None:
        """
        Add events to be committed as part of the transaction.

        Args:
            transaction_id: ID of the distributed transaction
            events: Events to add to the transaction
        """
        if transaction_id not in self._pending_events:
            self._pending_events[transaction_id] = []

        self._pending_events[transaction_id].extend(events)
        self.logger.debug(f"Added {len(events)} events to transaction {transaction_id}")

    async def prepare(self, transaction_id: str) -> Result[bool, Error]:
        """
        Prepare the event store for a transaction.

        For event stores, this doesn't actually do anything since the events
        are only stored during commit.

        Args:
            transaction_id: ID of the distributed transaction

        Returns:
            Result indicating success or failure
        """
        # Verify that we have events for this transaction
        if transaction_id not in self._pending_events:
            self.logger.warning(f"No events for transaction {transaction_id}")
            self._pending_events[transaction_id] = []

        self.logger.debug(f"Prepared event store for transaction {transaction_id}")
        return Result.ok(True)

    async def commit(self, transaction_id: str) -> Result[bool, Error]:
        """
        Commit the events for the transaction.

        Args:
            transaction_id: ID of the distributed transaction

        Returns:
            Result indicating success or failure
        """
        if transaction_id not in self._pending_events:
            self.logger.warning(f"No events for transaction {transaction_id}")
            return Result.ok(True)

        events = self._pending_events[transaction_id]
        if not events:
            # No events to commit
            del self._pending_events[transaction_id]
            return Result.ok(True)

        try:
            # Store the events
            await self.event_store.append_events(events)

            # Remove the pending events
            del self._pending_events[transaction_id]

            self.logger.debug(
                f"Committed {len(events)} events for transaction {transaction_id}"
            )
            return Result.ok(True)
        except Exception as e:
            self.logger.error(
                f"Failed to commit events for transaction {transaction_id}: {e}"
            )
            return Result.err(
                Error(
                    message=f"Failed to commit events: {str(e)}",
                    error_code="EVENT_COMMIT_FAILED",
                    context={"transaction_id": transaction_id},
                )
            )

    async def rollback(self, transaction_id: str) -> Result[bool, Error]:
        """
        Rollback the events for the transaction.

        For event stores, this just means discarding the pending events.

        Args:
            transaction_id: ID of the distributed transaction

        Returns:
            Result indicating success or failure
        """
        if transaction_id in self._pending_events:
            del self._pending_events[transaction_id]

        self.logger.debug(f"Rolled back events for transaction {transaction_id}")
        return Result.ok(True)


class DistributedUnitOfWork(AbstractUnitOfWork):
    """
    Distributed implementation of the Unit of Work pattern.

    This implementation coordinates transactions across multiple services,
    databases, and other resources to ensure consistency in distributed systems.
    It implements a two-phase commit protocol for transaction coordination.
    """

    def __init__(
        self,
        coordinator_id: str | None = None,
        transaction_id: str | None = None,
        event_bus: Optional[AsyncEventBus] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the distributed Unit of Work.

        Args:
            coordinator_id: ID of the coordinator (defaults to a random UUID)
            transaction_id: ID of the transaction (defaults to a random UUID)
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostics
        """
        super().__init__(event_bus, logger)
        self.coordinator_id = coordinator_id or str(uuid.uuid4())
        self.transaction = DistributedTransaction(
            transaction_id=transaction_id or str(uuid.uuid4()),
            coordinator_id=self.coordinator_id,
        )
        self.participants: Dict[str, TransactionParticipant] = {}
        self._logger = logger or get_logger(
            f"uno.uow.distributed.{self.coordinator_id[:8]}"
        )

    def register_participant(
        self, name: str, participant: TransactionParticipant
    ) -> str:
        """
        Register a participant in the distributed transaction.

        Args:
            name: Name of the participant
            participant: The participant implementation

        Returns:
            ID of the participant
        """
        participant_id = str(uuid.uuid4())

        # Add to participants dictionary
        self.participants[participant_id] = participant

        # Add to transaction
        self.transaction.participants[participant_id] = Participant(
            participant_id=participant_id,
            name=name,
            resource_type=participant.__class__.__name__,
        )

        self._logger.debug(f"Registered participant {name} with ID {participant_id}")
        return participant_id

    def register_unit_of_work(self, name: str, unit_of_work: AbstractUnitOfWork) -> str:
        """
        Register a Unit of Work as a participant.

        Args:
            name: Name of the Unit of Work
            unit_of_work: The Unit of Work to register

        Returns:
            ID of the participant
        """
        participant = UnitOfWorkParticipant(unit_of_work, name)
        return self.register_participant(name, participant)

    def register_event_store(self, name: str, event_store: Any) -> str:
        """
        Register an event store as a participant.

        Args:
            name: Name of the event store
            event_store: The event store to register

        Returns:
            ID of the participant
        """
        participant = EventStoreParticipant(event_store, name)
        return self.register_participant(name, participant)

    def add_events_to_participant(
        self, participant_id: str, events: list[Event]
    ) -> None:
        """
        Add events to a participant for eventual commit.

        Args:
            participant_id: ID of the participant
            events: Events to add
        """
        if participant_id not in self.participants:
            raise ValueError(f"Participant {participant_id} not found")

        participant = self.participants[participant_id]
        if not isinstance(participant, EventStoreParticipant):
            raise TypeError(
                f"Participant {participant_id} is not an EventStoreParticipant"
            )

        participant.add_events(self.transaction.transaction_id, events)

    async def prepare_all(self) -> bool:
        """
        Prepare all participants for commit (phase 1).

        Returns:
            True if all participants were prepared successfully, False otherwise
        """
        if not self.participants:
            self._logger.warning("No participants to prepare")
            return True

        self.transaction.status = TwoPhaseStatus.PREPARING
        self.transaction.prepare_time = datetime.now(UTC)

        # Prepare all participants
        prepare_tasks = []
        for participant_id, participant in self.participants.items():
            self._logger.debug(f"Preparing participant {participant_id}")
            prepare_tasks.append(participant.prepare(self.transaction.transaction_id))

        # Wait for all preparations to complete
        results = await asyncio.gather(*prepare_tasks, return_exceptions=True)

        # Check results
        all_prepared = True
        for i, (participant_id, participant) in enumerate(self.participants.items()):
            result = results[i]

            if isinstance(result, Exception):
                self._logger.error(
                    f"Error preparing participant {participant_id}: {result}"
                )
                all_prepared = False
                continue

            if result.is_error():
                self._logger.error(
                    f"Failed to prepare participant {participant_id}: {result.unwrap_error()}"
                )
                all_prepared = False
                continue

            # Preparation succeeded
            self.transaction.prepared_participants.add(participant_id)
            self._logger.debug(f"Participant {participant_id} prepared successfully")

        # Update transaction status
        if all_prepared:
            self.transaction.status = TwoPhaseStatus.PREPARED
            self._logger.info(
                f"All {len(self.participants)} participants prepared successfully"
            )
        else:
            self.transaction.status = TwoPhaseStatus.FAILED
            self._logger.error(
                f"Failed to prepare all participants. {len(self.transaction.prepared_participants)} of {len(self.participants)} prepared."
            )

        return all_prepared

    async def commit_all(self) -> bool:
        """
        Commit all prepared participants (phase 2).

        Returns:
            True if all participants were committed successfully, False otherwise
        """
        if not self.transaction.prepared_participants:
            self._logger.warning("No prepared participants to commit")
            return True

        self.transaction.status = TwoPhaseStatus.COMMITTING
        self.transaction.commit_time = datetime.now(UTC)

        # Commit all prepared participants
        commit_tasks = []
        for participant_id in self.transaction.prepared_participants:
            if participant_id not in self.participants:
                self._logger.error(f"Participant {participant_id} not found")
                continue

            participant = self.participants[participant_id]
            self._logger.debug(f"Committing participant {participant_id}")
            commit_tasks.append(participant.commit(self.transaction.transaction_id))

        # Wait for all commits to complete
        results = await asyncio.gather(*commit_tasks, return_exceptions=True)

        # Check results
        all_committed = True
        for i, participant_id in enumerate(self.transaction.prepared_participants):
            if i >= len(results):
                continue

            result = results[i]

            if isinstance(result, Exception):
                self._logger.error(
                    f"Error committing participant {participant_id}: {result}"
                )
                all_committed = False
                continue

            if result.is_error():
                self._logger.error(
                    f"Failed to commit participant {participant_id}: {result.unwrap_error()}"
                )
                all_committed = False
                continue

            # Commit succeeded
            self.transaction.committed_participants.add(participant_id)
            self._logger.debug(f"Participant {participant_id} committed successfully")

        # Update transaction status
        if all_committed:
            self.transaction.status = TwoPhaseStatus.COMMITTED
            self._logger.info(
                f"All {len(self.transaction.prepared_participants)} prepared participants committed successfully"
            )
        else:
            self.transaction.status = TwoPhaseStatus.FAILED
            self._logger.error(
                f"Failed to commit all prepared participants. {len(self.transaction.committed_participants)} of {len(self.transaction.prepared_participants)} committed."
            )

        return all_committed

    async def rollback_all(self) -> bool:
        """
        Rollback all prepared participants.

        Returns:
            True if all participants were rolled back successfully, False otherwise
        """
        # Only roll back prepared participants
        to_rollback = (
            self.transaction.prepared_participants
            - self.transaction.committed_participants
        )

        if not to_rollback:
            self._logger.debug("No prepared participants to roll back")
            return True

        self.transaction.status = TwoPhaseStatus.ROLLING_BACK
        self.transaction.rollback_time = datetime.now(UTC)

        # Roll back all prepared participants
        rollback_tasks = []
        for participant_id in to_rollback:
            if participant_id not in self.participants:
                self._logger.error(f"Participant {participant_id} not found")
                continue

            participant = self.participants[participant_id]
            self._logger.debug(f"Rolling back participant {participant_id}")
            rollback_tasks.append(participant.rollback(self.transaction.transaction_id))

        # Wait for all rollbacks to complete
        results = await asyncio.gather(*rollback_tasks, return_exceptions=True)

        # Check results
        all_rolled_back = True
        for i, participant_id in enumerate(to_rollback):
            if i >= len(results):
                continue

            result = results[i]

            if isinstance(result, Exception):
                self._logger.error(
                    f"Error rolling back participant {participant_id}: {result}"
                )
                all_rolled_back = False
                continue

            if result.is_error():
                self._logger.error(
                    f"Failed to roll back participant {participant_id}: {result.unwrap_error()}"
                )
                all_rolled_back = False
                continue

            # Rollback succeeded
            self.transaction.rolled_back_participants.add(participant_id)
            self._logger.debug(f"Participant {participant_id} rolled back successfully")

        # Update transaction status
        if all_rolled_back:
            self.transaction.status = TwoPhaseStatus.ROLLED_BACK
            self._logger.info(
                f"All {len(to_rollback)} participants rolled back successfully"
            )
        else:
            self.transaction.status = TwoPhaseStatus.FAILED
            self._logger.error(
                f"Failed to roll back all participants. {len(self.transaction.rolled_back_participants)} of {len(to_rollback)} rolled back."
            )

        return all_rolled_back

    async def begin(self) -> None:
        """Begin the distributed transaction."""
        self._logger.debug(
            f"Beginning distributed transaction {self.transaction.transaction_id}"
        )
        # The actual work happens in prepare
        pass

    async def commit(self) -> None:
        """
        Commit the distributed transaction.

        This implements the two-phase commit protocol:
        1. Prepare all participants
        2. If all preparations succeed, commit all participants
        3. If any preparation fails, rollback all participants
        """
        self._logger.debug(
            f"Committing distributed transaction {self.transaction.transaction_id}"
        )

        # Phase 1: Prepare all participants
        prepared = await self.prepare_all()

        if not prepared:
            # Some preparations failed, rollback everything
            self._logger.error("Preparation failed, rolling back all participants")
            await self.rollback_all()
            raise RuntimeError("Failed to prepare all participants for commit")

        # Phase 2: Commit all prepared participants
        committed = await self.commit_all()

        if not committed:
            # This is a critical error - some participants committed but others failed
            # This leaves the system in an inconsistent state that requires manual resolution
            self._logger.critical(
                "PARTIAL COMMIT FAILURE: Some participants committed but others failed. "
                "The system is in an inconsistent state and requires manual recovery."
            )
            raise RuntimeError("Failed to commit all prepared participants")

        self._logger.info(
            f"Successfully committed distributed transaction {self.transaction.transaction_id}"
        )

    async def rollback(self) -> None:
        """
        Rollback the distributed transaction.

        This rolls back all prepared participants.
        """
        self._logger.debug(
            f"Rolling back distributed transaction {self.transaction.transaction_id}"
        )
        await self.rollback_all()

        # Even if not all participants rolled back, we've done our best
        # Log a warning but don't raise an exception
        if self.transaction.status == TwoPhaseStatus.FAILED:
            self._logger.warning(
                f"Could not roll back all participants in transaction {self.transaction.transaction_id}. "
                f"Only {len(self.transaction.rolled_back_participants)} of {len(self.transaction.prepared_participants)} were rolled back."
            )
        else:
            self._logger.info(
                f"Successfully rolled back distributed transaction {self.transaction.transaction_id}"
            )

    def get_transaction_status(self) -> Dict[str, Any]:
        """
        Get the status of the distributed transaction.

        Returns:
            Dictionary with transaction status information
        """
        return {
            "transaction_id": self.transaction.transaction_id,
            "coordinator_id": self.transaction.coordinator_id,
            "status": self.transaction.status.name,
            "start_time": (
                self.transaction.start_time.isoformat()
                if self.transaction.start_time
                else None
            ),
            "prepare_time": (
                self.transaction.prepare_time.isoformat()
                if self.transaction.prepare_time
                else None
            ),
            "commit_time": (
                self.transaction.commit_time.isoformat()
                if self.transaction.commit_time
                else None
            ),
            "rollback_time": (
                self.transaction.rollback_time.isoformat()
                if self.transaction.rollback_time
                else None
            ),
            "participant_count": len(self.transaction.participants),
            "prepared_count": len(self.transaction.prepared_participants),
            "committed_count": len(self.transaction.committed_participants),
            "rolled_back_count": len(self.transaction.rolled_back_participants),
            "participants": {
                participant_id: {
                    "name": participant.name,
                    "resource_type": participant.resource_type,
                    "status": (
                        "COMMITTED"
                        if participant_id in self.transaction.committed_participants
                        else (
                            "ROLLED_BACK"
                            if participant_id
                            in self.transaction.rolled_back_participants
                            else (
                                "PREPARED"
                                if participant_id
                                in self.transaction.prepared_participants
                                else "INIT"
                            )
                        )
                    ),
                }
                for participant_id, participant in self.transaction.participants.items()
            },
        }
