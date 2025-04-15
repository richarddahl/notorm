"""
Integration tests for complex API scenarios.

This module provides comprehensive tests for complex API scenarios, including
pagination, field selection, filtering, sorting, and error handling.
"""

import pytest
import json
import re
import uuid
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Union, Type, Callable
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi import FastAPI, Depends, HTTPException, Query, Path, status
from fastapi.testclient import TestClient
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, field_validator, ConfigDict

from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchemaConfig
from uno.core.errors import ValidationContext, UnoError, ErrorCode
from uno.core.errors.validation import ValidationError
from uno.api.endpoint import UnoEndpoint, UnoRouter, CreateEndpoint, ViewEndpoint, ListEndpoint, UpdateEndpoint, DeleteEndpoint
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.database.db import FilterParam


# ===== TEST MODELS =====

class ProductModel(UnoModel):
    """Database model for products."""
    
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    sku: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, unique=True)
    category: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    inventory_count: Mapped[int] = mapped_column(nullable=False, default=0)
    weight: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=True)
    dimensions: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)
    tags: Mapped[str] = mapped_column(nullable=True)  # Comma-separated tags
    is_featured: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    

class OrderItemModel(UnoModel):
    """Database model for order items."""
    
    __tablename__ = "order_items"
    
    order_id: Mapped[str] = mapped_column(nullable=False)
    product_id: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)


class OrderModel(UnoModel):
    """Database model for orders."""
    
    __tablename__ = "orders"
    
    customer_id: Mapped[str] = mapped_column(nullable=False)
    order_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    total_amount: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    status: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


# ===== BUSINESS OBJECTS =====

class Product(UnoObj[ProductModel]):
    """Product business object with domain-specific validation."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "name", "price", "category", "inventory_count", "is_active"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for products."""
        # Call parent validation first
        context = super().validate(schema_name)
        
        # Price validation
        if hasattr(self, "price") and self.price is not None:
            if self.price <= Decimal("0.00"):
                context.add_error(
                    field="price",
                    message="Price must be greater than zero",
                    error_code="INVALID_PRICE"
                )
        
        # SKU validation - must follow pattern ABC-12345
        if hasattr(self, "sku") and self.sku:
            sku_pattern = r"^[A-Z]{3}-\d{5}$"
            if not re.match(sku_pattern, self.sku):
                context.add_error(
                    field="sku",
                    message="SKU must follow pattern ABC-12345 (3 uppercase letters, dash, 5 digits)",
                    error_code="INVALID_SKU_FORMAT"
                )
        
        # Category validation
        if hasattr(self, "category") and self.category:
            valid_categories = ["Electronics", "Clothing", "Books", "Home", "Toys", "Food", "Sports"]
            if self.category not in valid_categories:
                context.add_error(
                    field="category",
                    message=f"Invalid category. Must be one of {', '.join(valid_categories)}",
                    error_code="INVALID_CATEGORY"
                )
        
        return context


class OrderItem(UnoObj[OrderItemModel]):
    """Order item business object."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "order_id", "product_id", "quantity", "unit_price"
        })
    }


class Order(UnoObj[OrderModel]):
    """Order business object."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "customer_id", "order_date", "total_amount", "status"
        })
    }


# ===== CUSTOM ENDPOINT TYPES =====

class CustomResponseModel(BaseModel):
    """Custom response model for composite API responses."""
    
    data: Dict[str, Any]
    meta: Dict[str, Any]
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class StatsRouter(UnoRouter):
    """Router for retrieving statistics about a resource."""
    
    path_suffix: str = "/stats"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"Get statistics for {self.model.display_name_plural}"
    
    @property
    def description(self) -> str:
        return f"""
            Get statistics for {self.model.display_name_plural}, such as counts, averages, and other metrics.
            
            Supports the following query parameters:
            - `group_by`: Field to group statistics by (e.g., 'category', 'status')
            - `time_range`: Time range for time-based statistics (e.g., 'day', 'week', 'month', 'year')
        """
    
    def endpoint_factory(self):
        from typing import Optional
        from fastapi import Query as QueryParam
        
        async def endpoint(
            self,
            group_by: Optional[str] = QueryParam(None, description="Field to group statistics by"),
            time_range: Optional[str] = QueryParam(None, description="Time range for time-based statistics")
        ) -> Dict[str, Any]:
            # Get basic counts
            total_count = await self.model.count()
            
            # Get additional statistics based on the model
            stats = {
                "total_count": total_count,
                "group_by": group_by,
                "time_range": time_range,
                "metrics": {},
            }
            
            # If it's a product model, add product-specific stats
            if hasattr(self.model, "inventory_count") and hasattr(self.model, "price"):
                # Get products
                products = await self.model.filter()
                
                # Calculate metrics
                if products:
                    total_value = sum(p.price * p.inventory_count for p in products)
                    avg_price = sum(p.price for p in products) / len(products)
                    out_of_stock = sum(1 for p in products if p.inventory_count == 0)
                    
                    stats["metrics"] = {
                        "total_inventory_value": total_value,
                        "average_price": avg_price,
                        "out_of_stock_count": out_of_stock,
                        "out_of_stock_percentage": (out_of_stock / len(products)) * 100
                    }
                    
                    # Add group by statistics if requested
                    if group_by == "category":
                        categories = {}
                        for p in products:
                            if p.category not in categories:
                                categories[p.category] = {"count": 0, "total_value": 0}
                            
                            categories[p.category]["count"] += 1
                            categories[p.category]["total_value"] += p.price * p.inventory_count
                        
                        stats["by_category"] = categories
            
            # If it's an order model, add order-specific stats
            elif hasattr(self.model, "total_amount") and hasattr(self.model, "status"):
                # Get orders
                orders = await self.model.filter()
                
                # Calculate metrics
                if orders:
                    total_revenue = sum(o.total_amount for o in orders)
                    avg_order_value = total_revenue / len(orders)
                    
                    stats["metrics"] = {
                        "total_revenue": total_revenue,
                        "average_order_value": avg_order_value,
                        "order_count": len(orders)
                    }
                    
                    # Add group by statistics if requested
                    if group_by == "status":
                        status_counts = {}
                        for o in orders:
                            if o.status not in status_counts:
                                status_counts[o.status] = {"count": 0, "total_value": 0}
                            
                            status_counts[o.status]["count"] += 1
                            status_counts[o.status]["total_value"] += o.total_amount
                        
                        stats["by_status"] = status_counts
                    
                    # Add time-based statistics if requested
                    if time_range:
                        now = datetime.now()
                        if time_range == "day":
                            start_date = now - timedelta(days=1)
                        elif time_range == "week":
                            start_date = now - timedelta(weeks=1)
                        elif time_range == "month":
                            start_date = now - timedelta(days=30)
                        elif time_range == "year":
                            start_date = now - timedelta(days=365)
                        else:
                            start_date = now - timedelta(days=30)  # Default to month
                        
                        recent_orders = [o for o in orders if o.order_date >= start_date]
                        stats["time_range_stats"] = {
                            "period": time_range,
                            "order_count": len(recent_orders),
                            "total_revenue": sum(o.total_amount for o in recent_orders),
                            "period_start": start_date.isoformat(),
                            "period_end": now.isoformat()
                        }
            
            return stats
        
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


