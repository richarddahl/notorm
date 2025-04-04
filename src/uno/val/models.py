# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
import decimal

from uno.schema import UnoSchemaConfig
from uno.model import UnoModel
from uno.auth.mixins import DefaultModelMixin
from uno.val.bases import (
    AttachmentBase,
    BooleanValueBase,
    DateTimeValueBase,
    DateValueBase,
    DecimalValueBase,
    IntegerValueBase,
    TextValueBase,
    TimeValueBase,
)


class Attachment(UnoModel, DefaultModelMixin):
    # Class variables
    base = AttachmentBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "file_path",
                "group_id",
            ],
        ),
    }

    # Fields
    name: str
    file_path: str


class BooleanValue(UnoModel, DefaultModelMixin):
    # Class variables
    base = BooleanValueBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "value",
                "group_id",
            ],
        ),
    }

    # Fields
    name: str
    value: bool


class DateTimeValue(UnoModel, DefaultModelMixin):
    # Class variables
    base = DateTimeValueBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "value",
                "group_id",
            ],
        ),
    }

    # Fields
    name: str
    value: datetime.datetime


class DateValue(UnoModel, DefaultModelMixin):
    # Class variables
    base = DateValueBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "value",
                "group_id",
            ],
        ),
    }

    # Fields
    name: str
    value: datetime.date


class DecimalValue(UnoModel, DefaultModelMixin):
    # Class variables
    base = DecimalValueBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "value",
                "group_id",
            ],
        ),
    }

    # Fields
    name: str
    value: decimal.Decimal


class IntegerValue(UnoModel, DefaultModelMixin):
    # Class variables
    base = IntegerValueBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "value",
                "group_id",
            ],
        ),
    }

    # Fields
    name: str
    value: int


class TextValue(UnoModel, DefaultModelMixin):
    # Class variables
    base = TextValueBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "value",
                "group_id",
            ],
        ),
    }

    # Fields
    name: str
    value: str


class TimeValue(UnoModel, DefaultModelMixin):
    # Class variables
    base = TimeValueBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "value",
                "group_id",
            ],
        ),
    }

    # Fields
    name: str
    value: datetime.time
