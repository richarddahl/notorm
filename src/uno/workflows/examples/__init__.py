# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Examples demonstrating how to use the workflow module.

This package contains examples showing different aspects of the workflow module,
including creating workflows, triggering them with events, using advanced
features like QueryModel integration, and the action executor system.
"""

from uno.workflows.examples.query_integration import run_query_integration_example
from uno.workflows.examples.action_executor_example import run_workflow_executor_example
from uno.workflows.examples.advanced_targeting_example import run_advanced_targeting_example

__all__ = [
    "run_query_integration_example",
    "run_workflow_executor_example",
    "run_advanced_targeting_example",
]