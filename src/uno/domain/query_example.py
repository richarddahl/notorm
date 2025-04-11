"""
Example usage of the enhanced query system.

This module demonstrates how to use the enhanced query system with
path-based queries, caching, and performance tracking.
"""

import logging
from typing import List, Dict, Any, Optional, Type, Tuple

from pydantic import BaseModel

from uno.domain.core import Entity
from uno.domain.repository import Repository
from uno.domain.enhanced_query import EnhancedQueryExecutor, QueryMetadata
from uno.domain.graph_path_query import (
    GraphPathQuery,
    GraphPathQueryService,
    PathQuerySpecification
)
from uno.domain.query_optimizer import (
    QueryPerformanceTracker,
    QueryResultCache
)
from uno.queries.filter import UnoFilter
from uno.queries.objs import QueryPath


# Example entity
class Product(Entity):
    """Example product entity."""
    
    name: str
    description: Optional[str] = None
    price: float
    category_id: Optional[str] = None
    is_active: bool = True


# Example repository
class ProductRepository(Repository[Product]):
    """Repository for products."""
    
    async def get(self, id: str) -> Optional[Product]:
        """Get a product by ID."""
        # Implementation would interact with the database
        pass
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0
    ) -> List[Product]:
        """List products matching filters."""
        # Implementation would interact with the database
        pass
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count products matching filters."""
        # Implementation would interact with the database
        pass


# Example usage
async def example_query_usage() -> None:
    """Example of using the enhanced query system."""
    
    # Set up logging
    logger = logging.getLogger("query_example")
    
    # Create performance tracking and caching components
    performance_tracker = QueryPerformanceTracker(logger=logger)
    cache = QueryResultCache(ttl_seconds=300, logger=logger)
    
    # Create a repository
    repository = ProductRepository()
    
    # Create an enhanced query executor
    query_executor = EnhancedQueryExecutor(
        entity_type=Product,
        repository=repository,
        performance_tracker=performance_tracker,
        cache=cache,
        logger=logger
    )
    
    # Create a query specification
    query = BaseModel(
        filters={"category_id": "electronics", "price": {"lookup": "gte", "val": 100}},
        order_by=["price"],
        limit=10,
        offset=0
    )
    
    # Execute the query
    results, metadata = await query_executor.execute(query)
    
    # Print results
    logger.info(f"Found {len(results.items)} products")
    logger.info(f"Query took {metadata.execution_time} seconds")
    
    # Create a materialized view for a frequently-used query
    query_executor.create_materialized_view(
        name="active_electronics",
        query=BaseModel(
            filters={"category_id": "electronics", "is_active": True},
            order_by=["name"]
        ),
        refresh_interval=3600  # Refresh every hour
    )


# Example of using graph path queries
async def example_path_query_usage() -> None:
    """Example of using graph path queries."""
    
    # Set up logging
    logger = logging.getLogger("path_query_example")
    
    # Create the path query executor
    path_query = GraphPathQuery(
        track_performance=True,
        use_cache=True,
        cache_ttl=300,
        logger=logger
    )
    
    # Create the path query service
    path_query_service = GraphPathQueryService(
        path_query=path_query,
        logger=logger
    )
    
    # Create a repository
    repository = ProductRepository()
    
    # Create a path query using a string path
    string_path_query = PathQuerySpecification(
        path="(s:Product)-[:CATEGORY]->(c:Category)",
        params={"c.name": "Electronics"},
        limit=10
    )
    
    # Execute the path query to get product IDs
    product_ids, metadata = await path_query.execute(string_path_query)
    logger.info(f"Found {len(product_ids)} product IDs")
    
    # Or use the service to get full product entities
    products, metadata = await path_query_service.query_entities(
        query=string_path_query,
        repository=repository,
        entity_type=Product
    )
    logger.info(f"Found {len(products)} products")
    
    # Create a path query using a QueryPath object
    # (Assuming we have a QueryPath instance)
    query_path = QueryPath(
        source_meta_type_id="product",
        target_meta_type_id="category",
        cypher_path="(s:Product)-[:CATEGORY]->(t:Category)"
    )
    
    path_query = PathQuerySpecification(
        path=query_path,
        params={"t.name": "Electronics"},
        limit=10
    )
    
    # Execute the query
    products, metadata = await path_query_service.query_entities(
        query=path_query,
        repository=repository,
        entity_type=Product
    )
    
    # Check if a path query would return any results
    exists = await path_query_service.query_exists(path_query)
    logger.info(f"Query would return results: {exists}")


# Example complex query using multiple hops
async def example_complex_path_query() -> None:
    """Example of a complex multi-hop path query."""
    
    logger = logging.getLogger("complex_query_example")
    
    # Create the path query executor
    path_query = GraphPathQuery(logger=logger)
    
    # Create the path query service
    path_query_service = GraphPathQueryService(path_query=path_query, logger=logger)
    
    # Create a repository
    repository = ProductRepository()
    
    # Complex path query: Find products that are in a category that belongs to a department
    # where a specific user has made purchases in the last 30 days
    complex_path = """
    (s:Product)-[:CATEGORY]->(c:Category)-[:DEPARTMENT]->(d:Department)<-[:PURCHASED_IN]-(o:Order)-[:PLACED_BY]->(u:User)
    """
    
    query = PathQuerySpecification(
        path=complex_path,
        params={
            "u.id": "user123",
            "o.created_at": {"lookup": "gte", "val": "2025-03-01T00:00:00Z"}
        },
        limit=20,
        order_by="s.popularity",
        order_direction="desc"
    )
    
    # Execute the query
    products, metadata = await path_query_service.query_entities(
        query=query,
        repository=repository,
        entity_type=Product
    )
    
    logger.info(f"Found {len(products)} recommended products for user123")
    logger.info(f"Query execution time: {metadata.execution_time} seconds")
    
    # Get the count without retrieving entities
    count = await path_query_service.count_query_results(query)
    logger.info(f"Total matching products: {count}")


# Example of working with the selective graph updater
async def example_selective_update() -> None:
    """Example of using the selective graph updater."""
    
    from uno.domain.selective_updater import GraphChangeEvent, SelectiveGraphUpdater
    
    logger = logging.getLogger("selective_update_example")
    
    # Create the selective graph updater
    updater = SelectiveGraphUpdater(logger=logger)
    
    # Create a change event for a new product
    create_event = GraphChangeEvent(
        entity_type="product",
        entity_id="prod456",
        change_type=GraphChangeEvent.CREATE,
        data={
            "id": "prod456",
            "name": "New Smartphone",
            "price": 899.99,
            "category_id": "cat123",
            "is_active": True
        }
    )
    
    # Handle the event (this would update the graph)
    await updater.handle_entity_change(create_event)
    
    # Create an update event
    update_event = GraphChangeEvent(
        entity_type="product",
        entity_id="prod456",
        change_type=GraphChangeEvent.UPDATE,
        data={
            "id": "prod456",
            "name": "New Smartphone",
            "price": 799.99,  # Price changed
            "category_id": "cat456",  # Category changed
            "is_active": True
        },
        previous_data={
            "id": "prod456",
            "name": "New Smartphone",
            "price": 899.99,
            "category_id": "cat123",
            "is_active": True
        },
        changed_fields={"price", "category_id"}
    )
    
    # Handle the update event
    await updater.handle_entity_change(update_event)
    
    # Create a delete event
    delete_event = GraphChangeEvent(
        entity_type="product",
        entity_id="prod456",
        change_type=GraphChangeEvent.DELETE,
        previous_data={
            "id": "prod456",
            "name": "New Smartphone",
            "price": 799.99,
            "category_id": "cat456",
            "is_active": True
        }
    )
    
    # Handle the delete event
    await updater.handle_entity_change(delete_event)