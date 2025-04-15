# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import json
from typing import Any, Callable, Optional, Type, TypeVar, List, Dict, Tuple, cast

from psycopg import sql
from asyncpg.exceptions import UniqueViolationError  # type: ignore

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    select,
    delete,
    update,
    text,
    func,
    UniqueConstraint,
)
from sqlalchemy.exc import IntegrityError


from uno.core.errors.result import Result, Success, Failure
from uno.core.protocols import (
    DatabaseSessionContextProtocol,
    DatabaseRepository,
)


class IntegrityConflictException(Exception):
    pass


class NotFoundException(Exception):
    pass


# FilterParam has been moved to uno.core.types to avoid circular imports
from uno.core.types import FilterParam


T = TypeVar("T", bound=BaseModel)
K = TypeVar("K")


def UnoDBFactory(
    obj: BaseModel,
    session_context_factory: Optional[Type[DatabaseSessionContextProtocol]] = None,
) -> Type[DatabaseRepository[T, K, Any, Dict[str, Any], Any]]:
    """
    Factory function that creates a UnoDB class implementing the DatabaseRepository protocol.

    Args:
        obj: A BaseModel containing model and filter information
        session_context_factory: Optional session context class

    Returns:
        A UnoDB class that implements the DatabaseRepository protocol
    """
    # Dynamically import async_session to avoid circular imports
    from uno.database.session import AsyncSessionContext

    # Use provided session factory or default
    SessionContextClass = session_context_factory or AsyncSessionContext

    class UnoDB(DatabaseRepository[T, K, Any, Dict[str, Any], Any]):

        @classmethod
        def table_keys(cls) -> tuple[list[str], list[list[str]]]:
            """
            Retrieve a dictionary of table keys, including primary keys and unique constraints.

            This method gathers information about the primary keys and unique constraints
            defined in the table schema of the associated model. It checks for unique constraints
            defined in `__table_args__` as well as unique constraints on individual columns.

            Returns:
                dict[str, list[str]]: A dictionary where the keys are the names of the constraints
                (e.g., "pk" for primary key or the name of the unique constraint) and the values
                are lists of column names that make up the constraint.
            """

            # Initialize a dictionary to store table keys, starting with the primary key columns
            pk_fields = obj.model.__table__.primary_key.columns.keys()
            uq_fields = []

            # Check for unique constraints defined in the `__table_args__` attribute of the model
            if hasattr(cls.obj.model, "__table_args__"):
                for constraint in cls.obj.model.__table_args__:
                    # If the constraint is a UniqueConstraint, process it
                    if isinstance(constraint, UniqueConstraint):
                        # Add the unique constraint to the table_keys dictionary
                        uq_fields.append(constraint.columns.keys())

            # Check for unique constraints defined on individual columns of the table
            for column in cls.obj.model.__table__.columns:
                if column.unique is not None and column.name not in pk_fields:
                    uq_fields.append([column.name])

            return pk_fields, uq_fields

        @classmethod
        async def merge(cls, data: Dict[str, Any]) -> Any:
            """
            Call the PostgreSQL merge_record function with escaped colons in the data values.
            """
            # pk_fields, unique_constraints = cls.table_keys()
            table_name = f"{obj.model.__table__.schema}.{cls.table_name}"

            # Create a deep copy of the data to avoid modifying the original
            import copy

            data_copy = copy.deepcopy(data)

            # Function to escape colons in string values
            def escape_colons(value):
                if isinstance(value, str):
                    # Escape colons with backslashes
                    return value.replace(":", "\\:")
                return value

            # Process all values in the data dictionary
            for key, value in data_copy.items():
                data_copy[key] = escape_colons(value)

            data_json = json.dumps(data_copy)

            # Create raw SQL with the E'' string syntax for proper escape handling
            query = (
                sql.SQL("SELECT merge_record('{table_name}', E'{data_json}'::jsonb)")
                .format(table_name=sql.SQL(table_name), data_json=sql.SQL(data_json))
                .as_string()
            )
            try:
                # Create a session context that implements the protocol
                session_context = SessionContextClass()
                async with session_context as session:
                    await session.execute(func.set_role("writer"))

                    # Execute raw SQL
                    result = await session.execute(text(query))
                    await session.commit()
                    return result.fetchone()
            except Exception as e:
                print(f"Error in merge_or_update_record_sa: {e}")
                print(f"SQL: {query}")
                raise

        @classmethod
        async def create(
            cls,
            schema: T,
        ) -> Tuple[T, bool]:
            try:
                session_context = SessionContextClass()
                async with session_context as session:
                    await session.execute(func.set_role("writer"))
                    session.add(schema)
                    await session.commit()
                    return schema, True

            except IntegrityError as e:
                # This is the only way I can find to check for a unique constraint violation
                # As the asyncpg.UniqueViolationError gets wrapped in a SQLAlchemy IntegrityError
                # And isinstance(e.orig, UniqueViolationError) doesn't work
                if "duplicate key value violates unique constraint" in str(e):
                    # Handle the case where the object already exists
                    raise UniqueViolationError
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}", "UNKNOWN_ERROR") from e

        @classmethod
        async def update(
            cls,
            to_db_model: T,
            **kwargs: Any,
        ) -> T:
            try:
                obj = await cls.get(to_db_model=to_db_model, **kwargs)
                session_context = SessionContextClass()
                async with session_context as session:
                    await session.execute(func.set_role("writer"))
                    session.add(to_db_model)
                    await session.commit()
                    return to_db_model

            except IntegrityError as e:
                # This is the only way I can find to check for a unique constraint violation
                # As the asyncpg.UniqueViolationError gets wrapped in a SQLAlchemy IntegrityError
                # And isinstance(e.orig, UniqueViolationError) doesn't work
                if "duplicate key value violates unique constraint" in str(e):
                    # Handle the case where the object already exists
                    raise UniqueViolationError
            except Exception as e:
                raise UnoError(f"Unknown error occurred: {e}") from e

        @classmethod
        async def get(cls, select_related=None, **kwargs: Any) -> Optional[T]:
            """
            Get a record from the database with optional relationship loading.

            Args:
                select_related: Controls which relationships to load:
                    - None/False: Load no relationships
                    - True: Load all relationships
                    - List[str]: Load only specified relationships
                **kwargs: Keyword arguments for filtering

            Returns:
                The requested record if found, None otherwise

            Raises:
                NotFoundException: If the record does not exist
                IntegrityConflictException: If multiple records match the query
                UnoError: For other errors
            """
            column_names = obj.model.__table__.columns.keys()
            stmt = select(obj.model.__table__.c[*column_names])

            if kwargs:
                for key, val in kwargs.items():
                    if key == "to_db_model":
                        continue
                    if key in column_names:
                        stmt = stmt.where(getattr(obj.model, key) == val)
                    else:
                        raise ValueError(
                            f"Invalid natural key field provided in kwargs: {key}"
                        )

            try:
                session_context = SessionContextClass()
                async with session_context as session:
                    await session.execute(func.set_role("reader"))
                    result = await session.execute(stmt)
                    rows = result.fetchall()
                    row_count = len(rows)
                    if row_count == 0:
                        raise NotFoundException(
                            f"Record not found for the provided natural key: {kwargs}"
                        )
                    if row_count > 1:
                        # This should never happen, but if it does, raise an exception
                        raise IntegrityConflictException(
                            f"Multiple records found for the provided natural key: {kwargs}"
                        )
                    row = rows[0]

                    # Convert to mapping
                    record = row._mapping if row is not None else None

                    # Load relationships if requested
                    if (
                        select_related
                        and record
                        and hasattr(obj.model, "__relationships__")
                    ):
                        # Import the relationship loader
                        from uno.database.relationship_loader import RelationshipLoader

                        # Create loader and load relationships
                        loader = RelationshipLoader(obj.model.__class__)
                        record = await loader.load_relationships(
                            record, select_related, session
                        )

                    return record
            except Exception as e:
                raise UnoError(
                    f"Unhandled error occurred: {e}", error_code="SELECT_ERROR"
                ) from e

        @classmethod
        async def delete(cls, **kwargs: Any) -> bool:
            """Delete a record using kwargs as filters."""
            column_names = obj.model.__table__.columns.keys()
            stmt = delete(obj.model.__table__)

            if kwargs:
                for key, val in kwargs.items():
                    if key in column_names:
                        stmt = stmt.where(getattr(obj.model, key) == val)
                    else:
                        raise ValueError(
                            f"Invalid field provided in kwargs for delete: {key}"
                        )

            try:
                session_context = SessionContextClass()
                async with session_context as session:
                    await session.execute(func.set_role("writer"))
                    result = await session.execute(stmt)
                    await session.commit()
                    return True
            except Exception as e:
                raise UnoError(
                    f"Unhandled error occurred during delete: {e}",
                    error_code="DELETE_ERROR",
                ) from e

        @classmethod
        async def filter(
            cls, filters: Optional[FilterParam] = None, select_related=None
        ) -> List[T]:
            """
            Filter records with optional relationship loading.

            Args:
                filters: Filter parameters for querying
                select_related: Controls which relationships to load:
                    - None/False: Load no relationships
                    - True: Load all relationships
                    - List[str]: Load only specified relationships

            Returns:
                List of matching records
            """
            limit = 25
            offset = 0
            order_by = None
            order = "asc"
            column_names = obj.model.__table__.columns.keys()
            stmt = select(obj.model.__table__.c[*column_names])

            for fltr in filters:
                if fltr.label in ["limit", "offset", "order_by"]:
                    if fltr.label == "limit":
                        limit = fltr.val
                        continue
                    if fltr.label == "offset":
                        offset = fltr.val
                        continue
                    if fltr.label == "order_by":
                        order_by = fltr.val
                        continue
                label = fltr.label.split(".")[0]
                filter = obj.filters.get(label)
                cypher_query = filter.cypher_query(fltr.val, fltr.lookup)
                print(cypher_query)
                stmt = stmt.where(obj.model.id.in_(select(text(cypher_query))))

            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)
            if order_by:
                if order == "desc":
                    stmt = stmt.order_by(getattr(obj.model, order_by).desc())
                else:
                    stmt = stmt.order_by(getattr(obj.model, order_by).asc())

            try:
                session_context = SessionContextClass()
                async with session_context as session:
                    await session.execute(func.set_role("reader"))
                    result = await session.execute(stmt)
                    records = result.mappings().all()

                    # Load relationships if requested
                    if (
                        select_related
                        and records
                        and hasattr(obj.model, "__relationships__")
                    ):
                        # Import the relationship loader
                        from uno.database.relationship_loader import RelationshipLoader

                        # Create loader and load relationships in batch
                        loader = RelationshipLoader(obj.model.__class__)
                        records = await loader.load_relationships_batch(
                            records, select_related, session
                        )

                    return records
            except Exception as e:
                raise UnoError(
                    f"Unhandled error occurred: {e}", error_code="SELECT_ERROR"
                ) from e

    UnoDB.obj = obj
    UnoDB.table_name = obj.model.__table__.name
    return UnoDB
