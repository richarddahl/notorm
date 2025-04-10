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
from uno.values.objs import (
    AttachmentModel,
    BooleanValueModel,
    DateTimeValueModel,
    DateValueModel,
    DecimalValueModel,
    IntegerValueModel,
    TextValueModel,
    TimeValueModel,
)


class AttachmentSQLConfig(SQLConfig):
    table = AttachmentModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class BooleanValueSQLConfig(SQLConfig):
    table = BooleanValueModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class DateTimeValueSQLConfig(SQLConfig):
    table = DateTimeValueModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class DateValueSQLConfig(SQLConfig):
    table = DateValueModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class DecimalValueSQLConfig(SQLConfig):
    table = DecimalValueModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class IntegerValueSQLConfig(SQLConfig):
    table = IntegerValueModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class TextValueSQLConfig(SQLConfig):
    table = TextValueModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class TimeValueSQLConfig(SQLConfig):
    table = TimeValueModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]
