"""
Examples demonstrating different database interaction approaches in uno.

This module contains examples of the various database interaction approaches
available in uno, including:
1. CQRS and Read Models
2. UnoObj Pattern
3. Repository Pattern
4. Enhanced Database API
5. SQL Generation API

These examples help developers understand when to use each approach based on
their specific requirements.
"""

import asyncio
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from decimal import Decimal
from uuid import uuid4

# Import uno components
from uno.core.cqrs import Command, CommandHandler, Query, QueryHandler, get_mediator
from uno.core.result import Result, Success, Failure
from uno.domain.event_store import EventStore, PostgresEventStore
from uno.read_model import (
    ReadModel, ReadModelId, Projection, ProjectionService,
    ReadModelRepository, PostgresReadModelRepository
)
from uno.model import UnoObj
from uno.database.repository import Repository
from uno.database.enhanced_db import EnhancedDB
from uno.sql.statement import SelectBuilder, InsertBuilder, UpdateBuilder, DeleteBuilder
from uno.sql.emitter import PostgresEmitter
from uno.domain.unit_of_work import UnitOfWork, SqlAlchemyUnitOfWork
from uno.read_model.query_service import ReadModelQueryService, EnhancedQueryService, SearchQuery
from uno.dependencies import inject_dependency

# Example 1: CQRS and Read Models
# ===============================

# Command Side
class CreateProductCommand(Command[str]):
    """Command to create a new product."""
    name: str
    description: str
    price: Decimal
    category: str
    tags: List[str] = []


class CreateProductCommandHandler(CommandHandler[CreateProductCommand, str]):
    """Handler for CreateProductCommand."""
    
    def __init__(self, unit_of_work_factory):
        self.unit_of_work_factory = unit_of_work_factory
        self.events = []
    
    async def handle(self, command: CreateProductCommand) -> Result[str]:
        """Handle the command to create a product."""
        try:
            async with self.unit_of_work_factory() as uow:
                # Create a unique product ID
                product_id = str(uuid4())
                
                # In a real implementation, this would validate and store the product
                # in the write database
                
                # Create an event for the product creation
                product_created_event = {
                    "type": "ProductCreated",
                    "aggregate_id": product_id,
                    "aggregate_type": "Product",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "data": {
                        "id": product_id,
                        "name": command.name,
                        "description": command.description,
                        "price": float(command.price),
                        "category": command.category,
                        "tags": command.tags
                    }
                }
                
                # Store the event
                await uow.get_repository("events").add(product_created_event)
                
                # Commit the transaction
                await uow.commit()
                
                # In a real implementation, this event would be published to an event bus
                # to update read models
                
                return Success(product_id)
        except Exception as e:
            return Failure(str(e))


# Query Side
class GetProductByIdQuery(Query[Dict[str, Any]]):
    """Query to get a product by ID."""
    product_id: str


class GetProductByIdQueryHandler(QueryHandler[GetProductByIdQuery, Dict[str, Any]]):
    """Handler for GetProductByIdQuery."""
    
    def __init__(self, read_model_service):
        self.read_model_service = read_model_service
    
    async def handle(self, query: GetProductByIdQuery) -> Result[Optional[Dict[str, Any]]]:
        """Handle the query to get a product by ID."""
        try:
            # Get the product from the read model
            read_model_id = ReadModelId(value=query.product_id)
            product = await self.read_model_service.get_by_id(read_model_id)
            
            if not product:
                return Success(None)
            
            # Return the product data
            return Success(product.data)
        except Exception as e:
            return Failure(str(e))


class SearchProductsQuery(Query[List[Dict[str, Any]]]):
    """Query to search for products."""
    search_term: str
    category: Optional[str] = None
    page: int = 1
    page_size: int = 10


class SearchProductsQueryHandler(QueryHandler[SearchProductsQuery, List[Dict[str, Any]]]):
    """Handler for SearchProductsQuery."""
    
    def __init__(self, query_service):
        self.query_service = query_service
    
    async def handle(self, query: SearchProductsQuery) -> Result[List[Dict[str, Any]]]:
        """Handle the query to search for products."""
        try:
            # Create a search query for the read model
            search_query = SearchQuery(
                search_term=query.search_term,
                filters={"category": query.category} if query.category else {},
                page=query.page,
                page_size=query.page_size
            )
            
            # Execute the search
            result = await self.query_service.search(search_query)
            
            # Return the results
            return Success([item.data for item in result.items])
        except Exception as e:
            return Failure(str(e))


