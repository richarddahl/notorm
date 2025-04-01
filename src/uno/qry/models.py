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
    ComparisonOperator,
    boolean_comparison_operators,
    numeric_comparison_operators,
    text_comparison_operators,
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
    source_meta_type_id: str
    source_meta_type: Optional[MetaType] = None
    destination_meta_type_id: str
    destination_meta_type: Optional[MetaType] = None
    filter_ids: list[str] = []
    path: str
    data_type: str
    comparison_operators: list[str]

    def __str__(self) -> str:
        return self.name


def create_query_paths(filter: UnoFilter) -> list[QueryPath]:
    query_paths: list = []
    # Create filter paths for the filter
    query_paths.append(
        QueryPath(
            source_meta_type_id=filter.source_node_label,
            path=filter.source_path,
            data_type=filter.data_type,
            comparison_operators=filter.comparison_operators,
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
                "query_path",
                "values",
                "queries",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "include",
                "match",
                "comparison_operator",
            ],
        ),
    }

    # Fields
    id: Optional[str] = None
    query_path_id: int
    query_path: Optional[QueryPath] = None
    include: Include = Include.INCLUDE
    match: Match = Match.AND
    comparison_operator: ComparisonOperator = ComparisonOperator.EQUAL
    values: Optional[list[MetaRecord]] = []
    queries: Optional[list["Query"]] = []

    @model_validator(mode="after")
    def model_validator(self) -> Self:
        self.comparison_operator = ComparisonOperator[self.comparison_operator]
        self.include = Include[self.include]
        self.match = Match[self.match]
        if not self.values and not self.queries:
            raise ValueError("Must have either values or queries")
        return self


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
