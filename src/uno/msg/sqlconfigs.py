# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sqlemitter import (
    SQLConfig,
    AlterGrants,
    InsertMetaType,
    InsertPermission,
)
from uno.graphsql import GraphSQLEmitter
from uno.msg.bases import MessageUserBase, MessageBase


class MessageUserSQLConfig(SQLConfig):
    table = MessageUserBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertPermission,
        InsertMetaType,
        GraphSQLEmitter,
    ]


class MessageBaseSQLConfig(SQLConfig):
    table = MessageBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]
