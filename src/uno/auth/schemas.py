# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import ClassVar

from pydantic import BaseModel

from uno.db.enums import SchemaDataType
from uno.schemas import (
    Schema,
    ListSchema,
    SelectSchema,
    CreateSchema,
    UpdateSchema,
    DeleteSchema,
)

from uno.routers import Router
from uno.auth.enums import TenantType


class UserCreateSchema(Schema):
    name: ClassVar[str] = "UserCreate"
    table_name: ClassVar[str] = "uno.user"
    doc: ClassVar[str] = "Schema to Create a new User into the database"
    base: ClassVar[type[BaseModel]] = CreateSchema
    data_type: ClassVar[SchemaDataType] = SchemaDataType.NATIVE
    exclude_fields: ClassVar[list[str]] = [
        "id",
        "created_at",
        "owner_id",
        "modified_at",
        "modified_by_id",
        "deleted_at",
        "deleted_by_id",
    ]
    router_def: ClassVar[Router] = Router(
        path_suffix="",
        path_objs="/user",
        method="POST",
        endpoint="post",
        multiple=False,
        include_in_schema=True,
        summary="Create a new User",
        description="Insert a new User into the database",
        tags=["auth"],
    )


class UserListSchema(Schema):
    name: ClassVar[str] = "UserList"
    table_name: ClassVar[str] = "uno.user"
    doc: ClassVar[str] = "Schema to list Users from the database"
    base: ClassVar[type[BaseModel]] = ListSchema
    data_type: ClassVar[SchemaDataType] = SchemaDataType.HTML
    include_fields: ClassVar[list[str]] = [
        "id",
        "email",
        "handle",
        "full_name",
        "is_active",
    ]
    router_def: ClassVar[Router] = Router(
        path_suffix="",
        path_objs="/user",
        method="GET",
        endpoint="get",
        multiple=True,
        include_in_schema=True,
        summary="Select list of Users",
        description="Select a list of Users from the database",
        tags=["auth"],
    )


class UserSelectSchema(Schema):
    name: ClassVar[str] = "UserSelect"
    table_name: ClassVar[str] = "uno.user"
    doc: ClassVar[str] = "Schema to select a User from the database"
    base: ClassVar[type[BaseModel]] = SelectSchema
    data_type: ClassVar[SchemaDataType] = SchemaDataType.NATIVE
    exclude_fields: ClassVar[list[str]] = []
    router_def: ClassVar[Router] = Router(
        path_suffix="/{id}",
        path_objs="/user",
        method="GET",
        endpoint="get_by_id",
        multiple=False,
        include_in_schema=True,
        summary="Select a User",
        description="Select a User from the database",
        tags=["auth"],
    )


class UserUpdateSchema(Schema):
    name: ClassVar[str] = "UserUpdate"
    table_name: ClassVar[str] = "uno.user"
    doc: ClassVar[str] = "Schema to update a User in the database"
    base: ClassVar[type[BaseModel]] = UpdateSchema
    data_type: ClassVar[SchemaDataType] = SchemaDataType.NATIVE
    exclude_fields: ClassVar[list[str]] = [
        "id",
        "created_at",
        "modified_at",
        "modified_by_id",
        "deleted_at",
        "deleted_by_id",
    ]
    router_def: ClassVar[Router] = Router(
        path_suffix="/{id}",
        path_objs="/user",
        method="PATCH",
        endpoint="patch",
        multiple=False,
        include_in_schema=True,
        summary="Update a User",
        description="Update a User in the database",
        tags=["auth"],
    )


class UserDeleteSchema(Schema):
    name: ClassVar[str] = "UserDelete"
    table_name: ClassVar[str] = "uno.user"
    doc: ClassVar[str] = "Schema to delete a User from the database"
    base: ClassVar[type[BaseModel]] = DeleteSchema
    data_type: ClassVar[SchemaDataType] = SchemaDataType.NATIVE
    include_fields: ClassVar[list[str]] = ["id"]
    router_def: ClassVar[Router] = Router(
        path_suffix="/{id}",
        path_objs="/user",
        method="DELETE",
        endpoint="delete",
        multiple=False,
        include_in_schema=True,
        summary="Delete a User",
        description="Delete a User from the database",
        tags=["auth"],
    )


class UserImportSchema(Schema):
    name: ClassVar[str] = "UserImport"
    table_name: ClassVar[str] = "uno.user"
    doc: ClassVar[str] = "Schema to import a User into the database"
    base: ClassVar[type[BaseModel]] = DeleteSchema
    data_type: ClassVar[SchemaDataType] = SchemaDataType.NATIVE
    router_def: ClassVar[Router] = Router(
        path_suffix="/{id}",
        path_objs="/user",
        method="PUT",
        endpoint="put",
        multiple=False,
        include_in_schema=True,
        summary="Import a User",
        description="Import a User into the database",
        tags=["auth"],
    )
