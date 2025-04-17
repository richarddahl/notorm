"""
Example demonstrating CQRS performance optimizations and monitoring capabilities.

This example shows how to use the various performance optimization techniques
and monitoring capabilities provided by the uno CQRS implementation, including:

1. Batch command processing
2. Parallel query execution
3. Command and query metrics collection
4. Health monitoring
5. Tracing and observability
"""

import asyncio
import time
from datetime import datetime, UTC
from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import uuid4

# Import CQRS components
from uno.core.cqrs import Command, CommandHandler, Query, QueryHandler, Mediator
from uno.core.cqrs_optimizations import (
    BatchCommandBus, ParallelQueryBus, CachedQueryHandler, 
    OptimizedMediator, get_optimized_mediator
)
from uno.core.cqrs_monitoring import (
    InMemoryMetricsProvider, CQRSMetrics, TracingMediator,
    CommandBusHealthCheck, QueryBusHealthCheck,
    CQRSHealthMonitor, get_tracing_mediator
)
from uno.core.result import Result, Success, Failure

# Models for the example
class Product:
    """Product entity for the example."""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        price: Decimal,
        category: str,
        tags: List[str] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.tags = tags or []
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

# In-memory repository for the example
class ProductRepository:
    """In-memory product repository for the example."""
    
    def __init__(self):
        self.products: Dict[str, Product] = {}
    
    async def add(self, product: Product) -> None:
        """Add a product to the repository."""
        self.products[product.id] = product
    
    async def get_by_id(self, id: str) -> Optional[Product]:
        """Get a product by ID."""
        return self.products.get(id)
    
    async def find_by_category(self, category: str) -> List[Product]:
        """Find products by category."""
        return [p for p in self.products.values() if p.category == category]
    
    async def find_all(self) -> List[Product]:
        """Find all products."""
        return list(self.products.values())
    
    async def update(self, product: Product) -> None:
        """Update a product."""
        if product.id in self.products:
            product.updated_at = datetime.now(UTC)
            self.products[product.id] = product
    
    async def delete(self, id: str) -> None:
        """Delete a product."""
        if id in self.products:
            del self.products[id]
    
    async def add_batch(self, products: List[Product]) -> None:
        """Add multiple products in a batch."""
        for product in products:
            self.products[product.id] = product


# Commands
class CreateProductCommand(Command[str]):
    """Command to create a new product."""
    name: str
    description: str
    price: Decimal
    category: str
    tags: List[str] = []


class UpdateProductCommand(Command[bool]):
    """Command to update a product."""
    product_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class DeleteProductCommand(Command[bool]):
    """Command to delete a product."""
    product_id: str


class CreateProductsInBatchCommand(Command[List[str]]):
    """Command to create multiple products in a batch."""
    products: List[Dict[str, Any]]


# Command Handlers
class CreateProductCommandHandler(CommandHandler[CreateProductCommand, str]):
    """Handler for CreateProductCommand."""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def handle(self, command: CreateProductCommand) -> Result[str]:
        """Handle the create product command."""
        try:
            # Create a product ID
            product_id = str(uuid4())
            
            # Create a product instance
            product = Product(
                id=product_id,
                name=command.name,
                description=command.description,
                price=command.price,
                category=command.category,
                tags=command.tags
            )
            
            # Add to repository
            await self.repository.add(product)
            
            # Simulate some work
            await asyncio.sleep(0.05)
            
            return Success(product_id)
        except Exception as e:
            return Failure(str(e))


class UpdateProductCommandHandler(CommandHandler[UpdateProductCommand, bool]):
    """Handler for UpdateProductCommand."""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def handle(self, command: UpdateProductCommand) -> Result[bool]:
        """Handle the update product command."""
        try:
            # Get the product
            product = await self.repository.get_by_id(command.product_id)
            if not product:
                return Failure(f"Product with ID {command.product_id} not found")
            
            # Update fields
            if command.name is not None:
                product.name = command.name
            if command.description is not None:
                product.description = command.description
            if command.price is not None:
                product.price = command.price
            if command.category is not None:
                product.category = command.category
            if command.tags is not None:
                product.tags = command.tags
            
            # Update repository
            await self.repository.update(product)
            
            # Simulate some work
            await asyncio.sleep(0.03)
            
            return Success(True)
        except Exception as e:
            return Failure(str(e))


