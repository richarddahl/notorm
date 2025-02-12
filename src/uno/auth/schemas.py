# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import ClassVar

from pydantic import BaseModel

from uno.db.enums import SchemaDataType
from uno.db.schemas import (
    SchemaDef,
    ListSchema,
    SelectSchema,
    CreateSchema,
    UpdateSchema,
    DeleteSchema,
)

from uno.db.routers import RouterDef
from uno.auth.enums import TenantType


class UserCreateSchemaDef(SchemaDef):
    name: str = "UserCreate"
    table_name: str = "uno.user"
    doc: str = "Schema to Create a new User into the database"
    base: type[BaseModel] = CreateSchema
    data_type: SchemaDataType = SchemaDataType.NATIVE
    exclude_fields: list[str] = [
        "id",
        "created_at",
        "owner_id",
        "modified_at",
        "modified_by_id",
        "deleted_at",
        "deleted_by_id",
    ]
    router_def: ClassVar[RouterDef] = RouterDef(
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


class UserListShemaDef(SchemaDef):
    name: str = "UserList"
    table_name: str = "uno.user"
    doc: str = "Schema to list Users from the database"
    base: type[BaseModel] = ListSchema
    data_type: SchemaDataType = SchemaDataType.HTML
    include_fields: list[str] = ["id", "email", "handle", "full_name", "is_active"]
    router_def: ClassVar[RouterDef] = RouterDef(
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


class UserSelectSchemaDef(SchemaDef):
    name: str = "UserSelect"
    table_name: str = "uno.user"
    doc: str = "Schema to select a User from the database"
    base: type[BaseModel] = SelectSchema
    data_type: SchemaDataType = SchemaDataType.NATIVE
    exclude_fields: list[str] = []
    router_def: ClassVar[RouterDef] = RouterDef(
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


class UserUpdateSchemaDef(SchemaDef):
    name: str = "UserUpdate"
    table_name: str = "uno.user"
    doc: str = "Schema to update a User in the database"
    base: type[BaseModel] = UpdateSchema
    data_type: SchemaDataType = SchemaDataType.NATIVE
    exclude_fields: list[str] = [
        "id",
        "created_at",
        "modified_at",
        "modified_by_id",
        "deleted_at",
        "deleted_by_id",
    ]
    router_def: ClassVar[RouterDef] = RouterDef(
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


class UserDeleteSchemaDef(SchemaDef):
    name: str = "UserDelete"
    table_name: str = "uno.user"
    doc: str = "Schema to delete a User from the database"
    base: type[BaseModel] = DeleteSchema
    data_type: SchemaDataType = SchemaDataType.NATIVE
    include_fields: list[str] = ["id"]
    router_def: ClassVar[RouterDef] = RouterDef(
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


class UserImportSchemaDef(SchemaDef):
    name: str = "UserImport"
    table_name: str = "uno.user"
    doc: str = "Schema to import a User into the database"
    base: type[BaseModel] = DeleteSchema
    data_type: SchemaDataType = SchemaDataType.NATIVE
    router_def: ClassVar[RouterDef] = RouterDef(
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


"""
class TenantSchema(BaseModel):
    name: str
    tenant_type: TenantType

    tenant_users: list["UserSchema"]


class UserSchema(BaseModel):
    email: str
    handle: str
    full_name: str
    tenant_id: Optional[str]
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool
    created_at: datetime.datetime
    owner_id: Optional[str]
    modified_at: datetime.datetime
    modified_by_id: str
    deleted_at: Optional[datetime.datetime]
    deleted_by_id: Optional[str]

    tenant: Optional[TenantSchema]
    default_group: Optional["GroupSchema"]


class PermissionSchema(BaseModel):
    object_type_id: str
    operations: list[SQLOperation]

    object_type: ObjectType


class RoleSchema(BaseModel):
    tenant_id: str
    name: str
    description: str

    tenant: TenantSchema


class RolePermissionSchema(BaseModel):
    role_id: str
    permission_id: str


class GroupSchema(BaseModel):
    tenant_id: str
    name: str
    users_default_group: list["UserSchema"]


class UserGroupSchema(BaseModel):
    user_id: str
    group_id: str
    role_id: str

"""
