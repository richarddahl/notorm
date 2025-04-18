"""
DEPRECATED: This module has been replaced by the new validation framework.

Please use uno.core.validation instead.

This file will be removed in a future version.
"""

import warnings
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union, cast

warnings.warn(
    "The uno.domain.validation module is deprecated and will be removed "
    "in a future version. Use uno.core.validation instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from uno.core.validation import (
    Validator, ValidationContext, DomainValidator, 
    domain_validator, ValidationProtocol
)
from uno.core.errors.result import ErrorSeverity as ValidationSeverity
from uno.core.errors.result import ValidationResult, ValidationError

# Backward compatibility aliases
FieldValidator = DomainValidator
DataValidator = DomainValidator