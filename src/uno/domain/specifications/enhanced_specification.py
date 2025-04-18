"""
Enhanced specifications for common query patterns.

This module provides specialized specifications for common query patterns,
such as range queries, text search, date comparisons, and more.
"""

from typing import TypeVar, Generic, Any, List, Dict, Optional, Union, Callable, Set
from datetime import datetime, date, time, timedelta
import re
import uuid

from uno.domain.protocols import EntityProtocol
from uno.domain.specifications.base import Specification


# Type variable for the entity being specified
T = TypeVar('T', bound=EntityProtocol)


class RangeSpecification(Specification[T]):
    """
    Specification for a range query.
    
    This specification matches entities where an attribute falls within a range.
    """
    
    def __init__(
        self, 
        attribute: str, 
        min_value: Any, 
        max_value: Any, 
        include_min: bool = True, 
        include_max: bool = True
    ):
        """
        Initialize a range specification.
        
        Args:
            attribute: The attribute to check
            min_value: The minimum value of the range
            max_value: The maximum value of the range
            include_min: Whether to include the minimum value
            include_max: Whether to include the maximum value
        """
        self.attribute = attribute
        self.min_value = min_value
        self.max_value = max_value
        self.include_min = include_min
        self.include_max = include_max
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's attribute is within the range.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the attribute is within the range, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        value = getattr(entity, self.attribute)
        
        # Check if the value is within the range
        min_check = (
            value > self.min_value if not self.include_min else 
            value >= self.min_value
        )
        max_check = (
            value < self.max_value if not self.include_max else 
            value <= self.max_value
        )
        
        return min_check and max_check


class DateRangeSpecification(Specification[T]):
    """
    Specification for a date range query.
    
    This specification matches entities where a date attribute falls within a date range.
    """
    
    def __init__(
        self, 
        attribute: str, 
        start_date: Union[datetime, date], 
        end_date: Union[datetime, date], 
        include_start: bool = True, 
        include_end: bool = True
    ):
        """
        Initialize a date range specification.
        
        Args:
            attribute: The attribute to check
            start_date: The start date of the range
            end_date: The end date of the range
            include_start: Whether to include the start date
            include_end: Whether to include the end date
        """
        self.attribute = attribute
        self.start_date = start_date
        self.end_date = end_date
        self.include_start = include_start
        self.include_end = include_end
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's date attribute is within the date range.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the date attribute is within the range, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        date_value = getattr(entity, self.attribute)
        
        # Check if the date is within the range
        start_check = (
            date_value > self.start_date if not self.include_start else 
            date_value >= self.start_date
        )
        end_check = (
            date_value < self.end_date if not self.include_end else 
            date_value <= self.end_date
        )
        
        return start_check and end_check


class RelativeDateSpecification(Specification[T]):
    """
    Specification for a relative date range query.
    
    This specification matches entities where a date attribute falls within a range
    relative to the current date (e.g., within the last 7 days).
    """
    
    def __init__(
        self,
        attribute: str,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        mode: str = "past",
        include_boundary: bool = True
    ):
        """
        Initialize a relative date specification.
        
        Args:
            attribute: The attribute to check
            days: Number of days in the relative range
            hours: Number of hours in the relative range
            minutes: Number of minutes in the relative range
            mode: "past" for dates in the past, "future" for dates in the future
            include_boundary: Whether to include the boundary date
        """
        self.attribute = attribute
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.mode = mode
        self.include_boundary = include_boundary
        
        # Calculate the time delta
        self.delta = timedelta(days=days, hours=hours, minutes=minutes)
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's date attribute is within the relative range.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the date attribute is within the range, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        date_value = getattr(entity, self.attribute)
        now = datetime.now(timezone.utc) if isinstance(date_value, datetime) else date.today()
        
        if self.mode == "past":
            boundary_date = now - self.delta
            if self.include_boundary:
                return date_value >= boundary_date
            else:
                return date_value > boundary_date
        else:  # mode == "future"
            boundary_date = now + self.delta
            if self.include_boundary:
                return date_value <= boundary_date
            else:
                return date_value < boundary_date


