# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional, List
from typing_extensions import Self
from pydantic import model_validator

from uno.obj import UnoObj
from uno.schema.schema import UnoSchemaConfig
from uno.enums import MessageImportance
from uno.msg.models import MessageUserModel, MessageModel
from uno.auth.objs import User
from uno.auth.mixins import DefaultObjectMixin


class Message(UnoObj[MessageModel], DefaultObjectMixin):
    # Class variables
    model = MessageModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "parent",
                "to",
                "cc",
                "bcc",
                "attachments",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "flag",
                "is_draft",
                "parent_id",
                "to",
                "cc",
                "bcc",
                "attachments",
                "subject",
                "body",
            ],
        ),
    }
    endpoints = ["List", "Create"]
    terminate_filters = True

    # Fields
    id: Optional[str]
    flag: Optional[MessageImportance]
    is_draft: Optional[bool] = True
    parent_id: Optional[str]
    parent: Optional["Message"]
    to: Optional[List[str]]
    cc: Optional[List[str]]
    bcc: Optional[List[str]]
    attachments: Optional[List[str]]
    subject: str
    body: str
    sent_at: Optional[datetime.datetime]
    status: str = "draft"  # draft, sent, failed

    def __str__(self) -> str:
        return self.subject

    @model_validator(mode="after")
    def validate_message(self) -> Self:
        # Validate status is one of the allowed statuses
        allowed_statuses = ["draft", "sent", "failed"]
        if self.status not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")

        return self


class MessageUser(UnoObj[MessageUserModel], DefaultObjectMixin):
    # Class variables
    model = MessageUserModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "message",
                "user",
            ],
        ),
    }
    endpoints = ["List", "Delete"]
    terminate_filters = True

    id: Optional[str]
    user: Optional[User]
    message: Optional[Message]
    user_id: Optional[str]
    message_id: Optional[str]
    is_sender: Optional[bool]
    is_addressee: Optional[bool]
    is_copied_on: Optional[bool]
    is_blind_copied_on: Optional[bool]
    was_read: Optional[bool]
    read_at: Optional[datetime.datetime]

    def __str__(self) -> str:
        return f"{self.user_id}: {self.message_id}"
