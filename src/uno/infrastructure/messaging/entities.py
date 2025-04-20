# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional, Dict, Any

from uno.domain.core import Entity, AggregateRoot, ValueObject
from uno.enums import MessageImportance


@dataclass
class MessageUser(Entity):
    """Represents a relationship between a message and a user."""

    id: str
    message_id: str
    user_id: str
    is_sender: bool = False
    is_addressee: bool = True
    is_copied_on: bool = False
    is_blind_copied_on: bool = False
    is_read: bool = False
    read_at: Optional[datetime] = None

    def mark_as_read(self) -> None:
        """Mark the message as read by this user."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now(UTC)


@dataclass
class Message(AggregateRoot):
    """Represents a message in the system."""

    id: str
    subject: str
    body: str
    flag: MessageImportance = MessageImportance.INFORMATION
    is_draft: bool = True
    sent_at: Optional[datetime] = None
    parent_id: str | None = None
    users: list[MessageUser] = field(default_factory=list)
    meta_record_ids: list[str] = field(default_factory=list)
    group_id: str | None = None

    def send(self) -> None:
        """Send the message, marking it as no longer a draft."""
        if self.is_draft:
            self.is_draft = False
            self.sent_at = datetime.now(UTC)

    def add_user(
        self,
        user_id: str,
        is_sender: bool = False,
        is_addressee: bool = False,
        is_copied_on: bool = False,
        is_blind_copied_on: bool = False,
    ) -> MessageUser:
        """Add a user to the message."""
        if self._find_user(user_id) is not None:
            raise ValueError(f"User {user_id} is already associated with this message")

        message_user = MessageUser(
            id=f"{self.id}_{user_id}",
            message_id=self.id,
            user_id=user_id,
            is_sender=is_sender,
            is_addressee=is_addressee,
            is_copied_on=is_copied_on,
            is_blind_copied_on=is_blind_copied_on,
        )

        self.users.append(message_user)
        return message_user

    def add_meta_record(self, meta_record_id: str) -> None:
        """Add a meta record to the message."""
        if meta_record_id in self.meta_record_ids:
            return

        self.meta_record_ids.append(meta_record_id)

    def remove_meta_record(self, meta_record_id: str) -> None:
        """Remove a meta record from the message."""
        if meta_record_id in self.meta_record_ids:
            self.meta_record_ids.remove(meta_record_id)

    def mark_as_read_by_user(self, user_id: str) -> None:
        """Mark the message as read by a specific user."""
        message_user = self._find_user(user_id)
        if message_user:
            message_user.mark_as_read()

    def _find_user(self, user_id: str) -> Optional[MessageUser]:
        """Find a user associated with this message."""
        for user in self.users:
            if user.user_id == user_id:
                return user
        return None

    def is_read_by_user(self, user_id: str) -> bool:
        """Check if the message is read by a specific user."""
        message_user = self._find_user(user_id)
        return message_user is not None and message_user.is_read
