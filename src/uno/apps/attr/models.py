# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, List
from uno.db.enums import SQLOperation
from uno.model.schema import UnoSchemaConfig
from uno.model.model import UnoModel
from uno.model.mixins import GeneralModelMixin
from uno.apps.auth.mixins import RecordAuditMixin
from uno.apps.attr.bases import AttributeBase, AttributeTypeBase
from uno.apps.fltr.models import Query
from uno.apps.meta.models import MetaType
from uno.config import settings


class Attribute(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = AttributeBase
    table_name = "attribute"
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
                "group",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "tenant_id",
                "group_id",
            ],
        ),
    }
    filter_excludes = [
        "created_by_id",
        "modified_by_id",
        "deleted_by_id",
        "tenant_id",
        "default_group_id",
    ]
    terminate_filters = True
    endpoint_tags = ["Attributes"]

    # Fields
    attribute_type_id: Optional[str] = None
    attribute_type: Optional["AttributeType"] = None
    comment: Optional[str] = None
    followw_up_required: bool = False

    def __str__(self) -> str:
        return self.attribute_type.name


class AttributeType(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = AttributeTypeBase
    table_name = "attribute_type"
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
            ],
        ),
    }
    filter_excludes = [
        "created_by_id",
        "modified_by_id",
        "deleted_by_id",
        "tenant_id",
    ]
    terminate_filters = True
    endpoint_tags = ["Attributes"]

    # Fields
    id: Optional[str]
    name: str
    text: Optional[str]
    parent_id: Optional[str]
    parent: Optional["AttributeType"]
    describes: Optional[List[MetaType]]
    description_limiting_query_id: Optional[str]
    description_limiting_query: Optional[Query]
    value_type_limiting_query_id: Optional[str]
    value_type_limiting_query: Optional[Query]
    required: bool = False
    multiple_allowed: bool = False
    comment_required: bool = False
    initial_comment: Optional[str] = None

    def __str__(self) -> str:
        return self.name
