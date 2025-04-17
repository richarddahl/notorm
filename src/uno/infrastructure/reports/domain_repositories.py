"""Domain repositories for the Reports module."""

from typing import Any, Dict, List, Optional, Sequence, TypeVar, cast

from uno.core.errors.result import Result, Success, Failure
from uno.domain.repository import UnoDBRepository
from uno.reports.entities import (
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
)


class ReportFieldDefinitionRepository(UnoDBRepository[ReportFieldDefinition]):
    """Repository for report field definition entities."""

    async def find_by_name(self, name: str) -> Optional[ReportFieldDefinition]:
        """Find a field definition by name.

        Args:
            name: The name of the field definition to find.

        Returns:
            The field definition if found, None otherwise.
        """
        filters = {"name": {"lookup": "eq", "val": name}}
        results = await self.list(filters=filters, limit=1)
        return results[0] if results else None

    async def find_by_field_type(self, field_type: str) -> List[ReportFieldDefinition]:
        """Find field definitions by field type.

        Args:
            field_type: The field type to search for.

        Returns:
            A list of field definitions with the specified field type.
        """
        filters = {"field_type": {"lookup": "eq", "val": field_type}}
        return await self.list(filters=filters)

    async def find_by_parent_field_id(
        self, parent_field_id: str
    ) -> List[ReportFieldDefinition]:
        """Find field definitions by parent field ID.

        Args:
            parent_field_id: The ID of the parent field.

        Returns:
            A list of field definitions with the specified parent field ID.
        """
        filters = {"parent_field_id": {"lookup": "eq", "val": parent_field_id}}
        return await self.list(filters=filters)

    async def find_by_template_id(
        self, template_id: str
    ) -> List[ReportFieldDefinition]:
        """Find field definitions by template ID.

        Args:
            template_id: The ID of the template.

        Returns:
            A list of field definitions associated with the specified template ID.
        """
        # Note: This requires joining through the junction table
        # Implementation may vary based on your ORM specifics
        query = f"""
        SELECT fd.* 
        FROM report_field_definition fd
        JOIN report_template__field tf ON fd.id = tf.report_field_definition_id
        WHERE tf.report_template_id = :template_id
        """
        results = await self._db.fetch_all(query, {"template_id": template_id})
        return [self._create_entity_from_row(row) for row in results]


class ReportTemplateRepository(UnoDBRepository[ReportTemplate]):
    """Repository for report template entities."""

    async def find_by_name(self, name: str) -> Optional[ReportTemplate]:
        """Find a template by name.

        Args:
            name: The name of the template to find.

        Returns:
            The template if found, None otherwise.
        """
        filters = {"name": {"lookup": "eq", "val": name}}
        results = await self.list(filters=filters, limit=1)
        return results[0] if results else None

    async def find_by_base_object_type(
        self, base_object_type: str
    ) -> List[ReportTemplate]:
        """Find templates by base object type.

        Args:
            base_object_type: The base object type to search for.

        Returns:
            A list of templates with the specified base object type.
        """
        filters = {"base_object_type": {"lookup": "eq", "val": base_object_type}}
        return await self.list(filters=filters)

    async def find_with_relationships(self, template_id: str) -> Result[ReportTemplate]:
        """Find a template with all relationships loaded.

        Args:
            template_id: The ID of the template to find.

        Returns:
            Success with the template if found, Failure otherwise.
        """
        try:
            template = await self.get(template_id)
            if not template:
                return Failure(f"Template with ID {template_id} not found")

            # Load all relationships
            await self.load_relationships(template)
            return Success(template)
        except Exception as e:
            return Failure(str(e))


class ReportTriggerRepository(UnoDBRepository[ReportTrigger]):
    """Repository for report trigger entities."""

    async def find_by_template_id(self, template_id: str) -> List[ReportTrigger]:
        """Find triggers by template ID.

        Args:
            template_id: The ID of the template.

        Returns:
            A list of triggers associated with the specified template ID.
        """
        filters = {"report_template_id": {"lookup": "eq", "val": template_id}}
        return await self.list(filters=filters)

    async def find_by_trigger_type(self, trigger_type: str) -> List[ReportTrigger]:
        """Find triggers by trigger type.

        Args:
            trigger_type: The trigger type to search for.

        Returns:
            A list of triggers with the specified trigger type.
        """
        filters = {"trigger_type": {"lookup": "eq", "val": trigger_type}}
        return await self.list(filters=filters)

    async def find_active_triggers(self) -> List[ReportTrigger]:
        """Find all active triggers.

        Returns:
            A list of all active triggers.
        """
        filters = {"is_active": {"lookup": "eq", "val": True}}
        return await self.list(filters=filters)

    async def find_active_scheduled_triggers(self) -> List[ReportTrigger]:
        """Find active scheduled triggers.

        Returns:
            A list of active scheduled triggers.
        """
        filters = {
            "is_active": {"lookup": "eq", "val": True},
            "trigger_type": {"lookup": "eq", "val": "scheduled"},
        }
        return await self.list(filters=filters)


