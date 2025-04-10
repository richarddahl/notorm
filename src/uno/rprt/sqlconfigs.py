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
from uno.rprt.objs import (
    ReportFieldConfigModel,
    ReportFieldModel,
    ReportTypeModel,
    ReportModel,
)


class ReportFieldConfSQLConfig(SQLConfig):
    table = ReportFieldConfigModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        GraphSQLEmitter,
    ]


class ReportFielSQLConfig(SQLConfig):
    table = ReportFieldModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportTypeSQLConfig(SQLConfig):
    table = ReportTypeModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportSQLConfig(SQLConfig):
    table = ReportModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]
