"""
Repository code generation utilities for Uno applications.

This module provides tools for generating repository classes for Uno models.
"""

import re
from typing import Dict, List, Optional, Set, Union, Any
import inspect
import logging
from pathlib import Path

from uno.devtools.codegen.formatter import format_code


logger = logging.getLogger("uno.codegen")


def generate_repository(
    name: str,
    model_name: str,
    module_name: Optional[str] = None,
    include_imports: bool = True,
    include_docstrings: bool = True,
    include_crud: bool = True,
    include_query_methods: bool = True,
    include_bulk_methods: bool = True,
    id_type: str = "str",
    base_repository_class: str = "UnoRepository",
    filters: Optional[List[Dict[str, Any]]] = None,
    output_file: Optional[Union[str, Path]] = None,
) -> str:
    """Generate a repository class for a model.

    Args:
        name: Name of the repository class
        model_name: Name of the model class
        module_name: Optional module name for imports
        include_imports: Whether to include import statements
        include_docstrings: Whether to include docstrings
        include_crud: Whether to include CRUD methods
        include_query_methods: Whether to include query methods
        include_bulk_methods: Whether to include bulk operation methods
        id_type: Type of the model's ID field
        base_repository_class: Base class for the repository
        filters: Optional list of filter method definitions
        output_file: Optional file path to write the generated code to

    Returns:
        The generated code
    """
    # Start building the code
    code_parts = []

    # Add imports
    if include_imports:
        imports = _generate_repository_imports(
            module_name=module_name,
            model_name=model_name,
            base_repository_class=base_repository_class,
            include_crud=include_crud,
            include_bulk_methods=include_bulk_methods,
            id_type=id_type,
        )
        code_parts.append(imports)

    # Add repository class
    repository_code = _generate_repository_class(
        name=name,
        model_name=model_name,
        include_docstrings=include_docstrings,
        include_crud=include_crud,
        include_query_methods=include_query_methods,
        include_bulk_methods=include_bulk_methods,
        id_type=id_type,
        base_repository_class=base_repository_class,
        filters=filters,
    )
    code_parts.append(repository_code)

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
            logger.info(f"Generated repository written to {output_path}")
        except Exception as e:
            logger.error(f"Error writing to {output_file}: {str(e)}")

    return code


def _generate_repository_imports(
    module_name: Optional[str],
    model_name: str,
    base_repository_class: str,
    include_crud: bool,
    include_bulk_methods: bool,
    id_type: str,
) -> str:
    """Generate import statements for a repository.

    Args:
        module_name: Optional module name for imports
        model_name: Name of the model class
        base_repository_class: Base class for the repository
        include_crud: Whether to include CRUD methods
        include_bulk_methods: Whether to include bulk operation methods
        id_type: Type of the model's ID field

    Returns:
        Import statements as a string
    """
    imports = [
        "from typing import Dict, List, Optional, Set, Union, Any, Type, TypeVar, Generic",
    ]

    # Type imports
    if id_type.lower() == "uuid":
        imports.append("from uuid import UUID")

    # Import base class
    if module_name:
        imports.append(
            f"from {module_name}.database.repository import {base_repository_class}"
        )
        imports.append(f"from {module_name}.model import {model_name}")
    else:
        imports.append(f"from uno.database.repository import {base_repository_class}")
        imports.append(f"from uno.domain.base.model import {model_name}")

    # Additional imports for CRUD and bulk methods
    if include_crud or include_bulk_methods:
        imports.append(f"from sqlalchemy import select, insert, update, delete")
        imports.append(f"from sqlalchemy.ext.asyncio import AsyncSession")

    if include_bulk_methods:
        imports.append(f"from sqlalchemy import bindparam")

    # Type variable for model
    imports.append(f"T = TypeVar('T', bound={model_name})")

    return "\n".join(imports)