class BatchRouter(UnoRouter):
    """Router for batch operations on resources."""
    
    path_suffix: str = "/batch"
    method: str = "POST"
    path_prefix: str = "/api"
    tags: List[str] = None
    
    @property
    def summary(self) -> str:
        return f"Perform batch operations on {self.model.display_name_plural}"
    
    @property
    def description(self) -> str:
        return f"""
            Perform batch operations on multiple {self.model.display_name_plural} at once.
            
            Operations supported:
            - `create`: Create multiple resources
            - `update`: Update multiple resources
            - `delete`: Delete multiple resources
            
            Request format:
            ```json
            {{
                "operation": "create|update|delete",
                "items": [
                    {{ ... item 1 data ... }},
                    {{ ... item 2 data ... }}
                ],
                "options": {{ ... optional operation-specific options ... }}
            }}
            ```
        """
    
    def endpoint_factory(self):
        from typing import List, Dict, Any, Optional
        from pydantic import BaseModel, Field
        
        class BatchOperationRequest(BaseModel):
            operation: str = Field(..., description="Operation to perform (create, update, delete)")
            items: List[Dict[str, Any]] = Field(..., description="Items to process")
            options: Optional[Dict[str, Any]] = Field(default={}, description="Operation-specific options")
        
        class BatchOperationResponse(BaseModel):
            success_count: int = Field(..., description="Number of successfully processed items")
            error_count: int = Field(..., description="Number of failed items")
            results: List[Dict[str, Any]] = Field(..., description="Results for each item")
            
        async def endpoint(self, request: BatchOperationRequest) -> BatchOperationResponse:
            operation = request.operation.lower()
            items = request.items
            options = request.options
            
            # Validate the operation
            if operation not in ["create", "update", "delete"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid operation: {operation}. Must be one of: create, update, delete"
                )
            
            # Initialize results
            results = []
            success_count = 0
            error_count = 0
            
            # Process each item
            for index, item in enumerate(items):
                try:
                    if operation == "create":
                        # Create a new resource
                        obj = self.model(**item)
                        await obj.save()
                        results.append({
                            "success": True,
                            "index": index,
                            "id": obj.id,
                            "data": obj.dict()
                        })
                        success_count += 1
                    
                    elif operation == "update":
                        # Update an existing resource
                        if "id" not in item:
                            raise ValueError("Missing 'id' field for update operation")
                        
                        obj = await self.model.get(item["id"])
                        if not obj:
                            raise ValueError(f"Resource with id '{item['id']}' not found")
                        
                        # Update fields
                        for key, value in item.items():
                            if key != "id":
                                setattr(obj, key, value)
                        
                        await obj.save()
                        results.append({
                            "success": True,
                            "index": index,
                            "id": obj.id,
                            "data": obj.dict()
                        })
                        success_count += 1
                    
                    elif operation == "delete":
                        # Delete an existing resource
                        if "id" not in item:
                            raise ValueError("Missing 'id' field for delete operation")
                        
                        obj = await self.model.get(item["id"])
                        if not obj:
                            raise ValueError(f"Resource with id '{item['id']}' not found")
                        
                        await obj.delete()
                        results.append({
                            "success": True,
                            "index": index,
                            "id": item["id"]
                        })
                        success_count += 1
                
                except Exception as e:
                    # Handle errors for individual items
                    results.append({
                        "success": False,
                        "index": index,
                        "error": str(e)
                    })
                    error_count += 1
            
            # Return the response with counts and results
            return BatchOperationResponse(
                success_count=success_count,
                error_count=error_count,
                results=results
            )
        
        endpoint.__annotations__["return"] = BatchOperationResponse
        setattr(self.__class__, "endpoint", endpoint)


class StatsEndpoint(UnoEndpoint):
    """Endpoint for retrieving statistics about a resource."""
    
    router: UnoRouter = StatsRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class BatchEndpoint(UnoEndpoint):
    """Endpoint for batch operations on resources."""
    
    router: UnoRouter = BatchRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


# ===== CUSTOM MIDDLEWARE =====

