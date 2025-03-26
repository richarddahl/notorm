# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.table_sql_emitters import AlterGrants, InsertMetaType
from uno.db.sql.db_sql_emitters import (
    RecordUserAuditFunction,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
)
from uno.db.sql.sql_config import SQLConfig
from uno.db.sql.graph_sql_emitter import GraphSQLEmitter
from uno.pkgs.attr.bases import (
    attribute__value,
    attribute_type___meta_type,
    attribute_type__value_type,
    AttributeBase,
    AttributeTypeBase,
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
    table = AttributeBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class AttributeTypeSQLConfig(SQLConfig):
    table = AttributeTypeBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]
