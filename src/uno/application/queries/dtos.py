# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Data Transfer Objects (DTOs) for the Queries module.

This module provides Pydantic models for the Queries API, handling serialization
and validation for HTTP requests and responses related to queries, query paths,
and query values.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator
from enum import Enum


class IncludeEnum(str, Enum):
    """Enum for include/exclude options."""
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"


class MatchEnum(str, Enum):
    """Enum for match options."""
    AND = "AND"
    OR = "OR"


class LookupTypeEnum(str, Enum):
    """Enum for lookup types."""
    EQUAL = "eq"
    NOT_EQUAL = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


# QueryPath DTOs

class QueryPathBaseDto(BaseModel):
    """Base DTO for query paths."""
    source_meta_type_id: str = Field(..., description="ID of the source meta type")
    target_meta_type_id: str = Field(..., description="ID of the target meta type")
    cypher_path: str = Field(..., description="The Cypher path expression")
    data_type: str = Field(..., description="The data type of the path result")


class QueryPathCreateDto(QueryPathBaseDto):
    """DTO for creating query paths."""
    model_config = {
        "json_schema_extra": {
            "example": {
                "source_meta_type_id": "product",
                "target_meta_type_id": "category",
                "cypher_path": "()-[:HAS_CATEGORY]->()",
                "data_type": "string"
            }
        }
    }


class QueryPathUpdateDto(BaseModel):
    """DTO for updating query paths."""
    source_meta_type_id: Optional[str] = Field(None, description="ID of the source meta type")
    target_meta_type_id: Optional[str] = Field(None, description="ID of the target meta type")
    cypher_path: Optional[str] = Field(None, description="The Cypher path expression")
    data_type: Optional[str] = Field(None, description="The data type of the path result")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "cypher_path": "()-[:UPDATED_CATEGORY]->()",
                "data_type": "string"
            }
        }
    }


class QueryPathViewDto(QueryPathBaseDto):
    """DTO for viewing query paths."""
    id: str = Field(..., description="Unique identifier for the query path")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "abc123",
                "source_meta_type_id": "product",
                "target_meta_type_id": "category",
                "cypher_path": "()-[:HAS_CATEGORY]->()",
                "data_type": "string"
            }
        }
    }


class QueryPathFilterParams(BaseModel):
    """Filter parameters for query paths."""
    source_meta_type_id: Optional[str] = Field(None, description="Filter by source meta type ID")
    target_meta_type_id: Optional[str] = Field(None, description="Filter by target meta type ID")
    data_type: Optional[str] = Field(None, description="Filter by data type")


# QueryValue DTOs

class QueryValueBaseDto(BaseModel):
    """Base DTO for query values."""
    query_path_id: str = Field(..., description="ID of the query path")
    include: IncludeEnum = Field(IncludeEnum.INCLUDE, description="Whether to include or exclude")
    match: MatchEnum = Field(MatchEnum.AND, description="AND/OR match type")
    lookup: str = Field("equal", description="Lookup operation")
    values: List[Any] = Field(default_factory=list, description="Values for filtering")


class QueryValueCreateDto(QueryValueBaseDto):
    """DTO for creating query values."""
    model_config = {
        "json_schema_extra": {
            "example": {
                "query_path_id": "path123",
                "include": "INCLUDE",
                "match": "AND",
                "lookup": "equal",
                "values": ["red", "blue", "green"]
            }
        }
    }


class QueryValueUpdateDto(BaseModel):
    """DTO for updating query values."""
    query_path_id: Optional[str] = Field(None, description="ID of the query path")
    include: Optional[IncludeEnum] = Field(None, description="Whether to include or exclude")
    match: Optional[MatchEnum] = Field(None, description="AND/OR match type")
    lookup: Optional[str] = Field(None, description="Lookup operation")
    values: Optional[List[Any]] = Field(None, description="Values for filtering")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "lookup": "contains",
                "values": ["yellow", "purple"]
            }
        }
    }


class QueryValueViewDto(QueryValueBaseDto):
    """DTO for viewing query values."""
    id: str = Field(..., description="Unique identifier for the query value")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "value123",
                "query_path_id": "path123",
                "include": "INCLUDE",
                "match": "AND",
                "lookup": "equal",
                "values": ["red", "blue", "green"]
            }
        }
    }


class QueryValueFilterParams(BaseModel):
    """Filter parameters for query values."""
    query_path_id: Optional[str] = Field(None, description="Filter by query path ID")
    include: Optional[IncludeEnum] = Field(None, description="Filter by include/exclude")
    match: Optional[MatchEnum] = Field(None, description="Filter by AND/OR match type")
    lookup: Optional[str] = Field(None, description="Filter by lookup operation")


