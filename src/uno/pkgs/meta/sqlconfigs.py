# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.sqlconfig import SQLConfig
from uno.db.sql.tablesql import AlterGrants, InsertMetaType
from uno.db.sql.dbsql import InsertPermission
from uno.db.sql.graphsql import GraphSQLEmitter
from uno.pkgs.meta.bases import MetaTypeBase, MetaBase


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