class TextMatchSpecification(Specification[T]):
    """
    Specification for text matching queries.
    
    This specification matches entities where a text attribute contains, starts with,
    ends with, or matches a pattern.
    """
    
    def __init__(
        self, 
        attribute: str, 
        text: str, 
        match_type: str = "contains", 
        case_sensitive: bool = False
    ):
        """
        Initialize a text match specification.
        
        Args:
            attribute: The attribute to check
            text: The text to match
            match_type: The type of match (contains, starts_with, ends_with, exact, regex)
            case_sensitive: Whether the match is case-sensitive
        """
        self.attribute = attribute
        self.text = text
        self.match_type = match_type
        self.case_sensitive = case_sensitive
        
        # Precompile regex pattern if match type is regex
        if self.match_type == "regex":
            flags = 0 if case_sensitive else re.IGNORECASE
            self.pattern = re.compile(text, flags)
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's text attribute matches the text.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the text attribute matches, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        value = getattr(entity, self.attribute)
        
        # If value is not a string, convert it to string
        if not isinstance(value, str):
            value = str(value)
        
        # If not case sensitive, convert both to lowercase
        if not self.case_sensitive:
            value = value.lower()
            match_text = self.text.lower()
        else:
            match_text = self.text
        
        # Check based on match type
        if self.match_type == "contains":
            return match_text in value
        elif self.match_type == "starts_with":
            return value.startswith(match_text)
        elif self.match_type == "ends_with":
            return value.endswith(match_text)
        elif self.match_type == "exact":
            return value == match_text
        elif self.match_type == "regex":
            return bool(self.pattern.search(value))
        else:
            raise ValueError(f"Unknown match type: {self.match_type}")


class InListSpecification(Specification[T]):
    """
    Specification for checking if an attribute is in a list of values.
    
    This specification matches entities where an attribute is in a list of values.
    """
    
    def __init__(self, attribute: str, values: List[Any]):
        """
        Initialize an in-list specification.
        
        Args:
            attribute: The attribute to check
            values: The list of values to check against
        """
        self.attribute = attribute
        self.values = values
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's attribute is in the list of values.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the attribute is in the list, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        value = getattr(entity, self.attribute)
        return value in self.values


class NotInListSpecification(Specification[T]):
    """
    Specification for checking if an attribute is not in a list of values.
    
    This specification matches entities where an attribute is not in a list of values.
    """
    
    def __init__(self, attribute: str, values: List[Any]):
        """
        Initialize a not-in-list specification.
        
        Args:
            attribute: The attribute to check
            values: The list of values to check against
        """
        self.attribute = attribute
        self.values = values
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's attribute is not in the list of values.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the attribute is not in the list, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        value = getattr(entity, self.attribute)
        return value not in self.values


class ComparableSpecification(Specification[T]):
    """
    Specification for comparable values (gt, lt, gte, lte).
    
    This specification matches entities where an attribute compares to a value
    in the specified way (greater than, less than, etc.).
    """
    
    def __init__(self, attribute: str, value: Any, operator: str = "eq"):
        """
        Initialize a comparable specification.
        
        Args:
            attribute: The attribute to check
            value: The value to compare against
            operator: The comparison operator (eq, neq, gt, gte, lt, lte)
        """
        self.attribute = attribute
        self.value = value
        self.operator = operator
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's attribute compares to the value as specified.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the comparison is satisfied, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        actual_value = getattr(entity, self.attribute)
        
        # Check based on operator
        if self.operator == "eq":
            return actual_value == self.value
        elif self.operator == "neq":
            return actual_value != self.value
        elif self.operator == "gt":
            return actual_value > self.value
        elif self.operator == "gte":
            return actual_value >= self.value
        elif self.operator == "lt":
            return actual_value < self.value
        elif self.operator == "lte":
            return actual_value <= self.value
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


class NullSpecification(Specification[T]):
    """
    Specification for checking if an attribute is null.
    
    This specification matches entities where an attribute is None.
    """
    
    def __init__(self, attribute: str):
        """
        Initialize a null specification.
        
        Args:
            attribute: The attribute to check
        """
        self.attribute = attribute
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's attribute is None.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the attribute is None, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        return getattr(entity, self.attribute) is None


class NotNullSpecification(Specification[T]):
    """
    Specification for checking if an attribute is not null.
    
    This specification matches entities where an attribute is not None.
    """
    
    def __init__(self, attribute: str):
        """
        Initialize a not-null specification.
        
        Args:
            attribute: The attribute to check
        """
        self.attribute = attribute
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's attribute is not None.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the attribute is not None, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        return getattr(entity, self.attribute) is not None


