"""
Specification pattern implementation for domain models.

This package provides a flexible, composable way to express business rules
and constraints on domain entities through the specification pattern.
"""

from uno.domain.specifications.base import (
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    AttributeSpecification,
    PredicateSpecification,
    DictionarySpecification,
    specification_factory,
)

from uno.domain.specifications.enhanced import (
    RangeSpecification,
    DateRangeSpecification,
    TextMatchSpecification,
    InListSpecification,
    NotInListSpecification,
    ComparableSpecification,
    NullSpecification,
    NotNullSpecification,
    enhance_specification_factory,
)

# Re-export specification factory and enhance it
SpecificationFactory = specification_factory
EnhancedSpecificationFactory = enhance_specification_factory