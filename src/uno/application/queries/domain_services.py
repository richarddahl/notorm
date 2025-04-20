"""Domain services for the Queries module."""

from typing import Dict, List, Optional, Union, Any, Type, cast, Tuple
import logging

from uno.domain.service import UnoEntityService
from uno.core.errors.result import Result
from uno.queries.entities import Query, QueryPath, QueryValue
from uno.queries.domain_repositories import (
    QueryPathRepository,
    QueryValueRepository,
    QueryRepository,
)
from uno.queries.errors import QueryExecutionError, QueryPathError, QueryNotFoundError
from uno.queries.filter_manager import UnoFilterManager, get_filter_manager
from uno.queries.executor import QueryExecutor, get_query_executor
from uno.enums import Include, Match


class QueryPathService(UnoEntityService[QueryPath]):
    """Service for query path entities."""

    def __init__(self, repository: QueryPathRepository):
        """Initialize the service.

        Args:
            repository: The repository for query path entities.
        """
        super().__init__(repository)
        self.repository = repository

    async def find_by_attribute_id(self, attribute_id: str) -> Result[list[QueryPath]]:
        """Find query paths by attribute ID.

        Args:
            attribute_id: The ID of the attribute to search for.

        Returns:
            Success with a list of query paths associated with the attribute,
            or Failure if an error occurs.
        """
        try:
            paths = await self.repository.find_by_attribute_id(attribute_id)
            return Success(paths)
        except Exception as e:
            return Failure(str(e))

    async def find_by_meta_type_id(self, meta_type_id: str) -> Result[list[QueryPath]]:
        """Find query paths by meta type ID.

        Args:
            meta_type_id: The ID of the meta type to search for.

        Returns:
            Success with a list of query paths associated with the meta type,
            or Failure if an error occurs.
        """
        try:
            paths = await self.repository.find_by_meta_type_id(meta_type_id)
            return Success(paths)
        except Exception as e:
            return Failure(str(e))

    async def find_by_path_name(self, path_name: str) -> Result[Optional[QueryPath]]:
        """Find a query path by name.

        Args:
            path_name: The name of the path to search for.

        Returns:
            Success with the query path if found, or None if not found,
            or Failure if an error occurs.
        """
        try:
            path = await self.repository.find_by_path_name(path_name)
            return Success(path)
        except Exception as e:
            return Failure(str(e))

    async def generate_for_model(
        self, model_class: Type[Any]
    ) -> Result[list[QueryPath]]:
        """Generate query paths for a model class.

        This method uses the FilterManager to create filter definitions from a model's schema
        and converts them to QueryPath entities.

        Args:
            model_class: The model class to generate paths for.

        Returns:
            Success with a list of generated query paths,
            or Failure if an error occurs.
        """
        try:
            # Get the filter manager
            filter_manager = get_filter_manager()

            # Create filters from the model class
            filters = filter_manager.create_filters_from_table(model_class)

            # Convert filters to query paths
            query_paths = []
            for filter_name, filter_def in filters.items():
                query_path = QueryPath(
                    source_meta_type_id=filter_def.source_meta_type_id,
                    target_meta_type_id=filter_def.target_meta_type_id,
                    cypher_path=filter_def.cypher_path(),
                    data_type=filter_def.data_type,
                )

                # Add path name as a description or additional property
                setattr(query_path, "path_name", filter_name)

                query_paths.append(query_path)

            return Success(query_paths)
        except Exception as e:
            return Failure(str(e))


class QueryValueService(UnoEntityService[QueryValue]):
    """Service for query value entities."""

    def __init__(self, repository: QueryValueRepository):
        """Initialize the service.

        Args:
            repository: The repository for query value entities.
        """
        super().__init__(repository)
        self.repository = repository

    async def find_by_query_id(self, query_id: str) -> Result[list[QueryValue]]:
        """Find query values by query ID.

        Args:
            query_id: The ID of the query to search for.

        Returns:
            Success with a list of query values associated with the query,
            or Failure if an error occurs.
        """
        try:
            values = await self.repository.find_by_query_id(query_id)
            return Success(values)
        except Exception as e:
            return Failure(str(e))

    async def find_by_query_path_id(
        self, query_path_id: str
    ) -> Result[list[QueryValue]]:
        """Find query values by query path ID.

        Args:
            query_path_id: The ID of the query path to search for.

        Returns:
            Success with a list of query values associated with the query path,
            or Failure if an error occurs.
        """
        try:
            values = await self.repository.find_by_query_path_id(query_path_id)
            return Success(values)
        except Exception as e:
            return Failure(str(e))

    async def delete_for_query(self, query_id: str) -> Result[None]:
        """Delete all query values for a query.

        Args:
            query_id: The ID of the query to delete values for.

        Returns:
            Success if the values were deleted, Failure otherwise.
        """
        return await self.repository.delete_for_query(query_id)


