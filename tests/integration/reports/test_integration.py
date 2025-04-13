# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Integration tests for the reports module."""

import pytest
import uuid
import json
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Success
from uno.database.session import UnoAsyncSessionMaker
from uno.reports.entities import (
    ReportTemplate,
    ReportFieldDefinition,
    ReportTrigger,
    ReportOutput,
    ReportExecution,
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
    ReportExecutionStatus,
)
from uno.reports.domain_services import (
    ReportTemplateService,
    ReportFieldDefinitionService,
    ReportTriggerService,
    ReportExecutionService,
    ReportOutputService,
    ReportOutputExecutionService,
)
from uno.reports.domain_repositories import (
    ReportTemplateRepository,
    ReportFieldDefinitionRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)
from uno.reports.domain_provider import (
    get_report_template_service,
    get_report_field_definition_service,
    get_report_trigger_service,
    get_report_execution_service,
    get_report_output_service,
    get_report_output_execution_service,
)
from tests.integration.reports.fixtures import (
    TEMPLATE_DATA,
    FIELD_DATA,
    TRIGGER_DATA,
    OUTPUT_DATA,
)


@pytest.fixture
async def session_maker():
    """Get async session maker."""
    # Get the session maker from the modern DI system
    from uno.dependencies.modern_provider import get_service_provider
    from uno.database.session import UnoAsyncSessionMaker
    
    # Import database provider
    from uno.dependencies.interfaces import UnoDatabaseProviderProtocol
    
    # Get the provider and access session maker
    provider = get_service_provider()
    db_provider = provider.get_service(UnoDatabaseProviderProtocol)
    return db_provider.async_session_maker


@pytest.fixture
async def services(session_maker):
    """Create all required services for testing."""
    async with session_maker() as session:
        # Create repositories
        template_repo = ReportTemplateRepository(session)
        field_repo = ReportFieldDefinitionRepository(session)
        trigger_repo = ReportTriggerRepository(session)
        output_repo = ReportOutputRepository(session)
        execution_repo = ReportExecutionRepository(session)
        output_execution_repo = ReportOutputExecutionRepository(session)
        
        # Create field service
        field_service = ReportFieldDefinitionService(field_repo)
        
        # Create output execution service
        output_execution_service = ReportOutputExecutionService(output_execution_repo)
        
        # Create output service
        output_service = ReportOutputService(output_repo)
        
        # Create execution service
        execution_service = ReportExecutionService(execution_repo)
        
        # Create trigger service
        trigger_service = ReportTriggerService(trigger_repo)
        
        # Create template service
        template_service = ReportTemplateService(
            template_repo,
            field_service,
            trigger_service,
            output_service
        )
        
        yield {
            "template_service": template_service,
            "field_service": field_service,
            "trigger_service": trigger_service,
            "execution_service": execution_service,
            "output_service": output_service,
            "output_execution_service": output_execution_service,
            "session": session,
            "template_repo": template_repo,
            "field_repo": field_repo,
            "trigger_repo": trigger_repo,
            "output_repo": output_repo,
            "execution_repo": execution_repo,
            "output_execution_repo": output_execution_repo,
        }


