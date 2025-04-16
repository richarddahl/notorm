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
- Action Executors: Handle the execution of different types of actions
- Notification System: Integration with the notification system
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

from uno.workflows.entities import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
    WorkflowExecutionRecord,
    User,
)


from uno.workflows.engine import (
    WorkflowEngine,
    WorkflowEventHandler,
    PostgresWorkflowEventListener,
    WorkflowEventModel,
)

from uno.workflows.errors import (
    WorkflowErrorCode,
    WorkflowNotFoundError,
    WorkflowExecutionError,
    WorkflowActionError,
    WorkflowEventError,
    WorkflowQueryError,
    register_workflow_errors,
)

from uno.workflows.provider import (
    WorkflowRepository,
    WorkflowService,
    configure_workflow_module,
)

from uno.workflows.executor import (
    ActionExecutionContext,
    ActionExecutor,
    NotificationExecutor,
    EmailExecutor,
    WebhookExecutor,
    DatabaseExecutor,
    CustomExecutor,
    get_executor,
    register_executor,
    get_executor_registry,
    init_executors,
)

from uno.workflows.conditions import (
    ConditionEvaluator,
    FieldValueEvaluator,
    TimeBasedEvaluator,
    RoleBasedEvaluator,
    QueryMatchEvaluator,
    CustomEvaluator,
    CompositeEvaluator,
    get_evaluator,
    register_evaluator,
    get_evaluator_registry,
    init_evaluators,
    LogicalOperator,
    ComparisonOperator,
    TimeUnit,
    TimeOperator,
    Weekday,
    ExtendedWorkflowConditionType,
)

from uno.workflows.recipients import (
    RecipientResolver,
    UserResolver,
    RoleResolver,
    GroupResolver,
    AttributeResolver,
    QueryRecipientResolver,
    DynamicRecipientResolver,
    get_resolver,
    register_resolver,
    get_resolver_registry,
    init_resolvers,
    ExtendedRecipientType,
)

from uno.workflows.notifications import (
    WorkflowNotification,
    NotificationPriority,
    NotificationType,
    SystemNotificationCreated,
    NotificationRead,
    BatchNotificationsCreated,
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

# Register schemas and error codes
try:
    # Register workflow pydantic schemas
    register_workflow_schemas()

    # Register workflow error codes in the error catalog
    register_workflow_errors()
except Exception as e:
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Failed to register workflow components: {e}")

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
    "LogicalOperator",
    "ComparisonOperator",
    "TimeUnit",
    "TimeOperator",
    "Weekday",
    "ExtendedWorkflowConditionType",
    "ExtendedRecipientType",
    # Domain Entities - New domain-driven design approach
    "WorkflowDef",
    "WorkflowTrigger",
    "WorkflowCondition",
    "WorkflowAction",
    "WorkflowRecipient",
    "WorkflowExecutionRecord",
    "User",
    # Engine components
    "WorkflowEngine",
    "WorkflowEventHandler",
    "PostgresWorkflowEventListener",
    "WorkflowEventModel",
    # Action Executors
    "ActionExecutionContext",
    "ActionExecutor",
    "NotificationExecutor",
    "EmailExecutor",
    "WebhookExecutor",
    "DatabaseExecutor",
    "CustomExecutor",
    "get_executor",
    "register_executor",
    "get_executor_registry",
    "init_executors",
    # Condition Evaluators
    "ConditionEvaluator",
    "FieldValueEvaluator",
    "TimeBasedEvaluator",
    "RoleBasedEvaluator",
    "QueryMatchEvaluator",
    "CustomEvaluator",
    "CompositeEvaluator",
    "get_evaluator",
    "register_evaluator",
    "get_evaluator_registry",
    "init_evaluators",
    # Recipient Resolvers
    "RecipientResolver",
    "UserResolver",
    "RoleResolver",
    "GroupResolver",
    "AttributeResolver",
    "QueryRecipientResolver",
    "DynamicRecipientResolver",
    "get_resolver",
    "register_resolver",
    "get_resolver_registry",
    "init_resolvers",
    # Notification System
    "WorkflowNotification",
    "NotificationPriority",
    "NotificationType",
    "SystemNotificationCreated",
    "NotificationRead",
    "BatchNotificationsCreated",
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
    # Error types
    "WorkflowErrorCode",
    "WorkflowNotFoundError",
    "WorkflowExecutionError",
    "WorkflowActionError",
    "WorkflowEventError",
    "WorkflowQueryError",
]
