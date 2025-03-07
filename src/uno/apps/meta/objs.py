# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import VARCHAR

from uno.record.obj import UnoRecord, meta_data, UnoTableDef
from uno.storage.sql.table_sql_emitters import InsertPermission
from uno.record.graph import GraphNode, GraphEdge
from uno.config import settings


class MetaType(UnoRecord):
    table_def = UnoTableDef(
        table_name="meta_type",
        meta_data=meta_data,
        args=[
            Column(
                "id",
                VARCHAR(63),
                primary_key=True,
                unique=True,
                index=True,
                nullable=False,
            ),
        ],
    )
    include_in_api_docs = False
    sql_emitters = [InsertPermission]

    id: str


class MetaRecord(UnoRecord):
    table_def = UnoTableDef(
        table_name="meta_record",
        meta_data=meta_data,
        args=[
            Column(
                "id",
                VARCHAR(26),
                primary_key=True,
                nullable=False,
                unique=True,
                index=True,
            ),
            Column(
                "meta_type_id",
                ForeignKey("meta_type.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
        ],
    )
    table_name = "meta_record"
    include_in_api_docs = False

    # BaseModel fields
    id: str
    meta_type_id: str

    def __str__(self) -> str:
        return f"{self.meta_type_id}"
