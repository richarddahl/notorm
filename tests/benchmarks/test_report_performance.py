"""
Performance benchmarks for report module functionality.

These benchmarks measure the performance of report operations
under different conditions to help identify bottlenecks and
optimization opportunities.
"""

import pytest
import asyncio
import time
import uuid
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Dict, Tuple

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
from uno.reports.domain_services import (
    ReportFieldDefinitionService,
    ReportTemplateService,
    ReportTriggerService,
    ReportOutputService,
    ReportExecutionService,
    ReportOutputExecutionService,
)
from uno.database.session import async_session
from uno.dependencies import get_service, register_service, register_factory


# Skip these benchmarks in normal test runs
pytestmark = [
    pytest.mark.benchmark,
    pytest.mark.skipif(
        "not config.getoption('--run-benchmark')",
        reason="Only run when --run-benchmark is specified"
    )
]


@pytest.fixture(scope="module")
async def db_session():
    """Create a database session."""
    async with async_session() as session:
        yield session


@pytest.fixture(scope="module")
async def report_services():
    """Create report services for benchmarking."""
    # Create repositories
    field_repo = ReportFieldDefinitionRepository()
    template_repo = ReportTemplateRepository()
    trigger_repo = ReportTriggerRepository()
    output_repo = ReportOutputRepository()
    execution_repo = ReportExecutionRepository()
    output_execution_repo = ReportOutputExecutionRepository()
    
    # Create services
    field_service = ReportFieldDefinitionService(field_repo)
    register_service(ReportFieldDefinitionService, field_service)
    
    output_service = ReportOutputService(output_repo)
    register_service(ReportOutputService, output_service)
    
    trigger_service = ReportTriggerService(trigger_repo)
    register_service(ReportTriggerService, trigger_service)
    
    template_service = ReportTemplateService(
        template_repo, field_service, trigger_service, output_service
    )
    register_service(ReportTemplateService, template_service)
    
    execution_service = ReportExecutionService(execution_repo)
    register_service(ReportExecutionService, execution_service)
    
    output_execution_service = ReportOutputExecutionService(output_execution_repo)
    register_service(ReportOutputExecutionService, output_execution_service)
    
    services = {
        "field_service": field_service,
        "template_service": template_service,
        "trigger_service": trigger_service,
        "output_service": output_service,
        "execution_service": execution_service,
        "output_execution_service": output_execution_service,
    }
    
    yield services


