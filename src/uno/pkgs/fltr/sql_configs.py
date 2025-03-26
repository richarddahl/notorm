# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.table_sql_emitters import (
    AlterGrants,
    InsertMetaType,
)
from uno.db.sql.db_sql_emitters import (
    RecordUserAuditFunction,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
)
from uno.db.sql.sql_config import SQLConfig
from uno.db.sql.graph_sql_emitter import GraphSQLEmitter
from uno.pkgs.fltr.bases import FilterBase, FilterValueBase, QueryBase


class FilterSQLConfig(SQLConfig):
    table = FilterBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]


class FilterValueSQLConfig(SQLConfig):
    table = FilterValueBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class QuerySQLConfig(SQLConfig):
    table = QueryBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]
