# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import status

from uno.api.endpoint import UnoEndpoint
from uno.model.schema import UnoSchema
from uno.model.model import UnoModel
from uno.api.router import (
    UnoRouter,
    InsertRouter,
    SummaryRouter,
    SelectRouter,
    UpdateRouter,
    DeleteRouter,
    ImportRouter,
)

# from uno.apps.auth.masks import (
#    UserImport,
#    UserView,
#    UserEdit,
#    UserSummary,
#    TenantImport,
#    TenantView,
#    TenantEdit,
#    TenantSummary,
#    GroupImport,
#    GroupView,
#    GroupEdit,
#    GroupSummary,
#    RoleImport,
#    RoleView,
#    RoleEdit,
#    RoleSummary,
# )


class CreateUser(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoSchema = "edit_schema"
    response_model: UnoSchema = "view_schema"
    status_code: int = status.HTTP_201_CREATED


class ViewUser(UnoEndpoint):
    router: UnoRouter = SelectRouter
    response_model: UnoSchema = "view_schema"
    body_model: UnoSchema = None


class ViewUserSummary(UnoEndpoint):
    router: UnoRouter = SummaryRouter
    response_model: UnoSchema = "summary_schema"
    body_model: UnoSchema = None


class UpdateUser(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoSchema = "edit_schema"
    response_model: UnoSchema = "view_schema"


class DeleteUser(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    response_model: UnoSchema = "view_schema"
    body_model: UnoSchema = None


"""
class CreateTenant(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoSchema = TenantEdit
    response_model: UnoSchema = TenantView
    status_code: int = status.HTTP_201_CREATED


class ViewTenant(UnoEndpoint):
    router: UnoRouter = SelectRouter
    response_model: UnoSchema = TenantView
    body_model: UnoSchema = None


class ViewTenantSummary(UnoEndpoint):
    router: UnoRouter = SummaryRouter
    response_model: UnoSchema = TenantSummary
    body_model: UnoSchema = None


class UpdateTenant(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoSchema = TenantEdit
    response_model: UnoSchema = TenantView


class DeleteTenant(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    response_model: UnoSchema = TenantView
    body_model: UnoSchema = None


class ImportTenant(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoSchema = TenantImport
    response_model: UnoSchema = TenantView


class CreateGroup(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoSchema = GroupEdit
    response_model: UnoSchema = GroupView
    status_code: int = status.HTTP_201_CREATED


class ViewGroup(UnoEndpoint):
    router: UnoRouter = SelectRouter
    response_model: UnoSchema = GroupView
    body_model: UnoSchema = None


class ViewGroupSummary(UnoEndpoint):
    router: UnoRouter = SummaryRouter
    response_model: UnoSchema = GroupSummary
    body_model: UnoSchema = None


class UpdateGroup(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoSchema = GroupEdit
    response_model: UnoSchema = GroupView


class DeleteGroup(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    response_model: UnoSchema = GroupView
    body_model: UnoSchema = None


class ImportGroup(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoSchema = GroupImport
    response_model: UnoSchema = GroupView


class CreateRole(UnoEndpoint):
    router: UnoRouter = InsertRouter
    body_model: UnoSchema = RoleEdit
    response_model: UnoSchema = RoleView
    status_code: int = status.HTTP_201_CREATED


class ViewRole(UnoEndpoint):
    router: UnoRouter = SelectRouter
    response_model: UnoSchema = RoleView
    body_model: UnoSchema = None


class ViewRoleSummary(UnoEndpoint):
    router: UnoRouter = SummaryRouter
    response_model: UnoSchema = RoleSummary
    body_model: UnoSchema = None


class UpdateRole(UnoEndpoint):
    router: UnoRouter = UpdateRouter
    body_model: UnoSchema = RoleEdit
    response_model: UnoSchema = RoleView


class DeleteRole(UnoEndpoint):
    router: UnoRouter = DeleteRouter
    response_model: UnoSchema = RoleView
    body_model: UnoSchema = None


class ImportRole(UnoEndpoint):
    router: UnoRouter = ImportRouter
    body_model: UnoSchema = RoleImport
    response_model: UnoSchema = RoleView

"""
