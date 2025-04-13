"""Domain services for the Reports module."""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, cast

from uno.core.domain import UnoEntityService
from uno.core.errors.result import Result, Success, Failure
from uno.reports.entities import (
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
    ReportExecutionStatus,
    ReportTriggerType,
)
from uno.reports.domain_repositories import (
    ReportFieldDefinitionRepository,
    ReportTemplateRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)


class ReportFieldDefinitionService(UnoEntityService[ReportFieldDefinition]):
    """Service for report field definition entities."""

    def __init__(self, repository: ReportFieldDefinitionRepository):
        """Initialize the service.
        
        Args:
            repository: The repository for field definition entities.
        """
        super().__init__(repository)
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    async def find_by_name(self, name: str) -> Result[Optional[ReportFieldDefinition]]:
        """Find a field definition by name.
        
        Args:
            name: The name of the field definition to find.
            
        Returns:
            Success with the field definition if found, or None if not found,
            or Failure if an error occurs.
        """
        try:
            field_definition = await self.repository.find_by_name(name)
            return Success(field_definition)
        except Exception as e:
            self.logger.error(f"Error finding field definition by name: {e}")
            return Failure(str(e))

    async def find_by_field_type(self, field_type: str) -> Result[List[ReportFieldDefinition]]:
        """Find field definitions by field type.
        
        Args:
            field_type: The field type to search for.
            
        Returns:
            Success with a list of field definitions with the specified field type,
            or Failure if an error occurs.
        """
        try:
            field_definitions = await self.repository.find_by_field_type(field_type)
            return Success(field_definitions)
        except Exception as e:
            self.logger.error(f"Error finding field definitions by field type: {e}")
            return Failure(str(e))
    
    async def find_by_parent_field_id(self, parent_field_id: str) -> Result[List[ReportFieldDefinition]]:
        """Find field definitions by parent field ID.
        
        Args:
            parent_field_id: The ID of the parent field.
            
        Returns:
            Success with a list of field definitions with the specified parent field ID,
            or Failure if an error occurs.
        """
        try:
            field_definitions = await self.repository.find_by_parent_field_id(parent_field_id)
            return Success(field_definitions)
        except Exception as e:
            self.logger.error(f"Error finding field definitions by parent field ID: {e}")
            return Failure(str(e))
    
    async def find_by_template_id(self, template_id: str) -> Result[List[ReportFieldDefinition]]:
        """Find field definitions by template ID.
        
        Args:
            template_id: The ID of the template.
            
        Returns:
            Success with a list of field definitions associated with the specified template ID,
            or Failure if an error occurs.
        """
        try:
            field_definitions = await self.repository.find_by_template_id(template_id)
            return Success(field_definitions)
        except Exception as e:
            self.logger.error(f"Error finding field definitions by template ID: {e}")
            return Failure(str(e))


