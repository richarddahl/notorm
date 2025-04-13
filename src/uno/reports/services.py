# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Service implementations for the reports module.

This module provides concrete implementations of the service interfaces
defined in the interfaces module, building upon the repository layer.
"""

from typing import List, Optional, Dict, Any, cast, Tuple, TypeVar
from datetime import datetime, timedelta
import hashlib
import json
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.base import UnoError, ErrorCode
from uno.dependencies.interfaces import UnoServiceProtocol
from uno.reports.interfaces import (
    ReportTemplateServiceProtocol,
    ReportFieldServiceProtocol,
    ReportExecutionServiceProtocol,
    ReportTriggerServiceProtocol,
    ReportOutputServiceProtocol,
)
from uno.reports.repositories import (
    ReportTemplateRepository,
    ReportFieldDefinitionRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
    ReportError,
)
from uno.reports.objs import (
    ReportTemplate,
    ReportFieldDefinition,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
    ReportExecutionStatus,
)


T = TypeVar('T')


class ReportTemplateService(UnoServiceProtocol, ReportTemplateServiceProtocol):
    """Service for managing report templates."""

    def __init__(
        self,
        session: AsyncSession,
        template_repository: ReportTemplateRepository,
        field_repository: ReportFieldDefinitionRepository,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service with required repositories.
        
        Args:
            session: SQLAlchemy async session
            template_repository: Repository for report templates
            field_repository: Repository for report field definitions
            logger: Optional logger
        """
        self.session = session
        self.template_repository = template_repository
        self.field_repository = field_repository
        self.logger = logger or logging.getLogger(__name__)
    
    async def create_template(
        self, 
        template_data: Dict[str, Any]
    ) -> Result[ReportTemplate, ReportError]:
        """Create a new report template."""
        try:
            # Extract fields data if present
            fields_data = template_data.pop("fields", [])
            
            # Create the template
            template = ReportTemplate(**template_data)
            result = await self.template_repository.create(template, self.session)
            
            if result.is_failure:
                return result
            
            created_template = result.value
            
            # Create fields if provided
            if fields_data:
                for field_data in fields_data:
                    field_data["report_template_id"] = created_template.id
                    field = ReportFieldDefinition(**field_data)
                    await self.field_repository.create(field, self.session)
            
            # Get the full template with relationships
            return await self.template_repository.get_by_id(created_template.id, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to create report template: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_data=template_data
            ))
    
    async def update_template(
        self, 
        template_id: str, 
        template_data: Dict[str, Any]
    ) -> Result[ReportTemplate, ReportError]:
        """Update an existing report template."""
        try:
            # First get the existing template
            template_result = await self.template_repository.get_by_id(template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            existing_template = template_result.value
            if existing_template is None:
                return Failure(ReportError(
                    f"Template with ID {template_id} not found",
                    ErrorCode.NOT_FOUND,
                    template_id=template_id
                ))
            
            # Update fields from template_data
            for key, value in template_data.items():
                if key != "fields" and hasattr(existing_template, key):
                    setattr(existing_template, key, value)
            
            # Update the template
            update_result = await self.template_repository.update(
                existing_template, 
                self.session
            )
            
            if update_result.is_failure:
                return update_result
            
            # Handle fields if provided
            if "fields" in template_data:
                # This is a complex operation that would require deleting/updating/creating fields
                # For now, we'll skip this part and indicate that fields should be updated separately
                self.logger.info(
                    "Fields were provided in update_template but are handled separately. "
                    "Use the field service to manage fields."
                )
            
            # Return the updated template
            return await self.template_repository.get_by_id(template_id, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to update report template: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id,
                template_data=template_data
            ))
    
    async def delete_template(
        self, 
        template_id: str
    ) -> Result[bool, ReportError]:
        """Delete a report template."""
        try:
            # Check if template exists
            template_result = await self.template_repository.get_by_id(template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            if template_result.value is None:
                return Failure(ReportError(
                    f"Template with ID {template_id} not found",
                    ErrorCode.NOT_FOUND,
                    template_id=template_id
                ))
            
            # Delete the template (cascade delete should handle related entities)
            return await self.template_repository.delete(template_id, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to delete report template: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id
            ))
    
    async def get_template(
        self, 
        template_id: str
    ) -> Result[Optional[ReportTemplate], ReportError]:
        """Get a report template by ID."""
        try:
            return await self.template_repository.get_by_id(template_id, self.session)
        except Exception as e:
            return Failure(ReportError(
                f"Failed to get report template: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id
            ))
    
    async def list_templates(
        self, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Result[List[ReportTemplate], ReportError]:
        """List report templates, optionally filtered."""
        try:
            return await self.template_repository.list_templates(filters, self.session)
        except Exception as e:
            return Failure(ReportError(
                f"Failed to list report templates: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                filters=filters
            ))
    
    async def clone_template(
        self, 
        template_id: str, 
        new_name: str
    ) -> Result[ReportTemplate, ReportError]:
        """Clone an existing template with a new name."""
        try:
            # Get the source template
            template_result = await self.template_repository.get_by_id(template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            source_template = template_result.value
            if source_template is None:
                return Failure(ReportError(
                    f"Template with ID {template_id} not found",
                    ErrorCode.NOT_FOUND,
                    template_id=template_id
                ))
            
            # Create new template with the same data but a new name
            template_data = source_template.model_dump(exclude={"id", "fields", "triggers", "outputs", "executions"})
            template_data["name"] = new_name
            
            # Create the new template
            new_template = ReportTemplate(**template_data)
            create_result = await self.template_repository.create(new_template, self.session)
            
            if create_result.is_failure:
                return create_result
                
            new_template_id = create_result.value.id
            
            # Clone fields
            field_result = await self.field_repository.list_by_template(template_id, self.session)
            if field_result.is_success and field_result.value:
                for field in field_result.value:
                    field_data = field.model_dump(exclude={"id", "parent_field", "child_fields", "templates"})
                    field_data["report_template_id"] = new_template_id
                    new_field = ReportFieldDefinition(**field_data)
                    await self.field_repository.create(new_field, self.session)
            
            # Get the full new template with relationships
            return await self.template_repository.get_by_id(new_template_id, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to clone report template: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id,
                new_name=new_name
            ))


class ReportFieldService(UnoServiceProtocol, ReportFieldServiceProtocol):
    """Service for managing report fields."""

    def __init__(
        self,
        session: AsyncSession,
        template_repository: ReportTemplateRepository,
        field_repository: ReportFieldDefinitionRepository,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service with required repositories.
        
        Args:
            session: SQLAlchemy async session
            template_repository: Repository for report templates
            field_repository: Repository for report field definitions
            logger: Optional logger
        """
        self.session = session
        self.template_repository = template_repository
        self.field_repository = field_repository
        self.logger = logger or logging.getLogger(__name__)
    
    async def add_field(
        self, 
        template_id: str, 
        field_data: Dict[str, Any]
    ) -> Result[ReportFieldDefinition, ReportError]:
        """Add a field to a report template."""
        try:
            # Check if template exists
            template_result = await self.template_repository.get_by_id(template_id, self.session)
            if template_result.is_failure:
                return Failure(ReportError(
                    f"Failed to get template: {template_result.error}",
                    ErrorCode.OPERATION_FAILED,
                    template_id=template_id
                ))
                
            if template_result.value is None:
                return Failure(ReportError(
                    f"Template with ID {template_id} not found",
                    ErrorCode.NOT_FOUND,
                    template_id=template_id
                ))
            
            # Add template ID to field data
            field_data["report_template_id"] = template_id
            
            # Create the field
            field = ReportFieldDefinition(**field_data)
            return await self.field_repository.create(field, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to add field to template: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id,
                field_data=field_data
            ))
    
    async def update_field(
        self, 
        field_id: str, 
        field_data: Dict[str, Any]
    ) -> Result[ReportFieldDefinition, ReportError]:
        """Update a field definition."""
        try:
            # Get the existing field
            field_result = await self.field_repository.get_by_id(field_id, self.session)
            if field_result.is_failure:
                return field_result
                
            existing_field = field_result.value
            if existing_field is None:
                return Failure(ReportError(
                    f"Field with ID {field_id} not found",
                    ErrorCode.NOT_FOUND,
                    field_id=field_id
                ))
            
            # Update fields
            for key, value in field_data.items():
                if key not in ["parent_field", "child_fields", "templates"] and hasattr(existing_field, key):
                    setattr(existing_field, key, value)
            
            # Update the field
            return await self.field_repository.update(existing_field, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to update field: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                field_id=field_id,
                field_data=field_data
            ))
    
    async def delete_field(
        self, 
        field_id: str
    ) -> Result[bool, ReportError]:
        """Delete a field from a report template."""
        try:
            # Check if field exists
            field_result = await self.field_repository.get_by_id(field_id, self.session)
            if field_result.is_failure:
                return field_result
                
            if field_result.value is None:
                return Failure(ReportError(
                    f"Field with ID {field_id} not found",
                    ErrorCode.NOT_FOUND,
                    field_id=field_id
                ))
            
            # Delete the field
            return await self.field_repository.delete(field_id, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to delete field: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                field_id=field_id
            ))
    
    async def get_available_fields(
        self, 
        base_object_type: str
    ) -> Result[List[Dict[str, Any]], ReportError]:
        """Get available fields for a specific object type."""
        try:
            # This would involve inspecting the database schema or metadata
            # For now, we'll return a placeholder implementation
            available_fields = []
            
            # DB Columns (would come from schema inspection)
            available_fields.append({
                "name": "id",
                "display_name": "ID",
                "field_type": ReportFieldType.DB_COLUMN,
                "field_config": {
                    "table": base_object_type,
                    "column": "id"
                }
            })
            
            available_fields.append({
                "name": "created_at",
                "display_name": "Created At",
                "field_type": ReportFieldType.DB_COLUMN,
                "field_config": {
                    "table": base_object_type,
                    "column": "created_at"
                }
            })
            
            # Attributes (would come from attributes module)
            available_fields.append({
                "name": "status",
                "display_name": "Status",
                "field_type": ReportFieldType.ATTRIBUTE,
                "field_config": {
                    "attribute_type_id": "status"
                }
            })
            
            # Methods (would come from reflection)
            available_fields.append({
                "name": "full_name",
                "display_name": "Full Name",
                "field_type": ReportFieldType.METHOD,
                "field_config": {
                    "method": "get_full_name",
                    "module": f"uno.domain.{base_object_type.lower()}"
                }
            })
            
            return Success(available_fields)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to get available fields: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                base_object_type=base_object_type
            ))
    
    async def validate_field_config(
        self, 
        field_type: str, 
        field_config: Dict[str, Any]
    ) -> Result[bool, ReportError]:
        """Validate a field configuration."""
        try:
            # Validate based on field type
            if field_type == ReportFieldType.DB_COLUMN:
                required_props = ["table", "column"]
                for prop in required_props:
                    if prop not in field_config:
                        return Failure(ReportError(
                            f"Field config for DB_COLUMN must include {prop}",
                            ErrorCode.VALIDATION_ERROR,
                            field_type=field_type,
                            field_config=field_config
                        ))
            
            elif field_type == ReportFieldType.ATTRIBUTE:
                if "attribute_type_id" not in field_config:
                    return Failure(ReportError(
                        "Field config for ATTRIBUTE must include attribute_type_id",
                        ErrorCode.VALIDATION_ERROR,
                        field_type=field_type,
                        field_config=field_config
                    ))
            
            elif field_type == ReportFieldType.METHOD:
                required_props = ["method", "module"]
                for prop in required_props:
                    if prop not in field_config:
                        return Failure(ReportError(
                            f"Field config for METHOD must include {prop}",
                            ErrorCode.VALIDATION_ERROR,
                            field_type=field_type,
                            field_config=field_config
                        ))
            
            elif field_type == ReportFieldType.QUERY:
                if "query_id" not in field_config:
                    return Failure(ReportError(
                        "Field config for QUERY must include query_id",
                        ErrorCode.VALIDATION_ERROR,
                        field_type=field_type,
                        field_config=field_config
                    ))
            
            elif field_type == ReportFieldType.AGGREGATE:
                required_props = ["function", "field"]
                for prop in required_props:
                    if prop not in field_config:
                        return Failure(ReportError(
                            f"Field config for AGGREGATE must include {prop}",
                            ErrorCode.VALIDATION_ERROR,
                            field_type=field_type,
                            field_config=field_config
                        ))
            
            elif field_type == ReportFieldType.RELATED:
                required_props = ["relation", "field"]
                for prop in required_props:
                    if prop not in field_config:
                        return Failure(ReportError(
                            f"Field config for RELATED must include {prop}",
                            ErrorCode.VALIDATION_ERROR,
                            field_type=field_type,
                            field_config=field_config
                        ))
            
            return Success(True)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to validate field config: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                field_type=field_type,
                field_config=field_config
            ))
    
    async def get_field_by_id(
        self,
        field_id: str
    ) -> Result[Optional[ReportFieldDefinition], ReportError]:
        """Get a field by ID."""
        try:
            return await self.field_repository.get_by_id(field_id, self.session)
        except Exception as e:
            return Failure(ReportError(
                f"Failed to get field: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                field_id=field_id
            ))
    
    async def list_fields_by_template(
        self,
        template_id: str
    ) -> Result[List[ReportFieldDefinition], ReportError]:
        """List all fields for a template."""
        try:
            return await self.field_repository.list_by_template(template_id, self.session)
        except Exception as e:
            return Failure(ReportError(
                f"Failed to list fields: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id
            ))


class ReportExecutionService(UnoServiceProtocol, ReportExecutionServiceProtocol):
    """Service for executing reports."""

    def __init__(
        self,
        session: AsyncSession,
        template_repository: ReportTemplateRepository,
        field_repository: ReportFieldDefinitionRepository,
        execution_repository: ReportExecutionRepository,
        output_execution_repository: ReportOutputExecutionRepository,
        output_repository: ReportOutputRepository,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service with required repositories.
        
        Args:
            session: SQLAlchemy async session
            template_repository: Repository for report templates
            field_repository: Repository for report field definitions
            execution_repository: Repository for report executions
            output_execution_repository: Repository for report output executions
            output_repository: Repository for report outputs
            logger: Optional logger
        """
        self.session = session
        self.template_repository = template_repository
        self.field_repository = field_repository
        self.execution_repository = execution_repository
        self.output_execution_repository = output_execution_repository
        self.output_repository = output_repository
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute_report(
        self, 
        template_id: str, 
        parameters: Optional[Dict[str, Any]] = None,
        trigger_type: str = "manual",
        user_id: Optional[str] = None
    ) -> Result[ReportExecution, ReportError]:
        """Execute a report with optional parameters."""
        try:
            # Get the template
            template_result = await self.template_repository.get_by_id(template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            template = template_result.value
            if template is None:
                return Failure(ReportError(
                    f"Template with ID {template_id} not found",
                    ErrorCode.NOT_FOUND,
                    template_id=template_id
                ))
            
            # Validate parameters against template parameter definitions
            if parameters:
                for param_name, param_def in template.parameter_definitions.items():
                    if param_name not in parameters and param_def.get("required", False):
                        return Failure(ReportError(
                            f"Required parameter '{param_name}' is missing",
                            ErrorCode.VALIDATION_ERROR,
                            parameter=param_name
                        ))
            
            # Create execution record
            execution = ReportExecution(
                report_template_id=template_id,
                triggered_by=user_id or "system",
                trigger_type=trigger_type,
                parameters=parameters or {},
                status=ReportExecutionStatus.PENDING,
                started_at=datetime.utcnow()
            )
            
            # Save the execution
            execution_result = await self.execution_repository.create(execution, self.session)
            if execution_result.is_failure:
                return execution_result
            
            execution = execution_result.value
            
            # Get output configurations
            outputs_result = await self.output_repository.list_by_template(template_id, self.session)
            if outputs_result.is_failure:
                return Failure(ReportError(
                    f"Failed to get outputs: {outputs_result.error}",
                    ErrorCode.OPERATION_FAILED,
                    execution_id=execution.id
                ))
            
            # Create output execution records for each output
            for output in outputs_result.value:
                if output.is_active:
                    output_execution = ReportOutputExecution(
                        report_execution_id=execution.id,
                        report_output_id=output.id,
                        status=ReportExecutionStatus.PENDING
                    )
                    await self.output_execution_repository.create(output_execution, self.session)
            
            # Update execution status to in_progress
            await self.execution_repository.update_status(
                execution.id,
                ReportExecutionStatus.IN_PROGRESS,
                session=self.session
            )
            
            # In a real implementation, we would now start a background task to
            # actually execute the report. For now, we'll just return the execution record.
            
            return Success(execution)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to execute report: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id,
                parameters=parameters
            ))
    
    async def get_execution_status(
        self, 
        execution_id: str
    ) -> Result[Dict[str, Any], ReportError]:
        """Get the status of a report execution."""
        try:
            # Get the execution
            execution_result = await self.execution_repository.get_by_id(execution_id, self.session)
            if execution_result.is_failure:
                return execution_result
                
            execution = execution_result.value
            if execution is None:
                return Failure(ReportError(
                    f"Execution with ID {execution_id} not found",
                    ErrorCode.NOT_FOUND,
                    execution_id=execution_id
                ))
            
            # Get output executions
            output_executions_result = await self.output_execution_repository.list_by_execution(
                execution_id, 
                self.session
            )
            
            output_statuses = []
            if output_executions_result.is_success:
                for output_execution in output_executions_result.value:
                    output_statuses.append({
                        "id": output_execution.id,
                        "output_id": output_execution.report_output_id,
                        "status": output_execution.status,
                        "completed_at": output_execution.completed_at,
                        "output_location": output_execution.output_location,
                        "output_size_bytes": output_execution.output_size_bytes
                    })
            
            # Build status response
            status_info = {
                "id": execution.id,
                "template_id": execution.report_template_id,
                "status": execution.status,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "error_details": execution.error_details,
                "row_count": execution.row_count,
                "execution_time_ms": execution.execution_time_ms,
                "outputs": output_statuses
            }
            
            return Success(status_info)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to get execution status: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                execution_id=execution_id
            ))
    
    async def cancel_execution(
        self, 
        execution_id: str
    ) -> Result[bool, ReportError]:
        """Cancel a running report execution."""
        try:
            # Get the execution
            execution_result = await self.execution_repository.get_by_id(execution_id, self.session)
            if execution_result.is_failure:
                return execution_result
                
            execution = execution_result.value
            if execution is None:
                return Failure(ReportError(
                    f"Execution with ID {execution_id} not found",
                    ErrorCode.NOT_FOUND,
                    execution_id=execution_id
                ))
            
            # Check if execution can be cancelled
            if execution.status not in [ReportExecutionStatus.PENDING, ReportExecutionStatus.IN_PROGRESS]:
                return Failure(ReportError(
                    f"Execution with status '{execution.status}' cannot be cancelled",
                    ErrorCode.VALIDATION_ERROR,
                    execution_id=execution_id,
                    status=execution.status
                ))
            
            # Update execution status to cancelled
            status_result = await self.execution_repository.update_status(
                execution_id,
                ReportExecutionStatus.CANCELLED,
                session=self.session
            )
            
            if status_result.is_failure:
                return status_result
            
            # Cancel all pending output executions
            output_executions_result = await self.output_execution_repository.list_by_execution(
                execution_id, 
                self.session
            )
            
            if output_executions_result.is_success:
                for output_execution in output_executions_result.value:
                    if output_execution.status in [ReportExecutionStatus.PENDING, ReportExecutionStatus.IN_PROGRESS]:
                        await self.output_execution_repository.update(
                            ReportOutputExecution(
                                id=output_execution.id,
                                status=ReportExecutionStatus.CANCELLED,
                                completed_at=datetime.utcnow()
                            ),
                            self.session
                        )
            
            return Success(True)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to cancel execution: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                execution_id=execution_id
            ))
    
    async def get_execution_result(
        self, 
        execution_id: str,
        format: Optional[str] = None
    ) -> Result[Any, ReportError]:
        """Get the result of a completed report execution."""
        try:
            # Get the execution
            execution_result = await self.execution_repository.get_by_id(execution_id, self.session)
            if execution_result.is_failure:
                return execution_result
                
            execution = execution_result.value
            if execution is None:
                return Failure(ReportError(
                    f"Execution with ID {execution_id} not found",
                    ErrorCode.NOT_FOUND,
                    execution_id=execution_id
                ))
            
            # Check if execution is completed
            if execution.status != ReportExecutionStatus.COMPLETED:
                return Failure(ReportError(
                    f"Execution is not completed (status: {execution.status})",
                    ErrorCode.VALIDATION_ERROR,
                    execution_id=execution_id,
                    status=execution.status
                ))
            
            # In a real implementation, we would retrieve the result data from storage
            # For now, we'll return a placeholder
            
            # Get template and fields
            template_result = await self.template_repository.get_by_id(execution.report_template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            template = template_result.value
            
            # Get fields if field_repository is available
            if self.field_repository:
                fields_result = await self.field_repository.list_by_template(template.id, self.session)
                if fields_result.is_failure:
                    return fields_result
                    
                fields = fields_result.value
            else:
                # Use empty field list if field_repository is not available
                fields = []
            
            # Build a sample result
            result_data = {
                "execution_id": execution_id,
                "template_id": template.id,
                "template_name": template.name,
                "executed_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "row_count": execution.row_count or 0,
                "execution_time_ms": execution.execution_time_ms or 0,
                "parameters": execution.parameters,
                "columns": [field.name for field in fields],
                "data": []  # Would contain the actual data rows
            }
            
            # If a specific format is requested
            if format:
                # Convert to requested format (in real implementation)
                if format == "csv":
                    return Success("id,name,value\n1,test,123")
                elif format == "json":
                    return Success(json.dumps(result_data))
                else:
                    return Failure(ReportError(
                        f"Unsupported format: {format}",
                        ErrorCode.VALIDATION_ERROR,
                        format=format
                    ))
            
            return Success(result_data)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to get execution result: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                execution_id=execution_id,
                format=format
            ))
    
    async def list_executions(
        self, 
        template_id: Optional[str] = None, 
        status: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 100
    ) -> Result[List[ReportExecution], ReportError]:
        """List report executions, optionally filtered."""
        try:
            # For now, we only support filtering by template and status
            if template_id:
                return await self.execution_repository.list_by_template(
                    template_id, 
                    status=status,
                    limit=limit,
                    session=self.session
                )
            
            # In a real implementation, we would support more filters
            # For now, return an error for unsupported filters
            return Failure(ReportError(
                "Filtering executions without a template_id is not yet implemented",
                ErrorCode.NOT_IMPLEMENTED,
                status=status,
                date_range=date_range
            ))
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to list executions: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id,
                status=status,
                date_range=date_range,
                limit=limit
            ))


