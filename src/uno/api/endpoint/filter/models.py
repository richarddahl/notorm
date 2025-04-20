"""
Filtering models for the unified endpoint framework.

This module defines the models used for filtering operations in the unified endpoint framework.
"""

from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field

T = TypeVar("T")


class FilterOperator(str, Enum):
    """Filter operators supported by the filtering system."""

    EQUAL = "eq"
    NOT_EQUAL = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"


class SortDirection(str, Enum):
    """Sort directions supported by the filtering system."""

    ASCENDING = "asc"
    DESCENDING = "desc"


class FilterField(BaseModel):
    """
    Filter field model.

    This model represents a field to filter on, with a name, operator, and value.
    """

    name: str = Field(..., description="Field name")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value")


class SortField(BaseModel):
    """
    Sort field model.

    This model represents a field to sort by, with a name and direction.
    """

    name: str = Field(..., description="Field name")
    direction: SortDirection = Field(
        SortDirection.ASCENDING, description="Sort direction"
    )


class FilterCondition(BaseModel):
    """
    Filter condition model.

    This model represents a condition for filtering, either a field condition or a group of conditions.
    """

    type: str = Field(..., description="Condition type (field or group)")
    field: Optional[FilterField] = Field(
        None, description="Field condition, required if type is 'field'"
    )
    group: Optional["FilterConditionGroup"] = Field(
        None, description="Group of conditions, required if type is 'group'"
    )

    class Config:
        """Pydantic configuration for the model."""

        arbitrary_types_allowed = True


class FilterConditionGroup(BaseModel):
    """
    Filter condition group model.

    This model represents a group of conditions with a logical operator.
    """

    operator: str = Field(..., description="Logical operator (and, or)")
    conditions: list[FilterCondition] = Field(..., description="List of conditions")


# Update forward reference for FilterCondition
FilterCondition.model_rebuild()


class FilterCriteria(BaseModel):
    """
    Filter criteria model.

    This model represents the criteria for filtering entities.
    """

    conditions: Union[FilterCondition, list[FilterCondition]] = Field(
        ..., description="Filter conditions"
    )
    sort: Optional[list[SortField]] = Field(None, description="Sort fields")
    limit: Optional[int] = Field(
        None, description="Maximum number of results to return"
    )
    offset: Optional[int] = Field(None, description="Offset for pagination")


class FilterRequest(BaseModel):
    """
    Filter request model.

    This model represents a request for filtering entities.
    """

    criteria: FilterCriteria = Field(..., description="Filter criteria")
    include_count: bool = Field(
        True, description="Whether to include the total count of matching entities"
    )


class FilterResult(BaseModel, Generic[T]):
    """
    Filter result model.

    This model represents the result of a filtering operation.
    """

    items: list[T] = Field(..., description="Filtered items")
    total: Optional[int] = Field(None, description="Total count of matching entities")
    limit: Optional[int] = Field(None, description="Maximum number of results returned")
    offset: Optional[int] = Field(None, description="Offset used for pagination")


class FilterResponse(BaseModel, Generic[T]):
    """
    Filter response model.

    This model represents the response to a filter request.
    """

    data: FilterResult[T] = Field(..., description="Filter result")
    meta: Optional[Dict[str, Any]] = Field(None, description="Response metadata")
