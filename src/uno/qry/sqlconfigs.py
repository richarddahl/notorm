# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.classes import SQLConfig

from uno.db.sql.tablesql import (
    AlterGrants,
    InsertMetaType,
    RecordUserAuditFunction,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
)
from uno.db.sql.graphsql import GraphSQLEmitter
from uno.qry.models import QueryPathModel, QueryValueModel, QueryModel


class QueryPathSQLConfig(SQLConfig):
    table = QueryPathModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        GraphSQLEmitter,
    ]


class QueryValueSQLConfig(SQLConfig):
    table = QueryValueModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class QuerySQLConfig(SQLConfig):
    table = QueryModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]
