# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.graphs import VertexDef, EdgeDef


UserVertex = VertexDef(
    table_name="user",
    label="User",
)
