"""
Model code generation utilities for Uno applications.

This module provides tools for generating UnoModel and UnoSchema classes.
"""

import re
from typing import Dict, List, Optional, Set, Union, Any
import inspect
import logging
from pathlib import Path

from uno.devtools.codegen.formatter import format_code


logger = logging.getLogger("uno.codegen")


def generate_model(
    name: str,
    fields: Dict[str, Dict[str, Any]],
    table_name: Optional[str] = None,
    module_name: Optional[str] = None,
    include_schema: bool = True,
    include_imports: bool = True,
    include_docstrings: bool = True,
    schema_name: Optional[str] = None,
    base_model_class: str = "UnoModel",
    base_schema_class: str = "UnoSchema",
    timestamps: bool = True,
    soft_delete: bool = False,
    relationships: Optional[List[Dict[str, Any]]] = None,
    indexes: Optional[List[Dict[str, Any]]] = None,
    output_file: Optional[Union[str, Path]] = None,
) -> str:
    """Generate a UnoModel class with an optional UnoSchema.

    Args:
        name: Name of the model class
        fields: Dictionary of field definitions
        table_name: Optional table name (defaults to snake_case of name)
        module_name: Optional module name for imports
        include_schema: Whether to generate a UnoSchema class
        include_imports: Whether to include import statements
        include_docstrings: Whether to include docstrings
        schema_name: Optional name for the schema class (defaults to {name}Schema)
        base_model_class: Base class for the model
        base_schema_class: Base class for the schema
        timestamps: Whether to include created_at and updated_at fields
        soft_delete: Whether to include deleted_at field for soft delete
        relationships: Optional list of relationship definitions
        indexes: Optional list of index definitions
        output_file: Optional file path to write the generated code to

    Returns:
        The generated code
    """
    # Prepare table name
    if not table_name:
        table_name = _camel_to_snake(name)

    # Prepare schema name
    if not schema_name and include_schema:
        schema_name = f"{name}Schema"

    # Start building the code
    code_parts = []

    # Add imports
    if include_imports:
        imports = _generate_model_imports(
            module_name=module_name,
            base_model_class=base_model_class,
            base_schema_class=base_schema_class,
            include_schema=include_schema,
            fields=fields,
        )
        code_parts.append(imports)

    # Add model class
    model_code = _generate_model_class(
        name=name,
        fields=fields,
        table_name=table_name,
        include_docstrings=include_docstrings,
        base_model_class=base_model_class,
        timestamps=timestamps,
        soft_delete=soft_delete,
        relationships=relationships,
        indexes=indexes,
    )
    code_parts.append(model_code)

    # Add schema class if requested
    if include_schema:
        schema_code = _generate_schema_class(
            name=schema_name,
            model_name=name,
            fields=fields,
            include_docstrings=include_docstrings,
            base_schema_class=base_schema_class,
        )
        code_parts.append(schema_code)

    # Join code parts
    code = "\n\n".join(code_parts)

    # Format the code
    code = format_code(code)

    # Write to file if requested
    if output_file:
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)
            logger.info(f"Generated model written to {output_path}")
        except Exception as e:
            logger.error(f"Error writing to {output_file}: {str(e)}")

    return code


