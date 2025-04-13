#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Command-line interface tool for working with attributes.

This script provides CLI commands for managing attribute types and attributes,
allowing users to create, list, update, and delete them from the command line.
"""

import sys
import argparse
import asyncio
import json
from typing import List, Optional, Dict, Any
import logging

from uno.database.db_manager import DBManager
from uno.attributes import (
    AttributeRepository,
    AttributeTypeRepository,
    AttributeService,
    AttributeTypeService,
    Attribute,
    AttributeType,
)
from uno.meta.objs import MetaType, MetaRecord


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AttributeCLI:
    """CLI tool for managing attributes and attribute types."""
    
    def __init__(self):
        """Initialize the CLI tool with required services."""
        self.db_manager = DBManager()
        self.attribute_repository = AttributeRepository(self.db_manager)
        self.attribute_type_repository = AttributeTypeRepository(self.db_manager)
        self.attribute_service = AttributeService(
            attribute_repository=self.attribute_repository,
            attribute_type_repository=self.attribute_type_repository,
            db_manager=self.db_manager,
            logger=logger
        )
        self.attribute_type_service = AttributeTypeService(
            attribute_type_repository=self.attribute_type_repository,
            db_manager=self.db_manager,
            logger=logger
        )
    
    async def create_attribute_type(self, args):
        """Create a new attribute type."""
        # Parse metadata ids if provided
        applicable_meta_types = None
        if args.meta_type_ids:
            applicable_meta_types = []
            for meta_type_id in args.meta_type_ids:
                meta_type = await MetaType.get(meta_type_id)
                if meta_type:
                    applicable_meta_types.append(meta_type)
                else:
                    logger.warning(f"Meta type with ID {meta_type_id} not found")
        
        # Parse value type ids if provided
        value_meta_types = None
        if args.value_type_ids:
            value_meta_types = []
            for meta_type_id in args.value_type_ids:
                meta_type = await MetaType.get(meta_type_id)
                if meta_type:
                    value_meta_types.append(meta_type)
                else:
                    logger.warning(f"Meta type with ID {meta_type_id} not found")
        
        # Create attribute type object
        attribute_type = AttributeType(
            name=args.name,
            text=args.text,
            parent_id=args.parent_id,
            required=args.required,
            multiple_allowed=args.multiple_allowed,
            comment_required=args.comment_required,
            display_with_objects=args.display_with_objects,
            initial_comment=args.initial_comment
        )
        
        # Create attribute type
        result = await self.attribute_type_service.create_attribute_type(
            attribute_type,
            applicable_meta_types,
            value_meta_types
        )
        
        if result.is_ok():
            created_type = result.unwrap()
            print(f"Successfully created attribute type '{created_type.name}' with ID: {created_type.id}")
            print(json.dumps({
                "id": created_type.id,
                "name": created_type.name,
                "text": created_type.text,
                "required": created_type.required,
                "multiple_allowed": created_type.multiple_allowed,
                "comment_required": created_type.comment_required,
                "display_with_objects": created_type.display_with_objects,
                "created_at": created_type.created_at.isoformat() if created_type.created_at else None
            }, indent=2))
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to create attribute type: {error}")
            sys.exit(1)
    
    async def get_attribute_type(self, args):
        """Get an attribute type by ID."""
        # Get the attribute type
        async with self.db_manager.get_enhanced_session() as session:
            result = await self.attribute_type_repository.get_by_id(args.id, session)
            
            if result.is_ok():
                attribute_type = result.unwrap()
                
                if not attribute_type:
                    logger.error(f"Attribute type with ID {args.id} not found")
                    sys.exit(1)
                
                print(f"Found attribute type '{attribute_type.name}':")
                print(json.dumps({
                    "id": attribute_type.id,
                    "name": attribute_type.name,
                    "text": attribute_type.text,
                    "parent_id": attribute_type.parent_id,
                    "required": attribute_type.required,
                    "multiple_allowed": attribute_type.multiple_allowed,
                    "comment_required": attribute_type.comment_required,
                    "display_with_objects": attribute_type.display_with_objects,
                    "initial_comment": attribute_type.initial_comment,
                    "created_at": attribute_type.created_at.isoformat() if attribute_type.created_at else None,
                    "updated_at": attribute_type.updated_at.isoformat() if attribute_type.updated_at else None,
                    "describes": [{"id": mt.id, "name": mt.name} for mt in attribute_type.describes] if attribute_type.describes else [],
                    "value_types": [{"id": mt.id, "name": mt.name} for mt in attribute_type.value_types] if attribute_type.value_types else []
                }, indent=2))
            else:
                error = result.unwrap_err()
                logger.error(f"Failed to get attribute type: {error}")
                sys.exit(1)
    
    async def list_attribute_types(self, args):
        """List all attribute types or those applicable to a meta type."""
        if args.meta_type_id:
            # Get attribute types applicable to meta type
            result = await self.attribute_type_service.get_applicable_attribute_types(args.meta_type_id)
            
            if result.is_ok():
                attribute_types = result.unwrap()
                print(f"Found {len(attribute_types)} attribute types for meta type {args.meta_type_id}:")
            else:
                error = result.unwrap_err()
                logger.error(f"Failed to get attribute types: {error}")
                sys.exit(1)
        else:
            # Get all attribute types
            async with self.db_manager.get_enhanced_session() as session:
                attribute_types = await AttributeType.filter({}, session=session)
                print(f"Found {len(attribute_types)} attribute types:")
        
        # Display attribute types
        for idx, at in enumerate(attribute_types, 1):
            print(f"{idx}. {at.name} (ID: {at.id}) - {at.text}")
            print(f"   Required: {at.required}, Multiple Allowed: {at.multiple_allowed}")
            if at.describes:
                print(f"   Applicable to: {', '.join(mt.name for mt in at.describes)}")
            print()
    
    async def delete_attribute_type(self, args):
        """Delete an attribute type by ID."""
        # Delete the attribute type
        async with self.db_manager.get_enhanced_session() as session:
            result = await self.attribute_type_repository.delete(args.id, session)
            
            if result.is_ok():
                success = result.unwrap()
                
                if success:
                    print(f"Successfully deleted attribute type with ID {args.id}")
                else:
                    logger.error(f"Attribute type with ID {args.id} not found")
                    sys.exit(1)
            else:
                error = result.unwrap_err()
                logger.error(f"Failed to delete attribute type: {error}")
                sys.exit(1)
    
    async def create_attribute(self, args):
        """Create a new attribute."""
        # Parse value ids if provided
        values = None
        if args.value_ids:
            values = []
            for value_id in args.value_ids:
                value = await MetaRecord.get(value_id)
                if value:
                    values.append(value)
                else:
                    logger.warning(f"Value with ID {value_id} not found")
        
        # Create attribute object
        attribute = Attribute(
            attribute_type_id=args.attribute_type_id,
            comment=args.comment,
            follow_up_required=args.follow_up_required
        )
        
        # Create attribute
        result = await self.attribute_service.create_attribute(attribute, values)
        
        if result.is_ok():
            created_attribute = result.unwrap()
            print(f"Successfully created attribute with ID: {created_attribute.id}")
            print(json.dumps({
                "id": created_attribute.id,
                "attribute_type_id": created_attribute.attribute_type_id,
                "comment": created_attribute.comment,
                "follow_up_required": created_attribute.follow_up_required,
                "created_at": created_attribute.created_at.isoformat() if created_attribute.created_at else None,
                "values": [{"id": v.id, "name": getattr(v, "name", None)} for v in created_attribute.values] if created_attribute.values else []
            }, indent=2))
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to create attribute: {error}")
            sys.exit(1)
    
    async def get_attribute(self, args):
        """Get an attribute by ID."""
        # Get the attribute
        async with self.db_manager.get_enhanced_session() as session:
            result = await self.attribute_repository.get_by_id(args.id, session)
            
            if result.is_ok():
                attribute = result.unwrap()
                
                if not attribute:
                    logger.error(f"Attribute with ID {args.id} not found")
                    sys.exit(1)
                
                print(f"Found attribute with ID {attribute.id}:")
                print(json.dumps({
                    "id": attribute.id,
                    "attribute_type_id": attribute.attribute_type_id,
                    "comment": attribute.comment,
                    "follow_up_required": attribute.follow_up_required,
                    "created_at": attribute.created_at.isoformat() if attribute.created_at else None,
                    "updated_at": attribute.updated_at.isoformat() if attribute.updated_at else None,
                    "values": [{"id": v.id, "name": getattr(v, "name", None)} for v in attribute.values] if attribute.values else []
                }, indent=2))
            else:
                error = result.unwrap_err()
                logger.error(f"Failed to get attribute: {error}")
                sys.exit(1)
    
    async def add_values(self, args):
        """Add values to an attribute."""
        # Parse value ids
        values = []
        for value_id in args.value_ids:
            value = await MetaRecord.get(value_id)
            if value:
                values.append(value)
            else:
                logger.warning(f"Value with ID {value_id} not found")
        
        if not values:
            logger.error("No valid values found to add")
            sys.exit(1)
        
        # Add values
        result = await self.attribute_service.add_values(args.id, values)
        
        if result.is_ok():
            updated_attribute = result.unwrap()
            print(f"Successfully added values to attribute with ID {updated_attribute.id}")
            print(f"Added {len(values)} values. Attribute now has {len(updated_attribute.values) if updated_attribute.values else 0} values.")
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to add values to attribute: {error}")
            sys.exit(1)
    
    async def remove_values(self, args):
        """Remove values from an attribute."""
        # Remove values
        result = await self.attribute_service.remove_values(args.id, args.value_ids)
        
        if result.is_ok():
            updated_attribute = result.unwrap()
            print(f"Successfully removed values from attribute with ID {updated_attribute.id}")
            print(f"Attribute now has {len(updated_attribute.values) if updated_attribute.values else 0} values.")
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to remove values from attribute: {error}")
            sys.exit(1)
    
    async def get_attributes_for_record(self, args):
        """Get all attributes for a record."""
        # Get attributes
        result = await self.attribute_service.get_attributes_for_record(
            args.record_id,
            include_values=not args.no_values
        )
        
        if result.is_ok():
            attributes = result.unwrap()
            print(f"Found {len(attributes)} attributes for record {args.record_id}:")
            
            for idx, attr in enumerate(attributes, 1):
                print(f"{idx}. Attribute ID: {attr.id}")
                print(f"   Type ID: {attr.attribute_type_id}")
                print(f"   Comment: {attr.comment}")
                
                if not args.no_values and attr.values:
                    print(f"   Values ({len(attr.values)}):")
                    for v_idx, value in enumerate(attr.values, 1):
                        print(f"      {v_idx}. ID: {value.id}, Name: {getattr(value, 'name', None)}")
                print()
        else:
            error = result.unwrap_err()
            logger.error(f"Failed to get attributes for record: {error}")
            sys.exit(1)
    
    async def delete_attribute(self, args):
        """Delete an attribute by ID."""
        # Delete the attribute
        async with self.db_manager.get_enhanced_session() as session:
            result = await self.attribute_repository.delete(args.id, session)
            
            if result.is_ok():
                success = result.unwrap()
                
                if success:
                    print(f"Successfully deleted attribute with ID {args.id}")
                else:
                    logger.error(f"Attribute with ID {args.id} not found")
                    sys.exit(1)
            else:
                error = result.unwrap_err()
                logger.error(f"Failed to delete attribute: {error}")
                sys.exit(1)


def setup_attribute_type_subparsers(subparsers):
    """Set up subparsers for attribute type commands."""
    # Create attribute type
    create_at_parser = subparsers.add_parser("create", help="Create a new attribute type")
    create_at_parser.add_argument("--name", required=True, help="Name of the attribute type")
    create_at_parser.add_argument("--text", required=True, help="Text description of the attribute type")
    create_at_parser.add_argument("--parent-id", help="ID of the parent attribute type")
    create_at_parser.add_argument("--required", action="store_true", help="Whether attributes of this type are required")
    create_at_parser.add_argument("--multiple-allowed", action="store_true", help="Whether multiple values are allowed")
    create_at_parser.add_argument("--comment-required", action="store_true", help="Whether a comment is required")
    create_at_parser.add_argument("--display-with-objects", action="store_true", help="Whether to display with objects")
    create_at_parser.add_argument("--initial-comment", help="Initial comment template")
    create_at_parser.add_argument("--meta-type-ids", nargs="+", help="IDs of meta types this attribute type applies to")
    create_at_parser.add_argument("--value-type-ids", nargs="+", help="IDs of meta types allowed as values")
    create_at_parser.set_defaults(func=lambda cli, args: cli.create_attribute_type(args))
    
    # Get attribute type
    get_at_parser = subparsers.add_parser("get", help="Get an attribute type by ID")
    get_at_parser.add_argument("id", help="ID of the attribute type")
    get_at_parser.set_defaults(func=lambda cli, args: cli.get_attribute_type(args))
    
    # List attribute types
    list_at_parser = subparsers.add_parser("list", help="List attribute types")
    list_at_parser.add_argument("--meta-type-id", help="List attribute types applicable to this meta type")
    list_at_parser.set_defaults(func=lambda cli, args: cli.list_attribute_types(args))
    
    # Delete attribute type
    delete_at_parser = subparsers.add_parser("delete", help="Delete an attribute type")
    delete_at_parser.add_argument("id", help="ID of the attribute type to delete")
    delete_at_parser.set_defaults(func=lambda cli, args: cli.delete_attribute_type(args))


def setup_attribute_subparsers(subparsers):
    """Set up subparsers for attribute commands."""
    # Create attribute
    create_parser = subparsers.add_parser("create", help="Create a new attribute")
    create_parser.add_argument("--attribute-type-id", required=True, help="ID of the attribute type")
    create_parser.add_argument("--comment", help="Comment about the attribute")
    create_parser.add_argument("--follow-up-required", action="store_true", help="Whether follow-up is required")
    create_parser.add_argument("--value-ids", nargs="+", help="IDs of values to associate with the attribute")
    create_parser.set_defaults(func=lambda cli, args: cli.create_attribute(args))
    
    # Get attribute
    get_parser = subparsers.add_parser("get", help="Get an attribute by ID")
    get_parser.add_argument("id", help="ID of the attribute")
    get_parser.set_defaults(func=lambda cli, args: cli.get_attribute(args))
    
    # Add values
    add_values_parser = subparsers.add_parser("add-values", help="Add values to an attribute")
    add_values_parser.add_argument("id", help="ID of the attribute")
    add_values_parser.add_argument("value_ids", nargs="+", help="IDs of values to add")
    add_values_parser.set_defaults(func=lambda cli, args: cli.add_values(args))
    
    # Remove values
    remove_values_parser = subparsers.add_parser("remove-values", help="Remove values from an attribute")
    remove_values_parser.add_argument("id", help="ID of the attribute")
    remove_values_parser.add_argument("value_ids", nargs="+", help="IDs of values to remove")
    remove_values_parser.set_defaults(func=lambda cli, args: cli.remove_values(args))
    
    # Get attributes for record
    get_for_record_parser = subparsers.add_parser("get-for-record", help="Get attributes for a record")
    get_for_record_parser.add_argument("record_id", help="ID of the record")
    get_for_record_parser.add_argument("--no-values", action="store_true", help="Don't include attribute values")
    get_for_record_parser.set_defaults(func=lambda cli, args: cli.get_attributes_for_record(args))
    
    # Delete attribute
    delete_parser = subparsers.add_parser("delete", help="Delete an attribute")
    delete_parser.add_argument("id", help="ID of the attribute to delete")
    delete_parser.set_defaults(func=lambda cli, args: cli.delete_attribute(args))


def setup_parser():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(
        description="Command-line tool for managing attributes and attribute types"
    )
    
    # Create subparsers for top-level commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Attribute types command
    attribute_types_parser = subparsers.add_parser("attribute-types", help="Manage attribute types")
    attribute_types_subparsers = attribute_types_parser.add_subparsers(
        dest="subcommand",
        help="Attribute type command to run"
    )
    setup_attribute_type_subparsers(attribute_types_subparsers)
    
    # Attributes command
    attributes_parser = subparsers.add_parser("attributes", help="Manage attributes")
    attributes_subparsers = attributes_parser.add_subparsers(
        dest="subcommand",
        help="Attribute command to run"
    )
    setup_attribute_subparsers(attributes_subparsers)
    
    return parser


async def main():
    """Run the CLI tool."""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not hasattr(args, "command") or not args.command:
        parser.print_help()
        sys.exit(1)
    
    if not hasattr(args, "subcommand") or not args.subcommand:
        if args.command == "attribute-types":
            parser.parse_args(["attribute-types", "--help"])
        elif args.command == "attributes":
            parser.parse_args(["attributes", "--help"])
        sys.exit(1)
    
    # Run the command
    cli = AttributeCLI()
    
    try:
        await args.func(cli, args)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())