class DeleteProductCommandHandler(CommandHandler[DeleteProductCommand, bool]):
    """Handler for DeleteProductCommand."""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def handle(self, command: DeleteProductCommand) -> Result[bool]:
        """Handle the delete product command."""
        try:
            # Check if product exists
            product = await self.repository.get_by_id(command.product_id)
            if not product:
                return Failure(f"Product with ID {command.product_id} not found")
            
            # Delete from repository
            await self.repository.delete(command.product_id)
            
            # Simulate some work
            await asyncio.sleep(0.02)
            
            return Success(True)
        except Exception as e:
            return Failure(str(e))


class CreateProductsInBatchCommandHandler(CommandHandler[CreateProductsInBatchCommand, List[str]]):
    """Handler for CreateProductsInBatchCommand."""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def handle(self, command: CreateProductsInBatchCommand) -> Result[List[str]]:
        """Handle the create products in batch command."""
        try:
            products = []
            product_ids = []
            
            # Create product instances
            for product_data in command.products:
                product_id = str(uuid4())
                product_ids.append(product_id)
                
                product = Product(
                    id=product_id,
                    name=product_data.get("name", ""),
                    description=product_data.get("description", ""),
                    price=Decimal(str(product_data.get("price", 0))),
                    category=product_data.get("category", ""),
                    tags=product_data.get("tags", [])
                )
                products.append(product)
            
            # Add to repository in batch
            await self.repository.add_batch(products)
            
            # Simulate some work
            await asyncio.sleep(0.1)
            
            return Success(product_ids)
        except Exception as e:
            return Failure(str(e))


# Queries
class GetProductByIdQuery(Query[Dict[str, Any]]):
    """Query to get a product by ID."""
    product_id: str


class GetProductsByCategoryQuery(Query[List[Dict[str, Any]]]):
    """Query to get products by category."""
    category: str


class GetAllProductsQuery(Query[List[Dict[str, Any]]]):
    """Query to get all products."""
    pass


# Query Handlers
class GetProductByIdQueryHandler(QueryHandler[GetProductByIdQuery, Dict[str, Any]]):
    """Handler for GetProductByIdQuery."""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def handle(self, query: GetProductByIdQuery) -> Result[Dict[str, Any]]:
        """Handle the get product by ID query."""
        try:
            # Get the product
            product = await self.repository.get_by_id(query.product_id)
            if not product:
                return Failure(f"Product with ID {query.product_id} not found")
            
            # Simulate some work
            await asyncio.sleep(0.01)
            
            return Success(product.to_dict())
        except Exception as e:
            return Failure(str(e))


class GetProductsByCategoryQueryHandler(QueryHandler[GetProductsByCategoryQuery, List[Dict[str, Any]]]):
    """Handler for GetProductsByCategoryQuery."""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def handle(self, query: GetProductsByCategoryQuery) -> Result[List[Dict[str, Any]]]:
        """Handle the get products by category query."""
        try:
            # Get products by category
            products = await self.repository.find_by_category(query.category)
            
            # Simulate some work
            await asyncio.sleep(0.02)
            
            return Success([p.to_dict() for p in products])
        except Exception as e:
            return Failure(str(e))


class GetAllProductsQueryHandler(QueryHandler[GetAllProductsQuery, List[Dict[str, Any]]]):
    """Handler for GetAllProductsQuery."""
    
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def handle(self, query: GetAllProductsQuery) -> Result[List[Dict[str, Any]]]:
        """Handle the get all products query."""
        try:
            # Get all products
            products = await self.repository.find_all()
            
            # Simulate some work
            await asyncio.sleep(0.03)
            
            return Success([p.to_dict() for p in products])
        except Exception as e:
            return Failure(str(e))


