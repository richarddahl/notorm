# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, List
from uno.model.schema import UnoSchemaConfig
from uno.model.model import UnoModel
from uno.model.mixins import GeneralModelMixin
from uno.pkgs.auth.mixins import RecordAuditMixin
from uno.pkgs.attr.bases import AttributeBase, AttributeTypeBase
from uno.pkgs.fltr.models import Query
from uno.pkgs.meta.models import MetaType


class Attribute(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = AttributeBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "attribute_type",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "attribute_type_id",
                "comment",
                "follow_up_required",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    attribute_type_id: Optional[str] = None
    attribute_type: Optional["AttributeType"] = None
    comment: Optional[str] = None
    follow_up_required: bool = False

    def __str__(self) -> str:
        return self.attribute_type.name


class AttributeType(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    base = AttributeTypeBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "parent",
                "describes",
                "description_limiting_query",
                "value_type_limiting_query",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "text",
                "parent_id",
                "description_limiting_query_id",
                "value_type_limiting_query_id",
                "required",
                "multiple_allowed",
                "comment_required",
                "initial_comment",
            ],
        ),
    }
    terminate_filters = True

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
