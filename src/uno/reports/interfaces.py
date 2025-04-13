# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Protocol definitions for the reports module.

This module defines the interfaces for reports repositories and services,
following the project's dependency injection pattern.
"""

from typing import List, Optional, Dict, Any, Protocol, TypeVar, runtime_checkable
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Result
from uno.reports.objs import (
    ReportTemplate,
    ReportFieldDefinition,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
)


T = TypeVar('T')
ReportError = TypeVar('ReportError')


# Repository protocols

@runtime_checkable
class ReportTemplateRepositoryProtocol(Protocol):
    """Protocol for report template repositories."""

    async def get_by_id(
        self, 
        template_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[Optional[ReportTemplate], ReportError]:
        """Get a report template by ID."""
        ...

    async def get_by_name(
        self, 
        name: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[Optional[ReportTemplate], ReportError]:
        """Get a report template by name."""
        ...

    async def list_templates(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        session: Optional[AsyncSession] = None
    ) -> Result[List[ReportTemplate], ReportError]:
        """List report templates, optionally filtered."""
        ...

    async def create(
        self, 
        template: ReportTemplate, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportTemplate, ReportError]:
        """Create a new report template."""
        ...

    async def update(
        self, 
        template: ReportTemplate, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportTemplate, ReportError]:
        """Update an existing report template."""
        ...

    async def delete(
        self, 
        template_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[bool, ReportError]:
        """Delete a report template by ID."""
        ...


@runtime_checkable
class ReportFieldDefinitionRepositoryProtocol(Protocol):
    """Protocol for report field definition repositories."""

    async def get_by_id(
        self, 
        field_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[Optional[ReportFieldDefinition], ReportError]:
        """Get a report field definition by ID."""
        ...

    async def list_by_template(
        self, 
        template_id: str,
        session: Optional[AsyncSession] = None
    ) -> Result[List[ReportFieldDefinition], ReportError]:
        """List field definitions for a template."""
        ...

    async def create(
        self, 
        field: ReportFieldDefinition, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportFieldDefinition, ReportError]:
        """Create a new field definition."""
        ...

    async def update(
        self, 
        field: ReportFieldDefinition, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportFieldDefinition, ReportError]:
        """Update an existing field definition."""
        ...

    async def delete(
        self, 
        field_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[bool, ReportError]:
        """Delete a field definition by ID."""
        ...

    async def bulk_create(
        self, 
        fields: List[ReportFieldDefinition],
        session: Optional[AsyncSession] = None
    ) -> Result[List[ReportFieldDefinition], ReportError]:
        """Create multiple field definitions."""
        ...


@runtime_checkable
class ReportTriggerRepositoryProtocol(Protocol):
    """Protocol for report trigger repositories."""

    async def get_by_id(
        self, 
        trigger_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[Optional[ReportTrigger], ReportError]:
        """Get a report trigger by ID."""
        ...

    async def list_by_template(
        self, 
        template_id: str,
        session: Optional[AsyncSession] = None
    ) -> Result[List[ReportTrigger], ReportError]:
        """List triggers for a template."""
        ...

    async def list_by_event_type(
        self, 
        event_type: str,
        session: Optional[AsyncSession] = None
    ) -> Result[List[ReportTrigger], ReportError]:
        """List triggers for an event type."""
        ...

    async def list_active_scheduled_triggers(
        self,
        session: Optional[AsyncSession] = None
    ) -> Result[List[ReportTrigger], ReportError]:
        """List all active scheduled triggers."""
        ...

    async def create(
        self, 
        trigger: ReportTrigger, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportTrigger, ReportError]:
        """Create a new trigger."""
        ...

    async def update(
        self, 
        trigger: ReportTrigger, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportTrigger, ReportError]:
        """Update an existing trigger."""
        ...

    async def delete(
        self, 
        trigger_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[bool, ReportError]:
        """Delete a trigger by ID."""
        ...

    async def update_last_triggered(
        self,
        trigger_id: str,
        timestamp: datetime,
        session: Optional[AsyncSession] = None
    ) -> Result[bool, ReportError]:
        """Update the last_triggered timestamp for a trigger."""
        ...


@runtime_checkable
class ReportOutputRepositoryProtocol(Protocol):
    """Protocol for report output repositories."""

    async def get_by_id(
        self, 
        output_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[Optional[ReportOutput], ReportError]:
        """Get a report output by ID."""
        ...

    async def list_by_template(
        self, 
        template_id: str,
        session: Optional[AsyncSession] = None
    ) -> Result[List[ReportOutput], ReportError]:
        """List outputs for a template."""
        ...

    async def create(
        self, 
        output: ReportOutput, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportOutput, ReportError]:
        """Create a new output."""
        ...

    async def update(
        self, 
        output: ReportOutput, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportOutput, ReportError]:
        """Update an existing output."""
        ...

    async def delete(
        self, 
        output_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[bool, ReportError]:
        """Delete an output by ID."""
        ...


@runtime_checkable
class ReportExecutionRepositoryProtocol(Protocol):
    """Protocol for report execution repositories."""

    async def get_by_id(
        self, 
        execution_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[Optional[ReportExecution], ReportError]:
        """Get a report execution by ID."""
        ...

    async def list_by_template(
        self, 
        template_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        session: Optional[AsyncSession] = None
    ) -> Result[List[ReportExecution], ReportError]:
        """List executions for a template."""
        ...

    async def create(
        self, 
        execution: ReportExecution, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportExecution, ReportError]:
        """Create a new execution."""
        ...

    async def update(
        self, 
        execution: ReportExecution, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportExecution, ReportError]:
        """Update an existing execution."""
        ...

    async def update_status(
        self,
        execution_id: str,
        status: str,
        error_details: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> Result[bool, ReportError]:
        """Update the status of an execution."""
        ...

    async def complete_execution(
        self,
        execution_id: str,
        row_count: int,
        execution_time_ms: int,
        result_hash: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> Result[bool, ReportError]:
        """Mark an execution as completed with result information."""
        ...


@runtime_checkable
class ReportOutputExecutionRepositoryProtocol(Protocol):
    """Protocol for report output execution repositories."""

    async def get_by_id(
        self, 
        output_execution_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[Optional[ReportOutputExecution], ReportError]:
        """Get a report output execution by ID."""
        ...

    async def list_by_execution(
        self, 
        execution_id: str,
        session: Optional[AsyncSession] = None
    ) -> Result[List[ReportOutputExecution], ReportError]:
        """List output executions for a report execution."""
        ...

    async def create(
        self, 
        output_execution: ReportOutputExecution, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportOutputExecution, ReportError]:
        """Create a new output execution."""
        ...

    async def update(
        self, 
        output_execution: ReportOutputExecution, 
        session: Optional[AsyncSession] = None
    ) -> Result[ReportOutputExecution, ReportError]:
        """Update an existing output execution."""
        ...

    async def complete_output_execution(
        self,
        output_execution_id: str,
        output_location: str,
        output_size_bytes: int,
        session: Optional[AsyncSession] = None
    ) -> Result[bool, ReportError]:
        """Mark an output execution as completed with result information."""
        ...


# Service protocols

@runtime_checkable
class ReportTemplateServiceProtocol(Protocol):
    """Protocol for report template services."""

    async def create_template(
        self, 
        template_data: Dict[str, Any]
    ) -> Result[ReportTemplate, ReportError]:
        """Create a new report template."""
        ...

    async def update_template(
        self, 
        template_id: str, 
        template_data: Dict[str, Any]
    ) -> Result[ReportTemplate, ReportError]:
        """Update an existing report template."""
        ...

    async def delete_template(
        self, 
        template_id: str
    ) -> Result[bool, ReportError]:
        """Delete a report template."""
        ...

    async def get_template(
        self, 
        template_id: str
    ) -> Result[Optional[ReportTemplate], ReportError]:
        """Get a report template by ID."""
        ...

    async def list_templates(
        self, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Result[List[ReportTemplate], ReportError]:
        """List report templates, optionally filtered."""
        ...

    async def clone_template(
        self, 
        template_id: str, 
        new_name: str
    ) -> Result[ReportTemplate, ReportError]:
        """Clone an existing template with a new name."""
        ...


@runtime_checkable
class ReportFieldServiceProtocol(Protocol):
    """Protocol for report field services."""

    async def add_field(
        self, 
        template_id: str, 
        field_data: Dict[str, Any]
    ) -> Result[ReportFieldDefinition, ReportError]:
        """Add a field to a report template."""
        ...

    async def update_field(
        self, 
        field_id: str, 
        field_data: Dict[str, Any]
    ) -> Result[ReportFieldDefinition, ReportError]:
        """Update a field definition."""
        ...

    async def delete_field(
        self, 
        field_id: str
    ) -> Result[bool, ReportError]:
        """Delete a field from a report template."""
        ...

    async def get_available_fields(
        self, 
        base_object_type: str
    ) -> Result[List[Dict[str, Any]], ReportError]:
        """Get available fields for a specific object type."""
        ...

    async def validate_field_config(
        self, 
        field_type: str, 
        field_config: Dict[str, Any]
    ) -> Result[bool, ReportError]:
        """Validate a field configuration."""
        ...

    async def get_field_by_id(
        self,
        field_id: str
    ) -> Result[Optional[ReportFieldDefinition], ReportError]:
        """Get a field by ID."""
        ...

    async def list_fields_by_template(
        self,
        template_id: str
    ) -> Result[List[ReportFieldDefinition], ReportError]:
        """List all fields for a template."""
        ...


@runtime_checkable
class ReportExecutionServiceProtocol(Protocol):
    """Protocol for report execution services."""

    async def execute_report(
        self, 
        template_id: str, 
        parameters: Optional[Dict[str, Any]] = None,
        trigger_type: str = "manual",
        user_id: Optional[str] = None
    ) -> Result[ReportExecution, ReportError]:
        """Execute a report with optional parameters."""
        ...

    async def get_execution_status(
        self, 
        execution_id: str
    ) -> Result[Dict[str, Any], ReportError]:
        """Get the status of a report execution."""
        ...

    async def cancel_execution(
        self, 
        execution_id: str
    ) -> Result[bool, ReportError]:
        """Cancel a running report execution."""
        ...

    async def get_execution_result(
        self, 
        execution_id: str,
        format: Optional[str] = None
    ) -> Result[Any, ReportError]:
        """Get the result of a completed report execution."""
        ...

    async def list_executions(
        self, 
        template_id: Optional[str] = None, 
        status: Optional[str] = None,
        date_range: Optional[tuple[datetime, datetime]] = None,
        limit: int = 100
    ) -> Result[List[ReportExecution], ReportError]:
        """List report executions, optionally filtered."""
        ...


@runtime_checkable
class ReportTriggerServiceProtocol(Protocol):
    """Protocol for report trigger services."""

    async def create_trigger(
        self, 
        template_id: str, 
        trigger_data: Dict[str, Any]
    ) -> Result[ReportTrigger, ReportError]:
        """Create a new trigger for a report template."""
        ...

    async def update_trigger(
        self, 
        trigger_id: str, 
        trigger_data: Dict[str, Any]
    ) -> Result[ReportTrigger, ReportError]:
        """Update an existing trigger."""
        ...

    async def delete_trigger(
        self, 
        trigger_id: str
    ) -> Result[bool, ReportError]:
        """Delete a trigger."""
        ...

    async def enable_trigger(
        self, 
        trigger_id: str
    ) -> Result[bool, ReportError]:
        """Enable a trigger."""
        ...

    async def disable_trigger(
        self, 
        trigger_id: str
    ) -> Result[bool, ReportError]:
        """Disable a trigger."""
        ...

    async def handle_event(
        self, 
        event_type: str, 
        event_data: Dict[str, Any]
    ) -> Result[List[str], ReportError]:
        """Handle an event that might trigger reports (returns execution IDs)."""
        ...

    async def check_query_triggers(
        self
    ) -> Result[List[str], ReportError]:
        """Check query-based triggers and execute reports if conditions are met."""
        ...

    async def process_scheduled_triggers(
        self
    ) -> Result[List[str], ReportError]:
        """Process scheduled triggers and execute reports if due."""
        ...


@runtime_checkable
class ReportOutputServiceProtocol(Protocol):
    """Protocol for report output services."""

    async def create_output_config(
        self, 
        template_id: str, 
        output_data: Dict[str, Any]
    ) -> Result[ReportOutput, ReportError]:
        """Create a new output configuration for a report template."""
        ...

    async def update_output_config(
        self, 
        output_id: str, 
        output_data: Dict[str, Any]
    ) -> Result[ReportOutput, ReportError]:
        """Update an existing output configuration."""
        ...

    async def delete_output_config(
        self, 
        output_id: str
    ) -> Result[bool, ReportError]:
        """Delete an output configuration."""
        ...

    async def format_report(
        self, 
        execution_id: str, 
        format: str
    ) -> Result[bytes, ReportError]:
        """Format a report result in the specified format."""
        ...

    async def deliver_report(
        self, 
        execution_id: str, 
        output_id: str
    ) -> Result[bool, ReportError]:
        """Deliver a report according to an output configuration."""
        ...