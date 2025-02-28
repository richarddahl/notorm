from __future__ import annotations


import datetime
import decimal

import asyncio
import pytest

"""
from uno.model import (
    UnoModel,
    UnoRelationConfig,
    UnoAdditionalFieldConfig,
    UnoMaskConfig,
)  # type: ignore
from uno.db_definition import UnoDB  # type: ignore
import uno.audit.models  # type: ignore
import uno.auth.models  # type: ignore
from uno.enumerations import FieldType  # type: ignore
from uno.database import metadata  # type: ignore

from config import settings  # type: ignore


pytest_plugins = ("pytest_asyncio",)

@pytest.fixture
def user_model_class():
    return UnoModel.get_model_from_registry_by_model_name("User")


def test_authuser_new(user_model_class):
    assert user_model_class.db_table_name == f"{settings.DB_SCHEMA}.user"
    assert (
        user_model_class.db_table == UnoDB(f"{settings.DB_SCHEMA}.user").db_table
    )
    assert user_model_class.user_filterable is True


def test_authuser_fields(user_model_class):
    field_list = [
        "id",
        "email",
        "hashed_password",
        "hashed_password_history",
        "client_hint_hash",
        "full_name",
        "handle",
        "is_superuser",
        "is_customer_admin",
        "is_locked",
        "is_suspended",
        "is_verified",
        "suspension_expiration",
        "last_login",
        "token",
        "token_renewal_at",
        "group_id",
        "default_group_id",  # End of Table Column Fields
        "password",  # Additional Field
        "group",  # Relations start (Class Variable)
        "meta",
        "default_group",
        "accesslogs",
        "filters",
        "logs",
        "queries",
        "roles",  # End of Relations
    ]
    for field_name in user_model_class.model_fields:
        assert field_name in field_list
    for field_name in field_list:
        if field_name in [
            "meta",
            "group",
            "default_group",
            "accesslogs",
            "filters",
            "logs",
            "queries",
            "roles",
        ]:
            continue
        assert field_name in user_model_class.model_fields


def test_authuser_configuration(user_model_class):
    assert user_model_class.system_columns == [
        "hashed_password",
        "client_hint_hash",
        "hashed_password_history",
    ]
    assert user_model_class.secret_columns == [
        "is_locked",
        "is_suspended",
        "suspension_expiration",
        "token",
        "token_renewal_at",
    ]
    assert user_model_class.relation_configs == {
        "rev": UnoRelationConfig(name="users"),
        "user_default_group_id_fkey": UnoRelationConfig(
            name="default_group",
        ),
        "user_group_id_fkey": UnoRelationConfig(name="group"),
        "user_id_fkey": UnoRelationConfig(name="meta"),
        "accesslog_user_id_fkey": UnoRelationConfig(name="accesslogs"),
        "audit__log_user_id_fkey": UnoRelationConfig(name="logs"),
        "filter_user_id_fkey": UnoRelationConfig(name="filters"),
        "query_user_id_fkey": UnoRelationConfig(name="queries"),
        "user__role_user_id_fkey": UnoRelationConfig(
            name="roles",
        ),
    }
    assert user_model_class.non_db_field_configs == {
        "password": UnoAdditionalFieldConfig(field_type=FieldType.TEXT)
    }
    assert user_model_class.mask_configs.get("login_mask").include_fields == [
        "email",
        "password",
    ]
    assert user_model_class.mask_configs.get("token_mask").include_fields == [
        "email",
        "token",
        "token_renewal_at",
    ]


def test_authuser_mask_creation(user_model_class):
    assert hasattr(user_model_class, "string_mask")
    assert hasattr(user_model_class, "element_mask")
    assert hasattr(user_model_class, "login_mask")
    assert hasattr(user_model_class, "token_mask")


def test_authuser_string_mask(user_model_class):
    mask = user_model_class.string_mask
    for field_name in [
        "id",
        "hashed_password",
        "email",
        "full_name",
        "handle",
        "is_superuser",
        "is_customer_admin",
        "is_locked",
        "is_suspended",
        "is_verified",
        "suspension_expiration",
        "last_login",
        "client_hint_hash",
        "token",
        "token_renewal_at",
        "hashed_password_history",
        "group_id",
        "default_group_id",
        "password",
    ]:
        assert field_name in mask.model_fields.keys()


def test_authuser_element_mask(user_model_class):
    mask = user_model_class.string_mask
    for field_name in [
        "id",
        "hashed_password",
        "email",
        "full_name",
        "handle",
        "is_superuser",
        "is_customer_admin",
        "is_locked",
        "is_suspended",
        "is_verified",
        "suspension_expiration",
        "last_login",
        "client_hint_hash",
        "token",
        "token_renewal_at",
        "hashed_password_history",
        "group_id",
        "default_group_id",
        "password",
    ]:
        assert field_name in mask.model_fields.keys()


def test_authuser_login_mask(user_model_class):
    mask = user_model_class.login_mask
    for field_name in [
        "email",
        "password",
    ]:
        assert field_name in mask.model_fields.keys()
    assert mask.model_fields["email"].annotation == str
    assert mask.model_fields["password"].annotation == str


def test_authuser_token_mask(user_model_class):
    mask = user_model_class.token_mask
    for field_name in [
        "email",
        "token",
        "token_renewal_at",
    ]:
        assert field_name in mask.model_fields.keys()
    assert mask.model_fields["email"].annotation == str
    assert mask.model_fields["token"].annotation == str | None
    assert mask.model_fields["token_renewal_at"].annotation == datetime.datetime | None


# Group UnoModel Tests
@pytest.fixture
def group_model_class():
    return UnoModel.get_model_from_registry_by_model_name("Group")


def test_authgroup_new(group_model_class):
    assert group_model_class.db_table_name == f"{settings.DB_SCHEMA}.group"
    assert (
        group_model_class.db_table
        == UnoDB(f"{settings.DB_SCHEMA}.group").db_table
    )
    assert group_model_class.user_filterable is True


def test_authgroup_fields(group_model_class):
    field_list = [
        "id",
        "name",
        "parent_id",
        "parent",  # Relations start (Class Variable)
        "children",  # End of Relations
    ]
    for field_name in group_model_class.model_fields:
        assert field_name in field_list
    for field_name in field_list:
        if field_name in ["parent", "children"]:
            continue
        assert field_name in group_model_class.model_fields


def test_authgroup_configuration(group_model_class):
    assert group_model_class.relation_configs == {
        "rev": UnoRelationConfig(name="groups"),
        "group_id_fkey": UnoRelationConfig(
            name="children",
        ),
        "group_parent_id_fkey": UnoRelationConfig(name="parent"),
    }


def test_authgroup_mask_creation(group_model_class):
    assert hasattr(group_model_class, "string_mask")
    assert hasattr(group_model_class, "element_mask")


def test_authgroup_string_mask(group_model_class):
    mask = group_model_class.string_mask
    for field_name in [
        "id",
        "name",
        "parent_id",
    ]:
        assert field_name in mask.model_fields.keys()


def test_authgroup_element_mask(group_model_class):
    mask = group_model_class.element_mask
    for field_name in [
        "id",
        "name",
        "parent_id",
    ]:
        assert field_name in mask.model_fields.keys()


# Role UnoModel Tests
@pytest.fixture
def role_model_class():
    return UnoModel.get_model_from_registry_by_model_name("Role")

"""
