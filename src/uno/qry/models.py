# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

import datetime
import decimal
from typing import Optional
from typing_extensions import Self
from pydantic import BaseModel, model_validator
from sqlalchemy import Table, Column

from uno.schema import UnoSchemaConfig
from uno.model import UnoModel
from uno.mixins import ModelMixin
from uno.auth.mixins import RecordAuditMixin
from uno.qry.bases import QueryPathBase, QueryValueBase, QueryBase
from uno.filter import UnoFilter
from uno.meta.models import MetaRecord, MetaType
from uno.utilities import (
    snake_to_title,
    snake_to_camel,
    snake_to_caps_snake,
)
from uno.enums import (
    Include,
    Match,
    Lookup,
    object_lookups,
    numeric_lookups,
    text_lookups,
)
from uno.config import settings


class QueryPath(UnoModel, ModelMixin):
    # Class variables
    base = QueryPathBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "source_meta_type",
                "destination_meta_type",
                "filter_ids",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "source_meta_type_id",
                "destination_meta_type_id",
                "filter_ids",
            ],
        ),
    }

    # Fields
    source_meta_type_id: Optional[str] = None
    source_meta_type: Optional[MetaType] = None
    destination_meta_type_id: Optional[str] = None
    destination_meta_type: Optional[MetaType] = None
    filter_ids: Optional[list[str]] = []
    path: Optional[str] = None
    data_type: Optional[str] = None
    lookups: Optional[list[str]] = None

    def __str__(self) -> str:
        return self.name


def create_query_paths(filter: UnoFilter) -> list[QueryPath]:
    query_paths: list = []
    # Create filter paths for the filter
    query_paths.append(
        QueryPath(
            source_meta_type_id=filter.source_node,
            path=filter.source_path,
            data_type=filter.data_type,
            lookups=filter.lookups,
        )
    )


class QueryValue(UnoModel, ModelMixin, RecordAuditMixin):
    # Class variables
    base = QueryValueBase
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                # "query_path",
                "values",
                "queries",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "include",
                "match",
                "lookup",
            ],
        ),
    }

    # Fields
    id: Optional[str] = None
    query_path_id: Optional[int] = None
    # query_path: Optional[QueryPath] = None
    include: Optional[Include] = Include.INCLUDE
    match: Optional[Match] = Match.AND
    lookup: Optional[Lookup] = Lookup.EQUAL
    values: Optional[list[MetaRecord]] = []
    queries: Optional[list["Query"]] = []


class Query(UnoModel, ModelMixin, RecordAuditMixin):
    # Class variables
    base = QueryBase
    display_name_plural = "Queries"
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
    terminate_filters = True

    # Fields
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    query_meta_type_id: Optional[str] = None
    query_meta_type: Optional[MetaType] = None
    include_values: Optional[Include] = Include.INCLUDE
    match_values: Optional[Match] = Match.AND
    include_queries: Optional[Include] = Include.INCLUDE
    match_queries: Optional[Match] = Match.AND

    def __str__(self) -> str:
        return self.name
