# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


# Report Enumerations
class Status(str, enum.Enum):
    CLOSED = "Closed"
    OPEN = "Open"
    AT_RISK = "At Risk"
    OVERDUE = "Overdue"


class State(str, enum.Enum):
    PENDING = "Pending"
    COMPLETE = "Complete"
    CANCELLED = "Cancelled"
    DEFERRED = "Deferred"


class Flag(str, enum.Enum):
    INFORMATION = "Information"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