def _generate_repository_class(
    name: str,
    model_name: str,
    include_docstrings: bool,
    include_crud: bool,
    include_query_methods: bool,
    include_bulk_methods: bool,
    id_type: str,
    base_repository_class: str,
    filters: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Generate a repository class definition.

    Args:
        name: Name of the repository class
        model_name: Name of the model class
        include_docstrings: Whether to include docstrings
        include_crud: Whether to include CRUD methods
        include_query_methods: Whether to include query methods
        include_bulk_methods: Whether to include bulk operation methods
        id_type: Type of the model's ID field
        base_repository_class: Base class for the repository
        filters: Optional list of filter method definitions

    Returns:
        Repository class definition as a string
    """
    lines = []

    # Class definition and docstring
    lines.append(f"class {name}({base_repository_class}[T, {id_type}]):")

    if include_docstrings:
        lines.append(f'    """{name} repository for {model_name} models."""')

    # Model reference
    lines.append(f"    model_type: Type[T] = {model_name}")

    # Add initialization method
    lines.append("")
    lines.append("    def __init__(self, session: AsyncSession):")
    if include_docstrings:
        lines.append('        """Initialize the repository.')
        lines.append("")
        lines.append("        Args:")
        lines.append("            session: The database session")
        lines.append('        """')
    lines.append(f"        super().__init__(session=session, model_type={model_name})")

    # Add CRUD methods
    if include_crud:
        lines.extend(_generate_crud_methods(model_name, id_type, include_docstrings))

    # Add query methods
    if include_query_methods:
        lines.extend(_generate_query_methods(model_name, include_docstrings))

    # Add bulk methods
    if include_bulk_methods:
        lines.extend(_generate_bulk_methods(model_name, include_docstrings))

    # Add filter methods
    if filters:
        lines.extend(_generate_filter_methods(filters, include_docstrings))

    return "\n".join(lines)


def _generate_crud_methods(
    model_name: str, id_type: str, include_docstrings: bool
) -> List[str]:
    """Generate CRUD methods for a repository.

    Args:
        model_name: Name of the model class
        id_type: Type of the model's ID field
        include_docstrings: Whether to include docstrings

    Returns:
        CRUD method definitions as a list of strings
    """
    lines = []

    # Get by ID method
    lines.append("")
    lines.append(f"    async def get_by_id(self, id: {id_type}) -> Optional[T]:")
    if include_docstrings:
        lines.append(f'        """Get a {model_name} by ID.')
        lines.append("")
        lines.append("        Args:")
        lines.append(f"            id: The {model_name} ID")
        lines.append("")
        lines.append("        Returns:")
        lines.append(f"            The {model_name} if found, None otherwise")
        lines.append('        """')
    lines.append(
        f"        query = select(self.model_type).where(self.model_type.id == id)"
    )
    lines.append(f"        result = await self.session.execute(query)")
    lines.append(f"        return result.scalars().first()")

    # Create method
    lines.append("")
    lines.append(f"    async def create(self, **kwargs) -> T:")
    if include_docstrings:
        lines.append(f'        """Create a new {model_name}.')
        lines.append("")
        lines.append("        Args:")
        lines.append(f"            **kwargs: The {model_name} attributes")
        lines.append("")
        lines.append("        Returns:")
        lines.append(f"            The created {model_name}")
        lines.append('        """')
    lines.append(f"        obj = self.model_type(**kwargs)")
    lines.append(f"        self.session.add(obj)")
    lines.append(f"        await self.session.flush()")
    lines.append(f"        return obj")

    # Update method
    lines.append("")
    lines.append(f"    async def update(self, id: {id_type}, **kwargs) -> Optional[T]:")
    if include_docstrings:
        lines.append(f'        """Update a {model_name}.')
        lines.append("")
        lines.append("        Args:")
        lines.append(f"            id: The {model_name} ID")
        lines.append(f"            **kwargs: The attributes to update")
        lines.append("")
        lines.append("        Returns:")
        lines.append(f"            The updated {model_name} if found, None otherwise")
        lines.append('        """')
    lines.append(f"        obj = await self.get_by_id(id)")
    lines.append(f"        if obj is None:")
    lines.append(f"            return None")
    lines.append("")
    lines.append(f"        for key, value in kwargs.items():")
    lines.append(f"            setattr(obj, key, value)")
    lines.append("")
    lines.append(f"        await self.session.flush()")
    lines.append(f"        return obj")

    # Delete method
    lines.append("")
    lines.append(f"    async def delete(self, id: {id_type}) -> bool:")
    if include_docstrings:
        lines.append(f'        """Delete a {model_name}.')
        lines.append("")
        lines.append("        Args:")
        lines.append(f"            id: The {model_name} ID")
        lines.append("")
        lines.append("        Returns:")
        lines.append(
            f"            True if the {model_name} was deleted, False otherwise"
        )
        lines.append('        """')
    lines.append(f"        obj = await self.get_by_id(id)")
    lines.append(f"        if obj is None:")
    lines.append(f"            return False")
    lines.append("")
    lines.append(f"        await self.session.delete(obj)")
    lines.append(f"        await self.session.flush()")
    lines.append(f"        return True")

    return lines


def _generate_query_methods(model_name: str, include_docstrings: bool) -> List[str]:
    """Generate query methods for a repository.

    Args:
        model_name: Name of the model class
        include_docstrings: Whether to include docstrings

    Returns:
        Query method definitions as a list of strings
    """
    lines = []

    # Get all method
    lines.append("")
    lines.append(
        f"    async def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:"
    )
    if include_docstrings:
        lines.append(f'        """Get all {model_name}s.')
        lines.append("")
        lines.append("        Args:")
        lines.append(
            f"            limit: Optional limit on the number of {model_name}s to return"
        )
        lines.append(f"            offset: Optional offset for pagination")
        lines.append("")
        lines.append("        Returns:")
        lines.append(f"            List of {model_name}s")
        lines.append('        """')
    lines.append(f"        query = select(self.model_type)")
    lines.append(f"        if limit is not None:")
    lines.append(f"            query = query.limit(limit)")
    lines.append(f"        if offset:")
    lines.append(f"            query = query.offset(offset)")
    lines.append(f"        result = await self.session.execute(query)")
    lines.append(f"        return list(result.scalars().all())")

    # Count method
    lines.append("")
    lines.append(f"    async def count(self) -> int:")
    if include_docstrings:
        lines.append(f'        """Count all {model_name}s.')
        lines.append("")
        lines.append("        Returns:")
        lines.append(f"            The number of {model_name}s")
        lines.append('        """')
    lines.append(f"        query = select(self.model_type)")
    lines.append(f"        result = await self.session.execute(query)")
    lines.append(f"        return len(result.scalars().all())")

    # Exists method
    lines.append("")
    lines.append(f"    async def exists(self, id: Any) -> bool:")
    if include_docstrings:
        lines.append(f'        """Check if a {model_name} exists.')
        lines.append("")
        lines.append("        Args:")
        lines.append(f"            id: The {model_name} ID")
        lines.append("")
        lines.append("        Returns:")
        lines.append(f"            True if the {model_name} exists, False otherwise")
        lines.append('        """')
    lines.append(f"        obj = await self.get_by_id(id)")
    lines.append(f"        return obj is not None")

    return lines


def _generate_bulk_methods(model_name: str, include_docstrings: bool) -> List[str]:
    """Generate bulk operation methods for a repository.

    Args:
        model_name: Name of the model class
        include_docstrings: Whether to include docstrings

    Returns:
        Bulk method definitions as a list of strings
    """
    lines = []

    # Bulk create method
    lines.append("")
    lines.append(
        f"    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:"
    )
    if include_docstrings:
        lines.append(f'        """Create multiple {model_name}s in a single operation.')
        lines.append("")
        lines.append("        Args:")
        lines.append(
            f"            items: List of dictionaries with {model_name} attributes"
        )
        lines.append("")
        lines.append("        Returns:")
        lines.append(f"            List of created {model_name}s")
        lines.append('        """')
    lines.append(f"        if not items:")
    lines.append(f"            return []")
    lines.append("")
    lines.append(f"        stmt = insert(self.model_type).returning(self.model_type)")
    lines.append(f"        result = await self.session.execute(stmt, items)")
    lines.append(f"        await self.session.flush()")
    lines.append(f"        return list(result.scalars().all())")

    # Bulk update method
    lines.append("")
    lines.append(
        f"    async def bulk_update(self, items: List[Dict[str, Any]], key_field: str = 'id') -> int:"
    )
    if include_docstrings:
        lines.append(f'        """Update multiple {model_name}s in a single operation.')
        lines.append("")
        lines.append("        Args:")
        lines.append(
            f"            items: List of dictionaries with {model_name} attributes"
        )
        lines.append(f"            key_field: Field to use as the primary key")
        lines.append("")
        lines.append("        Returns:")
        lines.append(f"            Number of updated {model_name}s")
        lines.append('        """')
    lines.append(f"        if not items:")
    lines.append(f"            return 0")
    lines.append("")
    lines.append(f"        # Extract fields to update (excluding the key field)")
    lines.append(f"        update_fields = set()")
    lines.append(f"        for item in items:")
    lines.append(f"            update_fields.update(item.keys())")
    lines.append(f"        update_fields.discard(key_field)")
    lines.append("")
    lines.append(f"        # Prepare the update statement")
    lines.append(f"        stmt = update(self.model_type)")
    lines.append(
        f"        stmt = stmt.where(getattr(self.model_type, key_field) == bindparam(f'b_{key_field}'))"
    )
    lines.append("")
    lines.append(f"        # Add value bindings for each field")
    lines.append(f"        for field in update_fields:")
    lines.append(f"            stmt = stmt.values({field: bindparam(f'b_{field}')})")
    lines.append("")
    lines.append(f"        # Prepare parameters for execution")
    lines.append(f"        params = []")
    lines.append(f"        for item in items:")
    lines.append(f"            param = {{'b_' + key_field: item[key_field]}}")
    lines.append(f"            for field in update_fields:")
    lines.append(f"                if field in item:")
    lines.append(f"                    param[f'b_{field}'] = item[field]")
    lines.append(f"            params.append(param)")
    lines.append("")
    lines.append(f"        # Execute the update")
    lines.append(f"        result = await self.session.execute(stmt, params)")
    lines.append(f"        await self.session.flush()")
    lines.append(f"        return result.rowcount")

    # Bulk delete method
    lines.append("")
    lines.append(f"    async def bulk_delete(self, ids: List[Any]) -> int:")
    if include_docstrings:
        lines.append(f'        """Delete multiple {model_name}s in a single operation.')
        lines.append("")
        lines.append("        Args:")
        lines.append(f"            ids: List of {model_name} IDs to delete")
        lines.append("")
        lines.append("        Returns:")
        lines.append(f"            Number of deleted {model_name}s")
        lines.append('        """')
    lines.append(f"        if not ids:")
    lines.append(f"            return 0")
    lines.append("")
    lines.append(
        f"        stmt = delete(self.model_type).where(self.model_type.id.in_(ids))"
    )
    lines.append(f"        result = await self.session.execute(stmt)")
    lines.append(f"        await self.session.flush()")
    lines.append(f"        return result.rowcount")

    return lines


def _generate_filter_methods(
    filters: List[Dict[str, Any]], include_docstrings: bool
) -> List[str]:
    """Generate filter methods for a repository.

    Args:
        filters: List of filter method definitions
        include_docstrings: Whether to include docstrings

    Returns:
        Filter method definitions as a list of strings
    """
    lines = []

    for filter_def in filters:
        name = filter_def.get("name")
        fields = filter_def.get("fields", [])
        return_type = filter_def.get("return_type", "List[T]")
        is_single = return_type.startswith("Optional[")

        if not name or not fields:
            continue

        # Start method definition
        lines.append("")

        # Build parameter list
        params = []
        for field in fields:
            field_name = field.get("name")
            field_type = field.get("type", "Any")
            optional = field.get("optional", False)

            if optional:
                params.append(f"{field_name}: Optional[{field_type}] = None")
            else:
                params.append(f"{field_name}: {field_type}")

        param_str = ", ".join(params)
        lines.append(f"    async def {name}({param_str}) -> {return_type}:")

        # Add docstring
        if include_docstrings:
            lines.append(f'        """Find by {", ".join(f["name"] for f in fields)}.')
            lines.append("")
            lines.append("        Args:")
            for field in fields:
                field_name = field.get("name")
                field_desc = field.get("description", f"The {field_name}")
                lines.append(f"            {field_name}: {field_desc}")
            lines.append("")
            lines.append("        Returns:")
            if is_single:
                lines.append("            The matching object if found, None otherwise")
            else:
                lines.append("            List of matching objects")
            lines.append('        """')

        # Build query
        lines.append(f"        query = select(self.model_type)")

        # Add where clauses
        for field in fields:
            field_name = field.get("name")
            optional = field.get("optional", False)
            operator = field.get("operator", "==")

            if optional:
                lines.append(f"        if {field_name} is not None:")
                lines.append(
                    f"            query = query.where(self.model_type.{field_name} {operator} {field_name})"
                )
            else:
                lines.append(
                    f"        query = query.where(self.model_type.{field_name} {operator} {field_name})"
                )

        # Execute query and return result
        lines.append(f"        result = await self.session.execute(query)")

        if is_single:
            lines.append(f"        return result.scalars().first()")
        else:
            lines.append(f"        return list(result.scalars().all())")

    return lines