# Cached version of the query handler
class CachedGetProductByIdQueryHandler(CachedQueryHandler[GetProductByIdQuery, Dict[str, Any]]):
    """Cached handler for GetProductByIdQuery."""
    
    def __init__(self, repository: ProductRepository):
        # Create delegate handler
        delegate = GetProductByIdQueryHandler(repository)
        
        # Initialize cache
        super().__init__(
            delegate=delegate,
            ttl_seconds=60  # Cache for 1 minute
        )


# Example 1: Basic CQRS with metrics
async def example_basic_cqrs_with_metrics():
    """Example of basic CQRS with metrics collection."""
    print("\n=== Example 1: Basic CQRS with Metrics ===")
    
    # Create repository
    repository = ProductRepository()
    
    # Create metrics provider and metrics collector
    metrics_provider = InMemoryMetricsProvider()
    metrics = CQRSMetrics(metrics_provider)
    
    # Create tracing mediator
    mediator = TracingMediator(metrics=metrics)
    
    # Create command handlers
    create_handler = CreateProductCommandHandler(repository)
    update_handler = UpdateProductCommandHandler(repository)
    delete_handler = DeleteProductCommandHandler(repository)
    
    # Create query handlers
    get_by_id_handler = GetProductByIdQueryHandler(repository)
    get_by_category_handler = GetProductsByCategoryQueryHandler(repository)
    get_all_handler = GetAllProductsQueryHandler(repository)
    
    # Register handlers with mediator
    mediator.register_command_handler(CreateProductCommand, create_handler)
    mediator.register_command_handler(UpdateProductCommand, update_handler)
    mediator.register_command_handler(DeleteProductCommand, delete_handler)
    
    mediator.register_query_handler(GetProductByIdQuery, get_by_id_handler)
    mediator.register_query_handler(GetProductsByCategoryQuery, get_by_category_handler)
    mediator.register_query_handler(GetAllProductsQuery, get_all_handler)
    
    # Create and execute commands and queries
    
    # Create products
    print("Creating products...")
    product_ids = []
    for i in range(5):
        command = CreateProductCommand(
            name=f"Product {i+1}",
            description=f"Description for product {i+1}",
            price=Decimal(f"{10 + i * 5}.99"),
            category="Electronics" if i % 2 == 0 else "Books",
            tags=["example", f"tag{i+1}"]
        )
        
        result = await mediator.execute_command(command)
        if result.is_success():
            product_ids.append(result.value)
            print(f"  Created product {i+1} with ID: {result.value}")
    
    # Get products by ID
    print("\nGetting products by ID...")
    for product_id in product_ids[:2]:
        query = GetProductByIdQuery(product_id=product_id)
        result = await mediator.execute_query(query)
        
        if result.is_success():
            product = result.value
            print(f"  Retrieved product: {product['name']} - ${product['price']}")
    
    # Get products by category
    print("\nGetting products by category...")
    query = GetProductsByCategoryQuery(category="Electronics")
    result = await mediator.execute_query(query)
    
    if result.is_success():
        products = result.value
        print(f"  Found {len(products)} electronics products:")
        for product in products:
            print(f"    - {product['name']}")
    
    # Update a product
    print("\nUpdating a product...")
    if product_ids:
        update_command = UpdateProductCommand(
            product_id=product_ids[0],
            name="Updated Product 1",
            price=Decimal("24.99")
        )
        
        result = await mediator.execute_command(update_command)
        if result.is_success():
            print(f"  Updated product {product_ids[0]}")
            
            # Get the updated product
            query = GetProductByIdQuery(product_id=product_ids[0])
            result = await mediator.execute_query(query)
            
            if result.is_success():
                product = result.value
                print(f"  Updated product details: {product['name']} - ${product['price']}")
    
    # Delete a product
    print("\nDeleting a product...")
    if len(product_ids) >= 2:
        delete_command = DeleteProductCommand(product_id=product_ids[1])
        result = await mediator.execute_command(delete_command)
        
        if result.is_success():
            print(f"  Deleted product {product_ids[1]}")
    
    # Display metrics
    print("\nCommand Metrics:")
    command_stats = metrics.get_command_stats()
    print(f"  Total commands executed: {sum(command_stats.get('count', {}).get('values', {}).values())}")
    
    print("\nQuery Metrics:")
    query_stats = metrics.get_query_stats()
    print(f"  Total queries executed: {sum(query_stats.get('count', {}).get('values', {}).values())}")
    
    print("Basic CQRS with Metrics Example Completed")


