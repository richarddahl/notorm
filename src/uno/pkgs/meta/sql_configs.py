# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.sql_config import SQLConfig
from uno.db.sql.table_sql_emitters import AlterGrants, InsertMetaType
from uno.db.sql.db_sql_emitters import InsertPermission
from uno.db.sql.graph_sql_emitter import GraphSQLEmitter
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
