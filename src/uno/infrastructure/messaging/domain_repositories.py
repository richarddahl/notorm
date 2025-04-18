# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import List, Optional, Protocol, Dict, Any, runtime_checkable
from uuid import UUID

from uno.core.base.respository import Repository
from uno.messaging.entities import Message, MessageUser
from uno.messaging.models import MessageModel, MessageUserModel
from uno.enums import MessageImportance
from uno.core.errors import EntityNotFoundError
from uno.core.base.respository import Repository
from uno.database.session import UnoSession, UnoAsyncSession


@runtime_checkable
class MessageRepositoryProtocol(Protocol):
    """Protocol for message repository."""

    async def get_by_id(self, message_id: str) -> Optional[Message]:
        """Get a message by its ID."""
        ...

    async def get_messages_for_user(
        self,
        user_id: str,
        only_unread: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Message]:
        """Get messages for a specific user."""
        ...

    async def get_message_thread(
        self, parent_message_id: str, page: int = 1, page_size: int = 20
    ) -> List[Message]:
        """Get all messages in a thread."""
        ...

    async def create(self, message: Message) -> Message:
        """Create a new message."""
        ...

    async def update(self, message: Message) -> Message:
        """Update an existing message."""
        ...

    async def delete(self, message_id: str) -> None:
        """Delete a message."""
        ...

    async def get_draft_messages_for_user(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> List[Message]:
        """Get draft messages for a specific user."""
        ...

    async def get_sent_messages_for_user(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> List[Message]:
        """Get sent messages for a specific user."""
        ...


class MessageRepository(Repository, MessageRepositoryProtocol):
    """Repository for managing messages."""

    def __init__(self, session: UnoSession):
        """Initialize the repository with a database session."""
        self.session = session

    async def get_by_id(self, message_id: str) -> Optional[Message]:
        """Get a message by its ID."""
        message_model = (
            await self.session.query(MessageModel)
            .filter(MessageModel.id == message_id)
            .first()
        )

        if not message_model:
            return None

        return self._model_to_entity(message_model)

    async def get_messages_for_user(
        self,
        user_id: str,
        only_unread: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Message]:
        """Get messages for a specific user."""
        query = (
            self.session.query(MessageModel)
            .join(MessageUserModel, MessageUserModel.message_id == MessageModel.id)
            .filter(MessageUserModel.user_id == user_id, MessageModel.is_draft == False)
        )

        if only_unread:
            query = query.filter(MessageUserModel.is_read == False)

        offset = (page - 1) * page_size
        message_models = (
            await query.order_by(MessageModel.sent_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [self._model_to_entity(model) for model in message_models]

    async def get_message_thread(
        self, parent_message_id: str, page: int = 1, page_size: int = 20
    ) -> List[Message]:
        """Get all messages in a thread."""
        # First get the parent message
        parent_message = await self.get_by_id(parent_message_id)
        if not parent_message:
            raise EntityNotFoundError(f"Message with ID {parent_message_id} not found")

        # Get all child messages
        offset = (page - 1) * page_size
        child_models = (
            await self.session.query(MessageModel)
            .filter(MessageModel.parent_id == parent_message_id)
            .order_by(MessageModel.sent_at.asc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        messages = [parent_message]
        messages.extend([self._model_to_entity(model) for model in child_models])

        return messages

    async def create(self, message: Message) -> Message:
        """Create a new message."""
        message_model = MessageModel(
            id=message.id,
            subject=message.subject,
            body=message.body,
            flag=message.flag,
            is_draft=message.is_draft,
            sent_at=message.sent_at,
            parent_id=message.parent_id,
            group_id=message.group_id,
        )

        await self.session.add(message_model)
        await self.session.flush()

        # Create message user associations
        for user in message.users:
            user_model = MessageUserModel(
                id=user.id,
                message_id=user.message_id,
                user_id=user.user_id,
                is_sender=user.is_sender,
                is_addressee=user.is_addressee,
                is_copied_on=user.is_copied_on,
                is_blind_copied_on=user.is_blind_copied_on,
                is_read=user.is_read,
                read_at=user.read_at,
            )
            await self.session.add(user_model)

        # Associate meta records if specified
        if message.meta_record_ids:
            for meta_record_id in message.meta_record_ids:
                await self.session.execute(
                    f"INSERT INTO message__meta_record (message_id, meta_record_id) "
                    f"VALUES ('{message.id}', '{meta_record_id}')"
                )

        return message

    async def update(self, message: Message) -> Message:
        """Update an existing message."""
        message_model = (
            await self.session.query(MessageModel)
            .filter(MessageModel.id == message.id)
            .first()
        )

        if not message_model:
            raise EntityNotFoundError(f"Message with ID {message.id} not found")

        # Update message model properties
        message_model.subject = message.subject
        message_model.body = message.body
        message_model.flag = message.flag
        message_model.is_draft = message.is_draft
        message_model.sent_at = message.sent_at
        message_model.parent_id = message.parent_id
        message_model.group_id = message.group_id

        await self.session.flush()

        # Update message user associations
        # First, get all existing users
        existing_users = (
            await self.session.query(MessageUserModel)
            .filter(MessageUserModel.message_id == message.id)
            .all()
        )

        existing_user_ids = {user.user_id for user in existing_users}
        updated_user_ids = {user.user_id for user in message.users}

        # Add new users
        for user in message.users:
            if user.user_id not in existing_user_ids:
                user_model = MessageUserModel(
                    id=user.id,
                    message_id=user.message_id,
                    user_id=user.user_id,
                    is_sender=user.is_sender,
                    is_addressee=user.is_addressee,
                    is_copied_on=user.is_copied_on,
                    is_blind_copied_on=user.is_blind_copied_on,
                    is_read=user.is_read,
                    read_at=user.read_at,
                )
                await self.session.add(user_model)
            else:
                # Update existing user
                user_model = next(
                    (u for u in existing_users if u.user_id == user.user_id), None
                )
                if user_model:
                    user_model.is_sender = user.is_sender
                    user_model.is_addressee = user.is_addressee
                    user_model.is_copied_on = user.is_copied_on
                    user_model.is_blind_copied_on = user.is_blind_copied_on
                    user_model.is_read = user.is_read
                    user_model.read_at = user.read_at

        # Remove users that are no longer associated
        for user_id in existing_user_ids - updated_user_ids:
            await self.session.query(MessageUserModel).filter(
                MessageUserModel.message_id == message.id,
                MessageUserModel.user_id == user_id,
            ).delete()

        # Update meta record associations
        await self.session.execute(
            f"DELETE FROM message__meta_record WHERE message_id = '{message.id}'"
        )

        for meta_record_id in message.meta_record_ids:
            await self.session.execute(
                f"INSERT INTO message__meta_record (message_id, meta_record_id) "
                f"VALUES ('{message.id}', '{meta_record_id}')"
            )

        return message

    async def delete(self, message_id: str) -> None:
        """Delete a message."""
        message_model = (
            await self.session.query(MessageModel)
            .filter(MessageModel.id == message_id)
            .first()
        )

        if not message_model:
            raise EntityNotFoundError(f"Message with ID {message_id} not found")

        await self.session.delete(message_model)

    async def get_draft_messages_for_user(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> List[Message]:
        """Get draft messages for a specific user."""
        offset = (page - 1) * page_size
        message_models = (
            await self.session.query(MessageModel)
            .join(MessageUserModel, MessageUserModel.message_id == MessageModel.id)
            .filter(
                MessageUserModel.user_id == user_id,
                MessageUserModel.is_sender == True,
                MessageModel.is_draft == True,
            )
            .order_by(MessageModel.sent_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [self._model_to_entity(model) for model in message_models]

    async def get_sent_messages_for_user(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> List[Message]:
        """Get sent messages for a specific user."""
        offset = (page - 1) * page_size
        message_models = (
            await self.session.query(MessageModel)
            .join(MessageUserModel, MessageUserModel.message_id == MessageModel.id)
            .filter(
                MessageUserModel.user_id == user_id,
                MessageUserModel.is_sender == True,
                MessageModel.is_draft == False,
            )
            .order_by(MessageModel.sent_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [self._model_to_entity(model) for model in message_models]

    def _model_to_entity(self, model: MessageModel) -> Message:
        """Convert a MessageModel to a Message entity."""
        users = []
        for user_model in model.users:
            user = MessageUser(
                id=user_model.id,
                message_id=user_model.message_id,
                user_id=user_model.user_id,
                is_sender=user_model.is_sender,
                is_addressee=user_model.is_addressee,
                is_copied_on=user_model.is_copied_on,
                is_blind_copied_on=user_model.is_blind_copied_on,
                is_read=user_model.is_read,
                read_at=user_model.read_at,
            )
            users.append(user)

        meta_record_ids = (
            [mr.id for mr in model.meta_records]
            if hasattr(model, "meta_records")
            else []
        )

        return Message(
            id=model.id,
            subject=model.subject,
            body=model.body,
            flag=model.flag,
            is_draft=model.is_draft,
            sent_at=model.sent_at,
            parent_id=model.parent_id,
            users=users,
            meta_record_ids=meta_record_ids,
            group_id=model.group_id if hasattr(model, "group_id") else None,
        )
