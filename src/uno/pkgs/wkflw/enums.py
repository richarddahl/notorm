# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT
import enum


# Workflow Enums


class WorkflowDBEvent(str, enum.Enum):
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"


class WorkflowTrigger(str, enum.Enum):
    DB_EVENT = "DB Event"
    SCHEDULE = "Schedule"
    USER = "User"
