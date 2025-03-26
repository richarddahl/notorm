# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.tablesql import (
    AlterGrants,
    InsertMetaType,
)
from uno.db.sql.dbsql import (
    RecordUserAuditFunction,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
)
from uno.db.sql.sqlconfig import SQLConfig
from uno.db.sql.graphsql import GraphSQLEmitter
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
