# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Command-line interface for the reports module.

This module provides CLI commands for managing and executing reports.
"""

import argparse
import asyncio
import sys
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from uno.core.errors.result import Result
from uno.database.db_manager import DBManager
from uno.reports.repositories import (
    ReportTemplateRepository,
    ReportFieldDefinitionRepository,
    ReportTriggerRepository,
    ReportOutputRepository,
    ReportExecutionRepository,
    ReportOutputExecutionRepository,
)
from uno.reports.services import (
    ReportTemplateService,
    ReportFieldService,
    ReportExecutionService,
    ReportTriggerService,
    ReportOutputService,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("reports-cli")


# Helper functions
async def get_session(connection_string: str) -> AsyncSession:
    """Create a database session."""
    engine = create_async_engine(connection_string)
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    return async_session()


async def get_services(
    session: AsyncSession
) -> tuple[
    ReportTemplateService,
    ReportFieldService,
    ReportExecutionService,
    ReportTriggerService,
    ReportOutputService
]:
    """Create service instances."""
    # Repositories
    template_repo = ReportTemplateRepository(session)
    field_repo = ReportFieldDefinitionRepository(session)
    trigger_repo = ReportTriggerRepository(session)
    execution_repo = ReportExecutionRepository(session)
    output_repo = ReportOutputRepository(session)
    output_execution_repo = ReportOutputExecutionRepository(session)
    
    # Services
    execution_service = ReportExecutionService(
        session, template_repo, field_repo, execution_repo, output_execution_repo, output_repo
    )
    
    template_service = ReportTemplateService(session, template_repo, field_repo)
    field_service = ReportFieldService(session, template_repo, field_repo)
    trigger_service = ReportTriggerService(session, template_repo, trigger_repo, execution_service)
    output_service = ReportOutputService(
        session, template_repo, output_repo, execution_repo, output_execution_repo, field_repo
    )
    
    return (
        template_service,
        field_service,
        execution_service,
        trigger_service,
        output_service
    )


def print_result(result: Result[Any], success_message: str = "Operation successful") -> int:
    """Print the result of an operation and return exit code."""
    if result.is_success:
        if result.value is not None:
            if isinstance(result.value, list):
                for item in result.value:
                    if hasattr(item, "model_dump"):
                        print(json.dumps(item.model_dump(), indent=2))
                    else:
                        print(item)
            elif hasattr(result.value, "model_dump"):
                print(json.dumps(result.value.model_dump(), indent=2))
            else:
                print(result.value)
        else:
            print(success_message)
        return 0
    else:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1


# Command implementations
async def list_templates(args: argparse.Namespace) -> int:
    """List report templates."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        template_service = services[0]
        
        filters = {}
        if args.name:
            filters["name"] = args.name
        if args.object_type:
            filters["base_object_type"] = args.object_type
        
        result = await template_service.list_templates(filters)
        return print_result(result)


async def get_template(args: argparse.Namespace) -> int:
    """Get a report template by ID."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        template_service = services[0]
        
        result = await template_service.get_template(args.id)
        return print_result(result)


async def create_template(args: argparse.Namespace) -> int:
    """Create a new report template."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        template_service = services[0]
        
        # Parse template data from file or stdin
        if args.file:
            with open(args.file, "r") as f:
                template_data = json.load(f)
        else:
            template_data = json.loads(sys.stdin.read())
        
        result = await template_service.create_template(template_data)
        return print_result(result, "Template created successfully")


async def update_template(args: argparse.Namespace) -> int:
    """Update an existing report template."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        template_service = services[0]
        
        # Parse template data from file or stdin
        if args.file:
            with open(args.file, "r") as f:
                template_data = json.load(f)
        else:
            template_data = json.loads(sys.stdin.read())
        
        result = await template_service.update_template(args.id, template_data)
        return print_result(result, "Template updated successfully")


async def delete_template(args: argparse.Namespace) -> int:
    """Delete a report template."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        template_service = services[0]
        
        result = await template_service.delete_template(args.id)
        return print_result(result, "Template deleted successfully")


async def clone_template(args: argparse.Namespace) -> int:
    """Clone a report template."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        template_service = services[0]
        
        result = await template_service.clone_template(args.id, args.new_name)
        return print_result(result, "Template cloned successfully")


async def execute_report(args: argparse.Namespace) -> int:
    """Execute a report."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        execution_service = services[2]
        
        # Parse parameters
        parameters = {}
        if args.parameters:
            parameters = json.loads(args.parameters)
        elif args.parameters_file:
            with open(args.parameters_file, "r") as f:
                parameters = json.load(f)
        
        result = await execution_service.execute_report(
            args.id,
            parameters,
            trigger_type="manual",
            user_id=args.user_id
        )
        
        if result.is_success:
            execution = result.value
            print(f"Report execution started with ID: {execution.id}")
            print(f"Status: {execution.status}")
            
            if args.wait:
                print("Waiting for execution to complete...")
                
                # Poll for status
                max_retries = 60  # 5 minutes with 5-second intervals
                for _ in range(max_retries):
                    status_result = await execution_service.get_execution_status(execution.id)
                    if status_result.is_failure:
                        print(f"Error getting status: {status_result.error}", file=sys.stderr)
                        return 1
                    
                    status_info = status_result.value
                    if status_info["status"] in ["completed", "failed", "cancelled"]:
                        break
                    
                    await asyncio.sleep(5)
                
                # Get final status
                status_result = await execution_service.get_execution_status(execution.id)
                if status_result.is_success:
                    status_info = status_result.value
                    print(f"Final status: {status_info['status']}")
                    
                    if status_info["status"] == "completed":
                        result_format = args.format or "json"
                        result = await execution_service.get_execution_result(execution.id, result_format)
                        return print_result(result)
                    else:
                        if status_info["error_details"]:
                            print(f"Error details: {status_info['error_details']}", file=sys.stderr)
                        return 1 if status_info["status"] != "completed" else 0
                else:
                    print(f"Error getting final status: {status_result.error}", file=sys.stderr)
                    return 1
            
            return 0
        else:
            print(f"Error: {result.error}", file=sys.stderr)
            return 1