# Example CQRS usage
async def example_cqrs():
    """Example of using CQRS and Read Models."""
    print("\n=== CQRS and Read Models Example ===")
    
    # Set up dependencies
    db_provider = EnhancedDB.get_instance()
    unit_of_work_factory = lambda: SqlAlchemyUnitOfWork(db_provider)
    
    # Create repositories
    event_store = PostgresEventStore(db_provider)
    product_repository = PostgresReadModelRepository(
        model_type=dict,
        db_provider=db_provider,
        table_name="product_read_models"
    )
    
    # Create services
    read_model_service = ReadModelQueryService(
        repository=product_repository,
        model_type=dict
    )
    query_service = EnhancedQueryService(
        repository=product_repository,
        model_type=dict
    )
    
    # Create handlers
    create_product_handler = CreateProductCommandHandler(unit_of_work_factory)
    get_product_handler = GetProductByIdQueryHandler(read_model_service)
    search_products_handler = SearchProductsQueryHandler(query_service)
    
    # Register handlers with mediator
    mediator = get_mediator()
    mediator.register_command_handler(CreateProductCommand, create_product_handler)
    mediator.register_query_handler(GetProductByIdQuery, get_product_handler)
    mediator.register_query_handler(SearchProductsQuery, search_products_handler)
    
    # Create a product
    create_command = CreateProductCommand(
        name="CQRS Example Product",
        description="A product created using CQRS",
        price=Decimal("29.99"),
        category="Examples",
        tags=["cqrs", "example"]
    )
    
    create_result = await mediator.execute_command(create_command)
    if create_result.is_success():
        product_id = create_result.value
        print(f"Created product with ID: {product_id}")
        
        # Simulate the read model being updated from the event
        # (In a real system, this would happen via event handlers)
        product_read_model = ReadModel(
            id=ReadModelId(value=product_id),
            version=1,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            data={
                "id": product_id,
                "name": create_command.name,
                "description": create_command.description,
                "price": float(create_command.price),
                "category": create_command.category,
                "tags": create_command.tags
            }
        )
        await product_repository.save(product_read_model)
        
        # Get the product by ID
        get_query = GetProductByIdQuery(product_id=product_id)
        get_result = await mediator.execute_query(get_query)
        
        if get_result.is_success() and get_result.value:
            print(f"Retrieved product: {get_result.value['name']}")
        
        # Search for products
        search_query = SearchProductsQuery(
            search_term="Example",
            category="Examples"
        )
        search_result = await mediator.execute_query(search_query)
        
        if search_result.is_success():
            print(f"Found {len(search_result.value)} products in search")
            for product in search_result.value:
                print(f" - {product['name']}")
    
    print("CQRS Example Completed")


# Example 2: UnoObj Pattern
# =========================

async def example_unoobj():
    """Example of using the UnoObj pattern."""
    print("\n=== UnoObj Pattern Example ===")
    
    # Create a new product
    product = UnoObj("products")
    product.name = "UnoObj Example Product"
    product.description = "A product created using UnoObj"
    product.price = 39.99
    product.category = "Examples"
    product.tags = ["unoobj", "example"]
    
    # Save the product
    await product.create()
    print(f"Created product with ID: {product.id}")
    
    # Get the product by ID
    retrieved_product = await UnoObj("products").filter(id=product.id).get_one()
    print(f"Retrieved product: {retrieved_product.name}")
    
    # Update the product
    retrieved_product.price = 35.99
    await retrieved_product.update()
    print(f"Updated product price: {retrieved_product.price}")
    
    # Search for products
    found_products = await UnoObj("products").filter(
        category="Examples",
        name__contains="Example"
    ).get()
    
    print(f"Found {len(found_products)} products in search")
    for p in found_products:
        print(f" - {p.name}: ${p.price}")
    
    print("UnoObj Example Completed")


# Example 3: Repository Pattern
# ============================

# Domain model
class Product:
    """Product domain entity."""
    
    def __init__(
        self,
        name: str,
        description: str,
        price: Decimal,
        category: str,
        tags: List[str] = None,
        id: str = None
    ):
        self.id = id or str(uuid4())
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.tags = tags or []
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
    
    def update_price(self, new_price: Decimal) -> None:
        """Update the product price."""
        if new_price <= Decimal(0):
            raise ValueError("Price must be greater than zero")
        self.price = new_price
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            price=Decimal(str(data.get("price", 0))),
            category=data.get("category", ""),
            tags=data.get("tags", [])
        )


