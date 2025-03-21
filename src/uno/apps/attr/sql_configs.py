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
from uno.db.sql.graph_sql_emitters import NodeSQLEmitter
from uno.apps.attr.models import Attribute, AttributeType


class AttributeSQLConfig(SQLConfig):
    table_name = "attribute"
    model = Attribute
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        NodeSQLEmitter,
    ]


class AttributeTypeSQLConfig(SQLConfig):
    table_name = "attribute_type"
    model = AttributeType
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        NodeSQLEmitter,
    ]
