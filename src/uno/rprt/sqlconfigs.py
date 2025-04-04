# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sqlemitter import (
    AlterGrants,
    InsertMetaType,
    RecordUserAuditFunction,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
    SQLConfig,
)
from uno.graphsql import GraphSQLEmitter
from uno.rprt.bases import (
    ReportFieldConfigBase,
    ReportFieldBase,
    ReportTypeBase,
    ReportBase,
)


class ReportFieldConfSQLConfig(SQLConfig):
    table = ReportFieldConfigBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        GraphSQLEmitter,
    ]


class ReportFielSQLConfig(SQLConfig):
    table = ReportFieldBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportTypeSQLConfig(SQLConfig):
    table = ReportTypeBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportSQLConfig(SQLConfig):
    table = ReportBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]
