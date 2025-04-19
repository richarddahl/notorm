"""
Domain specification translators package.

DEPRECATED: This module has been deprecated and replaced by the new domain entity framework
in uno.domain.entity.specification.translator. Please use the new implementation instead.

This package contains translators for converting specifications to database queries.
"""

import warnings

warnings.warn(
    "The uno.domain.specification_translators module is deprecated. "
    "Use uno.domain.entity.specification.translator instead.",
    DeprecationWarning,
    stacklevel=2
)

from .postgresql_translator import PostgreSQLSpecificationTranslator

__all__ = [
    "PostgreSQLSpecificationTranslator",
]