@pytest.fixture(scope="module")
async def setup_benchmark_environment(db_session, report_services):
    """Set up the benchmark environment with test data."""
    template_service = report_services["template_service"]
    field_service = report_services["field_service"]
    trigger_service = report_services["trigger_service"]
    output_service = report_services["output_service"]
    
    # Create test data with different sizes
    template_counts = [5, 10, 20]
    field_counts = [10, 20, 30]
    trigger_counts = [2, 5, 10]
    output_counts = [2, 3, 5]
    
    created_templates = []
    created_fields = []
    created_triggers = []
    created_outputs = []
    
    print(f"Setting up report benchmark environment...")
    
    # Create field definitions
    for i in range(max(field_counts)):
        field = ReportFieldDefinition(
            id=str(uuid.uuid4()),
            name=f"Field_{i}",
            field_type="string" if i % 3 == 0 else "number" if i % 3 == 1 else "date",
            description=f"Benchmark field definition {i}",
            is_required=i % 2 == 0,
            default_value=f"default_{i}" if i % 3 == 0 else i if i % 3 == 1 else None,
            validation_rules=json.dumps({"min_length": 1, "max_length": 100}) if i % 3 == 0 else None,
        )
        
        result = await field_service.create(field)
        if result.is_success:
            created_fields.append(result.value)
    
    print(f"Created {len(created_fields)} field definitions")
    
    # Create templates with varying numbers of fields
    for size_index, template_count in enumerate(template_counts):
        for i in range(template_count):
            template = ReportTemplate(
                id=str(uuid.uuid4()),
                name=f"Template_{size_index}_{i}",
                description=f"Benchmark template {i} for size {size_index}",
                base_object_type="customer" if i % 3 == 0 else "order" if i % 3 == 1 else "product",
                query=f"SELECT * FROM {i % 3 == 0 and 'customers' or i % 3 == 1 and 'orders' or 'products'} LIMIT 100",
                parameters=json.dumps({"param1": "value1", "param2": "value2"}),
                created_by="benchmark",
                updated_by="benchmark",
            )
            
            # Add fields to the template (different number based on size)
            field_count = field_counts[size_index]
            field_ids = [field.id for field in created_fields[:field_count]]
            
            result = await template_service.create_with_relationships(template, field_ids)
            if result.is_success:
                created_templates.append(result.value)
                
                # Create triggers for this template
                for j in range(trigger_counts[size_index]):
                    trigger = ReportTrigger(
                        id=str(uuid.uuid4()),
                        report_template_id=template.id,
                        name=f"Trigger_{i}_{j}",
                        description=f"Benchmark trigger {j} for template {i}",
                        trigger_type=ReportTriggerType.SCHEDULED if j % 2 == 0 else ReportTriggerType.EVENT,
                        schedule=f"0 {j} * * *" if j % 2 == 0 else None,
                        event_type=f"entity.created" if j % 2 == 1 else None,
                        is_active=True,
                        parameters=json.dumps({"key": f"value_{j}"}),
                    )
                    
                    trigger_result = await trigger_service.create(trigger)
                    if trigger_result.is_success:
                        created_triggers.append(trigger_result.value)
                
                # Create outputs for this template
                for j in range(output_counts[size_index]):
                    output = ReportOutput(
                        id=str(uuid.uuid4()),
                        report_template_id=template.id,
                        name=f"Output_{i}_{j}",
                        description=f"Benchmark output {j} for template {i}",
                        output_type="file" if j % 2 == 0 else "email",
                        format="CSV" if j % 3 == 0 else "PDF" if j % 3 == 1 else "XLSX",
                        destination=f"/reports/template_{i}" if j % 2 == 0 else f"user{j}@example.com",
                        is_active=True,
                        parameters=json.dumps({"key": f"value_{j}"}),
                    )
                    
                    output_result = await output_service.create(output)
                    if output_result.is_success:
                        created_outputs.append(output_result.value)
    
    print(f"Created {len(created_templates)} templates")
    print(f"Created {len(created_triggers)} triggers")
    print(f"Created {len(created_outputs)} outputs")
    
    # Return created data for tests to use
    yield {
        "templates": created_templates,
        "fields": created_fields,
        "triggers": created_triggers,
        "outputs": created_outputs,
        "sizes": {
            "small": 0,
            "medium": 1,
            "large": 2,
        }
    }
    
    # Cleanup would be nice, but for benchmarks, it's often faster to just recreate the database


