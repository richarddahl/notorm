"""
Example implementation of filtering with the unified endpoint framework.

This module demonstrates how to use the filtering capabilities of the unified endpoint framework,
including support for the Apache AGE knowledge graph.
"""

from typing import List, Optional

from fastapi import FastAPI, Query, Request
from pydantic import BaseModel, Field

from uno.api.endpoint import (
    create_api,
    CrudEndpoint,
    CqrsEndpoint,
    QueryHandler,
    CommandHandler,
)
from uno.api.endpoint.filter import (
    FilterBackend,
    FilterCriteria,
    FilterOperator,
    FilterRequest,
    FilterableEndpoint,
    FilterableCrudEndpoint,
    FilterableCqrsEndpoint,
    GraphFilterBackend,
    SqlFilterBackend,
    get_filter_criteria,
)
from uno.core.errors.result import Result, Success
from uno.domain.entity.service import ApplicationService, CrudService


# Models
class Product(BaseModel):
    """Product model."""

    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    tags: list[str] = Field(default_factory=list, description="Product tags")
    is_active: bool = Field(True, description="Whether the product is active")


class CreateProductRequest(BaseModel):
    """Create product request."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    tags: list[str] = Field(default_factory=list, description="Product tags")
    is_active: bool = Field(True, description="Whether the product is active")


class UpdateProductRequest(BaseModel):
    """Update product request."""

    name: str | None = Field(None, description="Product name")
    description: str | None = Field(None, description="Product description")
    price: Optional[float] = Field(None, description="Product price")
    category: str | None = Field(None, description="Product category")
    tags: list[str] | None = Field(None, description="Product tags")
    is_active: Optional[bool] = Field(None, description="Whether the product is active")


# Sample data for the example
PRODUCTS = [
    Product(
        id="1",
        name="Laptop",
        description="High-performance laptop",
        price=1299.99,
        category="Electronics",
        tags=["tech", "computer", "portable"],
        is_active=True,
    ),
    Product(
        id="2",
        name="Smartphone",
        description="Latest smartphone model",
        price=899.99,
        category="Electronics",
        tags=["tech", "mobile", "phone"],
        is_active=True,
    ),
    Product(
        id="3",
        name="Headphones",
        description="Noise-cancelling headphones",
        price=249.99,
        category="Electronics",
        tags=["audio", "tech", "accessories"],
        is_active=True,
    ),
    Product(
        id="4",
        name="Coffee Maker",
        description="Automatic coffee maker",
        price=89.99,
        category="Home",
        tags=["kitchen", "appliance", "coffee"],
        is_active=True,
    ),
    Product(
        id="5",
        name="Desk Chair",
        description="Ergonomic desk chair",
        price=199.99,
        category="Furniture",
        tags=["office", "chair", "ergonomic"],
        is_active=True,
    ),
]


# Mock repository for the example
class ProductRepository:
    """Repository for products."""

    async def get_by_ids(self, ids: list[str]) -> list[Product]:
        """
        Get products by IDs.

        Args:
            ids: Product IDs

        Returns:
            List of products with matching IDs
        """
        return [p for p in PRODUCTS if p.id in ids]


# Mock filter backend for the example
class MockFilterBackend(FilterBackend):
    """
    Mock filter backend for the example.

    This backend filters products in memory to simulate database filtering.
    """

    async def filter_entities(
        self,
        entity_type: str,
        filter_criteria: list[dict],
        *,
        sort_by: list[str] | None = None,
        sort_dir: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include_count: bool = True,
    ) -> tuple[list[str], Optional[int]]:
        """
        Filter entities based on criteria.

        Args:
            entity_type: The type of entity to filter
            filter_criteria: Filter criteria
            sort_by: Optional fields to sort by
            sort_dir: Optional sort directions
            limit: Optional maximum number of results
            offset: Optional offset for pagination
            include_count: Whether to include the total count

        Returns:
            Tuple of (list of entity IDs, total count if include_count is True)
        """
        # Filter products
        filtered_products = PRODUCTS

        for criteria in filter_criteria:
            field = criteria.field
            operator = criteria.operator
            value = criteria.value

            filtered_products = [
                p
                for p in filtered_products
                if self._matches_criteria(p, field, operator, value)
            ]

        # Get total count if requested
        total = len(filtered_products) if include_count else None

        # Sort products
        if sort_by and sort_dir:
            # Apply each sort
            for i, field in enumerate(sort_by):
                direction = sort_dir[i] if i < len(sort_dir) else "asc"
                reverse = direction == "desc"
                filtered_products.sort(
                    key=lambda p: getattr(p, field) if hasattr(p, field) else None,
                    reverse=reverse,
                )

        # Apply pagination
        if offset is not None:
            filtered_products = filtered_products[offset:]

        if limit is not None:
            filtered_products = filtered_products[:limit]

        # Return product IDs
        return [p.id for p in filtered_products], total

    async def count_entities(
        self,
        entity_type: str,
        filter_criteria: list[dict],
    ) -> int:
        """
        Count entities based on criteria.

        Args:
            entity_type: The type of entity to count
            filter_criteria: Filter criteria

        Returns:
            Total count of matching entities
        """
        # Filter products
        filtered_products = PRODUCTS

        for criteria in filter_criteria:
            field = criteria.field
            operator = criteria.operator
            value = criteria.value

            filtered_products = [
                p
                for p in filtered_products
                if self._matches_criteria(p, field, operator, value)
            ]

        # Return count
        return len(filtered_products)

    def _matches_criteria(
        self, product: Product, field: str, operator: str, value: Any
    ) -> bool:
        """
        Check if a product matches the given criteria.

        Args:
            product: Product to check
            field: Field to check
            operator: Operator to use
            value: Value to check against

        Returns:
            True if the product matches the criteria, False otherwise
        """
        # Get field value
        if not hasattr(product, field):
            return False

        field_value = getattr(product, field)

        # Handle different operators
        if operator == FilterOperator.EQUAL or operator == "eq":
            return field_value == value
        elif operator == FilterOperator.NOT_EQUAL or operator == "ne":
            return field_value != value
        elif operator == FilterOperator.GREATER_THAN or operator == "gt":
            return field_value > value
        elif operator == FilterOperator.GREATER_THAN_OR_EQUAL or operator == "gte":
            return field_value >= value
        elif operator == FilterOperator.LESS_THAN or operator == "lt":
            return field_value < value
        elif operator == FilterOperator.LESS_THAN_OR_EQUAL or operator == "lte":
            return field_value <= value
        elif operator == FilterOperator.IN or operator == "in":
            return field_value in value
        elif operator == FilterOperator.NOT_IN or operator == "not_in":
            return field_value not in value
        elif operator == FilterOperator.CONTAINS or operator == "contains":
            return value in field_value
        elif operator == FilterOperator.STARTS_WITH or operator == "starts_with":
            return field_value.startswith(value)
        elif operator == FilterOperator.ENDS_WITH or operator == "ends_with":
            return field_value.endswith(value)
        elif operator == FilterOperator.IS_NULL or operator == "is_null":
            return field_value is None
        elif operator == FilterOperator.IS_NOT_NULL or operator == "is_not_null":
            return field_value is not None

        return False


# Mock service for the CRUD endpoint
class ProductService(CrudService):
    """Service for managing products."""

    async def create(self, data):
        """Create a product."""
        product = Product(
            id=str(len(PRODUCTS) + 1),
            **data.dict(),
        )
        PRODUCTS.append(product)
        return Success(product)

    async def get_by_id(self, id):
        """Get a product by ID."""
        for product in PRODUCTS:
            if product.id == id:
                return Success(product)
        return Success(None)

    async def get_all(self):
        """Get all products."""
        return Success(PRODUCTS)

    async def update(self, id, data):
        """Update a product."""
        for i, product in enumerate(PRODUCTS):
            if product.id == id:
                # Update product data
                update_data = {k: v for k, v in data.dict().items() if v is not None}
                updated_product = product.copy(update=update_data)
                PRODUCTS[i] = updated_product
                return Success(updated_product)
        return Success(None)

    async def delete(self, id):
        """Delete a product."""
        for i, product in enumerate(PRODUCTS):
            if product.id == id:
                PRODUCTS.pop(i)
                return Success(True)
        return Success(False)

    async def get_by_ids(self, ids):
        """Get products by IDs."""
        return [p for p in PRODUCTS if p.id in ids]


def create_filter_app():
    """
    Create a FastAPI application with filtering capabilities.

    Returns:
        A FastAPI application with filtering capabilities
    """
    # Create the API
    app = create_api(
        title="Product Filter API",
        description="API for filtering products, demonstrating the unified endpoint framework's filtering capabilities",
    )

    # Create filter backend
    filter_backend = MockFilterBackend()

    # Set up repositories
    product_repository = ProductRepository()

    # Example 1: FilterableEndpoint
    # Create a filterable endpoint that uses a custom service and repository
    filterable_endpoint = FilterableEndpoint(
        filter_backend=filter_backend,
        entity_type="Product",
        repository=product_repository,
        router=FastAPI().router,
        tags=["Products - Filterable"],
    )

    # Register a filter route
    filterable_endpoint.register_filter_route(
        path="/api/products/filterable/filter",
        response_model=Product,
    )

    # Register the endpoint
    filterable_endpoint.register(app)

    # Example 2: FilterableCrudEndpoint
    # Create a filterable CRUD endpoint
    filterable_crud_endpoint = FilterableCrudEndpoint(
        service=ProductService(),
        create_model=CreateProductRequest,
        response_model=Product,
        update_model=UpdateProductRequest,
        filter_backend=filter_backend,
        entity_type="Product",
        tags=["Products - CRUD"],
        path="/api/products/crud",
    )

    # Register the endpoint
    filterable_crud_endpoint.register(app)

    # Example 3: FilterableCqrsEndpoint
    # Create services for CQRS
    class GetProductService(ApplicationService):
        """Service for getting a product."""

        async def execute(self, id: str) -> Result[Product]:
            """Get a product by ID."""
            for product in PRODUCTS:
                if product.id == id:
                    return Success(product)
            return Success(None)

    # Create query and command handlers
    get_product_query = QueryHandler(
        service=GetProductService(),
        response_model=Product,
        path="/{id}",
        method="get",
    )

    # Create a filterable CQRS endpoint
    filterable_cqrs_endpoint = FilterableCqrsEndpoint(
        queries=[get_product_query],
        commands=[],
        filter_backend=filter_backend,
        entity_type="Product",
        repository=product_repository,
        tags=["Products - CQRS"],
        base_path="/api/products/cqrs",
    )

    # Register the endpoint
    filterable_cqrs_endpoint.register(app)

    # Example 4: Add routes that use filter parameters directly
    @app.get("/api/products/filter", response_model=list[Product])
    async def filter_products(
        request: Request,
        filter_criteria: FilterCriteria = Depends(get_filter_criteria),
    ):
        """Filter products based on query parameters."""
        # Set the filter backend in the request state
        request.state.filter_backend = filter_backend

        # Get entities using the filter backend
        entities, _ = await filter_backend.get_entities(
            entity_type="Product",
            filter_criteria=filter_criteria,
            repository=product_repository,
        )

        return entities

    return app


# Example of an Apache AGE integration
def create_age_filter_app():
    """
    Create a FastAPI application with Apache AGE filtering capabilities.

    This is just a conceptual example, as it would require a real database connection.

    Returns:
        A FastAPI application with Apache AGE filtering capabilities
    """
    # Create the API
    app = create_api(
        title="Product AGE Filter API",
        description="API for filtering products using Apache AGE knowledge graph",
    )

    # This would be a real session factory that provides a database connection
    # For this example, we just use a mock
    class MockSessionFactory:
        async def __call__(self):
            class MockSession:
                async def __aenter__(self):
                    return self

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass

                async def execute(self, query, params=None):
                    class MockResult:
                        def fetchall(self):
                            return [("1",), ("2",)]

                        def scalar(self):
                            return 2

                    return MockResult()

            return MockSession()

    # Create filter backends
    session_factory = MockSessionFactory()

    # Create a SQL filter backend as fallback
    sql_backend = SqlFilterBackend(session_factory)

    # Create a graph filter backend that uses Apache AGE
    graph_backend = GraphFilterBackend(session_factory, fallback_backend=sql_backend)

    # Create the repository
    product_repository = ProductRepository()

    # Create a filterable CRUD endpoint that uses the graph backend
    filterable_crud_endpoint = FilterableCrudEndpoint(
        service=ProductService(),
        create_model=CreateProductRequest,
        response_model=Product,
        update_model=UpdateProductRequest,
        filter_backend=graph_backend,
        entity_type="Product",
        tags=["Products - Graph"],
        path="/api/products/graph",
    )

    # Register the endpoint
    filterable_crud_endpoint.register(app)

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_filter_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
