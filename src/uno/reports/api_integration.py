"""API integration for the Reports module."""

from typing import Any, Dict, List, Optional, Union, Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, FastAPI
from pydantic import BaseModel

from uno.reports.entities import (
    ReportFieldDefinition,
    ReportTemplate,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportOutputExecution,
)
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
from uno.reports.schemas import (
    ReportFieldDefinitionSchemaManager,
    ReportTemplateSchemaManager,
    ReportTriggerSchemaManager,
    ReportOutputSchemaManager,
    ReportExecutionSchemaManager,
    ReportOutputExecutionSchemaManager,
)
from uno.reports.dtos import (
    # Field Definition DTOs
    ReportFieldDefinitionCreateDto,
    ReportFieldDefinitionUpdateDto,
    ReportFieldDefinitionViewDto,
    ReportFieldDefinitionFilterParams,
    
    # Template DTOs
    ReportTemplateCreateDto,
    ReportTemplateUpdateDto,
    ReportTemplateViewDto,
    ReportTemplateFilterParams,
    
    # Trigger DTOs
    ReportTriggerCreateDto,
    ReportTriggerUpdateDto,
    ReportTriggerViewDto,
    ReportTriggerFilterParams,
    
    # Output DTOs
    ReportOutputCreateDto,
    ReportOutputUpdateDto,
    ReportOutputViewDto,
    ReportOutputFilterParams,
    
    # Execution DTOs
    ReportExecutionCreateDto,
    ReportExecutionUpdateStatusDto,
    ReportExecutionViewDto,
    ReportExecutionFilterParams,
    
    # Output Execution DTOs
    ReportOutputExecutionCreateDto,
    ReportOutputExecutionUpdateStatusDto,
    ReportOutputExecutionViewDto,
    ReportOutputExecutionFilterParams,
)


