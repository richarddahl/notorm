# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import ClassVar, Any, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import VARCHAR, BOOLEAN, TIMESTAMP

from pydantic import BaseModel, ConfigDict

from uno.db.sql.sql_emitter import SQLEmitter
from uno.db.sql.table_sql_emitters import (
    InsertMetaRecordTrigger,
    RecordVersionAudit,
    CreateHistoryTable,
    InsertHistoryTableRecord,
    RecordUserAuditFunction,
    RecordStatusFunction,
    RecordUserAuditFunction,
)
from uno.db.graph import Edge
from uno.config import settings


class ColumnDef(BaseModel):
    args: list[Any] = []
    kwargs: dict[str, Any] = {}

    def create_column(self) -> None:
        return Column(*self.args, **self.kwargs)


class UnoMixin(BaseModel):
    """Base class for all database table mixins"""

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    column_defs: ClassVar[list[ColumnDef]] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RecordVersionAuditMixin(UnoMixin):
    """Mixin for recording version history of a record"""

    sql_emitters = [RecordVersionAudit]


class HistoryTableAuditMixin(UnoMixin):
    """Mixin for recording history of a table"""

    sql_emitters = [CreateHistoryTable, InsertHistoryTableRecord]


class InsertMetaRecordMixin(UnoMixin):
    """Mixin for MetaRecord Objects"""

    sql_emitters = [InsertMetaRecordTrigger]


class RecordStatusMixin(UnoMixin):
    sql_emitters = [RecordStatusFunction]

    column_defs = [
        ColumnDef(
            args=["is_active", BOOLEAN],
            kwargs={
                "nullable": False,
                "doc": "Is the record active",
            },
        ),
        ColumnDef(
            args=["is_deleted", BOOLEAN],
            kwargs={
                "nullable": False,
                "doc": "Is the record deleted",
            },
        ),
        ColumnDef(
            args=["created_at", TIMESTAMP],
            kwargs={
                "nullable": False,
                "doc": "Time the record was created",
            },
        ),
        ColumnDef(
            args=["modified_at", TIMESTAMP],
            kwargs={
                "nullable": False,
                "doc": "Time the record was last modified",
            },
        ),
        ColumnDef(
            args=["deleted_at", TIMESTAMP],
            kwargs={
                "nullable": True,
                "doc": "Time the record was deleted",
            },
        ),
    ]

    is_active: bool = True
    is_deleted: bool = False
    created_at: Optional[datetime.datetime] = None
    modified_at: Optional[datetime.datetime] = None
    deleted_at: Optional[datetime.datetime] = None


class RecordUserAuditMixin(UnoMixin):

    sql_emitters = [RecordUserAuditFunction]

    column_defs = [
        ColumnDef(
            args=["created_by_id", VARCHAR(26)],
            kwargs={
                "nullable": False,
                "index": True,
            },
        ),
        ColumnDef(
            args=["modified_by_id", VARCHAR(26)],
            kwargs={
                "nullable": False,
                "index": True,
            },
        ),
        ColumnDef(
            args=["deleted_by_id", VARCHAR(26)],
            kwargs={
                "index": True,
                "nullable": True,
            },
        ),
    ]

    created_by_id: Optional[str] = None
    modified_by_id: Optional[str] = None
    deleted_by_id: Optional[str] = None


class GeneralMixin(InsertMetaRecordMixin, RecordStatusMixin, RecordUserAuditMixin):
    """Mixin for General Objects"""

    column_defs = []
    sql_emitters = []
