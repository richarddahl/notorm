# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import pytest

from sqlalchemy import text


class TestUserGraphStructure:
    def test_user_nodes(self, connection, test_db):
        for node in [
            "User",
            "Email",
            "Handle",
            "FullName",
            "Tenant",
            "Group",
            "Role",
            "Permission",
            "IsActive",
            "IsDeleted",
            "IsSuperuser",
            "CreatedAt",
            "ModifiedAt",
            "DeletedAt",
        ]:
            assert connection.execute(
                text(
                    f"""
                    SET ROLE uno_test_admin;
                    SELECT EXISTS (SELECT * FROM ag_catalog.ag_label WHERE name = '{node}' AND kind = 'v');
                    """
                )
            )

    def test_user_edges(self, connection, test_db):
        for edge in [
            "EMAIL",
            "HANDLE",
            "FULL_NAME",
            "TENANT",
            "DEFAULT_GROUP",
            "IS_ACTIVE",
            "IS_DELETED",
            "IS_SUPERUSER",
            "CREATED_AT",
            "CREATED_BY",
            "OBJECTS_CREATED",
            "MODIFIED_AT",
            "MODIFIED_BY",
            "OBJECTS_MODIFIED",
            "DELETED_AT",
            "DELETED_BY",
            "OBJECTS_DELETED",
            "USERS",
            "DEFAULT_GROUP_USERS",
            "GROUP_USERS",
            "GROUPS",
            "ROLE_USERS",
            "ACCESS_ROLES",
        ]:
            assert connection.execute(
                text(
                    f"""
                    SET ROLE uno_test_admin;
                    SELECT EXISTS (SELECT * FROM ag_catalog.ag_label WHERE name = '{edge}' AND kind = 'e');
                    """
                )
            )