class SimpleAuthMiddleware:
    """Simple authentication middleware for testing purposes."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Get the request headers
        headers = dict(scope.get("headers", {}))
        auth_header = headers.get(b"authorization", b"").decode("utf-8")
        
        # Check if authorization header exists and has the correct format
        if not auth_header.startswith("Bearer "):
            # Unauthorized response
            response = {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    [b"content-type", b"application/json"]
                ]
            }
            await send(response)
            
            # Response body
            body = json.dumps({"detail": "Not authenticated"}).encode("utf-8")
            await send({
                "type": "http.response.body",
                "body": body,
                "more_body": False
            })
            return
        
        # Extract token
        token = auth_header.split(" ")[1]
        
        # For this example, just check if the token is "test_token"
        if token != "test_token":
            # Unauthorized response
            response = {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    [b"content-type", b"application/json"]
                ]
            }
            await send(response)
            
            # Response body
            body = json.dumps({"detail": "Invalid token"}).encode("utf-8")
            await send({
                "type": "http.response.body",
                "body": body,
                "more_body": False
            })
            return
        
        # Continue with the request
        await self.app(scope, receive, send)


class RequestLoggerMiddleware:
    """Middleware for logging all requests."""
    
    def __init__(self, app):
        self.app = app
        self.log = []
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Get request information
        method = scope.get("method", "")
        path = scope.get("path", "")
        query_string = scope.get("query_string", b"").decode("utf-8")
        headers = dict(scope.get("headers", {}))
        
        # Log the request
        request_info = {
            "method": method,
            "path": path,
            "query_string": query_string,
            "headers": {k.decode("utf-8"): v.decode("utf-8") for k, v in headers.items()},
            "timestamp": datetime.now().isoformat()
        }
        
        self.log.append(request_info)
        
        # Continue with the request
        await self.app(scope, receive, send)
    
    def get_logs(self):
        """Get the request logs."""
        return self.log
    
    def clear_logs(self):
        """Clear the request logs."""
        self.log = []


# ===== SUPPORT FUNCTIONS =====

def create_test_app():
    """Create a test FastAPI application with all the required components."""
    # Create the app
    app = FastAPI(title="Test API", description="API for testing complex scenarios")
    
    # Create the endpoint factory
    factory = UnoEndpointFactory()
    
    # Register custom endpoint types
    factory.register_endpoint_type("Stats", StatsEndpoint)
    factory.register_endpoint_type("Batch", BatchEndpoint)
    
    # Create the endpoints for each model
    product_endpoints = factory.create_endpoints(
        app=app,
        model_obj=Product,
        endpoints=["Create", "View", "List", "Update", "Delete", "Stats", "Batch"],
        endpoint_tags=["Products"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    order_endpoints = factory.create_endpoints(
        app=app,
        model_obj=Order,
        endpoints=["Create", "View", "List", "Update", "Delete", "Stats"],
        endpoint_tags=["Orders"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    order_item_endpoints = factory.create_endpoints(
        app=app,
        model_obj=OrderItem,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        endpoint_tags=["Order Items"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    # Add custom route with authentication
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    
    @app.get("/api/v1/me", tags=["Auth"])
    async def get_current_user(token: str = Depends(oauth2_scheme)):
        if token != "test_token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"id": "user-1", "username": "testuser", "email": "test@example.com"}
    
    # Add route that supports HATEOAS links
    @app.get("/api/v1/products/{product_id}/details", tags=["Products"])
    async def get_product_details(product_id: str):
        product = await Product.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Convert to dict with HATEOAS links
        data = product.dict()
        
        # Add HATEOAS links
        data["_links"] = {
            "self": {"href": f"/api/v1/products/{product_id}"},
            "update": {"href": f"/api/v1/products/{product_id}", "method": "PATCH"},
            "delete": {"href": f"/api/v1/products/{product_id}", "method": "DELETE"},
            "stats": {"href": f"/api/v1/products/stats", "method": "GET"},
            "orders": {"href": f"/api/v1/products/{product_id}/orders", "method": "GET"}
        }
        
        return data
    
    # Add a route for product search with advanced filtering
    @app.get("/api/v1/products/search", tags=["Products"])
    async def search_products(
        q: Optional[str] = Query(None, description="Search query for product name or description"),
        min_price: Optional[float] = Query(None, description="Minimum price filter"),
        max_price: Optional[float] = Query(None, description="Maximum price filter"),
        categories: Optional[str] = Query(None, description="Comma-separated list of categories"),
        tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
        in_stock: Optional[bool] = Query(None, description="Filter for products in stock"),
        sort_by: Optional[str] = Query("name", description="Field to sort by"),
        sort_direction: Optional[str] = Query("asc", description="Sort direction (asc or desc)"),
        page: int = Query(1, description="Page number", ge=1),
        page_size: int = Query(10, description="Items per page", ge=1, le=100)
    ):
        # Create filter conditions
        filters = {}
        
        if q:
            # Search in name and description
            products_by_name = await Product.filter({"name__contains": q})
            products_by_desc = await Product.filter({"description__contains": q})
            # Combine results
            results = products_by_name + products_by_desc
            # Remove duplicates
            product_ids = set()
            unique_products = []
            for product in results:
                if product.id not in product_ids:
                    product_ids.add(product.id)
                    unique_products.append(product)
            products = unique_products
        else:
            # Get all products
            products = await Product.filter({})
        
        # Apply filters
        if min_price is not None:
            products = [p for p in products if p.price >= Decimal(str(min_price))]
        
        if max_price is not None:
            products = [p for p in products if p.price <= Decimal(str(max_price))]
        
        if categories:
            category_list = categories.split(",")
            products = [p for p in products if p.category in category_list]
        
        if tags:
            tag_list = tags.split(",")
            products = [p for p in products if p.tags and any(tag in p.tags.split(",") for tag in tag_list)]
        
        if in_stock is not None:
            if in_stock:
                products = [p for p in products if p.inventory_count > 0]
            else:
                products = [p for p in products if p.inventory_count == 0]
        
        # Sort results
        if sort_by:
            reverse = sort_direction.lower() == "desc"
            if sort_by == "price":
                products.sort(key=lambda x: x.price, reverse=reverse)
            elif sort_by == "name":
                products.sort(key=lambda x: x.name, reverse=reverse)
            elif sort_by == "inventory_count":
                products.sort(key=lambda x: x.inventory_count, reverse=reverse)
            elif sort_by == "created_at":
                products.sort(key=lambda x: x.created_at, reverse=reverse)
        
        # Paginate results
        total = len(products)
        offset = (page - 1) * page_size
        paginated_products = products[offset:offset + page_size]
        
        # Prepare the response with pagination metadata
        return {
            "data": [p.dict() for p in paginated_products],
            "meta": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        }
    
    # Add a streaming endpoint for large datasets
    @app.get("/api/v1/products/export", tags=["Products"])
    async def export_products(
        format: str = Query("json", description="Export format (json or csv)"),
        response_class=streaming_response,
    ):
        # Get all products
        products = await Product.filter({})
        
        # Return a streaming response
        if format.lower() == "json":
            # JSON streaming format (newline-delimited JSON)
            async def stream_json():
                yield "["
                
                for i, product in enumerate(products):
                    product_json = json.dumps(product.dict())
                    if i > 0:
                        yield ","
                    yield product_json
                
                yield "]"
            
            return streaming_response(stream_json(), media_type="application/json")
        
        elif format.lower() == "csv":
            # CSV streaming format
            import csv
            import io
            
            async def stream_csv():
                # Yield CSV header
                if products:
                    fields = list(products[0].dict().keys())
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(fields)
                    yield output.getvalue()
                    output.close()
                
                # Yield CSV rows
                for product in products:
                    product_dict = product.dict()
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow([str(product_dict.get(field, "")) for field in fields])
                    yield output.getvalue()
                    output.close()
            
            return streaming_response(stream_csv(), media_type="text/csv")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    
    return app, factory


class MockDB:
    """Mock database for testing."""
    
    def __init__(self):
        """Initialize the mock database."""
        self.products = {}
        self.orders = {}
        self.order_items = {}
        self.reset()
    
    def reset(self):
        """Reset the database to its initial state."""
        # Clear existing data
        self.products.clear()
        self.orders.clear()
        self.order_items.clear()
        
        # Add some seed data
        # Products
        for i in range(1, 30):
            category = ["Electronics", "Clothing", "Books", "Home", "Toys", "Food", "Sports"][i % 7]
            price = Decimal(f"{(i * 10)}.99")
            inventory = i * 5
            tags = f"tag{i % 5},tag{(i + 1) % 5},tag{(i + 2) % 5}"
            
            product = Product(
                id=f"prod-{i}",
                name=f"Product {i}",
                description=f"Description for product {i}",
                price=price,
                sku=f"SKU-{i:05d}",
                category=category,
                inventory_count=inventory,
                is_active=i % 5 != 0,
                is_featured=i % 10 == 0,
                tags=tags,
                weight=Decimal(f"{i}.{i}"),
                dimensions=f"{i}x{i}x{i}"
            )
            
            self.products[product.id] = product
        
        # Orders
        for i in range(1, 10):
            order = Order(
                id=f"order-{i}",
                customer_id=f"cust-{i % 3 + 1}",
                order_date=datetime.now() - timedelta(days=i * 3),
                total_amount=Decimal(f"{(i * 100)}.00"),
                status=["pending", "processing", "shipped", "delivered"][i % 4]
            )
            
            self.orders[order.id] = order
            
            # Order items (2-3 items per order)
            for j in range(1, 2 + (i % 2) + 1):
                product_id = f"prod-{(i * j) % 29 + 1}"
                product = self.products[product_id]
                
                item = OrderItem(
                    id=f"item-{i}-{j}",
                    order_id=order.id,
                    product_id=product_id,
                    quantity=j,
                    unit_price=product.price
                )
                
                self.order_items[item.id] = item


# ===== MOCK ASYNC METHODS =====

async def mock_product_get(id):
    """Mock Product.get method."""
    db = MockDB()
    return db.products.get(id)

async def mock_product_filter(filters=None, page=1, page_size=10):
    """Mock Product.filter method."""
    db = MockDB()
    products = list(db.products.values())
    
    # If filters are provided, apply them
    if filters:
        if hasattr(filters, "get"):
            # Category filter
            category = filters.get("category")
            if category:
                products = [p for p in products if p.category == category]
            
            # Name contains filter
            name_contains = filters.get("name__contains")
            if name_contains:
                products = [p for p in products if name_contains.lower() in p.name.lower()]
            
            # Description contains filter
            desc_contains = filters.get("description__contains")
            if desc_contains:
                products = [p for p in products if p.description and desc_contains.lower() in p.description.lower()]
            
            # Price filters
            min_price = filters.get("price__gte")
            if min_price:
                products = [p for p in products if p.price >= min_price]
                
            max_price = filters.get("price__lte")
            if max_price:
                products = [p for p in products if p.price <= max_price]
            
            # Active filter
            is_active = filters.get("is_active")
            if is_active is not None:
                products = [p for p in products if p.is_active == is_active]
    
    # Apply pagination
    total = len(products)
    offset = (page - 1) * page_size
    paginated = products[offset:offset + page_size]
    
    # Create pagination response
    class PaginatedResponse:
        def __init__(self, items, total, page, page_size):
            self.items = items
            self.total = total
            self.page = page
            self.page_size = page_size
            self.total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(paginated, total, page, page_size)

async def mock_product_count():
    """Mock Product.count method."""
    db = MockDB()
    return len(db.products)

async def mock_product_save(self):
    """Mock Product.save method."""
    db = MockDB()
    
    # If it's a new product, generate an ID
    if not getattr(self, "id", None):
        self.id = f"prod-{len(db.products) + 1}"
    
    # Update the database
    db.products[self.id] = self
    return self

async def mock_product_delete(self):
    """Mock Product.delete method."""
    db = MockDB()
    
    # Remove from database
    if self.id in db.products:
        del db.products[self.id]
    
    return True

async def mock_order_get(id):
    """Mock Order.get method."""
    db = MockDB()
    return db.orders.get(id)

async def mock_order_filter(filters=None, page=1, page_size=10):
    """Mock Order.filter method."""
    db = MockDB()
    orders = list(db.orders.values())
    
    # If filters are provided, apply them
    if filters:
        if hasattr(filters, "get"):
            # Customer filter
            customer_id = filters.get("customer_id")
            if customer_id:
                orders = [o for o in orders if o.customer_id == customer_id]
            
            # Status filter
            status = filters.get("status")
            if status:
                orders = [o for o in orders if o.status == status]
    
    # Apply pagination
    total = len(orders)
    offset = (page - 1) * page_size
    paginated = orders[offset:offset + page_size]
    
    # Create pagination response
    class PaginatedResponse:
        def __init__(self, items, total, page, page_size):
            self.items = items
            self.total = total
            self.page = page
            self.page_size = page_size
            self.total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(paginated, total, page, page_size)

async def mock_order_count():
    """Mock Order.count method."""
    db = MockDB()
    return len(db.orders)

async def mock_order_save(self):
    """Mock Order.save method."""
    db = MockDB()
    
    # If it's a new order, generate an ID
    if not getattr(self, "id", None):
        self.id = f"order-{len(db.orders) + 1}"
    
    # Update the database
    db.orders[self.id] = self
    return self

async def mock_order_delete(self):
    """Mock Order.delete method."""
    db = MockDB()
    
    # Remove from database
    if self.id in db.orders:
        del db.orders[self.id]
    
    return True

async def mock_order_item_get(id):
    """Mock OrderItem.get method."""
    db = MockDB()
    return db.order_items.get(id)

async def mock_order_item_filter(filters=None, page=1, page_size=10):
    """Mock OrderItem.filter method."""
    db = MockDB()
    items = list(db.order_items.values())
    
    # If filters are provided, apply them
    if filters:
        if hasattr(filters, "get"):
            # Order filter
            order_id = filters.get("order_id")
            if order_id:
                items = [i for i in items if i.order_id == order_id]
            
            # Product filter
            product_id = filters.get("product_id")
            if product_id:
                items = [i for i in items if i.product_id == product_id]
    
    # Apply pagination
    total = len(items)
    offset = (page - 1) * page_size
    paginated = items[offset:offset + page_size]
    
    # Create pagination response
    class PaginatedResponse:
        def __init__(self, items, total, page, page_size):
            self.items = items
            self.total = total
            self.page = page
            self.page_size = page_size
            self.total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(paginated, total, page, page_size)

async def mock_order_item_count():
    """Mock OrderItem.count method."""
    db = MockDB()
    return len(db.order_items)

async def mock_order_item_save(self):
    """Mock OrderItem.save method."""
    db = MockDB()
    
    # If it's a new item, generate an ID
    if not getattr(self, "id", None):
        self.id = f"item-{len(db.order_items) + 1}"
    
    # Update the database
    db.order_items[self.id] = self
    return self

async def mock_order_item_delete(self):
    """Mock OrderItem.delete method."""
    db = MockDB()
    
    # Remove from database
    if self.id in db.order_items:
        del db.order_items[self.id]
    
    return True


def setup_mock_methods():
    """Set up mock methods for testing."""
    # Product methods
    patch.object(Product, 'get', mock_product_get).start()
    patch.object(Product, 'filter', mock_product_filter).start()
    patch.object(Product, 'count', mock_product_count).start()
    patch.object(Product, 'save', mock_product_save).start()
    patch.object(Product, 'delete', mock_product_delete).start()
    
    # Order methods
    patch.object(Order, 'get', mock_order_get).start()
    patch.object(Order, 'filter', mock_order_filter).start()
    patch.object(Order, 'count', mock_order_count).start()
    patch.object(Order, 'save', mock_order_save).start()
    patch.object(Order, 'delete', mock_order_delete).start()
    
    # OrderItem methods
    patch.object(OrderItem, 'get', mock_order_item_get).start()
    patch.object(OrderItem, 'filter', mock_order_item_filter).start()
    patch.object(OrderItem, 'count', mock_order_item_count).start()
    patch.object(OrderItem, 'save', mock_order_item_save).start()
    patch.object(OrderItem, 'delete', mock_order_item_delete).start()


# ===== TEST FIXTURES =====

@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app, factory = create_test_app()
    setup_mock_methods()
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the test app."""
    return TestClient(test_app)


