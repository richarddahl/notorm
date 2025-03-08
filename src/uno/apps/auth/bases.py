# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    CheckConstraint,
    ForeignKey,
    UniqueConstraint,
    Identity,
    text,
    Table,
    Column,
    FetchedValue,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import (
    ENUM,
    VARCHAR,
    BIGINT,
)

from uno.db.base import UnoBase, meta_data, str_26, str_255
from uno.db.enums import SQLOperation
from uno.apps.auth.enums import TenantType
from uno.apps.auth.sql.rls_sql_statements import (
    UserRowLevelSecurity,
)
from uno.apps.auth.sql.sql_statements import (
    ValidateGroupInsert,
    DefaultGroupTenant,
    InsertGroupForTenant,
    UserRecordUserAuditFunction,
)
from uno.db.sql.table_sql_emitters import (
    GeneralSqlEmitter,
    AlterGrants,
    RecordUserAuditFunction,
)
from uno.config import settings


user__group__role = Table(
    "user__group__role",
    meta_data,
    Column(
        "user_id",
        VARCHAR(26),
        ForeignKey("user.id"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "group_id",
        VARCHAR(26),
        ForeignKey("group.id"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "role_id",
        VARCHAR(26),
        ForeignKey("role.id"),
        primary_key=True,
        nullable=False,
    ),
    Index(
        "ix_user__group__role_user_id_group_id_role_id",
        "user_id",
        "group_id",
        "role_id",
    ),
)


role__permission = Table(
    "role__permission",
    meta_data,
    Column(
        "role_id",
        VARCHAR(26),
        ForeignKey("role.id"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "permission_id",
        BIGINT,
        ForeignKey("permission.id"),
        primary_key=True,
        nullable=False,
    ),
    Index("ix_role__permission_role_id_permission_id", "role_id", "permission_id"),
)


class UserBase(UnoBase):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            """
                is_superuser = 'false' AND default_group_id IS NOT NULL OR 
                is_superuser = 'true' AND default_group_id IS NULL
                --is_superuser = 'false' AND is_customer_admin = 'false' OR
                --is_superuser = 'true' AND is_customer_admin = 'false' OR
                --is_superuser = 'false' AND is_customer_admin = 'true'
            """,
            name="ck_user_is_superuser",
        ),
        {
            "comment": "Application users",
            "info": {
                "sql_emitters": [
                    GeneralSqlEmitter,
                    UserRowLevelSecurity,
                    UserRecordUserAuditFunction,
                ]
            },
        },
    )

    # Columns
    id: Mapped[int] = mapped_column(
        ForeignKey("meta.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Primary Key and Foreign Key to Meta Base",
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="Indicates that the record is currently active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates that the record has been soft deleted",
    )
    email: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
        doc="Email address, used as login ID",
    )
    handle: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
        doc="User's displayed name and alternate login ID",
    )
    full_name: Mapped[str_255] = mapped_column(
        nullable=False,
        doc="User's full name",
    )
    tenant_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
        info={"edge_label": "WORKS_FOR"},
    )
    default_group_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("group.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        info={"edge_label": "HAS_DEFAULT_GROUP"},
    )
    is_superuser: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates that the user is a Superuser",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        doc="Timestamp when the record was created",
    )
    created_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that created the record",
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        doc="Timestamp when the record was last modified",
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that last modified the record",
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=True,
        doc="Timestamp when the record was soft deleted",
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that deleted the record",
    )

    # Relationships
    tenant: Mapped["TenantBase"] = relationship(
        foreign_keys=[tenant_id],
        doc="Tenant to which the user is assigned",
    )
    default_group: Mapped["GroupBase"] = relationship(
        foreign_keys=[default_group_id],
        doc="User's default group, used as default for creating new objects",
    )
    created_by: Mapped["UserBase"] = relationship(
        foreign_keys=[created_by_id],
        doc="User that created the record",
    )
    modified_by: Mapped["UserBase"] = relationship(
        foreign_keys=[modified_by_id],
        doc="User that last modified the record",
    )
    deleted_by: Mapped["UserBase"] = relationship(
        foreign_keys=[deleted_by_id],
        doc="User that deleted the record",
    )
    groups: Mapped[list["GroupBase"]] = relationship(
        secondary=user__group__role,
        doc="Groups to which the user is assigned",
    )
    # roles: Mapped[list["RoleBase"]] = relationship(
    #    secondary="user__group__role",
    #    doc="Roles assigned to the user",
    # )