def register_report_field_definition_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    field_definition_service: Optional[ReportFieldDefinitionService] = None,
) -> Dict[str, Any]:
    """Register API endpoints for report field definitions.
    
    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        field_definition_service: Optional field definition service to use.
        
    Returns:
        A dictionary of endpoint handlers.
    """
    router = APIRouter(
        prefix=f"{path_prefix}/report-field-definitions",
        tags=["Report Field Definitions"],
        dependencies=dependencies or [],
    )
    
    handlers = {}
    
    # Get service from DI container if not provided
    if field_definition_service is None:
        from uno.dependencies import get_service
        field_definition_service = get_service(ReportFieldDefinitionService)
    
    schema_manager = ReportFieldDefinitionSchemaManager()
    
    # Create field definition
    @router.post(
        "",
        response_model=ReportFieldDefinitionViewDto,
        status_code=201,
        summary="Create a new report field definition",
    )
    async def create_field_definition(
        data: ReportFieldDefinitionCreateDto = Body(...),
    ) -> ReportFieldDefinitionViewDto:
        """Create a new report field definition."""
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data)
        
        # Create entity
        result = await field_definition_service.create(entity)
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        # Convert entity to DTO
        return schema_manager.entity_to_dto(result.value)
    
    handlers["create_field_definition"] = create_field_definition
    
    # Get field definition by ID
    @router.get(
        "/{field_definition_id}",
        response_model=ReportFieldDefinitionViewDto,
        summary="Get a report field definition by ID",
    )
    async def get_field_definition(
        field_definition_id: str = Path(..., description="The ID of the field definition"),
    ) -> ReportFieldDefinitionViewDto:
        """Get a report field definition by ID."""
        result = await field_definition_service.get(field_definition_id)
        if result.is_failure:
            raise HTTPException(status_code=404, detail=f"Field definition with ID {field_definition_id} not found")
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["get_field_definition"] = get_field_definition
    
    # List field definitions with filtering
    @router.get(
        "",
        response_model=List[ReportFieldDefinitionViewDto],
        summary="List report field definitions",
    )
    async def list_field_definitions(
        name: Optional[str] = Query(None, description="Filter by field name"),
        field_type: Optional[str] = Query(None, description="Filter by field type"),
        parent_field_id: Optional[str] = Query(None, description="Filter by parent field ID"),
        template_id: Optional[str] = Query(None, description="Filter by template ID"),
        is_visible: Optional[bool] = Query(None, description="Filter by visibility"),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> List[ReportFieldDefinitionViewDto]:
        """List report field definitions with filtering."""
        filters = {}
        
        if name:
            filters["name"] = {"lookup": "eq", "val": name}
        if field_type:
            filters["field_type"] = {"lookup": "eq", "val": field_type}
        if parent_field_id:
            filters["parent_field_id"] = {"lookup": "eq", "val": parent_field_id}
        if is_visible is not None:
            filters["is_visible"] = {"lookup": "eq", "val": is_visible}
        
        # Handle template_id special case
        if template_id:
            # Using the repository method that joins through the junction table
            field_definition_repository = field_definition_service.repository
            entities = await field_definition_repository.find_by_template_id(template_id)
            # Apply skip and limit
            entities = entities[skip:skip + limit]
            return schema_manager.entity_list_to_dto_list(entities)
        
        # Standard filtering
        result = await field_definition_service.list(filters=filters, skip=skip, limit=limit)
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return schema_manager.entity_list_to_dto_list(result.value)
    
    handlers["list_field_definitions"] = list_field_definitions
    
    # Update field definition
    @router.patch(
        "/{field_definition_id}",
        response_model=ReportFieldDefinitionViewDto,
        summary="Update a report field definition",
    )
    async def update_field_definition(
        field_definition_id: str = Path(..., description="The ID of the field definition"),
        data: ReportFieldDefinitionUpdateDto = Body(...),
    ) -> ReportFieldDefinitionViewDto:
        """Update a report field definition."""
        # Get existing entity
        get_result = await field_definition_service.get(field_definition_id)
        if get_result.is_failure:
            raise HTTPException(status_code=404, detail=f"Field definition with ID {field_definition_id} not found")
        
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data, get_result.value)
        
        # Update entity
        update_result = await field_definition_service.update(entity)
        if update_result.is_failure:
            raise HTTPException(status_code=400, detail=str(update_result.error))
        
        return schema_manager.entity_to_dto(update_result.value)
    
    handlers["update_field_definition"] = update_field_definition
    
    # Delete field definition
    @router.delete(
        "/{field_definition_id}",
        status_code=204,
        summary="Delete a report field definition",
    )
    async def delete_field_definition(
        field_definition_id: str = Path(..., description="The ID of the field definition"),
    ) -> None:
        """Delete a report field definition."""
        delete_result = await field_definition_service.delete(field_definition_id)
        if delete_result.is_failure:
            raise HTTPException(status_code=404, detail=f"Field definition with ID {field_definition_id} not found")
    
    handlers["delete_field_definition"] = delete_field_definition
    
    # Register router
    app_or_router.include_router(router)
    
    return handlers


