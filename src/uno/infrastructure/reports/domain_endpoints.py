"""Domain endpoints for the Reports module."""
from typing import Any, Dict, List, Optional, Union, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query
from pydantic import BaseModel, Field

from uno.domain.api_integration import DomainRouter, domain_endpoint
from uno.core.errors.result import Result
from uno.reports.domain_provider import (
    get_report_field_definition_service,
    get_report_template_service,
    get_report_trigger_service,
    get_report_output_service,
    get_report_execution_service,
    get_report_output_execution_service,
)
from uno.reports.domain_services import (
    ReportFieldDefinitionService,
    ReportTemplateService,
    ReportTriggerService,
    ReportOutputService,
    ReportExecutionService,
    ReportOutputExecutionService,
)
from uno.reports.entities import (
    ReportFieldDefinition,
    ReportTemplate,
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


# ========== ReportFieldDefinition Schemas ==========
class ReportFieldDefinitionCreate(BaseModel):
    """Schema for creating a report field definition."""
    name: str = Field(..., description="Internal name of the field")
    display_name: str = Field(..., description="Display name of the field")
    field_type: str = Field(..., description="Type of field (db_column, attribute, method, query, aggregate, etc.)")
    field_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration specific to field_type")
    description: Optional[str] = Field(None, description="Description of the field")
    order: int = Field(0, description="Display order of the field")
    format_string: Optional[str] = Field(None, description="Format string for the field value")
    conditional_formats: Optional[Dict[str, Any]] = Field(None, description="Conditional formatting rules")
    is_visible: bool = Field(True, description="Whether the field is visible in the report")
    parent_field_id: Optional[str] = Field(None, description="Parent field ID for nested fields")


class ReportFieldDefinitionUpdate(BaseModel):
    """Schema for updating a report field definition."""
    name: Optional[str] = Field(None, description="Internal name of the field")
    display_name: Optional[str] = Field(None, description="Display name of the field")
    field_type: Optional[str] = Field(None, description="Type of field (db_column, attribute, method, query, aggregate, etc.)")
    field_config: Optional[Dict[str, Any]] = Field(None, description="Configuration specific to field_type")
    description: Optional[str] = Field(None, description="Description of the field")
    order: Optional[int] = Field(None, description="Display order of the field")
    format_string: Optional[str] = Field(None, description="Format string for the field value")
    conditional_formats: Optional[Dict[str, Any]] = Field(None, description="Conditional formatting rules")
    is_visible: Optional[bool] = Field(None, description="Whether the field is visible in the report")
    parent_field_id: Optional[str] = Field(None, description="Parent field ID for nested fields")


class ReportFieldDefinitionResponse(BaseModel):
    """Schema for a report field definition response."""
    id: str = Field(..., description="The ID of the field definition")
    name: str = Field(..., description="Internal name of the field")
    display_name: str = Field(..., description="Display name of the field")
    field_type: str = Field(..., description="Type of field (db_column, attribute, method, query, aggregate, etc.)")
    field_config: Dict[str, Any] = Field(..., description="Configuration specific to field_type")
    description: Optional[str] = Field(None, description="Description of the field")
    order: int = Field(..., description="Display order of the field")
    format_string: Optional[str] = Field(None, description="Format string for the field value")
    conditional_formats: Optional[Dict[str, Any]] = Field(None, description="Conditional formatting rules")
    is_visible: bool = Field(..., description="Whether the field is visible in the report")
    parent_field_id: Optional[str] = Field(None, description="Parent field ID for nested fields")


# ========== ReportTemplate Schemas ==========
class ReportTemplateCreate(BaseModel):
    """Schema for creating a report template."""
    name: str = Field(..., description="Name of the report template")
    description: str = Field(..., description="Description of the report template")
    base_object_type: str = Field(..., description="What type of entity this report is based on")
    format_config: Dict[str, Any] = Field(default_factory=dict, description="JSON configuration for output format")
    parameter_definitions: Dict[str, Any] = Field(default_factory=dict, description="User parameters the report accepts")
    cache_policy: Dict[str, Any] = Field(default_factory=dict, description="How report results are cached")
    version: str = Field("1.0.0", description="Version of the template")
    field_ids: Optional[List[str]] = Field(None, description="IDs of fields to include in the template")


class ReportTemplateUpdate(BaseModel):
    """Schema for updating a report template."""
    name: Optional[str] = Field(None, description="Name of the report template")
    description: Optional[str] = Field(None, description="Description of the report template")
    base_object_type: Optional[str] = Field(None, description="What type of entity this report is based on")
    format_config: Optional[Dict[str, Any]] = Field(None, description="JSON configuration for output format")
    parameter_definitions: Optional[Dict[str, Any]] = Field(None, description="User parameters the report accepts")
    cache_policy: Optional[Dict[str, Any]] = Field(None, description="How report results are cached")
    version: Optional[str] = Field(None, description="Version of the template")
    field_ids_to_add: Optional[List[str]] = Field(None, description="IDs of fields to add to the template")
    field_ids_to_remove: Optional[List[str]] = Field(None, description="IDs of fields to remove from the template")


class ReportTemplateResponse(BaseModel):
    """Schema for a report template response."""
    id: str = Field(..., description="The ID of the template")
    name: str = Field(..., description="Name of the report template")
    description: str = Field(..., description="Description of the report template")
    base_object_type: str = Field(..., description="What type of entity this report is based on")
    format_config: Dict[str, Any] = Field(..., description="JSON configuration for output format")
    parameter_definitions: Dict[str, Any] = Field(..., description="User parameters the report accepts")
    cache_policy: Dict[str, Any] = Field(..., description="How report results are cached")
    version: str = Field(..., description="Version of the template")
    # We don't include relationships in the response schema for simplicity
    # In a real implementation, you might include them or provide separate endpoints


# ========== ReportTrigger Schemas ==========
class ReportTriggerCreate(BaseModel):
    """Schema for creating a report trigger."""
    report_template_id: str = Field(..., description="The ID of the template this trigger belongs to")
    trigger_type: str = Field(..., description="Type of trigger (manual, scheduled, event, query)")
    trigger_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration specific to trigger_type")
    schedule: Optional[str] = Field(None, description="Cron-style schedule expression")
    event_type: Optional[str] = Field(None, description="Type of event that triggers the report")
    entity_type: Optional[str] = Field(None, description="Type of entity involved in the event")
    query_id: Optional[str] = Field(None, description="ID of the query that triggers the report")
    is_active: bool = Field(True, description="Whether this trigger is active")


class ReportTriggerUpdate(BaseModel):
    """Schema for updating a report trigger."""
    trigger_type: Optional[str] = Field(None, description="Type of trigger (manual, scheduled, event, query)")
    trigger_config: Optional[Dict[str, Any]] = Field(None, description="Configuration specific to trigger_type")
    schedule: Optional[str] = Field(None, description="Cron-style schedule expression")
    event_type: Optional[str] = Field(None, description="Type of event that triggers the report")
    entity_type: Optional[str] = Field(None, description="Type of entity involved in the event")
    query_id: Optional[str] = Field(None, description="ID of the query that triggers the report")
    is_active: Optional[bool] = Field(None, description="Whether this trigger is active")


class ReportTriggerResponse(BaseModel):
    """Schema for a report trigger response."""
    id: str = Field(..., description="The ID of the trigger")
    report_template_id: str = Field(..., description="The ID of the template this trigger belongs to")
    trigger_type: str = Field(..., description="Type of trigger (manual, scheduled, event, query)")
    trigger_config: Dict[str, Any] = Field(..., description="Configuration specific to trigger_type")
    schedule: Optional[str] = Field(None, description="Cron-style schedule expression")
    event_type: Optional[str] = Field(None, description="Type of event that triggers the report")
    entity_type: Optional[str] = Field(None, description="Type of entity involved in the event")
    query_id: Optional[str] = Field(None, description="ID of the query that triggers the report")
    is_active: bool = Field(..., description="Whether this trigger is active")
    last_triggered: Optional[str] = Field(None, description="When this trigger was last activated")


# ========== ReportOutput Schemas ==========
class ReportOutputCreate(BaseModel):
    """Schema for creating a report output."""
    report_template_id: str = Field(..., description="The ID of the template this output belongs to")
    output_type: str = Field(..., description="Type of output (file, email, webhook, notification)")
    format: str = Field(..., description="Format of the output (csv, pdf, json, html, excel, text)")
    output_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration specific to output_type")
    format_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration specific to format")
    is_active: bool = Field(True, description="Whether this output is active")


class ReportOutputUpdate(BaseModel):
    """Schema for updating a report output."""
    output_type: Optional[str] = Field(None, description="Type of output (file, email, webhook, notification)")
    format: Optional[str] = Field(None, description="Format of the output (csv, pdf, json, html, excel, text)")
    output_config: Optional[Dict[str, Any]] = Field(None, description="Configuration specific to output_type")
    format_config: Optional[Dict[str, Any]] = Field(None, description="Configuration specific to format")
    is_active: Optional[bool] = Field(None, description="Whether this output is active")


class ReportOutputResponse(BaseModel):
    """Schema for a report output response."""
    id: str = Field(..., description="The ID of the output")
    report_template_id: str = Field(..., description="The ID of the template this output belongs to")
    output_type: str = Field(..., description="Type of output (file, email, webhook, notification)")
    format: str = Field(..., description="Format of the output (csv, pdf, json, html, excel, text)")
    output_config: Dict[str, Any] = Field(..., description="Configuration specific to output_type")
    format_config: Dict[str, Any] = Field(..., description="Configuration specific to format")
    is_active: bool = Field(..., description="Whether this output is active")


# ========== ReportExecution Schemas ==========
class ReportExecutionCreate(BaseModel):
    """Schema for creating a report execution."""
    report_template_id: str = Field(..., description="The ID of the template being executed")
    triggered_by: str = Field(..., description="ID of trigger or user that initiated execution")
    trigger_type: str = Field(..., description="Type of trigger that initiated execution")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters provided for this execution")


class ReportExecutionUpdateStatus(BaseModel):
    """Schema for updating a report execution status."""
    status: str = Field(..., description="New status for the execution")
    error_details: Optional[str] = Field(None, description="Error details if status is 'failed'")


class ReportExecutionResponse(BaseModel):
    """Schema for a report execution response."""
    id: str = Field(..., description="The ID of the execution")
    report_template_id: str = Field(..., description="The ID of the template being executed")
    triggered_by: str = Field(..., description="ID of trigger or user that initiated execution")
    trigger_type: str = Field(..., description="Type of trigger that initiated execution")
    parameters: Dict[str, Any] = Field(..., description="Parameters provided for this execution")
    status: str = Field(..., description="Status of the execution")
    started_at: str = Field(..., description="When execution started")
    completed_at: Optional[str] = Field(None, description="When execution completed")
    error_details: Optional[str] = Field(None, description="Error details if execution failed")
    row_count: Optional[int] = Field(None, description="Number of rows in the result")
    execution_time_ms: Optional[int] = Field(None, description="Execution time in milliseconds")
    result_hash: Optional[str] = Field(None, description="Hash of the result data for caching")


# ========== ReportOutputExecution Schemas ==========
class ReportOutputExecutionCreateParams(BaseModel):
    """Parameters for creating a report output execution."""
    report_output_id: str = Field(..., description="The ID of the output configuration used")


class ReportOutputExecutionUpdateStatus(BaseModel):
    """Schema for updating a report output execution status."""
    status: str = Field(..., description="New status for the output execution")
    error_details: Optional[str] = Field(None, description="Error details if status is 'failed'")
    output_location: Optional[str] = Field(None, description="Location of the output (URL, file path, etc.)")
    output_size_bytes: Optional[int] = Field(None, description="Size of the output in bytes")


class ReportOutputExecutionResponse(BaseModel):
    """Schema for a report output execution response."""
    id: str = Field(..., description="The ID of the output execution")
    report_execution_id: str = Field(..., description="The ID of the execution this output is for")
    report_output_id: str = Field(..., description="The ID of the output configuration used")
    status: str = Field(..., description="Status of the output delivery")
    completed_at: Optional[str] = Field(None, description="When output delivery completed")
    error_details: Optional[str] = Field(None, description="Error details if output delivery failed")
    output_location: Optional[str] = Field(None, description="Location of the output (URL, file path, etc.)")
    output_size_bytes: Optional[int] = Field(None, description="Size of the output in bytes")


# ========== ReportExecution Result Schema ==========
class ReportExecutionResultResponse(BaseModel):
    """Schema for a report execution result response."""
    execution_id: str = Field(..., description="The ID of the execution")
    template_id: str = Field(..., description="The ID of the template")
    template_name: str = Field(..., description="The name of the template")
    status: str = Field(..., description="Status of the execution")
    outputs: List[Dict[str, Any]] = Field(..., description="Output delivery records")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="Report data if available")