# Example 2: Batch Command Processing
async def example_batch_command_processing():
    """Example of batch command processing for improved performance."""
    print("\n=== Example 2: Batch Command Processing ===")
    
    # Create repository
    repository = ProductRepository()
    
    # Create optimized mediator
    mediator = get_optimized_mediator()
    
    # Create command handlers
    create_batch_handler = CreateProductsInBatchCommandHandler(repository)
    get_all_handler = GetAllProductsQueryHandler(repository)
    
    # Register handlers with mediator
    mediator.register_command_handler(CreateProductsInBatchCommand, create_batch_handler)
    mediator.register_query_handler(GetAllProductsQuery, get_all_handler)
    
    # Create batch of products
    print("Creating products in batch...")
    
    # Prepare batch data
    batch_products = []
    for i in range(10):
        batch_products.append({
            "name": f"Batch Product {i+1}",
            "description": f"Description for batch product {i+1}",
            "price": 10 + i * 2.5,
            "category": "Electronics" if i % 2 == 0 else "Books",
            "tags": ["batch", f"tag{i+1}"]
        })
    
    # Create batch command
    batch_command = CreateProductsInBatchCommand(products=batch_products)
    
    # Execute with standard command bus
    start_time = time.time()
    result = await mediator.execute_command(batch_command)
    standard_duration = time.time() - start_time
    
    if result.is_success():
        product_ids = result.value
        print(f"  Created {len(product_ids)} products in batch")
    
    # Execute with batch command bus
    start_time = time.time()
    result = await mediator.execute_batch([batch_command])
    batch_duration = time.time() - start_time
    
    if result and result[0].is_success():
        product_ids = result[0].value
        print(f"  Created {len(product_ids)} products with batch command bus")
    
    # Compare performance
    print("\nPerformance Comparison:")
    print(f"  Standard execution: {standard_duration:.4f} seconds")
    print(f"  Batch execution: {batch_duration:.4f} seconds")
    
    if standard_duration > 0:
        improvement = (standard_duration - batch_duration) / standard_duration * 100
        print(f"  Performance improvement: {improvement:.2f}%")
    
    # Get all products
    query = GetAllProductsQuery()
    result = await mediator.execute_query(query)
    
    if result.is_success():
        products = result.value
        print(f"\nRepository now contains {len(products)} products")
    
    print("Batch Command Processing Example Completed")