# Query DTOs

class QueryBaseDto(BaseModel):
    """Base DTO for queries."""
    name: str = Field(..., description="Name of the query")
    query_meta_type_id: str = Field(..., description="ID of the query meta type")
    description: Optional[str] = Field(None, description="Description of the query")
    include_values: IncludeEnum = Field(IncludeEnum.INCLUDE, description="Whether to include or exclude values")
    match_values: MatchEnum = Field(MatchEnum.AND, description="AND/OR match type for values")
    include_queries: IncludeEnum = Field(IncludeEnum.INCLUDE, description="Whether to include or exclude queries")
    match_queries: MatchEnum = Field(MatchEnum.AND, description="AND/OR match type for queries")


class QueryCreateDto(QueryBaseDto):
    """DTO for creating queries."""
    query_values: List[Dict[str, Any]] = Field(default_factory=list, description="Values for the query")
    sub_queries: List[str] = Field(default_factory=list, description="IDs of sub-queries")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Red Products",
                "query_meta_type_id": "product",
                "description": "Query for red products",
                "include_values": "INCLUDE",
                "match_values": "AND",
                "include_queries": "INCLUDE",
                "match_queries": "AND",
                "query_values": [
                    {
                        "query_path_id": "path123",
                        "include": "INCLUDE",
                        "match": "AND", 
                        "lookup": "equal",
                        "values": ["red"]
                    }
                ],
                "sub_queries": []
            }
        }
    }


class QueryUpdateDto(BaseModel):
    """DTO for updating queries."""
    name: Optional[str] = Field(None, description="Name of the query")
    query_meta_type_id: Optional[str] = Field(None, description="ID of the query meta type")
    description: Optional[str] = Field(None, description="Description of the query")
    include_values: Optional[IncludeEnum] = Field(None, description="Whether to include or exclude values")
    match_values: Optional[MatchEnum] = Field(None, description="AND/OR match type for values")
    include_queries: Optional[IncludeEnum] = Field(None, description="Whether to include or exclude queries")
    match_queries: Optional[MatchEnum] = Field(None, description="AND/OR match type for queries")
    query_values: Optional[List[Dict[str, Any]]] = Field(None, description="Values for the query")
    sub_queries: Optional[List[str]] = Field(None, description="IDs of sub-queries")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Updated Red Products",
                "description": "Updated query for red products",
                "query_values": [
                    {
                        "query_path_id": "path123",
                        "lookup": "contains",
                        "values": ["dark red", "light red"]
                    }
                ]
            }
        }
    }


class QueryViewDto(QueryBaseDto):
    """DTO for viewing queries."""
    id: str = Field(..., description="Unique identifier for the query")
    query_values: List[QueryValueViewDto] = Field(default_factory=list, description="Values for the query")
    sub_queries: List["QueryViewDto"] = Field(default_factory=list, description="Sub-queries")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "query123",
                "name": "Red Products",
                "query_meta_type_id": "product",
                "description": "Query for red products",
                "include_values": "INCLUDE",
                "match_values": "AND",
                "include_queries": "INCLUDE",
                "match_queries": "AND",
                "query_values": [
                    {
                        "id": "value123",
                        "query_path_id": "path123",
                        "include": "INCLUDE",
                        "match": "AND",
                        "lookup": "equal",
                        "values": ["red"]
                    }
                ],
                "sub_queries": []
            }
        }
    }


class QueryFilterParams(BaseModel):
    """Filter parameters for queries."""
    name: Optional[str] = Field(None, description="Filter by name")
    query_meta_type_id: Optional[str] = Field(None, description="Filter by query meta type ID")


# Execution DTOs

class QueryExecuteDto(BaseModel):
    """DTO for executing queries."""
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters to apply")
    options: Optional[Dict[str, Any]] = Field(None, description="Options for query execution")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "filters": {
                    "price": {"lookup": "gt", "val": 100}
                },
                "options": {
                    "limit": 20,
                    "offset": 0,
                    "order_by": ["name"]
                }
            }
        }
    }


class QueryExecuteResultDto(BaseModel):
    """DTO for query execution results."""
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    count: int = Field(..., description="Total count of results")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "results": [
                    {"id": "prod1", "name": "Red Chair", "price": 199.99},
                    {"id": "prod2", "name": "Red Table", "price": 299.99}
                ],
                "count": 2
            }
        }
    }


# Support recursive references for QueryViewDto
QueryViewDto.model_rebuild()