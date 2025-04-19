"""
Specification translators for the Specification pattern.

This module provides abstract and concrete translator implementations that convert
Specification objects into queries for different data sources (SQL, in-memory, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Protocol, Type, TypeVar, cast

from uno.domain.entity.base import EntityBase
from uno.domain.entity.specification.base import Specification, AttributeSpecification, PredicateSpecification
from uno.domain.entity.specification.composite import (
    AndSpecification, OrSpecification, NotSpecification, 
    AllSpecification, AnySpecification
)

T = TypeVar("T", bound=EntityBase)  # Entity type
Q = TypeVar("Q")  # Query type


class SpecificationTranslator(Generic[T, Q], ABC):
    """
    Abstract base class for translating specifications to queries.
    
    This class defines the interface for translators that convert Specification
    objects into queries for different data sources.
    """
    
    @abstractmethod
    def translate(self, specification: Specification[T]) -> Q:
        """
        Translate a specification into a query.
        
        Args:
            specification: The specification to translate
            
        Returns:
            The resulting query object
        """
        pass


class InMemorySpecificationTranslator(SpecificationTranslator[T, List[T]]):
    """
    Translator that applies specifications to in-memory collections.
    
    This translator evaluates specifications against a list of entities in memory.
    """
    
    def translate(self, specification: Specification[T]) -> List[T]:
        """
        Apply a specification to a list of entities.
        
        Args:
            specification: The specification to apply
            
        Returns:
            A function that takes a list of entities and returns filtered entities
        """
        return lambda entities: [e for e in entities if specification.is_satisfied_by(e)]


class SQLSpecificationTranslator(SpecificationTranslator[T, Dict[str, Any]]):
    """
    Translator that converts specifications to SQL filter criteria.
    
    This translator produces filter dictionaries that can be used with SQL queries.
    """
    
    def translate(self, specification: Specification[T]) -> Dict[str, Any]:
        """
        Translate a specification into SQL filter criteria.
        
        Args:
            specification: The specification to translate
            
        Returns:
            A dictionary of filter criteria suitable for SQL queries
        """
        if isinstance(specification, AttributeSpecification):
            return self._translate_attribute_specification(specification)
        elif isinstance(specification, AndSpecification):
            return self._translate_and_specification(specification)
        elif isinstance(specification, OrSpecification):
            return self._translate_or_specification(specification)
        elif isinstance(specification, NotSpecification):
            return self._translate_not_specification(specification)
        elif isinstance(specification, AllSpecification):
            return self._translate_all_specification(specification)
        elif isinstance(specification, AnySpecification):
            return self._translate_any_specification(specification)
        else:
            raise ValueError(f"Unsupported specification type: {type(specification)}")
    
    def _translate_attribute_specification(self, specification: AttributeSpecification[T]) -> Dict[str, Any]:
        """
        Translate an attribute specification into SQL filter criteria.
        
        Args:
            specification: The attribute specification to translate
            
        Returns:
            A dictionary with the attribute name and expected value
        """
        # Simple equality filter
        return {specification.attribute_name: specification.expected_value}
    
    def _translate_and_specification(self, specification: AndSpecification[T]) -> Dict[str, Any]:
        """
        Translate an AND specification into SQL filter criteria.
        
        Args:
            specification: The AND specification to translate
            
        Returns:
            A dictionary combining the filters from both specifications
        """
        left_filters = self.translate(specification.left)
        right_filters = self.translate(specification.right)
        
        # Combine filters from both sides
        return {**left_filters, **right_filters}
    
    def _translate_or_specification(self, specification: OrSpecification[T]) -> Dict[str, Any]:
        """
        Translate an OR specification into SQL filter criteria.
        
        Args:
            specification: The OR specification to translate
            
        Returns:
            A dictionary representing an OR condition
        """
        left_filters = self.translate(specification.left)
        right_filters = self.translate(specification.right)
        
        # Use a special "$or" operator for OR conditions
        return {"$or": [left_filters, right_filters]}
    
    def _translate_not_specification(self, specification: NotSpecification[T]) -> Dict[str, Any]:
        """
        Translate a NOT specification into SQL filter criteria.
        
        Args:
            specification: The NOT specification to translate
            
        Returns:
            A dictionary representing a NOT condition
        """
        inner_filters = self.translate(specification.specification)
        
        # Use a special "$not" operator for NOT conditions
        return {"$not": inner_filters}
    
    def _translate_all_specification(self, specification: AllSpecification[T]) -> Dict[str, Any]:
        """
        Translate an ALL specification into SQL filter criteria.
        
        Args:
            specification: The ALL specification to translate
            
        Returns:
            A dictionary combining filters from all specifications
        """
        # Combine filters from all specifications
        result = {}
        for spec in specification.specifications:
            result.update(self.translate(spec))
        return result
    
    def _translate_any_specification(self, specification: AnySpecification[T]) -> Dict[str, Any]:
        """
        Translate an ANY specification into SQL filter criteria.
        
        Args:
            specification: The ANY specification to translate
            
        Returns:
            A dictionary representing an OR condition over all specifications
        """
        # Create an OR condition over all specifications
        return {"$or": [self.translate(spec) for spec in specification.specifications]}


class PostgreSQLSpecificationTranslator(SQLSpecificationTranslator[T]):
    """
    Translator that converts specifications to PostgreSQL-specific filter criteria.
    
    This translator extends the base SQL translator with PostgreSQL-specific features.
    """
    
    def _translate_attribute_specification(self, specification: AttributeSpecification[T]) -> Dict[str, Any]:
        """
        Translate an attribute specification into PostgreSQL filter criteria.
        
        Args:
            specification: The attribute specification to translate
            
        Returns:
            A dictionary with the attribute name and expected value, with PostgreSQL operations
        """
        # If we have a custom comparator, we might need special handling
        if specification.comparator.__name__ != 'eq':
            if specification.comparator.__name__ == 'lt':
                return {f"{specification.attribute_name}__lt": specification.expected_value}
            elif specification.comparator.__name__ == 'lte':
                return {f"{specification.attribute_name}__lte": specification.expected_value}
            elif specification.comparator.__name__ == 'gt':
                return {f"{specification.attribute_name}__gt": specification.expected_value}
            elif specification.comparator.__name__ == 'gte':
                return {f"{specification.attribute_name}__gte": specification.expected_value}
            elif specification.comparator.__name__ == 'contains':
                return {f"{specification.attribute_name}__contains": specification.expected_value}
            elif specification.comparator.__name__ == 'startswith':
                return {f"{specification.attribute_name}__startswith": specification.expected_value}
            elif specification.comparator.__name__ == 'endswith':
                return {f"{specification.attribute_name}__endswith": specification.expected_value}
        
        # Default to standard equality
        return super()._translate_attribute_specification(specification)