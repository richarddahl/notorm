# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphEdgeDef


message_edge_defs = [
    GraphEdgeDef(
        name="WAS_SENT_BY",
        destination_table_name="user",
        accessor="sender",
    ),
    GraphEdgeDef(
        name="IS_PARENT_OF",
        destination_table_name="message",
        accessor="parent",
    ),
    GraphEdgeDef(
        name="IS_CHILD_OF",
        destination_table_name="message",
        accessor="children",
    ),
    GraphEdgeDef(
        name="WAS_SENT_TO",
        destination_table_name="user",
        accessor="addressed_to",
        secondary_table_name=f"{settings.DB_SCHEMA}.message__addressed_to",
    ),
    # GraphEdgeDef(
    #    name="HAS_ATTACHMENT",
    #    start_node_label="Message",
    #    destination_table_name="Attachment",
    #    accessor="attachments",
    # ),
]
