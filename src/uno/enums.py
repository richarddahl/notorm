# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


class SchemaDataType(str, enum.Enum):
    """
    Enumeration representing the data types for mask configurations.

    Attributes:
        NATIVE (str): Native (python) data.
        STRING (str): Babel formatted (localized) string.
        HTML (str): HTML Form Element JSON.
    """

    NATIVE = "native"
    STRING = "string"
    HTML = "html"