@pytest.mark.asyncio
async def test_template_creation_performance(report_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of creating a report template with fields."""
    template_service = report_services["template_service"]
    fields = setup_benchmark_environment["fields"]
    
    # Define field counts to test
    field_counts = [5, 20, 50]
    results = {}
    
    for count in field_counts:
        # Create a unique template
        template = ReportTemplate(
            id=str(uuid.uuid4()),
            name=f"BenchTemplate_{count}_{uuid.uuid4()}",
            description=f"Benchmark template with {count} fields",
            base_object_type="customer",
            query="SELECT * FROM customers LIMIT 100",
            parameters=json.dumps({"param1": "value1", "param2": "value2"}),
            created_by="benchmark",
            updated_by="benchmark",
        )
        
        # Select fields
        field_ids = [field.id for field in fields[:count]]
        
        # Define async benchmark function
        async def create_template_benchmark():
            result = await template_service.create_with_relationships(
                template=template.copy(deep=True), 
                field_ids=field_ids
            )
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(create_template_benchmark()),
            iterations=5,
            rounds=3,
            name=f"template_create_{count}_fields"
        )
        
        results[count] = runtime
        print(f"Template creation with {count} fields took {runtime:.4f} seconds")

    # Compare results
    print("\nTemplate creation performance by field count:")
    for count, time in results.items():
        print(f"  Fields {count}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_template_query_performance(report_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of querying report templates with different filters."""
    template_service = report_services["template_service"]
    
    # Define different query types to benchmark
    query_benchmarks = [
        ("find_all", None),
        ("find_by_name", "Template_2_"),
        ("find_by_base_object_type", "customer"),
    ]
    
    results = {}
    
    for query_name, query_param in query_benchmarks:
        # Define async benchmark function based on query type
        async def query_benchmark():
            if query_name == "find_all":
                result = await template_service.list()
                return result
            elif query_name == "find_by_name":
                # This is a prefix search
                templates = []
                all_templates = await template_service.list() 
                if all_templates.is_success:
                    for template in all_templates.value:
                        if template.name.startswith(query_param):
                            templates.append(template)
                return Success(templates)
            elif query_name == "find_by_base_object_type":
                result = await template_service.find_by_base_object_type(query_param)
                return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(query_benchmark()),
            iterations=10,
            rounds=3,
            name=f"template_query_{query_name}"
        )
        
        results[query_name] = runtime
        print(f"Template query {query_name} took {runtime:.4f} seconds")
    
    # Compare results
    print("\nTemplate query performance by query type:")
    for query_name, time in results.items():
        print(f"  {query_name}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_trigger_processing_performance(report_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of processing triggers with different batch sizes."""
    trigger_service = report_services["trigger_service"]
    template_service = report_services["template_service"]
    
    # Create a test wrapper to limit the number of triggers processed
    async def process_triggers_with_limit(limit: int):
        # Override process_due_triggers to limit the number of triggers processed
        original_method = trigger_service.process_due_triggers
        
        async def limited_process():
            triggers_result = await trigger_service.find_active_scheduled_triggers()
            if triggers_result.is_failure:
                return triggers_result
            
            triggers = triggers_result.value
            limited_triggers = triggers[:limit] if limit < len(triggers) else triggers
            processed_count = 0
            
            for trigger in limited_triggers:
                execution_result = await template_service.execute_template(
                    template_id=trigger.report_template_id,
                    triggered_by="benchmark",
                    trigger_type=ReportTriggerType.SCHEDULED,
                    parameters={},
                )
                
                if execution_result.is_success:
                    processed_count += 1
                    
                    # Update the trigger's last_triggered timestamp
                    trigger.last_triggered = datetime.utcnow()
                    await trigger_service.repository.update(trigger)
            
            return Success(processed_count)
        
        try:
            # Replace the method
            trigger_service.process_due_triggers = limited_process
            
            # Call the method
            result = await trigger_service.process_due_triggers()
            return result
        finally:
            # Restore the original method
            trigger_service.process_due_triggers = original_method
    
    # Define batch sizes to test
    batch_sizes = [1, 5, 10]
    results = {}
    
    for batch_size in batch_sizes:
        # Define async benchmark function
        async def trigger_benchmark():
            result = await process_triggers_with_limit(batch_size)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(trigger_benchmark()),
            iterations=3,
            rounds=3,
            name=f"trigger_process_{batch_size}"
        )
        
        results[batch_size] = runtime
        print(f"Processing {batch_size} triggers took {runtime:.4f} seconds")
    
    # Calculate per-trigger time
    per_trigger_times = {size: time/size for size, time in results.items()}
    
    # Compare results
    print("\nTrigger processing performance:")
    for size, time in results.items():
        print(f"  Batch size {size}: {time:.4f} seconds total, {per_trigger_times[size]:.4f} seconds per trigger")


