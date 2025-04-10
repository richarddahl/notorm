# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, List
from typing_extensions import Self
from pydantic import model_validator

from uno.schema.schema import UnoSchemaConfig
from uno.obj import UnoObj
from uno.authorization.mixins import DefaultObjectMixin
from uno.meta.objs import MetaType
from uno.reports.models import (
    ReportFieldConfigModel,
    ReportFieldModel,
    ReportTypeModel,
    ReportModel,
)


class ReportFieldConfig(UnoObj[ReportFieldConfigModel], DefaultObjectMixin):
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
    parent_field_id: Optional[str] = None
    parent_field: Optional["ReportField"] = None
    is_label_included: bool
    field_format: str

    def __str__(self) -> str:
        return f"{self.report_field.name} config"


class ReportField(UnoObj[ReportFieldModel], DefaultObjectMixin):
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
    field_meta_type: Optional[MetaType] = None
    field_type: str
    name: str
    description: Optional[str] = None

    def __str__(self) -> str:
        return self.name

    @model_validator(mode="after")
    def validate_field(self) -> Self:
        # Validate field_type is one of the allowed types
        allowed_types = ["string", "number", "boolean", "date", "object", "array"]
        if self.field_type not in allowed_types:
            raise ValueError(f"Field type must be one of: {', '.join(allowed_types)}")

        return self


class ReportType(UnoObj[ReportTypeModel], DefaultObjectMixin):
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
    description: Optional[str] = None
    report_fields: List[ReportField] = []
    report_field_configs: List[ReportFieldConfig] = []
    report_type_configs: List[ReportFieldConfig] = []
    report_type_field_configs: List[ReportFieldConfig] = []

    def __str__(self) -> str:
        return self.name


class Report(UnoObj[ReportModel], DefaultObjectMixin):
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
    description: Optional[str] = None
    report_type_id: str
    report_type: Optional[ReportType] = None

    def __str__(self) -> str:
        return self.name
