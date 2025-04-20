"""Database schema diff detection.

This module provides utilities for detecting differences between database schemas,
including comparing SQLAlchemy models to database schemas, and comparing
two different database schemas.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
import logging
from sqlalchemy import MetaData, Table, Column, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.sql import sqltypes
from sqlalchemy.ext.declarative import DeclarativeMeta

logger = logging.getLogger(__name__)


@dataclass
class SchemaDiff:
    """Represents differences between two schemas."""

    added_tables: list[str]
    removed_tables: list[str]
    modified_tables: Dict[str, Dict[str, Any]]

    added_columns: Dict[str, list[str]]
    removed_columns: Dict[str, list[str]]
    modified_columns: Dict[str, Dict[str, Dict[str, Any]]]

    added_indexes: Dict[str, list[str]]
    removed_indexes: Dict[str, list[str]]

    added_constraints: Dict[str, list[str]]
    removed_constraints: Dict[str, list[str]]

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes in the schema diff."""
        return any(
            [
                self.added_tables,
                self.removed_tables,
                self.modified_tables,
                self.added_columns,
                self.removed_columns,
                self.modified_columns,
                self.added_indexes,
                self.removed_indexes,
                self.added_constraints,
                self.removed_constraints,
            ]
        )

    def summary(self) -> str:
        """Get a human-readable summary of the changes."""
        parts = []

        if self.added_tables:
            parts.append(f"Added tables: {', '.join(self.added_tables)}")

        if self.removed_tables:
            parts.append(f"Removed tables: {', '.join(self.removed_tables)}")

        if self.modified_tables:
            parts.append(f"Modified tables: {', '.join(self.modified_tables.keys())}")

        if self.added_columns:
            column_info = [
                f"{table}: {', '.join(cols)}"
                for table, cols in self.added_columns.items()
            ]
            parts.append(f"Added columns: {'; '.join(column_info)}")

        if self.removed_columns:
            column_info = [
                f"{table}: {', '.join(cols)}"
                for table, cols in self.removed_columns.items()
            ]
            parts.append(f"Removed columns: {'; '.join(column_info)}")

        if self.modified_columns:
            column_info = [
                f"{table}: {', '.join(cols.keys())}"
                for table, cols in self.modified_columns.items()
            ]
            parts.append(f"Modified columns: {'; '.join(column_info)}")

        if self.added_indexes:
            index_info = [
                f"{table}: {', '.join(idxs)}"
                for table, idxs in self.added_indexes.items()
            ]
            parts.append(f"Added indexes: {'; '.join(index_info)}")

        if self.removed_indexes:
            index_info = [
                f"{table}: {', '.join(idxs)}"
                for table, idxs in self.removed_indexes.items()
            ]
            parts.append(f"Removed indexes: {'; '.join(index_info)}")

        if self.added_constraints:
            constraint_info = [
                f"{table}: {', '.join(cons)}"
                for table, cons in self.added_constraints.items()
            ]
            parts.append(f"Added constraints: {'; '.join(constraint_info)}")

        if self.removed_constraints:
            constraint_info = [
                f"{table}: {', '.join(cons)}"
                for table, cons in self.removed_constraints.items()
            ]
            parts.append(f"Removed constraints: {'; '.join(constraint_info)}")

        if not parts:
            return "No schema changes detected"

        return "\n".join(parts)


def diff_model_to_db(
    models: Union[list[DeclarativeMeta], DeclarativeMeta],
    engine: Engine,
    schema: str | None = None,
) -> SchemaDiff:
    """Compare SQLAlchemy models to an existing database.

    Args:
        models: A list of SQLAlchemy model classes or a single model class
        engine: SQLAlchemy engine connected to the database
        schema: Optional database schema name

    Returns:
        A SchemaDiff instance with the detected differences
    """
    if not isinstance(models, list):
        models = [models]

    # Create a new metadata object for the models
    metadata = MetaData(schema=schema)

    # Add each model's table to the metadata
    model_tables: Dict[str, Table] = {}
    for model in models:
        if hasattr(model, "__table__"):
            model_tables[model.__table__.name] = model.__table__

    # Reflect the existing database tables
    db_metadata = MetaData(schema=schema)
    db_metadata.reflect(bind=engine)
    db_tables = {table.name: table for table in db_metadata.tables.values()}

    # Calculate differences
    added_tables = [name for name in model_tables if name not in db_tables]
    removed_tables = [name for name in db_tables if name not in model_tables]

    common_tables = set(model_tables) & set(db_tables)

    # Compare common tables
    modified_tables = {}
    added_columns = {}
    removed_columns = {}
    modified_columns = {}
    added_indexes = {}
    removed_indexes = {}
    added_constraints = {}
    removed_constraints = {}

    for table_name in common_tables:
        model_table = model_tables[table_name]
        db_table = db_tables[table_name]

        # Compare columns
        model_columns = {col.name: col for col in model_table.columns}
        db_columns = {col.name: col for col in db_table.columns}

        table_added_columns = [name for name in model_columns if name not in db_columns]
        table_removed_columns = [
            name for name in db_columns if name not in model_columns
        ]

        if table_added_columns:
            added_columns[table_name] = table_added_columns

        if table_removed_columns:
            removed_columns[table_name] = table_removed_columns

        # Compare common columns for differences
        table_modified_columns = {}
        common_columns = set(model_columns) & set(db_columns)

        for col_name in common_columns:
            model_col = model_columns[col_name]
            db_col = db_columns[col_name]

            # Check for type differences - simplified check
            if not isinstance(db_col.type, type(model_col.type)):
                if table_name not in modified_columns:
                    modified_columns[table_name] = {}
                table_modified_columns[col_name] = {
                    "type_changed": True,
                    "old_type": str(db_col.type),
                    "new_type": str(model_col.type),
                }

            # Check nullable differences
            if db_col.nullable != model_col.nullable:
                if col_name not in table_modified_columns:
                    table_modified_columns[col_name] = {}
                table_modified_columns[col_name]["nullable_changed"] = True
                table_modified_columns[col_name]["old_nullable"] = db_col.nullable
                table_modified_columns[col_name]["new_nullable"] = model_col.nullable

            # Check default value differences
            if db_col.server_default != model_col.server_default:
                if col_name not in table_modified_columns:
                    table_modified_columns[col_name] = {}
                table_modified_columns[col_name]["default_changed"] = True

        if table_modified_columns:
            modified_columns[table_name] = table_modified_columns

        # TODO: Implement index and constraint comparison
        # This requires more complex reflection and is beyond this basic version

    return SchemaDiff(
        added_tables=added_tables,
        removed_tables=removed_tables,
        modified_tables=modified_tables,
        added_columns=added_columns,
        removed_columns=removed_columns,
        modified_columns=modified_columns,
        added_indexes=added_indexes,
        removed_indexes=removed_indexes,
        added_constraints=added_constraints,
        removed_constraints=removed_constraints,
    )


