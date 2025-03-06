# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field, EmailStr

from uno.api.endpoint import UnoModel


class UserImport(UnoModel):
    uno_record = BaseModel
    modelname = "import_model"

    id: str
    handle: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_deleted: bool
    is_superuser: bool
    tenant_id: Optional[str]
    default_group_id: Optional[str]
    created_at: datetime
    created_by_id: str
    modified_at: datetime
    modified_by_id: str
    deleted_at: Optional[datetime]
    deleted_by_id: Optional[str]

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class UserView(UnoModel):
    uno_record = BaseModel
    modelname = "view_model"

    id: str = Field(None, title="ID")
    handle: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_deleted: bool
    is_superuser: bool
    tenant_id: Optional["TenantSummary"] = None
    default_group_id: Optional["GroupSummary"] = None
    created_at: datetime
    created_by_id: "UserSummary"
    modified_at: datetime
    modified_by_id: "UserSummary"
    deleted_at: Optional[datetime]
    deleted_by_id: Optional["UserSummary"] = None

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class UserEdit(UnoModel):
    uno_record = BaseModel
    modelname = "edit_model"

    email: EmailStr
    handle: str
    full_name: str
    tenant_id: Optional[str] = None
    default_group_id: Optional[str] = None
    is_superuser: bool = False

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class UserSummary(UnoModel):
    uno_record = BaseModel
    modelname = "summary_model"

    id: str
    handle: str
    is_active: bool

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class TenantImport(UnoModel):
    uno_record = BaseModel
    modelname = "import_model"

    id: str
    name: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by_id: str
    modified_at: datetime
    modified_by_id: str
    deleted_at: Optional[datetime]
    deleted_by_id: Optional[str]

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class TenantView(UnoModel):
    uno_record = BaseModel
    modelname = "view_model"

    id: str = Field(None, title="ID")
    name: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by_id: UserSummary
    modified_at: datetime
    modified_by_id: UserSummary
    deleted_at: Optional[datetime]
    deleted_by_id: Optional[UserSummary]

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class TenantEdit(UnoModel):
    uno_record = BaseModel
    modelname = "edit_model"

    name: str
    is_active: bool = True

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class TenantSummary(UnoModel):
    uno_record = BaseModel
    modelname = "summary_model"

    id: str
    name: str
    is_active: bool

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class GroupImport(UnoModel):
    uno_record = BaseModel
    modelname = "import_model"

    id: str
    name: str
    tenant_id: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by_id: str
    modified_at: datetime
    modified_by_id: str
    deleted_at: Optional[datetime]
    deleted_by_id: Optional[str]

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class GroupView(UnoModel):
    uno_record = BaseModel
    modelname = "view_model"

    id: str = Field(None, title="ID")
    name: str
    tenant: TenantSummary
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by_id: UserSummary
    modified_at: datetime
    modified_by_id: UserSummary
    deleted_at: Optional[datetime]
    deleted_by_id: Optional[UserSummary]

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class GroupEdit(UnoModel):
    uno_record = BaseModel
    modelname = "edit_model"

    name: str
    tenant_id: str
    is_active: bool = True

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class GroupSummary(UnoModel):
    uno_record = BaseModel
    modelname = "summary_model"

    id: str
    name: str
    is_active: bool

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class RoleImport(UnoModel):
    uno_record = BaseModel
    modelname = "import_model"

    id: str
    name: str
    tenant_id: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by_id: str
    modified_at: datetime
    modified_by_id: str
    deleted_at: Optional[datetime]
    deleted_by_id: Optional[str]

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class RoleView(UnoModel):
    uno_record = BaseModel
    modelname = "view_model"

    id: str = Field(None, title="ID")
    name: str
    tenant: TenantSummary
    is_active: bool
    is_deleted: bool
    created_at: datetime
    created_by_id: UserSummary
    modified_at: datetime
    modified_by_id: UserSummary
    deleted_at: Optional[datetime]
    deleted_by_id: Optional[UserSummary]

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class RoleEdit(UnoModel):
    uno_record = BaseModel
    modelname = "edit_model"

    name: str
    tenant_id: str
    is_active: bool = True

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass


class RoleSummary(UnoModel):
    uno_record = BaseModel
    modelname = "summary_model"

    id: str
    name: str
    is_active: bool

    def before_db_operation(self):
        pass

    def after_db_operation(self):
        pass
