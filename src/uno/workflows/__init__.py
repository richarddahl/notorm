# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Workflow Module: User-defined notification workflows triggered by database events.

This module enables tenant administrators to define and manage custom notification
workflows based on database events without requiring developer intervention.

Components:
- Workflow Definitions: Define workflows that can be triggered by events
- Workflow Triggers: Specify conditions for when workflows should execute
- Workflow Actions: Define what actions to take when workflows are triggered
- Workflow Engine: Core component that handles workflow execution
- Event Integration: Connects to domain events and database events
"""

import inject

from uno.workflows.models import (
    WorkflowDefinition,
    WorkflowTriggerModel,
    WorkflowConditionModel,
    WorkflowActionModel,
    WorkflowRecipientModel,
    WorkflowExecutionLog,
    WorkflowStatus,
    WorkflowActionType,
    WorkflowRecipientType,
    WorkflowExecutionStatus,
    WorkflowConditionType,
)

from uno.workflows.objs import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
    WorkflowExecutionRecord,
)

from uno.workflows.engine import (
    WorkflowEngine,
    WorkflowEventHandler,
    PostgresWorkflowEventListener,
    WorkflowEventModel,
    WorkflowError,
)

from uno.workflows.provider import (
    WorkflowRepository,
    WorkflowService,
    configure_workflow_module,
)

from uno.workflows.sqlconfigs import workflow_module_sql_config
from uno.workflows.integration import (
    WorkflowEventIntegration,
    get_workflow_integration,
    register_workflow_integrations,
)
from uno.workflows.app_integration import (
    setup_workflow_module,
    get_workflow_dependency,
    workflow_dependency,
)

# We'll configure the workflow module later, when main application dependencies are set up
# This prevents "No injector is configured" errors during import
# inject.configure_once(configure_workflow_module)

# Import schemas and registration function
from uno.workflows.schemas import register_workflow_schemas
# Legacy schemas have been removed for simplicity

# Register schemas
try:
    register_workflow_schemas()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to register workflow schemas: {e}")

# Make everything available
__all__ = [
    # Models
    "WorkflowDefinition",
    "WorkflowTriggerModel",
    "WorkflowConditionModel",
    "WorkflowActionModel",
    "WorkflowRecipientModel",
    "WorkflowExecutionLog",
    
    # Enums
    "WorkflowStatus",
    "WorkflowActionType",
    "WorkflowRecipientType",
    "WorkflowExecutionStatus",
    "WorkflowConditionType",
    
    # Objects - Legacy objects have been removed
    "WorkflowDef",
    "WorkflowTrigger",
    "WorkflowCondition",
    "WorkflowAction",
    "WorkflowRecipient",
    "WorkflowExecutionRecord",
    
    # Engine components
    "WorkflowEngine",
    "WorkflowEventHandler",
    "PostgresWorkflowEventListener",
    "WorkflowEventModel",
    "WorkflowError",
    
    # Repository and services
    "WorkflowRepository",
    "WorkflowService",
    
    # Event Integrations
    "WorkflowEventIntegration",
    "get_workflow_integration",
    "register_workflow_integrations",
    
    # App Integrations
    "setup_workflow_module",
    "get_workflow_dependency",
    "workflow_dependency",
    
    # SQL configurations
    "workflow_module_sql_config",
]