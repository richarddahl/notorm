# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API endpoints for the reports module.

This module provides FastAPI endpoints for interacting with the reports module,
building upon the service layer implementations.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Query,
    Path,
    Body,
    status,
    FastAPI,
)
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from uno.api.endpoint import UnoEndpoint, ListRouter
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.reports.domain_endpoints import ReportTemplateCreate
from uno.dependencies.database import get_db_session


# Helper function to replace inject_dependency
def inject_dependency(interface_type):
    def _inject(request):
        from uno.dependencies.modern_provider import get_service_provider

        provider = get_service_provider()
        return provider.get_service(interface_type)

    return _inject


from uno.core.errors.result import Result
from uno.reports.interfaces import (
    ReportTemplateServiceProtocol,
    ReportFieldServiceProtocol,
    ReportExecutionServiceProtocol,
    ReportTriggerServiceProtocol,
    ReportOutputServiceProtocol,
)
from uno.reports.services import (
    ReportTemplateService,
    ReportFieldService,
    ReportExecutionService,
    ReportTriggerService,
    ReportOutputService,
)
from uno.reports.repositories import ReportError
from uno.reports.repositories import (
    ReportTemplateRepository,
    ReportFieldDefinitionRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
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


# Create router
router = APIRouter(
    prefix="/reports", tags=["reports"], responses={404: {"description": "Not found"}}
)


# Schema classes for request/response payloads
class Rejson_schema_extrCreate(BaseModel):
    name: str
    description: str
    base_object_type: str
    format_config: Dict[str, Any] = {}
    parameter_definitions: Dict[str, Any] = {}
    cache_policy: Dict[str, Any] = {}
    version: str = "1.0.0"
    fields: List[Dict[str, Any]] = []

    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
                "name": "Customer Report",
                "description": "Report showing customer information",
                "base_object_type": "customer",
                "format_config": {
                    "title_format": "{name} - Generated on {date}",
                    "show_footer": True,
                },
                "parameter_definitions": {
                    "start_date": {
                        "type": "date",
                        "required": True,
                        "default": "today-30d",
                    },
                    "customer_type": {
                        "type": "string",
                        "required": False,
                        "choices": ["individual", "business", "government"],
                    },
                },
                "fields": [
                    {
                        "name": "customer_id",
                        "display_name": "Customer ID",
                        "field_type": "db_column",
                        "field_config": {"table": "customer", "column": "id"},
                        "order": 1,
                    },
                    {
                        "name": "name",
                        "display_name": "Customer Name",
                        "field_type": "db_column",
                        "field_config": {"table": "customer", "column": "name"},
                        "order": 2,
                    },
                ],
            }
        }


class ReportTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    format_config: Optional[Dict[str, Any]] = None
    parameter_definitions: Optional[Dict[str, Any]] = None
    cache_policy: Optional[Dict[str, Any]] = None
    version: Optional[str] = None

    class Config:
        extra = "allow"


class ReportFieldCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    field_type: str
    field_config: Dict[str, Any]
    order: int = 0
    format_string: Optional[str] = None
    conditional_formats: Optional[Dict[str, Any]] = None
    is_visible: bool = True
    parent_field_id: Optional[str] = None

    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
                "name": "total_value",
                "display_name": "Total Value",
                "description": "Sum of all order values",
                "field_type": "aggregate",
                "field_config": {"function": "sum", "field": "value"},
                "order": 5,
                "format_string": "${value:,.2f}",
                "conditional_formats": {
                    "highlight": {
                        "condition": "value > 1000",
                        "style": "background-color: #ffeeee",
                    }
                },
            }
        }


class ReportFieldUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    field_type: Optional[str] = None
    field_config: Optional[Dict[str, Any]] = None
    order: Optional[int] = None
    format_string: Optional[str] = None
    conditional_formats: Optional[Dict[str, Any]] = None
    is_visible: Optional[bool] = None
    parent_field_id: Optional[str] = None

    class Config:
        extra = "allow"


class ReportTriggerCreate(BaseModel):
    trigger_type: str
    trigger_config: Dict[str, Any] = {}
    schedule: Optional[str] = None
    event_type: Optional[str] = None
    entity_type: Optional[str] = None
    query_id: Optional[str] = None
    is_active: bool = True

    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
                "trigger_type": "scheduled",
                "schedule": "interval:24:hours",
                "trigger_config": {"run_on_holidays": False, "timezone": "UTC"},
                "is_active": True,
            }
        }