class ReportTriggerService(UnoServiceProtocol, ReportTriggerServiceProtocol):
    """Service for managing report triggers."""

    def __init__(
        self,
        session: AsyncSession,
        template_repository: ReportTemplateRepository,
        trigger_repository: ReportTriggerRepository,
        execution_service: ReportExecutionService,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service with required repositories and services.
        
        Args:
            session: SQLAlchemy async session
            template_repository: Repository for report templates
            trigger_repository: Repository for report triggers
            execution_service: Service for executing reports
            logger: Optional logger
        """
        self.session = session
        self.template_repository = template_repository
        self.trigger_repository = trigger_repository
        self.execution_service = execution_service
        self.logger = logger or logging.getLogger(__name__)
    
    async def list_triggers_by_template(
        self,
        template_id: str
    ) -> Result[List[ReportTrigger], ReportError]:
        """List triggers for a template."""
        try:
            # Check if template exists
            template_result = await self.template_repository.get_by_id(template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            if template_result.value is None:
                return Failure(ReportError(
                    f"Template with ID {template_id} not found",
                    ErrorCode.NOT_FOUND,
                    template_id=template_id
                ))
                
            # List triggers for template
            return await self.trigger_repository.list_by_template(template_id, self.session)
        except Exception as e:
            return Failure(ReportError(
                f"Failed to list triggers: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id
            ))
    
    async def create_trigger(
        self, 
        template_id: str, 
        trigger_data: Dict[str, Any]
    ) -> Result[ReportTrigger, ReportError]:
        """Create a new trigger for a report template."""
        try:
            # Check if template exists
            template_result = await self.template_repository.get_by_id(template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            if template_result.value is None:
                return Failure(ReportError(
                    f"Template with ID {template_id} not found",
                    ErrorCode.NOT_FOUND,
                    template_id=template_id
                ))
            
            # Add template ID to trigger data
            trigger_data["report_template_id"] = template_id
            
            # Create the trigger
            trigger = ReportTrigger(**trigger_data)
            return await self.trigger_repository.create(trigger, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to create trigger: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id,
                trigger_data=trigger_data
            ))
    
    async def update_trigger(
        self, 
        trigger_id: str, 
        trigger_data: Dict[str, Any]
    ) -> Result[ReportTrigger, ReportError]:
        """Update an existing trigger."""
        try:
            # Get the existing trigger
            trigger_result = await self.trigger_repository.get_by_id(trigger_id, self.session)
            if trigger_result.is_failure:
                return trigger_result
                
            existing_trigger = trigger_result.value
            if existing_trigger is None:
                return Failure(ReportError(
                    f"Trigger with ID {trigger_id} not found",
                    ErrorCode.NOT_FOUND,
                    trigger_id=trigger_id
                ))
            
            # Update fields
            for key, value in trigger_data.items():
                if key != "report_template" and hasattr(existing_trigger, key):
                    setattr(existing_trigger, key, value)
            
            # Update the trigger
            return await self.trigger_repository.update(existing_trigger, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to update trigger: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                trigger_id=trigger_id,
                trigger_data=trigger_data
            ))
    
    async def delete_trigger(
        self, 
        trigger_id: str
    ) -> Result[bool, ReportError]:
        """Delete a trigger."""
        try:
            # Check if trigger exists
            trigger_result = await self.trigger_repository.get_by_id(trigger_id, self.session)
            if trigger_result.is_failure:
                return trigger_result
                
            if trigger_result.value is None:
                return Failure(ReportError(
                    f"Trigger with ID {trigger_id} not found",
                    ErrorCode.NOT_FOUND,
                    trigger_id=trigger_id
                ))
            
            # Delete the trigger
            return await self.trigger_repository.delete(trigger_id, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to delete trigger: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                trigger_id=trigger_id
            ))
    
    async def enable_trigger(
        self, 
        trigger_id: str
    ) -> Result[bool, ReportError]:
        """Enable a trigger."""
        try:
            # Get the existing trigger
            trigger_result = await self.trigger_repository.get_by_id(trigger_id, self.session)
            if trigger_result.is_failure:
                return trigger_result
                
            existing_trigger = trigger_result.value
            if existing_trigger is None:
                return Failure(ReportError(
                    f"Trigger with ID {trigger_id} not found",
                    ErrorCode.NOT_FOUND,
                    trigger_id=trigger_id
                ))
            
            # Enable the trigger
            existing_trigger.is_active = True
            await self.trigger_repository.update(existing_trigger, self.session)
            
            return Success(True)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to enable trigger: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                trigger_id=trigger_id
            ))
    
    async def disable_trigger(
        self, 
        trigger_id: str
    ) -> Result[bool, ReportError]:
        """Disable a trigger."""
        try:
            # Get the existing trigger
            trigger_result = await self.trigger_repository.get_by_id(trigger_id, self.session)
            if trigger_result.is_failure:
                return trigger_result
                
            existing_trigger = trigger_result.value
            if existing_trigger is None:
                return Failure(ReportError(
                    f"Trigger with ID {trigger_id} not found",
                    ErrorCode.NOT_FOUND,
                    trigger_id=trigger_id
                ))
            
            # Disable the trigger
            existing_trigger.is_active = False
            await self.trigger_repository.update(existing_trigger, self.session)
            
            return Success(True)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to disable trigger: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                trigger_id=trigger_id
            ))
    
    async def handle_event(
        self, 
        event_type: str, 
        event_data: Dict[str, Any]
    ) -> Result[List[str], ReportError]:
        """Handle an event that might trigger reports (returns execution IDs)."""
        try:
            # Get triggers for this event type
            triggers_result = await self.trigger_repository.list_by_event_type(event_type, self.session)
            if triggers_result.is_failure:
                return triggers_result
                
            triggers = triggers_result.value
            if not triggers:
                # No triggers for this event type
                return Success([])
            
            # Execute reports for matching triggers
            execution_ids = []
            for trigger in triggers:
                # Check if entity type matches (if specified)
                if trigger.entity_type and event_data.get("entity_type") != trigger.entity_type:
                    continue
                
                # Check for any additional conditions in trigger_config
                # This would be more complex in a real implementation
                
                # Execute the report
                execution_result = await self.execution_service.execute_report(
                    trigger.report_template_id,
                    parameters=event_data,
                    trigger_type=ReportTriggerType.EVENT,
                    session=self.session
                )
                
                if execution_result.is_success:
                    execution_ids.append(execution_result.value.id)
                    
                    # Update last_triggered timestamp
                    await self.trigger_repository.update_last_triggered(
                        trigger.id,
                        datetime.utcnow(),
                        self.session
                    )
                else:
                    self.logger.error(
                        f"Failed to execute report for trigger {trigger.id}: {execution_result.error}"
                    )
            
            return Success(execution_ids)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to handle event: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                event_type=event_type,
                event_data=event_data
            ))
    
    async def check_query_triggers(self) -> Result[List[str], ReportError]:
        """Check query-based triggers and execute reports if conditions are met."""
        try:
            # Get all active query triggers
            stmt = (
                select(ReportTriggerModel)
                .options(joinedload(ReportTriggerModel.report_template))
                .where(
                    and_(
                        ReportTriggerModel.trigger_type == ReportTriggerType.QUERY,
                        ReportTriggerModel.is_active == True
                    )
                )
            )
            result = await self.session.execute(stmt)
            triggers = [ReportTrigger.from_orm(model) for model in result.scalars().all()]
            
            if not triggers:
                # No query triggers to check
                return Success([])
            
            # Execute reports for triggers whose queries match
            execution_ids = []
            for trigger in triggers:
                # In a real implementation, we would execute the query and check results
                # For now, we'll just execute reports for all query triggers
                
                execution_result = await self.execution_service.execute_report(
                    trigger.report_template_id,
                    parameters={},
                    trigger_type=ReportTriggerType.QUERY,
                    session=self.session
                )
                
                if execution_result.is_success:
                    execution_ids.append(execution_result.value.id)
                    
                    # Update last_triggered timestamp
                    await self.trigger_repository.update_last_triggered(
                        trigger.id,
                        datetime.utcnow(),
                        self.session
                    )
                else:
                    self.logger.error(
                        f"Failed to execute report for query trigger {trigger.id}: {execution_result.error}"
                    )
            
            return Success(execution_ids)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to check query triggers: {str(e)}",
                ErrorCode.OPERATION_FAILED
            ))
    
    async def process_scheduled_triggers(self) -> Result[List[str], ReportError]:
        """Process scheduled triggers and execute reports if due."""
        try:
            # Get all active scheduled triggers
            triggers_result = await self.trigger_repository.list_active_scheduled_triggers(self.session)
            if triggers_result.is_failure:
                return triggers_result
                
            triggers = triggers_result.value
            if not triggers:
                # No scheduled triggers to process
                return Success([])
            
            # Check which triggers are due
            execution_ids = []
            now = datetime.utcnow()
            
            for trigger in triggers:
                # Skip triggers with invalid schedule
                if not trigger.schedule:
                    continue
                
                # Parse the schedule and check if it's due
                is_due = False
                
                # In a real implementation, we would use a library like APScheduler
                # or parse cron-like expressions to determine if a trigger is due
                
                # For now, use a simple implementation based on last_triggered
                if not trigger.last_triggered:
                    # Never triggered before, so it's due
                    is_due = True
                else:
                    # Parse the schedule string
                    # Format: "interval:<value>:<unit>" or "cron:<expression>"
                    try:
                        if trigger.schedule.startswith("interval:"):
                            parts = trigger.schedule.split(":")
                            if len(parts) >= 3:
                                value = int(parts[1])
                                unit = parts[2]
                                
                                if unit == "minutes":
                                    is_due = now >= trigger.last_triggered + timedelta(minutes=value)
                                elif unit == "hours":
                                    is_due = now >= trigger.last_triggered + timedelta(hours=value)
                                elif unit == "days":
                                    is_due = now >= trigger.last_triggered + timedelta(days=value)
                        elif trigger.schedule.startswith("cron:"):
                            # For cron expressions, we would use a library like croniter
                            # For now, just log that cron is not implemented
                            self.logger.warning(f"Cron schedules not implemented: {trigger.schedule}")
                    except Exception as e:
                        self.logger.error(f"Error parsing schedule {trigger.schedule}: {str(e)}")
                
                # If the trigger is due, execute the report
                if is_due:
                    execution_result = await self.execution_service.execute_report(
                        trigger.report_template_id,
                        parameters={},
                        trigger_type=ReportTriggerType.SCHEDULED,
                        session=self.session
                    )
                    
                    if execution_result.is_success:
                        execution_ids.append(execution_result.value.id)
                        
                        # Update last_triggered timestamp
                        await self.trigger_repository.update_last_triggered(
                            trigger.id,
                            now,
                            self.session
                        )
                    else:
                        self.logger.error(
                            f"Failed to execute report for scheduled trigger {trigger.id}: {execution_result.error}"
                        )
            
            return Success(execution_ids)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to process scheduled triggers: {str(e)}",
                ErrorCode.OPERATION_FAILED
            ))


class ReportOutputService(UnoServiceProtocol, ReportOutputServiceProtocol):
    """Service for managing report outputs."""

    def __init__(
        self,
        session: AsyncSession,
        template_repository: ReportTemplateRepository,
        output_repository: ReportOutputRepository,
        execution_repository: ReportExecutionRepository,
        output_execution_repository: ReportOutputExecutionRepository,
        field_repository: Optional[ReportFieldDefinitionRepository] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service with required repositories.
        
        Args:
            session: SQLAlchemy async session
            template_repository: Repository for report templates
            output_repository: Repository for report outputs
            execution_repository: Repository for report executions
            output_execution_repository: Repository for report output executions
            field_repository: Repository for report field definitions (optional)
            logger: Optional logger
        """
        self.session = session
        self.template_repository = template_repository
        self.output_repository = output_repository
        self.execution_repository = execution_repository
        self.output_execution_repository = output_execution_repository
        self.field_repository = field_repository
        self.logger = logger or logging.getLogger(__name__)
        
    async def list_outputs_by_template(
        self,
        template_id: str
    ) -> Result[List[ReportOutput], ReportError]:
        """List output configurations for a template."""
        try:
            # Check if template exists
            template_result = await self.template_repository.get_by_id(template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            if template_result.value is None:
                return Failure(ReportError(
                    f"Template with ID {template_id} not found",
                    ErrorCode.NOT_FOUND,
                    template_id=template_id
                ))
                
            # List outputs for template
            return await self.output_repository.list_by_template(template_id, self.session)
        except Exception as e:
            return Failure(ReportError(
                f"Failed to list outputs: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id
            ))
    
    async def create_output_config(
        self, 
        template_id: str, 
        output_data: Dict[str, Any]
    ) -> Result[ReportOutput, ReportError]:
        """Create a new output configuration for a report template."""
        try:
            # Check if template exists
            template_result = await self.template_repository.get_by_id(template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            if template_result.value is None:
                return Failure(ReportError(
                    f"Template with ID {template_id} not found",
                    ErrorCode.NOT_FOUND,
                    template_id=template_id
                ))
            
            # Add template ID to output data
            output_data["report_template_id"] = template_id
            
            # Create the output
            output = ReportOutput(**output_data)
            return await self.output_repository.create(output, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to create output config: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                template_id=template_id,
                output_data=output_data
            ))
    
    async def update_output_config(
        self, 
        output_id: str, 
        output_data: Dict[str, Any]
    ) -> Result[ReportOutput, ReportError]:
        """Update an existing output configuration."""
        try:
            # Get the existing output
            output_result = await self.output_repository.get_by_id(output_id, self.session)
            if output_result.is_failure:
                return output_result
                
            existing_output = output_result.value
            if existing_output is None:
                return Failure(ReportError(
                    f"Output with ID {output_id} not found",
                    ErrorCode.NOT_FOUND,
                    output_id=output_id
                ))
            
            # Update fields
            for key, value in output_data.items():
                if key not in ["report_template", "output_executions"] and hasattr(existing_output, key):
                    setattr(existing_output, key, value)
            
            # Update the output
            return await self.output_repository.update(existing_output, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to update output config: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                output_id=output_id,
                output_data=output_data
            ))
    
    async def delete_output_config(
        self, 
        output_id: str
    ) -> Result[bool, ReportError]:
        """Delete an output configuration."""
        try:
            # Check if output exists
            output_result = await self.output_repository.get_by_id(output_id, self.session)
            if output_result.is_failure:
                return output_result
                
            if output_result.value is None:
                return Failure(ReportError(
                    f"Output with ID {output_id} not found",
                    ErrorCode.NOT_FOUND,
                    output_id=output_id
                ))
            
            # Delete the output
            return await self.output_repository.delete(output_id, self.session)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to delete output config: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                output_id=output_id
            ))
    
    async def format_report(
        self, 
        execution_id: str, 
        format: str
    ) -> Result[bytes, ReportError]:
        """Format a report result in the specified format."""
        try:
            # Check if format is supported
            if format not in [f.value for f in ReportFormat]:
                return Failure(ReportError(
                    f"Unsupported format: {format}",
                    ErrorCode.VALIDATION_ERROR,
                    format=format
                ))
            
            # Get the execution
            execution_result = await self.execution_repository.get_by_id(execution_id, self.session)
            if execution_result.is_failure:
                return execution_result
                
            execution = execution_result.value
            if execution is None:
                return Failure(ReportError(
                    f"Execution with ID {execution_id} not found",
                    ErrorCode.NOT_FOUND,
                    execution_id=execution_id
                ))
            
            # Check if execution is completed
            if execution.status != ReportExecutionStatus.COMPLETED:
                return Failure(ReportError(
                    f"Execution is not completed (status: {execution.status})",
                    ErrorCode.VALIDATION_ERROR,
                    execution_id=execution_id,
                    status=execution.status
                ))
            
            # Get template and fields
            template_result = await self.template_repository.get_by_id(execution.report_template_id, self.session)
            if template_result.is_failure:
                return template_result
                
            template = template_result.value
            
            # Get fields if field_repository is available
            if self.field_repository:
                fields_result = await self.field_repository.list_by_template(template.id, self.session)
                if fields_result.is_failure:
                    return fields_result
                    
                fields = fields_result.value
            else:
                # Use empty field list if field_repository is not available
                fields = []
            
            # In a real implementation, we would retrieve the result data and format it
            # For now, we'll return a placeholder
            
            if format == ReportFormat.CSV:
                # Generate CSV
                header = ",".join([f'"{field.name}"' for field in fields])
                return Success(f"{header}\n".encode("utf-8"))
                
            elif format == ReportFormat.JSON:
                # Generate JSON
                data = {
                    "execution_id": execution_id,
                    "template_id": template.id,
                    "template_name": template.name,
                    "fields": [field.name for field in fields],
                    "data": []  # Would contain the actual data
                }
                return Success(json.dumps(data).encode("utf-8"))
                
            elif format == ReportFormat.PDF:
                # Generate PDF (placeholder)
                return Success(b"%PDF-1.5\n%Mock PDF data")
                
            elif format == ReportFormat.EXCEL:
                # Generate Excel (placeholder)
                return Success(b"Mock Excel data")
                
            elif format == ReportFormat.HTML:
                # Generate HTML
                html = f"""<!DOCTYPE html>
                <html>
                <head>
                    <title>{template.name} Report</title>
                </head>
                <body>
                    <h1>{template.name}</h1>
                    <p>Execution ID: {execution_id}</p>
                    <p>Generated at: {execution.started_at}</p>
                    <table border="1">
                        <thead>
                            <tr>{"".join([f"<th>{field.name}</th>" for field in fields])}</tr>
                        </thead>
                        <tbody>
                            <!-- Data rows would go here -->
                        </tbody>
                    </table>
                </body>
                </html>"""
                return Success(html.encode("utf-8"))
                
            elif format == ReportFormat.TEXT:
                # Generate plain text
                text = f"{template.name} Report\n\n"
                text += f"Generated at: {execution.started_at}\n\n"
                text += "Fields: " + ", ".join([field.name for field in fields]) + "\n\n"
                return Success(text.encode("utf-8"))
            
            # Should never get here, but just in case
            return Failure(ReportError(
                f"Unhandled format: {format}",
                ErrorCode.INTERNAL_ERROR,
                format=format
            ))
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to format report: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                execution_id=execution_id,
                format=format
            ))
    
    async def deliver_report(
        self, 
        execution_id: str, 
        output_id: str
    ) -> Result[bool, ReportError]:
        """Deliver a report according to an output configuration."""
        try:
            # Get the execution
            execution_result = await self.execution_repository.get_by_id(execution_id, self.session)
            if execution_result.is_failure:
                return execution_result
                
            execution = execution_result.value
            if execution is None:
                return Failure(ReportError(
                    f"Execution with ID {execution_id} not found",
                    ErrorCode.NOT_FOUND,
                    execution_id=execution_id
                ))
            
            # Check if execution is completed
            if execution.status != ReportExecutionStatus.COMPLETED:
                return Failure(ReportError(
                    f"Execution is not completed (status: {execution.status})",
                    ErrorCode.VALIDATION_ERROR,
                    execution_id=execution_id,
                    status=execution.status
                ))
            
            # Get the output config
            output_result = await self.output_repository.get_by_id(output_id, self.session)
            if output_result.is_failure:
                return output_result
                
            output = output_result.value
            if output is None:
                return Failure(ReportError(
                    f"Output with ID {output_id} not found",
                    ErrorCode.NOT_FOUND,
                    output_id=output_id
                ))
            
            # Check if output is for the same template as the execution
            if output.report_template_id != execution.report_template_id:
                return Failure(ReportError(
                    "Output configuration is for a different template than the execution",
                    ErrorCode.VALIDATION_ERROR,
                    execution_id=execution_id,
                    execution_template_id=execution.report_template_id,
                    output_id=output_id,
                    output_template_id=output.report_template_id
                ))
            
            # Create or get the output execution record
            stmt = (
                select(ReportOutputExecutionModel)
                .where(
                    and_(
                        ReportOutputExecutionModel.report_execution_id == execution_id,
                        ReportOutputExecutionModel.report_output_id == output_id
                    )
                )
            )
            result = await self.session.execute(stmt)
            output_execution_model = result.scalars().first()
            
            if output_execution_model is None:
                # Create a new output execution record
                output_execution = ReportOutputExecution(
                    report_execution_id=execution_id,
                    report_output_id=output_id,
                    status=ReportExecutionStatus.IN_PROGRESS
                )
                output_execution_result = await self.output_execution_repository.create(
                    output_execution, 
                    self.session
                )
                
                if output_execution_result.is_failure:
                    return output_execution_result
                    
                output_execution = output_execution_result.value
            else:
                output_execution = ReportOutputExecution.from_orm(output_execution_model)
                
                # Check if already completed
                if output_execution.status == ReportExecutionStatus.COMPLETED:
                    return Success(True)
                
                # Update status to in progress
                output_execution.status = ReportExecutionStatus.IN_PROGRESS
                await self.output_execution_repository.update(output_execution, self.session)
            
            # Format the report
            format_result = await self.format_report(execution_id, output.format)
            if format_result.is_failure:
                # Update output execution to failed
                await self.output_execution_repository.update(
                    ReportOutputExecution(
                        id=output_execution.id,
                        status=ReportExecutionStatus.FAILED,
                        completed_at=datetime.utcnow(),
                        error_details=str(format_result.error)
                    ),
                    self.session
                )
                return format_result
                
            formatted_report = format_result.value
            
            # In a real implementation, we would deliver the report according to the output type
            # For now, we'll just log what would happen
            
            output_location = "unknown"
            output_size = len(formatted_report)
            
            if output.output_type == ReportOutputType.FILE:
                # Would write to a file
                output_location = output.output_config.get("path", "/tmp") + f"/{execution_id}.{output.format.lower()}"
                self.logger.info(f"Would write {output_size} bytes to {output_location}")
                
            elif output.output_type == ReportOutputType.EMAIL:
                # Would send an email
                recipients = output.output_config.get("recipients", [])
                output_location = f"email:{','.join(recipients)}"
                self.logger.info(f"Would email {output_size} bytes to {recipients}")
                
            elif output.output_type == ReportOutputType.WEBHOOK:
                # Would post to a webhook
                url = output.output_config.get("url", "")
                output_location = f"webhook:{url}"
                self.logger.info(f"Would post {output_size} bytes to {url}")
                
            elif output.output_type == ReportOutputType.NOTIFICATION:
                # Would send a notification
                channel = output.output_config.get("channel", "")
                output_location = f"notification:{channel}"
                self.logger.info(f"Would send notification to {channel}")
            
            # Update output execution to completed
            complete_result = await self.output_execution_repository.complete_output_execution(
                output_execution.id,
                output_location,
                output_size,
                self.session
            )
            
            if complete_result.is_failure:
                return complete_result
                
            return Success(True)
            
        except Exception as e:
            return Failure(ReportError(
                f"Failed to deliver report: {str(e)}",
                ErrorCode.OPERATION_FAILED,
                execution_id=execution_id,
                output_id=output_id
            ))