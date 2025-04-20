"""Domain repositories for the Queries module."""

from typing import Any, Dict, List, Optional, Sequence, TypeVar, cast

from uno.core.errors.result import Result
from uno.database.repository import UnoDBRepository
from uno.queries.entities import Query, QueryPath, QueryValue

T = TypeVar("T", Query, QueryPath, QueryValue)


class QueryPathRepository(UnoDBRepository[QueryPath]):
    """Repository for query path entities."""

    async def find_by_attribute_id(self, attribute_id: str) -> list[QueryPath]:
        """Find query paths by attribute ID.

        Args:
            attribute_id: The ID of the attribute to search for.

        Returns:
            A list of query paths associated with the attribute.
        """
        filters = {"attribute_id": {"lookup": "eq", "val": attribute_id}}
        return await self.list(filters=filters)

    async def find_by_meta_type_id(self, meta_type_id: str) -> list[QueryPath]:
        """Find query paths by meta type ID.

        Args:
            meta_type_id: The ID of the meta type to search for.

        Returns:
            A list of query paths associated with the meta type.
        """
        filters = {"meta_type_id": {"lookup": "eq", "val": meta_type_id}}
        return await self.list(filters=filters)

    async def find_by_path_name(self, path_name: str) -> Optional[QueryPath]:
        """Find a query path by name.

        Args:
            path_name: The name of the path to search for.

        Returns:
            The query path if found, None otherwise.
        """
        filters = {"path_name": {"lookup": "eq", "val": path_name}}
        results = await self.list(filters=filters, limit=1)
        return results[0] if results else None


class QueryValueRepository(UnoDBRepository[QueryValue]):
    """Repository for query value entities."""

    async def find_by_query_id(self, query_id: str) -> list[QueryValue]:
        """Find query values by query ID.

        Args:
            query_id: The ID of the query to search for.

        Returns:
            A list of query values associated with the query.
        """
        filters = {"query_id": {"lookup": "eq", "val": query_id}}
        return await self.list(filters=filters)

    async def find_by_query_path_id(self, query_path_id: str) -> list[QueryValue]:
        """Find query values by query path ID.

        Args:
            query_path_id: The ID of the query path to search for.

        Returns:
            A list of query values associated with the query path.
        """
        filters = {"query_path_id": {"lookup": "eq", "val": query_path_id}}
        return await self.list(filters=filters)

    async def delete_for_query(self, query_id: str) -> Result[None]:
        """Delete all query values for a query.

        Args:
            query_id: The ID of the query to delete values for.

        Returns:
            Success if the values were deleted, Failure otherwise.
        """
        try:
            filters = {"query_id": {"lookup": "eq", "val": query_id}}
            values = await self.list(filters=filters)

            for value in values:
                await self.delete(value.id)

            return Success(None)
        except Exception as e:
            return Failure(str(e))


class QueryRepository(UnoDBRepository[Query]):
    """Repository for query entities."""

    async def find_by_name(self, name: str) -> Optional[Query]:
        """Find a query by name.

        Args:
            name: The name of the query to search for.

        Returns:
            The query if found, None otherwise.
        """
        filters = {"name": {"lookup": "eq", "val": name}}
        results = await self.list(filters=filters, limit=1)
        return results[0] if results else None

    async def find_by_meta_type_id(self, meta_type_id: str) -> list[Query]:
        """Find queries by meta type ID.

        Args:
            meta_type_id: The ID of the meta type to search for.

        Returns:
            A list of queries associated with the meta type.
        """
        filters = {"query_meta_type_id": {"lookup": "eq", "val": meta_type_id}}
        return await self.list(filters=filters)

    async def find_with_values(self, query_id: str) -> Result[Query]:
        """Find a query with its values populated.

        Args:
            query_id: The ID of the query to search for.

        Returns:
            Success with the query if found, Failure otherwise.
        """
        try:
            query = await self.get(query_id)
            if not query:
                return Failure(f"Query with ID {query_id} not found")

            # Load relationships
            await self.load_relationships(query)
            return Success(query)
        except Exception as e:
            return Failure(str(e))

    async def find_all_with_values(
        self, meta_type_id: str | None = None
    ) -> Result[list[Query]]:
        """Find all queries with their values populated.

        Args:
            meta_type_id: Optional meta type ID to filter by.

        Returns:
            Success with a list of queries if found, Failure otherwise.
        """
        try:
            filters = {}
            if meta_type_id:
                filters = {"query_meta_type_id": {"lookup": "eq", "val": meta_type_id}}

            queries = await self.list(filters=filters)

            # Load relationships for each query
            for query in queries:
                await self.load_relationships(query)

            return Success(queries)
        except Exception as e:
            return Failure(str(e))
