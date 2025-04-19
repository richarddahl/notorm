# E-Commerce Application Example

This example demonstrates a comprehensive e-commerce application built using the unified Domain-Driven Design approach in the Uno framework. It shows the complete stack from domain entities to API endpoints, with proper separation of concerns and integration between components.

## Implementation Status

- **Catalog Context**: ✅ Fully implemented with domain model, repositories, services, and API
- **Order Context**: 🚧 Placeholder (to be implemented)
- **Customer Context**: 🚧 Placeholder (to be implemented)
- **Cart Context**: 🚧 Placeholder (to be implemented)
- **Shipping Context**: 🚧 Placeholder (to be implemented)
- **Payment Context**: 🚧 Placeholder (to be implemented)

## Domain Structure

The example follows a clean domain-driven design architecture:

- **Domain Layer**: Core business logic and domain entities
- **Repository Layer**: Database access and data persistence
- **Services Layer**: Application services and use cases
- **API Layer**: FastAPI endpoints for exposing the domain

## Key Features Demonstrated

1. **Domain Model**:
   - Entity and aggregate design
   - Value objects for encapsulation
   - Domain events for communication
   - Invariant enforcement

2. **Repository Pattern**:
   - Standard repository implementation
   - SQLAlchemy integration
   - Unit of work for transactions
   - Specification pattern for queries

3. **Domain Services**:
   - Transactional domain services
   - Read-only query services
   - Entity services for CRUD operations
   - Aggregate services with optimistic concurrency

4. **Events**:
   - Domain event publishing and handling
   - Event collection from aggregates
   - Event-driven workflows

5. **API Integration**:
   - Service endpoint factory
   - Domain service adapters
   - Input/output model conversion
   - Error handling and status codes

## Catalog Context

The catalog context demonstrates:

- **Domain Entities**:
  - `Product` aggregate root with variants and images
  - `Category` entity for organizing products
  - `ProductVariant` and `ProductImage` child entities
  - Value objects: `Money`, `Weight`, `Dimensions`, `Inventory`

- **Domain Events**:
  - `ProductCreatedEvent`
  - `ProductUpdatedEvent`
  - `ProductPriceChangedEvent`
  - `ProductInventoryUpdatedEvent`

- **Repositories**:
  - `ProductRepository` with specification support
  - `CategoryRepository` with hierarchy management

- **Services**:
  - `ProductService` for product creation and updates
  - `ProductQueryService` for querying products
  - `CategoryService` for category management

- **API Endpoints**:
  - CRUD operations for products and categories
  - Filtering and search capabilities
  - Pagination support

## Running the Example

1. Start the Uno database: `docker compose up -d`
2. Run the application: `python -m src.uno.examples.ecommerce_app.main`
3. Open the API documentation: http://localhost:8000/docs

## API Endpoints

- **Product Endpoints**:
  - `GET /api/catalog/products` - List products with filtering and pagination
  - `GET /api/catalog/products/{product_id}` - Get product details
  - `POST /api/catalog/products` - Create a new product
  - `PUT /api/catalog/products/{product_id}` - Update a product

- **Category Endpoints**:
  - `GET /api/catalog/categories` - List categories
  - `GET /api/catalog/categories/hierarchy` - Get category hierarchy
  - `GET /api/catalog/categories/{category_id}` - Get category details
  - `POST /api/catalog/categories` - Create a new category
  - `PUT /api/catalog/categories/{category_id}` - Update a category

## Code Organization

The application is organized into bounded contexts:

- **Catalog Context**: Products, categories, variants, images
- **Order Context**: Orders, order items, statuses (to be implemented)
- **Customer Context**: Customers, addresses, preferences (to be implemented)
- **Cart Context**: Shopping carts, cart items (to be implemented)
- **Shipping Context**: Shipping methods, rates (to be implemented)
- **Payment Context**: Payment methods, transactions (to be implemented)

Each context follows the same structure:

```
context/
  ├── domain/        # Domain model (entities, value objects, events)
  ├── repository/    # Repositories and specifications
  ├── services/      # Domain services
  └── api/           # API endpoints
```

## Future Enhancements

- Complete implementation of remaining contexts
- Cross-context integration with domain events
- Authentication and authorization
- Workflow automation for orders
- Search and recommendation features