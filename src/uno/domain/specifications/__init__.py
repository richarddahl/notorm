"""
Domain specifications package.

DEPRECATED: This module has been deprecated and replaced by the new domain entity framework
in uno.domain.entity.specification. Please use the new implementation instead.

This module now serves as a redirection layer to the new implementation.
"""

import warnings

warnings.warn(
    "CRITICAL: The uno.domain.specifications module is deprecated and will be removed in a future release. "
    "Use uno.domain.entity.specification instead for all specification implementations.",
    DeprecationWarning,
    stacklevel=2
)

# Import from the new implementation to re-export
from uno.domain.entity.specification.base import (
    Specification,
    AttributeSpecification,
    PredicateSpecification,
    Specifiable
)

from uno.domain.entity.specification.composite import (
    CompositeSpecification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    AllSpecification,
    AnySpecification
)

# Legacy exports
DictionarySpecification = PredicateSpecification
specification_factory = lambda: None  # Stub for backward compatibility
enhance_specification_factory = lambda: None  # Stub for backward compatibility

# For backward compatibility
from uno.domain.entity.compatibility import (
    LegacySpecification,
    LegacyAndSpecification,
    LegacyOrSpecification,
    LegacyNotSpecification
)

# Re-export specification factory class
SpecificationFactory = None  # Stub for backward compatibility
EnhancedSpecificationFactory = None  # Stub for backward compatibility

# For enhanced specifications, redirect to base specs
# These will throw deprecation warnings when used
RangeSpecification = AttributeSpecification
DateRangeSpecification = AttributeSpecification
TextMatchSpecification = AttributeSpecification
InListSpecification = AttributeSpecification
NotInListSpecification = AttributeSpecification
ComparableSpecification = AttributeSpecification
NullSpecification = AttributeSpecification
NotNullSpecification = AttributeSpecification

__all__ = [
    # Base specifications
    "Specification",
    "AttributeSpecification",
    "PredicateSpecification",
    "DictionarySpecification",
    "Specifiable",
    
    # Composite specifications
    "CompositeSpecification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    "AllSpecification",
    "AnySpecification",
    
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
    "SpecificationFactory",
    "EnhancedSpecificationFactory",
    
    # Legacy compatibility
    "LegacySpecification",
    "LegacyAndSpecification",
    "LegacyOrSpecification",
    "LegacyNotSpecification"
]