@pytest.mark.asyncio
async def test_report_execution_performance(report_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of report execution with different output counts."""
    template_service = report_services["template_service"]
    templates = setup_benchmark_environment["templates"]
    
    # Group templates by size
    templates_by_size = {}
    for template in templates:
        if "Template_0_" in template.name:
            size = "small"
        elif "Template_1_" in template.name:
            size = "medium"
        elif "Template_2_" in template.name:
            size = "large"
        
        if size not in templates_by_size:
            templates_by_size[size] = []
        templates_by_size[size].append(template)
    
    # Make sure we have templates for each size
    for size in ["small", "medium", "large"]:
        if size not in templates_by_size or not templates_by_size[size]:
            print(f"Warning: No templates found for size {size}")
    
    results = {}
    
    # Test execution for each size
    for size, size_templates in templates_by_size.items():
        if not size_templates:
            continue
        
        template = size_templates[0]  # Take the first template of this size
        
        # Define async benchmark function
        async def execution_benchmark():
            result = await template_service.execute_template(
                template_id=template.id,
                triggered_by="benchmark",
                trigger_type="manual",
                parameters={},
            )
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(execution_benchmark()),
            iterations=5,
            rounds=3,
            name=f"report_execution_{size}"
        )
        
        results[size] = runtime
        print(f"Report execution for {size} template took {runtime:.4f} seconds")
    
    # Compare results
    print("\nReport execution performance by template size:")
    for size, time in results.items():
        print(f"  {size} template: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_field_update_performance(report_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of updating fields in templates with different field counts."""
    template_service = report_services["template_service"]
    field_service = report_services["field_service"]
    
    templates = setup_benchmark_environment["templates"]
    fields = setup_benchmark_environment["fields"]
    
    # Create new fields for the update
    new_fields = []
    for i in range(10):
        field = ReportFieldDefinition(
            id=str(uuid.uuid4()),
            name=f"UpdateField_{i}_{uuid.uuid4().hex[:8]}",
            field_type="string" if i % 3 == 0 else "number" if i % 3 == 1 else "date",
            description=f"Benchmark update field {i}",
            is_required=i % 2 == 0,
            default_value=f"update_default_{i}" if i % 3 == 0 else i if i % 3 == 1 else None,
            validation_rules=json.dumps({"min_length": 1, "max_length": 100}) if i % 3 == 0 else None,
        )
        
        result = await field_service.create(field)
        if result.is_success:
            new_fields.append(result.value)
    
    print(f"Created {len(new_fields)} new fields for update tests")
    
    # Group templates by size based on name prefix
    templates_by_size = {}
    for template in templates:
        if "Template_0_" in template.name:  # Small
            if "small" not in templates_by_size:
                templates_by_size["small"] = []
            templates_by_size["small"].append(template)
        elif "Template_1_" in template.name:  # Medium
            if "medium" not in templates_by_size:
                templates_by_size["medium"] = []
            templates_by_size["medium"].append(template)
        elif "Template_2_" in template.name:  # Large
            if "large" not in templates_by_size:
                templates_by_size["large"] = []
            templates_by_size["large"].append(template)
    
    results = {}
    
    # Test field updates for each size
    for size, size_templates in templates_by_size.items():
        if not size_templates:
            continue
        
        template = size_templates[0]  # Take the first template of this size
        
        # Get new field IDs to add
        fields_to_add = [field.id for field in new_fields[:5]]
        
        # Get existing field IDs to remove
        template_with_fields = await template_service.get_with_relationships(template.id)
        if template_with_fields.is_failure or not template_with_fields.value.fields:
            print(f"Warning: No fields found for template {template.id}")
            continue
        
        fields_to_remove = [field.id for field in template_with_fields.value.fields[:3]]
        
        # Define async benchmark function
        async def update_fields_benchmark():
            result = await template_service.update_fields(
                template_id=template.id,
                field_ids_to_add=fields_to_add,
                field_ids_to_remove=fields_to_remove,
            )
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(update_fields_benchmark()),
            iterations=3,
            rounds=3,
            name=f"field_update_{size}"
        )
        
        results[size] = runtime
        print(f"Field update for {size} template took {runtime:.4f} seconds")
    
    # Compare results
    print("\nField update performance by template size:")
    for size, time in results.items():
        print(f"  {size} template: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_recent_executions_query_performance(report_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of querying recent executions with different limits."""
    execution_service = report_services["execution_service"]
    
    # Define limits to test
    limits = [10, 50, 100]
    results = {}
    
    for limit in limits:
        # Define async benchmark function
        async def query_benchmark():
            result = await execution_service.find_recent_executions(limit)
            return result
        
        # Run benchmark
        runtime = benchmark.pedantic(
            lambda: asyncio.run(query_benchmark()),
            iterations=5,
            rounds=3,
            name=f"recent_executions_{limit}"
        )
        
        results[limit] = runtime
        print(f"Querying {limit} recent executions took {runtime:.4f} seconds")
    
    # Compare results
    print("\nRecent executions query performance by limit:")
    for limit, time in results.items():
        print(f"  Limit {limit}: {time:.4f} seconds")


@pytest.mark.asyncio
async def test_execution_with_relationships_query_performance(report_services, setup_benchmark_environment, benchmark):
    """Benchmark the performance of querying executions with relationships."""
    execution_service = report_services["execution_service"]
    template_service = report_services["template_service"]
    
    # First, execute some templates to create executions
    templates = setup_benchmark_environment["templates"]
    
    # Take a few templates
    test_templates = templates[:3]
    executions = []
    
    for template in test_templates:
        execution_result = await template_service.execute_template(
            template_id=template.id,
            triggered_by="benchmark_relationship_test",
            trigger_type="manual",
            parameters={},
        )
        
        if execution_result.is_success:
            executions.append(execution_result.value)
    
    print(f"Created {len(executions)} executions for relationship query tests")
    
    if not executions:
        print("Warning: No executions created for benchmark")
        return
    
    # Benchmark finding executions with relationships
    execution_id = executions[0].id
    
    # Define async benchmark function
    async def relationship_query_benchmark():
        result = await execution_service.find_with_output_executions(execution_id)
        return result
    
    # Run benchmark
    runtime = benchmark.pedantic(
        lambda: asyncio.run(relationship_query_benchmark()),
        iterations=10,
        rounds=3,
        name="execution_with_relationships"
    )
    
    print(f"Querying execution with relationships took {runtime:.4f} seconds")