def diff_db_to_db(
    source_engine: Engine,
    target_engine: Engine,
    schema: str | None = None,
    include_tables: list[str] | None = None,
    exclude_tables: list[str] | None = None,
) -> SchemaDiff:
    """Compare two database schemas.

    Args:
        source_engine: SQLAlchemy engine for the source database
        target_engine: SQLAlchemy engine for the target database
        schema: Optional database schema name
        include_tables: Optional list of tables to include
        exclude_tables: Optional list of tables to exclude

    Returns:
        A SchemaDiff instance with the detected differences
    """
    exclude_tables = exclude_tables or []

    # Reflect the source database
    source_metadata = MetaData(schema=schema)
    source_metadata.reflect(bind=source_engine)

    # Reflect the target database
    target_metadata = MetaData(schema=schema)
    target_metadata.reflect(bind=target_engine)

    # Filter tables if needed
    source_tables = {
        table.name: table
        for table in source_metadata.tables.values()
        if (include_tables is None or table.name in include_tables)
        and table.name not in exclude_tables
    }

    target_tables = {
        table.name: table
        for table in target_metadata.tables.values()
        if (include_tables is None or table.name in include_tables)
        and table.name not in exclude_tables
    }

    # Calculate differences
    added_tables = [name for name in source_tables if name not in target_tables]
    removed_tables = [name for name in target_tables if name not in source_tables]

    common_tables = set(source_tables) & set(target_tables)

    # Compare columns in common tables
    added_columns = {}
    removed_columns = {}
    modified_columns = {}

    for table_name in common_tables:
        source_table = source_tables[table_name]
        target_table = target_tables[table_name]

        source_columns = {col.name: col for col in source_table.columns}
        target_columns = {col.name: col for col in target_table.columns}

        table_added_columns = [
            name for name in source_columns if name not in target_columns
        ]
        table_removed_columns = [
            name for name in target_columns if name not in source_columns
        ]

        if table_added_columns:
            added_columns[table_name] = table_added_columns

        if table_removed_columns:
            removed_columns[table_name] = table_removed_columns

        # Compare common columns
        common_columns = set(source_columns) & set(target_columns)
        table_modified_columns = {}

        for col_name in common_columns:
            source_col = source_columns[col_name]
            target_col = target_columns[col_name]

            # Check column differences
            if not isinstance(target_col.type, type(source_col.type)):
                if table_name not in modified_columns:
                    modified_columns[table_name] = {}
                if col_name not in table_modified_columns:
                    table_modified_columns[col_name] = {}
                table_modified_columns[col_name]["type_changed"] = True
                table_modified_columns[col_name]["old_type"] = str(target_col.type)
                table_modified_columns[col_name]["new_type"] = str(source_col.type)

            if target_col.nullable != source_col.nullable:
                if col_name not in table_modified_columns:
                    table_modified_columns[col_name] = {}
                table_modified_columns[col_name]["nullable_changed"] = True
                table_modified_columns[col_name]["old_nullable"] = target_col.nullable
                table_modified_columns[col_name]["new_nullable"] = source_col.nullable

            if target_col.server_default != source_col.server_default:
                if col_name not in table_modified_columns:
                    table_modified_columns[col_name] = {}
                table_modified_columns[col_name]["default_changed"] = True

        if table_modified_columns:
            modified_columns[table_name] = table_modified_columns

    # TODO: Implement index and constraint comparison

    return SchemaDiff(
        added_tables=added_tables,
        removed_tables=removed_tables,
        modified_tables={},  # Placeholder, not fully implemented
        added_columns=added_columns,
        removed_columns=removed_columns,
        modified_columns=modified_columns,
        added_indexes={},
        removed_indexes={},
        added_constraints={},
        removed_constraints={},
    )
