# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Service implementations for schema operations in the DTO module.

This module provides service interfaces and implementations for
managing, validating, and transforming schema definitions.
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable, TypeVar
from datetime import datetime, UTC

from uno.core.base.error import BaseError
from uno.dto.entities import (
    SchemaDefinition, 
    SchemaId, 
    SchemaConfiguration,
    SchemaType,
    FieldDefinition,
    SchemaCreationRequest,
    SchemaUpdateRequest
)
from uno.dto.domain_repositories import (
    SchemaDefinitionRepositoryProtocol,
    SchemaConfigurationRepositoryProtocol
)


# Generic type parameters
SchemaDefT = TypeVar('SchemaDefT', bound=SchemaDefinition)
SchemaConfT = TypeVar('SchemaConfT', bound=SchemaConfiguration)


@runtime_checkable
class SchemaManagerServiceProtocol(Protocol):
    """Protocol for services that manage schema definitions."""
    
    async def create_schema(self, request: SchemaCreationRequest) -> SchemaDefinition:
        """Create a new schema definition."""
        ...
        
    async def update_schema(
        self, schema_id: uuid.UUID, request: SchemaUpdateRequest
    ) -> SchemaDefinition:
        """Update an existing schema definition."""
        ...
        
    async def get_schema(self, schema_id: uuid.UUID) -> Optional[SchemaDefinition]:
        """Get a schema definition by ID."""
        ...
        
    async def get_schema_by_name_version(
        self, name: str, version: str
    ) -> Optional[SchemaDefinition]:
        """Get a schema definition by name and version."""
        ...
        
    async def list_schemas(self, limit: int = 100, offset: int = 0) -> List[SchemaDefinition]:
        """List schema definitions with pagination."""
        ...
        
    async def delete_schema(self, schema_id: uuid.UUID) -> bool:
        """Delete a schema definition by ID."""
        ...
        
    async def set_schema_configuration(
        self, schema_id: uuid.UUID, config: SchemaConfiguration
    ) -> SchemaConfiguration:
        """Set the configuration for a schema."""
        ...
        
    async def get_schema_configuration(
        self, schema_id: uuid.UUID
    ) -> Optional[SchemaConfiguration]:
        """Get the configuration for a schema."""
        ...


@runtime_checkable
class SchemaValidationServiceProtocol(Protocol):
    """Protocol for services that validate data against schema definitions."""
    
    async def validate(
        self, 
        schema: SchemaDefinition,
        data: Dict[str, Any],
        config: Optional[SchemaConfiguration] = None
    ) -> Dict[str, List[str]]:
        """
        Validate data against a schema.
        
        Args:
            schema: The schema to validate against
            data: The data to validate
            config: Optional configuration for validation
            
        Returns:
            Dictionary of validation errors by field name
        """
        ...
        
    async def is_valid(
        self,
        schema: SchemaDefinition,
        data: Dict[str, Any],
        config: Optional[SchemaConfiguration] = None
    ) -> bool:
        """
        Check if data is valid against a schema.
        
        Args:
            schema: The schema to validate against
            data: The data to validate
            config: Optional configuration for validation
            
        Returns:
            True if the data is valid, False otherwise
        """
        ...


