"""
Specification Pattern for Domain Entities.

This package provides the implementation of the Specification pattern for domain entities.
Specifications encapsulate query criteria, making them reusable, composable, and expressive.

Key components:
- Specification: Base class for all specifications
- CompositeSpecification: Base class for composite specifications (And, Or, Not)
- PredicateSpecification: Specification based on a predicate function
- AttributeSpecification: Specification that checks a specific attribute value
- Specification Translators: Convert specifications to database queries
"""

from uno.domain.entity.specification.base import (
    Specification,
    PredicateSpecification,
    AttributeSpecification,
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
from uno.domain.entity.specification.translator import (
    SpecificationTranslator,
    InMemorySpecificationTranslator,
    SQLSpecificationTranslator,
    PostgreSQLSpecificationTranslator
)

__all__ = [
    # Base
    'Specification',
    'PredicateSpecification',
    'AttributeSpecification',
    'Specifiable',
    
    # Composite
    'CompositeSpecification',
    'AndSpecification',
    'OrSpecification',
    'NotSpecification',
    'AllSpecification',
    'AnySpecification',
    
    # Translators
    'SpecificationTranslator',
    'InMemorySpecificationTranslator',
    'SQLSpecificationTranslator',
    'PostgreSQLSpecificationTranslator'
]