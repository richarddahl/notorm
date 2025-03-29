# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import pytest

from sqlalchemy import inspect, Inspector, text
from sqlalchemy.dialects.postgresql import (
    VARCHAR,
    ENUM,
    TEXT,
    BOOLEAN,
    TIMESTAMP,
    BIGINT,
    JSONB,
    ARRAY,
    TEXT,
)

from uno.enums import TenantType
from uno.config import settings  # type: ignore
from tests.conftest import db_column


class TestUserFunctions:

    def test_user_triggers_and_functions(self, connection, test_db):
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_delete_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_delete_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_insert_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_insert_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'insert_meta_record')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_insert_meta_record_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'insert_record_status_columns')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_insert_record_status_columns_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_manage_audit_columns')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_manage_audit_columns_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_update_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_update_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user_truncate_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user_truncate_graph_trigger')"
            )
        ).scalar()


class TestUserGroupFunctions:
    def test_user_group_triggers_and_functions(self, connection, test_db):

        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__group_delete_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__group_delete_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__group_insert_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__group_insert_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__group_update_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__group_update_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__group_truncate_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__group_truncate_graph_trigger')"
            )
        ).scalar()


class TestUserRoleFunctions:
    def test_user_role_triggers_and_functions(self, connection, test_db):

        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__role_delete_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__role_delete_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__role_insert_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__role_insert_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__role_update_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__role_update_graph_trigger')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = 'user__role_truncate_graph')"
            )
        ).scalar()
        assert connection.execute(
            text(
                "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgname = 'user__role_truncate_graph_trigger')"
            )
        ).scalar()
