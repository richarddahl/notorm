# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Dict, Any, Type
import inject

from uno.jobs.domain_repositories import (
    JobRepositoryProtocol, 
    ScheduleRepositoryProtocol,
    JobRepository,
    ScheduleRepository
)
from uno.jobs.domain_services import (
    JobManagerServiceProtocol,
    TaskRegistryProtocol,
    JobManagerService,
    TaskRegistryService
)


def configure_jobs_dependencies(binder: inject.Binder) -> None:
    """Configure dependency injection for jobs module.
    
    Args:
        binder: The inject binder to configure
    """
    # Create instances
    task_registry = TaskRegistryService()
    
    # Bind task registry
    binder.bind(TaskRegistryProtocol, task_registry)
    
    # Bind repositories
    binder.bind_to_provider(JobRepositoryProtocol, JobRepository)
    binder.bind_to_provider(ScheduleRepositoryProtocol, ScheduleRepository)
    
    # Bind job manager service
    binder.bind_to_provider(JobManagerServiceProtocol, JobManagerService)


def get_jobs_di_config() -> Dict[Type, Any]:
    """Get dependency injection configuration for jobs module.
    
    Returns:
        Dictionary mapping interface types to implementation types
    """
    # Create instances
    task_registry = TaskRegistryService()
    
    # Create configuration
    return {
        TaskRegistryProtocol: task_registry,
        JobRepositoryProtocol: JobRepository,
        ScheduleRepositoryProtocol: ScheduleRepository,
        JobManagerServiceProtocol: JobManagerService,
    }