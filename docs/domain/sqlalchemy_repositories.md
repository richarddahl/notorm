# SQLAlchemy Repositories

The SQLAlchemy repository implementation provides a powerful way to bridge domain models with PostgreSQL databases using SQLAlchemy, while maintaining clean separation of concerns through the specification pattern.

## Overview

The SQLAlchemy repository system in Uno provides:

1. Full integration with the domain specification pattern
2. Async-first database operations for modern application architectures 
3. Type-safe repository interfaces with generics
4. Result pattern for clear error handling
5. Unit of work pattern for transaction management
6. Comprehensive repository operations (get, find, count, exists, add, update, remove)

## Key Components

### SQLAlchemyRepository

The `SQLAlchemyRepository` class is a concrete implementation of the `AsyncRepositoryProtocol` that uses SQLAlchemy for database access.

```python
class SQLAlchemyRepository(Generic[T, M], AsyncRepositoryProtocol[T]):
    """
    Repository implementation for SQLAlchemy.
    
    This class provides a base implementation of the repository protocol
    using SQLAlchemy for data access and specification translation.
    """
```

Key features:

- Generic type parameters for entities (`T`) and models (`M`)
- Translation of domain specifications to SQLAlchemy queries
- Conversion between domain entities and SQLAlchemy models
- Asynchronous database operations
- Result pattern for error handling

### SQLAlchemyUnitOfWork

The `SQLAlchemyUnitOfWork` class implements the `AsyncUnitOfWorkProtocol` to provide transaction management for SQLAlchemy operations.

```python
class SQLAlchemyUnitOfWork(AsyncUnitOfWorkProtocol):
    """
    Unit of work implementation for SQLAlchemy.
    
    This class manages transactions and tracks changes to entities.
    """
```

Key features:

- Transaction management with async context managers
- Entity tracking (new, dirty, removed)
- Automatic commits and rollbacks
- Repository management and creation

## Usage

### Basic Repository Operations

```python
# Create the SQLAlchemy model
class ProductModel(Base):
    __tablename__ = "products"
    
    id = sa.Column(sa.String, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    price = sa.Column(sa.Float, nullable=False)
    category = sa.Column(sa.String, nullable=False)
    in_stock = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

# Create the domain entity
class Product(Entity):
    name: str
    price: float
    category: str
    in_stock: bool = True
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: Optional[datetime] = None

# Create a session factory
async def get_session() -> AsyncSession:
    engine = create_async_engine(DATABASE_URL)
    async_session = AsyncSession(engine, expire_on_commit=False)
    return async_session

# Create the repository
repository = SQLAlchemyRepository(
    entity_type=Product,
    model_class=ProductModel,
    session_factory=get_session
)

# Get an entity by ID
product = await repository.get("123")

# Find entities with a specification
tools_spec = AttributeSpecification("category", "Tools")
tools = await repository.find(tools_spec)

# Find in-stock tools with a complex specification
in_stock_tools_spec = AndSpecification(
    AttributeSpecification("category", "Tools"),
    AttributeSpecification("in_stock", True)
)
in_stock_tools = await repository.find(in_stock_tools_spec)

# Count entities with a specification
count = await repository.count(in_stock_tools_spec)

# Check if entities exist with a specification
exists = await repository.exists(in_stock_tools_spec)

# Add a new entity
new_product = Product(
    id=str(uuid4()),
    name="New Product",
    price=99.99,
    category="New Category"
)
await repository.add(new_product)

# Update an entity
product.price = 129.99
product.updated_at = datetime.now(timezone.utc)
await repository.update(product)

# Remove an entity
await repository.remove(product)
```

### Using the Unit of Work Pattern

```python
# Create repositories
product_repository = SQLAlchemyRepository(
    entity_type=Product,
    model_class=ProductModel,
    session_factory=get_session
)

# Create unit of work
unit_of_work = SQLAlchemyUnitOfWork(
    session_factory=get_session,
    repositories={Product: product_repository}
)

# Use unit of work to manage transactions
async with unit_of_work:
    # Create entities
    new_product1 = Product(
        id=str(uuid4()),
        name="Product 1",
        price=19.99,
        category="Category A"
    )
    
    new_product2 = Product(
        id=str(uuid4()),
        name="Product 2",
        price=29.99,
        category="Category B"
    )
    
    # Register entities
    await unit_of_work.register_new(new_product1)
    await unit_of_work.register_new(new_product2)
    
    # Changes are automatically committed at the end of the context block
    # If an exception occurs, changes are automatically rolled back
```

