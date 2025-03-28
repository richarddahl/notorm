# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sql import (
    SQLConfig,
    AlterGrants,
    InsertMetaType,
    InsertPermission,
)
from uno.graphsql import GraphSQLEmitter
from uno.meta.bases import MetaTypeBase, MetaBase


class MetaTypeSQLConfig(SQLConfig):
    table = MetaTypeBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertPermission,
        InsertMetaType,
        GraphSQLEmitter,
    ]


class MetaSQLConfig(SQLConfig):
    table = MetaBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]