@runtime_checkable
class SchemaTransformationServiceProtocol(Protocol):
    """Protocol for services that transform data between different schema formats."""
    
    async def transform(
        self,
        data: Dict[str, Any],
        source_schema: SchemaDefinition,
        target_schema: SchemaDefinition,
        config: Optional[SchemaConfiguration] = None
    ) -> Dict[str, Any]:
        """
        Transform data from one schema to another.
        
        Args:
            data: The data to transform
            source_schema: The source schema
            target_schema: The target schema
            config: Optional configuration for transformation
            
        Returns:
            The transformed data
        """
        ...
        
    async def generate_code(
        self,
        schema: SchemaDefinition,
        language: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate code from a schema.
        
        Args:
            schema: The schema to generate code from
            language: The programming language to generate code for
            config: Optional configuration for code generation
            
        Returns:
            The generated code
        """
        ...


class SchemaManagerService:
    """Service for managing schema definitions."""
    
    def __init__(
        self,
        schema_repository: SchemaDefinitionRepositoryProtocol,
        config_repository: SchemaConfigurationRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            schema_repository: Repository for schema definitions
            config_repository: Repository for schema configurations
            logger: Optional logger instance
        """
        self.schema_repository = schema_repository
        self.config_repository = config_repository
        self.logger = logger or logging.getLogger(__name__)
        
    async def create_schema(self, request: SchemaCreationRequest) -> SchemaDefinition:
        """Create a new schema definition."""
        # Create a schema ID
        schema_id = SchemaId(
            id=uuid.uuid4(),
            name=request.name,
            version=request.version
        )
        
        # Create the schema definition
        schema = SchemaDefinition(
            id=schema_id,
            type=request.type,
            fields=request.fields,
            description=request.description,
            created_at=datetime.now(UTC),
            metadata=request.metadata
        )
        
        # Store the schema
        try:
            return await self.schema_repository.add(schema)
        except Exception as e:
            self.logger.error(f"Error creating schema: {str(e)}")
            raise BaseError(
                f"Failed to create schema: {str(e)}",
                "SCHEMA_CREATION_FAILED",
                schema_name=request.name,
                schema_version=request.version
            )
        
    async def update_schema(
        self, schema_id: uuid.UUID, request: SchemaUpdateRequest
    ) -> SchemaDefinition:
        """Update an existing schema definition."""
        # Get the existing schema
        schema = await self.schema_repository.get_by_id(schema_id)
        if not schema:
            raise BaseError(
                f"Schema with ID {schema_id} not found",
                "SCHEMA_NOT_FOUND",
                schema_id=str(schema_id)
            )
            
        # Update the schema fields
        if request.fields is not None:
            schema.fields = request.fields
            
        # Update other properties
        if request.description is not None:
            schema.description = request.description
            
        if request.metadata is not None:
            schema.metadata = request.metadata or {}
            
        # Update the timestamp
        schema.updated_at = datetime.now(UTC)
        
        # Store the updated schema
        try:
            return await self.schema_repository.update(schema)
        except Exception as e:
            self.logger.error(f"Error updating schema: {str(e)}")
            raise BaseError(
                f"Failed to update schema: {str(e)}",
                "SCHEMA_UPDATE_FAILED",
                schema_id=str(schema_id)
            )
        
    async def get_schema(self, schema_id: uuid.UUID) -> Optional[SchemaDefinition]:
        """Get a schema definition by ID."""
        return await self.schema_repository.get_by_id(schema_id)
        
    async def get_schema_by_name_version(
        self, name: str, version: str
    ) -> Optional[SchemaDefinition]:
        """Get a schema definition by name and version."""
        return await self.schema_repository.get_by_name_version(name, version)
        
    async def list_schemas(self, limit: int = 100, offset: int = 0) -> List[SchemaDefinition]:
        """List schema definitions with pagination."""
        return await self.schema_repository.list_schemas(limit, offset)
        
    async def delete_schema(self, schema_id: uuid.UUID) -> bool:
        """Delete a schema definition by ID."""
        # Delete the schema configuration first
        await self.config_repository.delete(schema_id)
        
        # Then delete the schema
        return await self.schema_repository.delete(schema_id)
        
    async def set_schema_configuration(
        self, schema_id: uuid.UUID, config: SchemaConfiguration
    ) -> SchemaConfiguration:
        """Set the configuration for a schema."""
        # Check if the schema exists
        schema = await self.schema_repository.get_by_id(schema_id)
        if not schema:
            raise BaseError(
                f"Schema with ID {schema_id} not found",
                "SCHEMA_NOT_FOUND",
                schema_id=str(schema_id)
            )
            
        # Check if a configuration already exists
        existing_config = await self.config_repository.get_by_schema_id(schema_id)
        if existing_config:
            return await self.config_repository.update(schema_id, config)
        else:
            return await self.config_repository.add(schema_id, config)
        
    async def get_schema_configuration(
        self, schema_id: uuid.UUID
    ) -> Optional[SchemaConfiguration]:
        """Get the configuration for a schema."""
        return await self.config_repository.get_by_schema_id(schema_id)


class SchemaValidationService:
    """Service for validating data against schema definitions."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the service.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
    async def validate(
        self, 
        schema: SchemaDefinition,
        data: Dict[str, Any],
        config: Optional[SchemaConfiguration] = None
    ) -> Dict[str, List[str]]:
        """
        Validate data against a schema.
        
        Args:
            schema: The schema to validate against
            data: The data to validate
            config: Optional configuration for validation
            
        Returns:
            Dictionary of validation errors by field name
        """
        errors: Dict[str, List[str]] = {}
        config = config or SchemaConfiguration()
        
        # Check for missing required fields
        for field in schema.fields:
            if field.required and field.name not in data:
                if field.name not in errors:
                    errors[field.name] = []
                errors[field.name].append("Field is required")
        
        # Check field types and additional validation
        for field_name, field_value in data.items():
            # Skip unknown fields if allowed
            field = schema.get_field(field_name)
            if not field:
                if not config.allow_additional_fields:
                    if field_name not in errors:
                        errors[field_name] = []
                    errors[field_name].append("Unknown field")
                continue
                
            # Check field type
            if field_value is not None:
                if not self._check_field_type(field, field_value):
                    if field_name not in errors:
                        errors[field_name] = []
                    errors[field_name].append(f"Expected type {field.type}, got {type(field_value).__name__}")
                    
            # Apply additional validators
            if field.validators:
                field_errors = self._apply_validators(field, field_value)
                if field_errors:
                    if field_name not in errors:
                        errors[field_name] = []
                    errors[field_name].extend(field_errors)
        
        return errors
        
    async def is_valid(
        self,
        schema: SchemaDefinition,
        data: Dict[str, Any],
        config: Optional[SchemaConfiguration] = None
    ) -> bool:
        """
        Check if data is valid against a schema.
        
        Args:
            schema: The schema to validate against
            data: The data to validate
            config: Optional configuration for validation
            
        Returns:
            True if the data is valid, False otherwise
        """
        errors = await self.validate(schema, data, config)
        return len(errors) == 0
        
    def _check_field_type(self, field: FieldDefinition, value: Any) -> bool:
        """
        Check if a value matches the expected field type.
        
        Args:
            field: The field definition
            value: The value to check
            
        Returns:
            True if the value matches the expected type, False otherwise
        """
        # Handle different field types
        field_type = field.type.lower()
        
        # Common types
        if field_type == "string" and isinstance(value, str):
            return True
        elif field_type == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        elif field_type == "number" and (isinstance(value, (int, float)) and not isinstance(value, bool)):
            return True
        elif field_type == "boolean" and isinstance(value, bool):
            return True
        elif field_type == "array" and isinstance(value, list):
            return True
        elif field_type == "object" and isinstance(value, dict):
            return True
        elif field_type == "null" and value is None:
            return True
        
        # Special types
        if field_type == "date" and isinstance(value, str):
            # Simple date format check (YYYY-MM-DD)
            import re
            return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", value))
            
        if field_type == "datetime" and isinstance(value, str):
            # Simple ISO datetime format check
            import re
            return bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value))
            
        # Return False for unrecognized types
        return False
        
    def _apply_validators(self, field: FieldDefinition, value: Any) -> List[str]:
        """
        Apply validators to a field value.
        
        Args:
            field: The field definition
            value: The value to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        if not field.validators:
            return errors
            
        for validator in field.validators:
            validator_type = validator.get("type")
            
            if validator_type == "minLength" and isinstance(value, str):
                min_length = validator.get("value", 0)
                if len(value) < min_length:
                    errors.append(f"Value must be at least {min_length} characters long")
            
            elif validator_type == "maxLength" and isinstance(value, str):
                max_length = validator.get("value", float("inf"))
                if len(value) > max_length:
                    errors.append(f"Value must be at most {max_length} characters long")
            
            elif validator_type == "pattern" and isinstance(value, str):
                import re
                pattern = validator.get("value", "")
                if not re.match(pattern, value):
                    errors.append(f"Value does not match the required pattern")
            
            elif validator_type == "minimum" and isinstance(value, (int, float)):
                minimum = validator.get("value", float("-inf"))
                if value < minimum:
                    errors.append(f"Value must be at least {minimum}")
            
            elif validator_type == "maximum" and isinstance(value, (int, float)):
                maximum = validator.get("value", float("inf"))
                if value > maximum:
                    errors.append(f"Value must be at most {maximum}")
            
            elif validator_type == "enum":
                enum_values = validator.get("values", [])
                if value not in enum_values:
                    errors.append(f"Value must be one of: {', '.join(str(v) for v in enum_values)}")
                    
        return errors


class SchemaTransformationService:
    """Service for transforming data between different schema formats."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the service.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
    async def transform(
        self,
        data: Dict[str, Any],
        source_schema: SchemaDefinition,
        target_schema: SchemaDefinition,
        config: Optional[SchemaConfiguration] = None
    ) -> Dict[str, Any]:
        """
        Transform data from one schema to another.
        
        Args:
            data: The data to transform
            source_schema: The source schema
            target_schema: The target schema
            config: Optional configuration for transformation
            
        Returns:
            The transformed data
        """
        result: Dict[str, Any] = {}
        config = config or SchemaConfiguration()
        
        # Build a mapping of source to target fields
        field_mapping: Dict[str, str] = {}
        for target_field in target_schema.fields:
            # Try to find a matching source field
            source_field = source_schema.get_field(target_field.name)
            if source_field:
                field_mapping[target_field.name] = target_field.name
            else:
                # Check for field mapping in configuration
                if config.field_policies and target_field.name in config.field_policies:
                    mapping = config.field_policies[target_field.name].get("mapping")
                    if mapping:
                        field_mapping[target_field.name] = mapping
        
        # Transform fields using the mapping
        for target_field_name, source_field_name in field_mapping.items():
            if source_field_name in data:
                # Get the field definitions
                target_field = target_schema.get_field(target_field_name)
                source_field = source_schema.get_field(source_field_name)
                
                if not target_field or not source_field:
                    continue
                    
                # Get the field value
                value = data[source_field_name]
                
                # Transform the value if needed
                transformed_value = self._transform_value(
                    value, source_field, target_field, config
                )
                
                # Add to the result
                result[target_field_name] = transformed_value
                
        # Add default values for missing fields
        for field in target_schema.fields:
            if field.name not in result and field.default is not None:
                result[field.name] = field.default
                
        return result
        
    def _transform_value(
        self, 
        value: Any, 
        source_field: FieldDefinition, 
        target_field: FieldDefinition,
        config: SchemaConfiguration
    ) -> Any:
        """
        Transform a single value between field types.
        
        Args:
            value: The value to transform
            source_field: The source field definition
            target_field: The target field definition
            config: Configuration for transformation
            
        Returns:
            The transformed value
        """
        if value is None:
            return None
            
        # Skip transformation if types are the same
        if source_field.type == target_field.type:
            return value
            
        # Perform type conversion
        target_type = target_field.type.lower()
        
        try:
            if target_type == "string":
                return str(value)
            elif target_type == "integer":
                return int(value)
            elif target_type == "number":
                return float(value)
            elif target_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "yes", "1", "y")
                return bool(value)
            elif target_type == "array" and not isinstance(value, list):
                return [value]
            elif target_type == "object" and isinstance(value, str):
                import json
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return {"value": value}
        except (ValueError, TypeError):
            # If conversion fails, return the default value or None
            return target_field.default
            
        # Return original value if no transformation is needed
        return value
        
    async def generate_code(
        self,
        schema: SchemaDefinition,
        language: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate code from a schema.
        
        Args:
            schema: The schema to generate code from
            language: The programming language to generate code for
            config: Optional configuration for code generation
            
        Returns:
            The generated code
        """
        config = config or {}
        language = language.lower()
        
        if language == "python":
            return self._generate_python_code(schema, config)
        elif language == "typescript":
            return self._generate_typescript_code(schema, config)
        else:
            raise BaseError(
                f"Unsupported language: {language}",
                "UNSUPPORTED_LANGUAGE",
                language=language
            )
            
    def _generate_python_code(self, schema: SchemaDefinition, config: Dict[str, Any]) -> str:
        """
        Generate Python code from a schema.
        
        Args:
            schema: The schema to generate code from
            config: Configuration for code generation
            
        Returns:
            The generated Python code
        """
        class_name = config.get("class_name", f"{schema.id.name}Model")
        base_class = config.get("base_class", "pydantic.BaseModel")
        imports = [
            "from typing import Dict, List, Optional, Any",
            "import pydantic",
            "from datetime import datetime",
        ]
        
        # Build the class definition
        lines = []
        lines.append(f"class {class_name}({base_class}):")
        lines.append(f'    """')
        if schema.description:
            lines.append(f"    {schema.description}")
        else:
            lines.append(f"    Model for {schema.id.name}.")
        lines.append(f'    """')
        
        # Add field definitions
        for field in schema.fields:
            # Determine the Python type
            python_type = self._get_python_type(field)
            
            # Add field with type annotation
            default_value = "None" if field.default is None and not field.required else repr(field.default)
            if not field.required:
                python_type = f"Optional[{python_type}]"
                if default_value == "None":
                    default_value = "None"
                else:
                    default_value = f"pydantic.Field({default_value})"
            else:
                default_value = "..."
                
            field_line = f"    {field.name}: {python_type} = {default_value}"
            if len(field_line) <= 88:
                lines.append(field_line)
            else:
                lines.append(f"    {field.name}: {python_type} =")
                lines.append(f"        {default_value}")
                
            # Add field docstring if available
            if field.description:
                prev_line = lines[-1]
                lines[-1] = f"{prev_line}  # {field.description}"
                
        # Complete the code
        code = "\n".join(imports) + "\n\n\n" + "\n".join(lines)
        return code
        
    def _generate_typescript_code(self, schema: SchemaDefinition, config: Dict[str, Any]) -> str:
        """
        Generate TypeScript code from a schema.
        
        Args:
            schema: The schema to generate code from
            config: Configuration for code generation
            
        Returns:
            The generated TypeScript code
        """
        interface_name = config.get("interface_name", f"{schema.id.name}Interface")
        
        # Build the interface definition
        lines = []
        if schema.description:
            lines.append("/**")
            lines.append(f" * {schema.description}")
            lines.append(" */")
        lines.append(f"export interface {interface_name} {{")
        
        # Add field definitions
        for field in schema.fields:
            # Determine the TypeScript type
            ts_type = self._get_typescript_type(field)
            
            # Add field docstring if available
            if field.description:
                lines.append(f"  /**")
                lines.append(f"   * {field.description}")
                lines.append(f"   */")
                
            # Add the field definition
            required = field.required
            field_line = f"  {field.name}{'' if required else '?'}: {ts_type};"
            lines.append(field_line)
            
        # Complete the interface
        lines.append("}")
        
        # Add example usage
        lines.append("")
        lines.append("// Example usage:")
        lines.append(f"// const example: {interface_name} = {{")
        for field in schema.fields:
            if field.default is not None:
                value = repr(field.default)
                if field.type.lower() == "string":
                    value = f'"{field.default}"'
                lines.append(f"//   {field.name}: {value},")
            elif field.required:
                example_value = self._get_typescript_example_value(field)
                lines.append(f"//   {field.name}: {example_value},")
        lines.append("// };")
        
        return "\n".join(lines)
        
    def _get_python_type(self, field: FieldDefinition) -> str:
        """
        Get the Python type for a field.
        
        Args:
            field: The field definition
            
        Returns:
            The Python type as a string
        """
        field_type = field.type.lower()
        
        if field_type == "string":
            return "str"
        elif field_type == "integer":
            return "int"
        elif field_type == "number":
            return "float"
        elif field_type == "boolean":
            return "bool"
        elif field_type == "array":
            return "List[Any]"
        elif field_type == "object":
            return "Dict[str, Any]"
        elif field_type == "date" or field_type == "datetime":
            return "datetime"
        else:
            return "Any"
            
    def _get_typescript_type(self, field: FieldDefinition) -> str:
        """
        Get the TypeScript type for a field.
        
        Args:
            field: The field definition
            
        Returns:
            The TypeScript type as a string
        """
        field_type = field.type.lower()
        
        if field_type == "string":
            return "string"
        elif field_type == "integer" or field_type == "number":
            return "number"
        elif field_type == "boolean":
            return "boolean"
        elif field_type == "array":
            return "any[]"
        elif field_type == "object":
            return "Record<string, any>"
        elif field_type == "date" or field_type == "datetime":
            return "string"  # ISO date string
        else:
            return "any"
            
    def _get_typescript_example_value(self, field: FieldDefinition) -> str:
        """
        Get an example value for a TypeScript field.
        
        Args:
            field: The field definition
            
        Returns:
            An example value as a string
        """
        field_type = field.type.lower()
        
        if field_type == "string":
            return '"example"'
        elif field_type == "integer":
            return "42"
        elif field_type == "number":
            return "3.14"
        elif field_type == "boolean":
            return "true"
        elif field_type == "array":
            return "[]"
        elif field_type == "object":
            return "{}"
        elif field_type == "date":
            return '"2023-01-01"'
        elif field_type == "datetime":
            return '"2023-01-01T00:00:00Z"'
        else:
            return "null"