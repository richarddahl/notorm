# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


class FilterType(enum.Enum):
    Column = "Column"
    Relationship = "Relationship"
