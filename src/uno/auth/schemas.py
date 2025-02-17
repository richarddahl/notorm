# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.schemas import (
    CreateSchemaDef,
    DeleteSchemaDef,
    ImportSchemaDef,
    ListSchemaDef,
    SelectSchemaDef,
    UpdateSchemaDef,
)

tenant_schema_defs = [
    CreateSchemaDef(
        exclude_fields=[
            "id",
            "created_at",
            "owner_id",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ],
    ),
    ListSchemaDef(
        include_fields=[
            "id",
            "name",
            "is_active",
        ],
    ),
    SelectSchemaDef(),
    UpdateSchemaDef(
        exclude_fields=[
            "id",
            "created_at",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ],
    ),
    DeleteSchemaDef(),
    ImportSchemaDef(),
]

user_schema_defs = [
    CreateSchemaDef(
        exclude_fields=[
            "id",
            "created_at",
            "owner_id",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ],
    ),
    ListSchemaDef(
        include_fields=[
            "id",
            "email",
            "handle",
            "full_schema_type",
            "is_active",
        ],
    ),
    SelectSchemaDef(),
    UpdateSchemaDef(
        exclude_fields=[
            "id",
            "created_at",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ],
    ),
    DeleteSchemaDef(),
    ImportSchemaDef(),
]

group_schema_defs = [
    CreateSchemaDef(
        exclude_fields=[
            "id",
            "created_at",
            "owner_id",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ],
    ),
    ListSchemaDef(
        include_fields=[
            "id",
            "name",
            "is_active",
        ],
    ),
    SelectSchemaDef(),
    UpdateSchemaDef(
        exclude_fields=[
            "id",
            "created_at",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ],
    ),
    DeleteSchemaDef(),
    ImportSchemaDef(),
]

role_schema_defs = [
    CreateSchemaDef(
        exclude_fields=[
            "id",
            "created_at",
            "owner_id",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ],
    ),
    ListSchemaDef(
        include_fields=[
            "id",
            "name",
            "is_active",
        ],
    ),
    SelectSchemaDef(),
    UpdateSchemaDef(
        exclude_fields=[
            "id",
            "created_at",
            "modified_at",
            "modified_by_id",
            "deleted_at",
            "deleted_by_id",
        ],
    ),
    DeleteSchemaDef(),
    ImportSchemaDef(),
]
