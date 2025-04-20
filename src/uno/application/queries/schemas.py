# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Schema managers for the Queries module.

This module provides schema managers for converting between domain entities and DTOs
for various query types. It serves as a bridge between the repository/domain layer
and the API layer.
"""

from typing import Dict, Type, Any, Optional, Union, List
from pydantic import BaseModel

from uno.queries.entities import Query, QueryPath, QueryValue
from uno.queries.dtos import (
    # QueryPath DTOs
    QueryPathCreateDto,
    QueryPathViewDto,
    QueryPathUpdateDto,
    QueryPathFilterParams,
    # QueryValue DTOs
    QueryValueCreateDto,
    QueryValueViewDto,
    QueryValueUpdateDto,
    QueryValueFilterParams,
    # Query DTOs
    QueryCreateDto,
    QueryViewDto,
    QueryUpdateDto,
    QueryFilterParams,
)


class QueryPathSchemaManager:
    """Schema manager for query path entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": QueryPathViewDto,
            "create_schema": QueryPathCreateDto,
            "update_schema": QueryPathUpdateDto,
            "filter_schema": QueryPathFilterParams,
        }

    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: QueryPath) -> QueryPathViewDto:
        """Convert a query path entity to a DTO."""
        return QueryPathViewDto(
            id=entity.id,
            source_meta_type_id=entity.source_meta_type_id,
            target_meta_type_id=entity.target_meta_type_id,
            cypher_path=entity.cypher_path,
            data_type=entity.data_type,
        )

    def dto_to_entity(
        self,
        dto: Union[QueryPathCreateDto, QueryPathUpdateDto],
        entity_id: str | None = None,
    ) -> QueryPath:
        """Convert a DTO to a query path entity."""
        data = dto.model_dump(exclude_unset=True)

        if entity_id:
            data["id"] = entity_id

        return QueryPath(**data)

    def update_entity_from_dto(
        self, entity: QueryPath, dto: QueryPathUpdateDto
    ) -> QueryPath:
        """Update a query path entity from a DTO."""
        data = dto.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(entity, key, value)

        return entity


class QueryValueSchemaManager:
    """Schema manager for query value entities."""

    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": QueryValueViewDto,
            "create_schema": QueryValueCreateDto,
            "update_schema": QueryValueUpdateDto,
            "filter_schema": QueryValueFilterParams,
        }

    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: QueryValue) -> QueryValueViewDto:
        """Convert a query value entity to a DTO."""
        return QueryValueViewDto(
            id=entity.id,
            query_path_id=entity.query_path_id,
            include=entity.include,
            match=entity.match,
            lookup=entity.lookup,
            values=entity.values,
        )

    def dto_to_entity(
        self,
        dto: Union[QueryValueCreateDto, QueryValueUpdateDto],
        entity_id: str | None = None,
    ) -> QueryValue:
        """Convert a DTO to a query value entity."""
        data = dto.model_dump(exclude_unset=True)

        if entity_id:
            data["id"] = entity_id

        return QueryValue(**data)

    def update_entity_from_dto(
        self, entity: QueryValue, dto: QueryValueUpdateDto
    ) -> QueryValue:
        """Update a query value entity from a DTO."""
        data = dto.model_dump(exclude_unset=True)

        for key, value in data.items():
            setattr(entity, key, value)

        return entity


class QuerySchemaManager:
    """Schema manager for query entities."""

    def __init__(
        self, query_value_schema_manager: Optional[QueryValueSchemaManager] = None
    ):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": QueryViewDto,
            "create_schema": QueryCreateDto,
            "update_schema": QueryUpdateDto,
            "filter_schema": QueryFilterParams,
        }
        self.query_value_schema_manager = (
            query_value_schema_manager or QueryValueSchemaManager()
        )

    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """Get a schema by name."""
        return self.schemas.get(schema_name)

    def entity_to_dto(self, entity: Query) -> QueryViewDto:
        """Convert a query entity to a DTO."""
        # Convert query values to DTOs
        query_value_dtos = []
        for query_value in entity.query_values:
            query_value_dto = self.query_value_schema_manager.entity_to_dto(query_value)
            query_value_dtos.append(query_value_dto)

        # Convert sub-queries to DTOs recursively
        sub_query_dtos = []
        for sub_query in entity.sub_queries:
            sub_query_dto = self.entity_to_dto(sub_query)
            sub_query_dtos.append(sub_query_dto)

        return QueryViewDto(
            id=entity.id,
            name=entity.name,
            query_meta_type_id=entity.query_meta_type_id,
            description=entity.description,
            include_values=entity.include_values,
            match_values=entity.match_values,
            include_queries=entity.include_queries,
            match_queries=entity.match_queries,
            query_values=query_value_dtos,
            sub_queries=sub_query_dtos,
        )

    def dto_to_entity(
        self, dto: Union[QueryCreateDto, QueryUpdateDto], entity_id: str | None = None
    ) -> Query:
        """Convert a DTO to a query entity."""
        data = dto.model_dump(exclude_unset=True)

        # Remove nested objects from data
        query_values_data = data.pop("query_values", [])
        sub_queries_data = data.pop("sub_queries", [])

        if entity_id:
            data["id"] = entity_id

        # Create the query entity
        query = Query(**data)

        return query

    def update_entity_from_dto(self, entity: Query, dto: QueryUpdateDto) -> Query:
        """Update a query entity from a DTO."""
        data = dto.model_dump(exclude_unset=True)

        # Remove nested objects from data
        data.pop("query_values", None)
        data.pop("sub_queries", None)

        for key, value in data.items():
            setattr(entity, key, value)

        return entity
