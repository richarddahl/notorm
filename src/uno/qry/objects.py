# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Optional
from typing_extensions import Self
from pydantic import model_validator

from uno.schema import UnoSchemaConfig
from uno.obj import UnoObj
from uno.mixins import ObjectMixin
from uno.auth.mixins import DefaultObjectMixin
from uno.qry.models import QueryPathModel, QueryValueModel, QueryModel
from uno.meta.objects import MetaRecord, MetaType
from uno.enums import (
    Include,
    Match,
)
from uno.config import settings


class QueryPath(UnoObj, ObjectMixin):
    # Class variables
    model = QueryPathModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "source_meta_type",
                "destination_meta_type",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "source_meta_type_id",
                "cypher_path",
                "target_meta_type_id",
                "data_type",
            ],
        ),
    }
    endpoints = ["List", "View"]

    # Fields
    source_meta_type_id: str
    source_meta_type: Optional[MetaType] = None
    target_meta_type_id: str
    destination_meta_type: Optional[MetaType] = None
    cypher_path: str
    data_type: str
    # lookups: list[str]

    def __str__(self) -> str:
        return self.cypher_path


class QueryValue(UnoObj, DefaultObjectMixin):
    # Class variables
    model = QueryValueModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "query_path",
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
    query_path_id: int
    query_path: Optional[QueryPath] = None
    include: Include = Include.INCLUDE
    match: Match = Match.AND
    lookup: str = "equal"
    values: Optional[list[MetaRecord]] = []
    queries: Optional[list["Query"]] = []

    @model_validator(mode="after")
    def model_validator(self) -> Self:
        self.lookup = self.lookup
        self.include = Include[self.include]
        self.match = Match[self.match]
        if not self.values and not self.queries:
            raise ValueError("Must have either values or queries")
        return self


class Query(UnoObj, DefaultObjectMixin):
    # Class variables
    model = QueryModel
    display_name_plural = "Queries"
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "query_meta_type",
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