@pytest.fixture
def auth_app():
    """Create a test FastAPI application with authentication middleware."""
    app, factory = create_test_app()
    
    # Add authentication middleware
    app.add_middleware(SimpleAuthMiddleware)
    
    setup_mock_methods()
    return app


@pytest.fixture
def auth_client(auth_app):
    """Create a test client for the auth app."""
    return TestClient(auth_app)


@pytest.fixture
def logger_app():
    """Create a test FastAPI application with request logger middleware."""
    app, factory = create_test_app()
    
    # Add request logger middleware
    logger_middleware = RequestLoggerMiddleware(app)
    app.middleware_stack = logger_middleware
    
    setup_mock_methods()
    return app, logger_middleware


@pytest.fixture
def logger_client(logger_app):
    """Create a test client for the logger app."""
    app, _ = logger_app
    return TestClient(app)


# ===== TESTS =====

# --- Pagination Tests ---

def test_list_products_pagination(test_client):
    """Test pagination of product list endpoint."""
    # Page 1 with 5 items per page
    response = test_client.get("/api/v1/product?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    
    # Verify the right number of items was returned
    assert "items" in data
    assert len(data["items"]) == 5
    
    # Verify the pagination metadata
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert data["page"] == 1
    assert data["page_size"] == 5
    
    # Get another page
    response = test_client.get("/api/v1/product?page=2&page_size=5")
    assert response.status_code == 200
    data = response.json()
    
    # Verify different items were returned
    assert len(data["items"]) == 5
    assert data["page"] == 2
    
    # Verify the items are different
    first_page_ids = [item["id"] for item in response.json()["items"]]
    previous_response = test_client.get("/api/v1/product?page=1&page_size=5")
    previous_page_ids = [item["id"] for item in previous_response.json()["items"]]
    
    # No items should appear on both pages
    assert not set(first_page_ids).intersection(set(previous_page_ids))


def test_list_products_invalid_pagination(test_client):
    """Test invalid pagination parameters."""
    # Invalid page number (negative)
    response = test_client.get("/api/v1/product?page=-1&page_size=5")
    assert response.status_code == 422  # Validation error
    
    # Invalid page size (too large)
    response = test_client.get("/api/v1/product?page=1&page_size=1000")
    assert response.status_code == 422  # Validation error
    
    # Invalid page size (negative)
    response = test_client.get("/api/v1/product?page=1&page_size=-5")
    assert response.status_code == 422  # Validation error


# --- Field Selection Tests ---

def test_product_field_selection(test_client):
    """Test field selection for product endpoints."""
    # Get a specific product with all fields
    response = test_client.get("/api/v1/product/prod-1")
    assert response.status_code == 200
    full_data = response.json()
    
    # Get the same product with only specific fields
    response = test_client.get("/api/v1/product/prod-1?fields=id,name,price")
    assert response.status_code == 200
    partial_data = response.json()
    
    # Verify that only the requested fields were returned
    assert set(partial_data.keys()) == {"id", "name", "price"}
    
    # Verify that the values match
    assert partial_data["id"] == full_data["id"]
    assert partial_data["name"] == full_data["name"]
    assert partial_data["price"] == full_data["price"]
    
    # Verify that other fields are not present
    assert "description" not in partial_data
    assert "category" not in partial_data


def test_product_list_field_selection(test_client):
    """Test field selection for product list endpoint."""
    # Get products with all fields
    response = test_client.get("/api/v1/product?page=1&page_size=5")
    assert response.status_code == 200
    full_data = response.json()
    
    # Get products with only specific fields
    response = test_client.get("/api/v1/product?page=1&page_size=5&fields=id,name,price")
    assert response.status_code == 200
    partial_data = response.json()
    
    # Verify that only the requested fields were returned for each item
    for item in partial_data["items"]:
        assert set(item.keys()) == {"id", "name", "price"}
    
    # Verify that the values match
    for i, item in enumerate(partial_data["items"]):
        assert item["id"] == full_data["items"][i]["id"]
        assert item["name"] == full_data["items"][i]["name"]
        assert item["price"] == full_data["items"][i]["price"]


# --- Filtering Tests ---

def test_advanced_product_search(test_client):
    """Test the advanced product search endpoint."""
    # Search by query
    response = test_client.get("/api/v1/products/search?q=Product")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert len(data["data"]) > 0
    
    # Search by price range
    response = test_client.get("/api/v1/products/search?min_price=50&max_price=200")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    # Verify all prices are in the specified range
    for product in data["data"]:
        price = Decimal(product["price"])
        assert price >= Decimal("50")
        assert price <= Decimal("200")
    
    # Search by categories
    response = test_client.get("/api/v1/products/search?categories=Electronics,Books")
    assert response.status_code == 200
    data = response.json()
    # Verify all products are in the specified categories
    for product in data["data"]:
        assert product["category"] in ["Electronics", "Books"]
    
    # Search for in-stock products
    response = test_client.get("/api/v1/products/search?in_stock=true")
    assert response.status_code == 200
    data = response.json()
    # Verify all products are in stock
    for product in data["data"]:
        assert product["inventory_count"] > 0
    
    # Search with sorting (price, descending)
    response = test_client.get("/api/v1/products/search?sort_by=price&sort_direction=desc")
    assert response.status_code == 200
    data = response.json()
    # Verify products are sorted by price in descending order
    prices = [Decimal(product["price"]) for product in data["data"]]
    assert prices == sorted(prices, reverse=True)
    
    # Combined search with multiple filters
    response = test_client.get("/api/v1/products/search?min_price=50&max_price=200&categories=Electronics&in_stock=true&sort_by=price")
    assert response.status_code == 200
    data = response.json()
    # Verify all constraints are met
    for product in data["data"]:
        price = Decimal(product["price"])
        assert price >= Decimal("50")
        assert price <= Decimal("200")
        assert product["category"] == "Electronics"
        assert product["inventory_count"] > 0
    
    # Verify pagination metadata
    assert "total" in data["meta"]
    assert "page" in data["meta"]
    assert "page_size" in data["meta"]
    assert "total_pages" in data["meta"]


def test_product_list_filtering(test_client):
    """Test filtering for the standard product list endpoint."""
    # Filter by category
    response = test_client.get("/api/v1/product?category=Electronics")
    assert response.status_code == 200
    data = response.json()
    
    # Verify all returned products are in the specified category
    for product in data["items"]:
        assert product["category"] == "Electronics"
    
    # Filter by active status
    response = test_client.get("/api/v1/product?is_active=true")
    assert response.status_code == 200
    data = response.json()
    
    # Verify all returned products are active
    for product in data["items"]:
        assert product["is_active"] is True


# --- Custom Endpoint Types Tests ---

def test_product_stats_endpoint(test_client):
    """Test the product stats endpoint."""
    response = test_client.get("/api/v1/product/stats")
    assert response.status_code == 200
    data = response.json()
    
    # Verify the response contains the expected statistics
    assert "total_count" in data
    assert "metrics" in data
    
    # Verify the metrics include expected values
    assert "total_inventory_value" in data["metrics"]
    assert "average_price" in data["metrics"]
    assert "out_of_stock_count" in data["metrics"]
    
    # Test with group_by parameter
    response = test_client.get("/api/v1/product/stats?group_by=category")
    assert response.status_code == 200
    data = response.json()
    
    # Verify the response includes the by_category breakdown
    assert "by_category" in data
    assert isinstance(data["by_category"], dict)
    
    # Verify the categories have the expected structure
    for category, stats in data["by_category"].items():
        assert "count" in stats
        assert "total_value" in stats


def test_order_stats_endpoint(test_client):
    """Test the order stats endpoint."""
    response = test_client.get("/api/v1/order/stats")
    assert response.status_code == 200
    data = response.json()
    
    # Verify the response contains the expected statistics
    assert "total_count" in data
    assert "metrics" in data
    
    # Verify the metrics include expected values
    assert "total_revenue" in data["metrics"]
    assert "average_order_value" in data["metrics"]
    assert "order_count" in data["metrics"]
    
    # Test with group_by parameter
    response = test_client.get("/api/v1/order/stats?group_by=status")
    assert response.status_code == 200
    data = response.json()
    
    # Verify the response includes the by_status breakdown
    assert "by_status" in data
    assert isinstance(data["by_status"], dict)
    
    # Test with time_range parameter
    response = test_client.get("/api/v1/order/stats?time_range=week")
    assert response.status_code == 200
    data = response.json()
    
    # Verify the response includes the time_range_stats
    assert "time_range_stats" in data
    assert "period" in data["time_range_stats"]
    assert "order_count" in data["time_range_stats"]
    assert "total_revenue" in data["time_range_stats"]


def test_batch_operations_endpoint(test_client):
    """Test the batch operations endpoint."""
    # Test batch create
    batch_create_data = {
        "operation": "create",
        "items": [
            {
                "name": "Batch Product 1",
                "description": "Created in batch",
                "price": "29.99",
                "sku": "BAT-00001",
                "category": "Electronics",
                "inventory_count": 10,
                "is_active": True
            },
            {
                "name": "Batch Product 2",
                "description": "Created in batch",
                "price": "39.99",
                "sku": "BAT-00002",
                "category": "Books",
                "inventory_count": 20,
                "is_active": True
            }
        ]
    }
    
    response = test_client.post("/api/v1/product/batch", json=batch_create_data)
    assert response.status_code == 200
    data = response.json()
    
    # Verify the response format
    assert "success_count" in data
    assert "error_count" in data
    assert "results" in data
    
    # Verify the results
    assert data["success_count"] == 2
    assert data["error_count"] == 0
    assert len(data["results"]) == 2
    
    # Get the IDs of the created products
    product_ids = [result["id"] for result in data["results"]]
    
    # Test batch update
    batch_update_data = {
        "operation": "update",
        "items": [
            {
                "id": product_ids[0],
                "price": "49.99",
                "inventory_count": 15
            },
            {
                "id": product_ids[1],
                "price": "59.99",
                "inventory_count": 25
            }
        ]
    }
    
    response = test_client.post("/api/v1/product/batch", json=batch_update_data)
    assert response.status_code == 200
    data = response.json()
    
    # Verify the results
    assert data["success_count"] == 2
    assert data["error_count"] == 0
    
    # Verify the updates were applied
    for result in data["results"]:
        if result["id"] == product_ids[0]:
            assert result["data"]["price"] == "49.99"
            assert result["data"]["inventory_count"] == 15
        elif result["id"] == product_ids[1]:
            assert result["data"]["price"] == "59.99"
            assert result["data"]["inventory_count"] == 25
    
    # Test batch delete
    batch_delete_data = {
        "operation": "delete",
        "items": [
            {"id": product_ids[0]},
            {"id": product_ids[1]}
        ]
    }
    
    response = test_client.post("/api/v1/product/batch", json=batch_delete_data)
    assert response.status_code == 200
    data = response.json()
    
    # Verify the results
    assert data["success_count"] == 2
    assert data["error_count"] == 0
    
    # Verify the products were deleted by trying to fetch them
    for product_id in product_ids:
        response = test_client.get(f"/api/v1/product/{product_id}")
        assert response.status_code == 404


def test_batch_operations_with_errors(test_client):
    """Test batch operations with errors."""
    # Test batch create with some invalid items
    batch_create_data = {
        "operation": "create",
        "items": [
            {
                "name": "Valid Product",
                "description": "This should succeed",
                "price": "29.99",
                "sku": "BAT-00003",
                "category": "Electronics",
                "inventory_count": 10,
                "is_active": True
            },
            {
                "name": "Invalid Product",
                "description": "This should fail",
                "price": "-10.00",  # Invalid negative price
                "sku": "invalid-sku",  # Invalid SKU format
                "category": "Invalid Category",  # Invalid category
                "inventory_count": 10,
                "is_active": True
            }
        ]
    }
    
    response = test_client.post("/api/v1/product/batch", json=batch_create_data)
    assert response.status_code == 200
    data = response.json()
    
    # Verify the response contains mixed results
    assert data["success_count"] == 1
    assert data["error_count"] == 1
    assert len(data["results"]) == 2
    
    # Verify the successful and error results
    successful_result = next((r for r in data["results"] if r["success"]), None)
    error_result = next((r for r in data["results"] if not r["success"]), None)
    
    assert successful_result is not None
    assert error_result is not None
    assert "id" in successful_result
    assert "error" in error_result
    
    # Test invalid operation
    invalid_operation_data = {
        "operation": "invalid_op",
        "items": [
            {"id": "prod-1", "price": "99.99"}
        ]
    }
    
    response = test_client.post("/api/v1/product/batch", json=invalid_operation_data)
    assert response.status_code == 400


# --- Authentication and Security Tests ---

def test_authenticated_endpoint(auth_client):
    """Test an endpoint that requires authentication."""
    # Without authentication
    response = auth_client.get("/api/v1/me")
    assert response.status_code == 401
    
    # With invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = auth_client.get("/api/v1/me", headers=headers)
    assert response.status_code == 401
    
    # With valid token
    headers = {"Authorization": "Bearer test_token"}
    response = auth_client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert "email" in data


def test_auth_middleware_with_api_endpoints(auth_client):
    """Test that middleware applies to all API endpoints."""
    # List products without authentication
    response = auth_client.get("/api/v1/product")
    assert response.status_code == 401
    
    # With valid token
    headers = {"Authorization": "Bearer test_token"}
    response = auth_client.get("/api/v1/product", headers=headers)
    assert response.status_code == 200


# --- Request Logging Middleware Tests ---

def test_request_logger_middleware(logger_client, logger_app):
    """Test the request logger middleware."""
    _, logger_middleware = logger_app
    
    # Clear logs
    logger_middleware.clear_logs()
    
    # Make some requests
    logger_client.get("/api/v1/product")
    logger_client.get("/api/v1/product/prod-1")
    logger_client.post("/api/v1/product", json={
        "name": "Test Product",
        "description": "Test description",
        "price": "99.99",
        "sku": "TST-12345",
        "category": "Electronics",
        "inventory_count": 10
    })
    
    # Get the logs
    logs = logger_middleware.get_logs()
    
    # Verify that all requests were logged
    assert len(logs) == 3
    
    # Verify the log structure
    for log in logs:
        assert "method" in log
        assert "path" in log
        assert "query_string" in log
        assert "headers" in log
        assert "timestamp" in log
    
    # Verify specific methods
    assert logs[0]["method"] == "GET"
    assert logs[1]["method"] == "GET"
    assert logs[2]["method"] == "POST"
    
    # Verify paths
    assert logs[0]["path"] == "/api/v1/product"
    assert logs[1]["path"] == "/api/v1/product/prod-1"
    assert logs[2]["path"] == "/api/v1/product"


# --- HATEOAS Links Tests ---

def test_hateoas_links(test_client):
    """Test endpoint that returns HATEOAS links."""
    response = test_client.get("/api/v1/products/prod-1/details")
    assert response.status_code == 200
    data = response.json()
    
    # Verify the HATEOAS links are present
    assert "_links" in data
    assert "self" in data["_links"]
    assert "update" in data["_links"]
    assert "delete" in data["_links"]
    assert "stats" in data["_links"]
    assert "orders" in data["_links"]
    
    # Verify the link format
    for link_name, link_data in data["_links"].items():
        assert "href" in link_data
        assert link_data["href"].startswith("/api/v1/")


# --- Error Handling Tests ---

def test_not_found_errors(test_client):
    """Test 404 error handling."""
    # Non-existent product
    response = test_client.get("/api/v1/product/non-existent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()
    
    # Non-existent endpoint
    response = test_client.get("/api/v1/non-existent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_validation_errors(test_client):
    """Test validation error handling."""
    # Invalid product data
    invalid_product = {
        "name": "Invalid Product",
        "description": "Product with invalid data",
        "price": "-10.00",  # Invalid negative price
        "sku": "invalid-sku",  # Invalid SKU format
        "category": "Invalid Category",  # Invalid category
        "inventory_count": 10
    }
    
    response = test_client.post("/api/v1/product", json=invalid_product)
    assert response.status_code == 422  # Validation error
    data = response.json()
    
    # Verify the error response format
    assert "detail" in data
    
    # The validation errors should contain information about each invalid field
    errors = data["detail"]
    error_fields = [error["loc"][1] for error in errors]
    
    # Check for specific validation errors
    assert "price" in error_fields or "sku" in error_fields or "category" in error_fields


def test_internal_server_error_handling(test_client):
    """Test internal server error handling."""
    # This test requires modifying the application to trigger an internal error
    # For now, we'll just verify that error responses follow the expected format
    
    # The format should include a detail field
    response = test_client.get("/api/v1/product/non-existent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# --- Streaming Response Tests ---

def test_export_products_endpoint(test_client):
    """Test the streaming export endpoint."""
    # Export as JSON
    response = test_client.get("/api/v1/products/export?format=json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    # Verify the response is valid JSON
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Export as CSV
    response = test_client.get("/api/v1/products/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    
    # Verify the response is valid CSV (at least check headers and rows)
    content = response.content.decode("utf-8")
    lines = content.strip().split("\n")
    assert len(lines) > 1  # Header + at least one row
    
    # Verify invalid format handling
    response = test_client.get("/api/v1/products/export?format=invalid")
    assert response.status_code == 400


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])