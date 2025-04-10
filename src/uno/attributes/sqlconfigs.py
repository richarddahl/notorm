# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sql.config import SQLConfig
from uno.sql.emitters.table import (
    AlterGrants,
    InsertMetaType,
    InsertMetaRecordTrigger,
    RecordUserAuditFunction,
    RecordStatusFunction,
)
from uno.sql.emitters.graph import GraphSQLEmitter
from uno.attributes.models import (
    attribute__value,
    attribute_type___meta_type,
    attribute_type__value_type,
    AttributeModel,
    AttributeTypeModel,
)


class AttributeValueSQLConfig(SQLConfig):
    table = attribute__value
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class AttributeTypeMetaTypeSQLConfig(SQLConfig):
    table = attribute_type___meta_type
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class AttributeTypeValueTypeSQLConfig(SQLConfig):
    table = attribute_type__value_type
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class AttributeSQLConfig(SQLConfig):
    table = AttributeModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class AttributeTypeSQLConfig(SQLConfig):
    table = AttributeTypeModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]
