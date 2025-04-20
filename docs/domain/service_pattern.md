# Service Pattern in UNO

This document explains the Service pattern implementation in the UNO framework's domain entity package. It covers the different types of services, their responsibilities, and how to use them effectively in your applications.

## Overview

The Service pattern in the UNO framework is implemented in the `uno.domain.entity.service` module and includes the following components:

- **DomainService**: Base class for domain-specific business logic
- **DomainServiceWithUnitOfWork**: Domain service with transactional support
- **ApplicationService**: Service for cross-domain orchestration
- **CrudService**: Standardized service for entity CRUD operations
- **ServiceFactory**: Factory for creating and configuring services

The service pattern separates business logic from data access and presentation concerns, allowing for cleaner, more maintainable code.

## Domain Services

### DomainService

Domain services encapsulate business logic that doesn't naturally fit on entities. They operate on entities and value objects but are not entities themselves.

```python
from uno.domain.entity import DomainService, EntityRepository
from uno.core.errors.result import Result, Success, Failure

class UserService(DomainService[User, UUID]):
    def __init__(
        self,
        repository: EntityRepository[User, UUID],
        logger: logging.Logger | None = None
    ):
        super().__init__(User, repository, logger)
    
    async def authenticate(self, email: str, password: str) -> Result[User, str]:
        # Find user by email using repository
        user = await self.find_by_email(email)
        if user is None:
            return Failure("User not found")
        
        # Verify password
        if not self._verify_password(user, password):
            return Failure("Invalid password")
        
        return Success(user)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        from uno.domain.entity.specification import AttributeSpecification
        
        email_spec = AttributeSpecification("email", email)
        return await self.repository.find_one(email_spec)
    
    def _verify_password(self, user: User, password: str) -> bool:
        # Password verification logic
        # ...
```

### DomainServiceWithUnitOfWork

This service extends DomainService with transaction support using the Unit of Work pattern. It's useful when operations need to span multiple repositories or ensure atomicity.

```python
from uno.domain.entity import DomainServiceWithUnitOfWork
from uno.core.uow import AbstractUnitOfWork

class OrderService(DomainServiceWithUnitOfWork[Order, UUID]):
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        logger: logging.Logger | None = None
    ):
        super().__init__(Order, unit_of_work, logger)
    
    async def create_order(
        self, customer_id: UUID, items: list[dict[str, Any]]
    ) -> Result[Order, str]:
        async with self.with_uow("create_order"):
            await self._ensure_repository()
            
            # Get product repository from unit of work
            product_repo = self.unit_of_work.get_repository(Product)
            
            # Validate products
            products = []
            for item in items:
                product = await product_repo.get(item["product_id"])
                if product is None:
                    return Failure(f"Product with ID {item['product_id']} not found")
                
                if product.inventory_count < item["quantity"]:
                    return Failure(f"Insufficient inventory for {product.name}")
                
                products.append((product, item["quantity"]))
            
            # Create order
            order = Order(
                id=uuid4(),
                customer_id=customer_id,
                status="pending",
                order_date=datetime.now(),
                items=[]
            )
            
            # Add items to order and update inventory
            total_amount = 0
            for product, quantity in products:
                order_item = OrderItem(
                    id=uuid4(),
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.price
                )
                
                order.items.append(order_item)
                total_amount += product.price * quantity
                
                # Update inventory
                product.inventory_count -= quantity
                await product_repo.update(product)
            
            # Set total amount
            order.total_amount = total_amount
            
            # Save order
            created_order = await self.repository.add(order)
            return Success(created_order)
```

## Application Services

### ApplicationService

Application services coordinate operations across multiple domain services. They implement the use cases of the application and orchestrate domain services.

```python
from uno.domain.entity import ApplicationService
from uno.core.errors.result import Result

class OrderingService(ApplicationService[Dict[str, Any], str]):
    def __init__(
        self,
        user_service: UserService,
        product_service: ProductService,
        order_service: OrderService,
        notification_service: NotificationService,
        logger: logging.Logger | None = None
    ):
        super().__init__(logger)
        self.user_service = user_service
        self.product_service = product_service
        self.order_service = order_service
        self.notification_service = notification_service
    
    async def place_order(
        self, customer_id: UUID, items: list[dict[str, Any]]
    ) -> Result[Dict[str, Any], str]:
        self.log_request("place_order", {"customer_id": customer_id, "items": items})
        
        # Validate customer
        customer_result = await self.user_service.get_by_id(customer_id)
        if not customer_result.is_success():
            self.log_response("place_order", customer_result)
            return customer_result
        
        # Place order
        order_result = await self.order_service.create_order(customer_id, items)
        if not order_result.is_success():
            self.log_response("place_order", order_result)
            return order_result
        
        # Send notification
        await self.notification_service.send_order_confirmation(
            customer_result.value, order_result.value
        )
        
        # Create response
        response = {
            "order_id": str(order_result.value.id),
            "status": order_result.value.status,
            "total_amount": order_result.value.total_amount,
            "order_date": order_result.value.order_date.isoformat()
        }
        
        self.log_response("place_order", Success(response))
        return Success(response)
```

### CrudService

CrudService provides a standardized interface for creating, reading, updating, and deleting entities. It delegates operations to a domain service.

```python
from uno.domain.entity import CrudService

class ProductCrudService(CrudService[Product, UUID]):
    def __init__(self, product_service: ProductService):
        super().__init__(product_service)
    
    async def validate(self, product: Product) -> Result[None, str]:
        """Add custom validation logic for products."""
        if product.price <= 0:
            return Failure("Product price must be positive")
        
        if not product.name:
            return Failure("Product name is required")
        
        return Success(None)
```

