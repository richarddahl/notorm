# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import VARCHAR

from uno.db.obj import UnoObj, meta_data, UnoTableDef
from uno.db.sql.table_sql_emitters import InsertPermission
from uno.db.graph import GraphNode, GraphEdge
from uno.config import settings


class MetaType(UnoObj):
    table_def = UnoTableDef(
        table_name="meta_type",
        meta_data=meta_data,
        args=[
            Column("id", VARCHAR(63), primary_key=True, unique=True, index=True),
        ],
    )
    include_in_api_docs = False
    sql_emitters = [InsertPermission]

    id: str


class MetaRecord(UnoObj):
    table_def = UnoTableDef(
        table_name="meta_record",
        meta_data=meta_data,
        args=[
            Column(
                "id",
                VARCHAR(26),
                primary_key=True,
            ),
            Column(
                "meta_type_id",
                ForeignKey("meta_type.id", ondelete="CASCADE"),
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