@pytest.mark.asyncio
async def test_full_report_lifecycle(services):
    """Test full report lifecycle from creation to execution and output using domain approach."""
    # Get services and repositories
    session = services["session"]
    template_service = services["template_service"]
    field_service = services["field_service"]
    trigger_service = services["trigger_service"]
    execution_service = services["execution_service"]
    output_service = services["output_service"]
    output_execution_service = services["output_execution_service"]
    execution_repo = services["execution_repo"]
    output_execution_repo = services["output_execution_repo"]
    
    # 1. Create a report template
    template = ReportTemplate(
        id=str(uuid.uuid4()),
        name=f"Domain Integration Test Template {uuid.uuid4()}",
        description="Template for domain integration testing",
        base_object_type="customer",
        format_config={
            "title_format": "{name} - Generated on {date}",
            "show_footer": True
        },
        parameter_definitions={
            "start_date": {
                "type": "date",
                "required": True,
                "default": "today-30d"
            }
        },
        cache_policy={
            "ttl_seconds": 3600,
            "invalidate_on_event": "customer_updated"
        },
        version="1.0.0"
    )
    template_result = await template_service.create(template)
    assert template_result.is_success
    template = template_result.value
    
    # 2. Create field definitions
    field_ids = []
    for i in range(3):
        field = ReportFieldDefinition(
            id=str(uuid.uuid4()),
            name=f"test_field_{i}_{uuid.uuid4().hex[:6]}",
            display_name=f"Test Field {i}",
            field_type=ReportFieldType.DB_COLUMN,
            field_config={"table": "customer", "column": "name"},
            description="Field for domain integration testing",
            order=i,
            format_string=None,
            conditional_formats=None,
            is_visible=True
        )
        field_result = await field_service.create(field)
        assert field_result.is_success
        field_ids.append(field_result.value.id)
    
    # Add fields to template
    update_fields_result = await template_service.update_fields(
        template_id=template.id,
        field_ids_to_add=field_ids
    )
    assert update_fields_result.is_success
    
    # 3. Create a manual trigger
    trigger = ReportTrigger(
        id=str(uuid.uuid4()),
        report_template_id=template.id,
        trigger_type=ReportTriggerType.MANUAL,
        trigger_config={
            "timezone": "UTC",
            "run_on_holidays": False
        },
        is_active=True
    )
    trigger_result = await trigger_service.create(trigger)
    assert trigger_result.is_success
    
    # 4. Create an output configuration
    output = ReportOutput(
        id=str(uuid.uuid4()),
        report_template_id=template.id,
        output_type=ReportOutputType.FILE,
        format=ReportFormat.JSON,
        output_config={"path": "/tmp/reports"},
        format_config={},
        is_active=True
    )
    output_result = await output_service.create(output)
    assert output_result.is_success
    
    # 5. Execute the report
    execution_result = await template_service.execute_template(
        template_id=template.id,
        triggered_by="integration_test",
        trigger_type=ReportTriggerType.MANUAL,
        parameters={"start_date": "2023-01-01", "end_date": "2023-12-31"}
    )
    assert execution_result.is_success
    execution = execution_result.value
    
    # 6. Update execution status (simulating background processing)
    update_status_result = await execution_service.update_execution_status(
        execution_id=execution.id,
        status=ReportExecutionStatus.COMPLETED,
        error_details=None
    )
    assert update_status_result.is_success
    
    # 7. Create an output execution record
    output_execution = ReportOutputExecution(
        id=str(uuid.uuid4()),
        report_execution_id=execution.id,
        report_output_id=output.id,
        status=ReportExecutionStatus.COMPLETED,
        completed_at=datetime.utcnow(),
        output_location="/tmp/reports/report.json",
        output_size_bytes=1024
    )
    output_execution_result = await output_execution_service.create(output_execution)
    assert output_execution_result.is_success
    
    # 8. Find execution with output executions
    find_execution_result = await execution_service.find_with_output_executions(execution.id)
    assert find_execution_result.is_success
    found_execution = find_execution_result.value
    
    # 9. Find output executions by execution
    find_output_executions_result = await output_execution_service.find_by_execution_id(execution.id)
    assert find_output_executions_result.is_success
    output_executions = find_output_executions_result.value
    assert len(output_executions) > 0
    assert output_executions[0].status == ReportExecutionStatus.COMPLETED
    
    # 10. Clean up
    await execution_repo.delete(execution.id)
    for field_id in field_ids:
        await field_service.delete(field_id)
    await trigger_service.delete(trigger.id)
    await output_service.delete(output.id)
    await template_service.delete(template.id)


