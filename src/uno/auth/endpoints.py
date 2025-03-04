# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import status

from uno.app.endpoint import UnoEndpoint, UnoModel
from uno.app.routers import (
    UnoRouter,
    InsertRouter,
    SummaryRouter,
    SelectRouter,
    UpdateRouter,
    DeleteRouter,
    ImportRouter,
)
from uno.auth.models import (
    UserImport,
    UserView,
    UserEdit,
    UserSummary,
    TenantImport,
    TenantView,
    TenantEdit,
    TenantSummary,
    GroupImport,
    GroupView,
    GroupEdit,
    GroupSummary,
    RoleImport,
    RoleView,
    RoleEdit,
    RoleSummary,
)


class CreateUser(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoModel = UserEdit
    response_model: UnoModel = UserView
    status_code: int = status.HTTP_201_CREATED


class ViewUser(UnoEndpoint):
    router: UnoRouter = SelectRouter
    response_model: UnoModel = UserView
    body_model: UnoModel = None


class ViewUserSummary(UnoEndpoint):
    router: UnoRouter = SummaryRouter
    response_model: UnoModel = UserSummary
    body_model: UnoModel = None


class UpdateUser(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoModel = UserEdit
    response_model: UnoModel = UserView


class DeleteUser(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    response_model: UnoModel = UserView
    body_model: UnoModel = None


class ImportUser(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoModel = UserImport
    response_model: UnoModel = UserView


class CreateTenant(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoModel = TenantEdit
    response_model: UnoModel = TenantView
    status_code: int = status.HTTP_201_CREATED


class ViewTenant(UnoEndpoint):
    router: UnoRouter = SelectRouter
    response_model: UnoModel = TenantView
    body_model: UnoModel = None


class ViewTenantSummary(UnoEndpoint):
    router: UnoRouter = SummaryRouter
    response_model: UnoModel = TenantSummary
    body_model: UnoModel = None


class UpdateTenant(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoModel = TenantEdit
    response_model: UnoModel = TenantView


class DeleteTenant(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    response_model: UnoModel = TenantView
    body_model: UnoModel = None


class ImportTenant(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoModel = TenantImport
    response_model: UnoModel = TenantView


class CreateGroup(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoModel = GroupEdit
    response_model: UnoModel = GroupView
    status_code: int = status.HTTP_201_CREATED


class ViewGroup(UnoEndpoint):
    router: UnoRouter = SelectRouter
    response_model: UnoModel = GroupView
    body_model: UnoModel = None


class ViewGroupSummary(UnoEndpoint):
    router: UnoRouter = SummaryRouter
    response_model: UnoModel = GroupSummary
    body_model: UnoModel = None


class UpdateGroup(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoModel = GroupEdit
    response_model: UnoModel = GroupView


class DeleteGroup(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    response_model: UnoModel = GroupView
    body_model: UnoModel = None


class ImportGroup(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoModel = GroupImport
    response_model: UnoModel = GroupView


class CreateRole(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoModel = RoleEdit
    response_model: UnoModel = RoleView
    status_code: int = status.HTTP_201_CREATED


class ViewRole(UnoEndpoint):
    router: UnoRouter = SelectRouter
    response_model: UnoModel = RoleView
    body_model: UnoModel = None


class ViewRoleSummary(UnoEndpoint):
    router: UnoRouter = SummaryRouter
    response_model: UnoModel = RoleSummary
    body_model: UnoModel = None


class UpdateRole(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoModel = RoleEdit
    response_model: UnoModel = RoleView


class DeleteRole(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    response_model: UnoModel = RoleView
    body_model: UnoModel = None


class ImportRole(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoModel = RoleImport
    response_model: UnoModel = RoleView
