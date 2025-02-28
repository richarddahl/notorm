# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import ClassVar, Any, Optional

from sqlalchemy import Column, ForeignKeyConstraint, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import VARCHAR, BOOLEAN, TIMESTAMP

from pydantic import BaseModel, ConfigDict
from pydantic.fields import Field

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
from uno.config import settings


class ColumnDef(BaseModel):
    args: list[Any] = []
    kwargs: dict[str, Any] = {}

    def create_column(self) -> None:
        return Column(*self.args, **self.kwargs)


class UnoMixinCKConstraint(BaseModel):
    sqltext: str
    name: str
    initially: Optional[str] = None
    info: Optional[dict[str, Any]] = None

    def create_constraint(self) -> None:
        return CheckConstraint(
            sqltext=self.sqltext,
            name=self.name,
            initially=self.initially,
            info=self.info,
        )


class UnoMixinUQConstraint(BaseModel):
    columns: list[str]
    name: str
    defferable: Optional[str] = None
    initially: Optional[str] = None

    def create_constraint(self) -> None:
        return UniqueConstraint(
            *self.columns,
            name=self.name,
            defferable=self.defferable,
            initially=self.initially,
        )


class UnoMixinFKConstraint(BaseModel):
    columns: list[str]
    ref_columns: list[str]
    name: str

    def create_constraint(self) -> None:
        return ForeignKeyConstraint(self.columns, self.ref_columns, name=self.name)


class UnoMixin(BaseModel):
    """Base class for all database table mixins"""

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    column_defs: ClassVar[list[ColumnDef]] = []
    constraint_defs: ClassVar[
        list[ForeignKeyConstraint | CheckConstraint | UniqueConstraint]
    ] = []

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

    is_active: bool = Field(True, serialization_alias="Is Active")
    is_deleted: bool = Field(False, serialization_alias="Is Deleted")
    created_at: Optional[datetime.datetime] = Field(
        None, serialization_alias="Created At"
    )
    modified_at: Optional[datetime.datetime] = Field(
        None, serialization_alias="Modified At"
    )
    deleted_at: Optional[datetime.datetime] = Field(
        None,
        serialization_alias="Deleted At",
    )


class RecordUserAuditMixin(UnoMixin):

    sql_emitters = [RecordUserAuditFunction]

    column_defs = [
        ColumnDef(
            args=["created_by_id", VARCHAR(26)],
            kwargs={
                "nullable": False,
                "doc": "User that created the record",
            },
        ),
        ColumnDef(
            args=["modified_by_id", VARCHAR(26)],
            kwargs={
                "nullable": False,
                "doc": "User that last modified the record",
            },
        ),
        ColumnDef(
            args=["deleted_by_id", VARCHAR(26)],
            kwargs={
                "nullable": True,
                "doc": "User that deleted the record",
            },
        ),
    ]

    constraint_defs = [
        UnoMixinFKConstraint(
            columns=["created_by_id"],
            ref_columns=["user.id"],
            name="fk_created_by_id",
        ),
        UnoMixinFKConstraint(
            columns=["modified_by_id"],
            ref_columns=["user.id"],
            name="fk_modified_by_id",
        ),
        UnoMixinFKConstraint(
            columns=["deleted_by_id"],
            ref_columns=["user.id"],
            name="fk_deleted_by_id",
        ),
    ]

    created_by_id: Optional[str] = Field(None, serialization_alias="Created By")
    modified_by_id: Optional[str] = Field(None, serialization_alias="Modified By")
    deleted_by_id: Optional[str] = Field(None, serialization_alias="Deleted By")


class GeneralMixin(
    InsertMetaRecordMixin,
    RecordStatusMixin,
    RecordUserAuditMixin,
):
    """Mixin for General Objects"""

    column_defs = []
    sql_emitters = []
