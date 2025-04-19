"""
Dependency injection provider for the Workflows domain services.

This module integrates the workflows domain services and repositories with
the dependency injection system, making them available throughout the application.

All dependency resolution and service exposure is now done via the central DI container/provider.
This module is fully DI container compliant and does not instantiate or expose dependencies ad hoc.
"""

import logging
from functools import lru_cache
from uno.database.db_manager import DBManager
from uno.dependencies.modern_provider import ServiceProvider, ServiceLifecycle
from uno.workflows.domain_repositories import (
    WorkflowDefRepository,
    WorkflowTriggerRepository,
    WorkflowConditionRepository,
    WorkflowActionRepository,
    WorkflowRecipientRepository,
    WorkflowExecutionRepository,
)
from uno.workflows.domain_services import (
    WorkflowDefService,
    WorkflowTriggerService,
    WorkflowConditionService,
    WorkflowActionService,
    WorkflowRecipientService,
    WorkflowExecutionService,
)


def configure_workflows_services(container):
    """Configure workflows services in the DI container."""
    Args:
        container: The dependency container to configure
    """
    import logging
    from uno.database.db_manager import DBManager
    from uno.dependencies.modern_provider import ServiceLifecycle
    from uno.workflows.domain_repositories import (
        WorkflowDefRepository,
        WorkflowTriggerRepository,
        WorkflowConditionRepository,
        WorkflowActionRepository,
        WorkflowRecipientRepository,
        WorkflowExecutionRepository,
    )
    from uno.workflows.domain_services import (
        WorkflowDefService,
        WorkflowTriggerService,
        WorkflowConditionService,
        WorkflowActionService,
        WorkflowRecipientService,
        WorkflowExecutionService,
    )

    logger = logging.getLogger("uno.workflows")

    # Register repositories
    container.register(
        WorkflowDefRepository,
        lambda c: WorkflowDefRepository(db_factory=c.resolve(DBManager)),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowTriggerRepository,
        lambda c: WorkflowTriggerRepository(db_factory=c.resolve(DBManager)),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowConditionRepository,
        lambda c: WorkflowConditionRepository(db_factory=c.resolve(DBManager)),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowActionRepository,
        lambda c: WorkflowActionRepository(db_factory=c.resolve(DBManager)),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowRecipientRepository,
        lambda c: WorkflowRecipientRepository(db_factory=c.resolve(DBManager)),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowExecutionRepository,
        lambda c: WorkflowExecutionRepository(db_factory=c.resolve(DBManager)),
        lifecycle=ServiceLifecycle.SCOPED,
    )

    # Register services
    container.register(
        WorkflowDefService,
        lambda c: WorkflowDefService(
            repository=c.resolve(WorkflowDefRepository),
            trigger_repository=c.resolve(WorkflowTriggerRepository),
            condition_repository=c.resolve(WorkflowConditionRepository),
            action_repository=c.resolve(WorkflowActionRepository),
            recipient_repository=c.resolve(WorkflowRecipientRepository),
            execution_repository=c.resolve(WorkflowExecutionRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowTriggerService,
        lambda c: WorkflowTriggerService(
            repository=c.resolve(WorkflowTriggerRepository),
            workflow_service=c.resolve(WorkflowDefService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowConditionService,
        lambda c: WorkflowConditionService(
            repository=c.resolve(WorkflowConditionRepository),
            workflow_service=c.resolve(WorkflowDefService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowRecipientService,
        lambda c: WorkflowRecipientService(
            repository=c.resolve(WorkflowRecipientRepository),
            workflow_service=c.resolve(WorkflowDefService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowActionService,
        lambda c: WorkflowActionService(
            repository=c.resolve(WorkflowActionRepository),
            workflow_service=c.resolve(WorkflowDefService),
            recipient_service=c.resolve(WorkflowRecipientService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        WorkflowExecutionService,
        lambda c: WorkflowExecutionService(
            repository=c.resolve(WorkflowExecutionRepository),
            workflow_service=c.resolve(WorkflowDefService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )

    # Handle circular dependency: Set action_service on recipient_service after container config
    def configure_circular_dependencies(container):
        recipient_service = container.resolve(WorkflowRecipientService)
        action_service = container.resolve(WorkflowActionService)
        recipient_service.action_service = action_service

    container.add_container_configured_callback(configure_circular_dependencies)