# ========== Create Routers ==========
field_definition_router = DomainRouter[ReportFieldDefinition, ReportFieldDefinitionService](
    entity_type=ReportFieldDefinition,
    service_type=ReportFieldDefinitionService,
    prefix="/report-field-definitions",
    tags=["Report Field Definitions"],
    create_dto=ReportFieldDefinitionCreate,
    update_dto=ReportFieldDefinitionUpdate,
    response_dto=ReportFieldDefinitionResponse,
)

template_router = DomainRouter[ReportTemplate, ReportTemplateService](
    entity_type=ReportTemplate,
    service_type=ReportTemplateService,
    prefix="/report-templates",
    tags=["Report Templates"],
    create_dto=ReportTemplateCreate,
    update_dto=ReportTemplateUpdate,
    response_dto=ReportTemplateResponse,
)

trigger_router = DomainRouter[ReportTrigger, ReportTriggerService](
    entity_type=ReportTrigger,
    service_type=ReportTriggerService,
    prefix="/report-triggers",
    tags=["Report Triggers"],
    create_dto=ReportTriggerCreate,
    update_dto=ReportTriggerUpdate,
    response_dto=ReportTriggerResponse,
)

output_router = DomainRouter[ReportOutput, ReportOutputService](
    entity_type=ReportOutput,
    service_type=ReportOutputService,
    prefix="/report-outputs",
    tags=["Report Outputs"],
    create_dto=ReportOutputCreate,
    update_dto=ReportOutputUpdate,
    response_dto=ReportOutputResponse,
)

