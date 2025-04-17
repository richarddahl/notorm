# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Integration between the workflow module and the domain event system.

This module provides the necessary hooks to connect the workflow module
with the domain event system, enabling workflows to be triggered by
domain events.
"""

import logging
import asyncio
from typing import Optional, Type, Any, Dict, List

import inject
from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.base import UnoError
from uno.workflows.errors import WorkflowErrorCode, WorkflowEventError

from uno.domain.events import (
    DomainEvent, EventBus, get_event_bus,
    EventSubscription, EventPriority
)
from uno.database.db_manager import DBManager
from uno.settings import uno_settings

from uno.workflows.engine import (
    WorkflowEngine,
    WorkflowEventHandler,
    PostgresWorkflowEventListener,
)
from uno.workflows.provider import WorkflowService


class WorkflowEventIntegration:
    """
    Integration between the workflow module and the domain event system.
    
    This class provides methods to register the workflow engine with
    the domain event system.
    """
    
    @inject.params(
        event_bus=EventBus,
        workflow_handler=WorkflowEventHandler,
        workflow_service=WorkflowService,
        db_manager=DBManager,
        logger=logging.Logger
    )
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        workflow_handler: Optional[WorkflowEventHandler] = None,
        workflow_service: Optional[WorkflowService] = None,
        db_manager: Optional[DBManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the workflow event integration.
        
        Args:
            event_bus: The event bus to integrate with
            workflow_handler: The workflow event handler
            workflow_service: The workflow service
            db_manager: The database manager
            logger: Optional logger instance
        """
        self.event_bus = event_bus or get_event_bus()
        self.workflow_handler = workflow_handler
        self.workflow_service = workflow_service
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)
        self._pg_listener = None
    
    def register_domain_event_handler(
        self,
        event_types: Optional[List[Type[DomainEvent]]] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """
        Register the workflow handler with the domain event system.
        
        Args:
            event_types: List of event types to register for
            priority: Handler priority
        """
        if not self.workflow_handler:
            self.logger.warning(
                "No workflow handler available for domain event integration"
            )
            return
        
        # If no specific event types are provided, register for all events
        if not event_types:
            # Register for all events via a wildcard subscription
            self.event_bus._subscriptions.append(
                EventSubscription(
                    handler=self.workflow_handler.handle,
                    event_type=None,  # Match any event type
                    topic_pattern=None,  # Match any topic
                    priority=priority,
                )
            )
            self.logger.info(
                "Registered workflow handler for all domain events"
            )
        else:
            # Register for specific event types
            for event_type in event_types:
                self.event_bus.subscribe(
                    handler=self.workflow_handler.handle,
                    event_type=event_type,
                    priority=priority,
                )
                self.logger.info(
                    f"Registered workflow handler for {event_type.__name__} events"
                )
    
    async def start_postgres_listener(
        self,
        channel: str = 'workflow_events',
    ) -> Result[bool]:
        """
        Start the PostgreSQL event listener.
        
        Args:
            channel: The PostgreSQL notification channel to listen on
        """
        if not self.workflow_service:
            error_msg = "No workflow service available for PostgreSQL event integration"
            self.logger.warning(error_msg)
            return Failure(UnoError(
                error_msg, 
                WorkflowErrorCode.WORKFLOW_EVENT_LISTENER_FAILED,
                component="workflow_service"
            ))
        
        # Start the event listener via the workflow service
        result = await self.workflow_service.start_event_listener()
        
        if result.is_failure:
            error_msg = f"Failed to start PostgreSQL event listener: {result.error}"
            self.logger.error(error_msg)
            return Failure(UnoError(
                error_msg, 
                WorkflowErrorCode.WORKFLOW_EVENT_LISTENER_FAILED,
                operation="start_postgres_listener"
            ))
        
        self.logger.info(f"Started PostgreSQL event listener on channel '{channel}'")
        return Success(True)
    
    async def stop_postgres_listener(self) -> Result[bool]:
        """Stop the PostgreSQL event listener."""
        if not self.workflow_service:
            return Success(False)
        
        # Stop the event listener via the workflow service
        result = await self.workflow_service.stop_event_listener()
        
        if result.is_failure:
            error_msg = f"Failed to stop PostgreSQL event listener: {result.error}"
            self.logger.error(error_msg)
            return Failure(UnoError(
                error_msg, 
                WorkflowErrorCode.WORKFLOW_EVENT_LISTENER_FAILED,
                operation="stop_postgres_listener"
            ))
        
        self.logger.info("Stopped PostgreSQL event listener")
        return Success(True)


# Create a singleton instance
@inject.autoparams()
def get_workflow_integration(
    event_bus: Optional[EventBus] = None,
    workflow_handler: Optional[WorkflowEventHandler] = None,
    workflow_service: Optional[WorkflowService] = None,
    db_manager: Optional[DBManager] = None,
    logger: Optional[logging.Logger] = None,
) -> WorkflowEventIntegration:
    """
    Get the workflow event integration singleton.
    
    Returns:
        The workflow event integration instance
    """
    return WorkflowEventIntegration(
        event_bus=event_bus,
        workflow_handler=workflow_handler,
        workflow_service=workflow_service,
        db_manager=db_manager,
        logger=logger,
    )


# Define a function to register the integrations at application startup
async def register_workflow_integrations(
    register_domain_events: bool = True,
    start_postgres_listener: bool = True,
    event_types: Optional[List[Type[DomainEvent]]] = None,
) -> Result[bool]:
    """
    Register all workflow integrations.
    
    Args:
        register_domain_events: Whether to register with the domain event system
        start_postgres_listener: Whether to start the PostgreSQL event listener
        event_types: List of event types to register for
    """
    try:
        integration = get_workflow_integration()
        
        # Register with domain event system
        if register_domain_events:
            integration.register_domain_event_handler(event_types)
        
        # Start PostgreSQL event listener
        if start_postgres_listener:
            result = await integration.start_postgres_listener()
            if result.is_failure:
                return Failure(WorkflowEventError(
                    event_type="postgres_listener",
                    reason=f"Failed to start PostgreSQL listener: {result.error}",
                    message="Workflow integration failure"
                ))
        
        return Success(True)
    except Exception as e:
        return Failure(WorkflowEventError(
            event_type="integration",
            reason=str(e),
            message="Failed to register workflow integrations"
        ))


# Add the integration to the workflow module exports
__all__ = [
    'WorkflowEventIntegration',
    'get_workflow_integration',
    'register_workflow_integrations',
]