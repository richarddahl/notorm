# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Repository implementations for the reports module.

This module provides concrete implementations of the repository interfaces
defined in the interfaces module, using the UnoBaseRepository as a foundation.
"""

from datetime import datetime, UTC
import logging
from enum import Enum

from sqlalchemy import select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from uno.core.errors.result import Result, Success, Failure
from uno.core.base.error import ErrorCode
from uno.reports.errors import (
    ReportError,
    ReportErrorCode,
    ReportTemplateNotFoundError,
    ReportFieldNotFoundError,
    ReportExecutionNotFoundError,
    ReportTriggerNotFoundError,
    ReportExecutionFailedError,
    ReportOutputDeliveryFailedError,
    ReportTemplateInvalidError,
)

from uno.database.repository import UnoBaseRepository
from uno.reports.models import (
    ReportTemplateModel,
    ReportFieldDefinitionModel,
    ReportTriggerModel,
    ReportOutputModel,
    ReportExecutionModel,
    ReportOutputExecutionModel,
)
from uno.reports.interfaces import (
    ReportTemplateRepositoryProtocol,
    ReportFieldDefinitionRepositoryProtocol,
    ReportTriggerRepositoryProtocol,
    ReportOutputRepositoryProtocol,
    ReportExecutionRepositoryProtocol,
    ReportOutputExecutionRepositoryProtocol,
)


# ReportError is now imported from uno.reports.errors


class ReportTemplateRepository(
    UnoBaseRepository[ReportTemplateModel], ReportTemplateRepositoryProtocol
):
    """Repository implementation for ReportTemplate."""

    def __init__(self, session: AsyncSession, logger: logging.Logger | None = None):
        """Initialize the repository with a session and optional logger."""
        super().__init__(session, ReportTemplateModel, logger)

    async def get_by_id(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[ReportTemplate | None]:
        """Get a report template by ID."""
        try:
            session = session or self.session
            stmt = (
                select(ReportTemplateModel)
                .options(
                    joinedload(ReportTemplateModel.fields),
                    joinedload(ReportTemplateModel.triggers),
                    joinedload(ReportTemplateModel.outputs),
                )
                .where(ReportTemplateModel.id == template_id)
            )
            result = await session.execute(stmt)
            model = result.scalars().first()

            if model is None:
                return Success(None)

            return Success(ReportTemplate.from_orm(model))
        except Exception as e:
            return Failure(Exception(f"Failed to get report template: {str(e)}"))

    async def get_by_name(
        self, name: str, session: AsyncSession | None = None
    ) -> Result[ReportTemplate | None]:
        """Get a report template by name."""
        try:
            session = session or self.session
            stmt = (
                select(ReportTemplateModel)
                .options(
                    joinedload(ReportTemplateModel.fields),
                    joinedload(ReportTemplateModel.triggers),
                    joinedload(ReportTemplateModel.outputs),
                )
                .where(ReportTemplateModel.name == name)
            )
            result = await session.execute(stmt)
            model = result.scalars().first()

            if model is None:
                return Success(None)

            return Success(ReportTemplate.from_orm(model))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to get report template by name: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    name=name,
                )
            )

    async def list_templates(
        self,
        filters: dict[str, Any] | None = None,
        session: AsyncSession | None = None,
    ) -> Result[list[ReportTemplate]]:
        """List report templates, optionally filtered."""
        try:
            session = session or self.session
            stmt = select(ReportTemplateModel)

            # Apply filters if provided
            if filters:
                filter_conditions = []
                for field, value in filters.items():
                    if hasattr(ReportTemplateModel, field):
                        filter_conditions.append(
                            getattr(ReportTemplateModel, field) == value
                        )

                if filter_conditions:
                    stmt = stmt.where(and_(*filter_conditions))

            # Execute query
            result = await session.execute(stmt)
            models = result.scalars().all()
            templates = [ReportTemplate.from_orm(model) for model in models]

            return Success(templates)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to list report templates: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    filters=filters,
                )
            )

    async def create(
        self, template: ReportTemplate, session: AsyncSession | None = None
    ) -> Result[ReportTemplate]:
        """Create a new report template."""
        try:
            session = session or self.session
            model_data = template.model_dump(
                exclude={"id"} if template.id is None else set()
            )

            # Extract related items
            fields_data = model_data.pop("fields", [])
            triggers_data = model_data.pop("triggers", [])
            outputs_data = model_data.pop("outputs", [])

            # Create the template
            model = ReportTemplateModel(**model_data)
            session.add(model)
            await session.flush()

            # Set the ID in the original object
            template.id = model.id

            # Return the template with the new ID
            return Success(template)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to create report template: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    template_data=template.model_dump(),
                )
            )

    async def update(
        self, template: ReportTemplate, session: AsyncSession | None = None
    ) -> Result[ReportTemplate]:
        """Update an existing report template."""
        try:
            session = session or self.session

            # Check if template exists
            template_id = template.id
            if template_id is None:
                return Failure(
                    ReportError(
                        "Cannot update template without ID", ErrorCode.VALIDATION_ERROR
                    )
                )

            existing_template = await session.get(ReportTemplateModel, template_id)
            if existing_template is None:
                return Failure(
                    ReportError(
                        f"Template with ID {template_id} not found",
                        ErrorCode.NOT_FOUND,
                        template_id=template_id,
                    )
                )

            # Update template fields
            model_data = template.model_dump(
                exclude={"fields", "triggers", "outputs", "executions"}
            )
            for key, value in model_data.items():
                if hasattr(existing_template, key):
                    setattr(existing_template, key, value)

            await session.flush()

            # Return the updated template
            result = await self.get_by_id(template_id, session)
            if result.is_failure:
                return result

            return Success(cast(ReportTemplate, result.value))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to update report template: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    template_id=template.id,
                )
            )

    async def delete(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[bool]:
        """Delete a report template by ID."""
        try:
            session = session or self.session

            # Check if template exists
            existing_template = await session.get(ReportTemplateModel, template_id)
            if existing_template is None:
                return Failure(
                    ReportError(
                        f"Template with ID {template_id} not found",
                        ErrorCode.NOT_FOUND,
                        template_id=template_id,
                    )
                )

            # Delete the template
            await session.delete(existing_template)
            await session.flush()

            return Success(True)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to delete report template: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    template_id=template_id,
                )
            )


class ReportFieldDefinitionRepository(
    UnoBaseRepository[ReportFieldDefinitionModel],
    ReportFieldDefinitionRepositoryProtocol,
):
    """Repository implementation for ReportFieldDefinition."""

    def __init__(self, session: AsyncSession, logger: logging.Logger | None = None):
        """Initialize the repository with a session and optional logger."""
        super().__init__(session, ReportFieldDefinitionModel, logger)

    async def get_by_id(
        self, field_id: str, session: AsyncSession | None = None
    ) -> Result[ReportFieldDefinition | None]:
        """Get a report field definition by ID."""
        try:
            session = session or self.session
            stmt = (
                select(ReportFieldDefinitionModel)
                .options(
                    joinedload(ReportFieldDefinitionModel.parent_field),
                    joinedload(ReportFieldDefinitionModel.child_fields),
                )
                .where(ReportFieldDefinitionModel.id == field_id)
            )
            result = await session.execute(stmt)
            model = result.scalars().first()

            if model is None:
                return Success(None)

            return Success(ReportFieldDefinition.from_orm(model))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to get field definition: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    field_id=field_id,
                )
            )

    async def list_by_template(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[list[ReportFieldDefinition]]:
        """List field definitions for a template."""
        try:
            session = session or self.session

            # Get template with fields
            stmt = (
                select(ReportTemplateModel)
                .options(joinedload(ReportTemplateModel.fields))
                .where(ReportTemplateModel.id == template_id)
            )
            result = await session.execute(stmt)
            template = result.scalars().first()

            if template is None:
                return Failure(
                    ReportError(
                        f"Template with ID {template_id} not found",
                        ErrorCode.NOT_FOUND,
                        template_id=template_id,
                    )
                )

            fields = [
                ReportFieldDefinition.from_orm(field) for field in template.fields
            ]
            return Success(fields)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to list fields for template: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    template_id=template_id,
                )
            )

    async def create(
        self, field: ReportFieldDefinition, session: AsyncSession | None = None
    ) -> Result[ReportFieldDefinition]:
        """Create a new field definition."""
        try:
            session = session or self.session
            model_data = field.model_dump(
                exclude={"id"} if field.id is None else set()
            )

            # Remove relationship fields from data
            model_data.pop("parent_field", None)
            model_data.pop("child_fields", None)
            model_data.pop("templates", None)

            # Create the field
            model = ReportFieldDefinitionModel(**model_data)
            session.add(model)
            await session.flush()

            # Set the ID in the original object
            field.id = model.id

            # Return the field with the new ID
            return Success(field)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to create field definition: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    field_data=field.model_dump(),
                )
            )

    async def update(
        self, field: ReportFieldDefinition, session: AsyncSession | None = None
    ) -> Result[ReportFieldDefinition]:
        """Update an existing field definition."""
        try:
            session = session or self.session

            # Check if field exists
            field_id = field.id
            if field_id is None:
                return Failure(
                    ReportError(
                        "Cannot update field without ID", ErrorCode.VALIDATION_ERROR
                    )
                )

            existing_field = await session.get(ReportFieldDefinitionModel, field_id)
            if existing_field is None:
                return Failure(
                    ReportError(
                        f"Field with ID {field_id} not found",
                        ErrorCode.NOT_FOUND,
                        field_id=field_id,
                    )
                )

            # Update field fields
            model_data = field.model_dump(
                exclude={"parent_field", "child_fields", "templates"}
            )
            for key, value in model_data.items():
                if hasattr(existing_field, key):
                    setattr(existing_field, key, value)

            await session.flush()

            # Return the updated field
            result = await self.get_by_id(field_id, session)
            if result.is_failure:
                return result

            return Success(cast(ReportFieldDefinition, result.value))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to update field definition: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    field_id=field.id,
                )
            )

    async def delete(
        self, field_id: str, session: AsyncSession | None = None
    ) -> Result[bool]:
        """Delete a field definition by ID."""
        try:
            session = session or self.session

            # Check if field exists
            existing_field = await session.get(ReportFieldDefinitionModel, field_id)
            if existing_field is None:
                return Failure(
                    ReportError(
                        f"Field with ID {field_id} not found",
                        ErrorCode.NOT_FOUND,
                        field_id=field_id,
                    )
                )

            # Delete the field
            await session.delete(existing_field)
            await session.flush()

            return Success(True)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to delete field definition: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    field_id=field_id,
                )
            )

    async def bulk_create(
        self,
        fields: list[ReportFieldDefinition],
        session: AsyncSession | None = None,
    ) -> Result[list[ReportFieldDefinition]]:
        """Create multiple field definitions."""
        try:
            session = session or self.session
            created_fields = []

            for field in fields:
                result = await self.create(field, session)
                if result.is_failure:
                    # Roll back all creations if any fails
                    return result
                created_fields.append(result.value)

            return Success(created_fields)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to bulk create field definitions: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    field_count=len(fields),
                )
            )


class ReportTriggerRepository(
    UnoBaseRepository[ReportTriggerModel], ReportTriggerRepositoryProtocol
):
    """Repository implementation for ReportTrigger."""

    def __init__(self, session: AsyncSession, logger: logging.Logger | None = None):
        """Initialize the repository with a session and optional logger."""
        super().__init__(session, ReportTriggerModel, logger)

    async def get_by_id(
        self, trigger_id: str, session: AsyncSession | None = None
    ) -> Result[ReportTrigger | None]:
        """Get a report trigger by ID."""
        try:
            session = session or self.session
            stmt = (
                select(ReportTriggerModel)
                .options(joinedload(ReportTriggerModel.report_template))
                .where(ReportTriggerModel.id == trigger_id)
            )
            result = await session.execute(stmt)
            model = result.scalars().first()

            if model is None:
                return Success(None)

            return Success(ReportTrigger.from_orm(model))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to get trigger: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    trigger_id=trigger_id,
                )
            )

    async def list_by_template(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[list[ReportTrigger]]:
        """List triggers for a template."""
        try:
            session = session or self.session
            stmt = select(ReportTriggerModel).where(
                ReportTriggerModel.report_template_id == template_id
            )
            result = await session.execute(stmt)
            models = result.scalars().all()

            triggers = [ReportTrigger.from_orm(model) for model in models]
            return Success(triggers)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to list triggers for template: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    template_id=template_id,
                )
            )

    async def list_by_event_type(
        self, event_type: str, session: AsyncSession | None = None
    ) -> Result[list[ReportTrigger]]:
        """List triggers for an event type."""
        try:
            session = session or self.session
            stmt = (
                select(ReportTriggerModel)
                .options(joinedload(ReportTriggerModel.report_template))
                .where(
                    and_(
                        ReportTriggerModel.event_type == event_type,
                        ReportTriggerModel.is_active == True,
                    )
                )
            )
            result = await session.execute(stmt)
            models = result.scalars().all()

            triggers = [ReportTrigger.from_orm(model) for model in models]
            return Success(triggers)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to list triggers for event type: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    event_type=event_type,
                )
            )

    async def list_active_scheduled_triggers(
        self, session: AsyncSession | None = None
    ) -> Result[list[ReportTrigger]]:
        """List all active scheduled triggers."""
        try:
            session = session or self.session
            stmt = (
                select(ReportTriggerModel)
                .options(joinedload(ReportTriggerModel.report_template))
                .where(
                    and_(
                        ReportTriggerModel.trigger_type == "scheduled",
                        ReportTriggerModel.is_active == True,
                    )
                )
            )
            result = await session.execute(stmt)
            models = result.scalars().all()

            triggers = [ReportTrigger.from_orm(model) for model in models]
            return Success(triggers)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to list active scheduled triggers: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                )
            )

    async def create(
        self, trigger: ReportTrigger, session: AsyncSession | None = None
    ) -> Result[ReportTrigger]:
        """Create a new trigger."""
        try:
            session = session or self.session
            model_data = trigger.model_dump(
                exclude={"id"} if trigger.id is None else set()
            )

            # Remove relationship fields from data
            model_data.pop("report_template", None)

            # Create the trigger
            model = ReportTriggerModel(**model_data)
            session.add(model)
            await session.flush()

            # Set the ID in the original object
            trigger.id = model.id

            # Return the trigger with the new ID
            return Success(trigger)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to create trigger: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    trigger_data=trigger.model_dump(),
                )
            )

    async def update(
        self, trigger: ReportTrigger, session: AsyncSession | None = None
    ) -> Result[ReportTrigger]:
        """Update an existing trigger."""
        try:
            session = session or self.session

            # Check if trigger exists
            trigger_id = trigger.id
            if trigger_id is None:
                return Failure(
                    ReportError(
                        "Cannot update trigger without ID", ErrorCode.VALIDATION_ERROR
                    )
                )

            existing_trigger = await session.get(ReportTriggerModel, trigger_id)
            if existing_trigger is None:
                return Failure(
                    ReportError(
                        f"Trigger with ID {trigger_id} not found",
                        ErrorCode.NOT_FOUND,
                        trigger_id=trigger_id,
                    )
                )

            # Update trigger fields
            model_data = trigger.model_dump(exclude={"report_template"})
            for key, value in model_data.items():
                if hasattr(existing_trigger, key):
                    setattr(existing_trigger, key, value)

            await session.flush()

            # Return the updated trigger
            result = await self.get_by_id(trigger_id, session)
            if result.is_failure:
                return result

            return Success(cast(ReportTrigger, result.value))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to update trigger: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    trigger_id=trigger.id,
                )
            )

    async def delete(
        self, trigger_id: str, session: AsyncSession | None = None
    ) -> Result[bool]:
        """Delete a trigger by ID."""
        try:
            session = session or self.session

            # Check if trigger exists
            existing_trigger = await session.get(ReportTriggerModel, trigger_id)
            if existing_trigger is None:
                return Failure(
                    ReportError(
                        f"Trigger with ID {trigger_id} not found",
                        ErrorCode.NOT_FOUND,
                        trigger_id=trigger_id,
                    )
                )

            # Delete the trigger
            await session.delete(existing_trigger)
            await session.flush()

            return Success(True)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to delete trigger: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    trigger_id=trigger_id,
                )
            )

    async def update_last_triggered(
        self,
        trigger_id: str,
        timestamp: datetime,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """Update the last_triggered timestamp for a trigger."""
        try:
            session = session or self.session

            # Check if trigger exists
            existing_trigger = await session.get(ReportTriggerModel, trigger_id)
            if existing_trigger is None:
                return Failure(
                    ReportError(
                        f"Trigger with ID {trigger_id} not found",
                        ErrorCode.NOT_FOUND,
                        trigger_id=trigger_id,
                    )
                )

            # Update the timestamp
            existing_trigger.last_triggered = timestamp
            await session.flush()

            return Success(True)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to update last_triggered timestamp: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    trigger_id=trigger_id,
                )
            )


class ReportOutputRepository(
    UnoBaseRepository[ReportOutputModel], ReportOutputRepositoryProtocol
):
    """Repository implementation for ReportOutput."""

    def __init__(self, session: AsyncSession, logger: logging.Logger | None = None):
        """Initialize the repository with a session and optional logger."""
        super().__init__(session, ReportOutputModel, logger)

    async def get_by_id(
        self, output_id: str, session: AsyncSession | None = None
    ) -> Result[ReportOutput | None]:
        """Get a report output by ID."""
        try:
            session = session or self.session
            stmt = (
                select(ReportOutputModel)
                .options(joinedload(ReportOutputModel.report_template))
                .where(ReportOutputModel.id == output_id)
            )
            result = await session.execute(stmt)
            model = result.scalars().first()

            if model is None:
                return Success(None)

            return Success(ReportOutput.from_orm(model))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to get output: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    output_id=output_id,
                )
            )

    async def list_by_template(
        self, template_id: str, session: AsyncSession | None = None
    ) -> Result[list[ReportOutput]]:
        """List outputs for a template."""
        try:
            session = session or self.session
            stmt = select(ReportOutputModel).where(
                ReportOutputModel.report_template_id == template_id
            )
            result = await session.execute(stmt)
            models = result.scalars().all()

            outputs = [ReportOutput.from_orm(model) for model in models]
            return Success(outputs)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to list outputs for template: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    template_id=template_id,
                )
            )

    async def create(
        self, output: ReportOutput, session: AsyncSession | None = None
    ) -> Result[ReportOutput]:
        """Create a new output."""
        try:
            session = session or self.session
            model_data = output.model_dump(
                exclude={"id"} if output.id is None else set()
            )

            # Remove relationship fields from data
            model_data.pop("report_template", None)
            model_data.pop("output_executions", None)

            # Create the output
            model = ReportOutputModel(**model_data)
            session.add(model)
            await session.flush()

            # Set the ID in the original object
            output.id = model.id

            # Return the output with the new ID
            return Success(output)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to create output: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    output_data=output.model_dump(),
                )
            )

    async def update(
        self, output: ReportOutput, session: AsyncSession | None = None
    ) -> Result[ReportOutput]:
        """Update an existing output."""
        try:
            session = session or self.session

            # Check if output exists
            output_id = output.id
            if output_id is None:
                return Failure(
                    ReportError(
                        "Cannot update output without ID", ErrorCode.VALIDATION_ERROR
                    )
                )

            existing_output = await session.get(ReportOutputModel, output_id)
            if existing_output is None:
                return Failure(
                    ReportError(
                        f"Output with ID {output_id} not found",
                        ErrorCode.NOT_FOUND,
                        output_id=output_id,
                    )
                )

            # Update output fields
            model_data = output.model_dump(
                exclude={"report_template", "output_executions"}
            )
            for key, value in model_data.items():
                if hasattr(existing_output, key):
                    setattr(existing_output, key, value)

            await session.flush()

            # Return the updated output
            result = await self.get_by_id(output_id, session)
            if result.is_failure:
                return result

            return Success(cast(ReportOutput, result.value))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to update output: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    output_id=output.id,
                )
            )

    async def delete(
        self, output_id: str, session: AsyncSession | None = None
    ) -> Result[bool]:
        """Delete an output by ID."""
        try:
            session = session or self.session

            # Check if output exists
            existing_output = await session.get(ReportOutputModel, output_id)
            if existing_output is None:
                return Failure(
                    ReportError(
                        f"Output with ID {output_id} not found",
                        ErrorCode.NOT_FOUND,
                        output_id=output_id,
                    )
                )

            # Delete the output
            await session.delete(existing_output)
            await session.flush()

            return Success(True)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to delete output: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    output_id=output_id,
                )
            )


class ReportExecutionRepository(
    UnoBaseRepository[ReportExecutionModel], ReportExecutionRepositoryProtocol
):
    """Repository implementation for ReportExecution."""

    def __init__(self, session: AsyncSession, logger: logging.Logger | None = None):
        """Initialize the repository with a session and optional logger."""
        super().__init__(session, ReportExecutionModel, logger)

    async def get_by_id(
        self, execution_id: str, session: AsyncSession | None = None
    ) -> Result[ReportExecution | None]:
        """Get a report execution by ID."""
        try:
            session = session or self.session
            stmt = (
                select(ReportExecutionModel)
                .options(
                    joinedload(ReportExecutionModel.report_template),
                    joinedload(ReportExecutionModel.output_executions),
                )
                .where(ReportExecutionModel.id == execution_id)
            )
            result = await session.execute(stmt)
            model = result.scalars().first()

            if model is None:
                return Success(None)

            return Success(ReportExecution.from_orm(model))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to get execution: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    execution_id=execution_id,
                )
            )

    async def list_by_template(
        self,
        template_id: str,
        status: str | None = None,
        limit: int = 100,
        session: AsyncSession | None = None,
    ) -> Result[list[ReportExecution]]:
        """List executions for a template."""
        try:
            session = session or self.session
            stmt = (
                select(ReportExecutionModel)
                .where(ReportExecutionModel.report_template_id == template_id)
                .order_by(ReportExecutionModel.started_at.desc())
                .limit(limit)
            )

            # Apply status filter if provided
            if status:
                stmt = stmt.where(ReportExecutionModel.status == status)

            result = await session.execute(stmt)
            models = result.scalars().all()

            executions = [ReportExecution.from_orm(model) for model in models]
            return Success(executions)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to list executions for template: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    template_id=template_id,
                    status=status,
                )
            )

    async def create(
        self, execution: ReportExecution, session: AsyncSession | None = None
    ) -> Result[ReportExecution]:
        """Create a new execution."""
        try:
            session = session or self.session
            model_data = execution.model_dump(
                exclude={"id"} if execution.id is None else set()
            )

            # Remove relationship fields from data
            model_data.pop("report_template", None)
            model_data.pop("output_executions", None)

            # Create the execution
            model = ReportExecutionModel(**model_data)
            session.add(model)
            await session.flush()

            # Set the ID in the original object
            execution.id = model.id

            # Return the execution with the new ID
            return Success(execution)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to create execution: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    execution_data=execution.model_dump(),
                )
            )

    async def update(
        self, execution: ReportExecution, session: AsyncSession | None = None
    ) -> Result[ReportExecution]:
        """Update an existing execution."""
        try:
            session = session or self.session

            # Check if execution exists
            execution_id = execution.id
            if execution_id is None:
                return Failure(
                    ReportError(
                        "Cannot update execution without ID", ErrorCode.VALIDATION_ERROR
                    )
                )

            existing_execution = await session.get(ReportExecutionModel, execution_id)
            if existing_execution is None:
                return Failure(
                    ReportError(
                        f"Execution with ID {execution_id} not found",
                        ErrorCode.NOT_FOUND,
                        execution_id=execution_id,
                    )
                )

            # Update execution fields
            model_data = execution.model_dump(
                exclude={"report_template", "output_executions"}
            )
            for key, value in model_data.items():
                if hasattr(existing_execution, key):
                    setattr(existing_execution, key, value)

            await session.flush()

            # Return the updated execution
            result = await self.get_by_id(execution_id, session)
            if result.is_failure:
                return result

            return Success(cast(ReportExecution, result.value))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to update execution: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    execution_id=execution.id,
                )
            )

    async def update_status(
        self,
        execution_id: str,
        status: str,
        error_details: str | None = None,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """Update the status of an execution."""
        try:
            session = session or self.session

            # Check if execution exists
            existing_execution = await session.get(ReportExecutionModel, execution_id)
            if existing_execution is None:
                return Failure(
                    ReportError(
                        f"Execution with ID {execution_id} not found",
                        ErrorCode.NOT_FOUND,
                        execution_id=execution_id,
                    )
                )

            # Update the status
            existing_execution.status = status
            if error_details:
                existing_execution.error_details = error_details

            # If status is completed or failed, set completed_at
            if status in ["completed", "failed"]:
                existing_execution.completed_at = datetime.now(datetime.UTC)

            await session.flush()

            return Success(True)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to update execution status: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    execution_id=execution_id,
                    status=status,
                )
            )

    async def complete_execution(
        self,
        execution_id: str,
        row_count: int,
        execution_time_ms: int,
        result_hash: str | None = None,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """Mark an execution as completed with result information."""
        try:
            session = session or self.session

            # Check if execution exists
            existing_execution = await session.get(ReportExecutionModel, execution_id)
            if existing_execution is None:
                return Failure(
                    ReportError(
                        f"Execution with ID {execution_id} not found",
                        ErrorCode.NOT_FOUND,
                        execution_id=execution_id,
                    )
                )

            # Update execution details
            existing_execution.status = "completed"
            existing_execution.completed_at = datetime.now(datetime.UTC)
            existing_execution.row_count = row_count
            existing_execution.execution_time_ms = execution_time_ms
            if result_hash:
                existing_execution.result_hash = result_hash

            await session.flush()

            return Success(True)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to complete execution: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    execution_id=execution_id,
                )
            )


class ReportOutputExecutionRepository(
    UnoBaseRepository[ReportOutputExecutionModel],
    ReportOutputExecutionRepositoryProtocol,
):
    """Repository implementation for ReportOutputExecution."""

    def __init__(self, session: AsyncSession, logger: logging.Logger | None = None):
        """Initialize the repository with a session and optional logger."""
        super().__init__(session, ReportOutputExecutionModel, logger)

    async def get_by_id(
        self, output_execution_id: str, session: AsyncSession | None = None
    ) -> Result[ReportOutputExecution | None]:
        """Get a report output execution by ID."""
        try:
            session = session or self.session
            stmt = (
                select(ReportOutputExecutionModel)
                .options(
                    joinedload(ReportOutputExecutionModel.report_execution),
                    joinedload(ReportOutputExecutionModel.report_output),
                )
                .where(ReportOutputExecutionModel.id == output_execution_id)
            )
            result = await session.execute(stmt)
            model = result.scalars().first()

            if model is None:
                return Success(None)

            return Success(ReportOutputExecution.from_orm(model))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to get output execution: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    output_execution_id=output_execution_id,
                )
            )

    async def list_by_execution(
        self, execution_id: str, session: AsyncSession | None = None
    ) -> Result[list[ReportOutputExecution]]:
        """List output executions for a report execution."""
        try:
            session = session or self.session
            stmt = (
                select(ReportOutputExecutionModel)
                .options(joinedload(ReportOutputExecutionModel.report_output))
                .where(ReportOutputExecutionModel.report_execution_id == execution_id)
            )
            result = await session.execute(stmt)
            models = result.scalars().all()

            output_executions = [
                ReportOutputExecution.from_orm(model) for model in models
            ]
            return Success(output_executions)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to list output executions for execution: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    execution_id=execution_id,
                )
            )

    async def create(
        self,
        output_execution: ReportOutputExecution,
        session: AsyncSession | None = None,
    ) -> Result[ReportOutputExecution]:
        """Create a new output execution."""
        try:
            session = session or self.session
            model_data = output_execution.model_dump(
                exclude={"id"} if output_execution.id is None else set()
            )

            # Remove relationship fields from data
            model_data.pop("report_execution", None)
            model_data.pop("report_output", None)

            # Create the output execution
            model = ReportOutputExecutionModel(**model_data)
            session.add(model)
            await session.flush()

            # Set the ID in the original object
            output_execution.id = model.id

            # Return the output execution with the new ID
            return Success(output_execution)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to create output execution: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    output_execution_data=output_execution.model_dump(),
                )
            )

    async def update(
        self,
        output_execution: ReportOutputExecution,
        session: AsyncSession | None = None,
    ) -> Result[ReportOutputExecution]:
        """Update an existing output execution."""
        try:
            session = session or self.session

            # Check if output execution exists
            output_execution_id = output_execution.id
            if output_execution_id is None:
                return Failure(
                    ReportError(
                        "Cannot update output execution without ID",
                        ErrorCode.VALIDATION_ERROR,
                    )
                )

            existing_output_execution = await session.get(
                ReportOutputExecutionModel, output_execution_id
            )
            if existing_output_execution is None:
                return Failure(
                    ReportError(
                        f"Output execution with ID {output_execution_id} not found",
                        ErrorCode.NOT_FOUND,
                        output_execution_id=output_execution_id,
                    )
                )

            # Update output execution fields
            model_data = output_execution.model_dump(
                exclude={"report_execution", "report_output"}
            )
            for key, value in model_data.items():
                if hasattr(existing_output_execution, key):
                    setattr(existing_output_execution, key, value)

            await session.flush()

            # Return the updated output execution
            result = await self.get_by_id(output_execution_id, session)
            if result.is_failure:
                return result

            return Success(cast(ReportOutputExecution, result.value))
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to update output execution: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    output_execution_id=output_execution.id,
                )
            )

    async def complete_output_execution(
        self,
        output_execution_id: str,
        output_location: str,
        output_size_bytes: int,
        session: AsyncSession | None = None,
    ) -> Result[bool]:
        """Mark an output execution as completed with result information."""
        try:
            session = session or self.session

            # Check if output execution exists
            existing_output_execution = await session.get(
                ReportOutputExecutionModel, output_execution_id
            )
            if existing_output_execution is None:
                return Failure(
                    ReportError(
                        f"Output execution with ID {output_execution_id} not found",
                        ErrorCode.NOT_FOUND,
                        output_execution_id=output_execution_id,
                    )
                )

            # Update output execution details
            existing_output_execution.status = "completed"
            existing_output_execution.completed_at = datetime.now(datetime.UTC)
            existing_output_execution.output_location = output_location
            existing_output_execution.output_size_bytes = output_size_bytes

            await session.flush()

            return Success(True)
        except Exception as e:
            return Failure(
                ReportError(
                    f"Failed to complete output execution: {str(e)}",
                    ErrorCode.DATABASE_ERROR,
                    output_execution_id=output_execution_id,
                )
            )