def register_report_template_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    template_service: Optional[ReportTemplateService] = None,
    field_definition_service: Optional[ReportFieldDefinitionService] = None,
) -> Dict[str, Any]:
    """Register API endpoints for report templates.
    
    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        template_service: Optional template service to use.
        field_definition_service: Optional field definition service to use.
        
    Returns:
        A dictionary of endpoint handlers.
    """
    router = APIRouter(
        prefix=f"{path_prefix}/report-templates",
        tags=["Report Templates"],
        dependencies=dependencies or [],
    )
    
    handlers = {}
    
    # Get services from DI container if not provided
    if template_service is None or field_definition_service is None:
        from uno.dependencies import get_service
        template_service = template_service or get_service(ReportTemplateService)
        field_definition_service = field_definition_service or get_service(ReportFieldDefinitionService)
    
    schema_manager = ReportTemplateSchemaManager()
    field_definition_schema_manager = ReportFieldDefinitionSchemaManager()
    
    # Create template
    @router.post(
        "",
        response_model=ReportTemplateViewDto,
        status_code=201,
        summary="Create a new report template",
    )
    async def create_template(
        data: ReportTemplateCreateDto = Body(...),
    ) -> ReportTemplateViewDto:
        """Create a new report template."""
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data)
        
        # If field_ids are provided, use create_with_relationships
        if hasattr(data, "field_ids") and data.field_ids:
            result = await template_service.create_with_relationships(entity, data.field_ids)
        else:
            result = await template_service.create(entity)
        
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        # Get with relationships
        get_result = await template_service.get_with_relationships(result.value.id)
        if get_result.is_failure:
            # Fall back to entity without relationships
            return schema_manager.entity_to_dto(result.value)
        
        return schema_manager.entity_to_dto(get_result.value)
    
    handlers["create_template"] = create_template
    
    # Get template by ID
    @router.get(
        "/{template_id}",
        response_model=ReportTemplateViewDto,
        summary="Get a report template by ID",
    )
    async def get_template(
        template_id: str = Path(..., description="The ID of the template"),
    ) -> ReportTemplateViewDto:
        """Get a report template by ID."""
        result = await template_service.get_with_relationships(template_id)
        if result.is_failure:
            # Try getting without relationships
            simple_result = await template_service.get(template_id)
            if simple_result.is_failure:
                raise HTTPException(status_code=404, detail=f"Template with ID {template_id} not found")
            return schema_manager.entity_to_dto(simple_result.value)
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["get_template"] = get_template
    
    # List templates with filtering
    @router.get(
        "",
        response_model=List[ReportTemplateViewDto],
        summary="List report templates",
    )
    async def list_templates(
        name: Optional[str] = Query(None, description="Filter by template name"),
        base_object_type: Optional[str] = Query(None, description="Filter by base object type"),
        field_id: Optional[str] = Query(None, description="Filter by associated field ID"),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> List[ReportTemplateViewDto]:
        """List report templates with filtering."""
        filters = {}
        
        if name:
            filters["name"] = {"lookup": "eq", "val": name}
        if base_object_type:
            filters["base_object_type"] = {"lookup": "eq", "val": base_object_type}
        
        # Handle field_id special case
        if field_id:
            # This would need a custom repository method
            # For this example, we'll just get all templates and filter in memory
            result = await template_service.list()
            if result.is_failure:
                raise HTTPException(status_code=400, detail=str(result.error))
            
            # Load relationships for all templates
            templates_with_fields = []
            for template in result.value:
                template_result = await template_service.get_with_relationships(template.id)
                if template_result.is_success:
                    templates_with_fields.append(template_result.value)
            
            # Filter templates by field_id
            filtered_templates = [
                template for template in templates_with_fields
                if any(field.id == field_id for field in template.fields)
            ]
            
            # Apply skip and limit
            paginated_templates = filtered_templates[skip:skip + limit]
            
            return schema_manager.entity_list_to_dto_list(paginated_templates)
        
        # Standard filtering
        result = await template_service.list(filters=filters, skip=skip, limit=limit)
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        # Load relationships for all templates
        templates_with_fields = []
        for template in result.value:
            template_result = await template_service.get_with_relationships(template.id)
            if template_result.is_success:
                templates_with_fields.append(template_result.value)
            else:
                templates_with_fields.append(template)
        
        return schema_manager.entity_list_to_dto_list(templates_with_fields)
    
    handlers["list_templates"] = list_templates
    
    # Update template
    @router.patch(
        "/{template_id}",
        response_model=ReportTemplateViewDto,
        summary="Update a report template",
    )
    async def update_template(
        template_id: str = Path(..., description="The ID of the template"),
        data: ReportTemplateUpdateDto = Body(...),
    ) -> ReportTemplateViewDto:
        """Update a report template."""
        # Get existing entity
        get_result = await template_service.get(template_id)
        if get_result.is_failure:
            raise HTTPException(status_code=404, detail=f"Template with ID {template_id} not found")
        
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data, get_result.value)
        
        # Update entity
        update_result = await template_service.update(entity)
        if update_result.is_failure:
            raise HTTPException(status_code=400, detail=str(update_result.error))
        
        # Get with relationships
        result = await template_service.get_with_relationships(template_id)
        if result.is_failure:
            # Fall back to entity without relationships
            return schema_manager.entity_to_dto(update_result.value)
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["update_template"] = update_template
    
    # Update template fields
    @router.put(
        "/{template_id}/fields",
        response_model=ReportTemplateViewDto,
        summary="Update fields associated with a report template",
    )
    async def update_template_fields(
        template_id: str = Path(..., description="The ID of the template"),
        field_ids_to_add: List[str] = Body(default=[]),
        field_ids_to_remove: List[str] = Body(default=[]),
    ) -> ReportTemplateViewDto:
        """Update fields associated with a report template."""
        # Update template fields
        result = await template_service.update_fields(
            template_id=template_id,
            field_ids_to_add=field_ids_to_add,
            field_ids_to_remove=field_ids_to_remove,
        )
        
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["update_template_fields"] = update_template_fields
    
    # Delete template
    @router.delete(
        "/{template_id}",
        status_code=204,
        summary="Delete a report template",
    )
    async def delete_template(
        template_id: str = Path(..., description="The ID of the template"),
    ) -> None:
        """Delete a report template."""
        delete_result = await template_service.delete(template_id)
        if delete_result.is_failure:
            raise HTTPException(status_code=404, detail=f"Template with ID {template_id} not found")
    
    handlers["delete_template"] = delete_template
    
    # Execute template
    @router.post(
        "/{template_id}/execute",
        response_model=ReportExecutionViewDto,
        summary="Execute a report template",
    )
    async def execute_template(
        template_id: str = Path(..., description="The ID of the template"),
        triggered_by: str = Body(..., description="ID or name of the entity triggering the execution"),
        parameters: Dict[str, Any] = Body(default={}),
    ) -> ReportExecutionViewDto:
        """Execute a report template."""
        execution_result = await template_service.execute_template(
            template_id=template_id,
            triggered_by=triggered_by,
            trigger_type="manual",
            parameters=parameters,
        )
        
        if execution_result.is_failure:
            raise HTTPException(status_code=400, detail=str(execution_result.error))
        
        # Use execution schema manager to convert the entity to a DTO
        execution_schema_manager = ReportExecutionSchemaManager()
        return execution_schema_manager.entity_to_dto(execution_result.value)
    
    handlers["execute_template"] = execute_template
    
    # Register router
    app_or_router.include_router(router)
    
    return handlers


