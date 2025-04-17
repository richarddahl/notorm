# Entity-Specific Repositories

Entity-specific repositories provide specialized data access for different domain entity types, implementing domain-specific queries and operations while leveraging the generic repository infrastructure.

## Overview

The entity-specific repository implementation in Uno provides:

1. Specialized repositories for different entity types (User, Product, Order, etc.)
2. Domain-specific query methods that encapsulate common access patterns
3. Rich domain operations that maintain entity invariants and business rules
4. Full integration with the specification pattern and SQLAlchemy
5. Asynchronous operations for modern application architecture

## Repository Structure

The entity-specific repositories are organized in a modular, extensible structure:

```
src/uno/domain/repositories/
  ├── __init__.py            # Package exports
  ├── base.py                # Base Repository class
  ├── unit_of_work.py        # Unit of Work implementations
  └── sqlalchemy/            # SQLAlchemy implementations
      ├── __init__.py        # Package exports
      ├── base.py            # SQLAlchemy base classes 
      ├── user.py            # UserRepository
      ├── product.py         # ProductRepository
      └── order.py           # OrderRepository
```

## Key Repository Implementations

### UserRepository

The `UserRepository` provides specialized operations for user management:

```python
class UserRepository(SQLAlchemyRepository[User, UserModel]):
    """Repository for User entities."""
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username."""
        # Implementation...
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        # Implementation...
    
    async def find_by_username_or_email(self, value: str) -> Optional[User]:
        """Find a user by username or email."""
        # Implementation...
    
    async def find_active(self) -> List[User]:
        """Find all active users."""
        # Implementation...
    
    async def find_by_role(self, role: UserRole) -> List[User]:
        """Find users by role."""
        # Implementation...
    
    async def find_active_by_role(self, role: UserRole) -> List[User]:
        """Find active users by role."""
        # Implementation...
    
    async def deactivate(self, user: User) -> None:
        """Deactivate a user."""
        # Implementation...
    
    async def activate(self, user: User) -> None:
        """Activate a user."""
        # Implementation...
    
    async def change_role(self, user: User, role: UserRole) -> None:
        """Change a user's role."""
        # Implementation...
```

### ProductRepository

The `ProductRepository` provides specialized operations for product management:

```python
class ProductRepository(SQLAlchemyRepository[Product, ProductModel]):
    """Repository for Product entities."""
    
    async def find_by_category(self, category: ProductCategory) -> List[Product]:
        """Find products by category."""
        # Implementation...
    
    async def find_by_sku(self, sku: str) -> Optional[Product]:
        """Find a product by SKU."""
        # Implementation...
    
    async def find_in_stock(self) -> List[Product]:
        """Find all in-stock products."""
        # Implementation...
    
    async def find_in_stock_by_category(self, category: ProductCategory) -> List[Product]:
        """Find in-stock products by category."""
        # Implementation...
    
    async def find_by_price_range(self, min_price: float, max_price: float) -> List[Product]:
        """Find products in a price range."""
        # Implementation...
    
    async def update_stock_quantity(self, product: Product, quantity: int) -> None:
        """Update a product's stock quantity."""
        # Implementation...
    
    async def find_low_stock(self, threshold: int = 10) -> List[Product]:
        """Find products with low stock."""
        # Implementation...
```

### OrderRepository

The `OrderRepository` provides specialized operations for order management:

```python
class OrderRepository(SQLAlchemyRepository[Order, OrderModel]):
    """Repository for Order entities."""
    
    async def find_by_user(self, user_id: str) -> List[Order]:
        """Find orders by user ID."""
        # Implementation...
    
    async def find_by_status(self, status: OrderStatus) -> List[Order]:
        """Find orders by status."""
        # Implementation...
    
    async def find_by_user_and_status(self, user_id: str, status: OrderStatus) -> List[Order]:
        """Find orders by user ID and status."""
        # Implementation...
    
    async def update_status(self, order: Order, status: OrderStatus) -> None:
        """Update an order's status."""
        # Implementation...
```

## Usage Examples

### Basic Repository Operations

```python
# Create repository
user_repository = UserRepository(session_factory=get_session)

# Find a user by username
user = await user_repository.find_by_username("johndoe")

# Find active users with admin role
admins = await user_repository.find_active_by_role(UserRole.ADMIN)

# Deactivate a user
await user_repository.deactivate(user)

# Change a user's role
await user_repository.change_role(user, UserRole.MANAGER)
```

### Using with Unit of Work

```python
# Create repositories
user_repository = UserRepository(session_factory=get_session)
product_repository = ProductRepository(session_factory=get_session)

# Create unit of work
unit_of_work = SQLAlchemyUnitOfWork(
    session_factory=get_session,
    repositories={
        User: user_repository,
        Product: product_repository
    }
)

# Use unit of work for transaction management
async with unit_of_work:
    # Update product stock
    product = await product_repository.find_by_sku("PROD123")
    await product_repository.update_stock_quantity(product, 10)
    
    # Create new user
    new_user = User(
        id=str(uuid4()),
        username="newuser",
        email="newuser@example.com",
        password_hash="hashedpassword",
        full_name="New User",
        role=UserRole.USER
    )
    await unit_of_work.register_new(new_user)
    
    # Changes are committed automatically at the end of the context block
    # If an exception occurs, changes are rolled back automatically
```

### Using with Dependency Injection

