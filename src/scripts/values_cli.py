#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Command-line interface tool for working with values.

This script provides CLI commands for managing values of different types,
allowing users to create, get, convert, and delete values from the command line.
"""

import sys
import argparse
import asyncio
import json
import os
from decimal import Decimal
from datetime import date, datetime, time
from typing import List, Optional, Dict, Any, Type, Union
import logging

from uno.database.db_manager import DBManager
from uno.values import (
    BooleanValueRepository,
    TextValueRepository,
    IntegerValueRepository,
    DecimalValueRepository,
    DateValueRepository,
    DateTimeValueRepository,
    TimeValueRepository,
    AttachmentRepository,
    ValueService,
    BooleanValue,
    TextValue,
    IntegerValue,
    DecimalValue,
    DateValue,
    DateTimeValue,
    TimeValue,
    Attachment,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ValueCLI:
    """CLI tool for managing values."""
    
    def __init__(self):
        """Initialize the CLI tool with required services."""
        self.db_manager = DBManager()
        
        # Initialize repositories
        self.boolean_repository = BooleanValueRepository(self.db_manager)
        self.text_repository = TextValueRepository(self.db_manager)
        self.integer_repository = IntegerValueRepository(self.db_manager)
        self.decimal_repository = DecimalValueRepository(self.db_manager)
        self.date_repository = DateValueRepository(self.db_manager)
        self.datetime_repository = DateTimeValueRepository(self.db_manager)
        self.time_repository = TimeValueRepository(self.db_manager)
        self.attachment_repository = AttachmentRepository(self.db_manager)
        
        # Initialize service
        self.value_service = ValueService(
            boolean_repository=self.boolean_repository,
            text_repository=self.text_repository,
            integer_repository=self.integer_repository,
            decimal_repository=self.decimal_repository,
            date_repository=self.date_repository,
            datetime_repository=self.datetime_repository,
            time_repository=self.time_repository,
            attachment_repository=self.attachment_repository,
            db_manager=self.db_manager,
            logger=logger
        )
    
    def _get_value_type_class(self, value_type: str) -> Type:
        """Get the value type class for a value type string."""
        value_type_mapping = {
            "boolean": BooleanValue,
            "text": TextValue,
            "integer": IntegerValue,
            "decimal": DecimalValue,
            "date": DateValue,
            "datetime": DateTimeValue,
            "time": TimeValue,
            "attachment": Attachment
        }
        
        if value_type.lower() not in value_type_mapping:
            logger.error(f"Invalid value type: {value_type}")
            logger.error(f"Valid types are: {', '.join(value_type_mapping.keys())}")
            sys.exit(1)
        
        return value_type_mapping[value_type.lower()]
    
    def _get_repository(self, value_type: str):
        """Get the repository for a value type string."""
        value_type_class = self._get_value_type_class(value_type)
        repository = self.value_service._get_repository(value_type_class)
        
        if not repository:
            logger.error(f"No repository found for value type {value_type}")
            sys.exit(1)
        
        return repository
    
    def _parse_value(self, value_type: str, value_str: str) -> Any:
        """Parse a value string based on the value type."""
        try:
            if value_type.lower() == "boolean":
                return value_str.lower() in ("true", "yes", "1", "y", "t")
            elif value_type.lower() == "integer":
                return int(value_str)
            elif value_type.lower() == "text":
                return value_str
            elif value_type.lower() == "decimal":
                return Decimal(value_str)
            elif value_type.lower() == "date":
                return date.fromisoformat(value_str)
            elif value_type.lower() == "datetime":
                return datetime.fromisoformat(value_str)
            elif value_type.lower() == "time":
                return time.fromisoformat(value_str)
            else:
                return value_str
        except Exception as e:
            logger.error(f"Error parsing value: {e}")
            sys.exit(1)
    
    async def create_value(self, args):
        """Create a new value."""
        # Get value type class
        value_type_class = self._get_value_type_class(args.value_type)
        
        # Parse the value
        parsed_value = self._parse_value(args.value_type, args.value)
        
        # Create value
        result = await self.value_service.create_value(
            value_type_class,
            parsed_value,
            args.name
        )
        
        if result.is_ok():
            value_obj = result.unwrap()
            print(f"Successfully created {args.value_type} value with ID: {value_obj.id}")
            print(json.dumps({
                "id": value_obj.id,
                "name": value_obj.name,
                "value": str(value_obj.value),
                "value_type": args.value_type,
                "created_at": value_obj.created_at.isoformat() if value_obj.created_at else None
            }, indent=2))
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to create value: {error}")
            sys.exit(1)
    
    async def get_or_create_value(self, args):
        """Get a value by its value, or create it if it doesn't exist."""
        # Get value type class
        value_type_class = self._get_value_type_class(args.value_type)
        
        # Parse the value
        parsed_value = self._parse_value(args.value_type, args.value)
        
        # Get or create value
        result = await self.value_service.get_or_create_value(
            value_type_class,
            parsed_value,
            args.name
        )
        
        if result.is_ok():
            value_obj = result.unwrap()
            print(f"Successfully got or created {args.value_type} value with ID: {value_obj.id}")
            print(json.dumps({
                "id": value_obj.id,
                "name": value_obj.name,
                "value": str(value_obj.value),
                "value_type": args.value_type,
                "created_at": value_obj.created_at.isoformat() if value_obj.created_at else None
            }, indent=2))
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to get or create value: {error}")
            sys.exit(1)
    
    async def get_value(self, args):
        """Get a value by ID."""
        # Get value type class
        value_type_class = self._get_value_type_class(args.value_type)
        
        # Get value
        result = await self.value_service.get_value_by_id(value_type_class, args.id)
        
        if result.is_ok():
            value_obj = result.unwrap()
            
            if not value_obj:
                logger.error(f"{args.value_type.capitalize()} value with ID {args.id} not found")
                sys.exit(1)
            
            print(f"Found {args.value_type} value with ID {value_obj.id}:")
            
            if args.value_type.lower() == "attachment":
                print(json.dumps({
                    "id": value_obj.id,
                    "name": value_obj.name,
                    "file_path": value_obj.file_path,
                    "value_type": "attachment",
                    "created_at": value_obj.created_at.isoformat() if value_obj.created_at else None,
                    "updated_at": value_obj.updated_at.isoformat() if value_obj.updated_at else None
                }, indent=2))
            else:
                print(json.dumps({
                    "id": value_obj.id,
                    "name": value_obj.name,
                    "value": str(value_obj.value),
                    "value_type": args.value_type,
                    "created_at": value_obj.created_at.isoformat() if value_obj.created_at else None,
                    "updated_at": value_obj.updated_at.isoformat() if value_obj.updated_at else None
                }, indent=2))
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to get value: {error}")
            sys.exit(1)
    
    async def convert_value(self, args):
        """Convert a value to a different type."""
        # Get source and target value type classes
        source_value_type_class = self._get_value_type_class(args.source_type)
        target_value_type_class = self._get_value_type_class(args.target_type)
        
        # Parse the value
        parsed_value = self._parse_value(args.source_type, args.value)
        
        # Validate the value
        validation_result = await self.value_service.validate_value(source_value_type_class, parsed_value)
        
        if validation_result.is_err():
            error = validation_result.unwrap_err()
            logger.error(f"Validation failed: {error}")
            sys.exit(1)
        
        # Convert the value
        convert_result = await self.value_service.convert_value(parsed_value, target_value_type_class)
        
        if convert_result.is_ok():
            converted_value = convert_result.unwrap()
            print(f"Successfully converted {args.source_type} value to {args.target_type}:")
            print(f"Original value ({args.source_type}): {parsed_value}")
            print(f"Converted value ({args.target_type}): {converted_value}")
        else:
            error = convert_result.unwrap_err()
            logger.error(f"Failed to convert value: {error}")
            sys.exit(1)
    
    async def upload_attachment(self, args):
        """Upload a file attachment."""
        # Check if file exists
        if not os.path.exists(args.file_path):
            logger.error(f"File not found: {args.file_path}")
            sys.exit(1)
        
        # Create attachment
        result = await self.value_service.create_attachment(args.file_path, args.name)
        
        if result.is_ok():
            attachment = result.unwrap()
            print(f"Successfully uploaded attachment with ID: {attachment.id}")
            print(json.dumps({
                "id": attachment.id,
                "name": attachment.name,
                "file_path": attachment.file_path,
                "value_type": "attachment",
                "created_at": attachment.created_at.isoformat() if attachment.created_at else None
            }, indent=2))
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to upload attachment: {error}")
            sys.exit(1)
    
    async def delete_value(self, args):
        """Delete a value by ID."""
        # Get repository
        repository = self._get_repository(args.value_type)
        
        # Delete value
        result = await repository.delete(args.id)
        
        if result.is_ok():
            success = result.unwrap()
            
            if success:
                print(f"Successfully deleted {args.value_type} value with ID {args.id}")
            else:
                logger.error(f"{args.value_type.capitalize()} value with ID {args.id} not found")
                sys.exit(1)
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to delete value: {error}")
            sys.exit(1)
    
    async def search_values(self, args):
        """Search for values matching a term."""
        # Get repository
        repository = self._get_repository(args.value_type)
        
        # Search values
        result = await repository.search(args.term, args.limit)
        
        if result.is_ok():
            values = result.unwrap()
            print(f"Found {len(values)} {args.value_type} values matching '{args.term}':")
            
            for idx, value_obj in enumerate(values, 1):
                if args.value_type.lower() == "attachment":
                    print(f"{idx}. {value_obj.name} (ID: {value_obj.id})")
                    print(f"   File path: {value_obj.file_path}")
                else:
                    print(f"{idx}. {value_obj.name} (ID: {value_obj.id})")
                    print(f"   Value: {value_obj.value}")
                print()
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to search values: {error}")
            sys.exit(1)


