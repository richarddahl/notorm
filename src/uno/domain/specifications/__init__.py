"""
Domain specifications package.

This package contains specification pattern implementations for domain queries.
"""

from uno.domain.specifications.base import (
    Specification,
    AttributeSpecification,
    PredicateSpecification,
    DictionarySpecification,
    specification_factory,
)

from uno.domain.specifications.composite import (
    AndSpecification,
    OrSpecification,
    NotSpecification,
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

__all__ = [
    # Base specifications
    "Specification",
    "AttributeSpecification",
    "PredicateSpecification",
    "DictionarySpecification",
    
    # Composite specifications
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    
    # Enhanced specifications
    "RangeSpecification",
    "DateRangeSpecification",
    "TextMatchSpecification",
    "InListSpecification",
    "NotInListSpecification",
    "ComparableSpecification",
    "NullSpecification",
    "NotNullSpecification",
    
    # Factories
    "specification_factory",
    "enhance_specification_factory",
]

# Re-export specification factory and enhance it
SpecificationFactory = specification_factory
EnhancedSpecificationFactory = enhance_specification_factory
