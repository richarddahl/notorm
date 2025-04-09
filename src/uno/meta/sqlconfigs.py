# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.classes import SQLConfig
from uno.db.sql.graphsql import GraphSQLEmitter
from uno.db.sql.tablesql import (
    AlterGrants,
    InsertMetaType,
    InsertPermission,
)
from uno.meta.models import MetaTypeModel, MetaRecordModel


class MetaTypeSQLConfig(SQLConfig):
    table = MetaTypeModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertPermission,
        InsertMetaType,
        GraphSQLEmitter,
    ]


class MetaSQLConfig(SQLConfig):
    table = MetaRecordModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]
