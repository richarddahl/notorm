# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphNode, GraphEdge

message_node = GraphNode(
    table_name="message",
    label="Message",
)

message_edges = [
    GraphEdge(
        table_name="message",
        label="WAS_SENT_BY",
        start_node_label="Message",
        end_node_label="User",
        accessor="sender",
    ),
    GraphEdge(
        table_name="message",
        label="IS_PARENT_OF",
        start_node_label="Message",
        end_node_label="Message",
        accessor="parent",
    ),
    GraphEdge(
        table_name="message",
        label="IS_CHILD_OF",
        start_node_label="Message",
        end_node_label="Message",
        accessor="children",
    ),
    GraphEdge(
        table_name="message",
        label="WAS_SENT_TO",
        start_node_label="Message",
        end_node_label="User",
        accessor="addressed_to",
        secondary_table_name="uno.message__addressed_to",
    ),
    # GraphEdge(
    #    label="HAS_ATTACHMENT",
    #    start_node_label="Message",
    #    end_node_label="Attachment",
    #    accessor="attachments",
    # ),
]
