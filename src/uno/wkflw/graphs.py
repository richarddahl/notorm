# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphNode, GraphEdge


workflow_node = GraphNode(
    table_name="workflow",
    label="Workflow",
)

workflow_edges = []

workflow_event_node = GraphNode(
    table_name="workflow_event",
    label="WorkflowEvent",
)

workflow_event_edges = []

workflow_record_node = GraphNode(
    table_name="workflow_record",
    label="WorkflowRecord",
)

workflow_record_edges = []