execution_router = DomainRouter[ReportExecution, ReportExecutionService](
    entity_type=ReportExecution,
    service_type=ReportExecutionService,
    prefix="/report-executions",
    tags=["Report Executions"],
    create_dto=ReportExecutionCreate,
    update_dto=ReportExecutionUpdateStatus,
    response_dto=ReportExecutionResponse,
)

output_execution_router = APIRouter(
    prefix="/report-output-executions",
    tags=["Report Output Executions"],
)


# ========== Custom Endpoints ==========

# ----- Field Definition Endpoints -----
@field_definition_router.router.get("/by-template/{template_id}", response_model=List[ReportFieldDefinitionResponse])
@domain_endpoint(entity_type=ReportFieldDefinition, service_type=ReportFieldDefinitionService)
async def find_fields_by_template(
    template_id: str = Path(..., description="The ID of the template"),
    service: ReportFieldDefinitionService = Depends(get_report_field_definition_service),
):
    """Find field definitions by template ID."""
    result = await service.find_by_template_id(template_id)
    return result.value


# ----- Template Endpoints -----
@template_router.router.get("/by-object-type/{object_type}", response_model=List[ReportTemplateResponse])
@domain_endpoint(entity_type=ReportTemplate, service_type=ReportTemplateService)
async def find_templates_by_object_type(
    object_type: str = Path(..., description="The object type to search for"),
    service: ReportTemplateService = Depends(get_report_template_service),
):
    """Find templates by object type."""
    result = await service.find_by_base_object_type(object_type)
    return result.value


