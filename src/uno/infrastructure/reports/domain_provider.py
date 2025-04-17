"""Dependency injection provider for the Reports module."""
from functools import lru_cache
from typing import Dict, Any, Optional, cast

from uno.dependencies.modern_provider import ServiceLifecycle
from uno.dependencies.modern_provider import UnoServiceProvider, get_service
from uno.reports.domain_repositories import (
    ReportFieldDefinitionRepository,
    ReportTemplateRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)
from uno.reports.domain_services import (
    ReportFieldDefinitionService,
    ReportTemplateService,
    ReportTriggerService,
    ReportOutputService,
    ReportExecutionService,
    ReportOutputExecutionService,
)
from uno.reports.entities import (
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
)


@lru_cache(maxsize=1)
def get_reports_provider() -> UnoServiceProvider:
    """Get the Reports module service provider.
    
    Returns:
        The service provider for the Reports module.
    """
    provider = UnoServiceProvider("reports")
    
    # Register repositories
    provider.register(ReportFieldDefinitionRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(ReportTemplateRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(ReportTriggerRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(ReportOutputRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(ReportExecutionRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(ReportOutputExecutionRepository, lifecycle=ServiceLifecycle.SCOPED)
    
    # Register services
    provider.register(
        ReportFieldDefinitionService,
        factory=lambda container: ReportFieldDefinitionService(
            repository=container.resolve(ReportFieldDefinitionRepository),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        ReportOutputService,
        factory=lambda container: ReportOutputService(
            repository=container.resolve(ReportOutputRepository),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        ReportTriggerService,
        factory=lambda container: ReportTriggerService(
            repository=container.resolve(ReportTriggerRepository),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        ReportExecutionService,
        factory=lambda container: ReportExecutionService(
            repository=container.resolve(ReportExecutionRepository),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        ReportOutputExecutionService,
        factory=lambda container: ReportOutputExecutionService(
            repository=container.resolve(ReportOutputExecutionRepository),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register the template service last, as it depends on other services
    provider.register(
        ReportTemplateService,
        factory=lambda container: ReportTemplateService(
            repository=container.resolve(ReportTemplateRepository),
            field_definition_service=container.resolve(ReportFieldDefinitionService),
            trigger_service=container.resolve(ReportTriggerService),
            output_service=container.resolve(ReportOutputService),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider


# Convenience functions for resolving services
def get_report_field_definition_service() -> ReportFieldDefinitionService:
    """Get the report field definition service.
    
    Returns:
        The report field definition service.
    """
    return get_service(ReportFieldDefinitionService)


def get_report_template_service() -> ReportTemplateService:
    """Get the report template service.
    
    Returns:
        The report template service.
    """
    return get_service(ReportTemplateService)


def get_report_trigger_service() -> ReportTriggerService:
    """Get the report trigger service.
    
    Returns:
        The report trigger service.
    """
    return get_service(ReportTriggerService)


def get_report_output_service() -> ReportOutputService:
    """Get the report output service.
    
    Returns:
        The report output service.
    """
    return get_service(ReportOutputService)


def get_report_execution_service() -> ReportExecutionService:
    """Get the report execution service.
    
    Returns:
        The report execution service.
    """
    return get_service(ReportExecutionService)


def get_report_output_execution_service() -> ReportOutputExecutionService:
    """Get the report output execution service.
    
    Returns:
        The report output execution service.
    """
    return get_service(ReportOutputExecutionService)