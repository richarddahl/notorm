"""
DEPRECATED: This module has been replaced by the new validation framework.

Please use uno.core.validation instead.

This file will be removed in a future version.
"""

import warnings

warnings.warn(
    "The uno.core.errors.validation module is deprecated and will be removed "
    "in a future version. Use uno.core.validation instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from uno.core.validation import ValidationContext
from uno.core.validation.validator import validate_fields

# Compatibility alias
def create_validation_context(entity_name=""):
    warnings.warn(
        "create_validation_context is deprecated. Use ValidationContext directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    return ValidationContext(entity_name)