class ReportOutputRepository(UnoDBRepository[ReportOutput]):
    """Repository for report output entities."""

    async def find_by_template_id(self, template_id: str) -> List[ReportOutput]:
        """Find outputs by template ID.

        Args:
            template_id: The ID of the template.

        Returns:
            A list of outputs associated with the specified template ID.
        """
        filters = {"report_template_id": {"lookup": "eq", "val": template_id}}
        return await self.list(filters=filters)

    async def find_by_output_type(self, output_type: str) -> List[ReportOutput]:
        """Find outputs by output type.

        Args:
            output_type: The output type to search for.

        Returns:
            A list of outputs with the specified output type.
        """
        filters = {"output_type": {"lookup": "eq", "val": output_type}}
        return await self.list(filters=filters)

    async def find_active_outputs(self) -> List[ReportOutput]:
        """Find all active outputs.

        Returns:
            A list of all active outputs.
        """
        filters = {"is_active": {"lookup": "eq", "val": True}}
        return await self.list(filters=filters)


class ReportExecutionRepository(UnoDBRepository[ReportExecution]):
    """Repository for report execution entities."""

    async def find_by_template_id(self, template_id: str) -> List[ReportExecution]:
        """Find executions by template ID.

        Args:
            template_id: The ID of the template.

        Returns:
            A list of executions associated with the specified template ID.
        """
        filters = {"report_template_id": {"lookup": "eq", "val": template_id}}
        return await self.list(filters=filters)

    async def find_by_status(self, status: str) -> List[ReportExecution]:
        """Find executions by status.

        Args:
            status: The status to search for.

        Returns:
            A list of executions with the specified status.
        """
        filters = {"status": {"lookup": "eq", "val": status}}
        return await self.list(filters=filters)

    async def find_by_triggered_by(self, triggered_by: str) -> List[ReportExecution]:
        """Find executions by triggered by.

        Args:
            triggered_by: The triggered by value to search for.

        Returns:
            A list of executions with the specified triggered by value.
        """
        filters = {"triggered_by": {"lookup": "eq", "val": triggered_by}}
        return await self.list(filters=filters)

    async def find_with_output_executions(
        self, execution_id: str
    ) -> Result[ReportExecution]:
        """Find an execution with output executions loaded.

        Args:
            execution_id: The ID of the execution to find.

        Returns:
            Success with the execution if found, Failure otherwise.
        """
        try:
            execution = await self.get(execution_id)
            if not execution:
                return Failure(f"Execution with ID {execution_id} not found")

            # Load output executions relationship
            await self.load_relationships(execution, ["output_executions"])
            return Success(execution)
        except Exception as e:
            return Failure(str(e))

    async def find_recent_executions(self, limit: int = 10) -> List[ReportExecution]:
        """Find recent executions.

        Args:
            limit: The maximum number of executions to return.

        Returns:
            A list of recent executions.
        """
        return await self.list(order_by="started_at", order_dir="desc", limit=limit)


class ReportOutputExecutionRepository(UnoDBRepository[ReportOutputExecution]):
    """Repository for report output execution entities."""

    async def find_by_execution_id(
        self, execution_id: str
    ) -> List[ReportOutputExecution]:
        """Find output executions by execution ID.

        Args:
            execution_id: The ID of the execution.

        Returns:
            A list of output executions associated with the specified execution ID.
        """
        filters = {"report_execution_id": {"lookup": "eq", "val": execution_id}}
        return await self.list(filters=filters)

    async def find_by_output_id(self, output_id: str) -> List[ReportOutputExecution]:
        """Find output executions by output ID.

        Args:
            output_id: The ID of the output.

        Returns:
            A list of output executions associated with the specified output ID.
        """
        filters = {"report_output_id": {"lookup": "eq", "val": output_id}}
        return await self.list(filters=filters)

    async def find_by_status(self, status: str) -> List[ReportOutputExecution]:
        """Find output executions by status.

        Args:
            status: The status to search for.

        Returns:
            A list of output executions with the specified status.
        """
        filters = {"status": {"lookup": "eq", "val": status}}
        return await self.list(filters=filters)