class GroupBase(UnoBase):
    __tablename__ = "group"
    __table_args__ = (
        Index("ix_group_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "comment": "Application end-user groups",
            "info": {
                "sql_emitters": [
                    GeneralSqlEmitter,
                    RecordUserAuditFunction,
                    ValidateGroupInsert,
                    DefaultGroupTenant,
                ]
            },
        },
    )

    # Columns

    id: Mapped[int] = mapped_column(
        ForeignKey("meta.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        doc="Primary Key and Foreign Key to Meta Base",
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="Indicates that the record is currently active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates that the record has been soft deleted",
    )
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "OWNED_BY_TENANT"},
    )
    name: Mapped[str_255] = mapped_column(doc="Group name")
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        doc="Timestamp when the record was created",
    )
    created_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that created the record",
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        doc="Timestamp when the record was last modified",
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that last modified the record",
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=True,
        doc="Timestamp when the record was soft deleted",
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that deleted the record",
    )

    # Relationships
    tenant: Mapped[list["TenantBase"]] = relationship(
        viewonly=True,
        doc="Customer to which the group belongs",
    )
    default_group_users: Mapped[list[UserBase]] = relationship(
        viewonly=True,
        foreign_keys=[UserBase.default_group_id],
        doc="Users assigned to the group",
    )
    created_by: Mapped[UserBase] = relationship(
        viewonly=True,
        foreign_keys=[created_by_id],
        doc="User that created the record",
    )
    modified_by: Mapped[UserBase] = relationship(
        viewonly=True,
        foreign_keys=[modified_by_id],
        doc="User that last modified the record",
    )
    deleted_by: Mapped[UserBase] = relationship(
        viewonly=True,
        foreign_keys=[deleted_by_id],
        doc="User that deleted the record",
    )
    users: Mapped[list[UserBase]] = relationship(
        viewonly=True,
        secondary=user__group__role,
        doc="Users assigned to the group",
    )
    roles: Mapped[list["RoleBase"]] = relationship(
        viewonly=True,
        secondary=user__group__role,
        doc="Roles assigned to the group",
    )


class RoleBase(UnoBase):
    __tablename__ = "role"
    __table_args__ = (
        Index("ix_role_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "comment": "Application roles",
            "info": {
                "sql_emitters": [
                    GeneralSqlEmitter,
                    RecordUserAuditFunction,
                ]
            },
        },
    )

    id: Mapped[int] = mapped_column(
        ForeignKey("meta.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        doc="Primary Key and Foreign Key to Meta Base",
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="Indicates that the record is currently active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates that the record has been soft deleted",
    )
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "OWNED_BY_TENANT"},
    )
    name: Mapped[str_255] = mapped_column(
        index=True,
        nullable=False,
        doc="Role name",
    )
    description: Mapped[str_255] = mapped_column(
        nullable=False,
        doc="Role description",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        doc="Timestamp when the record was created",
    )
    created_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that created the record",
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        doc="Timestamp when the record was last modified",
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that last modified the record",
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=True,
        doc="Timestamp when the record was soft deleted",
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that deleted the record",
    )

    # Relationships
    tenant: Mapped[list["TenantBase"]] = relationship(
        viewonly=True,
        doc="Customer to which the role belongs",
    )
    created_by: Mapped[UserBase] = relationship(
        viewonly=True,
        foreign_keys=[created_by_id],
        doc="User that created the record",
    )
    modified_by: Mapped[UserBase] = relationship(
        viewonly=True,
        foreign_keys=[modified_by_id],
        doc="User that last modified the record",
    )
    deleted_by: Mapped[UserBase] = relationship(
        viewonly=True,
        foreign_keys=[deleted_by_id],
        doc="User that deleted the record",
    )
    users: Mapped[list["UserBase"]] = relationship(
        viewonly=True,
        secondary=user__group__role,
        doc="Users assigned to the role",
    )
    groups: Mapped[list["GroupBase"]] = relationship(
        viewonly=True,
        secondary=user__group__role,
        doc="Groups assigned to the role",
    )
    permissions: Mapped[list["PermissionBase"]] = relationship(
        viewonly=True,
        secondary=role__permission,
        doc="Permissions assigned to the role",
    )


