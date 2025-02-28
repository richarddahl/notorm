# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import VARCHAR

from pydantic.fields import Field

from uno.db.obj import (
    UnoObj,
    UnoTableDef,
    meta_data,
)
from uno.db.rel_obj import UnoRelObj
from uno.db.mixins import GeneralMixin
from uno.config import settings


class InventoryCategory(UnoObj, GeneralMixin):
    table_def = UnoTableDef(
        table_name="inventory_category",
        meta_data=meta_data,
        args=[
            Column(
                "id",
                VARCHAR(26),
                primary_key=True,
                nullable=True,
                index=True,
            ),
            Column(
                "name",
                VARCHAR(255),
            ),
            Column(
                "description",
                VARCHAR,
            ),
            Column(
                "lot_prefix",
                VARCHAR(24),
            ),
            Column(
                "parent_id",
                VARCHAR(26),
            ),
        ],
    )

    # Class Variables
    sql_emitters = []
    schema_defs = inventory_category_schema_defs
    exclude_from_properties = []
    related_objects = inventory_category_rel_objs

    # BaseModel Fields
    name: str = Field(..., serialization_alias="Name")
    description: str = Field(..., serialization_alias="Description")
    lot_prefix: Optional[str] = Field(None, serialization_alias="Lot Prefix")
    parent_id: Optional[str] = Field(None, serialization_alias="Parent")
    tenant_id: Optional[str | UnoRelObj] = Field(None, serialization_alias="Tenant")
    group_id: Optional[str | UnoRelObj] = Field(None, serialization_alias="Group")
    id: Optional[str] = None

    def __str__(self) -> str:
        return self.handle