def register_report_trigger_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    trigger_service: Optional[ReportTriggerService] = None,
) -> Dict[str, Any]:
    """Register API endpoints for report triggers.
    
    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        trigger_service: Optional trigger service to use.
        
    Returns:
        A dictionary of endpoint handlers.
    """
    router = APIRouter(
        prefix=f"{path_prefix}/report-triggers",
        tags=["Report Triggers"],
        dependencies=dependencies or [],
    )
    
    handlers = {}
    
    # Get service from DI container if not provided
    if trigger_service is None:
        from uno.dependencies import get_service
        trigger_service = get_service(ReportTriggerService)
    
    schema_manager = ReportTriggerSchemaManager()
    
    # Create trigger
    @router.post(
        "",
        response_model=ReportTriggerViewDto,
        status_code=201,
        summary="Create a new report trigger",
    )
    async def create_trigger(
        data: ReportTriggerCreateDto = Body(...),
    ) -> ReportTriggerViewDto:
        """Create a new report trigger."""
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data)
        
        # Create entity
        result = await trigger_service.create(entity)
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["create_trigger"] = create_trigger
    
    # Get trigger by ID
    @router.get(
        "/{trigger_id}",
        response_model=ReportTriggerViewDto,
        summary="Get a report trigger by ID",
    )
    async def get_trigger(
        trigger_id: str = Path(..., description="The ID of the trigger"),
    ) -> ReportTriggerViewDto:
        """Get a report trigger by ID."""
        result = await trigger_service.get(trigger_id)
        if result.is_failure:
            raise HTTPException(status_code=404, detail=f"Trigger with ID {trigger_id} not found")
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["get_trigger"] = get_trigger
    
    # List triggers with filtering
    @router.get(
        "",
        response_model=List[ReportTriggerViewDto],
        summary="List report triggers",
    )
    async def list_triggers(
        report_template_id: Optional[str] = Query(None, description="Filter by template ID"),
        trigger_type: Optional[str] = Query(None, description="Filter by trigger type"),
        is_active: Optional[bool] = Query(None, description="Filter by active status"),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> List[ReportTriggerViewDto]:
        """List report triggers with filtering."""
        filters = {}
        
        if report_template_id:
            filters["report_template_id"] = {"lookup": "eq", "val": report_template_id}
        if trigger_type:
            filters["trigger_type"] = {"lookup": "eq", "val": trigger_type}
        if is_active is not None:
            filters["is_active"] = {"lookup": "eq", "val": is_active}
        
        result = await trigger_service.list(filters=filters, skip=skip, limit=limit)
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return schema_manager.entity_list_to_dto_list(result.value)
    
    handlers["list_triggers"] = list_triggers
    
    # Update trigger
    @router.patch(
        "/{trigger_id}",
        response_model=ReportTriggerViewDto,
        summary="Update a report trigger",
    )
    async def update_trigger(
        trigger_id: str = Path(..., description="The ID of the trigger"),
        data: ReportTriggerUpdateDto = Body(...),
    ) -> ReportTriggerViewDto:
        """Update a report trigger."""
        # Get existing entity
        get_result = await trigger_service.get(trigger_id)
        if get_result.is_failure:
            raise HTTPException(status_code=404, detail=f"Trigger with ID {trigger_id} not found")
        
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data, get_result.value)
        
        # Update entity
        update_result = await trigger_service.update(entity)
        if update_result.is_failure:
            raise HTTPException(status_code=400, detail=str(update_result.error))
        
        return schema_manager.entity_to_dto(update_result.value)
    
    handlers["update_trigger"] = update_trigger
    
    # Delete trigger
    @router.delete(
        "/{trigger_id}",
        status_code=204,
        summary="Delete a report trigger",
    )
    async def delete_trigger(
        trigger_id: str = Path(..., description="The ID of the trigger"),
    ) -> None:
        """Delete a report trigger."""
        delete_result = await trigger_service.delete(trigger_id)
        if delete_result.is_failure:
            raise HTTPException(status_code=404, detail=f"Trigger with ID {trigger_id} not found")
    
    handlers["delete_trigger"] = delete_trigger
    
    # Process due triggers
    @router.post(
        "/process-due",
        response_model=Dict[str, Any],
        summary="Process all due scheduled triggers",
    )
    async def process_due_triggers() -> Dict[str, Any]:
        """Process all due scheduled triggers."""
        result = await trigger_service.process_due_triggers()
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return {"processed": result.value}
    
    handlers["process_due_triggers"] = process_due_triggers
    
    # Register router
    app_or_router.include_router(router)
    
    return handlers