@pytest.mark.asyncio
async def test_scheduled_trigger_workflow(services):
    """Test scheduled trigger workflow with domain approach."""
    # Get services and repositories
    template_service = services["template_service"]
    trigger_service = services["trigger_service"]
    trigger_repo = services["trigger_repo"]
    
    # 1. Create a report template
    template = ReportTemplate(
        id=str(uuid.uuid4()),
        name=f"Domain Scheduled Test Template {uuid.uuid4()}",
        description="Template for domain scheduled trigger testing",
        base_object_type="customer",
        format_config={
            "title_format": "{name} - Generated on {date}",
            "show_footer": True
        },
        parameter_definitions={
            "start_date": {
                "type": "date",
                "required": True,
                "default": "today-30d"
            }
        },
        cache_policy={
            "ttl_seconds": 3600,
            "invalidate_on_event": "customer_updated"
        },
        version="1.0.0"
    )
    template_result = await template_service.create(template)
    assert template_result.is_success
    template = template_result.value
    
    # 2. Create a scheduled trigger
    trigger = ReportTrigger(
        id=str(uuid.uuid4()),
        report_template_id=template.id,
        trigger_type=ReportTriggerType.SCHEDULED,
        schedule="interval:1:hours",
        trigger_config={
            "timezone": "UTC",
            "run_on_holidays": False
        },
        is_active=True
    )
    trigger_result = await trigger_service.create(trigger)
    assert trigger_result.is_success
    trigger = trigger_result.value
    
    # 3. Process scheduled triggers
    process_result = await trigger_service.process_due_triggers()
    assert process_result.is_success
    
    # 4. Verify that the trigger has been updated with a last_triggered timestamp
    updated_trigger_result = await trigger_service.get(trigger.id)
    assert updated_trigger_result.is_success
    assert updated_trigger_result.value.last_triggered is not None
    
    # 5. Clean up
    await trigger_service.delete(trigger.id)
    await template_service.delete(template.id)


@pytest.mark.asyncio
async def test_event_trigger_workflow(services):
    """Test event trigger workflow with domain approach."""
    # Get services and repositories
    template_service = services["template_service"]
    trigger_service = services["trigger_service"]
    
    # 1. Create a report template
    template = ReportTemplate(
        id=str(uuid.uuid4()),
        name=f"Domain Event Test Template {uuid.uuid4()}",
        description="Template for domain event trigger testing",
        base_object_type="customer",
        format_config={
            "title_format": "{name} - Generated on {date}",
            "show_footer": True
        },
        parameter_definitions={
            "start_date": {
                "type": "date",
                "required": True,
                "default": "today-30d"
            }
        },
        cache_policy={
            "ttl_seconds": 3600,
            "invalidate_on_event": "customer_updated"
        },
        version="1.0.0"
    )
    template_result = await template_service.create(template)
    assert template_result.is_success
    template = template_result.value
    
    # 2. Create an event trigger
    trigger = ReportTrigger(
        id=str(uuid.uuid4()),
        report_template_id=template.id,
        trigger_type=ReportTriggerType.EVENT,
        event_type="test_integration_event",
        entity_type="customer",
        trigger_config={
            "filter_condition": "action = 'update'"
        },
        is_active=True
    )
    trigger_result = await trigger_service.create(trigger)
    assert trigger_result.is_success
    trigger = trigger_result.value
    
    # 3. Handle a test event
    event_data = {
        "entity_type": "customer",
        "entity_id": "CUST123",
        "action": "update",
        "data": {"field": "value"}
    }
    
    # Note: In the domain approach, we'd need to implement an event handling mechanism
    # For this test, we'll just check that the trigger is correctly configured
    active_triggers_result = await trigger_service.find_active_triggers()
    assert active_triggers_result.is_success
    active_triggers = active_triggers_result.value
    
    # Verify our event trigger is in the active triggers
    event_triggers = [t for t in active_triggers if t.trigger_type == ReportTriggerType.EVENT]
    assert len(event_triggers) > 0
    assert any(t.event_type == "test_integration_event" for t in event_triggers)
    
    # 4. Clean up
    await trigger_service.delete(trigger.id)
    await template_service.delete(template.id)