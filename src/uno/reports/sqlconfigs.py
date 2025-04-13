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
from uno.reports.models import (
    # Original models
    ReportFieldConfigModel,
    ReportFieldModel,
    ReportTypeModel,
    ReportModel,
    # Enhanced models
    ReportTemplateModel,
    ReportFieldDefinitionModel,
    ReportTriggerModel,
    ReportOutputModel,
    ReportExecutionModel,
    ReportOutputExecutionModel,
)


# Original model SQL configs (for backward compatibility)

class ReportFieldConfSQLConfig(SQLConfig):
    table = ReportFieldConfigModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        GraphSQLEmitter,
    ]


class ReportFieldSQLConfig(SQLConfig):
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


# Enhanced model SQL configs

class ReportTemplateSQLConfig(SQLConfig):
    table = ReportTemplateModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportFieldDefinitionSQLConfig(SQLConfig):
    table = ReportFieldDefinitionModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportTriggerSQLConfig(SQLConfig):
    table = ReportTriggerModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportOutputSQLConfig(SQLConfig):
    table = ReportOutputModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportExecutionSQLConfig(SQLConfig):
    table = ReportExecutionModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class ReportOutputExecutionSQLConfig(SQLConfig):
    table = ReportOutputExecutionModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]