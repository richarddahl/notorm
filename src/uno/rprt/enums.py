# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


# Workflow Enums
class WorkflowRecordStatus(str, enum.Enum):
    CLOSED = "Closed"
    OPEN = "Open"
    AT_RISK = "At Risk"
    OVERDUE = "Overdue"


class WorkflowRecordState(str, enum.Enum):
    PENDING = "Pending"
    COMPLETE = "Complete"
    CANCELLED = "Cancelled"
    DEFERRED = "Deferred"


class WorkflowFlag(str, enum.Enum):
    INFORMATION = "Information"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class WorkflowDBEvent(str, enum.Enum):
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"


class WorkflowTrigger(str, enum.Enum):
    DB_EVENT = "DB Event"
    SCHEDULE = "Schedule"
    USER = "User"