# Example 3: Parallel Query Execution
async def example_parallel_query_execution():
    """Example of parallel query execution for improved performance."""
    print("\n=== Example 3: Parallel Query Execution ===")
    
    # Create repository
    repository = ProductRepository()
    
    # Create optimized mediator
    mediator = get_optimized_mediator()
    
    # Create command and query handlers
    create_handler = CreateProductCommandHandler(repository)
    get_by_id_handler = GetProductByIdQueryHandler(repository)
    get_by_category_handler = GetProductsByCategoryQueryHandler(repository)
    
    # Register handlers with mediator
    mediator.register_command_handler(CreateProductCommand, create_handler)
    mediator.register_query_handler(GetProductByIdQuery, get_by_id_handler)
    mediator.register_query_handler(GetProductsByCategoryQuery, get_by_category_handler)
    
    # Create sample products
    print("Creating sample products...")
    product_ids = []
    categories = ["Electronics", "Books", "Clothing", "Food", "Toys"]
    
    for i in range(20):
        command = CreateProductCommand(
            name=f"Parallel Product {i+1}",
            description=f"Description for parallel product {i+1}",
            price=Decimal(f"{10 + i * 2}.99"),
            category=categories[i % len(categories)],
            tags=["parallel", f"tag{i+1}"]
        )
        
        result = await mediator.execute_command(command)
        if result.is_success():
            product_ids.append(result.value)
    
    print(f"  Created {len(product_ids)} products")
    
    # Create queries
    queries = []
    # Add product queries
    for product_id in product_ids[:5]:
        queries.append(GetProductByIdQuery(product_id=product_id))
    
    # Add category queries
    for category in categories:
        queries.append(GetProductsByCategoryQuery(category=category))
    
    # Execute queries sequentially
    print("\nExecuting queries sequentially...")
    start_time = time.time()
    sequential_results = []
    
    for query in queries:
        result = await mediator.execute_query(query)
        sequential_results.append(result)
    
    sequential_duration = time.time() - start_time
    print(f"  Sequential execution time: {sequential_duration:.4f} seconds")
    
    # Execute queries in parallel
    print("\nExecuting queries in parallel...")
    start_time = time.time()
    parallel_results = await mediator.execute_parallel_queries(queries)
    parallel_duration = time.time() - start_time
    
    print(f"  Parallel execution time: {parallel_duration:.4f} seconds")
    
    # Compare performance
    if sequential_duration > 0:
        improvement = (sequential_duration - parallel_duration) / sequential_duration * 100
        print(f"\nPerformance improvement: {improvement:.2f}%")
    
    # Verify results match
    results_match = len(sequential_results) == len(parallel_results)
    for i, (seq_result, par_result) in enumerate(zip(sequential_results, parallel_results)):
        if seq_result.is_success() != par_result.is_success():
            results_match = False
            break
    
    print(f"Results match: {results_match}")
    
    print("Parallel Query Execution Example Completed")


# Example 4: Query Caching
async def example_query_caching():
    """Example of query caching for improved performance."""
    print("\n=== Example 4: Query Caching ===")
    
    # Create repository
    repository = ProductRepository()
    
    # Create mediator
    mediator = Mediator()
    
    # Create command and query handlers
    create_handler = CreateProductCommandHandler(repository)
    
    # Create both standard and cached query handlers
    standard_handler = GetProductByIdQueryHandler(repository)
    cached_handler = CachedGetProductByIdQueryHandler(repository)
    
    # Register handlers with mediator
    mediator.register_command_handler(CreateProductCommand, create_handler)
    mediator.register_query_handler(GetProductByIdQuery, cached_handler)
    
    # Create sample product
    print("Creating sample product...")
    command = CreateProductCommand(
        name="Cached Product",
        description="A product for testing caching",
        price=Decimal("29.99"),
        category="Electronics",
        tags=["cached", "example"]
    )
    
    result = await mediator.execute_command(command)
    if result.is_success():
        product_id = result.value
        print(f"  Created product with ID: {product_id}")
        
        # Create query
        query = GetProductByIdQuery(product_id=product_id)
        
        # First query execution (cache miss)
        print("\nExecuting first query (cache miss)...")
        start_time = time.time()
        result1 = await mediator.execute_query(query)
        duration1 = time.time() - start_time
        
        if result1.is_success():
            print(f"  Retrieved product: {result1.value['name']}")
            print(f"  Duration: {duration1:.6f} seconds")
        
        # Second query execution (cache hit)
        print("\nExecuting second query (cache hit)...")
        start_time = time.time()
        result2 = await mediator.execute_query(query)
        duration2 = time.time() - start_time
        
        if result2.is_success():
            print(f"  Retrieved product: {result2.value['name']}")
            print(f"  Duration: {duration2:.6f} seconds")
        
        # Compare performance
        if duration1 > 0:
            improvement = (duration1 - duration2) / duration1 * 100
            print(f"\nCache performance improvement: {improvement:.2f}%")
        
        # Update the product
        print("\nUpdating product (which should invalidate cache)...")
        update_command = UpdateProductCommand(
            product_id=product_id,
            name="Updated Cached Product",
            price=Decimal("34.99")
        )
        
        # Replace the cached handler with standard handler to update the product
        mediator.register_query_handler(GetProductByIdQuery, standard_handler)
        
        # Register update handler
        update_handler = UpdateProductCommandHandler(repository)
        mediator.register_command_handler(UpdateProductCommand, update_handler)
        
        # Update product
        update_result = await mediator.execute_command(update_command)
        if update_result.is_success():
            print(f"  Updated product {product_id}")
            
            # Get updated product (using standard handler)
            updated_result = await mediator.execute_query(query)
            if updated_result.is_success():
                print(f"  Updated product details: {updated_result.value['name']} - ${updated_result.value['price']}")
        
        # Restore cached handler
        mediator.register_query_handler(GetProductByIdQuery, cached_handler)
        
        # Execute query again (should be cache miss due to update)
        print("\nExecuting query after update (should be cache miss)...")
        start_time = time.time()
        result3 = await mediator.execute_query(query)
        duration3 = time.time() - start_time
        
        if result3.is_success():
            print(f"  Retrieved product: {result3.value['name']} - ${result3.value['price']}")
            print(f"  Duration: {duration3:.6f} seconds")
    
    print("Query Caching Example Completed")