```python
from fastapi import Depends
from uno.dependencies.container import Container

# Register repositories in the container
container = Container()
container.register(UserRepository, lambda: UserRepository(session_factory=get_session))
container.register(ProductRepository, lambda: ProductRepository(session_factory=get_session))

# Use in FastAPI endpoints
@app.get("/users/{username}")
async def get_user(username: str, user_repository: UserRepository = Depends(lambda: container.resolve(UserRepository))):
    user = await user_repository.find_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()

@app.get("/products/category/{category}")
async def get_products_by_category(
    category: str, 
    product_repository: ProductRepository = Depends(lambda: container.resolve(ProductRepository))
):
    try:
        category_enum = ProductCategory(category)
        products = await product_repository.find_by_category(category_enum)
        return [product.to_dict() for product in products]
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
```

## Benefits

1. **Encapsulated Domain Logic**: Domain-specific queries are encapsulated in the repository
2. **Type Safety**: Strong typing with generics throughout
3. **Clean API**: Clear, focused API for each entity type
4. **Maintainability**: Easy to extend with new query methods
5. **Performance**: Optimized for common query patterns
6. **Testability**: Easy to mock for unit testing

## Best Practices

1. **Keep Repositories Focused**: Each repository should focus on a single entity type
2. **Use Domain Language**: Name repository methods using domain terminology
3. **Leverage Specifications**: Use the specification pattern for complex queries
4. **Maintain Entity Invariants**: Update entity state using domain operations
5. **Use Result Pattern**: Use the result pattern for error handling
6. **Use Unit of Work**: Use the unit of work pattern for transaction management

## Integrating Enhanced Specifications

Entity-specific repositories integrate seamlessly with the enhanced specification pattern, which provides specialized specifications for common query patterns.

### Creating Entity-Specific Specification Factories

For each entity type, create a specialized specification factory:

```python
from uno.domain.specifications import specification_factory, enhance_specification_factory

# Create a product-specific specification factory
ProductSpec = specification_factory(Product)

# Enhance it with additional methods for common operations
EnhancedProductSpec = enhance_specification_factory(ProductSpec)
```

### Implementing Repository Methods with Enhanced Specifications

Use the enhanced specification factories in repository methods:

```python
class ProductRepository(SQLAlchemyRepository[Product, ProductModel]):
    """Repository for Product entities with enhanced specifications."""
    
    async def find_by_price_range(self, min_price: float, max_price: float) -> List[Product]:
        """Find products in a price range."""
        # Use the enhanced range specification
        spec = EnhancedProductSpec.range("price", min_price, max_price)
        return await self.find(spec)
    
    async def find_by_name_pattern(self, pattern: str) -> List[Product]:
        """Find products by name pattern."""
        # Use the text match specification
        spec = EnhancedProductSpec.contains("name", pattern)
        return await self.find(spec)
    
    async def find_in_categories(self, categories: List[ProductCategory]) -> List[Product]:
        """Find products in multiple categories."""
        # Use the in-list specification
        spec = EnhancedProductSpec.in_list("category", categories)
        return await self.find(spec)
    
    async def find_created_within_days(self, days: int) -> List[Product]:
        """Find products created within the last n days."""
        # Use the relative date specification
        spec = EnhancedProductSpec.created_within_days("created_at", days)
        return await self.find(spec)
    
    async def find_with_tags(self, tags: List[str]) -> List[Product]:
        """Find products with specific tags."""
        # Use the collection contains specification
        spec = EnhancedProductSpec.collection_contains("tags", tags)
        return await self.find(spec)
    
    async def search_products(
        self,
        keywords: Optional[str] = None,
        category: Optional[ProductCategory] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[Product]:
        """Search products with multiple criteria."""
        specs = []
        
        if keywords:
            specs.append(EnhancedProductSpec.contains("name", keywords))
        
        if category:
            specs.append(EnhancedProductSpec.eq("category", category))
        
        if min_price is not None and max_price is not None:
            specs.append(EnhancedProductSpec.range("price", min_price, max_price))
        
        if in_stock_only:
            specs.append(EnhancedProductSpec.eq("in_stock", True))
        
        if tags:
            specs.append(EnhancedProductSpec.collection_contains("tags", tags))
        
        # Combine all specifications with AND
        if not specs:
            return await self.find_all()
        
        final_spec = specs[0]
        for spec in specs[1:]:
            final_spec = final_spec.and_(spec)
        
        return await self.find(final_spec)
```

### Advanced Query Examples with Enhanced Specifications

```python
# Repository using enhanced specifications for complex queries
user_repository = UserRepository(session_factory=get_session)

# Find users who have been active in the last 30 days
active_users = await user_repository.find(
    EnhancedUserSpec.created_within_days("last_login", 30)
)

# Find users in specific roles with confirmed email
confirmed_admins = await user_repository.find(
    EnhancedUserSpec.in_list("role", [UserRole.ADMIN, UserRole.SUPER_ADMIN])
    .and_(EnhancedUserSpec.eq("email_confirmed", True))
)

# Find users with specific permissions in their JSON metadata
users_with_permission = await user_repository.find(
    EnhancedUserSpec.json_path("metadata", ["permissions", "can_manage_users"], True)
)
```

## Extension Points

The entity-specific repositories can be extended in several ways:

1. **Additional Query Methods**: Add new query methods for common domain operations
2. **Specialized Specifications**: Create specialized specifications for complex queries
3. **Caching**: Add caching for frequently accessed entities
4. **Event Handling**: Integrate with domain events for event sourcing
5. **Auditing**: Add auditing for entity changes
6. **Custom Specification Types**: Create domain-specific specification types
7. **Query Optimization**: Add query hints and optimizations for specific access patterns

## Conclusion

Entity-specific repositories provide a clean, domain-focused way to access and manipulate domain entities. By encapsulating domain-specific queries and operations, they provide a rich, type-safe API while maintaining the separation of concerns between domain logic and data access.

When combined with the enhanced specification pattern, entity-specific repositories offer a powerful, flexible, and efficient way to express and execute complex domain queries. This approach results in more maintainable code, better performance, and a clearer expression of domain concepts in your application.