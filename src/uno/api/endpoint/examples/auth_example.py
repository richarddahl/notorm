"""
Example implementation of authentication and authorization with the unified endpoint framework.

This module demonstrates how to use the authentication and authorization features of the unified endpoint framework.
"""

from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field

from uno.api.endpoint import (
    create_api,
    BaseEndpoint,
    CrudEndpoint,
    CqrsEndpoint,
    CommandHandler,
    QueryHandler,
)
from uno.api.endpoint.auth import (
    JWTAuthBackend,
    SecureCrudEndpoint,
    SecureCqrsEndpoint,
    User,
    UserContext,
    setup_auth,
    get_user_context,
    requires_auth,
)
from uno.core.errors.result import Result, Success
from uno.domain.entity.service import ApplicationService, CrudService


# Models
class ProductSchema(BaseModel):
    """Product schema."""

    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    is_active: bool = Field(..., description="Whether the product is active")


class CreateProductRequest(BaseModel):
    """Create product request."""

    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")


class UpdateProductRequest(BaseModel):
    """Update product request."""

    name: str | None = Field(None, description="Product name")
    price: Optional[float] = Field(None, description="Product price")
    category: str | None = Field(None, description="Product category")


class ProductSearchQuery(BaseModel):
    """Product search query."""

    name: str | None = Field(None, description="Product name contains")
    min_price: Optional[float] = Field(None, description="Minimum price")
    max_price: Optional[float] = Field(None, description="Maximum price")
    category: str | None = Field(None, description="Product category")


class TokenRequest(BaseModel):
    """Token request."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str = Field(..., description="Access token")
    token_type: str = Field(..., description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


# Services
class ProductService(CrudService):
    """Example product service implementing CRUD operations."""

    async def create(self, data):
        # In a real service, this would create a product in the database
        return Success(
            {
                "id": "new-product-id",
                "name": data.name,
                "price": data.price,
                "category": data.category,
                "is_active": True,
            }
        )

    async def get_by_id(self, id):
        # In a real service, this would get a product from the database
        return Success(
            {
                "id": id,
                "name": "Example Product",
                "price": 19.99,
                "category": "Category 1",
                "is_active": True,
            }
        )

    async def update(self, id, data):
        # In a real service, this would update a product in the database
        product = {
            "id": id,
            "name": "Example Product",
            "price": 19.99,
            "category": "Category 1",
            "is_active": True,
        }

        if data.name is not None:
            product["name"] = data.name

        if data.price is not None:
            product["price"] = data.price

        if data.category is not None:
            product["category"] = data.category

        return Success(product)

    async def delete(self, id):
        # In a real service, this would delete a product from the database
        return Success(True)

    async def get_all(self):
        # In a real service, this would get all products from the database
        return Success(
            [
                {
                    "id": "1",
                    "name": "Product 1",
                    "price": 19.99,
                    "category": "Category 1",
                    "is_active": True,
                },
                {
                    "id": "2",
                    "name": "Product 2",
                    "price": 29.99,
                    "category": "Category 2",
                    "is_active": True,
                },
            ]
        )


class SearchProductsService(ApplicationService):
    """Example search products service implementing a query operation."""

    async def execute(self, query: ProductSearchQuery) -> Result[list[ProductSchema]]:
        """Execute the search products query."""
        # In a real service, this would search products in the database
        products = [
            ProductSchema(
                id="1",
                name="Product 1",
                price=19.99,
                category="Category 1",
                is_active=True,
            ),
            ProductSchema(
                id="2",
                name="Product 2",
                price=29.99,
                category="Category 2",
                is_active=True,
            ),
        ]

        # Filter products based on query parameters
        filtered_products = []
        for product in products:
            if (
                (query.name is None or query.name.lower() in product.name.lower())
                and (query.min_price is None or product.price >= query.min_price)
                and (query.max_price is None or product.price <= query.max_price)
                and (query.category is None or product.category == query.category)
            ):
                filtered_products.append(product)

        return Success(filtered_products)


def create_auth_app():
    """
    Create a FastAPI application with authentication and authorization.

    Returns:
        A FastAPI application with authentication and authorization
    """
    # Create the API
    app = create_api(
        title="Secure Product API",
        description="API for managing products with authentication and authorization",
    )

    # Create JWT auth backend
    auth_backend = JWTAuthBackend(
        secret_key="your-secret-key-here",  # In production, use a secure secret key
        algorithm="HS256",
        token_url="/api/token",
    )

    # Set up authentication
    setup_auth(
        app=app,
        auth_backend=auth_backend,
        exclude_paths=["/api/token", "/docs", "/openapi.json"],
    )

    # Create services
    product_service = ProductService()
    search_service = SearchProductsService()

    # Create secure CRUD endpoint
    crud_endpoint = SecureCrudEndpoint(
        service=product_service,
        create_model=CreateProductRequest,
        response_model=ProductSchema,
        update_model=UpdateProductRequest,
        tags=["Products"],
        path="/api/products",
        auth_backend=auth_backend,
        create_permissions=["products:create"],
        read_permissions=["products:read"],
        update_permissions=["products:update"],
        delete_permissions=["products:delete"],
    )
    crud_endpoint.register(app)

    # Create secure CQRS endpoint
    search_query = QueryHandler(
        service=search_service,
        response_model=list[ProductSchema],
        query_model=ProductSearchQuery,
        path="/search",
        method="get",
    )

    cqrs_endpoint = SecureCqrsEndpoint(
        queries=[search_query],
        tags=["Products"],
        base_path="/api/products",
        auth_backend=auth_backend,
        query_permissions={
            "search": ["products:read"],
        },
    )
    cqrs_endpoint.register(app)

    # Add token endpoint
    @app.post("/api/token", response_model=TokenResponse)
    async def login(request: TokenRequest):
        """
        Get an access token.

        In a real application, this would validate the username and password
        against a database or external authentication service.
        """
        # For this example, accept any username/password where they match
        if request.username != request.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid username or password",
                    }
                },
            )

        # Create a user with appropriate roles and permissions
        user = User(
            id="user-id",
            username=request.username,
            email=f"{request.username}@example.com",
            roles=["user"],
            permissions=[
                "products:read",
                # Conditionally add other permissions based on username
                *(
                    ["products:create", "products:update", "products:delete"]
                    if request.username == "admin"
                    else []
                ),
            ],
        )

        # Create a token
        token = auth_backend.create_token(user, expires_in=3600)

        # Return the token response
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 3600,
        }

    # Add a user info endpoint
    @app.get("/api/me")
    async def get_current_user(user_context: UserContext = Depends(get_user_context)):
        """Get information about the current user."""
        return {
            "id": user_context.user.id,
            "username": user_context.user.username,
            "email": user_context.user.email,
            "roles": user_context.user.roles,
            "permissions": user_context.user.permissions,
        }

    # Add an endpoint that requires specific roles
    @app.get("/api/admin", dependencies=[Depends(requires_auth(roles=["admin"]))])
    async def admin_only():
        """Admin-only endpoint."""
        return {"message": "You have admin access!"}

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_auth_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