## Service Factory

The ServiceFactory simplifies the creation of services by handling repository and unit of work creation.

```python
from uno.domain.entity import ServiceFactory

# Create a factory for the User entity
user_factory = ServiceFactory(
    User,
    repository_factory=lambda entity_type: user_repository,
    unit_of_work_factory=lambda: unit_of_work
)

# Create domain service
user_service = user_factory.create_domain_service()

# Create domain service with unit of work
user_service_with_uow = user_factory.create_domain_service_with_uow()

# Create CRUD service
user_crud_service = user_factory.create_crud_service(user_service)
```

## Result Pattern

All service methods return a `Result` object from `uno.core.errors.result`. This provides a consistent way to handle success and failure cases without using exceptions.

```python
from uno.core.errors.result import Result, Success, Failure

def handle_result(result: Result[User, str]) -> None:
    if result.is_success():
        # Access the value
        user = result.value
        print(f"User: {user.name}")
    else:
        # Access the error
        error = result.error
        print(f"Error: {error}")
```

## Best Practices

### Domain Service Design

1. Keep domain services focused on a single entity or a small group of related entities
2. Implement business rules and validations in domain services
3. Use `Result` objects to handle errors explicitly
4. Log important operations and error conditions
5. Use specifications for querying entities
6. Keep domain services free of infrastructure concerns

### Application Service Design

1. Use application services to coordinate multiple domain services
2. Implement use cases and user stories in application services
3. Handle cross-cutting concerns like logging and authorization in application services
4. Return consistent response structures
5. Keep application services thin by delegating business logic to domain services

### Transaction Management

1. Use `DomainServiceWithUnitOfWork` for operations that span multiple repositories
2. Begin transactions explicitly with `async with self.with_uow("operation_name"):`
3. Let Unit of Work handle commits and rollbacks automatically
4. Access repositories through the Unit of Work to ensure they participate in the transaction
5. Avoid mixing transactional and non-transactional operations in the same method

### Error Handling

1. Return `Result` objects from all service methods
2. Use `Success` for successful operations with relevant data
3. Use `Failure` for error conditions with descriptive error messages
4. Log errors at the appropriate level (warning, error, etc.)
5. Handle errors gracefully in application services

## Migration from Legacy Services

If you're migrating from legacy service implementations in UNO, follow these steps:

1. Replace `BaseService` implementations with `DomainService`
2. Replace manual transaction handling with `DomainServiceWithUnitOfWork`
3. Replace `ServiceProtocol` implementations with `ApplicationService`
4. Replace custom CRUD implementations with `CrudService`
5. Add deprecation warnings to legacy service implementations
6. Update service consumers to use the new pattern

## Example: Complete Implementation

Here's a complete example showing domain and application services working together:

```python
# Define domain services
class ProductService(DomainService[Product, UUID]):
    async def get_available_products(self) -> Result[list[Product], str]:
        from uno.domain.entity.specification import AttributeSpecification
        active_spec = AttributeSpecification("is_active", True)
        in_stock_spec = AttributeSpecification("inventory_count", 0, lambda a, b: a > b)
        
        try:
            products = await self.repository.find(active_spec.and_(in_stock_spec))
            return Success(products)
        except Exception as e:
            self.logger.error(f"Error getting available products: {e}", exc_info=True)
            return Failure(f"Error getting available products: {str(e)}")

class OrderService(DomainServiceWithUnitOfWork[Order, UUID]):
    async def place_order(self, user_id: UUID, product_ids: list[UUID]) -> Result[Order, str]:
        async with self.with_uow("place_order"):
            # Implementation details omitted for brevity
            # ...
            
            return Success(order)

# Define application service
class ShoppingService(ApplicationService[Dict[str, Any], str]):
    def __init__(
        self, 
        product_service: ProductService,
        order_service: OrderService
    ):
        super().__init__()
        self.product_service = product_service
        self.order_service = order_service
    
    async def checkout(
        self, user_id: UUID, product_ids: list[UUID]
    ) -> Result[Dict[str, Any], str]:
        self.log_request("checkout", {"user_id": user_id, "product_ids": product_ids})
        
        # Check product availability
        available_result = await self.product_service.get_available_products()
        if not available_result.is_success():
            self.log_response("checkout", available_result)
            return available_result
        
        available_ids = {str(p.id) for p in available_result.value}
        unavailable = [pid for pid in product_ids if str(pid) not in available_ids]
        
        if unavailable:
            result = Failure(f"Products not available: {', '.join(map(str, unavailable))}")
            self.log_response("checkout", result)
            return result
        
        # Place order
        order_result = await self.order_service.place_order(user_id, product_ids)
        if not order_result.is_success():
            self.log_response("checkout", order_result)
            return order_result
        
        # Create response
        response = {
            "order_id": str(order_result.value.id),
            "status": order_result.value.status,
            "total_amount": order_result.value.total_amount,
            "products": [str(pid) for pid in product_ids]
        }
        
        self.log_response("checkout", Success(response))
        return Success(response)
```

## Further Reading

- [Domain-Driven Design](https://domaindrivendesign.org/)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)
- [Result Pattern](https://fsharpforfunandprofit.com/rop/)
- [Unit of Work Pattern](https://martinfowler.com/eaaCatalog/unitOfWork.html)
- [Repository Pattern](docs/domain/repository_pattern.md)
- [Entity Framework](docs/domain/entity_framework.md)