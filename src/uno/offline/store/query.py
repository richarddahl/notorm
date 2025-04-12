"""Query functionality for the offline store.

This module provides classes and functions for querying data in the offline store.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Union, Callable, Generic, TypeVar

T = TypeVar('T')


class FilterOperator(Enum):
    """Operators for query filters."""
    
    # Comparison operators
    EQUALS = auto()
    NOT_EQUALS = auto()
    GREATER_THAN = auto()
    GREATER_THAN_OR_EQUAL = auto()
    LESS_THAN = auto()
    LESS_THAN_OR_EQUAL = auto()
    
    # Membership operators
    IN = auto()
    NOT_IN = auto()
    
    # String operators
    CONTAINS = auto()
    STARTS_WITH = auto()
    ENDS_WITH = auto()
    
    # Logical operators
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Existence operators
    EXISTS = auto()
    NOT_EXISTS = auto()
    
    # Array operators
    ARRAY_CONTAINS = auto()
    ARRAY_CONTAINS_ANY = auto()
    ARRAY_CONTAINS_ALL = auto()
    
    @staticmethod
    def from_string(op_str: str) -> 'FilterOperator':
        """Convert a string operator to a FilterOperator.
        
        Args:
            op_str: The string representation of the operator.
            
        Returns:
            The corresponding FilterOperator.
            
        Raises:
            ValueError: If the operator string is not recognized.
        """
        operator_map = {
            "==": FilterOperator.EQUALS,
            "=": FilterOperator.EQUALS,
            "eq": FilterOperator.EQUALS,
            "!=": FilterOperator.NOT_EQUALS,
            "ne": FilterOperator.NOT_EQUALS,
            ">": FilterOperator.GREATER_THAN,
            "gt": FilterOperator.GREATER_THAN,
            ">=": FilterOperator.GREATER_THAN_OR_EQUAL,
            "gte": FilterOperator.GREATER_THAN_OR_EQUAL,
            "<": FilterOperator.LESS_THAN,
            "lt": FilterOperator.LESS_THAN,
            "<=": FilterOperator.LESS_THAN_OR_EQUAL,
            "lte": FilterOperator.LESS_THAN_OR_EQUAL,
            "in": FilterOperator.IN,
            "not_in": FilterOperator.NOT_IN,
            "contains": FilterOperator.CONTAINS,
            "starts_with": FilterOperator.STARTS_WITH,
            "ends_with": FilterOperator.ENDS_WITH,
            "and": FilterOperator.AND,
            "or": FilterOperator.OR,
            "not": FilterOperator.NOT,
            "exists": FilterOperator.EXISTS,
            "not_exists": FilterOperator.NOT_EXISTS,
            "array_contains": FilterOperator.ARRAY_CONTAINS,
            "array_contains_any": FilterOperator.ARRAY_CONTAINS_ANY,
            "array_contains_all": FilterOperator.ARRAY_CONTAINS_ALL,
        }
        
        if op_str in operator_map:
            return operator_map[op_str]
        
        # Special MongoDB-style operators
        if op_str.startswith("$"):
            mongo_op = op_str[1:]
            mongo_map = {
                "eq": FilterOperator.EQUALS,
                "ne": FilterOperator.NOT_EQUALS,
                "gt": FilterOperator.GREATER_THAN,
                "gte": FilterOperator.GREATER_THAN_OR_EQUAL,
                "lt": FilterOperator.LESS_THAN,
                "lte": FilterOperator.LESS_THAN_OR_EQUAL,
                "in": FilterOperator.IN,
                "nin": FilterOperator.NOT_IN,
                "regex": FilterOperator.CONTAINS,
                "exists": FilterOperator.EXISTS,
                "and": FilterOperator.AND,
                "or": FilterOperator.OR,
                "not": FilterOperator.NOT,
            }
            
            if mongo_op in mongo_map:
                return mongo_map[mongo_op]
        
        raise ValueError(f"Unknown operator: {op_str}")


@dataclass
class Filter:
    """A filter for a query.
    
    Attributes:
        field: The field to filter on.
        operator: The filter operator.
        value: The filter value.
    """
    
    field: str
    operator: FilterOperator
    value: Any
    
    @staticmethod
    def parse(field: str, value: Any) -> 'Filter':
        """Parse a filter from a field and value.
        
        Args:
            field: The field to filter on.
            value: The filter value, which may be a simple value or a dict with operators.
            
        Returns:
            A Filter instance.
            
        Raises:
            ValueError: If the filter is invalid.
        """
        # Simple equality filter
        if not isinstance(value, dict) or not any(k.startswith("$") for k in value.keys()):
            return Filter(field, FilterOperator.EQUALS, value)
        
        # Complex filter with operators
        operator_field = next((k for k in value.keys() if k.startswith("$")), None)
        if not operator_field:
            return Filter(field, FilterOperator.EQUALS, value)
        
        operator = FilterOperator.from_string(operator_field)
        return Filter(field, operator, value[operator_field])
    
    def matches(self, record: Dict[str, Any]) -> bool:
        """Check if a record matches this filter.
        
        Args:
            record: The record to check.
            
        Returns:
            True if the record matches, False otherwise.
        """
        # Get the field value
        if "." in self.field:
            # Nested field
            parts = self.field.split(".")
            value = record
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    # Field doesn't exist
                    value = None
                    break
        else:
            # Top-level field
            value = record.get(self.field)
        
        # Check existence operators first
        if self.operator == FilterOperator.EXISTS:
            return value is not None
        elif self.operator == FilterOperator.NOT_EXISTS:
            return value is None
        
        # If the field doesn't exist, it doesn't match (except for NOT_EXISTS)
        if value is None:
            return False
        
        # Check the operator
        if self.operator == FilterOperator.EQUALS:
            return value == self.value
        elif self.operator == FilterOperator.NOT_EQUALS:
            return value != self.value
        elif self.operator == FilterOperator.GREATER_THAN:
            return value > self.value
        elif self.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return value >= self.value
        elif self.operator == FilterOperator.LESS_THAN:
            return value < self.value
        elif self.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return value <= self.value
        elif self.operator == FilterOperator.IN:
            return value in self.value
        elif self.operator == FilterOperator.NOT_IN:
            return value not in self.value
        elif self.operator == FilterOperator.CONTAINS:
            if isinstance(value, str) and isinstance(self.value, str):
                return self.value in value
            return False
        elif self.operator == FilterOperator.STARTS_WITH:
            if isinstance(value, str) and isinstance(self.value, str):
                return value.startswith(self.value)
            return False
        elif self.operator == FilterOperator.ENDS_WITH:
            if isinstance(value, str) and isinstance(self.value, str):
                return value.endswith(self.value)
            return False
        elif self.operator == FilterOperator.ARRAY_CONTAINS:
            if isinstance(value, list):
                return self.value in value
            return False
        elif self.operator == FilterOperator.ARRAY_CONTAINS_ANY:
            if isinstance(value, list) and isinstance(self.value, list):
                return any(item in value for item in self.value)
            return False
        elif self.operator == FilterOperator.ARRAY_CONTAINS_ALL:
            if isinstance(value, list) and isinstance(self.value, list):
                return all(item in value for item in self.value)
            return False
        
        # Unknown operator
        return False


@dataclass
class SortOption:
    """Sort option for a query.
    
    Attributes:
        field: The field to sort by.
        direction: The sort direction (asc or desc).
    """
    
    field: str
    direction: str = "asc"  # "asc" or "desc"
    
    def __post_init__(self):
        """Validate sort option."""
        if self.direction not in ["asc", "desc"]:
            raise ValueError(f"Invalid sort direction: {self.direction}. "
                           f"Valid options are: asc, desc")
    
    @staticmethod
    def parse(sort_spec: Union[str, Dict[str, str], List[Dict[str, str]]]) -> List['SortOption']:
        """Parse sort options from various formats.
        
        Args:
            sort_spec: The sort specification:
                - A string field name (ascending sort)
                - A field name with direction indicator (e.g., "-field" for descending)
                - A dict with field and direction (e.g., {"field": "asc"})
                - A list of dicts with field and direction
            
        Returns:
            A list of SortOption instances.
            
        Raises:
            ValueError: If the sort specification is invalid.
        """
        if isinstance(sort_spec, str):
            # String format: "field" or "-field"
            if sort_spec.startswith("-"):
                return [SortOption(field=sort_spec[1:], direction="desc")]
            else:
                return [SortOption(field=sort_spec, direction="asc")]
        
        elif isinstance(sort_spec, dict):
            # Dict format: {"field": "asc"}
            options = []
            for field, direction in sort_spec.items():
                options.append(SortOption(field=field, direction=direction))
            return options
        
        elif isinstance(sort_spec, list):
            # List format: [{"field": "field1", "direction": "asc"}, ...]
            options = []
            for item in sort_spec:
                if isinstance(item, dict) and "field" in item:
                    options.append(SortOption(
                        field=item["field"],
                        direction=item.get("direction", "asc")
                    ))
                elif isinstance(item, str):
                    # List of strings: ["field1", "-field2", ...]
                    if item.startswith("-"):
                        options.append(SortOption(field=item[1:], direction="desc"))
                    else:
                        options.append(SortOption(field=item, direction="asc"))
                else:
                    raise ValueError(f"Invalid sort item: {item}")
            return options
        
        else:
            raise ValueError(f"Invalid sort specification: {sort_spec}")


@dataclass
class Query:
    """A query for retrieving records from a collection.
    
    Attributes:
        filters: List of filters to apply.
        sort: List of sort options.
        limit: Maximum number of records to return (0 means no limit).
        offset: Number of records to skip.
        include: List of related collections to include.
    """
    
    filters: List[Filter] = field(default_factory=list)
    sort: List[SortOption] = field(default_factory=list)
    limit: int = 0
    offset: int = 0
    include: List[str] = field(default_factory=list)
    
    @staticmethod
    def parse(query_dict: Dict[str, Any]) -> 'Query':
        """Parse a query from a dictionary.
        
        Args:
            query_dict: The query parameters.
            
        Returns:
            A Query instance.
        """
        query = Query()
        
        # Parse filters
        filters = query_dict.get("filters", {})
        if isinstance(filters, dict):
            for field, value in filters.items():
                query.filters.append(Filter.parse(field, value))
        
        # Parse sort
        sort = query_dict.get("sort")
        if sort:
            query.sort = SortOption.parse(sort)
        
        # Parse limit and offset
        if "limit" in query_dict:
            query.limit = int(query_dict["limit"])
        
        if "offset" in query_dict:
            query.offset = int(query_dict["offset"])
        
        # Parse include
        include = query_dict.get("include", [])
        if isinstance(include, str):
            query.include = [include]
        elif isinstance(include, list):
            query.include = include
        
        return query
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the query to a dictionary.
        
        Returns:
            A dictionary representation of the query.
        """
        result = {}
        
        # Filters
        if self.filters:
            filters = {}
            for f in self.filters:
                if f.operator == FilterOperator.EQUALS:
                    filters[f.field] = f.value
                else:
                    # Use MongoDB-style operators
                    op_str = {
                        FilterOperator.NOT_EQUALS: "$ne",
                        FilterOperator.GREATER_THAN: "$gt",
                        FilterOperator.GREATER_THAN_OR_EQUAL: "$gte",
                        FilterOperator.LESS_THAN: "$lt",
                        FilterOperator.LESS_THAN_OR_EQUAL: "$lte",
                        FilterOperator.IN: "$in",
                        FilterOperator.NOT_IN: "$nin",
                        FilterOperator.CONTAINS: "$regex",
                        FilterOperator.EXISTS: "$exists",
                        FilterOperator.NOT_EXISTS: "$exists",
                        FilterOperator.ARRAY_CONTAINS: "$elemMatch",
                        FilterOperator.ARRAY_CONTAINS_ANY: "$in",
                        FilterOperator.ARRAY_CONTAINS_ALL: "$all",
                    }.get(f.operator, "$eq")
                    
                    # Special handling for NOT_EXISTS
                    if f.operator == FilterOperator.NOT_EXISTS:
                        filters[f.field] = {op_str: False}
                    else:
                        filters[f.field] = {op_str: f.value}
            
            result["filters"] = filters
        
        # Sort
        if self.sort:
            result["sort"] = [
                {"field": s.field, "direction": s.direction}
                for s in self.sort
            ]
        
        # Limit and offset
        if self.limit > 0:
            result["limit"] = self.limit
        
        if self.offset > 0:
            result["offset"] = self.offset
        
        # Include
        if self.include:
            result["include"] = self.include
        
        return result
    
    def matches(self, record: Dict[str, Any]) -> bool:
        """Check if a record matches all filters in this query.
        
        Args:
            record: The record to check.
            
        Returns:
            True if the record matches all filters, False otherwise.
        """
        return all(f.matches(record) for f in self.filters)
    
    def apply_sort(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply sort options to a list of records.
        
        Args:
            records: The records to sort.
            
        Returns:
            The sorted records.
        """
        if not self.sort:
            return records
        
        # Build sort key function
        def sort_key(record):
            return tuple(
                self._get_field_value(record, s.field) if s.direction == "asc" else
                self._get_field_value_for_desc(record, s.field)
                for s in self.sort
            )
        
        return sorted(records, key=sort_key)
    
    def apply_limit_offset(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply limit and offset to a list of records.
        
        Args:
            records: The records to limit.
            
        Returns:
            The limited records.
        """
        if self.offset > 0:
            records = records[self.offset:]
        
        if self.limit > 0:
            records = records[:self.limit]
        
        return records
    
    def _get_field_value(self, record: Dict[str, Any], field: str) -> Any:
        """Get a field value from a record, supporting nested fields.
        
        Args:
            record: The record to get the value from.
            field: The field name, which may be a dot-separated path.
            
        Returns:
            The field value, or None if the field doesn't exist.
        """
        if "." in field:
            # Nested field
            parts = field.split(".")
            value = record
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    # Field doesn't exist
                    return None
            return value
        else:
            # Top-level field
            return record.get(field)
    
    def _get_field_value_for_desc(self, record: Dict[str, Any], field: str) -> Any:
        """Get a field value for descending sort (inverted for proper sorting).
        
        Args:
            record: The record to get the value from.
            field: The field name.
            
        Returns:
            The inverted field value for descending sort.
        """
        value = self._get_field_value(record, field)
        
        # Return a value that sorts in reverse order
        if isinstance(value, (int, float)):
            return -value
        elif isinstance(value, str):
            # Invert string (this works because sorted() is stable)
            return "\uffff" * 100 if value is None else "\uffff" * 100 - value
        elif value is None:
            # None should sort last in descending order
            return "\uffff" * 100
        else:
            # For other types, just return the value (may not sort correctly)
            return value


@dataclass
class QueryResult(Generic[T]):
    """Result of a query operation.
    
    Attributes:
        items: The records that matched the query.
        total: The total number of records that matched (without limit/offset).
        page: The current page number (1-based).
        pages: The total number of pages.
        limit: The limit used for the query.
        offset: The offset used for the query.
    """
    
    items: List[T]
    total: int
    limit: int = 0
    offset: int = 0
    
    @property
    def page(self) -> int:
        """Get the current page number (1-based).
        
        Returns:
            The current page number.
        """
        if self.limit <= 0:
            return 1
        
        return (self.offset // self.limit) + 1
    
    @property
    def pages(self) -> int:
        """Get the total number of pages.
        
        Returns:
            The total number of pages.
        """
        if self.limit <= 0:
            return 1
        
        return (self.total + self.limit - 1) // self.limit
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the query result to a dictionary.
        
        Returns:
            A dictionary representation of the query result.
        """
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "pages": self.pages,
            "limit": self.limit,
            "offset": self.offset
        }