# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional

from uno.object import UnoObj
from uno.schema import UnoSchemaConfig
from uno.enums import MessageImportance
from uno.msg.models import MessageUserModel, MessageModel
from uno.auth.objects import User


class Message(UnoObj):
    # Class variables
    model = MessageModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
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

    # Fields
    id: Optional[str]
    flag: Optional[MessageImportance]
    is_draft: Optional[bool] = True
    parent_id: Optional[str]
    parent: Optional["Message"]
    to: Optional[list[str]]
    cc: Optional[list[str]]
    bcc: Optional[list[str]]
    attachments: Optional[list[str]]
    subject: str
    body: str
    sent_at: Optional[datetime.datetime]

    def __str__(self) -> str:
        return self.subject


class MessageUser(UnoObj):
    # Class variables
    model = MessageUserModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "message",
                "user",
            ],
        ),
    }
    endpoints = ["List", "Delete"]

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
