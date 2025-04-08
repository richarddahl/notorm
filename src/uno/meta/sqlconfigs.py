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
