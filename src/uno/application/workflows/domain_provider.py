"""
Dependency injection provider for the Workflows domain services.

This module integrates the workflows domain services and repositories with
the dependency injection system, making them available throughout the application.
"""

import logging
from functools import lru_cache
from typing import Dict, Any, Optional, Type

from uno.database.db_manager import DBManager
from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
)
from uno.workflows.entities import (
    WorkflowDef,
    WorkflowTrigger,
    WorkflowCondition,
    WorkflowAction,
    WorkflowRecipient,
    WorkflowExecutionRecord,
)
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


@lru_cache(maxsize=1)
def get_workflows_provider() -> UnoServiceProvider:
    """
    Get the Workflows module service provider.
    
    Returns:
        A configured service provider for the Workflows module
    """
    provider = UnoServiceProvider("workflows")
    logger = logging.getLogger("uno.workflows")
    
    # Register repositories with their dependencies
    provider.register(
        WorkflowDefRepository,
        lambda container: WorkflowDefRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        WorkflowTriggerRepository,
        lambda container: WorkflowTriggerRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        WorkflowConditionRepository,
        lambda container: WorkflowConditionRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        WorkflowActionRepository,
        lambda container: WorkflowActionRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        WorkflowRecipientRepository,
        lambda container: WorkflowRecipientRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        WorkflowExecutionRepository,
        lambda container: WorkflowExecutionRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register services with their dependencies
    # Note: We register services in order of dependency (services with fewer dependencies first)
    
    # WorkflowDefService depends on repositories for relationships but can be registered first
    provider.register(
        WorkflowDefService,
        lambda container: WorkflowDefService(
            repository=container.resolve(WorkflowDefRepository),
            trigger_repository=container.resolve(WorkflowTriggerRepository),
            condition_repository=container.resolve(WorkflowConditionRepository),
            action_repository=container.resolve(WorkflowActionRepository),
            recipient_repository=container.resolve(WorkflowRecipientRepository),
            execution_repository=container.resolve(WorkflowExecutionRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register trigger service
    provider.register(
        WorkflowTriggerService,
        lambda container: WorkflowTriggerService(
            repository=container.resolve(WorkflowTriggerRepository),
            workflow_service=container.resolve(WorkflowDefService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register condition service
    provider.register(
        WorkflowConditionService,
        lambda container: WorkflowConditionService(
            repository=container.resolve(WorkflowConditionRepository),
            workflow_service=container.resolve(WorkflowDefService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register recipient service
    # Note: This has a circular dependency with ActionService, so we'll handle that carefully
    provider.register(
        WorkflowRecipientService,
        lambda container: WorkflowRecipientService(
            repository=container.resolve(WorkflowRecipientRepository),
            workflow_service=container.resolve(WorkflowDefService),
            # action_service will be set later
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register action service
    provider.register(
        WorkflowActionService,
        lambda container: WorkflowActionService(
            repository=container.resolve(WorkflowActionRepository),
            workflow_service=container.resolve(WorkflowDefService),
            recipient_service=container.resolve(WorkflowRecipientService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register execution service
    provider.register(
        WorkflowExecutionService,
        lambda container: WorkflowExecutionService(
            repository=container.resolve(WorkflowExecutionRepository),
            workflow_service=container.resolve(WorkflowDefService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Handle circular dependency: Set action_service on recipient_service
    def configure_circular_dependencies(container):
        recipient_service = container.resolve(WorkflowRecipientService)
        action_service = container.resolve(WorkflowActionService)
        recipient_service.action_service = action_service
    
    provider.add_container_configured_callback(configure_circular_dependencies)
    
    return provider


def configure_workflows_services(container):
    """
    Configure workflows services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_workflows_provider()
    provider.configure_container(container)