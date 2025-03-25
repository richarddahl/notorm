# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import pytest  # type: ignore

from sqlalchemy import text


class TestUserGraphStructure:
    def test_user_graph_structure(self, connection, test_db):
        r = connection.connect().execute(
            text(
                """
                SET ROLE uno_test_admin;
                SELECT EXISTS (SELECT * FROM ag_catalog.ag_label WHERE name = 'User' AND kind = 'v');
                """
            )
        )
        print(r.fetchall())
