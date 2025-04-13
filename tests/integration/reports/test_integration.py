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
from uno.dependencies.container import UnoContainer
from uno.reports.objs import (
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
from uno.reports.services import (
    ReportTemplateService,
    ReportFieldService,
    ReportTriggerService,
    ReportExecutionService,
    ReportOutputService,
)
from uno.reports.repositories import (
    ReportTemplateRepository,
    ReportFieldDefinitionRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)
from uno.reports.endpoints import setup_report_routes
from tests.integration.reports.fixtures import (
    TEMPLATE_DATA,
    FIELD_DATA,
    TRIGGER_DATA,
    OUTPUT_DATA,
)


@pytest.fixture
async def session_maker():
    """Get async session maker."""
    # Get the session maker from the DI container
    return UnoContainer.get_instance().get(UnoAsyncSessionMaker)


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
        
        # Create services
        template_service = ReportTemplateService(session, template_repo, field_repo)
        field_service = ReportFieldService(session, template_repo, field_repo)
        execution_service = ReportExecutionService(
            session, template_repo, field_repo, execution_repo, output_execution_repo, output_repo
        )
        trigger_service = ReportTriggerService(session, template_repo, trigger_repo, execution_service)
        output_service = ReportOutputService(
            session, template_repo, output_repo, execution_repo, output_execution_repo, field_repo
        )
        
        yield {
            "template_service": template_service,
            "field_service": field_service,
            "trigger_service": trigger_service,
            "execution_service": execution_service,
            "output_service": output_service,
            "session": session,
        }


@pytest.mark.asyncio
async def test_full_report_lifecycle(services):
    """Test full report lifecycle from creation to execution and output."""
    session = services["session"]
    template_service = services["template_service"]
    field_service = services["field_service"]
    trigger_service = services["trigger_service"]
    execution_service = services["execution_service"]
    output_service = services["output_service"]
    
    # 1. Create a report template
    template_data = TEMPLATE_DATA.copy()
    template_data["name"] = f"Integration Test Template {uuid.uuid4()}"
    template_result = await template_service.create_template(template_data)
    assert template_result.is_success
    template = template_result.value
    
    # 2. Add fields to the template
    fields = []
    for i in range(3):
        field_data = FIELD_DATA.copy()
        field_data["name"] = f"test_field_{i}_{uuid.uuid4().hex[:6]}"
        field_data["display_name"] = f"Test Field {i}"
        field_data["order"] = i
        
        field_result = await field_service.add_field(template.id, field_data)
        assert field_result.is_success
        fields.append(field_result.value)
    
    # 3. Add a manual trigger
    trigger_data = TRIGGER_DATA.copy()
    trigger_data["trigger_type"] = ReportTriggerType.MANUAL
    trigger_result = await trigger_service.create_trigger(template.id, trigger_data)
    assert trigger_result.is_success
    trigger = trigger_result.value
    
    # 4. Add an output configuration
    output_data = OUTPUT_DATA.copy()
    output_data["output_type"] = ReportOutputType.FILE
    output_data["format"] = ReportFormat.JSON
    output_data["output_config"] = {"path": "/tmp/reports"}
    output_result = await output_service.create_output_config(template.id, output_data)
    assert output_result.is_success
    output = output_result.value
    
    # 5. Execute the report
    execution_result = await execution_service.execute_report(
        template.id,
        parameters={"start_date": "2023-01-01", "end_date": "2023-12-31"},
        trigger_type=ReportTriggerType.MANUAL,
        user_id="integration_test"
    )
    assert execution_result.is_success
    execution = execution_result.value
    
    # 6. Check execution status
    status_result = await execution_service.get_execution_status(execution.id)
    assert status_result.is_success
    assert status_result.value["status"] in [ReportExecutionStatus.PENDING, ReportExecutionStatus.IN_PROGRESS]
    
    # 7. Complete the execution manually (simulating background task)
    await execution_service.execution_repository.complete_execution(
        execution.id,
        row_count=100,
        execution_time_ms=1500,
        result_hash="integration_test_hash",
        session=session
    )
    
    # 8. Get the execution result
    result_result = await execution_service.get_execution_result(execution.id)
    assert result_result.is_success
    assert result_result.value["execution_id"] == execution.id
    
    # 9. Deliver the report to the configured output
    deliver_result = await output_service.deliver_report(execution.id, output.id)
    assert deliver_result.is_success
    
    # 10. Verify output execution status
    output_executions_result = await output_service.output_execution_repository.list_by_execution(
        execution.id,
        session=session
    )
    assert output_executions_result.is_success
    assert len(output_executions_result.value) > 0
    assert output_executions_result.value[0].status == ReportExecutionStatus.COMPLETED
    
    # 11. Clean up (delete the template, which should cascade delete all related entities)
    delete_result = await template_service.delete_template(template.id)
    assert delete_result.is_success


@pytest.mark.asyncio
async def test_scheduled_trigger_workflow(services):
    """Test scheduled trigger workflow."""
    template_service = services["template_service"]
    trigger_service = services["trigger_service"]
    
    # 1. Create a report template
    template_data = TEMPLATE_DATA.copy()
    template_data["name"] = f"Scheduled Test Template {uuid.uuid4()}"
    template_result = await template_service.create_template(template_data)
    assert template_result.is_success
    template = template_result.value
    
    # 2. Add a scheduled trigger
    trigger_data = TRIGGER_DATA.copy()
    trigger_data["trigger_type"] = ReportTriggerType.SCHEDULED
    trigger_data["schedule"] = "interval:1:hours"
    trigger_data["is_active"] = True
    trigger_result = await trigger_service.create_trigger(template.id, trigger_data)
    assert trigger_result.is_success
    trigger = trigger_result.value
    
    # 3. Process scheduled triggers
    process_result = await trigger_service.process_scheduled_triggers()
    assert process_result.is_success
    
    # 4. Verify that the trigger has been updated with a last_triggered timestamp
    updated_trigger_result = await trigger_service.trigger_repository.get_by_id(trigger.id)
    assert updated_trigger_result.is_success
    assert updated_trigger_result.value.last_triggered is not None
    
    # 5. Clean up
    delete_result = await template_service.delete_template(template.id)
    assert delete_result.is_success


@pytest.mark.asyncio
async def test_event_trigger_workflow(services):
    """Test event trigger workflow."""
    template_service = services["template_service"]
    trigger_service = services["trigger_service"]
    
    # 1. Create a report template
    template_data = TEMPLATE_DATA.copy()
    template_data["name"] = f"Event Test Template {uuid.uuid4()}"
    template_result = await template_service.create_template(template_data)
    assert template_result.is_success
    template = template_result.value
    
    # 2. Add an event trigger
    trigger_data = TRIGGER_DATA.copy()
    trigger_data["trigger_type"] = ReportTriggerType.EVENT
    trigger_data["event_type"] = "test_integration_event"
    trigger_data["entity_type"] = "customer"
    trigger_data["is_active"] = True
    trigger_result = await trigger_service.create_trigger(template.id, trigger_data)
    assert trigger_result.is_success
    
    # 3. Trigger an event
    event_data = {
        "entity_type": "customer",
        "entity_id": "CUST123",
        "action": "update",
        "data": {"field": "value"}
    }
    event_result = await trigger_service.handle_event("test_integration_event", event_data)
    assert event_result.is_success
    
    # 4. Check that the event triggered executions
    assert len(event_result.value) > 0
    
    # 5. Clean up
    delete_result = await template_service.delete_template(template.id)
    assert delete_result.is_success