### Working with the Result Pattern

```python
# Get an entity with a result object
result = await repository.get_result("123")
if result.is_success:
    product = result.entity
    # Process product
else:
    error = result.error
    # Handle error

# Find entities with a result object
result = await repository.find_result(tools_spec)
if result.is_success:
    tools = result.entities
    # Process tools
else:
    error = result.error
    # Handle error

# Add an entity with a result object
result = await repository.add_result(new_product)
if result.is_success:
    # Product added successfully
else:
    error = result.error
    # Handle error
```

## SQLAlchemy Specification Translation

The `SQLAlchemyRepository` uses the `PostgreSQLSpecificationTranslator` to translate domain specifications to SQLAlchemy queries:

```python
# Create a specification for in-stock products in the Tools category
in_stock_tools_spec = AndSpecification(
    AttributeSpecification("category", "Tools"),
    AttributeSpecification("in_stock", True)
)

# The translator converts this to:
# SELECT * FROM products 
# WHERE category = 'Tools' AND in_stock = true
```

The translator supports:
- Logical operations (AND, OR, NOT)
- Attribute comparisons
- Complex nested specifications

## Best Practices

1. **Use specifications for domain logic**: Keep database query details out of your domain logic
2. **Use the unit of work pattern**: Manage transactions explicitly with the unit of work pattern
3. **Handle results properly**: Use the result pattern for error handling
4. **Keep repositories domain-focused**: Focus on domain operations in repositories
5. **Use repository factories**: Create repository factories to simplify repository creation
6. **Create entity-specific repositories**: Extend `SQLAlchemyRepository` for entity-specific repositories

## Entity-Specific Repositories

For better organization and additional functionality, extend `SQLAlchemyRepository` for specific entity types:

```python
class ProductRepository(SQLAlchemyRepository[Product, ProductModel]):
    """Repository for Product entities."""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        super().__init__(
            entity_type=Product,
            model_class=ProductModel,
            session_factory=session_factory
        )
    
    async def find_by_category(self, category: str) -> List[Product]:
        """Find products by category."""
        spec = AttributeSpecification("category", category)
        return await self.find(spec)
    
    async def find_in_stock(self) -> List[Product]:
        """Find in-stock products."""
        spec = AttributeSpecification("in_stock", True)
        return await self.find(spec)
    
    async def find_by_price_range(self, min_price: float, max_price: float) -> List[Product]:
        """Find products in a price range."""
        min_price_spec = AttributeSpecification("price", min_price).not_()
        max_price_spec = AttributeSpecification("price", max_price).not_()
        price_range_spec = min_price_spec.and_(max_price_spec)
        return await self.find(price_range_spec)
```

## Integration with Dependency Injection

```python
from uno.dependencies.container import Container
from uno.dependencies.interfaces import UnoServiceProtocol
from uno.domain.sqlalchemy_repositories import SQLAlchemyRepository

# Register repositories in the container
container = Container()
container.register(
    ProductRepository,
    lambda: ProductRepository(session_factory=get_session)
)

# Use the container to resolve repositories
class ProductService(UnoServiceProtocol):
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository
        
    async def get_product(self, product_id: str) -> Optional[Product]:
        return await self.product_repository.get(product_id)
        
    async def get_products_by_category(self, category: str) -> List[Product]:
        return await self.product_repository.find_by_category(category)

# Register the service
container.register(
    ProductService,
    lambda c: ProductService(product_repository=c.resolve(ProductRepository))
)
```

## Conclusion

The SQLAlchemy repository implementation provides a powerful, type-safe, and clean way to work with PostgreSQL databases in Uno. By using the specification pattern, domain logic remains clean and focused on business rules while database details are handled by the repository implementations.