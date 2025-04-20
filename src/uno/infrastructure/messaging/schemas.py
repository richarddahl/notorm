# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import List, Optional, Dict, Any, Union, Type

from uno.messaging.entities import Message, MessageUser
from uno.messaging.dtos import (
    MessageUserViewDto,
    MessageViewDto,
    MessageListDto,
    MessageCreateDto,
    MessageUpdateDto,
    MessageFilterParams,
)


class MessageSchemaManager:
    """Schema manager for message entities."""

    def entity_to_dto(self, entity: Message) -> MessageViewDto:
        """Convert a message entity to a DTO."""
        users = [self._message_user_to_dto(user) for user in entity.users]

        return MessageViewDto(
            id=entity.id,
            subject=entity.subject,
            body=entity.body,
            flag=entity.flag,
            is_draft=entity.is_draft,
            sent_at=entity.sent_at,
            parent_id=entity.parent_id,
            users=users,
            meta_record_ids=entity.meta_record_ids,
            group_id=entity.group_id,
        )

    def entities_to_list_dto(
        self, entities: list[Message], total: int, page: int, page_size: int
    ) -> MessageListDto:
        """Convert a list of message entities to a list DTO with pagination."""
        items = [self.entity_to_dto(entity) for entity in entities]

        return MessageListDto(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if page_size > 0 else 0,
        )

    def create_dto_to_params(
        self, dto: MessageCreateDto, sender_id: str
    ) -> Dict[str, Any]:
        """Convert a create DTO to parameters for the domain service."""
        return {
            "subject": dto.subject,
            "body": dto.body,
            "sender_id": sender_id,
            "recipient_ids": dto.recipient_ids,
            "cc_ids": dto.cc_ids,
            "bcc_ids": dto.bcc_ids,
            "flag": dto.flag,
            "is_draft": dto.is_draft,
            "parent_id": dto.parent_id,
            "meta_record_ids": dto.meta_record_ids,
            "group_id": dto.group_id,
        }

    def update_dto_to_params(self, dto: MessageUpdateDto) -> Dict[str, Any]:
        """Convert an update DTO to parameters for the domain service."""
        params = {}

        if dto.subject is not None:
            params["subject"] = dto.subject

        if dto.body is not None:
            params["body"] = dto.body

        if dto.flag is not None:
            params["flag"] = dto.flag

        if dto.recipient_ids is not None:
            params["recipient_ids"] = dto.recipient_ids

        if dto.cc_ids is not None:
            params["cc_ids"] = dto.cc_ids

        if dto.bcc_ids is not None:
            params["bcc_ids"] = dto.bcc_ids

        if dto.meta_record_ids is not None:
            params["meta_record_ids"] = dto.meta_record_ids

        return params

    def _message_user_to_dto(self, entity: MessageUser) -> MessageUserViewDto:
        """Convert a message user entity to a DTO."""
        return MessageUserViewDto(
            id=entity.id,
            message_id=entity.message_id,
            user_id=entity.user_id,
            is_sender=entity.is_sender,
            is_addressee=entity.is_addressee,
            is_copied_on=entity.is_copied_on,
            is_blind_copied_on=entity.is_blind_copied_on,
            is_read=entity.is_read,
            read_at=entity.read_at,
        )
