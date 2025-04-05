# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from uno.schema import UnoSchemaConfig
from uno.obj import UnoObj
from uno.auth.mixins import DefaultObjectMixin
from uno.meta.objects import MetaType
from uno.rprt.models import (
    ReportFieldConfigModel,
    ReportFieldModel,
    ReportTypeModel,
    ReportModel,
)


class ReportFieldConfig(UnoObj, DefaultObjectMixin):
    # Class variables
    model = ReportFieldConfigModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "report_field",
                "report_type",
                "parent_field",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "report_field_id",
                "report_type_id",
                "parent_field_id",
                "is_label_included",
                "field_format",
            ],
        ),
    }

    # Fields
    report_field_id: str
    report_field: "ReportField"
    report_type_id: str
    report_type: "ReportType"
    parent_field_id: Optional[str]
    parent_field: Optional["ReportField"]
    is_label_included: bool
    field_format: str


class ReportField(UnoObj, DefaultObjectMixin):
    # Class variables
    model = ReportFieldModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "field_meta_type",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "field_meta_type_id",
                "field_type",
                "name",
                "description",
            ],
        ),
    }

    # Fields
    field_meta_type_id: str
    field_meta_type: Optional[MetaType]
    field_type: str
    name: str
    description: Optional[str]


class ReportType(UnoObj, DefaultObjectMixin):
    # Class variables
    model = ReportTypeModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "report_fields",
                "report_field_configs",
                "report_type_configs",
                "report_type_field_configs",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
            ],
        ),
    }

    # Fields
    name: str
    description: Optional[str]
    report_fields: list[ReportField]
    report_field_configs: list[ReportFieldConfig]
    report_type_configs: list[ReportFieldConfig]
    report_type_field_configs: list[ReportFieldConfig]


class Report(UnoObj, DefaultObjectMixin):
    # Class variables
    model = ReportModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "report_type",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
                "report_type_id",
            ],
        ),
    }

    # Fields
    name: str
    description: Optional[str]
    report_type_id: str
    report_type: Optional[ReportType]
