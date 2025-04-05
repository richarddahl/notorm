# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
import decimal

from uno.schema import UnoSchemaConfig
from uno.obj import UnoObj
from uno.auth.mixins import DefaultObjectMixin
from uno.val.models import (
    AttachmentModel,
    BooleanValueModel,
    DateTimeValueModel,
    DateValueModel,
    DecimalValueModel,
    IntegerValueModel,
    TextValueModel,
    TimeValueModel,
)


class Attachment(UnoObj, DefaultObjectMixin):
    # Class variables
    model = AttachmentModel
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


class BooleanValue(UnoObj, DefaultObjectMixin):
    # Class variables
    model = BooleanValueModel
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


class DateTimeValue(UnoObj, DefaultObjectMixin):
    # Class variables
    model = DateTimeValueModel
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


class DateValue(UnoObj, DefaultObjectMixin):
    # Class variables
    model = DateValueModel
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


class DecimalValue(UnoObj, DefaultObjectMixin):
    # Class variables
    model = DecimalValueModel
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


class IntegerValue(UnoObj, DefaultObjectMixin):
    # Class variables
    model = IntegerValueModel
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


class TextValue(UnoObj, DefaultObjectMixin):
    # Class variables
    model = TextValueModel
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


class TimeValue(UnoObj, DefaultObjectMixin):
    # Class variables
    model = TimeValueModel
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
