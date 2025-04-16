# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Reports module for Uno.

This module provides a flexible and customizable reporting system that allows
end-users to define, generate, and deliver reports in various formats.

Key components:
- Domain Entities: Core business objects with behavior following domain-driven design
  - ReportTemplate: Defines report structure and behavior
  - ReportFieldDefinition: Defines report fields
  - ReportTrigger: Controls when reports are generated
  - ReportOutput: Controls how reports are delivered
  - ReportExecution: Records of report runs
- Repository Pattern: Follows domain-driven design for data access
- Domain Services: Encapsulates business logic for reports
- API Integration: FastAPI endpoints for report operations
- Data Transfer Objects (DTOs): Objects for serialization/deserialization in the API
- Schema Managers: Handling conversion between domain entities and DTOs
"""

# Domain entities (DDD)
from uno.reports.entities import (
    # Domain entities
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
    # Enum-like classes
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
    ReportExecutionStatus,
)

# Domain repositories
from uno.reports.domain_repositories import (
    ReportFieldDefinitionRepository,
    ReportTemplateRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)

# Domain services
from uno.reports.domain_services import (
    ReportFieldDefinitionService,
    ReportTemplateService,
    ReportTriggerService,
    ReportOutputService,
    ReportExecutionService,
    ReportOutputExecutionService,
)

# Domain provider and endpoints
from uno.reports.domain_provider import (
    get_reports_provider,
    get_report_field_definition_service,
    get_report_template_service,
    get_report_trigger_service,
    get_report_output_service,
    get_report_execution_service,
    get_report_output_execution_service,
)

# Schema managers for entity-DTO conversion
from uno.reports.schemas import (
    ReportFieldDefinitionSchemaManager,
    ReportTemplateSchemaManager,
    ReportTriggerSchemaManager,
    ReportOutputSchemaManager,
    ReportExecutionSchemaManager,
    ReportOutputExecutionSchemaManager,
)

# Data Transfer Objects (DTOs) for API
from uno.reports.dtos import (
    # Enums
    ReportFieldTypeEnum,
    ReportTriggerTypeEnum,
    ReportOutputTypeEnum,
    ReportFormatEnum,
    ReportExecutionStatusEnum,
    
    # Field Definition DTOs
    ReportFieldDefinitionBaseDto,
    ReportFieldDefinitionCreateDto,
    ReportFieldDefinitionUpdateDto,
    ReportFieldDefinitionViewDto,
    ReportFieldDefinitionFilterParams,
    
    # Template DTOs
    ReportTemplateBaseDto,
    ReportTemplateCreateDto,
    ReportTemplateUpdateDto,
    ReportTemplateViewDto,
    ReportTemplateFilterParams,
    
    # Trigger DTOs
    ReportTriggerBaseDto,
    ReportTriggerCreateDto,
    ReportTriggerUpdateDto,
    ReportTriggerViewDto,
    ReportTriggerFilterParams,
    
    # Output DTOs
    ReportOutputBaseDto,
    ReportOutputCreateDto,
    ReportOutputUpdateDto,
    ReportOutputViewDto,
    ReportOutputFilterParams,
    
    # Execution DTOs
    ReportExecutionBaseDto,
    ReportExecutionCreateDto,
    ReportExecutionUpdateStatusDto,
    ReportExecutionViewDto,
    ReportExecutionFilterParams,
    
    # Output Execution DTOs
    ReportOutputExecutionBaseDto,
    ReportOutputExecutionCreateDto,
    ReportOutputExecutionUpdateStatusDto,
    ReportOutputExecutionViewDto,
    ReportOutputExecutionFilterParams,
)

# API integration functions for registering endpoints
from uno.reports.api_integration import (
    register_report_field_definition_endpoints,
    register_report_template_endpoints,
    register_report_trigger_endpoints,
    register_report_output_endpoints,
    register_report_execution_endpoints,
    register_report_output_execution_endpoints,
    register_reports_endpoints,
)

# Error types
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
)

__all__ = [
    # Domain Entities (DDD)
    "ReportFieldDefinition",
    "ReportTemplate",
    "ReportTrigger",
    "ReportOutput",
    "ReportExecution",
    "ReportOutputExecution",
    
    # Enum-like classes
    "ReportFieldType",
    "ReportTriggerType",
    "ReportOutputType",
    "ReportFormat", 
    "ReportExecutionStatus",
    
    # Domain Repositories
    "ReportFieldDefinitionRepository",
    "ReportTemplateRepository",
    "ReportTriggerRepository",
    "ReportOutputRepository",
    "ReportExecutionRepository",
    "ReportOutputExecutionRepository",
    
    # Domain Services
    "ReportFieldDefinitionService",
    "ReportTemplateService",
    "ReportTriggerService",
    "ReportOutputService",
    "ReportExecutionService",
    "ReportOutputExecutionService",
    
    # Domain Provider
    "get_reports_provider",
    "get_report_field_definition_service",
    "get_report_template_service",
    "get_report_trigger_service",
    "get_report_output_service",
    "get_report_execution_service",
    "get_report_output_execution_service",
    
    # Schema Managers
    "ReportFieldDefinitionSchemaManager",
    "ReportTemplateSchemaManager",
    "ReportTriggerSchemaManager",
    "ReportOutputSchemaManager",
    "ReportExecutionSchemaManager",
    "ReportOutputExecutionSchemaManager",
    
    # DTO Enums
    "ReportFieldTypeEnum",
    "ReportTriggerTypeEnum",
    "ReportOutputTypeEnum",
    "ReportFormatEnum",
    "ReportExecutionStatusEnum",
    
    # Field Definition DTOs
    "ReportFieldDefinitionBaseDto",
    "ReportFieldDefinitionCreateDto",
    "ReportFieldDefinitionUpdateDto",
    "ReportFieldDefinitionViewDto",
    "ReportFieldDefinitionFilterParams",
    
    # Template DTOs
    "ReportTemplateBaseDto",
    "ReportTemplateCreateDto",
    "ReportTemplateUpdateDto",
    "ReportTemplateViewDto",
    "ReportTemplateFilterParams",
    
    # Trigger DTOs
    "ReportTriggerBaseDto",
    "ReportTriggerCreateDto",
    "ReportTriggerUpdateDto",
    "ReportTriggerViewDto",
    "ReportTriggerFilterParams",
    
    # Output DTOs
    "ReportOutputBaseDto",
    "ReportOutputCreateDto",
    "ReportOutputUpdateDto",
    "ReportOutputViewDto",
    "ReportOutputFilterParams",
    
    # Execution DTOs
    "ReportExecutionBaseDto",
    "ReportExecutionCreateDto",
    "ReportExecutionUpdateStatusDto",
    "ReportExecutionViewDto",
    "ReportExecutionFilterParams",
    
    # Output Execution DTOs
    "ReportOutputExecutionBaseDto",
    "ReportOutputExecutionCreateDto",
    "ReportOutputExecutionUpdateStatusDto",
    "ReportOutputExecutionViewDto",
    "ReportOutputExecutionFilterParams",
    
    # API integration functions
    "register_report_field_definition_endpoints",
    "register_report_template_endpoints",
    "register_report_trigger_endpoints",
    "register_report_output_endpoints",
    "register_report_execution_endpoints",
    "register_report_output_execution_endpoints",
    "register_reports_endpoints",
    
    # Error types
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
]
