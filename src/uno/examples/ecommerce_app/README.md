# E-Commerce Application Example

This example demonstrates a comprehensive e-commerce application built using the unified Domain-Driven Design approach in the Uno framework. It shows the complete stack from domain entities to API endpoints, with proper separation of concerns and integration between components.

## Domain Structure

The example follows a clean domain-driven design architecture:

- **Domain Layer**: Core business logic and domain entities
- **Application Layer**: Application services and use cases
- **Infrastructure Layer**: Database access and external services
- **API Layer**: FastAPI endpoints for exposing the domain

## Key Features Demonstrated

1. **Domain Model**:
   - Entity and aggregate design
   - Value objects for encapsulation
   - Domain events for communication

2. **Repository Pattern**:
   - Standard repository implementation
   - Unit of work for transactions
   - Specification pattern for queries

3. **Domain Services**:
   - Transactional domain services
   - Read-only query services
   - Entity services for CRUD operations
   - Aggregate services with optimistic concurrency

4. **Events**:
   - Domain event publishing and handling
   - Cross-boundary communication
   - Event-driven workflows

5. **API Integration**:
   - Service endpoint factory
   - Input/output model conversion
   - Error handling and status codes
   - OpenAPI documentation

6. **Advanced Features**:
   - Authorization integration
   - Attribute/value system integration
   - Query optimization
   - Repository caching

## Running the Example

1. Start the Uno database: `docker compose up -d`
2. Run the application: `python -m src.uno.examples.ecommerce_app.main`
3. Open the API documentation: http://localhost:8000/docs

## Example API Endpoints

- Products API: `/api/products`
- Orders API: `/api/orders`
- Customers API: `/api/customers`
- Catalog API: `/api/catalog`
- Cart API: `/api/cart`
- Checkout API: `/api/checkout`

## Code Organization

The application is organized into bounded contexts:

- **Catalog Context**: Products, categories, pricing
- **Order Context**: Orders, order items, statuses
- **Customer Context**: Customers, addresses, preferences
- **Cart Context**: Shopping carts, cart items
- **Shipping Context**: Shipping methods, rates
- **Payment Context**: Payment methods, transactions

Each context follows the same structure:

```
context/
  ├── domain/        # Domain model (entities, value objects, events)
  ├── repository/    # Repositories and specifications
  ├── services/      # Domain services
  └── api/           # API endpoints
```

## Integration with Framework Features

This example also demonstrates integration with other Uno framework features:

- Attribute system for product characteristics
- Values system for product specifications
- Workflows for order processing
- Reports for sales analytics
- Vector search for product recommendations