def _generate_model_imports(
    module_name: Optional[str],
    base_model_class: str,
    base_schema_class: str,
    include_schema: bool,
    fields: Dict[str, Dict[str, Any]],
) -> str:
    """Generate import statements for a model.

    Args:
        module_name: Optional module name for imports
        base_model_class: Base class for the model
        base_schema_class: Base class for the schema
        include_schema: Whether to generate a UnoSchema class
        fields: Dictionary of field definitions

    Returns:
        Import statements as a string
    """
    imports = [
        "from datetime import datetime, date, time, timedelta",
        "from typing import Dict, List, Optional, Set, Union, Any",
        "from uuid import UUID",
    ]

    # Import sqlalchemy
    imports.append("import sqlalchemy as sa")

    # Import base classes
    if module_name:
        imports.append(f"from {module_name} import {base_model_class}")
        if include_schema:
            imports.append(f"from {module_name} import {base_schema_class}")
    else:
        imports.append(f"from uno.model import {base_model_class}")
        if include_schema:
            imports.append(f"from uno.model import {base_schema_class}")

    # Import additional types based on field definitions
    import_pydantic = False
    import_enum = False

    for field_info in fields.values():
        field_type = field_info.get("type", "").lower()

        if "enum" in field_type:
            import_enum = True

        if any(
            validator in field_info
            for validator in ["min_length", "max_length", "regex", "ge", "le"]
        ):
            import_pydantic = True

    if import_enum:
        imports.append("from enum import Enum")

    if import_pydantic:
        imports.append("from pydantic import Field, validator")

    return "\n".join(imports)


