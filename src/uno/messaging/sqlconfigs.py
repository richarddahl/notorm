# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sql.config import SQLConfig
from uno.sql.emitters.table import (
    AlterGrants,
    InsertMetaType,
    InsertPermission,
)
from uno.sql.emitters.graph import GraphSQLEmitter
from uno.messaging.models import MessageUserModel, MessageModel


class MessageUserSQLConfig(SQLConfig):
    table = MessageUserModel.__table__
    default_emitters = [
        AlterGrants,
        InsertPermission,
        InsertMetaType,
        GraphSQLEmitter,
    ]


class MessageModelSQLConfig(SQLConfig):
    table = MessageModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]