# Custom repository implementation
class ProductRepository(Repository[Product]):
    """Repository for Product entities."""
    
    def __init__(self, db_provider):
        self.db = db_provider
    
    async def add(self, product: Product) -> Product:
        """Add a product to the repository."""
        query = """
        INSERT INTO products (id, name, description, price, category, tags, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """
        params = [
            product.id,
            product.name,
            product.description,
            float(product.price),
            product.category,
            product.tags,
            product.created_at,
            product.updated_at
        ]
        
        result = await self.db.execute_query(query, params)
        return product
    
    async def get_by_id(self, id: str) -> Optional[Product]:
        """Get a product by ID."""
        query = "SELECT * FROM products WHERE id = $1"
        result = await self.db.execute_query(query, [id])
        
        if not result or len(result) == 0:
            return None
        
        row = result[0]
        return Product.from_dict(row)
    
    async def update(self, product: Product) -> Product:
        """Update a product."""
        query = """
        UPDATE products
        SET name = $1, description = $2, price = $3, category = $4, tags = $5, updated_at = $6
        WHERE id = $7
        """
        params = [
            product.name,
            product.description,
            float(product.price),
            product.category,
            product.tags,
            product.updated_at,
            product.id
        ]
        
        await self.db.execute_query(query, params)
        return product
    
    async def find(self, criteria: Dict[str, Any]) -> List[Product]:
        """Find products matching criteria."""
        conditions = []
        params = []
        param_index = 1
        
        for key, value in criteria.items():
            if key == "name__contains":
                conditions.append(f"name LIKE ${param_index}")
                params.append(f"%{value}%")
            elif key == "price__gt":
                conditions.append(f"price > ${param_index}")
                params.append(value)
            elif key == "price__lt":
                conditions.append(f"price < ${param_index}")
                params.append(value)
            else:
                conditions.append(f"{key} = ${param_index}")
                params.append(value)
            param_index += 1
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM products WHERE {where_clause}"
        
        result = await self.db.execute_query(query, params)
        return [Product.from_dict(row) for row in result]


async def example_repository():
    """Example of using the Repository pattern."""
    print("\n=== Repository Pattern Example ===")
    
    # Create repository
    db_provider = EnhancedDB.get_instance()
    repository = ProductRepository(db_provider)
    
    # Create a product
    product = Product(
        name="Repository Example Product",
        description="A product created using the Repository pattern",
        price=Decimal("49.99"),
        category="Examples",
        tags=["repository", "example"]
    )
    
    # Save the product
    created_product = await repository.add(product)
    print(f"Created product with ID: {created_product.id}")
    
    # Get the product by ID
    retrieved_product = await repository.get_by_id(created_product.id)
    print(f"Retrieved product: {retrieved_product.name}")
    
    # Update the product price using domain logic
    retrieved_product.update_price(Decimal("45.99"))
    updated_product = await repository.update(retrieved_product)
    print(f"Updated product price: {updated_product.price}")
    
    # Search for products
    found_products = await repository.find({
        "category": "Examples",
        "name__contains": "Repository"
    })
    
    print(f"Found {len(found_products)} products in search")
    for p in found_products:
        print(f" - {p.name}: ${p.price}")
    
    print("Repository Example Completed")


# Example 4: Enhanced Database API
# ===============================

async def example_enhanced_db():
    """Example of using the Enhanced Database API."""
    print("\n=== Enhanced Database API Example ===")
    
    # Get database instance
    db = EnhancedDB.get_instance()
    
    # Create a product using direct SQL
    product_id = str(uuid4())
    insert_query = """
    INSERT INTO products (id, name, description, price, category, tags, created_at, updated_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """
    
    params = [
        product_id,
        "Enhanced DB Example Product",
        "A product created using the Enhanced Database API",
        59.99,
        "Examples",
        ["enhanced", "db", "example"],
        datetime.now(UTC),
        datetime.now(UTC)
    ]
    
    await db.execute_query(insert_query, params)
    print(f"Created product with ID: {product_id}")
    
    # Get the product using direct SQL
    select_query = "SELECT * FROM products WHERE id = $1"
    result = await db.execute_query(select_query, [product_id])
    
    if result and len(result) > 0:
        product = result[0]
        print(f"Retrieved product: {product['name']}")
    
    # Update the product using direct SQL
    update_query = """
    UPDATE products
    SET price = $1, updated_at = $2
    WHERE id = $3
    """
    
    await db.execute_query(update_query, [55.99, datetime.now(UTC), product_id])
    print("Updated product price")
    
    # Search for products using direct SQL with complex conditions
    search_query = """
    SELECT * FROM products 
    WHERE category = $1 
    AND name LIKE $2
    ORDER BY price DESC
    """
    
    search_results = await db.execute_query(
        search_query, 
        ["Examples", "%Enhanced%"]
    )
    
    print(f"Found {len(search_results)} products in search")
    for p in search_results:
        print(f" - {p['name']}: ${p['price']}")
    
    # Use batch operations for multiple inserts
    batch_values = []
    for i in range(3):
        batch_values.append([
            str(uuid4()),
            f"Batch Product {i+1}",
            f"A batch-created product {i+1}",
            9.99 + i * 10,
            "Examples",
            ["batch", "example"],
            datetime.now(UTC),
            datetime.now(UTC)
        ])
    
    await db.batch_insert(
        "products",
        ["id", "name", "description", "price", "category", "tags", "created_at", "updated_at"],
        batch_values
    )
    
    print("Created 3 products using batch insert")
    
    print("Enhanced Database API Example Completed")


