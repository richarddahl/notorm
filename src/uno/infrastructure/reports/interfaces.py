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
from uno.reports.errors import (
    ReportTemplateNotFoundError,
    ReportFieldNotFoundError,
    ReportExecutionNotFoundError,
    ReportTriggerNotFoundError,
    ReportExecutionFailedError,
    ReportOutputFormatInvalidError,
)

T = TypeVar("T")


# Repository protocols


@runtime_checkable
class ReportTemplateRepositoryProtocol(Protocol):
    """Protocol for report template repositories."""

    async def get_by_id(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[Optional[ReportTemplate]]:
        """Get a report template by ID."""
        ...

    async def get_by_name(
        self, name: str, session: AsyncSession | None = None
    ) -> Result[Optional[ReportTemplate]]:
        """Get a report template by name."""
        ...

    async def list_templates(
        self,
        filters: dict[str, Any] | None = None,
        session: AsyncSession | None = None,
    ) -> Result[list[ReportTemplate]]:
        """List report templates, optionally filtered."""
        ...

    async def create(
        self, template: ReportTemplate, session: AsyncSession | None = None
    ) -> Result[ReportTemplate]:
        """Create a new report template."""
        ...

    async def update(
        self, template: ReportTemplate, session: AsyncSession | None = None
    ) -> Result[ReportTemplate]:
        """Update an existing report template."""
        ...

    async def delete(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[bool]:
        """Delete a report template by ID."""
        ...


@runtime_checkable
class ReportFieldDefinitionRepositoryProtocol(Protocol):
    """Protocol for report field definition repositories."""

    async def get_by_id(
        self, field_id: str, session: AsyncSession | None = None
    ) -> Result[Optional[ReportFieldDefinition]]:
        """Get a report field definition by ID."""
        ...

    async def list_by_template(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[list[ReportFieldDefinition]]:
        """List field definitions for a template."""
        ...

    async def create(
        self, field: ReportFieldDefinition, session: AsyncSession | None = None
    ) -> Result[ReportFieldDefinition]:
        """Create a new field definition."""
        ...

    async def update(
        self, field: ReportFieldDefinition, session: AsyncSession | None = None
    ) -> Result[ReportFieldDefinition]:
        """Update an existing field definition."""
        ...

    async def delete(
        self, field_id: str, session: AsyncSession | None = None
    ) -> Result[bool]:
        """Delete a field definition by ID."""
        ...

    async def bulk_create(
        self,
        fields: list[ReportFieldDefinition],
        session: AsyncSession | None = None,
    ) -> Result[list[ReportFieldDefinition]]:
        """Create multiple field definitions."""
        ...


@runtime_checkable
class ReportTriggerRepositoryProtocol(Protocol):
    """Protocol for report trigger repositories."""

    async def get_by_id(
        self, trigger_id: str, session: AsyncSession | None = None
    ) -> Result[Optional[ReportTrigger]]:
        """Get a report trigger by ID."""
        ...

    async def list_by_template(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[list[ReportTrigger]]:
        """List triggers for a template."""
        ...

    async def list_by_event_type(
        self, event_type: str, session: AsyncSession | None = None
    ) -> Result[list[ReportTrigger]]:
        """List triggers for an event type."""
        ...

    async def list_active_scheduled_triggers(
        self, session: AsyncSession | None = None
    ) -> Result[list[ReportTrigger]]:
        """List all active scheduled triggers."""
        ...

    async def create(
        self, trigger: ReportTrigger, session: AsyncSession | None = None
    ) -> Result[ReportTrigger]:
        """Create a new trigger."""
        ...

    async def update(
        self, trigger: ReportTrigger, session: AsyncSession | None = None
    ) -> Result[ReportTrigger]:
        """Update an existing trigger."""
        ...

    async def delete(
        self, trigger_id: str, session: AsyncSession | None = None
    ) -> Result[bool]:
        """Delete a trigger by ID."""
        ...

    async def update_last_triggered(
        self,
        trigger_id: str,
        timestamp: datetime,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """Update the last_triggered timestamp for a trigger."""
        ...


@runtime_checkable
class ReportOutputRepositoryProtocol(Protocol):
    """Protocol for report output repositories."""

    async def get_by_id(
        self, output_id: str, session: AsyncSession | None = None
    ) -> Result[Optional[ReportOutput]]:
        """Get a report output by ID."""
        ...

    async def list_by_template(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[list[ReportOutput]]:
        """List outputs for a template."""
        ...

    async def create(
        self, output: ReportOutput, session: AsyncSession | None = None
    ) -> Result[ReportOutput]:
        """Create a new output."""
        ...

    async def update(
        self, output: ReportOutput, session: AsyncSession | None = None
    ) -> Result[ReportOutput]:
        """Update an existing output."""
        ...

    async def delete(
        self, output_id: str, session: AsyncSession | None = None
    ) -> Result[bool]:
        """Delete an output by ID."""
        ...


@runtime_checkable
class ReportExecutionRepositoryProtocol(Protocol):
    """Protocol for report execution repositories."""

    async def get_by_id(
        self, execution_id: str, session: AsyncSession | None = None
    ) -> Result[Optional[ReportExecution]]:
        """Get a report execution by ID."""
        ...

    async def list_by_template(
        self,
        template_id: str,
        status: str | None = None,
        limit: int = 100,
        session: AsyncSession | None = None,
    ) -> Result[list[ReportExecution]]:
        """List executions for a template."""
        ...

    async def create(
        self, execution: ReportExecution, session: AsyncSession | None = None
    ) -> Result[ReportExecution]:
        """Create a new execution."""
        ...

    async def update(
        self, execution: ReportExecution, session: AsyncSession | None = None
    ) -> Result[ReportExecution]:
        """Update an existing execution."""
        ...

    async def update_status(
        self,
        execution_id: str,
        status: str,
        error_details: str | None = None,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """Update the status of an execution."""
        ...

    async def complete_execution(
        self,
        execution_id: str,
        row_count: int,
        execution_time_ms: int,
        result_hash: str | None = None,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """Mark an execution as completed with result information."""
        ...


@runtime_checkable
class ReportOutputExecutionRepositoryProtocol(Protocol):
    """Protocol for report output execution repositories."""

    async def get_by_id(
        self, output_execution_id: str, session: AsyncSession | None = None
    ) -> Result[Optional[ReportOutputExecution]]:
        """Get a report output execution by ID."""
        ...

    async def list_by_execution(
        self, execution_id: str, session: AsyncSession | None = None
    ) -> Result[list[ReportOutputExecution]]:
        """List output executions for a report execution."""
        ...

    async def create(
        self,
        output_execution: ReportOutputExecution,
        session: AsyncSession | None = None,
    ) -> Result[ReportOutputExecution]:
        """Create a new output execution."""
        ...

    async def update(
        self,
        output_execution: ReportOutputExecution,
        session: AsyncSession | None = None,
    ) -> Result[ReportOutputExecution]:
        """Update an existing output execution."""
        ...

    async def complete_output_execution(
        self,
        output_execution_id: str,
        output_location: str,
        output_size_bytes: int,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """Mark an output execution as completed with result information."""
        ...


# Service protocols


@runtime_checkable
class ReportTemplateServiceProtocol(Protocol):
    """Protocol for report template services."""

    async def create_template(
        self, template_data: dict[str, Any]
    ) -> Result[ReportTemplate]:
        """Create a new report template."""
        ...

    async def update_template(
        self, template_id: str, template_data: dict[str, Any]
    ) -> Result[ReportTemplate]:
        """Update an existing report template."""
        ...

    async def delete_template(self, template_id: str) -> Result[bool]:
        """Delete a report template."""
        ...

    async def get_template(self, template_id: str) -> Result[Optional[ReportTemplate]]:
        """Get a report template by ID."""
        ...

    async def list_templates(
        self, filters: dict[str, Any] | None = None
    ) -> Result[list[ReportTemplate]]:
        """List report templates, optionally filtered."""
        ...

    async def clone_template(
        self, template_id: str, new_name: str
    ) -> Result[ReportTemplate]:
        """Clone an existing template with a new name."""
        ...


@runtime_checkable
class ReportFieldServiceProtocol(Protocol):
    """Protocol for report field services."""

    async def add_field(
        self, template_id: str, field_data: dict[str, Any]
    ) -> Result[ReportFieldDefinition]:
        """Add a field to a report template."""
        ...

    async def update_field(
        self, field_id: str, field_data: dict[str, Any]
    ) -> Result[ReportFieldDefinition]:
        """Update a field definition."""
        ...

    async def delete_field(self, field_id: str) -> Result[bool]:
        """Delete a field from a report template."""
        ...

    async def get_available_fields(
        self, base_object_type: str
    ) -> Result[list[dict[str, Any]]]:
        """Get available fields for a specific object type."""
        ...

    async def validate_field_config(
        self, field_type: str, field_config: dict[str, Any]
    ) -> Result[bool]:
        """Validate a field configuration."""
        ...

    async def get_field_by_id(
        self, field_id: str
    ) -> Result[Optional[ReportFieldDefinition]]:
        """Get a field by ID."""
        ...

    async def list_fields_by_template(
        self, template_id: str
    ) -> Result[list[ReportFieldDefinition]]:
        """List all fields for a template."""
        ...


@runtime_checkable
class ReportExecutionServiceProtocol(Protocol):
    """Protocol for report execution services."""

    async def execute_report(
        self,
        template_id: str,
        parameters: dict[str, Any] | None = None,
        trigger_type: str = "manual",
        user_id: str | None = None,
    ) -> Result[ReportExecution]:
        """Execute a report with optional parameters."""
        ...

    async def get_execution_status(self, execution_id: str) -> Result[dict[str, Any]]:
        """Get the status of a report execution."""
        ...

    async def cancel_execution(self, execution_id: str) -> Result[bool]:
        """Cancel a running report execution."""
        ...

    async def get_execution_result(
        self, execution_id: str, format: str | None = None
    ) -> Result[Any]:
        """Get the result of a completed report execution."""
        ...

    async def list_executions(
        self,
        template_id: str | None = None,
        status: str | None = None,
        date_range: Optional[tuple[datetime, datetime]] = None,
        limit: int = 100,
    ) -> Result[list[ReportExecution]]:
        """List report executions, optionally filtered."""
        ...


@runtime_checkable
class ReportTriggerServiceProtocol(Protocol):
    """Protocol for report trigger services."""

    async def create_trigger(
        self, template_id: str, trigger_data: dict[str, Any]
    ) -> Result[ReportTrigger]:
        """Create a new trigger for a report template."""
        ...

    async def update_trigger(
        self, trigger_id: str, trigger_data: dict[str, Any]
    ) -> Result[ReportTrigger]:
        """Update an existing trigger."""
        ...

    async def delete_trigger(self, trigger_id: str) -> Result[bool]:
        """Delete a trigger."""
        ...

    async def enable_trigger(self, trigger_id: str) -> Result[bool]:
        """Enable a trigger."""
        ...

    async def disable_trigger(self, trigger_id: str) -> Result[bool]:
        """Disable a trigger."""
        ...

    async def handle_event(
        self, event_type: str, event_data: dict[str, Any]
    ) -> Result[list[str]]:
        """Handle an event that might trigger reports (returns execution IDs)."""
        ...

    async def check_query_triggers(self) -> Result[list[str]]:
        """Check query-based triggers and execute reports if conditions are met."""
        ...

    async def process_scheduled_triggers(self) -> Result[list[str]]:
        """Process scheduled triggers and execute reports if due."""
        ...


@runtime_checkable
class ReportOutputServiceProtocol(Protocol):
    """Protocol for report output services."""

    async def create_output_config(
        self, template_id: str, output_data: dict[str, Any]
    ) -> Result[ReportOutput]:
        """Create a new output configuration for a report template."""
        ...

    async def update_output_config(
        self, output_id: str, output_data: dict[str, Any]
    ) -> Result[ReportOutput]:
        """Update an existing output configuration."""
        ...

    async def delete_output_config(self, output_id: str) -> Result[bool]:
        """Delete an output configuration."""
        ...

    async def format_report(self, execution_id: str, format: str) -> Result[bytes]:
        """Format a report result in the specified format."""
        ...

    async def deliver_report(self, execution_id: str, output_id: str) -> Result[bool]:
        """Deliver a report according to an output configuration."""
        ...
