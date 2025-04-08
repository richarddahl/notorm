# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sqlclasses import (
    SQLConfig,
    AlterGrants,
    InsertMetaType,
    InsertPermission,
)
from uno.sqlgraph import GraphSQLEmitter
from uno.msg.models import MessageUserModel, MessageModel


class MessageUserSQLConfig(SQLConfig):
    table = MessageUserModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertPermission,
        InsertMetaType,
        GraphSQLEmitter,
    ]


class MessageModelSQLConfig(SQLConfig):
    table = MessageModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]
