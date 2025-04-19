"""
Domain specifications package.

DEPRECATED: This module has been deprecated and replaced by the new domain entity framework
in uno.domain.entity.specification. Please use the new implementation instead.

This package contains specification pattern implementations for domain queries.
"""

import warnings

warnings.warn(
    "The uno.domain.specifications module is deprecated. "
    "Use uno.domain.entity.specification instead.",
    DeprecationWarning,
    stacklevel=2
)

from uno.domain.specifications.base_specification import (
    Specification,
    AttributeSpecification,
    PredicateSpecification,
    DictionarySpecification,
    specification_factory,
)

from uno.domain.specifications.composite_specification import (
    AndSpecification,
    OrSpecification,
    NotSpecification,
)

from uno.domain.specifications.enhanced_specification import (
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
