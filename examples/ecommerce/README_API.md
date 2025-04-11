# E-commerce API Layer

This document provides an overview of the API layer for the e-commerce application.

## Overview

The API layer is implemented using FastAPI and follows RESTful principles. It provides endpoints for:

- User management
- Product catalog
- Order processing

The API is designed to work with the domain layer, which implements the business logic using domain-driven design.

## API Structure

The API is organized around the following components:

- **DTOs**: Data transfer objects that define the request and response formats
- **Mappers**: Functions for converting between domain entities and DTOs
- **Dependencies**: FastAPI dependencies for accessing services and getting the current user
- **Routers**: FastAPI routers that define the endpoints and handle requests

## Authentication

The API assumes that authentication is handled by an external service that provides a JWT with the user's email in the `sub` claim. The JWT is extracted from the `Authorization` header and used to identify the current user.

## Endpoints

### User Endpoints

- `GET /users/me`: Get the current user's profile
- `PATCH /users/me`: Update the current user's profile
- `POST /users`: Create a new user profile

### Product Endpoints

- `POST /products`: Create a new product (admin only)
- `GET /products`: Search for products
- `GET /products/{product_id}`: Get a product by ID
- `PATCH /products/{product_id}`: Update a product (admin only)
- `POST /products/{product_id}/inventory`: Update product inventory (admin only)
- `POST /products/{product_id}/ratings`: Add a rating to a product

### Order Endpoints

- `POST /orders`: Create a new order
- `GET /orders`: Get the current user's orders
- `GET /orders/{order_id}`: Get an order by ID
- `POST /orders/{order_id}/payment`: Process payment for an order
- `PATCH /orders/{order_id}/status`: Update an order's status (admin only)
- `POST /orders/{order_id}/cancel`: Cancel an order

## Running the API

To run the API, you can use the following command:

```bash
uvicorn examples.ecommerce.api.app:app --reload
```

This will start the FastAPI application with hot reloading enabled.

The application uses FastAPI's recommended lifespan context manager pattern for startup and shutdown events, which properly initializes services when the application starts and performs cleanup when it shuts down.

## API Documentation

FastAPI automatically generates OpenAPI documentation for the API. You can access it at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Error Handling

The API uses a consistent error response format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

Common error codes include:

- `NOT_FOUND`: The requested resource was not found
- `BAD_REQUEST`: The request contains invalid data
- `FORBIDDEN`: The user does not have permission to perform the action
- `INTERNAL_ERROR`: An internal server error occurred

## Integration with Domain Layer

The API layer integrates with the domain layer through service classes:

- `UserService`: For user management
- `ProductService`: For product management
- `OrderService`: For order management

These services are accessed through FastAPI dependencies that get them from the domain registry.

## API Design Principles

The API follows these design principles:

1. **Separation of concerns**: The API layer is separate from the domain layer
2. **Data validation**: All input is validated using Pydantic models
3. **Proper error handling**: All errors are properly handled and returned in a consistent format
4. **Authorization**: Access to resources is properly restricted based on user roles
5. **Documentation**: All endpoints are fully documented