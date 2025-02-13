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
        label="WAS_SENT_BY",
        start_node_label="Message",
        end_node_label="User",
        accessor="sender",
    ),
    GraphEdge(
        label="HAS_PARENT",
        start_node_label="Message",
        end_node_label="Message",
        accessor="parent",
    ),
    GraphEdge(
        label="HAS_CHILDREN",
        start_node_label="Message",
        end_node_label="Message",
        accessor="children",
    ),
    # GraphEdge(
    #    label="HAS_ATTACHMENT",
    #    start_node_label="Message",
    #    end_node_label="Attachment",
    #    accessor="attachments",
    # ),
]
