# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
import decimal

from uno.schema import UnoSchemaConfig
from uno.model import UnoModel
from uno.mixins import ModelMixin
from uno.auth.mixins import RecordAuditMixin, GroupMixin, TenantMixin
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


class Attachment(UnoModel, ModelMixin, RecordAuditMixin, GroupMixin, TenantMixin):
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


class BooleanValue(UnoModel, ModelMixin, RecordAuditMixin, GroupMixin, TenantMixin):
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


class DateTimeValue(UnoModel, ModelMixin, RecordAuditMixin, GroupMixin, TenantMixin):
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


class DateValue(UnoModel, ModelMixin, RecordAuditMixin, GroupMixin, TenantMixin):
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


class DecimalValue(UnoModel, ModelMixin, RecordAuditMixin, GroupMixin, TenantMixin):
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


class IntegerValue(UnoModel, ModelMixin, RecordAuditMixin, GroupMixin, TenantMixin):
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


class TextValue(UnoModel, ModelMixin, RecordAuditMixin, GroupMixin, TenantMixin):
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


class TimeValue(UnoModel, ModelMixin, RecordAuditMixin, GroupMixin, TenantMixin):
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
