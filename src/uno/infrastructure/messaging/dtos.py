# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator, ConfigDict

from uno.enums import MessageImportance


class MessageUserBaseDto(BaseModel):
    """Base DTO for message user data."""

    user_id: str = Field(..., description="ID of the user")
    is_sender: bool = Field(False, description="Whether the user is the sender")
    is_addressee: bool = Field(
        False, description="Whether the user is an addressee (TO)"
    )
    is_copied_on: bool = Field(False, description="Whether the user is copied (CC)")
    is_blind_copied_on: bool = Field(
        False, description="Whether the user is blind copied (BCC)"
    )
    is_read: bool = Field(
        False, description="Whether the message has been read by this user"
    )
    read_at: Optional[datetime] = Field(None, description="When the message was read")


class MessageUserViewDto(MessageUserBaseDto):
    """DTO for viewing message user data."""

    id: str = Field(..., description="ID of the message user relationship")
    message_id: str = Field(..., description="ID of the message")


class MessageBaseDto(BaseModel):
    """Base DTO for message data."""

    subject: str = Field(..., description="Subject of the message", max_length=255)
    body: str = Field(..., description="Content of the message", max_length=255)
    flag: MessageImportance = Field(
        MessageImportance.INFORMATION, description="Importance flag of the message"
    )


class MessageCreateDto(MessageBaseDto):
    """DTO for creating a new message."""

    recipient_ids: list[str] = Field(..., description="List of recipient user IDs")
    cc_ids: list[str] | None = Field([], description="List of CC user IDs")
    bcc_ids: list[str] | None = Field([], description="List of BCC user IDs")
    is_draft: bool = Field(True, description="Whether the message is a draft")
    parent_id: str | None = Field(
        None, description="ID of the parent message if this is a reply"
    )
    meta_record_ids: list[str] | None = Field(
        [], description="List of meta record IDs associated with this message"
    )
    group_id: str | None = Field(
        None, description="ID of the group this message belongs to"
    )


class MessageUpdateDto(BaseModel):
    """DTO for updating an existing message."""

    subject: str | None = Field(
        None, description="Subject of the message", max_length=255
    )
    body: str | None = Field(None, description="Content of the message", max_length=255)
    flag: Optional[MessageImportance] = Field(
        None, description="Importance flag of the message"
    )
    recipient_ids: list[str] | None = Field(
        None, description="List of recipient user IDs"
    )
    cc_ids: list[str] | None = Field(None, description="List of CC user IDs")
    bcc_ids: list[str] | None = Field(None, description="List of BCC user IDs")
    meta_record_ids: list[str] | None = Field(
        None, description="List of meta record IDs associated with this message"
    )

    model_config = ConfigDict(validate_assignment=True)


class MessageViewDto(MessageBaseDto):
    """DTO for viewing a message."""

    id: str = Field(..., description="ID of the message")
    is_draft: bool = Field(..., description="Whether the message is a draft")
    sent_at: Optional[datetime] = Field(None, description="When the message was sent")
    parent_id: str | None = Field(
        None, description="ID of the parent message if this is a reply"
    )
    users: list[MessageUserViewDto] = Field(
        [], description="List of users associated with this message"
    )
    meta_record_ids: list[str] = Field(
        [], description="List of meta record IDs associated with this message"
    )
    group_id: str | None = Field(
        None, description="ID of the group this message belongs to"
    )

    @property
    def sender(self) -> Optional[MessageUserViewDto]:
        """Get the sender of the message."""
        for user in self.users:
            if user.is_sender:
                return user
        return None

    @property
    def recipients(self) -> list[MessageUserViewDto]:
        """Get the recipients of the message."""
        return [user for user in self.users if user.is_addressee and not user.is_sender]

    @property
    def cc(self) -> list[MessageUserViewDto]:
        """Get the CC recipients of the message."""
        return [user for user in self.users if user.is_copied_on]

    @property
    def bcc(self) -> list[MessageUserViewDto]:
        """Get the BCC recipients of the message."""
        return [user for user in self.users if user.is_blind_copied_on]


class MessageFilterParams(BaseModel):
    """Parameters for filtering messages."""

    only_unread: bool = Field(
        False, description="Filter to only include unread messages"
    )
    page: int = Field(1, description="Page number", ge=1)
    page_size: int = Field(20, description="Number of items per page", ge=1, le=100)


class MessageListDto(BaseModel):
    """DTO for a list of messages with pagination information."""

    items: list[MessageViewDto] = Field(..., description="List of messages")
    total: int = Field(..., description="Total number of messages matching the filter")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")

    @model_validator(mode="after")
    @classmethod
    def validate_items(cls, v, values):
        """Validate that the items list is not empty if total is greater than 0."""
        if values.get("total", 0) > 0 and not v:
            raise ValueError("Items list cannot be empty if total is greater than 0.")
        return v

    @model_validator(mode="after")
    @classmethod
    def calculate_pages(cls, v, values):
        """Calculate the total number of pages based on total items and page size."""
        if "total" in values and "page_size" in values:
            return (values["total"] + values["page_size"] - 1) // values["page_size"]
        return v
