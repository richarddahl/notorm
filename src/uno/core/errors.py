"""
Error handling for the Uno framework.

IMPORTANT: This file is deprecated and provided only for backward compatibility.
Use the uno.core.errors package instead.
"""

import warnings

warnings.warn(
    "Importing directly from uno.core.errors is deprecated. "
    "Import from uno.core.errors.base, uno.core.errors.result, etc. instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import from the new location to maintain backward compatibility
from uno.core.errors.base import (
    UnoError as DomainError,
    ErrorCategory,
    ErrorSeverity,
    ErrorCode,
    ErrorContext,
    ErrorInfo,
    with_error_context,
    with_async_error_context,
    add_error_context,
    get_error_context
)

from uno.core.errors.result import (
    Result,
    Success, 
    Failure,
    of,
    failure,
    from_exception,
    from_awaitable,
    combine,
    combine_dict
)

from uno.core.errors.validation import (
    ValidationError,
    ValidationContext,
    FieldValidationError,
    validate_fields
)

from uno.core.errors.catalog import (
    ErrorCatalog,
    register_error,
    get_error_code_info,
    get_all_error_codes
)

from uno.core.errors.logging import (
    configure_logging,
    get_logger,
    LogConfig,
    with_logging_context,
    add_logging_context,
    get_logging_context,
    clear_logging_context
)