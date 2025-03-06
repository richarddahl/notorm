# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, Union

from pydantic import EmailStr
from pydantic.fields import Field

from uno.record.enums import SQLOperation
from uno.model.schema import UnoSchemaConfig
from uno.model.model import UnoModel
from uno.model.mixins import GeneralModelMixin
from uno.apps.meta.models import MetaRecord
from uno.apps.auth.enums import TenantType
from uno.apps.auth.model_mixins import ModelAuditMixin
from uno.config import settings


class User(UnoModel, GeneralModelMixin, ModelAuditMixin):
    # Class variables
    table_name = "user"
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "id",
                "email",
                "handle",
                "full_name",
                "tenant",
                "group",
                "is_superuser",
                "default_group",
            ],
        ),
        "summary_schema": UnoSchemaConfig(
            include_fields=[
                "id",
                "handle",
            ],
        ),
    }

    id: Optional[str] = None
    email: EmailStr
    handle: str
    full_name: str
    tenant: Optional[Union["Tenant", str]] = Field(None, alias="tenant_id")
    default_group: Optional[Union["Group", str]] = Field(None, alias="default_group_id")
    group: Optional[Union["Group", str]] = Field(None, alias="group_id")
    is_superuser: bool = False

    # roles: Optional[list["Role"]] = None
    # created_objects: Optional[list[MetaRecord]] = None
    # modified_objects: Optional[list[MetaRecord]] = None
    # deleted_objects: Optional[list[MetaRecord]] = None

    def __str__(self) -> str:
        return self.handle


class Group(UnoModel, GeneralModelMixin, ModelAuditMixin):
    # Class variables
    table_name = "group"

    id: Optional[str]
    name: str
    tenant: Optional["Tenant"]

    # roles: list["Role"] = []
    # default_users: list[User] = []
    # members: list[User] = []

    def __str__(self) -> str:
        return self.name


class Role(UnoModel, GeneralModelMixin, ModelAuditMixin):
    # Class variables
    table_name = "role"

    id: Optional[str]
    name: str
    description: Optional[str]
    tenant: Optional["Tenant"]

    def __str__(self) -> str:
        return self.name


class Tenant(UnoModel, GeneralModelMixin, ModelAuditMixin):
    # Class variables
    table_name = "tenant"

    id: Optional[str]
    name: str
    tenant_type: TenantType

    # users: list["User"] = []
    # groups: list["Group"] = []
    # roles: list["Role"] = []

    def __str__(self) -> str:
        return self.name


class Permission(UnoModel):
    # Class variables
    table_name = "permission"

    id: Optional[int]
    meta_type_id: str
    operation: SQLOperation

    def __str__(self) -> str:
        return f"{self.meta_type.name}:  {self.operation}"
