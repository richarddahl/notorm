"""
Domain specification translators package.

This package contains translators for converting specifications to database queries.
"""

from .postgresql_translator import PostgreSQLSpecificationTranslator

__all__ = [
    "PostgreSQLSpecificationTranslator",
]