class CollectionSizeSpecification(Specification[T]):
    """
    Specification for checking the size of a collection attribute.
    
    This specification matches entities based on the size of a collection attribute
    (e.g., list, set, dict, etc.).
    """
    
    def __init__(self, attribute: str, size: int, operator: str = "eq"):
        """
        Initialize a collection size specification.
        
        Args:
            attribute: The collection attribute to check
            size: The size to compare against
            operator: The comparison operator (eq, neq, gt, gte, lt, lte)
        """
        self.attribute = attribute
        self.size = size
        self.operator = operator
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's collection attribute size satisfies the condition.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the collection size condition is satisfied, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        collection = getattr(entity, self.attribute)
        
        # Check if attribute is a collection
        if not hasattr(collection, "__len__"):
            return False
        
        # Get the size of the collection
        actual_size = len(collection)
        
        # Compare using the specified operator
        if self.operator == "eq":
            return actual_size == self.size
        elif self.operator == "neq":
            return actual_size != self.size
        elif self.operator == "gt":
            return actual_size > self.size
        elif self.operator == "gte":
            return actual_size >= self.size
        elif self.operator == "lt":
            return actual_size < self.size
        elif self.operator == "lte":
            return actual_size <= self.size
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


class CollectionContainsSpecification(Specification[T]):
    """
    Specification for checking if a collection attribute contains a value.
    
    This specification matches entities where a collection attribute (e.g., list, set)
    contains a specific value.
    """
    
    def __init__(self, attribute: str, value: Any):
        """
        Initialize a collection contains specification.
        
        Args:
            attribute: The collection attribute to check
            value: The value to check for in the collection
        """
        self.attribute = attribute
        self.value = value
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's collection attribute contains the value.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the collection contains the value, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        collection = getattr(entity, self.attribute)
        
        # Check if the value is in the collection
        try:
            return self.value in collection
        except TypeError:
            # If the collection doesn't support 'in' operator
            return False


class UUIDSpecification(Specification[T]):
    """
    Specification for UUID fields.
    
    This specification matches entities with UUID fields that match a specific UUID
    or a string representation of a UUID.
    """
    
    def __init__(self, attribute: str, uuid_value: Union[uuid.UUID, str]):
        """
        Initialize a UUID specification.
        
        Args:
            attribute: The UUID attribute to check
            uuid_value: The UUID value to match (can be a UUID object or a string)
        """
        self.attribute = attribute
        
        # Convert string to UUID if needed
        if isinstance(uuid_value, str):
            try:
                self.uuid_value = uuid.UUID(uuid_value)
            except ValueError:
                # Keep as string if not a valid UUID
                self.uuid_value = uuid_value
        else:
            self.uuid_value = uuid_value
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's UUID attribute matches the specified UUID.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the UUID matches, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        attr_value = getattr(entity, self.attribute)
        
        # Convert attribute to UUID if it's a string
        if isinstance(attr_value, str):
            try:
                attr_value = uuid.UUID(attr_value)
            except ValueError:
                # Keep as string if not a valid UUID
                pass
        
        # Compare UUIDs or strings
        return attr_value == self.uuid_value


class JsonPathSpecification(Specification[T]):
    """
    Specification for checking values in JSON/dict fields using a path.
    
    This specification matches entities where a value at a specified path within
    a JSON/dict attribute matches a condition.
    """
    
    def __init__(
        self, 
        attribute: str, 
        path: List[str], 
        value: Any, 
        operator: str = "eq"
    ):
        """
        Initialize a JSON path specification.
        
        Args:
            attribute: The JSON/dict attribute to check
            path: The path to the nested value as a list of keys
            value: The value to compare against
            operator: The comparison operator (eq, neq, gt, gte, lt, lte)
        """
        self.attribute = attribute
        self.path = path
        self.value = value
        self.operator = operator
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity's JSON attribute at the specified path satisfies the condition.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the condition is satisfied, False otherwise
        """
        if not hasattr(entity, self.attribute):
            return False
        
        # Get the JSON/dict attribute
        data = getattr(entity, self.attribute)
        
        # Navigate the path to get the nested value
        try:
            for key in self.path:
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    return False
        except (TypeError, KeyError):
            return False
        
        # Compare using the specified operator
        if self.operator == "eq":
            return data == self.value
        elif self.operator == "neq":
            return data != self.value
        elif self.operator == "gt":
            return data > self.value
        elif self.operator == "gte":
            return data >= self.value
        elif self.operator == "lt":
            return data < self.value
        elif self.operator == "lte":
            return data <= self.value
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


class HasAttributeSpecification(Specification[T]):
    """
    Specification for checking if an entity has a specific attribute.
    
    This specification matches entities that have a specific attribute,
    regardless of its value.
    """
    
    def __init__(self, attribute: str):
        """
        Initialize a has-attribute specification.
        
        Args:
            attribute: The attribute to check for
        """
        self.attribute = attribute
    
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the entity has the specified attribute.
        
        Args:
            entity: The entity to check
            
        Returns:
            True if the entity has the attribute, False otherwise
        """
        return hasattr(entity, self.attribute)


