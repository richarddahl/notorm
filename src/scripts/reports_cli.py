#!/usr/bin/env python
"""
Reports CLI - Command line interface for the reports module.

This CLI provides functionality for managing report templates, fields, triggers,
and outputs, as well as executing reports and viewing their results.

Usage:
    reports_cli.py templates list
    reports_cli.py templates get <template_id>
    reports_cli.py templates create <name> <description> <base_object_type>
    reports_cli.py templates update <template_id> [--name=<name>] [--description=<desc>] [--base_object_type=<type>]
    reports_cli.py templates delete <template_id>
    reports_cli.py templates clone <template_id> <new_name>

    reports_cli.py fields list <template_id>
    reports_cli.py fields get <field_id>
    reports_cli.py fields add <template_id> <name> <display_name> <field_type> [--config=<config_json>]
    reports_cli.py fields update <field_id> [--name=<name>] [--display_name=<display_name>] [--config=<config_json>]
    reports_cli.py fields delete <field_id>

    reports_cli.py triggers list <template_id>
    reports_cli.py triggers get <trigger_id>
    reports_cli.py triggers add <template_id> <trigger_type> [--config=<config_json>] [--schedule=<schedule>]
    reports_cli.py triggers update <trigger_id> [--config=<config_json>] [--schedule=<schedule>] [--active=<true|false>]
    reports_cli.py triggers delete <trigger_id>
    reports_cli.py triggers enable <trigger_id>
    reports_cli.py triggers disable <trigger_id>

    reports_cli.py outputs list <template_id>
    reports_cli.py outputs get <output_id>
    reports_cli.py outputs add <template_id> <output_type> <format> [--config=<config_json>]
    reports_cli.py outputs update <output_id> [--output_type=<type>] [--format=<format>] [--config=<config_json>]
    reports_cli.py outputs delete <output_id>

    reports_cli.py execute <template_id> [--parameters=<params_json>] [--trigger_type=<type>] [--user_id=<user_id>]
    reports_cli.py executions list <template_id> [--status=<status>] [--limit=<limit>]
    reports_cli.py executions get <execution_id>
    reports_cli.py executions cancel <execution_id>
    reports_cli.py executions result <execution_id> [--format=<format>] [--output=<output_file>]

    reports_cli.py scheduler run
    reports_cli.py event trigger <event_type> <event_data_json>

Options:
    -h --help                   Show this help message and exit
    --name=<name>               Name of the template or field
    --description=<desc>        Description of the template
    --base_object_type=<type>   Base object type for the template
    --display_name=<name>       Display name for the field
    --config=<config_json>      Configuration as JSON string
    --schedule=<schedule>       Schedule for the trigger (e.g., "interval:24:hours")
    --active=<true|false>       Whether the trigger is active
    --parameters=<params_json>  Parameters for report execution as JSON string
    --trigger_type=<type>       Trigger type for execution (default: manual)
    --user_id=<user_id>         User ID for execution (default: current user)
    --status=<status>           Status filter for executions
    --limit=<limit>             Limit for number of results (default: 10)
    --format=<format>           Format for result output (csv, json, pdf, excel, html, text)
    --output=<output_file>      Output file for report result
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

import docopt
import tabulate
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to Python path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from uno.dependencies.container import UnoContainer
from uno.database.session import UnoAsyncSessionMaker
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
    ReportTriggerService,
    ReportExecutionService,
    ReportOutputService,
)


def create_services(session: AsyncSession) -> dict[str, Any]:
    """Create services needed for CLI."""
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
        session,
        template_repo,
        field_repo,
        execution_repo,
        output_execution_repo,
        output_repo,
    )
    trigger_service = ReportTriggerService(
        session, template_repo, trigger_repo, execution_service
    )
    output_service = ReportOutputService(
        session,
        template_repo,
        output_repo,
        execution_repo,
        output_execution_repo,
        field_repo,
    )

    return {
        "template_service": template_service,
        "field_service": field_service,
        "trigger_service": trigger_service,
        "execution_service": execution_service,
        "output_service": output_service,
    }


def format_table(data: list[dict[str, Any]], fields: list[str] = None) -> str:
    """Format data as a table."""
    if not data:
        return "No data available."

    # Use all fields if none specified
    if fields is None:
        fields = list(data[0].keys())

    # Extract rows
    rows = [[item.get(field, "") for field in fields] for item in data]

    # Format the table
    return tabulate.tabulate(rows, headers=fields, tablefmt="grid")


def format_dict(data: dict[str, Any]) -> str:
    """Format a dictionary as key-value pairs."""
    if not data:
        return "No data available."

    # Format the dictionary
    result = []
    for key, value in data.items():
        if isinstance(value, dict):
            value = json.dumps(value, indent=2)
        result.append(f"{key}: {value}")

    return "\n".join(result)


async def handle_templates(args: dict[str, Any], session: AsyncSession) -> None:
    """Handle templates commands."""
    services = create_services(session)
    template_service = services["template_service"]

    if args["list"]:
        result = await template_service.list_templates()
        if result.is_success:
            templates = [t.model_dump() for t in result.value]
            print(
                format_table(
                    templates,
                    ["id", "name", "base_object_type", "version", "created_at"],
                )
            )
        else:
            print(f"Error: {result.error}")

    elif args["get"]:
        template_id = args["<template_id>"]
        result = await template_service.get_template(template_id)
        if result.is_success and result.value:
            print(format_dict(result.value.model_dump()))
        elif result.is_success:
            print(f"Template with ID {template_id} not found.")
        else:
            print(f"Error: {result.error}")

    elif args["create"]:
        template_data = {
            "name": args["<name>"],
            "description": args["<description>"],
            "base_object_type": args["<base_object_type>"],
            "format_config": {
                "title_format": "{name} - Generated on {date}",
                "show_footer": True,
            },
            "parameter_definitions": {},
            "cache_policy": {"ttl_seconds": 3600},
            "version": "1.0.0",
        }
        result = await template_service.create_template(template_data)
        if result.is_success:
            print(f"Template created successfully with ID: {result.value.id}")
        else:
            print(f"Error: {result.error}")

    elif args["update"]:
        template_id = args["<template_id>"]
        template_data = {}
        if args["--name"]:
            template_data["name"] = args["--name"]
        if args["--description"]:
            template_data["description"] = args["--description"]
        if args["--base_object_type"]:
            template_data["base_object_type"] = args["--base_object_type"]

        if not template_data:
            print("No update data provided.")
            return

        result = await template_service.update_template(template_id, template_data)
        if result.is_success:
            print(f"Template {template_id} updated successfully.")
        else:
            print(f"Error: {result.error}")

    elif args["delete"]:
        template_id = args["<template_id>"]
        result = await template_service.delete_template(template_id)
        if result.is_success:
            print(f"Template {template_id} deleted successfully.")
        else:
            print(f"Error: {result.error}")

    elif args["clone"]:
        template_id = args["<template_id>"]
        new_name = args["<new_name>"]
        result = await template_service.clone_template(template_id, new_name)
        if result.is_success:
            print(f"Template cloned successfully with ID: {result.value.id}")
        else:
            print(f"Error: {result.error}")


async def handle_fields(args: dict[str, Any], session: AsyncSession) -> None:
    """Handle fields commands."""
    services = create_services(session)
    field_service = services["field_service"]

    if args["list"]:
        template_id = args["<template_id>"]
        result = await field_service.list_fields_by_template(template_id)
        if result.is_success:
            fields = [f.model_dump() for f in result.value]
            print(
                format_table(
                    fields,
                    ["id", "name", "display_name", "field_type", "order", "is_visible"],
                )
            )
        else:
            print(f"Error: {result.error}")

    elif args["get"]:
        field_id = args["<field_id>"]
        result = await field_service.get_field_by_id(field_id)
        if result.is_success and result.value:
            print(format_dict(result.value.model_dump()))
        elif result.is_success:
            print(f"Field with ID {field_id} not found.")
        else:
            print(f"Error: {result.error}")

    elif args["add"]:
        field_data = {
            "name": args["<name>"],
            "display_name": args["<display_name>"],
            "field_type": args["<field_type>"],
            "order": 0,
            "is_visible": True,
        }

        if args["--config"]:
            try:
                field_data["field_config"] = json.loads(args["--config"])
            except json.JSONDecodeError:
                print("Error: Invalid JSON in field configuration.")
                return

        template_id = args["<template_id>"]
        result = await field_service.add_field(template_id, field_data)
        if result.is_success:
            print(f"Field added successfully with ID: {result.value.id}")
        else:
            print(f"Error: {result.error}")

    elif args["update"]:
        field_id = args["<field_id>"]
        field_data = {}
        if args["--name"]:
            field_data["name"] = args["--name"]
        if args["--display_name"]:
            field_data["display_name"] = args["--display_name"]
        if args["--config"]:
            try:
                field_data["field_config"] = json.loads(args["--config"])
            except json.JSONDecodeError:
                print("Error: Invalid JSON in field configuration.")
                return

        if not field_data:
            print("No update data provided.")
            return

        result = await field_service.update_field(field_id, field_data)
        if result.is_success:
            print(f"Field {field_id} updated successfully.")
        else:
            print(f"Error: {result.error}")

    elif args["delete"]:
        field_id = args["<field_id>"]
        result = await field_service.delete_field(field_id)
        if result.is_success:
            print(f"Field {field_id} deleted successfully.")
        else:
            print(f"Error: {result.error}")


async def handle_triggers(args: dict[str, Any], session: AsyncSession) -> None:
    """Handle triggers commands."""
    services = create_services(session)
    trigger_service = services["trigger_service"]

    if args["list"]:
        template_id = args["<template_id>"]
        result = await trigger_service.list_triggers_by_template(template_id)
        if result.is_success:
            triggers = [t.model_dump() for t in result.value]
            print(
                format_table(
                    triggers,
                    ["id", "trigger_type", "schedule", "is_active", "last_triggered"],
                )
            )
        else:
            print(f"Error: {result.error}")

    elif args["get"]:
        trigger_id = args["<trigger_id>"]
        result = await trigger_service.trigger_repository.get_by_id(trigger_id)
        if result.is_success and result.value:
            print(format_dict(result.value.model_dump()))
        elif result.is_success:
            print(f"Trigger with ID {trigger_id} not found.")
        else:
            print(f"Error: {result.error}")

    elif args["add"]:
        trigger_data = {"trigger_type": args["<trigger_type>"], "is_active": True}

        if args["--config"]:
            try:
                trigger_data["trigger_config"] = json.loads(args["--config"])
            except json.JSONDecodeError:
                print("Error: Invalid JSON in trigger configuration.")
                return

        if args["--schedule"]:
            trigger_data["schedule"] = args["--schedule"]

        template_id = args["<template_id>"]
        result = await trigger_service.create_trigger(template_id, trigger_data)
        if result.is_success:
            print(f"Trigger added successfully with ID: {result.value.id}")
        else:
            print(f"Error: {result.error}")

    elif args["update"]:
        trigger_id = args["<trigger_id>"]
        trigger_data = {}
        if args["--config"]:
            try:
                trigger_data["trigger_config"] = json.loads(args["--config"])
            except json.JSONDecodeError:
                print("Error: Invalid JSON in trigger configuration.")
                return

        if args["--schedule"]:
            trigger_data["schedule"] = args["--schedule"]

        if args["--active"]:
            trigger_data["is_active"] = args["--active"].lower() == "true"

        if not trigger_data:
            print("No update data provided.")
            return

        result = await trigger_service.update_trigger(trigger_id, trigger_data)
        if result.is_success:
            print(f"Trigger {trigger_id} updated successfully.")
        else:
            print(f"Error: {result.error}")

    elif args["delete"]:
        trigger_id = args["<trigger_id>"]
        result = await trigger_service.delete_trigger(trigger_id)
        if result.is_success:
            print(f"Trigger {trigger_id} deleted successfully.")
        else:
            print(f"Error: {result.error}")

    elif args["enable"]:
        trigger_id = args["<trigger_id>"]
        result = await trigger_service.enable_trigger(trigger_id)
        if result.is_success:
            print(f"Trigger {trigger_id} enabled successfully.")
        else:
            print(f"Error: {result.error}")

    elif args["disable"]:
        trigger_id = args["<trigger_id>"]
        result = await trigger_service.disable_trigger(trigger_id)
        if result.is_success:
            print(f"Trigger {trigger_id} disabled successfully.")
        else:
            print(f"Error: {result.error}")


async def handle_outputs(args: dict[str, Any], session: AsyncSession) -> None:
    """Handle outputs commands."""
    services = create_services(session)
    output_service = services["output_service"]

    if args["list"]:
        template_id = args["<template_id>"]
        result = await output_service.list_outputs_by_template(template_id)
        if result.is_success:
            outputs = [o.model_dump() for o in result.value]
            print(format_table(outputs, ["id", "output_type", "format", "is_active"]))
        else:
            print(f"Error: {result.error}")

    elif args["get"]:
        output_id = args["<output_id>"]
        result = await output_service.output_repository.get_by_id(output_id)
        if result.is_success and result.value:
            print(format_dict(result.value.model_dump()))
        elif result.is_success:
            print(f"Output with ID {output_id} not found.")
        else:
            print(f"Error: {result.error}")

    elif args["add"]:
        output_data = {
            "output_type": args["<output_type>"],
            "format": args["<format>"],
            "is_active": True,
        }

        if args["--config"]:
            try:
                output_data["output_config"] = json.loads(args["--config"])
            except json.JSONDecodeError:
                print("Error: Invalid JSON in output configuration.")
                return

        template_id = args["<template_id>"]
        result = await output_service.create_output_config(template_id, output_data)
        if result.is_success:
            print(f"Output configuration added successfully with ID: {result.value.id}")
        else:
            print(f"Error: {result.error}")

    elif args["update"]:
        output_id = args["<output_id>"]
        output_data = {}
        if args["--output_type"]:
            output_data["output_type"] = args["--output_type"]
        if args["--format"]:
            output_data["format"] = args["--format"]
        if args["--config"]:
            try:
                output_data["output_config"] = json.loads(args["--config"])
            except json.JSONDecodeError:
                print("Error: Invalid JSON in output configuration.")
                return

        if not output_data:
            print("No update data provided.")
            return

        result = await output_service.update_output_config(output_id, output_data)
        if result.is_success:
            print(f"Output configuration {output_id} updated successfully.")
        else:
            print(f"Error: {result.error}")

    elif args["delete"]:
        output_id = args["<output_id>"]
        result = await output_service.delete_output_config(output_id)
        if result.is_success:
            print(f"Output configuration {output_id} deleted successfully.")
        else:
            print(f"Error: {result.error}")


async def handle_executions(args: dict[str, Any], session: AsyncSession) -> None:
    """Handle executions commands."""
    services = create_services(session)
    execution_service = services["execution_service"]

    if args["execute"]:
        template_id = args["<template_id>"]
        parameters = {}
        trigger_type = args["--trigger_type"] or "manual"
        user_id = args["--user_id"] or os.getenv("USER", "cli_user")

        if args["--parameters"]:
            try:
                parameters = json.loads(args["--parameters"])
            except json.JSONDecodeError:
                print("Error: Invalid JSON in parameters.")
                return

        result = await execution_service.execute_report(
            template_id,
            parameters=parameters,
            trigger_type=trigger_type,
            user_id=user_id,
        )

        if result.is_success:
            print(f"Report execution started with ID: {result.value.id}")
            print(f"Status: {result.value.status}")
        else:
            print(f"Error: {result.error}")

    elif args["list"]:
        template_id = args["<template_id>"]
        status = args["--status"]
        limit = int(args["--limit"]) if args["--limit"] else 10

        result = await execution_service.list_executions(
            template_id, status=status, limit=limit
        )

        if result.is_success:
            executions = [e.model_dump() for e in result.value]
            print(
                format_table(
                    executions,
                    [
                        "id",
                        "status",
                        "triggered_by",
                        "trigger_type",
                        "started_at",
                        "completed_at",
                        "row_count",
                    ],
                )
            )
        else:
            print(f"Error: {result.error}")

    elif args["get"]:
        execution_id = args["<execution_id>"]
        result = await execution_service.get_execution_status(execution_id)

        if result.is_success:
            print(format_dict(result.value))
        else:
            print(f"Error: {result.error}")

    elif args["cancel"]:
        execution_id = args["<execution_id>"]
        result = await execution_service.cancel_execution(execution_id)

        if result.is_success:
            print(f"Execution {execution_id} cancelled successfully.")
        else:
            print(f"Error: {result.error}")

    elif args["result"]:
        execution_id = args["<execution_id>"]
        format_type = args["--format"] or "json"
        output_file = args["--output"]

        result = await execution_service.get_execution_result(
            execution_id, format=format_type
        )

        if result.is_success:
            if output_file:
                with open(output_file, "w") as f:
                    f.write(str(result.value))
                print(f"Result saved to {output_file}")
            else:
                print(result.value)
        else:
            print(f"Error: {result.error}")


async def handle_scheduler(args: dict[str, Any], session: AsyncSession) -> None:
    """Handle scheduler commands."""
    services = create_services(session)
    trigger_service = services["trigger_service"]

    if args["run"]:
        result = await trigger_service.process_scheduled_triggers()

        if result.is_success:
            if result.value:
                print(f"Processed {len(result.value)} scheduled reports.")
                for execution_id in result.value:
                    print(f"  - Execution ID: {execution_id}")
            else:
                print("No reports were due for execution.")
        else:
            print(f"Error: {result.error}")


async def handle_event(args: dict[str, Any], session: AsyncSession) -> None:
    """Handle event commands."""
    services = create_services(session)
    trigger_service = services["trigger_service"]

    if args["trigger"]:
        event_type = args["<event_type>"]

        try:
            event_data = json.loads(args["<event_data_json>"])
        except json.JSONDecodeError:
            print("Error: Invalid JSON in event data.")
            return

        result = await trigger_service.handle_event(event_type, event_data)

        if result.is_success:
            if result.value:
                print(f"Event triggered {len(result.value)} reports.")
                for execution_id in result.value:
                    print(f"  - Execution ID: {execution_id}")
            else:
                print("No reports were triggered by this event.")
        else:
            print(f"Error: {result.error}")


async def main() -> None:
    """Main entry point for the CLI."""
    args = docopt.docopt(__doc__)

    # Initialize dependency injection container
    UnoContainer.configure()

    # Get async session maker
    session_maker = UnoContainer.get_instance().get(UnoAsyncSessionMaker)

    async with session_maker() as session:
        if args["templates"]:
            await handle_templates(args, session)
        elif args["fields"]:
            await handle_fields(args, session)
        elif args["triggers"]:
            await handle_triggers(args, session)
        elif args["outputs"]:
            await handle_outputs(args, session)
        elif args["execute"] or args["executions"]:
            await handle_executions(args, session)
        elif args["scheduler"]:
            await handle_scheduler(args, session)
        elif args["event"]:
            await handle_event(args, session)


if __name__ == "__main__":
    asyncio.run(main())