# Example 5: Health Monitoring
async def example_health_monitoring():
    """Example of health monitoring for CQRS components."""
    print("\n=== Example 5: Health Monitoring ===")
    
    # Create repository
    repository = ProductRepository()
    
    # Create mediator
    mediator = get_tracing_mediator()
    
    # Create command and query handlers
    create_handler = CreateProductCommandHandler(repository)
    get_by_id_handler = GetProductByIdQueryHandler(repository)
    
    # Register handlers with mediator
    mediator.register_command_handler(CreateProductCommand, create_handler)
    mediator.register_query_handler(GetProductByIdQuery, get_by_id_handler)
    
    # Create health monitor
    health_monitor = CQRSHealthMonitor(check_interval_seconds=10)
    
    # Register health checks
    health_monitor.register_health_check(
        "command_bus", 
        CommandBusHealthCheck(mediator.command_bus)
    )
    health_monitor.register_health_check(
        "query_bus", 
        QueryBusHealthCheck(mediator.query_bus)
    )
    
    # Start health monitoring
    await health_monitor.start_monitoring()
    
    # Create a sample product
    print("Creating sample product...")
    command = CreateProductCommand(
        name="Health Check Product",
        description="A product for testing health checks",
        price=Decimal("39.99"),
        category="Health",
        tags=["health", "check"]
    )
    
    result = await mediator.execute_command(command)
    if result.is_success():
        product_id = result.value
        print(f"  Created product with ID: {product_id}")
        
        # Query the product
        query = GetProductByIdQuery(product_id=product_id)
        query_result = await mediator.execute_query(query)
        
        if query_result.is_success():
            print(f"  Retrieved product: {query_result.value['name']}")
    
    # Check health status
    print("\nChecking health status...")
    health_status = await health_monitor.check_health()
    
    # Display health status
    for component, status in health_status.items():
        print(f"  {component}: {status.status}")
        print(f"    Details: {status.details}")
    
    # Get overall status
    overall_status = health_monitor.get_overall_status()
    print(f"\nOverall system status: {overall_status['status']}")
    
    # Stop health monitoring
    await health_monitor.stop_monitoring()
    
    print("Health Monitoring Example Completed")


# Main function to run all examples
async def main():
    """Run all examples."""
    print("=== CQRS Performance Optimizations and Monitoring Examples ===")
    
    # Run examples
    await example_basic_cqrs_with_metrics()
    await example_batch_command_processing()
    await example_parallel_query_execution()
    await example_query_caching()
    await example_health_monitoring()
    
    print("\n=== All Examples Completed ===")


if __name__ == "__main__":
    asyncio.run(main())