"""Domain services for the Queries module."""
from typing import Dict, List, Optional, Union, Any, cast

from uno.core.domain import UnoEntityService
from uno.core.errors.result import Result, Success, Failure
from uno.queries.entities import Query, QueryPath, QueryValue
from uno.queries.domain_repositories import (
    QueryPathRepository,
    QueryValueRepository,
    QueryRepository,
)


class QueryPathService(UnoEntityService[QueryPath]):
    """Service for query path entities."""

    def __init__(self, repository: QueryPathRepository):
        """Initialize the service.
        
        Args:
            repository: The repository for query path entities.
        """
        super().__init__(repository)
        self.repository = repository

    async def find_by_attribute_id(self, attribute_id: str) -> Result[List[QueryPath]]:
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

    async def find_by_meta_type_id(self, meta_type_id: str) -> Result[List[QueryPath]]:
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


class QueryValueService(UnoEntityService[QueryValue]):
    """Service for query value entities."""

    def __init__(self, repository: QueryValueRepository):
        """Initialize the service.
        
        Args:
            repository: The repository for query value entities.
        """
        super().__init__(repository)
        self.repository = repository

    async def find_by_query_id(self, query_id: str) -> Result[List[QueryValue]]:
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

    async def find_by_query_path_id(self, query_path_id: str) -> Result[List[QueryValue]]:
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
    ):
        """Initialize the service.
        
        Args:
            repository: The repository for query entities.
            query_value_service: The service for query value entities.
            query_path_service: The service for query path entities.
        """
        super().__init__(repository)
        self.repository = repository
        self.query_value_service = query_value_service
        self.query_path_service = query_path_service

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

    async def find_by_meta_type_id(self, meta_type_id: str) -> Result[List[Query]]:
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

    async def list_with_values(self, meta_type_id: Optional[str] = None) -> Result[List[Query]]:
        """List all queries with their values populated.
        
        Args:
            meta_type_id: Optional meta type ID to filter by.
            
        Returns:
            Success with a list of queries if found, Failure otherwise.
        """
        return await self.repository.find_all_with_values(meta_type_id)

    async def create_with_values(
        self, query: Query, values: List[Dict[str, Any]]
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
                    value=value_data.get("value"),
                    lookup_type=value_data.get("lookup_type", "eq"),
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
        self, query_id: str, query_data: Dict[str, Any], values: List[Dict[str, Any]]
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
                    value=value_data.get("value"),
                    lookup_type=value_data.get("lookup_type", "eq"),
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
            delete_values_result = await self.query_value_service.delete_for_query(query_id)
            if delete_values_result.is_failure:
                return delete_values_result
            
            # Delete the query
            delete_result = await self.delete(query_id)
            return delete_result
        except Exception as e:
            return Failure(str(e))

    async def execute_query(
        self, query_id: str, entity_type: str, filters: Optional[Dict[str, Any]] = None
    ) -> Result[List[Dict[str, Any]]]:
        """Execute a query to filter entities.
        
        Args:
            query_id: The ID of the query to execute.
            entity_type: The type of entity to filter.
            filters: Additional filters to apply.
            
        Returns:
            Success with a list of filtered entities if successful, Failure otherwise.
        """
        try:
            # Get the query with values
            query_result = await self.get_with_values(query_id)
            if query_result.is_failure:
                return query_result
            
            query = query_result.value
            
            # Validate that the query is for the requested entity type
            if query.query_meta_type_id != entity_type:
                return Failure(
                    f"Query is for entity type {query.query_meta_type_id}, "
                    f"but requested entity type is {entity_type}"
                )
            
            # Combine query values with additional filters
            combined_filters = filters or {}
            
            for value in query.query_values:
                path_result = await self.query_path_service.get(value.query_path_id)
                if path_result.is_failure:
                    return path_result
                
                path = path_result.value
                combined_filters[path.path_name] = {
                    "lookup": value.lookup_type,
                    "val": value.value,
                }
            
            # Execute the query using the repository
            # Note: This is simplified; in a real implementation, you would need to
            # use a repository for the entity type being queried
            from uno.database.repository import get_repository_for_entity_type
            repo = await get_repository_for_entity_type(entity_type)
            
            entities = await repo.list(filters=combined_filters)
            
            # Convert entities to dictionaries
            entity_dicts = [entity.to_dict() for entity in entities]
            
            return Success(entity_dicts)
        except Exception as e:
            return Failure(str(e))