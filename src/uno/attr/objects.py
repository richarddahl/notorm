# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, List
from uno.schema import UnoSchemaConfig
from uno.obj import UnoObj
from uno.auth.mixins import DefaultObjectMixin
from uno.attr.models import AttributeModel, AttributeTypeModel
from uno.qry.objects import Query
from uno.meta.objects import MetaType


class Attribute(UnoObj[AttributeModel], DefaultObjectMixin):
    # Class variables
    model = AttributeModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "attribute_type",
                "group",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "attribute_type_id",
                "comment",
                "follow_up_required",
                "group_id",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    attribute_type_id: str = None
    attribute_type: Optional["AttributeType"] = None
    comment: Optional[str] = None
    follow_up_required: bool = False

    def __str__(self) -> str:
        return self.attribute_type.name


class AttributeType(UnoObj[AttributeTypeModel], DefaultObjectMixin):
    # Class variables
    model = AttributeTypeModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
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
                "display_with_applicable_objects",
                "initial_comment",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    id: Optional[str]
    name: str
    text: str
    parent_id: Optional[str]
    parent: Optional["AttributeType"]
    describes: List[MetaType]
    description_limiting_query_id: Optional[str]
    description_limiting_query: Optional[Query]
    value_type_limiting_query_id: Optional[str]
    value_type_limiting_query: Optional[Query]
    required: bool = False
    multiple_allowed: bool = False
    comment_required: bool = False
    display_with_applicable_objects: bool = False
    initial_comment: Optional[str] = None

    def __str__(self) -> str:
        return self.name