class TenantBase(UnoBase):
    __tablename__ = "tenant"
    __table_args__ = (
        Index("ix_tenant_name", "name"),
        UniqueConstraint("name"),
        {
            "comment": "Application tenants",
            "info": {
                "sql_emitters": [
                    GeneralSqlEmitter,
                    RecordUserAuditFunction,
                    InsertGroupForTenant,
                ]
            },
        },
    )

    id: Mapped[int] = mapped_column(
        ForeignKey("meta.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        doc="Primary Key and Foreign Key to Meta Base",
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="Indicates that the record is currently active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates that the record has been soft deleted",
    )
    name: Mapped[str_255] = mapped_column(
        index=True,
        nullable=False,
        doc="Role name",
    )
    tenant_type = mapped_column(
        ENUM(
            TenantType,
            name="tenanttype",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        server_default=TenantType.INDIVIDUAL.name,
        nullable=False,
        doc="Tenant type",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        doc="Timestamp when the record was created",
    )
    created_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that created the record",
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        doc="Timestamp when the record was last modified",
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that last modified the record",
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=True,
        doc="Timestamp when the record was soft deleted",
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        doc="User that deleted the record",
    )

    # Relationships
    created_by: Mapped[UserBase] = relationship(
        viewonly=True,
        foreign_keys=[created_by_id],
        doc="User that created the record",
    )
    modified_by: Mapped[UserBase] = relationship(
        viewonly=True,
        foreign_keys=[modified_by_id],
        doc="User that last modified the record",
    )
    deleted_by: Mapped[UserBase] = relationship(
        viewonly=True,
        foreign_keys=[deleted_by_id],
        doc="User that deleted the record",
    )
    users: Mapped[list[UserBase]] = relationship(
        viewonly=True,
        foreign_keys=[UserBase.tenant_id],
        doc="Users assigned to the tenant",
    )
    groups: Mapped[list[GroupBase]] = relationship(
        viewonly=True,
        foreign_keys=[GroupBase.tenant_id],
        doc="Groups assigned to the tenant",
    )
    roles: Mapped[list[RoleBase]] = relationship(
        viewonly=True,
        foreign_keys=[RoleBase.tenant_id],
        doc="Roles assigned to the tenant",
    )


class PermissionBase(UnoBase):
    __tablename__ = "permission"
    __table_args__ = (
        Index("ix_permission_meta_type_id_operation", "meta_type_id", "operation"),
        UniqueConstraint("meta_type_id", "operation"),
        {
            "comment": "Application permissions",
            "info": {"sql_emitters": [AlterGrants]},
        },
    )
    id: Mapped[int] = mapped_column(
        Identity(start=1, cycle=True),
        primary_key=True,
        index=True,
        nullable=False,
        doc="Primary Key",
    )
    meta_type_id: Mapped[int] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="Foreign Key to Meta Type",
    )
    operation: Mapped[SQLOperation] = mapped_column(
        ENUM(
            SQLOperation,
            name="sqloperation",
            create_type=True,
        ),
        doc="SQL Operation",
    )