@template_router.router.get("/{template_id}/with-relationships", response_model=ReportTemplateResponse)
@domain_endpoint(entity_type=ReportTemplate, service_type=ReportTemplateService)
async def get_template_with_relationships(
    template_id: str = Path(..., description="The ID of the template"),
    service: ReportTemplateService = Depends(get_report_template_service),
):
    """Get a template with all relationships loaded."""
    result = await service.get_with_relationships(template_id)
    return result.value


@template_router.router.post("/{template_id}/execute", response_model=ReportExecutionResponse)
@domain_endpoint(entity_type=ReportTemplate, service_type=ReportTemplateService)
async def execute_template(
    template_id: str = Path(..., description="The ID of the template to execute"),
    parameters: Dict[str, Any] = Body(default_factory=dict),
    service: ReportTemplateService = Depends(get_report_template_service),
):
    """Execute a report template."""
    result = await service.execute_template(
        template_id=template_id,
        triggered_by="api",
        trigger_type=ReportTriggerType.MANUAL,
        parameters=parameters,
    )
    return result.value


@template_router.router.patch(
    "/{template_id}/fields",
    response_model=ReportTemplateResponse,
)
@domain_endpoint(entity_type=ReportTemplate, service_type=ReportTemplateService)
async def update_template_fields(
    template_id: str = Path(..., description="The ID of the template"),
    field_update: ReportTemplateUpdate = Body(...),
    service: ReportTemplateService = Depends(get_report_template_service),
):
    """Update the fields associated with a template."""
    result = await service.update_fields(
        template_id=template_id,
        field_ids_to_add=field_update.field_ids_to_add,
        field_ids_to_remove=field_update.field_ids_to_remove,
    )
    return result.value


