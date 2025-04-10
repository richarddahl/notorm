# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, List
from typing_extensions import Self
from pydantic import EmailStr, model_validator

from uno.enums import SQLOperation, TenantType
from uno.schema import UnoSchemaConfig
from uno.obj import UnoObj
from uno.mixins import ObjectMixin
from uno.auth.mixins import RecordAuditObjectMixin
from uno.auth.models import (
    UserModel,
    GroupModel,
    ResponsibilityRoleModel,
    RoleModel,
    TenantModel,
    PermissionModel,
)


class User(UnoObj[UserModel], ObjectMixin, RecordAuditObjectMixin):
    # Class variables
    model = UserModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
                "default_group",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "email",
                "handle",
                "full_name",
                "tenant_id",
                "default_group_id",
                "is_superuser",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    email: EmailStr = None
    handle: str = None
    full_name: str = None
    tenant: Optional["Tenant"] = None
    tenant_id: Optional[str] = None
    default_group: Optional["Group"] = None
    default_group_id: Optional[str] = None
    is_superuser: bool = False

    # roles: Optional[List["Role"]] = None
    # created_objects: Optional[List[MetaRecordModel]] = None
    # modified_objects: Optional[List[MetaRecordModel]] = None
    # deleted_objects: Optional[List[MetaRecordModel]] = None

    def __str__(self) -> str:
        return self.handle

    @model_validator(mode="after")
    def validate_user(self) -> Self:
        # Add any custom validation logic here
        return self


class Group(UnoObj[GroupModel], RecordAuditObjectMixin):
    # Class variables
    model = GroupModel

    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "tenant_id",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    id: Optional[str]
    name: str
    tenant_id: Optional[str]
    tenant: Optional["Tenant"]

    # roles: List["Role"] = []
    # default_users: List[User] = []
    # members: List[User] = []

    def __str__(self) -> str:
        return self.name


class ResponsibilityRole(UnoObj[ResponsibilityRoleModel], RecordAuditObjectMixin):
    # Class variables
    model = ResponsibilityRoleModel

    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
                "tenant_id",
            ],
        ),
    }

    # Fields
    name: str
    description: Optional[str]
    tenant_id: Optional[str]
    tenant: Optional["Tenant"]

    def __str__(self) -> str:
        return self.name


class Role(UnoObj[RoleModel], RecordAuditObjectMixin):
    # Class variables
    model = RoleModel

    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    id: Optional[str]
    name: str
    description: Optional[str]
    tenant_id: Optional[str]
    tenant: Optional["Tenant"]

    def __str__(self) -> str:
        return self.name


class Tenant(UnoObj[TenantModel], RecordAuditObjectMixin):
    # Class variables
    model = TenantModel

    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "tenant_type",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    id: Optional[str]
    name: str
    tenant_type: TenantType

    # users: List["User"] = []
    # groups: List["Group"] = []
    # roles: List["Role"] = []

    def __str__(self) -> str:
        return self.name


class Permission(UnoObj[PermissionModel]):
    # Class variables
    model = PermissionModel
    endpoints = ["List", "View"]
    schema_configs = {"view_schema": UnoSchemaConfig()}
    terminate_filters = True

    # Fields
    id: Optional[int]
    meta_type_id: str
    operation: SQLOperation

    def __str__(self) -> str:
        return f"{self.meta_type.id}:  {self.operation}"