def enhance_specification_factory(factory_class):
    """
    Enhance a specification factory with additional methods for enhanced specifications.
    
    Args:
        factory_class: The specification factory class to enhance
        
    Returns:
        The enhanced specification factory class
    """
    # Basic enhanced specifications
    factory_class.range = classmethod(lambda cls, attribute, min_value, max_value, include_min=True, include_max=True:
                                    RangeSpecification(attribute, min_value, max_value, include_min, include_max))
    
    factory_class.date_range = classmethod(lambda cls, attribute, start_date, end_date, include_start=True, include_end=True:
                                         DateRangeSpecification(attribute, start_date, end_date, include_start, include_end))
    
    factory_class.relative_date = classmethod(lambda cls, attribute, days=0, hours=0, minutes=0, mode="past", include_boundary=True:
                                            RelativeDateSpecification(attribute, days, hours, minutes, mode, include_boundary))
    
    factory_class.text_match = classmethod(lambda cls, attribute, text, match_type="contains", case_sensitive=False:
                                         TextMatchSpecification(attribute, text, match_type, case_sensitive))
    
    factory_class.in_list = classmethod(lambda cls, attribute, values:
                                      InListSpecification(attribute, values))
    
    factory_class.not_in_list = classmethod(lambda cls, attribute, values:
                                          NotInListSpecification(attribute, values))
    
    factory_class.compare = classmethod(lambda cls, attribute, value, operator="eq":
                                      ComparableSpecification(attribute, value, operator))
    
    factory_class.is_null = classmethod(lambda cls, attribute:
                                      NullSpecification(attribute))
    
    factory_class.is_not_null = classmethod(lambda cls, attribute:
                                          NotNullSpecification(attribute))
    
    # Collection specifications
    factory_class.collection_size = classmethod(lambda cls, attribute, size, operator="eq":
                                              CollectionSizeSpecification(attribute, size, operator))
    
    factory_class.collection_contains = classmethod(lambda cls, attribute, value:
                                                  CollectionContainsSpecification(attribute, value))
    
    # Advanced specifications
    factory_class.uuid = classmethod(lambda cls, attribute, uuid_value:
                                   UUIDSpecification(attribute, uuid_value))
    
    factory_class.json_path = classmethod(lambda cls, attribute, path, value, operator="eq":
                                        JsonPathSpecification(attribute, path, value, operator))
    
    factory_class.has_attribute = classmethod(lambda cls, attribute:
                                            HasAttributeSpecification(attribute))
    
    # Convenience methods for common comparisons
    factory_class.gt = classmethod(lambda cls, attribute, value: cls.compare(attribute, value, "gt"))
    factory_class.gte = classmethod(lambda cls, attribute, value: cls.compare(attribute, value, "gte"))
    factory_class.lt = classmethod(lambda cls, attribute, value: cls.compare(attribute, value, "lt"))
    factory_class.lte = classmethod(lambda cls, attribute, value: cls.compare(attribute, value, "lte"))
    factory_class.eq = classmethod(lambda cls, attribute, value: cls.compare(attribute, value, "eq"))
    factory_class.neq = classmethod(lambda cls, attribute, value: cls.compare(attribute, value, "neq"))
    
    # Convenience methods for common text matches
    factory_class.contains = classmethod(lambda cls, attribute, text, case_sensitive=False: 
                                       cls.text_match(attribute, text, "contains", case_sensitive))
    factory_class.starts_with = classmethod(lambda cls, attribute, text, case_sensitive=False: 
                                       cls.text_match(attribute, text, "starts_with", case_sensitive))
    factory_class.ends_with = classmethod(lambda cls, attribute, text, case_sensitive=False: 
                                       cls.text_match(attribute, text, "ends_with", case_sensitive))
    factory_class.exact_match = classmethod(lambda cls, attribute, text, case_sensitive=True: 
                                       cls.text_match(attribute, text, "exact", case_sensitive))
    factory_class.regex_match = classmethod(lambda cls, attribute, pattern, case_sensitive=False: 
                                       cls.text_match(attribute, pattern, "regex", case_sensitive))
    
    # Time-related convenience methods
    factory_class.created_within_days = classmethod(lambda cls, attribute, days: 
                                                 cls.relative_date(attribute, days=days))
    factory_class.created_after = classmethod(lambda cls, attribute, date: 
                                           cls.compare(attribute, date, "gt"))
    factory_class.created_before = classmethod(lambda cls, attribute, date: 
                                            cls.compare(attribute, date, "lt"))
    
    # Collection convenience methods
    factory_class.empty_collection = classmethod(lambda cls, attribute: 
                                               cls.collection_size(attribute, 0))
    factory_class.non_empty_collection = classmethod(lambda cls, attribute: 
                                                   cls.collection_size(attribute, 0, "gt"))
    
    return factory_class