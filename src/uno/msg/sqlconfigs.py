# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.classes import SQLConfig
from uno.db.sql.tablesql import (
    AlterGrants,
    InsertMetaType,
    InsertPermission,
)
from uno.db.sql.graphsql import GraphSQLEmitter
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