class ReportTriggerUpdate(BaseModel):
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    schedule: Optional[str] = None
    event_type: Optional[str] = None
    entity_type: Optional[str] = None
    query_id: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        extra = "allow"


class ReportOutputCreate(BaseModel):
    output_type: str
    output_config: Dict[str, Any] = {}
    format: str
    format_config: Dict[str, Any] = {}
    is_active: bool = True

    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
                "output_type": "email",
                "output_config": {
                    "recipients": ["user@example.com"],
                    "subject": "Monthly Sales Report",
                    "body": "Please find the attached monthly sales report.",
                },
                "format": "pdf",
                "format_config": {
                    "page_size": "letter",
                    "orientation": "portrait",
                    "include_header": True,
                },
                "is_active": True,
            }
        }


class ReportOutputUpdate(BaseModel):
    output_type: Optional[str] = None
    output_config: Optional[Dict[str, Any]] = None
    format: Optional[str] = None
    format_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    class Config:
        extra = "allow"


class ReportExecuteRequest(BaseModel):
    parameters: Dict[str, Any] = {}
    user_id: Optional[str] = None

    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
                "parameters": {
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "customer_type": "business",
                },
                "user_id": "user123",
            }
        }


class EventData(BaseModel):
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    data: Dict[str, Any] = {}

    class Config:
        extra = "allow"
        json_schema_extra = {
            "example": {
                "event_type": "order_created",
                "entity_type": "order",
                "entity_id": "order123",
                "data": {
                    "order_id": "order123",
                    "customer_id": "cust456",
                    "amount": 1250.50,
                    "status": "pending",
                },
            }
        }


# Helper functions for converting between Result and HTTP responses
def handle_result(
    result: Result[Any], not_found_message: str = "Item not found"
) -> Any:
    """Convert a Result to an HTTP response or raise an HTTPException."""
    if result.is_failure:
        error = result.error
        if hasattr(error, "error_code"):
            status_code = error.error_code.value
            # Map common error codes to HTTP status codes
            if error.error_code.name == "NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
                )
            elif error.error_code.name == "VALIDATION_ERROR":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
            )

    if result.value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=not_found_message
        )

    return result.value


# Dependency functions for services
async def get_template_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReportTemplateService:
    """Get the report template service."""
    template_repo = ReportTemplateRepository(session)
    field_repo = ReportFieldDefinitionRepository(session)
    return ReportTemplateService(session, template_repo, field_repo)


async def get_field_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReportFieldService:
    """Get the report field service."""
    template_repo = ReportTemplateRepository(session)
    field_repo = ReportFieldDefinitionRepository(session)
    return ReportFieldService(session, template_repo, field_repo)


async def get_execution_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReportExecutionService:
    """Get the report execution service."""
    template_repo = ReportTemplateRepository(session)
    field_repo = ReportFieldDefinitionRepository(session)
    execution_repo = ReportExecutionRepository(session)
    output_execution_repo = ReportOutputExecutionRepository(session)
    output_repo = ReportOutputRepository(session)
    return ReportExecutionService(
        session,
        template_repo,
        field_repo,
        execution_repo,
        output_execution_repo,
        output_repo,
    )


async def get_trigger_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReportTriggerService:
    """Get the report trigger service."""
    template_repo = ReportTemplateRepository(session)
    trigger_repo = ReportTriggerRepository(session)
    # Get the execution service
    execution_service = await get_execution_service(session)
    return ReportTriggerService(session, template_repo, trigger_repo, execution_service)


async def get_output_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReportOutputService:
    """Get the report output service."""
    template_repo = ReportTemplateRepository(session)
    field_repo = ReportFieldDefinitionRepository(session)
    output_repo = ReportOutputRepository(session)
    execution_repo = ReportExecutionRepository(session)
    output_execution_repo = ReportOutputExecutionRepository(session)
    return ReportOutputService(
        session,
        template_repo,
        output_repo,
        execution_repo,
        output_execution_repo,
        field_repository=field_repo,
    )


async def get_execution_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReportExecutionService:
    """Get the report execution service."""
    template_repo = ReportTemplateRepository(session)
    field_repo = ReportFieldDefinitionRepository(session)
    execution_repo = ReportExecutionRepository(session)
    output_execution_repo = ReportOutputExecutionRepository(session)
    output_repo = ReportOutputRepository(session)
    return ReportExecutionService(
        session,
        template_repo,
        field_repo,
        execution_repo,
        output_execution_repo,
        output_repo,
    )