def _generate_model_class(
    name: str,
    fields: Dict[str, Dict[str, Any]],
    table_name: str,
    include_docstrings: bool,
    base_model_class: str,
    timestamps: bool,
    soft_delete: bool,
    relationships: Optional[List[Dict[str, Any]]] = None,
    indexes: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Generate a UnoModel class definition.

    Args:
        name: Name of the model class
        fields: Dictionary of field definitions
        table_name: Table name
        include_docstrings: Whether to include docstrings
        base_model_class: Base class for the model
        timestamps: Whether to include created_at and updated_at fields
        soft_delete: Whether to include deleted_at field for soft delete
        relationships: Optional list of relationship definitions
        indexes: Optional list of index definitions

    Returns:
        Model class definition as a string
    """
    lines = []

    # Class definition and docstring
    lines.append(f"class {name}({base_model_class}):")

    if include_docstrings:
        lines.append(f'    """{name} model.')
        lines.append("")
        lines.append(f"    Table: {table_name}")
        lines.append('    """')

    # __tablename__
    lines.append(f'    __tablename__ = "{table_name}"')

    # Add fields
    for field_name, field_info in fields.items():
        field_line = _generate_model_field(field_name, field_info)
        lines.append(f"    {field_line}")

    # Add timestamps
    if timestamps:
        lines.append("    # Timestamps")
        lines.append(
            "    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)"
        )
        lines.append(
            "    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)"
        )

    # Add soft delete
    if soft_delete:
        lines.append("    # Soft delete")
        lines.append("    deleted_at = sa.Column(sa.DateTime, nullable=True)")

    # Add relationships
    if relationships:
        lines.append("")
        lines.append("    # Relationships")
        for relationship in relationships:
            rel_line = _generate_relationship(relationship)
            lines.append(f"    {rel_line}")

    # Add indexes
    if indexes:
        lines.append("")
        lines.append("    # Indexes")
        for index in indexes:
            idx_line = _generate_index(index)
            lines.append(f"    {idx_line}")

    return "\n".join(lines)


def _generate_schema_class(
    name: str,
    model_name: str,
    fields: Dict[str, Dict[str, Any]],
    include_docstrings: bool,
    base_schema_class: str,
) -> str:
    """Generate a UnoSchema class definition.

    Args:
        name: Name of the schema class
        model_name: Name of the model class
        fields: Dictionary of field definitions
        include_docstrings: Whether to include docstrings
        base_schema_class: Base class for the schema

    Returns:
        Schema class definition as a string
    """
    lines = []

    # Class definition and docstring
    lines.append(f"class {name}({base_schema_class}):")

    if include_docstrings:
        lines.append(f'    """{name} schema for the {model_name} model."""')

    # Add model reference
    lines.append(f"    model = {model_name}")

    # Add Config class
    lines.append("")
    lines.append("    model_config = ConfigDict(")
    lines.append("        from_attributes=True,")
    lines.append("        validate_assignment=True,")
    lines.append("        )")

    # Add validators if needed
    validators = []

    for field_name, field_info in fields.items():
        if any(
            validator in field_info
            for validator in ["min_length", "max_length", "regex", "ge", "le"]
        ):
            validator_lines = _generate_validator(field_name, field_info)
            validators.extend(validator_lines)

    if validators:
        lines.extend([""] + validators)

    return "\n".join(lines)


def _generate_model_field(field_name: str, field_info: Dict[str, Any]) -> str:
    """Generate a SQLAlchemy column definition for a model field.

    Args:
        field_name: Name of the field
        field_info: Field definition

    Returns:
        Column definition as a string
    """
    field_type = field_info.get("type", "String")
    nullable = field_info.get("nullable", True)
    primary_key = field_info.get("primary_key", False)
    unique = field_info.get("unique", False)
    default = field_info.get("default")
    server_default = field_info.get("server_default")
    index = field_info.get("index", False)
    comment = field_info.get("comment")

    args = []

    # Convert field type to SQLAlchemy type
    sa_type = _get_sqlalchemy_type(field_type, field_info)
    args.append(sa_type)

    # Add column options
    if primary_key:
        args.append("primary_key=True")

    if not nullable:
        args.append("nullable=False")
    elif nullable:
        args.append("nullable=True")

    if unique:
        args.append("unique=True")

    if default is not None:
        if field_type.lower() in ["string", "text"]:
            args.append(f"default='{default}'")
        elif field_type.lower() in ["datetime"]:
            if default == "utcnow":
                args.append("default=datetime.utcnow")
            else:
                args.append(f"default={default}")
        else:
            args.append(f"default={default}")

    if server_default is not None:
        args.append(f"server_default='{server_default}'")

    if index:
        args.append("index=True")

    if comment:
        args.append(f"comment='{comment}'")

    # Construct the column definition
    return f"{field_name} = sa.Column({', '.join(args)})"


def _get_sqlalchemy_type(field_type: str, field_info: Dict[str, Any]) -> str:
    """Convert a field type to a SQLAlchemy type.

    Args:
        field_type: Field type string
        field_info: Field definition

    Returns:
        SQLAlchemy type as a string
    """
    field_type = field_type.lower()

    # Basic types
    if field_type == "string":
        length = field_info.get("length", 255)
        return f"sa.String({length})"
    elif field_type == "text":
        return "sa.Text"
    elif field_type == "integer":
        return "sa.Integer"
    elif field_type == "biginteger":
        return "sa.BigInteger"
    elif field_type == "float":
        return "sa.Float"
    elif field_type == "numeric":
        precision = field_info.get("precision", 10)
        scale = field_info.get("scale", 2)
        return f"sa.Numeric({precision}, {scale})"
    elif field_type == "boolean":
        return "sa.Boolean"
    elif field_type == "date":
        return "sa.Date"
    elif field_type == "time":
        return "sa.Time"
    elif field_type == "datetime":
        return "sa.DateTime"
    elif field_type == "timestamp":
        return "sa.TIMESTAMP"
    elif field_type == "binary":
        return "sa.LargeBinary"
    elif field_type == "uuid":
        return "sa.UUID"
    elif field_type == "json":
        return "sa.JSON"
    elif field_type == "jsonb":
        return "sa.JSONB"
    elif field_type == "array":
        item_type = field_info.get("item_type", "String")
        sa_item_type = _get_sqlalchemy_type(item_type, {})
        return f"sa.ARRAY({sa_item_type})"
    elif field_type == "enum":
        values = field_info.get("values", [])
        values_str = ", ".join([f"'{v}'" for v in values])
        return f"sa.Enum({values_str})"
    elif field_type.startswith("foreign_key"):
        target = field_info.get("target", "")
        return f"sa.ForeignKey('{target}')"

    # Default to String
    return "sa.String(255)"


def _generate_relationship(relationship: Dict[str, Any]) -> str:
    """Generate a SQLAlchemy relationship definition.

    Args:
        relationship: Relationship definition

    Returns:
        Relationship definition as a string
    """
    name = relationship.get("name")
    target = relationship.get("target")
    backref = relationship.get("backref")
    foreign_keys = relationship.get("foreign_keys")
    lazy = relationship.get("lazy", "select")

    args = [f"'{target}'"]

    if backref:
        args.append(f"backref='{backref}'")

    if foreign_keys:
        args.append(f"foreign_keys=[{foreign_keys}]")

    args.append(f"lazy='{lazy}'")

    return f"{name} = sa.orm.relationship({', '.join(args)})"


def _generate_index(index: Dict[str, Any]) -> str:
    """Generate a SQLAlchemy index definition.

    Args:
        index: Index definition

    Returns:
        Index definition as a string
    """
    name = index.get("name")
    fields = index.get("fields", [])
    unique = index.get("unique", False)

    args = []

    for field in fields:
        args.append(field)

    options = []

    if unique:
        options.append("unique=True")

    options_str = ", ".join(options)
    if options_str:
        return (
            f"__table_args__ = (sa.Index('{name}', {', '.join(args)}, {options_str}),)"
        )
    else:
        return f"__table_args__ = (sa.Index('{name}', {', '.join(args)}),)"


def _generate_validator(field_name: str, field_info: Dict[str, Any]) -> List[str]:
    """Generate a Pydantic validator for a field.

    Args:
        field_name: Name of the field
        field_info: Field definition

    Returns:
        Validator definition as a list of strings
    """
    lines = []
    validator_name = f"validate_{field_name}"

    lines.append("    @validator('" + field_name + "', pre=True)")
    lines.append(f"    def {validator_name}(cls, v):")

    if field_info.get("min_length") or field_info.get("max_length"):
        min_length = field_info.get("min_length")
        max_length = field_info.get("max_length")

        if min_length and max_length:
            lines.append(f"        if v is not None and len(v) < {min_length}:")
            lines.append(
                f"            raise ValueError(f'{field_name} must be at least {min_length} characters')"
            )
            lines.append(f"        if v is not None and len(v) > {max_length}:")
            lines.append(
                f"            raise ValueError(f'{field_name} must be at most {max_length} characters')"
            )
        elif min_length:
            lines.append(f"        if v is not None and len(v) < {min_length}:")
            lines.append(
                f"            raise ValueError(f'{field_name} must be at least {min_length} characters')"
            )
        elif max_length:
            lines.append(f"        if v is not None and len(v) > {max_length}:")
            lines.append(
                f"            raise ValueError(f'{field_name} must be at most {max_length} characters')"
            )

    if field_info.get("regex"):
        regex = field_info.get("regex")
        lines.append(f"        if v is not None and not re.match(r'{regex}', v):")
        lines.append(
            f"            raise ValueError(f'{field_name} must match pattern {regex}')"
        )

    if field_info.get("ge") is not None or field_info.get("le") is not None:
        ge = field_info.get("ge")
        le = field_info.get("le")

        if ge is not None and le is not None:
            lines.append(f"        if v is not None and v < {ge}:")
            lines.append(
                f"            raise ValueError(f'{field_name} must be at least {ge}')"
            )
            lines.append(f"        if v is not None and v > {le}:")
            lines.append(
                f"            raise ValueError(f'{field_name} must be at most {le}')"
            )
        elif ge is not None:
            lines.append(f"        if v is not None and v < {ge}:")
            lines.append(
                f"            raise ValueError(f'{field_name} must be at least {ge}')"
            )
        elif le is not None:
            lines.append(f"        if v is not None and v > {le}:")
            lines.append(
                f"            raise ValueError(f'{field_name} must be at most {le}')"
            )

    lines.append("        return v")

    return lines


def _camel_to_snake(name: str) -> str:
    """Convert a CamelCase string to snake_case.

    Args:
        name: CamelCase string

    Returns:
        snake_case string
    """
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