class ReportTemplateService(UnoEntityService[ReportTemplate]):
    """Service for report template entities."""

    def __init__(
        self,
        repository: ReportTemplateRepository,
        field_definition_service: ReportFieldDefinitionService,
        trigger_service: 'ReportTriggerService',
        output_service: 'ReportOutputService',
    ):
        """Initialize the service.
        
        Args:
            repository: The repository for template entities.
            field_definition_service: The service for field definition entities.
            trigger_service: The service for trigger entities.
            output_service: The service for output entities.
        """
        super().__init__(repository)
        self.repository = repository
        self.field_definition_service = field_definition_service
        self.trigger_service = trigger_service
        self.output_service = output_service
        self.logger = logging.getLogger(__name__)

    async def find_by_name(self, name: str) -> Result[Optional[ReportTemplate]]:
        """Find a template by name.
        
        Args:
            name: The name of the template to find.
            
        Returns:
            Success with the template if found, or None if not found,
            or Failure if an error occurs.
        """
        try:
            template = await self.repository.find_by_name(name)
            return Success(template)
        except Exception as e:
            self.logger.error(f"Error finding template by name: {e}")
            return Failure(str(e))

    async def find_by_base_object_type(self, base_object_type: str) -> Result[List[ReportTemplate]]:
        """Find templates by base object type.
        
        Args:
            base_object_type: The base object type to search for.
            
        Returns:
            Success with a list of templates with the specified base object type,
            or Failure if an error occurs.
        """
        try:
            templates = await self.repository.find_by_base_object_type(base_object_type)
            return Success(templates)
        except Exception as e:
            self.logger.error(f"Error finding templates by base object type: {e}")
            return Failure(str(e))
    
    async def get_with_relationships(self, template_id: str) -> Result[ReportTemplate]:
        """Get a template with all relationships loaded.
        
        Args:
            template_id: The ID of the template to get.
            
        Returns:
            Success with the template if found, or Failure if an error occurs.
        """
        return await self.repository.find_with_relationships(template_id)
    
    async def create_with_relationships(
        self,
        template: ReportTemplate,
        field_ids: Optional[List[str]] = None,
    ) -> Result[ReportTemplate]:
        """Create a template with field relationships.
        
        Args:
            template: The template to create.
            field_ids: Optional list of field definition IDs to associate with the template.
            
        Returns:
            Success with the created template if successful, Failure otherwise.
        """
        try:
            # Create the template
            create_result = await self.create(template)
            if create_result.is_failure:
                return create_result
            
            created_template = create_result.value
            
            # Add fields if specified
            if field_ids:
                for field_id in field_ids:
                    field_result = await self.field_definition_service.get(field_id)
                    if field_result.is_failure:
                        continue  # Skip invalid fields
                    
                    field = field_result.value
                    created_template.add_field(field)
                
                # Update the template with the new field relationships
                await self.repository.update(created_template)
            
            # Return the template with relationships loaded
            return await self.get_with_relationships(created_template.id)
        except Exception as e:
            self.logger.error(f"Error creating template with relationships: {e}")
            return Failure(str(e))
    
    async def update_fields(
        self,
        template_id: str,
        field_ids_to_add: Optional[List[str]] = None,
        field_ids_to_remove: Optional[List[str]] = None,
    ) -> Result[ReportTemplate]:
        """Update the fields associated with a template.
        
        Args:
            template_id: The ID of the template to update.
            field_ids_to_add: Optional list of field definition IDs to add to the template.
            field_ids_to_remove: Optional list of field definition IDs to remove from the template.
            
        Returns:
            Success with the updated template if successful, Failure otherwise.
        """
        try:
            # Get the template with its current fields
            template_result = await self.get_with_relationships(template_id)
            if template_result.is_failure:
                return template_result
            
            template = template_result.value
            
            # Remove fields
            if field_ids_to_remove:
                for field_id in field_ids_to_remove:
                    # Find the field in the template's fields
                    for field in template.fields[:]:  # Create a copy to modify during iteration
                        if field.id == field_id:
                            template.remove_field(field)
                            break
            
            # Add fields
            if field_ids_to_add:
                for field_id in field_ids_to_add:
                    # Skip if the field is already in the template
                    if any(field.id == field_id for field in template.fields):
                        continue
                    
                    field_result = await self.field_definition_service.get(field_id)
                    if field_result.is_failure:
                        continue  # Skip invalid fields
                    
                    field = field_result.value
                    template.add_field(field)
            
            # Update the template
            await self.repository.update(template)
            
            # Return the template with updated relationships
            return await self.get_with_relationships(template_id)
        except Exception as e:
            self.logger.error(f"Error updating template fields: {e}")
            return Failure(str(e))
    
    async def execute_template(
        self,
        template_id: str,
        triggered_by: str,
        trigger_type: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Result[ReportExecution]:
        """Execute a report template.
        
        Args:
            template_id: The ID of the template to execute.
            triggered_by: The ID or name of the entity that triggered the execution.
            trigger_type: The type of trigger that initiated the execution.
            parameters: Optional parameters for the execution.
            
        Returns:
            Success with the execution if successful, Failure otherwise.
        """
        # This would typically integrate with a report generation system
        # Here we'll create an execution record but not actually generate the report
        try:
            # Get the template
            template_result = await self.get_with_relationships(template_id)
            if template_result.is_failure:
                return Failure(f"Template not found: {template_result.error}")
            
            template = template_result.value
            
            # Create the execution record
            execution = ReportExecution(
                report_template_id=template_id,
                triggered_by=triggered_by,
                trigger_type=trigger_type,
                parameters=parameters or {},
                status=ReportExecutionStatus.PENDING,
            )
            
            # Add the execution to the template
            template.add_execution(execution)
            
            # Validate the execution
            validation_result = execution.validate()
            if validation_result.is_failure:
                return Failure(f"Invalid execution: {validation_result.error}")
            
            # This is where you would actually generate the report
            # For this example, we'll just mark it as completed with some dummy data
            execution.status = ReportExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.row_count = 100
            execution.execution_time_ms = 1000
            execution.result_hash = "dummy_hash"
            
            # Create the execution record using the execution repository
            # In a real implementation, you would get this from a DI container
            from uno.dependencies import get_service
            execution_repository = get_service(ReportExecutionRepository)
            execution_result = await execution_repository.create(execution)
            
            # Create output executions for all active outputs
            output_execution_repository = get_service(ReportOutputExecutionRepository)
            
            for output in template.outputs:
                if output.is_active:
                    output_execution = ReportOutputExecution(
                        report_execution_id=execution.id,
                        report_output_id=output.id,
                        status=ReportExecutionStatus.COMPLETED,
                        completed_at=datetime.utcnow(),
                        output_location=f"/reports/{template.name}/{execution.id}.{output.format.lower()}",
                        output_size_bytes=1024,
                    )
                    
                    # Add the output execution to the execution
                    execution.add_output_execution(output_execution)
                    
                    # Create the output execution record
                    await output_execution_repository.create(output_execution)
            
            return Success(execution)
        except Exception as e:
            self.logger.error(f"Error executing template: {e}")
            return Failure(str(e))


class ReportTriggerService(UnoEntityService[ReportTrigger]):
    """Service for report trigger entities."""

    def __init__(self, repository: ReportTriggerRepository):
        """Initialize the service.
        
        Args:
            repository: The repository for trigger entities.
        """
        super().__init__(repository)
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    async def find_by_template_id(self, template_id: str) -> Result[List[ReportTrigger]]:
        """Find triggers by template ID.
        
        Args:
            template_id: The ID of the template.
            
        Returns:
            Success with a list of triggers associated with the specified template ID,
            or Failure if an error occurs.
        """
        try:
            triggers = await self.repository.find_by_template_id(template_id)
            return Success(triggers)
        except Exception as e:
            self.logger.error(f"Error finding triggers by template ID: {e}")
            return Failure(str(e))

    async def find_by_trigger_type(self, trigger_type: str) -> Result[List[ReportTrigger]]:
        """Find triggers by trigger type.
        
        Args:
            trigger_type: The trigger type to search for.
            
        Returns:
            Success with a list of triggers with the specified trigger type,
            or Failure if an error occurs.
        """
        try:
            triggers = await self.repository.find_by_trigger_type(trigger_type)
            return Success(triggers)
        except Exception as e:
            self.logger.error(f"Error finding triggers by trigger type: {e}")
            return Failure(str(e))
    
    async def find_active_triggers(self) -> Result[List[ReportTrigger]]:
        """Find all active triggers.
        
        Returns:
            Success with a list of all active triggers,
            or Failure if an error occurs.
        """
        try:
            triggers = await self.repository.find_active_triggers()
            return Success(triggers)
        except Exception as e:
            self.logger.error(f"Error finding active triggers: {e}")
            return Failure(str(e))
    
    async def find_active_scheduled_triggers(self) -> Result[List[ReportTrigger]]:
        """Find active scheduled triggers.
        
        Returns:
            Success with a list of active scheduled triggers,
            or Failure if an error occurs.
        """
        try:
            triggers = await self.repository.find_active_scheduled_triggers()
            return Success(triggers)
        except Exception as e:
            self.logger.error(f"Error finding active scheduled triggers: {e}")
            return Failure(str(e))
    
    async def process_due_triggers(self) -> Result[int]:
        """Process all due scheduled triggers.
        
        This method would typically be called by a scheduler to execute reports
        based on their schedule.
        
        Returns:
            Success with the number of triggers processed,
            or Failure if an error occurs.
        """
        try:
            # Get all active scheduled triggers
            triggers_result = await self.find_active_scheduled_triggers()
            if triggers_result.is_failure:
                return triggers_result
            
            triggers = triggers_result.value
            processed_count = 0
            
            # In a real implementation, you would check each trigger's schedule
            # to see if it's due to run. For this example, we'll just pretend they're all due.
            
            for trigger in triggers:
                # Get the template service
                from uno.dependencies import get_service
                template_service = get_service(ReportTemplateService)
                
                # Execute the template
                execution_result = await template_service.execute_template(
                    template_id=trigger.report_template_id,
                    triggered_by="scheduler",
                    trigger_type=ReportTriggerType.SCHEDULED,
                    parameters={},
                )
                
                if execution_result.is_success:
                    processed_count += 1
                    
                    # Update the trigger's last_triggered timestamp
                    trigger.last_triggered = datetime.utcnow()
                    await self.repository.update(trigger)
            
            return Success(processed_count)
        except Exception as e:
            self.logger.error(f"Error processing due triggers: {e}")
            return Failure(str(e))


class ReportOutputService(UnoEntityService[ReportOutput]):
    """Service for report output entities."""

    def __init__(self, repository: ReportOutputRepository):
        """Initialize the service.
        
        Args:
            repository: The repository for output entities.
        """
        super().__init__(repository)
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    async def find_by_template_id(self, template_id: str) -> Result[List[ReportOutput]]:
        """Find outputs by template ID.
        
        Args:
            template_id: The ID of the template.
            
        Returns:
            Success with a list of outputs associated with the specified template ID,
            or Failure if an error occurs.
        """
        try:
            outputs = await self.repository.find_by_template_id(template_id)
            return Success(outputs)
        except Exception as e:
            self.logger.error(f"Error finding outputs by template ID: {e}")
            return Failure(str(e))

    async def find_by_output_type(self, output_type: str) -> Result[List[ReportOutput]]:
        """Find outputs by output type.
        
        Args:
            output_type: The output type to search for.
            
        Returns:
            Success with a list of outputs with the specified output type,
            or Failure if an error occurs.
        """
        try:
            outputs = await self.repository.find_by_output_type(output_type)
            return Success(outputs)
        except Exception as e:
            self.logger.error(f"Error finding outputs by output type: {e}")
            return Failure(str(e))
    
    async def find_active_outputs(self) -> Result[List[ReportOutput]]:
        """Find all active outputs.
        
        Returns:
            Success with a list of all active outputs,
            or Failure if an error occurs.
        """
        try:
            outputs = await self.repository.find_active_outputs()
            return Success(outputs)
        except Exception as e:
            self.logger.error(f"Error finding active outputs: {e}")
            return Failure(str(e))


class ReportExecutionService(UnoEntityService[ReportExecution]):
    """Service for report execution entities."""

    def __init__(self, repository: ReportExecutionRepository):
        """Initialize the service.
        
        Args:
            repository: The repository for execution entities.
        """
        super().__init__(repository)
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    async def find_by_template_id(self, template_id: str) -> Result[List[ReportExecution]]:
        """Find executions by template ID.
        
        Args:
            template_id: The ID of the template.
            
        Returns:
            Success with a list of executions associated with the specified template ID,
            or Failure if an error occurs.
        """
        try:
            executions = await self.repository.find_by_template_id(template_id)
            return Success(executions)
        except Exception as e:
            self.logger.error(f"Error finding executions by template ID: {e}")
            return Failure(str(e))

    async def find_by_status(self, status: str) -> Result[List[ReportExecution]]:
        """Find executions by status.
        
        Args:
            status: The status to search for.
            
        Returns:
            Success with a list of executions with the specified status,
            or Failure if an error occurs.
        """
        try:
            executions = await self.repository.find_by_status(status)
            return Success(executions)
        except Exception as e:
            self.logger.error(f"Error finding executions by status: {e}")
            return Failure(str(e))
    
    async def find_by_triggered_by(self, triggered_by: str) -> Result[List[ReportExecution]]:
        """Find executions by triggered by.
        
        Args:
            triggered_by: The triggered by value to search for.
            
        Returns:
            Success with a list of executions with the specified triggered by value,
            or Failure if an error occurs.
        """
        try:
            executions = await self.repository.find_by_triggered_by(triggered_by)
            return Success(executions)
        except Exception as e:
            self.logger.error(f"Error finding executions by triggered by: {e}")
            return Failure(str(e))
    
    async def find_with_output_executions(self, execution_id: str) -> Result[ReportExecution]:
        """Find an execution with output executions loaded.
        
        Args:
            execution_id: The ID of the execution to find.
            
        Returns:
            Success with the execution if found, Failure otherwise.
        """
        return await self.repository.find_with_output_executions(execution_id)
    
    async def find_recent_executions(self, limit: int = 10) -> Result[List[ReportExecution]]:
        """Find recent executions.
        
        Args:
            limit: The maximum number of executions to return.
            
        Returns:
            Success with a list of recent executions,
            or Failure if an error occurs.
        """
        try:
            executions = await self.repository.find_recent_executions(limit)
            return Success(executions)
        except Exception as e:
            self.logger.error(f"Error finding recent executions: {e}")
            return Failure(str(e))
    
    async def update_execution_status(
        self,
        execution_id: str,
        status: str,
        error_details: Optional[str] = None,
    ) -> Result[ReportExecution]:
        """Update the status of an execution.
        
        Args:
            execution_id: The ID of the execution to update.
            status: The new status.
            error_details: Optional error details if the status is failed.
            
        Returns:
            Success with the updated execution if successful, Failure otherwise.
        """
        try:
            # Get the execution
            execution_result = await self.get(execution_id)
            if execution_result.is_failure:
                return execution_result
            
            execution = execution_result.value
            
            # Update the status
            status_result = execution.update_status(status, error_details)
            if status_result.is_failure:
                return Failure(f"Invalid status update: {status_result.error}")
            
            # Update the execution
            update_result = await self.update(execution)
            return update_result
        except Exception as e:
            self.logger.error(f"Error updating execution status: {e}")
            return Failure(str(e))


class ReportOutputExecutionService(UnoEntityService[ReportOutputExecution]):
    """Service for report output execution entities."""

    def __init__(self, repository: ReportOutputExecutionRepository):
        """Initialize the service.
        
        Args:
            repository: The repository for output execution entities.
        """
        super().__init__(repository)
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    async def find_by_execution_id(self, execution_id: str) -> Result[List[ReportOutputExecution]]:
        """Find output executions by execution ID.
        
        Args:
            execution_id: The ID of the execution.
            
        Returns:
            Success with a list of output executions associated with the specified execution ID,
            or Failure if an error occurs.
        """
        try:
            output_executions = await self.repository.find_by_execution_id(execution_id)
            return Success(output_executions)
        except Exception as e:
            self.logger.error(f"Error finding output executions by execution ID: {e}")
            return Failure(str(e))

    async def find_by_output_id(self, output_id: str) -> Result[List[ReportOutputExecution]]:
        """Find output executions by output ID.
        
        Args:
            output_id: The ID of the output.
            
        Returns:
            Success with a list of output executions associated with the specified output ID,
            or Failure if an error occurs.
        """
        try:
            output_executions = await self.repository.find_by_output_id(output_id)
            return Success(output_executions)
        except Exception as e:
            self.logger.error(f"Error finding output executions by output ID: {e}")
            return Failure(str(e))
    
    async def find_by_status(self, status: str) -> Result[List[ReportOutputExecution]]:
        """Find output executions by status.
        
        Args:
            status: The status to search for.
            
        Returns:
            Success with a list of output executions with the specified status,
            or Failure if an error occurs.
        """
        try:
            output_executions = await self.repository.find_by_status(status)
            return Success(output_executions)
        except Exception as e:
            self.logger.error(f"Error finding output executions by status: {e}")
            return Failure(str(e))
    
    async def update_output_execution_status(
        self,
        output_execution_id: str,
        status: str,
        error_details: Optional[str] = None,
    ) -> Result[ReportOutputExecution]:
        """Update the status of an output execution.
        
        Args:
            output_execution_id: The ID of the output execution to update.
            status: The new status.
            error_details: Optional error details if the status is failed.
            
        Returns:
            Success with the updated output execution if successful, Failure otherwise.
        """
        try:
            # Get the output execution
            output_execution_result = await self.get(output_execution_id)
            if output_execution_result.is_failure:
                return output_execution_result
            
            output_execution = output_execution_result.value
            
            # Update the status
            status_result = output_execution.update_status(status, error_details)
            if status_result.is_failure:
                return Failure(f"Invalid status update: {status_result.error}")
            
            # Update the output execution
            update_result = await self.update(output_execution)
            return update_result
        except Exception as e:
            self.logger.error(f"Error updating output execution status: {e}")
            return Failure(str(e))