def register_report_output_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    output_service: Optional[ReportOutputService] = None,
) -> Dict[str, Any]:
    """Register API endpoints for report outputs.
    
    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        output_service: Optional output service to use.
        
    Returns:
        A dictionary of endpoint handlers.
    """
    router = APIRouter(
        prefix=f"{path_prefix}/report-outputs",
        tags=["Report Outputs"],
        dependencies=dependencies or [],
    )
    
    handlers = {}
    
    # Get service from DI container if not provided
    if output_service is None:
        from uno.dependencies import get_service
        output_service = get_service(ReportOutputService)
    
    schema_manager = ReportOutputSchemaManager()
    
    # Create output
    @router.post(
        "",
        response_model=ReportOutputViewDto,
        status_code=201,
        summary="Create a new report output",
    )
    async def create_output(
        data: ReportOutputCreateDto = Body(...),
    ) -> ReportOutputViewDto:
        """Create a new report output."""
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data)
        
        # Create entity
        result = await output_service.create(entity)
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["create_output"] = create_output
    
    # Get output by ID
    @router.get(
        "/{output_id}",
        response_model=ReportOutputViewDto,
        summary="Get a report output by ID",
    )
    async def get_output(
        output_id: str = Path(..., description="The ID of the output"),
    ) -> ReportOutputViewDto:
        """Get a report output by ID."""
        result = await output_service.get(output_id)
        if result.is_failure:
            raise HTTPException(status_code=404, detail=f"Output with ID {output_id} not found")
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["get_output"] = get_output
    
    # List outputs with filtering
    @router.get(
        "",
        response_model=List[ReportOutputViewDto],
        summary="List report outputs",
    )
    async def list_outputs(
        report_template_id: Optional[str] = Query(None, description="Filter by template ID"),
        output_type: Optional[str] = Query(None, description="Filter by output type"),
        format: Optional[str] = Query(None, description="Filter by format"),
        is_active: Optional[bool] = Query(None, description="Filter by active status"),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> List[ReportOutputViewDto]:
        """List report outputs with filtering."""
        filters = {}
        
        if report_template_id:
            filters["report_template_id"] = {"lookup": "eq", "val": report_template_id}
        if output_type:
            filters["output_type"] = {"lookup": "eq", "val": output_type}
        if format:
            filters["format"] = {"lookup": "eq", "val": format}
        if is_active is not None:
            filters["is_active"] = {"lookup": "eq", "val": is_active}
        
        result = await output_service.list(filters=filters, skip=skip, limit=limit)
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return schema_manager.entity_list_to_dto_list(result.value)
    
    handlers["list_outputs"] = list_outputs
    
    # Update output
    @router.patch(
        "/{output_id}",
        response_model=ReportOutputViewDto,
        summary="Update a report output",
    )
    async def update_output(
        output_id: str = Path(..., description="The ID of the output"),
        data: ReportOutputUpdateDto = Body(...),
    ) -> ReportOutputViewDto:
        """Update a report output."""
        # Get existing entity
        get_result = await output_service.get(output_id)
        if get_result.is_failure:
            raise HTTPException(status_code=404, detail=f"Output with ID {output_id} not found")
        
        # Convert DTO to entity
        entity = schema_manager.dto_to_entity(data, get_result.value)
        
        # Update entity
        update_result = await output_service.update(entity)
        if update_result.is_failure:
            raise HTTPException(status_code=400, detail=str(update_result.error))
        
        return schema_manager.entity_to_dto(update_result.value)
    
    handlers["update_output"] = update_output
    
    # Delete output
    @router.delete(
        "/{output_id}",
        status_code=204,
        summary="Delete a report output",
    )
    async def delete_output(
        output_id: str = Path(..., description="The ID of the output"),
    ) -> None:
        """Delete a report output."""
        delete_result = await output_service.delete(output_id)
        if delete_result.is_failure:
            raise HTTPException(status_code=404, detail=f"Output with ID {output_id} not found")
    
    handlers["delete_output"] = delete_output
    
    # Register router
    app_or_router.include_router(router)
    
    return handlers


def register_report_execution_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    execution_service: Optional[ReportExecutionService] = None,
) -> Dict[str, Any]:
    """Register API endpoints for report executions.
    
    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        execution_service: Optional execution service to use.
        
    Returns:
        A dictionary of endpoint handlers.
    """
    router = APIRouter(
        prefix=f"{path_prefix}/report-executions",
        tags=["Report Executions"],
        dependencies=dependencies or [],
    )
    
    handlers = {}
    
    # Get service from DI container if not provided
    if execution_service is None:
        from uno.dependencies import get_service
        execution_service = get_service(ReportExecutionService)
    
    schema_manager = ReportExecutionSchemaManager()
    
    # Get execution by ID
    @router.get(
        "/{execution_id}",
        response_model=ReportExecutionViewDto,
        summary="Get a report execution by ID",
    )
    async def get_execution(
        execution_id: str = Path(..., description="The ID of the execution"),
    ) -> ReportExecutionViewDto:
        """Get a report execution by ID."""
        result = await execution_service.find_with_output_executions(execution_id)
        if result.is_failure:
            # Try getting without output executions
            simple_result = await execution_service.get(execution_id)
            if simple_result.is_failure:
                raise HTTPException(status_code=404, detail=f"Execution with ID {execution_id} not found")
            return schema_manager.entity_to_dto(simple_result.value)
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["get_execution"] = get_execution
    
    # List executions with filtering
    @router.get(
        "",
        response_model=List[ReportExecutionViewDto],
        summary="List report executions",
    )
    async def list_executions(
        report_template_id: Optional[str] = Query(None, description="Filter by template ID"),
        triggered_by: Optional[str] = Query(None, description="Filter by triggered by"),
        trigger_type: Optional[str] = Query(None, description="Filter by trigger type"),
        status: Optional[str] = Query(None, description="Filter by status"),
        created_after: Optional[datetime] = Query(None, description="Filter by created after date"),
        created_before: Optional[datetime] = Query(None, description="Filter by created before date"),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> List[ReportExecutionViewDto]:
        """List report executions with filtering."""
        filters = {}
        
        if report_template_id:
            filters["report_template_id"] = {"lookup": "eq", "val": report_template_id}
        if triggered_by:
            filters["triggered_by"] = {"lookup": "eq", "val": triggered_by}
        if trigger_type:
            filters["trigger_type"] = {"lookup": "eq", "val": trigger_type}
        if status:
            filters["status"] = {"lookup": "eq", "val": status}
        if created_after:
            filters["started_at"] = {"lookup": "gte", "val": created_after}
        if created_before:
            if "started_at" in filters:
                # Already have a created_after filter, so add a second condition
                filters["started_at"]["lookup"] = "between"
                filters["started_at"]["val"] = [filters["started_at"]["val"], created_before]
            else:
                filters["started_at"] = {"lookup": "lte", "val": created_before}
        
        result = await execution_service.list(filters=filters, skip=skip, limit=limit, order_by="started_at", order_dir="desc")
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        # Load output executions for each execution
        executions_with_outputs = []
        for execution in result.value:
            execution_result = await execution_service.find_with_output_executions(execution.id)
            if execution_result.is_success:
                executions_with_outputs.append(execution_result.value)
            else:
                executions_with_outputs.append(execution)
        
        return schema_manager.entity_list_to_dto_list(executions_with_outputs)
    
    handlers["list_executions"] = list_executions
    
    # Update execution status
    @router.patch(
        "/{execution_id}/status",
        response_model=ReportExecutionViewDto,
        summary="Update a report execution status",
    )
    async def update_execution_status(
        execution_id: str = Path(..., description="The ID of the execution"),
        data: ReportExecutionUpdateStatusDto = Body(...),
    ) -> ReportExecutionViewDto:
        """Update a report execution status."""
        result = await execution_service.update_execution_status(
            execution_id=execution_id,
            status=data.status,
            error_details=data.error_details,
        )
        
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["update_execution_status"] = update_execution_status
    
    # Register router
    app_or_router.include_router(router)
    
    return handlers


def register_report_output_execution_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    output_execution_service: Optional[ReportOutputExecutionService] = None,
) -> Dict[str, Any]:
    """Register API endpoints for report output executions.
    
    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        output_execution_service: Optional output execution service to use.
        
    Returns:
        A dictionary of endpoint handlers.
    """
    router = APIRouter(
        prefix=f"{path_prefix}/report-output-executions",
        tags=["Report Output Executions"],
        dependencies=dependencies or [],
    )
    
    handlers = {}
    
    # Get service from DI container if not provided
    if output_execution_service is None:
        from uno.dependencies import get_service
        output_execution_service = get_service(ReportOutputExecutionService)
    
    schema_manager = ReportOutputExecutionSchemaManager()
    
    # Get output execution by ID
    @router.get(
        "/{output_execution_id}",
        response_model=ReportOutputExecutionViewDto,
        summary="Get a report output execution by ID",
    )
    async def get_output_execution(
        output_execution_id: str = Path(..., description="The ID of the output execution"),
    ) -> ReportOutputExecutionViewDto:
        """Get a report output execution by ID."""
        result = await output_execution_service.get(output_execution_id)
        if result.is_failure:
            raise HTTPException(status_code=404, detail=f"Output execution with ID {output_execution_id} not found")
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["get_output_execution"] = get_output_execution
    
    # List output executions with filtering
    @router.get(
        "",
        response_model=List[ReportOutputExecutionViewDto],
        summary="List report output executions",
    )
    async def list_output_executions(
        report_execution_id: Optional[str] = Query(None, description="Filter by execution ID"),
        report_output_id: Optional[str] = Query(None, description="Filter by output ID"),
        status: Optional[str] = Query(None, description="Filter by status"),
        skip: int = Query(0, description="Number of records to skip"),
        limit: int = Query(100, description="Maximum number of records to return"),
    ) -> List[ReportOutputExecutionViewDto]:
        """List report output executions with filtering."""
        filters = {}
        
        if report_execution_id:
            filters["report_execution_id"] = {"lookup": "eq", "val": report_execution_id}
        if report_output_id:
            filters["report_output_id"] = {"lookup": "eq", "val": report_output_id}
        if status:
            filters["status"] = {"lookup": "eq", "val": status}
        
        result = await output_execution_service.list(filters=filters, skip=skip, limit=limit)
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return schema_manager.entity_list_to_dto_list(result.value)
    
    handlers["list_output_executions"] = list_output_executions
    
    # Update output execution status
    @router.patch(
        "/{output_execution_id}/status",
        response_model=ReportOutputExecutionViewDto,
        summary="Update a report output execution status",
    )
    async def update_output_execution_status(
        output_execution_id: str = Path(..., description="The ID of the output execution"),
        data: ReportOutputExecutionUpdateStatusDto = Body(...),
    ) -> ReportOutputExecutionViewDto:
        """Update a report output execution status."""
        result = await output_execution_service.update_output_execution_status(
            output_execution_id=output_execution_id,
            status=data.status,
            error_details=data.error_details,
        )
        
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return schema_manager.entity_to_dto(result.value)
    
    handlers["update_output_execution_status"] = update_output_execution_status
    
    # Register router
    app_or_router.include_router(router)
    
    return handlers


def register_reports_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """Register all Reports module API endpoints.
    
    Args:
        app_or_router: The FastAPI app or router to register endpoints with.
        path_prefix: The path prefix for the endpoints.
        dependencies: Optional dependencies for the endpoints.
        include_auth: Whether to include authentication dependencies.
        
    Returns:
        A dictionary of all endpoint handlers.
    """
    handlers = {}
    
    # Register field definition endpoints
    handlers["field_definitions"] = register_report_field_definition_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )
    
    # Register template endpoints
    handlers["templates"] = register_report_template_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )
    
    # Register trigger endpoints
    handlers["triggers"] = register_report_trigger_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )
    
    # Register output endpoints
    handlers["outputs"] = register_report_output_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )
    
    # Register execution endpoints
    handlers["executions"] = register_report_execution_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )
    
    # Register output execution endpoints
    handlers["output_executions"] = register_report_output_execution_endpoints(
        app_or_router=app_or_router,
        path_prefix=path_prefix,
        dependencies=dependencies,
        include_auth=include_auth,
    )
    
    return handlers