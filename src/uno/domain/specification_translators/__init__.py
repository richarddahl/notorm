"""
Domain specification translators package.

DEPRECATED: This module has been deprecated and replaced by the new domain entity framework
in uno.domain.entity.specification.translator. Please use the new implementation instead.

This module now serves as a redirection layer to the new implementation.
"""

import warnings

warnings.warn(
    "CRITICAL: The uno.domain.specification_translators module is deprecated and will be removed in a future release. "
    "Use uno.domain.entity.specification.translator instead for all specification translator implementations.",
    DeprecationWarning,
    stacklevel=2
)

# Import from the new implementation to re-export
from uno.domain.entity.specification.translator import (
    SpecificationTranslator,
    InMemorySpecificationTranslator,
    SQLSpecificationTranslator,
    PostgreSQLSpecificationTranslator
)

# Legacy export for backward compatibility
PostgreSQLTranslator = PostgreSQLSpecificationTranslator

__all__ = [
    "SpecificationTranslator",
    "InMemorySpecificationTranslator",
    "SQLSpecificationTranslator",
    "PostgreSQLSpecificationTranslator",
    "PostgreSQLTranslator"
]