def setup_parser():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(
        description="Command-line tool for managing values of different types"
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create value
    create_parser = subparsers.add_parser("create", help="Create a new value")
    create_parser.add_argument("--value-type", required=True, choices=["boolean", "integer", "text", "decimal", "date", "datetime", "time"], help="Type of value to create")
    create_parser.add_argument("--value", required=True, help="The actual value")
    create_parser.add_argument("--name", help="Optional name for the value")
    create_parser.set_defaults(func=lambda cli, args: cli.create_value(args))
    
    # Get or create value
    get_or_create_parser = subparsers.add_parser("get-or-create", help="Get a value by its value, or create it if it doesn't exist")
    get_or_create_parser.add_argument("--value-type", required=True, choices=["boolean", "integer", "text", "decimal", "date", "datetime", "time"], help="Type of value to get or create")
    get_or_create_parser.add_argument("--value", required=True, help="The actual value")
    get_or_create_parser.add_argument("--name", help="Optional name for the value if it needs to be created")
    get_or_create_parser.set_defaults(func=lambda cli, args: cli.get_or_create_value(args))
    
    # Get value
    get_parser = subparsers.add_parser("get", help="Get a value by ID")
    get_parser.add_argument("--value-type", required=True, choices=["boolean", "integer", "text", "decimal", "date", "datetime", "time", "attachment"], help="Type of value to get")
    get_parser.add_argument("--id", required=True, help="ID of the value")
    get_parser.set_defaults(func=lambda cli, args: cli.get_value(args))
    
    # Convert value
    convert_parser = subparsers.add_parser("convert", help="Convert a value to a different type")
    convert_parser.add_argument("--source-type", required=True, choices=["boolean", "integer", "text", "decimal", "date", "datetime", "time"], help="Source type of value")
    convert_parser.add_argument("--target-type", required=True, choices=["boolean", "integer", "text", "decimal", "date", "datetime", "time"], help="Target type to convert to")
    convert_parser.add_argument("--value", required=True, help="The value to convert")
    convert_parser.set_defaults(func=lambda cli, args: cli.convert_value(args))
    
    # Upload attachment
    upload_parser = subparsers.add_parser("upload", help="Upload a file attachment")
    upload_parser.add_argument("--file-path", required=True, help="Path to the file")
    upload_parser.add_argument("--name", required=True, help="Name of the attachment")
    upload_parser.set_defaults(func=lambda cli, args: cli.upload_attachment(args))
    
    # Delete value
    delete_parser = subparsers.add_parser("delete", help="Delete a value by ID")
    delete_parser.add_argument("--value-type", required=True, choices=["boolean", "integer", "text", "decimal", "date", "datetime", "time", "attachment"], help="Type of value to delete")
    delete_parser.add_argument("--id", required=True, help="ID of the value to delete")
    delete_parser.set_defaults(func=lambda cli, args: cli.delete_value(args))
    
    # Search values
    search_parser = subparsers.add_parser("search", help="Search for values matching a term")
    search_parser.add_argument("--value-type", required=True, choices=["boolean", "integer", "text", "decimal", "date", "datetime", "time", "attachment"], help="Type of value to search")
    search_parser.add_argument("--term", required=True, help="Search term")
    search_parser.add_argument("--limit", type=int, default=20, help="Maximum number of results (default: 20)")
    search_parser.set_defaults(func=lambda cli, args: cli.search_values(args))
    
    return parser


async def main():
    """Run the CLI tool."""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not hasattr(args, "command") or not args.command or not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    
    # Run the command
    cli = ValueCLI()
    
    try:
        await args.func(cli, args)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())