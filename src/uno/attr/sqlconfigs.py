# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.classes import SQLConfig
from uno.db.sql.tablesql import (
    AlterGrants,
    InsertMetaType,
    InsertMetaRecordTrigger,
    RecordUserAuditFunction,
    RecordStatusFunction,
)

from uno.db.sql.graphsql import GraphSQLEmitter

from uno.attr.models import (
    attribute__value,
    attribute_type___meta_type,
    attribute_type__value_type,
    AttributeModel,
    AttributeTypeModel,
)


class AttributeValueSQLConfig(SQLConfig):
    table = attribute__value
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class AttributeTypeMetaTypeSQLConfig(SQLConfig):
    table = attribute_type___meta_type
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class AttributeTypeValueTypeSQLConfig(SQLConfig):
    table = attribute_type__value_type
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class AttributeSQLConfig(SQLConfig):
    table = AttributeModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class AttributeTypeSQLConfig(SQLConfig):
    table = AttributeTypeModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]
