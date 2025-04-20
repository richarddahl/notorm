# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import uuid
from typing import List, Optional, Protocol, Dict, Any, runtime_checkable, Union
from datetime import datetime, UTC

from uno.domain.service import DomainService
from uno.messaging.entities import Message, MessageUser
from uno.messaging.domain_repositories import MessageRepositoryProtocol
from uno.enums import MessageImportance
from uno.core.errors import EntityNotFoundError


@runtime_checkable
class MessageDomainServiceProtocol(Protocol):
    """Protocol for message domain service."""

    async def get_message(self, message_id: str) -> Message:
        """Get a message by ID."""
        ...

    async def get_messages_for_user(
        self,
        user_id: str,
        only_unread: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Message]:
        """Get messages for a user."""
        ...

    async def get_draft_messages(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> list[Message]:
        """Get draft messages for a user."""
        ...

    async def get_sent_messages(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> list[Message]:
        """Get sent messages for a user."""
        ...

    async def get_message_thread(
        self, parent_message_id: str, page: int = 1, page_size: int = 20
    ) -> list[Message]:
        """Get a message thread."""
        ...

    async def create_message(
        self,
        subject: str,
        body: str,
        sender_id: str,
        recipient_ids: list[str],
        cc_ids: list[str] = None,
        bcc_ids: list[str] = None,
        flag: MessageImportance = MessageImportance.INFORMATION,
        is_draft: bool = True,
        parent_id: str | None = None,
        meta_record_ids: list[str] = None,
        group_id: str | None = None,
    ) -> Message:
        """Create a new message."""
        ...

    async def update_message(
        self,
        message_id: str,
        subject: str | None = None,
        body: str | None = None,
        recipient_ids: list[str] | None = None,
        cc_ids: list[str] | None = None,
        bcc_ids: list[str] | None = None,
        flag: Optional[MessageImportance] = None,
        meta_record_ids: list[str] | None = None,
    ) -> Message:
        """Update an existing message."""
        ...

    async def send_message(self, message_id: str) -> Message:
        """Send a draft message."""
        ...

    async def delete_message(self, message_id: str) -> None:
        """Delete a message."""
        ...

    async def mark_as_read(self, message_id: str, user_id: str) -> Message:
        """Mark a message as read by a user."""
        ...


class MessageDomainService(DomainService, MessageDomainServiceProtocol):
    """Service for managing messages."""

    def __init__(self, message_repository: MessageRepositoryProtocol):
        """Initialize the service with repositories."""
        self.message_repository = message_repository

    async def get_message(self, message_id: str) -> Message:
        """Get a message by ID."""
        message = await self.message_repository.get_by_id(message_id)
        if not message:
            raise EntityNotFoundError(f"Message with ID {message_id} not found")

        return message

    async def get_messages_for_user(
        self,
        user_id: str,
        only_unread: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Message]:
        """Get messages for a user."""
        return await self.message_repository.get_messages_for_user(
            user_id=user_id, only_unread=only_unread, page=page, page_size=page_size
        )

    async def get_draft_messages(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> list[Message]:
        """Get draft messages for a user."""
        return await self.message_repository.get_draft_messages_for_user(
            user_id=user_id, page=page, page_size=page_size
        )

    async def get_sent_messages(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> list[Message]:
        """Get sent messages for a user."""
        return await self.message_repository.get_sent_messages_for_user(
            user_id=user_id, page=page, page_size=page_size
        )

    async def get_message_thread(
        self, parent_message_id: str, page: int = 1, page_size: int = 20
    ) -> list[Message]:
        """Get a message thread."""
        return await self.message_repository.get_message_thread(
            parent_message_id=parent_message_id, page=page, page_size=page_size
        )

    async def create_message(
        self,
        subject: str,
        body: str,
        sender_id: str,
        recipient_ids: list[str],
        cc_ids: list[str] = None,
        bcc_ids: list[str] = None,
        flag: MessageImportance = MessageImportance.INFORMATION,
        is_draft: bool = True,
        parent_id: str | None = None,
        meta_record_ids: list[str] = None,
        group_id: str | None = None,
    ) -> Message:
        """Create a new message."""
        cc_ids = cc_ids or []
        bcc_ids = bcc_ids or []
        meta_record_ids = meta_record_ids or []

        # Create message entity
        message_id = str(uuid.uuid4())
        message = Message(
            id=message_id,
            subject=subject,
            body=body,
            flag=flag,
            is_draft=is_draft,
            sent_at=None if is_draft else datetime.now(UTC),
            parent_id=parent_id,
            users=[],
            meta_record_ids=meta_record_ids,
            group_id=group_id,
        )

        # Add sender
        message.add_user(user_id=sender_id, is_sender=True)

        # Add recipients
        for recipient_id in recipient_ids:
            message.add_user(user_id=recipient_id, is_addressee=True)

        # Add CC
        for cc_id in cc_ids:
            message.add_user(user_id=cc_id, is_copied_on=True)

        # Add BCC
        for bcc_id in bcc_ids:
            message.add_user(user_id=bcc_id, is_blind_copied_on=True)

        # Persist the message
        await self.message_repository.create(message)

        return message

    async def update_message(
        self,
        message_id: str,
        subject: str | None = None,
        body: str | None = None,
        recipient_ids: list[str] | None = None,
        cc_ids: list[str] | None = None,
        bcc_ids: list[str] | None = None,
        flag: Optional[MessageImportance] = None,
        meta_record_ids: list[str] | None = None,
    ) -> Message:
        """Update an existing message."""
        message = await self.get_message(message_id)

        # Only allow updating draft messages
        if not message.is_draft:
            raise ValueError("Cannot update a message that has already been sent")

        # Update basic properties
        if subject is not None:
            message.subject = subject

        if body is not None:
            message.body = body

        if flag is not None:
            message.flag = flag

        # Update meta records if provided
        if meta_record_ids is not None:
            message.meta_record_ids = meta_record_ids

        # Get the sender user_id
        sender_id = next(
            (user.user_id for user in message.users if user.is_sender), None
        )

        if sender_id is None:
            raise ValueError("Message has no sender")

        # If recipient lists are provided, update the recipients
        if any(ids is not None for ids in [recipient_ids, cc_ids, bcc_ids]):
            # Keep only the sender
            message.users = [user for user in message.users if user.is_sender]

            # Add new recipients
            if recipient_ids is not None:
                for recipient_id in recipient_ids:
                    message.add_user(user_id=recipient_id, is_addressee=True)

            # Add new CC
            if cc_ids is not None:
                for cc_id in cc_ids:
                    message.add_user(user_id=cc_id, is_copied_on=True)

            # Add new BCC
            if bcc_ids is not None:
                for bcc_id in bcc_ids:
                    message.add_user(user_id=bcc_id, is_blind_copied_on=True)

        # Persist the changes
        await self.message_repository.update(message)

        return message

    async def send_message(self, message_id: str) -> Message:
        """Send a draft message."""
        message = await self.get_message(message_id)

        if not message.is_draft:
            raise ValueError("Message is already sent")

        # Check if message has recipients
        has_recipients = any(not user.is_sender for user in message.users)

        if not has_recipients:
            raise ValueError("Cannot send a message without recipients")

        # Send the message
        message.send()

        # Persist the changes
        await self.message_repository.update(message)

        return message

    async def delete_message(self, message_id: str) -> None:
        """Delete a message."""
        await self.message_repository.delete(message_id)

    async def mark_as_read(self, message_id: str, user_id: str) -> Message:
        """Mark a message as read by a user."""
        message = await self.get_message(message_id)

        message.mark_as_read_by_user(user_id)

        # Persist the changes
        await self.message_repository.update(message)

        return message