class QueryService(UnoEntityService[Query]):
    """Service for query entities."""

    def __init__(
        self,
        repository: QueryRepository,
        query_value_service: QueryValueService,
        query_path_service: QueryPathService,
        logger: logging.Logger | None = None,
    ):
        """Initialize the service.

        Args:
            repository: The repository for query entities.
            query_value_service: The service for query value entities.
            query_path_service: The service for query path entities.
            logger: Optional logger for diagnostic output.
        """
        super().__init__(repository)
        self.repository = repository
        self.query_value_service = query_value_service
        self.query_path_service = query_path_service
        self.logger = logger or logging.getLogger(__name__)

        # Initialize the query executor
        self.query_executor = get_query_executor()

    async def find_by_name(self, name: str) -> Result[Optional[Query]]:
        """Find a query by name.

        Args:
            name: The name of the query to search for.

        Returns:
            Success with the query if found, or None if not found,
            or Failure if an error occurs.
        """
        try:
            query = await self.repository.find_by_name(name)
            return Success(query)
        except Exception as e:
            return Failure(str(e))

    async def find_by_meta_type_id(self, meta_type_id: str) -> Result[list[Query]]:
        """Find queries by meta type ID.

        Args:
            meta_type_id: The ID of the meta type to search for.

        Returns:
            Success with a list of queries associated with the meta type,
            or Failure if an error occurs.
        """
        try:
            queries = await self.repository.find_by_meta_type_id(meta_type_id)
            return Success(queries)
        except Exception as e:
            return Failure(str(e))

    async def get_with_values(self, query_id: str) -> Result[Query]:
        """Get a query with its values populated.

        Args:
            query_id: The ID of the query to search for.

        Returns:
            Success with the query if found, Failure otherwise.
        """
        return await self.repository.find_with_values(query_id)

    async def list_with_values(
        self, meta_type_id: str | None = None
    ) -> Result[list[Query]]:
        """List all queries with their values populated.

        Args:
            meta_type_id: Optional meta type ID to filter by.

        Returns:
            Success with a list of queries if found, Failure otherwise.
        """
        return await self.repository.find_all_with_values(meta_type_id)

    async def create_with_values(
        self, query: Query, values: list[dict[str, Any]]
    ) -> Result[Query]:
        """Create a query with its values.

        Args:
            query: The query to create.
            values: The values to associate with the query.

        Returns:
            Success with the created query if successful, Failure otherwise.
        """
        try:
            # Create the query
            create_result = await self.create(query)
            if create_result.is_failure:
                return create_result

            created_query = create_result.value

            # Create query values
            for value_data in values:
                path_id = value_data.get("query_path_id")
                if not path_id:
                    return Failure(f"Missing query_path_id in value data: {value_data}")

                path_result = await self.query_path_service.get(path_id)
                if path_result.is_failure:
                    return Failure(f"Invalid query_path_id: {path_id}")

                query_path = path_result.value

                query_value = QueryValue(
                    query_path_id=path_id,
                    query_id=created_query.id,
                    include=value_data.get("include", Include.INCLUDE),
                    match=value_data.get("match", Match.AND),
                    lookup=value_data.get("lookup", "equal"),
                    values=value_data.get("values", []),
                )

                # Add bidirectional relationships
                created_query.add_query_value(query_value)

                # Create the query value
                value_result = await self.query_value_service.create(query_value)
                if value_result.is_failure:
                    return value_result

            # Return the query with the values loaded
            return await self.get_with_values(created_query.id)
        except Exception as e:
            return Failure(str(e))

    async def update_with_values(
        self, query_id: str, query_data: dict[str, Any], values: list[dict[str, Any]]
    ) -> Result[Query]:
        """Update a query with its values.

        Args:
            query_id: The ID of the query to update.
            query_data: The data to update the query with.
            values: The values to associate with the query.

        Returns:
            Success with the updated query if successful, Failure otherwise.
        """
        try:
            # Get the query
            query_result = await self.get(query_id)
            if query_result.is_failure:
                return query_result

            query = query_result.value

            # Update the query
            for key, value in query_data.items():
                if hasattr(query, key) and key != "id":
                    setattr(query, key, value)

            update_result = await self.update(query)
            if update_result.is_failure:
                return update_result

            # Delete existing values
            delete_result = await self.query_value_service.delete_for_query(query_id)
            if delete_result.is_failure:
                return delete_result

            # Create new values
            for value_data in values:
                path_id = value_data.get("query_path_id")
                if not path_id:
                    return Failure(f"Missing query_path_id in value data: {value_data}")

                path_result = await self.query_path_service.get(path_id)
                if path_result.is_failure:
                    return Failure(f"Invalid query_path_id: {path_id}")

                query_path = path_result.value

                query_value = QueryValue(
                    query_path_id=path_id,
                    query_id=query_id,
                    include=value_data.get("include", Include.INCLUDE),
                    match=value_data.get("match", Match.AND),
                    lookup=value_data.get("lookup", "equal"),
                    values=value_data.get("values", []),
                )

                # Create the query value
                value_result = await self.query_value_service.create(query_value)
                if value_result.is_failure:
                    return value_result

            # Return the query with the values loaded
            return await self.get_with_values(query_id)
        except Exception as e:
            return Failure(str(e))

    async def delete_with_values(self, query_id: str) -> Result[None]:
        """Delete a query with its values.

        Args:
            query_id: The ID of the query to delete.

        Returns:
            Success if the query was deleted, Failure otherwise.
        """
        try:
            # Delete query values
            delete_values_result = await self.query_value_service.delete_for_query(
                query_id
            )
            if delete_values_result.is_failure:
                return delete_values_result

            # Delete the query
            delete_result = await self.delete(query_id)
            return delete_result
        except Exception as e:
            return Failure(str(e))

    async def execute_query(
        self,
        query_id: str,
        filters: dict[str, Any] | None = None,
        force_refresh: bool = False,
    ) -> Result[list[str]]:
        """Execute a query and return matching record IDs.

        This method uses the QueryExecutor to execute a query and return matching record IDs.

        Args:
            query_id: The ID of the query to execute.
            filters: Additional filters to apply.
            force_refresh: If True, bypass cache and force a fresh query.

        Returns:
            Success with a list of matching record IDs if successful, Failure otherwise.
        """
        try:
            # Get the query with values
            query_result = await self.get_with_values(query_id)
            if query_result.is_failure:
                return Failure(
                    QueryNotFoundError(f"Query with ID {query_id} not found")
                )

            query = query_result.value

            # Execute the query using the QueryExecutor
            executor_result = await self.query_executor.execute_query(
                query, session=None, force_refresh=force_refresh
            )

            if executor_result.is_failure:
                error = executor_result.error
                return Failure(error)

            # Get the matching record IDs
            record_ids = executor_result.value

            return Success(record_ids)
        except QueryExecutionError as e:
            return Failure(e)
        except QueryPathError as e:
            return Failure(e)
        except Exception as e:
            return Failure(
                QueryExecutionError(
                    reason=str(e),
                    query_id=query_id,
                    original_exception=str(type(e).__name__),
                )
            )

    async def count_query_matches(
        self, query_id: str, force_refresh: bool = False
    ) -> Result[int]:
        """Count the number of records that match a query.

        This method uses the QueryExecutor to count the number of records that match a query.

        Args:
            query_id: The ID of the query to count matches for.
            force_refresh: If True, bypass cache and force a fresh count.

        Returns:
            Success with the count of matching records if successful, Failure otherwise.
        """
        try:
            # Get the query with values
            query_result = await self.get_with_values(query_id)
            if query_result.is_failure:
                return Failure(
                    QueryNotFoundError(f"Query with ID {query_id} not found")
                )

            query = query_result.value

            # Count the matches using the QueryExecutor
            count_result = await self.query_executor.count_query_matches(
                query, session=None, force_refresh=force_refresh
            )

            if count_result.is_failure:
                error = count_result.error
                return Failure(error)

            # Get the match count
            count = count_result.value

            return Success(count)
        except QueryExecutionError as e:
            return Failure(e)
        except QueryPathError as e:
            return Failure(e)
        except Exception as e:
            return Failure(
                QueryExecutionError(
                    reason=str(e),
                    query_id=query_id,
                    operation="count",
                    original_exception=str(type(e).__name__),
                )
            )

    async def check_record_matches_query(
        self, query_id: str, record_id: str, force_refresh: bool = False
    ) -> Result[bool]:
        """Check if a record matches a query.

        This method uses the QueryExecutor to check if a specific record matches a query.

        Args:
            query_id: The ID of the query to check against.
            record_id: The ID of the record to check.
            force_refresh: If True, bypass cache and force a fresh check.

        Returns:
            Success with True if the record matches, False otherwise,
            or Failure if an error occurs.
        """
        try:
            # Get the query with values
            query_result = await self.get_with_values(query_id)
            if query_result.is_failure:
                return Failure(
                    QueryNotFoundError(f"Query with ID {query_id} not found")
                )

            query = query_result.value

            # Check if the record matches the query using the QueryExecutor
            match_result = await self.query_executor.check_record_matches_query(
                query, record_id, session=None, force_refresh=force_refresh
            )

            if match_result.is_failure:
                error = match_result.error
                return Failure(error)

            # Get the match result
            is_match = match_result.value

            return Success(is_match)
        except QueryExecutionError as e:
            return Failure(e)
        except QueryPathError as e:
            return Failure(e)
        except Exception as e:
            return Failure(
                QueryExecutionError(
                    reason=str(e),
                    query_id=query_id,
                    record_id=record_id,
                    operation="check_record",
                    original_exception=str(type(e).__name__),
                )
            )

    async def invalidate_cache(self, meta_type_id: str | None = None) -> Result[int]:
        """Invalidate the query cache.

        This method invalidates the query cache for a specific meta type or all meta types.

        Args:
            meta_type_id: Optional meta type ID to invalidate cache for.

        Returns:
            Success with the number of cache entries invalidated,
            or Failure if an error occurs.
        """
        try:
            count = 0

            if meta_type_id:
                # Invalidate cache for a specific meta type
                count = await self.query_executor.invalidate_cache_for_meta_type(
                    meta_type_id
                )
            else:
                # Invalidate all caches
                count = await self.query_executor.clear_cache()

            return Success(count)
        except Exception as e:
            return Failure(str(e))

    async def create_filter_manager(
        self, model_class: Type[Any]
    ) -> Result[UnoFilterManager]:
        """Create a filter manager for a model class.

        This method creates a filter manager and initializes it with filters
        generated from the model class.

        Args:
            model_class: The model class to create filters for.

        Returns:
            Success with the filter manager if successful, Failure otherwise.
        """
        try:
            # Create a filter manager
            filter_manager = UnoFilterManager(logger=self.logger)

            # Initialize with filters from the model class
            filters = filter_manager.create_filters_from_table(model_class)

            return Success(filter_manager)
        except Exception as e:
            return Failure(str(e))

    async def execute_query_with_filters(
        self, entity_type: str, filters: dict[str, Any]
    ) -> Result[Tuple[list[dict[str, Any]], int]]:
        """Execute a query with filters.

        This method is similar to the legacy `execute_query` method but uses the
        new filter system. It's provided for backward compatibility.

        Args:
            entity_type: The type of entity to filter.
            filters: The filters to apply.

        Returns:
            Success with a tuple of (entities, count) if successful, Failure otherwise.
        """
        try:
            # Create a filter manager for the entity type
            from uno.dependencies.service import get_entity_model_class

            model_class = get_entity_model_class(entity_type)

            if not model_class:
                return Failure(f"Invalid entity type: {entity_type}")

            filter_manager_result = await self.create_filter_manager(model_class)
            if filter_manager_result.is_failure:
                return filter_manager_result

            filter_manager = filter_manager_result.value

            # Validate and process the filters
            from uno.core.types import FilterParam

            filter_param = FilterParam(**filters)

            validated_filters = filter_manager.validate_filter_params(
                filter_param, model_class
            )

            # Execute the query using the repository for the entity type
            from uno.database.repository import get_repository_for_entity_type

            repo = await get_repository_for_entity_type(entity_type)

            entities = await repo.list(filters=validated_filters)
            count = len(entities)

            # Convert entities to dictionaries
            entity_dicts = [entity.to_dict() for entity in entities]

            return Success((entity_dicts, count))
        except Exception as e:
            return Failure(str(e))
