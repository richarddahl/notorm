# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import enum

from typing import Optional, ClassVar

from sqlalchemy import Table, Column
from sqlalchemy.sql.expression import Join, join, Alias

from psycopg.sql import SQL, Identifier

from pydantic import BaseModel, computed_field, field_validator

from uno.db.obj import UnoObj
from uno.db.enums import RelType
from uno.utilities import create_random_alias
from uno.config import settings


class UnoRelObj(BaseModel):
    table: ClassVar[Optional[Table]]  # Provided by UnoOBj during initialization
    table_alias: ClassVar[Alias]  # Provided by UnoOBj during initialization

    column: ClassVar[str]
    remote_table: ClassVar[str]
    remote_column: ClassVar[str]
    join_table: ClassVar[str] = None
    rel_type: ClassVar[RelType] = RelType.ONE_TO_MANY
    pre_fetch: ClassVar[bool] = True

    edge_label: ClassVar[Optional[str]] = None

    remote_table_alias: ClassVar[str] = None
    loc_column_alias: ClassVar[Column] = None
    rem_column_alias: ClassVar[Column] = None
    schema_name: ClassVar[str] = "list"
    join: ClassVar[Join] = None
    schema: ClassVar[BaseModel] = None
    rel_obj_class: ClassVar[BaseModel] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_obj()
        self.set_schema()
        self.create_join()

    @classmethod
    def set_obj(cls) -> BaseModel:
        cls.rel_obj_class = UnoObj.registry[cls.remote_table]

    @classmethod
    def set_schema(cls) -> BaseModel:
        return getattr(cls.rel_obj_class, f"{cls.schema_name}_schema")

    @classmethod
    def create_join(cls) -> Join:
        rem_table = cls.table.metadata.tables[
            f"{settings.DB_SCHEMA}.{cls.remote_table}"
        ]
        cls.remote_table_alias = create_random_alias(
            rem_table,
            prexic=cls.rel_obj_class.__name__,
        )
        cls.rem_column = cls.remote_table_alias.columns[cls.remote_column]
        cls.loc_column = cls.table_alias.columns[cls.column]
        if cls.rel_type == RelType.MANY_TO_MANY:
            cls.join = join(
                cls.table_alias,
                cls.remote_table_alias,
                onclause=cls.loc_column == cls.rem_column,
                isouter=True,
            )
        cls.join = join(
            cls.table_alias,
            cls.remote_table_alias,
            onclause=cls.loc_column == cls.rem_column,
            isouter=True,
        )


class GroupRelObj(UnoRelObj):
    column = "group_id"
    remote_table = "group"
    remote_column = "id"
    rel_type = RelType.ONE_TO_MANY
    edge_label = "IS_ASSIGNED_TO"


class TenantRelObj(UnoRelObj):
    column = "tenant_id"
    remote_table = "tenant"
    remote_column = "id"
    edge_label = "IS_ASSIGNED_TO"
    rel_type = RelType.ONE_TO_MANY


class CreatedByRelObj(UnoRelObj):
    column = "created_by_id"
    remote_table = "user"
    remote_column = "id"
    edge_label = "CREATED_BY"
    rel_type = RelType.ONE_TO_MANY


class ModifiedByRelObj(UnoRelObj):
    column = "modified_by_id"
    remote_table = "user"
    remote_column = "id"
    edge_label = "MODIFIED_BY"
    rel_type = RelType.ONE_TO_MANY


class DeletedByRelObj(UnoRelObj):
    column = "deleted_by_id"
    remote_table = "user"
    remote_column = "id"
    edge_label = "DELETED_BY"
    rel_type = RelType.ONE_TO_MANY


general_rel_objs = {
    "group_id": GroupRelObj,
    "tenant_id": TenantRelObj,
    "created_by_id": CreatedByRelObj,
    "modified_by_id": ModifiedByRelObj,
    "deleted_by_id": DeletedByRelObj,
}
