# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Base error classes for the Uno framework.

This module provides the fundamental error classes used throughout the framework,
ensuring consistent error handling and reporting.
"""

from typing import Any, Dict, Optional


class BaseError(Exception):
    """
    Base class for all Uno framework errors.

    This class provides standardized error formatting with error codes,
    contextual information, and stacktrace capture.
    """

    def __init__(self, message: str, error_code: str, **context: Any):
        """
        Initialize a BaseError.

        Args:
            message: The error message
            error_code: A code identifying the error type
            **context: Additional context information
        """
        super().__init__(message)
        self.message: str = message
        self.error_code: str = error_code
        self.context: dict[str, Any] = context

    def __str__(self) -> str:
        """
        Format the error as a string.

        Returns a string representation that includes the error code
        and message, with context if available.

        Returns:
            Formatted error string
        """
        if not self.context:
            return f"[{self.error_code}] {self.message}"

        context_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
        return f"[{self.error_code}] {self.message} (Context: {context_str})"

    def with_context(self, **additional_context: Any) -> "BaseError":
        """
        Add additional context to this error.

        Returns a new error with combined context from this error
        and the additional context provided.

        Args:
            **additional_context: Additional context information

        Returns:
            New error with combined context
        """
        new_context = self.context.copy()
        new_context.update(additional_context)

        return type(self)(self.message, self.error_code, **new_context)


# No backward compatibility needed
