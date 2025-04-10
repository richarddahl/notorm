# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sql.config import SQLConfig
from uno.sql.emitters.table import (
    AlterGrants,
    InsertMetaType,
    RecordUserAuditFunction,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
)
from uno.sql.emitters.graph import GraphSQLEmitter
from uno.reports.objs import (
    ReportFieldConfigModel,
    ReportFieldModel,
    ReportTypeModel,
    ReportModel,
)


class ReportFieldConfSQLConfig(SQLConfig):
    table = ReportFieldConfigModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        GraphSQLEmitter,
    ]


class ReportFielSQLConfig(SQLConfig):
    table = ReportFieldModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportTypeSQLConfig(SQLConfig):
    table = ReportTypeModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportSQLConfig(SQLConfig):
    table = ReportModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]