# Template endpoints
@router.get("/templates/", response_model=List[dict])
async def list_templates(
    name: Optional[str] = None,
    base_object_type: Optional[str] = None,
    service: ReportTemplateService = Depends(get_template_service),
):
    """List report templates, optionally filtered by name or object type."""
    filters = {}
    if name:
        filters["name"] = name
    if base_object_type:
        filters["base_object_type"] = base_object_type

    result = await service.list_templates(filters)
    templates = handle_result(result)

    # Convert to dictionaries for response
    return [template.model_dump() for template in templates]


@router.get("/templates/{template_id}", response_model=dict)
async def get_template(
    template_id: str = Path(..., description="The ID of the template to retrieve"),
    service: ReportTemplateService = Depends(get_template_service),
):
    """Get a report template by ID."""
    result = await service.get_template(template_id)
    template = handle_result(result, f"Template with ID {template_id} not found")

    return template.model_dump()


@router.post("/templates/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: ReportTemplateCreate,
    service: ReportTemplateService = Depends(get_template_service),
):
    """Create a new report template."""
    result = await service.create_template(template_data.dict())
    template = handle_result(result)

    return template.model_dump()


@router.put("/templates/{template_id}", response_model=dict)
async def update_template(
    template_data: ReportTemplateUpdate,
    template_id: str = Path(..., description="The ID of the template to update"),
    service: ReportTemplateService = Depends(get_template_service),
):
    """Update an existing report template."""
    result = await service.update_template(
        template_id, template_data.dict(exclude_unset=True)
    )
    template = handle_result(result, f"Template with ID {template_id} not found")

    return template.model_dump()


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str = Path(..., description="The ID of the template to delete"),
    service: ReportTemplateService = Depends(get_template_service),
):
    """Delete a report template."""
    result = await service.delete_template(template_id)
    handle_result(result, f"Template with ID {template_id} not found")

    return None