async def list_triggers(args: argparse.Namespace) -> int:
    """List triggers for a template."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        trigger_service = services[3]
        
        result = await trigger_service.list_triggers_by_template(args.id)
        return print_result(result)


async def process_scheduled_triggers(args: argparse.Namespace) -> int:
    """Process scheduled triggers."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        trigger_service = services[3]
        
        result = await trigger_service.process_scheduled_triggers()
        if result.is_success:
            execution_ids = result.value
            print(f"Processed scheduled triggers. {len(execution_ids)} reports executed.")
            for execution_id in execution_ids:
                print(f"- Execution ID: {execution_id}")
            return 0
        else:
            print(f"Error: {result.error}", file=sys.stderr)
            return 1


async def process_query_triggers(args: argparse.Namespace) -> int:
    """Process query triggers."""
    async with get_session(args.connection_string) as session:
        services = await get_services(session)
        trigger_service = services[3]
        
        result = await trigger_service.check_query_triggers()
        if result.is_success:
            execution_ids = result.value
            print(f"Processed query triggers. {len(execution_ids)} reports executed.")
            for execution_id in execution_ids:
                print(f"- Execution ID: {execution_id}")
            return 0
        else:
            print(f"Error: {result.error}", file=sys.stderr)
            return 1


# Main CLI function
def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Reports module CLI")
    parser.add_argument(
        "--connection-string",
        default="postgresql+asyncpg://postgres:postgres@localhost/postgres",
        help="Database connection string"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Template commands
    templates_parser = subparsers.add_parser("templates", help="Template management commands")
    templates_subparsers = templates_parser.add_subparsers(dest="subcommand")
    
    # List templates
    list_templates_parser = templates_subparsers.add_parser("list", help="List templates")
    list_templates_parser.add_argument("--name", help="Filter by name")
    list_templates_parser.add_argument("--object-type", help="Filter by object type")
    list_templates_parser.set_defaults(func=list_templates)
    
    # Get template
    get_template_parser = templates_subparsers.add_parser("get", help="Get template by ID")
    get_template_parser.add_argument("id", help="Template ID")
    get_template_parser.set_defaults(func=get_template)
    
    # Create template
    create_template_parser = templates_subparsers.add_parser("create", help="Create template")
    create_template_parser.add_argument(
        "--file", help="JSON file with template data (if not provided, read from stdin)"
    )
    create_template_parser.set_defaults(func=create_template)
    
    # Update template
    update_template_parser = templates_subparsers.add_parser("update", help="Update template")
    update_template_parser.add_argument("id", help="Template ID")
    update_template_parser.add_argument(
        "--file", help="JSON file with template data (if not provided, read from stdin)"
    )
    update_template_parser.set_defaults(func=update_template)
    
    # Delete template
    delete_template_parser = templates_subparsers.add_parser("delete", help="Delete template")
    delete_template_parser.add_argument("id", help="Template ID")
    delete_template_parser.set_defaults(func=delete_template)
    
    # Clone template
    clone_template_parser = templates_subparsers.add_parser("clone", help="Clone template")
    clone_template_parser.add_argument("id", help="Template ID")
    clone_template_parser.add_argument("new_name", help="New template name")
    clone_template_parser.set_defaults(func=clone_template)
    
    # Execution commands
    execute_parser = subparsers.add_parser("execute", help="Execute a report")
    execute_parser.add_argument("id", help="Template ID")
    execute_parser.add_argument(
        "--parameters", help="JSON string with parameters"
    )
    execute_parser.add_argument(
        "--parameters-file", help="JSON file with parameters"
    )
    execute_parser.add_argument(
        "--user-id", help="User ID to attribute the execution to"
    )
    execute_parser.add_argument(
        "--wait", action="store_true", help="Wait for execution to complete"
    )
    execute_parser.add_argument(
        "--format", help="Format for the result when waiting (json, csv, etc.)"
    )
    execute_parser.set_defaults(func=execute_report)
    
    # Trigger commands
    triggers_parser = subparsers.add_parser("triggers", help="Trigger management commands")
    triggers_subparsers = triggers_parser.add_subparsers(dest="subcommand")
    
    # List triggers
    list_triggers_parser = triggers_subparsers.add_parser("list", help="List triggers for template")
    list_triggers_parser.add_argument("id", help="Template ID")
    list_triggers_parser.set_defaults(func=list_triggers)
    
    # Process scheduled triggers
    process_scheduled_parser = triggers_subparsers.add_parser(
        "process-scheduled", help="Process scheduled triggers"
    )
    process_scheduled_parser.set_defaults(func=process_scheduled_triggers)
    
    # Process query triggers
    process_query_parser = triggers_subparsers.add_parser(
        "process-query", help="Process query triggers"
    )
    process_query_parser.set_defaults(func=process_query_triggers)
    
    args = parser.parse_args()
    
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    
    return asyncio.run(args.func(args))


if __name__ == "__main__":
    sys.exit(main())