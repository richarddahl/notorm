"""
Service code generation for Uno applications.

This module provides tools for generating service classes using the Uno
framework's conventions and patterns.
"""

import os
from typing import Dict, List, Optional, Set, Any, Tuple

from uno.devtools.codegen.formatter import format_code


def generate_service(
    name: str,
    module_path: str,
    fields: Optional[dict[str, str]] = None,
    methods: Optional[list[dict[str, Any]]] = None,
    dependencies: list[str] | None = None,
    base_class: str = "BaseService",
    imports: list[str] | None = None,
    output_dir: str | None = None,
) -> Tuple[str, str]:
    """
    Generate a service class for the Uno framework.

    Args:
        name: Name of the service class (CamelCase)
        module_path: Module path for imports (e.g. 'myapp.users')
        fields: Dictionary of field names and types
        methods: List of method definitions with name, args, return_type, and body
        dependencies: List of dependency names
        base_class: Base class for the service
        imports: Additional import statements
        output_dir: Optional directory to write file to

    Returns:
        Tuple of (code, file_path)
    """
    if fields is None:
        fields = {}

    if methods is None:
        methods = []

    if dependencies is None:
        dependencies = []

    if imports is None:
        imports = []

    # Prepare class name and file name
    service_name = f"{name}Service" if not name.endswith("Service") else name
    file_name = f"{_to_snake_case(service_name)}.py"

    # Generate import statements
    import_statements = [
        "from typing import List, Dict, Optional, Any, Union",
        f"from {module_path}.models import {name}",
        f"from {module_path}.repositories import {name}Repository",
        "from uno.core.result import Result, Success, Failure",
        "from uno.core.errors import BaseError",
    ]

    # Add base class import
    if base_class == "BaseService":
        import_statements.append("from uno.domain.service import BaseService")
    else:
        # If it's a custom base class, try to guess the import
        if "." in base_class:
            import_statements.append(
                f"from {base_class.rsplit('.', 1)[0]} import {base_class.rsplit('.', 1)[1]}"
            )

    # Add custom imports
    for imp in imports:
        if imp not in import_statements:
            import_statements.append(imp)

    # Generate class definition
    base_cls = base_class.split(".")[-1] if "." in base_class else base_class
    class_def = f"class {service_name}({base_cls}):"

    # Generate class docstring
    docstring = f'    """\n    Service for {name} operations.\n    """'

    # Generate initializer
    init_args = ["self"]
    init_body = []
    init_parent_args = []

    # Set up repository dependency
    init_args.append(f"repository: {name}Repository")
    init_body.append(f"self.repository = repository")

    # Add custom dependencies
    for dep in dependencies:
        # Extract type annotation if provided in format "name: type"
        if ":" in dep:
            dep_name, dep_type = dep.split(":", 1)
            dep_name = dep_name.strip()
            dep_type = dep_type.strip()
            init_args.append(f"{dep_name}: {dep_type}")
        else:
            # Use Any as default type
            dep_name = dep
            init_args.append(f"{dep_name}: Any")

        init_body.append(f"self.{dep_name} = {dep_name}")

    # Complete init method
    if base_cls != "object":
        if init_parent_args:
            init_method = f"    def __init__({', '.join(init_args)}):\n"
            init_method += f"        super().__init__({', '.join(init_parent_args)})\n"
        else:
            init_method = f"    def __init__({', '.join(init_args)}):\n"
            init_method += f"        super().__init__()\n"
    else:
        init_method = f"    def __init__({', '.join(init_args)}):\n"

    for line in init_body:
        init_method += f"        {line}\n"

    # Generate field properties
    field_properties = []
    for field_name, field_type in fields.items():
        prop = f"    @property\n"
        prop += f"    def {field_name}(self) -> {field_type}:\n"
        prop += f"        return self._{field_name}\n\n"

        prop += f"    @{field_name}.setter\n"
        prop += f"    def {field_name}(self, value: {field_type}):\n"
        prop += f"        self._{field_name} = value\n"
        field_properties.append(prop)

    # Generate standard CRUD methods if no methods provided
    if not methods:
        methods = [
            {
                "name": "get_by_id",
                "args": ["id: str"],
                "return_type": f"Result[Optional[{name}]]",
                "body": [
                    "result = await self.repository.get_by_id(id)",
                    "if result.is_failure():",
                    "    return Failure(result.error)",
                    "return Success(result.value)",
                ],
            },
            {
                "name": "list",
                "args": [
                    "limit: int = 100",
                    "offset: int = 0",
                    "filters: dict[str,Any] | None = None",
                ],
                "return_type": f"Result[list[{name}]]",
                "body": [
                    "result = await self.repository.list(limit=limit, offset=offset, filters=filters)",
                    "if result.is_failure():",
                    "    return Failure(result.error)",
                    "return Success(result.value)",
                ],
            },
            {
                "name": "create",
                "args": [f"item: {name}"],
                "return_type": f"Result[{name}]",
                "body": [
                    "result = await self.repository.create(item)",
                    "if result.is_failure():",
                    "    return Failure(result.error)",
                    "return Success(result.value)",
                ],
            },
            {
                "name": "update",
                "args": [f"item: {name}"],
                "return_type": f"Result[{name}]",
                "body": [
                    "result = await self.repository.update(item)",
                    "if result.is_failure():",
                    "    return Failure(result.error)",
                    "return Success(result.value)",
                ],
            },
            {
                "name": "delete",
                "args": ["id: str"],
                "return_type": "Result[bool]",
                "body": [
                    "result = await self.repository.delete(id)",
                    "if result.is_failure():",
                    "    return Failure(result.error)",
                    "return Success(result.value)",
                ],
            },
        ]

    # Generate method code
    method_code = []
    for method in methods:
        method_name = method.get("name", "method")
        method_args = ["self"] + method.get("args", [])
        method_return = method.get("return_type", "Any")
        method_body = method.get("body", ["pass"])
        method_is_async = method.get("is_async", True)

        # Create method signature
        method_sig = f"    {'async ' if method_is_async else ''}def {method_name}({', '.join(method_args)}) -> {method_return}:"

        # Add docstring if provided
        if "docstring" in method:
            method_sig += f'\n        """{method["docstring"]}"""'

        # Add method body
        for line in method_body:
            method_sig += f"\n        {line}"

        method_code.append(method_sig)

    # Assemble the complete code
    code_parts = [
        "\n".join(import_statements),
        "",
        "",
        class_def,
        docstring,
        "",
        init_method,
    ]

    # Add field properties if any
    if field_properties:
        code_parts.extend(field_properties)

    # Add method implementations
    code_parts.extend(method_code)

    # Join all code parts
    code = "\n".join(code_parts)

    # Format the code
    code = format_code(code)

    # Write to file if output directory is provided
    file_path = None
    if output_dir:
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Write to file
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "w") as f:
            f.write(code)

    return code, file_path or file_name


def _to_snake_case(name: str) -> str:
    """Convert a CamelCase name to snake_case."""
    result = [name[0].lower()]
    for char in name[1:]:
        if char.isupper():
            result.append("_")
            result.append(char.lower())
        else:
            result.append(char)
    return "".join(result)