@router.post(
    "/templates/{template_id}/clone",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def clone_template(
    new_name: str = Body(..., embed=True),
    template_id: str = Path(..., description="The ID of the template to clone"),
    service: ReportTemplateService = Depends(get_template_service),
):
    """Clone an existing template with a new name."""
    result = await service.clone_template(template_id, new_name)
    template = handle_result(result, f"Template with ID {template_id} not found")

    return template.model_dump()


# Field endpoints
@router.get("/templates/{template_id}/fields", response_model=List[dict])
async def list_fields(
    template_id: str = Path(..., description="The ID of the template"),
    service: ReportFieldService = Depends(get_field_service),
):
    """List fields for a template."""
    result = await service.list_fields_by_template(template_id)
    fields = handle_result(result, f"Template with ID {template_id} not found")

    return [field.model_dump() for field in fields]


@router.get("/fields/{field_id}", response_model=dict)
async def get_field(
    field_id: str = Path(..., description="The ID of the field to retrieve"),
    service: ReportFieldService = Depends(get_field_service),
):
    """Get a field by ID."""
    result = await service.get_field_by_id(field_id)
    field = handle_result(result, f"Field with ID {field_id} not found")

    return field.model_dump()


@router.post(
    "/templates/{template_id}/fields",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_field(
    field_data: ReportFieldCreate,
    template_id: str = Path(..., description="The ID of the template"),
    service: ReportFieldService = Depends(get_field_service),
):
    """Add a field to a template."""
    result = await service.add_field(template_id, field_data.dict())
    field = handle_result(result)

    return field.model_dump()


@router.put("/fields/{field_id}", response_model=dict)
async def update_field(
    field_data: ReportFieldUpdate,
    field_id: str = Path(..., description="The ID of the field to update"),
    service: ReportFieldService = Depends(get_field_service),
):
    """Update a field."""
    result = await service.update_field(field_id, field_data.dict(exclude_unset=True))
    field = handle_result(result, f"Field with ID {field_id} not found")

    return field.model_dump()


@router.delete("/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(
    field_id: str = Path(..., description="The ID of the field to delete"),
    service: ReportFieldService = Depends(get_field_service),
):
    """Delete a field."""
    result = await service.delete_field(field_id)
    handle_result(result, f"Field with ID {field_id} not found")

    return None


@router.get("/available-fields/{object_type}", response_model=List[dict])
async def get_available_fields(
    object_type: str = Path(
        ..., description="The object type to get available fields for"
    ),
    service: ReportFieldService = Depends(get_field_service),
):
    """Get available fields for an object type."""
    result = await service.get_available_fields(object_type)
    fields = handle_result(result)

    return fields


# Trigger endpoints
@router.get("/templates/{template_id}/triggers", response_model=List[dict])
async def list_triggers(
    template_id: str = Path(..., description="The ID of the template"),
    service: ReportTriggerService = Depends(get_trigger_service),
):
    """List triggers for a template."""
    result = await service.list_triggers_by_template(template_id)
    triggers = handle_result(result, f"Template with ID {template_id} not found")

    return [trigger.model_dump() for trigger in triggers]


@router.post(
    "/templates/{template_id}/triggers",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_trigger(
    trigger_data: ReportTriggerCreate,
    template_id: str = Path(..., description="The ID of the template"),
    service: ReportTriggerService = Depends(get_trigger_service),
):
    """Create a trigger for a template."""
    result = await service.create_trigger(template_id, trigger_data.dict())
    trigger = handle_result(result)

    return trigger.model_dump()


@router.put("/triggers/{trigger_id}", response_model=dict)
async def update_trigger(
    trigger_data: ReportTriggerUpdate,
    trigger_id: str = Path(..., description="The ID of the trigger to update"),
    service: ReportTriggerService = Depends(get_trigger_service),
):
    """Update a trigger."""
    result = await service.update_trigger(
        trigger_id, trigger_data.dict(exclude_unset=True)
    )
    trigger = handle_result(result, f"Trigger with ID {trigger_id} not found")

    return trigger.model_dump()


@router.delete("/triggers/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trigger(
    trigger_id: str = Path(..., description="The ID of the trigger to delete"),
    service: ReportTriggerService = Depends(get_trigger_service),
):
    """Delete a trigger."""
    result = await service.delete_trigger(trigger_id)
    handle_result(result, f"Trigger with ID {trigger_id} not found")

    return None


@router.post("/triggers/{trigger_id}/enable", response_model=dict)
async def enable_trigger(
    trigger_id: str = Path(..., description="The ID of the trigger to enable"),
    service: ReportTriggerService = Depends(get_trigger_service),
):
    """Enable a trigger."""
    result = await service.enable_trigger(trigger_id)
    handle_result(result, f"Trigger with ID {trigger_id} not found")

    return {"id": trigger_id, "is_active": True}


@router.post("/triggers/{trigger_id}/disable", response_model=dict)
async def disable_trigger(
    trigger_id: str = Path(..., description="The ID of the trigger to disable"),
    service: ReportTriggerService = Depends(get_trigger_service),
):
    """Disable a trigger."""
    result = await service.disable_trigger(trigger_id)
    handle_result(result, f"Trigger with ID {trigger_id} not found")

    return {"id": trigger_id, "is_active": False}


@router.post("/events", response_model=dict)
async def handle_event(
    event_data: EventData, service: ReportTriggerService = Depends(get_trigger_service)
):
    """Handle an event that might trigger reports."""
    result = await service.handle_event(event_data.event_type, event_data.dict())
    execution_ids = handle_result(result)

    return {
        "event_type": event_data.event_type,
        "execution_count": len(execution_ids),
        "executions": execution_ids,
    }


# Output endpoints
@router.get("/templates/{template_id}/outputs", response_model=List[dict])
async def list_outputs(
    template_id: str = Path(..., description="The ID of the template"),
    service: ReportOutputService = Depends(get_output_service),
):
    """List outputs for a template."""
    result = await service.list_outputs_by_template(template_id)
    outputs = handle_result(result, f"Template with ID {template_id} not found")

    return [output.model_dump() for output in outputs]


@router.post(
    "/templates/{template_id}/outputs",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_output(
    output_data: ReportOutputCreate,
    template_id: str = Path(..., description="The ID of the template"),
    service: ReportOutputService = Depends(get_output_service),
):
    """Create an output configuration for a template."""
    result = await service.create_output_config(template_id, output_data.dict())
    output = handle_result(result)

    return output.model_dump()


@router.put("/outputs/{output_id}", response_model=dict)
async def update_output(
    output_data: ReportOutputUpdate,
    output_id: str = Path(..., description="The ID of the output to update"),
    service: ReportOutputService = Depends(get_output_service),
):
    """Update an output configuration."""
    result = await service.update_output_config(
        output_id, output_data.dict(exclude_unset=True)
    )
    output = handle_result(result, f"Output with ID {output_id} not found")

    return output.model_dump()


@router.delete("/outputs/{output_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_output(
    output_id: str = Path(..., description="The ID of the output to delete"),
    service: ReportOutputService = Depends(get_output_service),
):
    """Delete an output configuration."""
    result = await service.delete_output_config(output_id)
    handle_result(result, f"Output with ID {output_id} not found")

    return None


# Execution endpoints
@router.post("/templates/{template_id}/execute", response_model=dict)
async def execute_report(
    execute_request: ReportExecuteRequest,
    template_id: str = Path(..., description="The ID of the template to execute"),
    service: ReportExecutionService = Depends(get_execution_service),
):
    """Execute a report template."""
    result = await service.execute_report(
        template_id,
        execute_request.parameters,
        trigger_type="manual",
        user_id=execute_request.user_id,
    )
    execution = handle_result(result)

    return {
        "execution_id": execution.id,
        "status": execution.status,
        "started_at": execution.started_at,
        "message": "Report execution started",
    }


@router.get("/executions/{execution_id}", response_model=dict)
async def get_execution_status(
    execution_id: str = Path(..., description="The ID of the execution"),
    service: ReportExecutionService = Depends(get_execution_service),
):
    """Get the status of a report execution."""
    result = await service.get_execution_status(execution_id)
    status_info = handle_result(result, f"Execution with ID {execution_id} not found")

    return status_info


@router.get("/executions/{execution_id}/result", response_model=Dict[str, Any])
async def get_execution_result(
    execution_id: str = Path(..., description="The ID of the execution"),
    format: Optional[str] = Query(
        None, description="Optional format to return the result in"
    ),
    service: ReportExecutionService = Depends(get_execution_service),
):
    """Get the result of a completed report execution."""
    result = await service.get_execution_result(execution_id, format)
    return handle_result(result, f"Execution with ID {execution_id} not found")


@router.post("/executions/{execution_id}/cancel", response_model=dict)
async def cancel_execution(
    execution_id: str = Path(..., description="The ID of the execution to cancel"),
    service: ReportExecutionService = Depends(get_execution_service),
):
    """Cancel a running report execution."""
    result = await service.cancel_execution(execution_id)
    handle_result(result, f"Execution with ID {execution_id} not found")

    return {
        "execution_id": execution_id,
        "status": "cancelled",
        "message": "Execution cancelled successfully",
    }


@router.post(
    "/executions/{execution_id}/outputs/{output_id}/deliver", response_model=dict
)
async def deliver_report(
    execution_id: str = Path(..., description="The ID of the execution"),
    output_id: str = Path(..., description="The ID of the output configuration"),
    service: ReportOutputService = Depends(get_output_service),
):
    """Deliver a report according to an output configuration."""
    result = await service.deliver_report(execution_id, output_id)
    handle_result(result)

    return {
        "execution_id": execution_id,
        "output_id": output_id,
        "status": "delivered",
        "message": "Report delivered successfully",
    }


@router.get("/templates/{template_id}/executions", response_model=List[dict])
async def list_executions(
    template_id: str = Path(..., description="The ID of the template"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of executions to return"),
    service: ReportExecutionService = Depends(get_execution_service),
):
    """List executions for a template."""
    result = await service.list_executions(template_id, status, limit=limit)
    executions = handle_result(result)

    return [execution.model_dump() for execution in executions]


# Create UnoEndpoint instances
# The UnoEndpoint initialization requires an app parameter
# This needs to be passed when integrating with a FastAPI application
# Will be initialized in the application startup code


# Define a function that will create the endpoints when an app is available
def create_endpoints(app: FastAPI):
    """Create UnoEndpoint instances for reports module with the FastAPI app instance."""
    return [
        UnoEndpoint(
            name="report_templates",
            model=ReportTemplate,
            router=ListRouter,  # Use appropriate router class
            app=app,
            response_model="view_schema",  # Use appropriate schema
            body_model=None,
        ),
        UnoEndpoint(
            name="report_fields",
            model=ReportFieldDefinition,
            router=ListRouter,  # Use appropriate router class
            app=app,
            response_model="view_schema",  # Use appropriate schema
            body_model=None,
        ),
        UnoEndpoint(
            name="report_triggers",
            model=ReportTrigger,
            router=ListRouter,  # Use appropriate router class
            app=app,
            response_model="view_schema",  # Use appropriate schema
            body_model=None,
        ),
        UnoEndpoint(
            name="report_outputs",
            model=ReportOutput,
            router=ListRouter,  # Use appropriate router class
            app=app,
            response_model="view_schema",  # Use appropriate schema
            body_model=None,
        ),
        UnoEndpoint(
            name="report_executions",
            model=ReportExecution,
            router=ListRouter,  # Use appropriate router class
            app=app,
            response_model="view_schema",  # Use appropriate schema
            body_model=None,
        ),
    ]


# Export endpoints via the router
endpoints = router
