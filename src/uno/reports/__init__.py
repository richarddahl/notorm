# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Reports module for Uno.

This module provides a flexible and customizable reporting system that allows
end-users to define, generate, and deliver reports in various formats.
"""

from uno.reports.interfaces import (
    ReportTemplateServiceProtocol,
    ReportFieldServiceProtocol,
    ReportExecutionServiceProtocol,
    ReportTriggerServiceProtocol,
    ReportOutputServiceProtocol,
)

from uno.reports.objs import (
    # Original classes
    ReportFieldConfig,
    ReportField,
    ReportType,
    Report,
    # Enhanced classes
    ReportTemplate,
    ReportFieldDefinition,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
    # Enums
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
    ReportExecutionStatus,
)

from uno.reports.services import (
    ReportTemplateService,
    ReportFieldService,
    ReportExecutionService,
    ReportTriggerService,
    ReportOutputService,
)

from uno.reports.errors import (
    ReportErrorCode,
    ReportTemplateNotFoundError,
    ReportFieldNotFoundError,
    ReportExecutionNotFoundError,
    ReportTriggerNotFoundError,
    ReportExecutionFailedError,
    ReportOutputFormatInvalidError,
    ReportOutputDeliveryFailedError,
    ReportTemplateInvalidError,
    ReportFieldInvalidError,
    ReportTriggerInvalidError,
    register_report_errors,
)

from uno.reports.repositories import (
    ReportTemplateRepository,
    ReportFieldDefinitionRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)

# Export endpoints for API integration
from uno.reports.endpoints import endpoints

# Register report errors
register_report_errors()

__all__ = [
    # Interfaces
    "ReportTemplateServiceProtocol",
    "ReportFieldServiceProtocol",
    "ReportExecutionServiceProtocol", 
    "ReportTriggerServiceProtocol",
    "ReportOutputServiceProtocol",
    
    # Object classes
    "ReportFieldConfig",
    "ReportField",
    "ReportType",
    "Report",
    "ReportTemplate",
    "ReportFieldDefinition",
    "ReportTrigger",
    "ReportOutput",
    "ReportExecution",
    "ReportOutputExecution",
    
    # Enums
    "ReportFieldType",
    "ReportTriggerType",
    "ReportOutputType",
    "ReportFormat",
    "ReportExecutionStatus",
    
    # Services
    "ReportTemplateService",
    "ReportFieldService",
    "ReportExecutionService",
    "ReportTriggerService",
    "ReportOutputService",
    
    # Error classes
    "ReportErrorCode",
    "ReportTemplateNotFoundError",
    "ReportFieldNotFoundError",
    "ReportExecutionNotFoundError",
    "ReportTriggerNotFoundError",
    "ReportExecutionFailedError",
    "ReportOutputFormatInvalidError",
    "ReportOutputDeliveryFailedError",
    "ReportTemplateInvalidError",
    "ReportFieldInvalidError",
    "ReportTriggerInvalidError",
    
    # Repositories
    "ReportTemplateRepository",
    "ReportFieldDefinitionRepository",
    "ReportTriggerRepository",
    "ReportOutputRepository",
    "ReportExecutionRepository",
    "ReportOutputExecutionRepository",
    
    # Endpoints
    "endpoints",
]