# ----- Trigger Endpoints -----
@trigger_router.router.get("/active", response_model=List[ReportTriggerResponse])
@domain_endpoint(entity_type=ReportTrigger, service_type=ReportTriggerService)
async def find_active_triggers(
    service: ReportTriggerService = Depends(get_report_trigger_service),
):
    """Find all active triggers."""
    result = await service.find_active_triggers()
    return result.value


@trigger_router.router.get("/scheduled", response_model=List[ReportTriggerResponse])
@domain_endpoint(entity_type=ReportTrigger, service_type=ReportTriggerService)
async def find_active_scheduled_triggers(
    service: ReportTriggerService = Depends(get_report_trigger_service),
):
    """Find active scheduled triggers."""
    result = await service.find_active_scheduled_triggers()
    return result.value


@trigger_router.router.post("/process-due", response_model=Dict[str, Any])
@domain_endpoint(entity_type=ReportTrigger, service_type=ReportTriggerService)
async def process_due_triggers(
    service: ReportTriggerService = Depends(get_report_trigger_service),
):
    """Process all due scheduled triggers."""
    result = await service.process_due_triggers()
    return {"processed_count": result.value}


# ----- Execution Endpoints -----
@execution_router.router.get("/recent", response_model=List[ReportExecutionResponse])
@domain_endpoint(entity_type=ReportExecution, service_type=ReportExecutionService)
async def find_recent_executions(
    limit: int = Query(10, description="Maximum number of executions to return"),
    service: ReportExecutionService = Depends(get_report_execution_service),
):
    """Find recent executions."""
    result = await service.find_recent_executions(limit)
    return result.value


@execution_router.router.get("/{execution_id}/with-outputs", response_model=ReportExecutionResponse)
@domain_endpoint(entity_type=ReportExecution, service_type=ReportExecutionService)
async def find_execution_with_outputs(
    execution_id: str = Path(..., description="The ID of the execution"),
    service: ReportExecutionService = Depends(get_report_execution_service),
):
    """Find an execution with output executions loaded."""
    result = await service.find_with_output_executions(execution_id)
    return result.value


@execution_router.router.patch("/{execution_id}/status", response_model=ReportExecutionResponse)
@domain_endpoint(entity_type=ReportExecution, service_type=ReportExecutionService)
async def update_execution_status(
    execution_id: str = Path(..., description="The ID of the execution"),
    status_update: ReportExecutionUpdateStatus = Body(...),
    service: ReportExecutionService = Depends(get_report_execution_service),
):
    """Update the status of an execution."""
    result = await service.update_execution_status(
        execution_id=execution_id,
        status=status_update.status,
        error_details=status_update.error_details,
    )
    return result.value


# ----- Output Execution Endpoints -----
@output_execution_router.get("/{output_execution_id}", response_model=ReportOutputExecutionResponse)
async def get_output_execution(
    output_execution_id: str = Path(..., description="The ID of the output execution"),
    service: ReportOutputExecutionService = Depends(FromDI(ReportOutputExecutionService)),
):
    """Get an output execution by ID."""
    result = await service.get(output_execution_id)
    if result.is_failure:
        raise HTTPException(status_code=404, detail=str(result.error))
    return result.value


@output_execution_router.get("/by-execution/{execution_id}", response_model=List[ReportOutputExecutionResponse])
async def find_output_executions_by_execution(
    execution_id: str = Path(..., description="The ID of the execution"),
    service: ReportOutputExecutionService = Depends(FromDI(ReportOutputExecutionService)),
):
    """Find output executions by execution ID."""
    result = await service.find_by_execution_id(execution_id)
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    return result.value


@output_execution_router.patch("/{output_execution_id}/status", response_model=ReportOutputExecutionResponse)
async def update_output_execution_status(
    output_execution_id: str = Path(..., description="The ID of the output execution"),
    status_update: ReportOutputExecutionUpdateStatus = Body(...),
    service: ReportOutputExecutionService = Depends(FromDI(ReportOutputExecutionService)),
):
    """Update the status of an output execution."""
    result = await service.update_output_execution_status(
        output_execution_id=output_execution_id,
        status=status_update.status,
        error_details=status_update.error_details,
    )
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    return result.value