# Example 5: SQL Generation API
# ============================

async def example_sql_generation():
    """Example of using the SQL Generation API."""
    print("\n=== SQL Generation API Example ===")
    
    # Create SQL emitter
    emitter = PostgresEmitter()
    
    # Get database instance
    db = EnhancedDB.get_instance()
    
    # Build an INSERT statement
    product_id = str(uuid4())
    insert_builder = (
        InsertBuilder()
        .into_table("products")
        .columns([
            "id", "name", "description", "price", 
            "category", "tags", "created_at", "updated_at"
        ])
        .values([
            product_id,
            "SQL Generation Example Product",
            "A product created using the SQL Generation API",
            69.99,
            "Examples",
            ["sql", "generation", "example"],
            datetime.now(UTC),
            datetime.now(UTC)
        ])
        .returning("id")
    )
    
    # Generate and execute SQL
    insert_sql, insert_params = emitter.emit(insert_builder)
    await db.execute_query(insert_sql, insert_params)
    print(f"Created product with ID: {product_id}")
    
    # Build a SELECT statement
    select_builder = (
        SelectBuilder()
        .select("*")
        .from_table("products")
        .where("id = ?")
        .bind_params([product_id])
    )
    
    # Generate and execute SQL
    select_sql, select_params = emitter.emit(select_builder)
    select_result = await db.execute_query(select_sql, select_params)
    
    if select_result and len(select_result) > 0:
        product = select_result[0]
        print(f"Retrieved product: {product['name']}")
    
    # Build an UPDATE statement
    update_builder = (
        UpdateBuilder()
        .update_table("products")
        .set_columns(["price", "updated_at"])
        .set_values([65.99, datetime.now(UTC)])
        .where("id = ?")
        .bind_params([product_id])
    )
    
    # Generate and execute SQL
    update_sql, update_params = emitter.emit(update_builder)
    await db.execute_query(update_sql, update_params)
    print("Updated product price")
    
    # Build a complex SELECT statement
    complex_select_builder = (
        SelectBuilder()
        .select("p.id", "p.name", "p.price", "c.name AS category_name")
        .from_table("products p")
        .join("categories c", "p.category = c.id")
        .where("p.category = ? AND p.price > ?")
        .order_by("p.price DESC")
        .limit(10)
        .bind_params(["Examples", 50])
    )
    
    # Generate SQL (not executing this one since we don't have the categories table)
    complex_sql, complex_params = emitter.emit(complex_select_builder)
    print("\nGenerated complex SQL:")
    print(complex_sql)
    print("Parameters:", complex_params)
    
    # Build a DELETE statement
    delete_builder = (
        DeleteBuilder()
        .from_table("products")
        .where("id = ?")
        .bind_params([product_id])
    )
    
    # Generate SQL (not executing to keep the example product)
    delete_sql, delete_params = emitter.emit(delete_builder)
    print("\nGenerated DELETE SQL (not executing):")
    print(delete_sql)
    print("Parameters:", delete_params)
    
    print("SQL Generation API Example Completed")


# Main function to run all examples
async def main():
    """Run all examples."""
    print("=== Database Interaction Approaches in uno ===")
    
    # Simulate table creation (in a real app, this would be handled by migrations)
    db = EnhancedDB.get_instance()
    
    try:
        # Drop table if it exists
        await db.execute_query("DROP TABLE IF EXISTS products", [])
        
        # Create products table
        create_table_query = """
        CREATE TABLE products (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            category VARCHAR(100),
            tags TEXT[],
            created_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE
        )
        """
        await db.execute_query(create_table_query, [])
        print("Created products table")
        
        # Run examples
        await example_cqrs()
        await example_unoobj()
        await example_repository()
        await example_enhanced_db()
        await example_sql_generation()
        
        print("\n=== All Examples Completed ===")
        
        # Clean up (optional)
        # await db.execute_query("DROP TABLE products", [])
        # print("Dropped products table")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())