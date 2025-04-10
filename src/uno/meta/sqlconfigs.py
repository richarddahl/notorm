# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.sql.config import SQLConfig
from uno.sql.emitters.graph import GraphSQLEmitter
from uno.sql.emitters.table import (
    AlterGrants,
    InsertMetaType,
    InsertPermission,
)
from uno.meta.models import MetaTypeModel, MetaRecordModel


class MetaTypeSQLConfig(SQLConfig):
    """SQL configuration for the MetaType table.
    
    This class defines the SQL emitters used for the MetaType table,
    which is a special table that stores information about all entity types.
    """
    table = MetaTypeModel.__table__
    default_emitters = [
        AlterGrants,
        InsertPermission,
        InsertMetaType,
        # Commenting out GraphSQLEmitter temporarily to isolate issue
        # GraphSQLEmitter,
    ]


class MetaSQLConfig(SQLConfig):
    table = MetaRecordModel.__table__
    default_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]
