"""
HATEOAS (Hypermedia as the Engine of Application State) support for UnoEndpoint APIs.

This module demonstrates how to implement HATEOAS links for UnoEndpoint-based
APIs, providing a more discoverable and self-describing REST API.

HATEOAS allows clients to navigate the API by following links provided in responses,
rather than having to know the structure of the API in advance.
"""

import enum
from typing import Dict, List, Optional, Any, Union, Type, Set, Callable
from datetime import datetime

from fastapi import FastAPI, status, APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict, create_model, computed_field
from sqlalchemy.orm import Mapped, mapped_column

from uno.model import UnoModel, PostgresTypes
from uno.api.endpoint import UnoEndpoint, UnoRouter
from uno.api.endpoint_factory import UnoEndpointFactory


# ===== HATEOAS LINK MODELS =====

class LinkRelation(str, enum.Enum):
    """Standard link relation types for HATEOAS."""
    
    SELF = "self"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NEXT = "next"
    PREV = "prev"
    FIRST = "first"
    LAST = "last"
    COLLECTION = "collection"
    SEARCH = "search"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    RELATED = "related"
    ALTERNATE = "alternate"
    ITEM = "item"
    PARENT = "parent"
    CHILD = "child"


class Link(BaseModel):
    """Model for a HATEOAS link."""
    
    href: str
    rel: LinkRelation
    method: Optional[str] = "GET"
    title: Optional[str] = None
    type: Optional[str] = None


class LinksModel(BaseModel):
    """Base model for any resource with HATEOAS links."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    _links: Dict[str, Link] = Field(default_factory=dict)


# ===== LINK BUILDER =====

class LinkBuilder:
    """Helper for building HATEOAS links for resources."""
    
    def __init__(self, base_url: str = ""):
        """Initialize the link builder."""
        self.base_url = base_url.rstrip("/")
    
    def build_link(
        self,
        href: str,
        rel: Union[str, LinkRelation],
        method: str = "GET",
        title: Optional[str] = None,
        link_type: Optional[str] = None
    ) -> Link:
        """Build a single link."""
        # Normalize the href
        if not href.startswith(("http://", "https://", "/")):
            href = f"/{href.lstrip('/')}"
        
        if href.startswith("/") and self.base_url:
            href = f"{self.base_url}{href}"
        
        # Normalize the relation
        if isinstance(rel, str):
            try:
                rel = LinkRelation(rel)
            except ValueError:
                # Custom relation - keep as is
                pass
        
        return Link(
            href=href,
            rel=rel,
            method=method,
            title=title,
            type=link_type
        )
    
    def build_self_link(self, resource_path: str, title: Optional[str] = None) -> Link:
        """Build a 'self' link for a resource."""
        return self.build_link(
            href=resource_path,
            rel=LinkRelation.SELF,
            title=title or "Self"
        )
    
    def build_collection_link(self, collection_path: str, title: Optional[str] = None) -> Link:
        """Build a 'collection' link for a resource collection."""
        return self.build_link(
            href=collection_path,
            rel=LinkRelation.COLLECTION,
            title=title or "Collection"
        )
    
    def build_create_link(self, resource_path: str, title: Optional[str] = None) -> Link:
        """Build a 'create' link for a resource."""
        return self.build_link(
            href=resource_path,
            rel=LinkRelation.CREATE,
            method="POST",
            title=title or "Create"
        )
    
    def build_update_link(self, resource_path: str, title: Optional[str] = None) -> Link:
        """Build an 'update' link for a resource."""
        return self.build_link(
            href=resource_path,
            rel=LinkRelation.UPDATE,
            method="PUT",
            title=title or "Update"
        )
    
    def build_patch_link(self, resource_path: str, title: Optional[str] = None) -> Link:
        """Build a 'patch' link for a resource."""
        return self.build_link(
            href=resource_path,
            rel="edit",  # Custom relation for PATCH
            method="PATCH",
            title=title or "Patch"
        )
    
    def build_delete_link(self, resource_path: str, title: Optional[str] = None) -> Link:
        """Build a 'delete' link for a resource."""
        return self.build_link(
            href=resource_path,
            rel=LinkRelation.DELETE,
            method="DELETE",
            title=title or "Delete"
        )
    
    def build_pagination_links(
        self,
        base_path: str,
        page: int,
        page_size: int,
        total_items: int,
        query_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Link]:
        """Build pagination links for a collection."""
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
        
        # Prepare query parameters
        query_params = query_params or {}
        query_params = {k: v for k, v in query_params.items() if k not in ["page", "page_size"]}
        
        query_string_parts = []
        for key, value in query_params.items():
            query_string_parts.append(f"{key}={value}")
        
        # Add pagination parameters
        query_string_parts.append(f"page_size={page_size}")
        
        # Build the base path with query string
        query_string_base = "&".join(query_string_parts)
        
        links = {}
        
        # Current page (self)
        self_path = f"{base_path}?{query_string_base}&page={page}"
        links["self"] = self.build_link(self_path, LinkRelation.SELF, title="Current Page")
        
        # First page
        first_path = f"{base_path}?{query_string_base}&page=1"
        links["first"] = self.build_link(first_path, LinkRelation.FIRST, title="First Page")
        
        # Last page
        last_path = f"{base_path}?{query_string_base}&page={total_pages}"
        links["last"] = self.build_link(last_path, LinkRelation.LAST, title="Last Page")
        
        # Previous page
        if page > 1:
            prev_path = f"{base_path}?{query_string_base}&page={page - 1}"
            links["prev"] = self.build_link(prev_path, LinkRelation.PREV, title="Previous Page")
        
        # Next page
        if page < total_pages:
            next_path = f"{base_path}?{query_string_base}&page={page + 1}"
            links["next"] = self.build_link(next_path, LinkRelation.NEXT, title="Next Page")
        
        return links


# ===== HATEOAS ROUTERS =====

class HATEOASResponseModel(BaseModel):
    """Base model for HATEOAS responses."""
    
    data: Any
    _links: Dict[str, Link]
    meta: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )


class HATEOASListRouter(UnoRouter):
    """Router for resource lists with HATEOAS links."""
    
    path_suffix: str = ""
    method: str = "GET"
    path_prefix: str = "/api"
    tags: List[str] = None
    link_builder: Optional[LinkBuilder] = None
    
    @property
    def summary(self) -> str:
        return f"List {self.model.display_name_plural} with HATEOAS links"
    
    @property
    def description(self) -> str:
        return f"""
            List {self.model.display_name_plural} with HATEOAS links.
            
            The response includes:
            - data: The list of resources
            - _links: Navigation links for the collection and related resources
            - meta: Metadata about the response, including pagination info
            
            Supports the following query parameters:
            - page: Page number for pagination (default: 1)
            - page_size: Number of items per page (default: 20, max: 100)
        """
    
    def endpoint_factory(self):
        from fastapi import Request, Query
        from typing import List, Dict, Any, Optional
        
        async def endpoint(
            self,
            request: Request,
            page: int = Query(1, ge=1, description="Page number"),
            page_size: int = Query(20, ge=1, le=100, description="Items per page")
        ) -> Dict[str, Any]:
            # Get the base URL for links
            base_url = str(request.base_url).rstrip("/")
            
            # Create a link builder if not provided
            link_builder = self.link_builder or LinkBuilder(base_url)
            
            # Get the resource path for links
            resource_path = f"{self.path_prefix}/{self.model.__name__.lower()}"
            
            # Get the resources with pagination
            resources = await self.model.filter(page=page, page_size=page_size)
            
            # Extract items and total count
            if hasattr(resources, "items") and hasattr(resources, "total"):
                items = resources.items
                total_items = resources.total
            else:
                items = resources
                total_items = len(resources)
            
            # Convert to dictionaries for serialization
            items_dict = [item.dict() for item in items]
            
            # Add self links to each item
            for i, item in enumerate(items_dict):
                item_id = item.get("id")
                if item_id:
                    item_path = f"{resource_path}/{item_id}"
                    item["_links"] = {
                        "self": link_builder.build_self_link(item_path).dict()
                    }
            
            # Calculate pagination metadata
            total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
            
            # Build collection links
            collection_links = link_builder.build_pagination_links(
                base_path=resource_path,
                page=page,
                page_size=page_size,
                total_items=total_items
            )
            
            # Add create link
            collection_links["create"] = link_builder.build_create_link(resource_path).dict()
            
            # Build the response
            response = {
                "data": items_dict,
                "_links": {key: link.dict() for key, link in collection_links.items()},
                "meta": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": total_pages
                }
            }
            
            return response
        
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


class HATEOASDetailRouter(UnoRouter):
    """Router for resource details with HATEOAS links."""
    
    path_suffix: str = "/{id}"
    method: str = "GET"
    path_prefix: str = "/api"
    tags: List[str] = None
    link_builder: Optional[LinkBuilder] = None
    
    @property
    def summary(self) -> str:
        return f"Get {self.model.display_name} details with HATEOAS links"
    
    @property
    def description(self) -> str:
        return f"""
            Get details for a specific {self.model.display_name} with HATEOAS links.
            
            The response includes:
            - data: The resource details
            - _links: Navigation links for this resource and related resources
        """
    
    def endpoint_factory(self):
        from fastapi import Request, Path
        from typing import Dict, Any
        
        async def endpoint(
            self,
            request: Request,
            id: str = Path(..., description=f"{self.model.display_name} ID")
        ) -> Dict[str, Any]:
            # Get the base URL for links
            base_url = str(request.base_url).rstrip("/")
            
            # Create a link builder if not provided
            link_builder = self.link_builder or LinkBuilder(base_url)
            
            # Get the resource paths for links
            resource_path = f"{self.path_prefix}/{self.model.__name__.lower()}"
            instance_path = f"{resource_path}/{id}"
            
            # Get the resource
            resource = await self.model.get(id)
            
            # Check if the resource exists
            if not resource:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.display_name} not found"
                )
            
            # Convert to dictionary for serialization
            resource_dict = resource.dict()
            
            # Build resource links
            resource_links = {
                "self": link_builder.build_self_link(instance_path).dict(),
                "collection": link_builder.build_collection_link(resource_path).dict(),
                "update": link_builder.build_update_link(instance_path).dict(),
                "delete": link_builder.build_delete_link(instance_path).dict(),
            }
            
            # Add resource-specific links based on resource type
            # This is where you would add custom links for related resources
            
            # Build the response
            response = {
                "data": resource_dict,
                "_links": resource_links
            }
            
            return response
        
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


class HATEOASCreateRouter(UnoRouter):
    """Router for creating resources with HATEOAS links."""
    
    path_suffix: str = ""
    method: str = "POST"
    path_prefix: str = "/api"
    tags: List[str] = None
    link_builder: Optional[LinkBuilder] = None
    
    @property
    def summary(self) -> str:
        return f"Create {self.model.display_name} with HATEOAS links"
    
    @property
    def description(self) -> str:
        return f"""
            Create a new {self.model.display_name} with HATEOAS links.
            
            The response includes:
            - data: The created resource
            - _links: Navigation links for this resource and related resources
        """
    
    def endpoint_factory(self):
        from fastapi import Request, Body, Response
        from typing import Dict, Any
        
        async def endpoint(
            self,
            request: Request,
            response: Response,
            body: Dict[str, Any] = Body(..., description=f"{self.model.display_name} data")
        ) -> Dict[str, Any]:
            # Get the base URL for links
            base_url = str(request.base_url).rstrip("/")
            
            # Create a link builder if not provided
            link_builder = self.link_builder or LinkBuilder(base_url)
            
            # Create the resource
            resource = self.model(**body)
            
            # Save the resource
            await resource.save()
            
            # Set the response status code
            response.status_code = status.HTTP_201_CREATED
            
            # Get the resource paths for links
            resource_path = f"{self.path_prefix}/{self.model.__name__.lower()}"
            instance_path = f"{resource_path}/{resource.id}"
            
            # Convert to dictionary for serialization
            resource_dict = resource.dict()
            
            # Build resource links
            resource_links = {
                "self": link_builder.build_self_link(instance_path).dict(),
                "collection": link_builder.build_collection_link(resource_path).dict(),
                "update": link_builder.build_update_link(instance_path).dict(),
                "delete": link_builder.build_delete_link(instance_path).dict(),
            }
            
            # Build the response
            response_data = {
                "data": resource_dict,
                "_links": resource_links
            }
            
            return response_data
        
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


class HATEOASUpdateRouter(UnoRouter):
    """Router for updating resources with HATEOAS links."""
    
    path_suffix: str = "/{id}"
    method: str = "PUT"
    path_prefix: str = "/api"
    tags: List[str] = None
    link_builder: Optional[LinkBuilder] = None
    
    @property
    def summary(self) -> str:
        return f"Update {self.model.display_name} with HATEOAS links"
    
    @property
    def description(self) -> str:
        return f"""
            Update an existing {self.model.display_name} with HATEOAS links.
            
            The response includes:
            - data: The updated resource
            - _links: Navigation links for this resource and related resources
        """
    
    def endpoint_factory(self):
        from fastapi import Request, Body, Path
        from typing import Dict, Any
        
        async def endpoint(
            self,
            request: Request,
            id: str = Path(..., description=f"{self.model.display_name} ID"),
            body: Dict[str, Any] = Body(..., description=f"{self.model.display_name} data")
        ) -> Dict[str, Any]:
            # Get the base URL for links
            base_url = str(request.base_url).rstrip("/")
            
            # Create a link builder if not provided
            link_builder = self.link_builder or LinkBuilder(base_url)
            
            # Get the resource
            resource = await self.model.get(id)
            
            # Check if the resource exists
            if not resource:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.display_name} not found"
                )
            
            # Update the resource
            for key, value in body.items():
                setattr(resource, key, value)
            
            # Save the updated resource
            await resource.save()
            
            # Get the resource paths for links
            resource_path = f"{self.path_prefix}/{self.model.__name__.lower()}"
            instance_path = f"{resource_path}/{id}"
            
            # Convert to dictionary for serialization
            resource_dict = resource.dict()
            
            # Build resource links
            resource_links = {
                "self": link_builder.build_self_link(instance_path).dict(),
                "collection": link_builder.build_collection_link(resource_path).dict(),
                "update": link_builder.build_update_link(instance_path).dict(),
                "delete": link_builder.build_delete_link(instance_path).dict(),
            }
            
            # Build the response
            response = {
                "data": resource_dict,
                "_links": resource_links
            }
            
            return response
        
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


class HATEOASDeleteRouter(UnoRouter):
    """Router for deleting resources with HATEOAS links."""
    
    path_suffix: str = "/{id}"
    method: str = "DELETE"
    path_prefix: str = "/api"
    tags: List[str] = None
    link_builder: Optional[LinkBuilder] = None
    
    @property
    def summary(self) -> str:
        return f"Delete {self.model.display_name} with HATEOAS links"
    
    @property
    def description(self) -> str:
        return f"""
            Delete a {self.model.display_name} with HATEOAS links.
            
            The response includes:
            - data: Confirmation of deletion
            - _links: Navigation links for related resources
        """
    
    def endpoint_factory(self):
        from fastapi import Request, Path
        from typing import Dict, Any
        
        async def endpoint(
            self,
            request: Request,
            id: str = Path(..., description=f"{self.model.display_name} ID")
        ) -> Dict[str, Any]:
            # Get the base URL for links
            base_url = str(request.base_url).rstrip("/")
            
            # Create a link builder if not provided
            link_builder = self.link_builder or LinkBuilder(base_url)
            
            # Get the resource
            resource = await self.model.get(id)
            
            # Check if the resource exists
            if not resource:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.display_name} not found"
                )
            
            # Delete the resource
            result = await resource.delete()
            
            # Get the resource path for links
            resource_path = f"{self.path_prefix}/{self.model.__name__.lower()}"
            
            # Build resource links
            resource_links = {
                "collection": link_builder.build_collection_link(resource_path).dict(),
                "create": link_builder.build_create_link(resource_path).dict(),
            }
            
            # Build the response
            response = {
                "data": {
                    "id": id,
                    "deleted": True,
                    "timestamp": datetime.now().isoformat()
                },
                "_links": resource_links
            }
            
            return response
        
        endpoint.__annotations__["return"] = Dict[str, Any]
        setattr(self.__class__, "endpoint", endpoint)


# ===== HATEOAS ENDPOINTS =====

class HATEOASListEndpoint(UnoEndpoint):
    """Endpoint for listing resources with HATEOAS links."""
    
    router: UnoRouter = HATEOASListRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class HATEOASDetailEndpoint(UnoEndpoint):
    """Endpoint for retrieving resource details with HATEOAS links."""
    
    router: UnoRouter = HATEOASDetailRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


class HATEOASCreateEndpoint(UnoEndpoint):
    """Endpoint for creating resources with HATEOAS links."""
    
    router: UnoRouter = HATEOASCreateRouter
    body_model: Optional[str] = "edit_schema"
    response_model: Optional[str] = None


class HATEOASUpdateEndpoint(UnoEndpoint):
    """Endpoint for updating resources with HATEOAS links."""
    
    router: UnoRouter = HATEOASUpdateRouter
    body_model: Optional[str] = "edit_schema"
    response_model: Optional[str] = None


class HATEOASDeleteEndpoint(UnoEndpoint):
    """Endpoint for deleting resources with HATEOAS links."""
    
    router: UnoRouter = HATEOASDeleteRouter
    body_model: Optional[str] = None
    response_model: Optional[str] = None


# ===== EXAMPLE RESOURCE MODELS =====

class ProductModel(UnoModel):
    """Example product model for demonstrating HATEOAS."""
    
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    category: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class CategoryModel(UnoModel):
    """Example category model for demonstrating HATEOAS."""
    
    __tablename__ = "categories"
    
    name: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    parent_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


# ===== EXAMPLE USAGE =====

def create_app():
    """Create a FastAPI application with HATEOAS endpoints."""
    # Create the app
    app = FastAPI(title="HATEOAS Example", description="API with HATEOAS links support")
    
    # Create the endpoint factory
    factory = UnoEndpointFactory()
    
    # Register HATEOAS endpoint types
    factory.register_endpoint_type("HATEOASList", HATEOASListEndpoint)
    factory.register_endpoint_type("HATEOASDetail", HATEOASDetailEndpoint)
    factory.register_endpoint_type("HATEOASCreate", HATEOASCreateEndpoint)
    factory.register_endpoint_type("HATEOASUpdate", HATEOASUpdateEndpoint)
    factory.register_endpoint_type("HATEOASDelete", HATEOASDeleteEndpoint)
    
    # Create HATEOAS endpoints for products
    product_endpoints = factory.create_endpoints(
        app=app,
        model_obj=ProductModel,
        endpoints=[
            "HATEOASList",
            "HATEOASDetail",
            "HATEOASCreate",
            "HATEOASUpdate",
            "HATEOASDelete"
        ],
        endpoint_tags=["Products"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    # Create HATEOAS endpoints for categories
    category_endpoints = factory.create_endpoints(
        app=app,
        model_obj=CategoryModel,
        endpoints=[
            "HATEOASList",
            "HATEOASDetail",
            "HATEOASCreate",
            "HATEOASUpdate",
            "HATEOASDelete"
        ],
        endpoint_tags=["Categories"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    # Add custom relationship endpoints
    
    @app.get("/api/v1/categories/{category_id}/products", tags=["Relationships"])
    async def get_products_by_category(request: Request, category_id: str):
        """
        Get products in a specific category.
        
        This endpoint demonstrates a relationship endpoint with HATEOAS links.
        """
        # Get the base URL for links
        base_url = str(request.base_url).rstrip("/")
        
        # Create a link builder
        link_builder = LinkBuilder(base_url)
        
        # Get the category
        category = await CategoryModel.get(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # In a real app, you'd query products by category
        # Here we'll just create a mock response
        products = [
            {
                "id": f"prod-{i}",
                "name": f"Product {i} in {category.name}",
                "price": 10.99 + i,
                "category": category.name
            }
            for i in range(1, 6)
        ]
        
        # Add self links to each product
        for product in products:
            product_path = f"/api/v1/products/{product['id']}"
            product["_links"] = {
                "self": link_builder.build_self_link(product_path).dict()
            }
        
        # Build links
        category_path = f"/api/v1/categories/{category_id}"
        products_path = f"{category_path}/products"
        
        links = {
            "self": link_builder.build_self_link(products_path).dict(),
            "category": link_builder.build_link(
                href=category_path,
                rel=LinkRelation.PARENT,
                title=f"Parent Category: {category.name}"
            ).dict(),
            "all_products": link_builder.build_link(
                href="/api/v1/products",
                rel=LinkRelation.COLLECTION,
                title="All Products"
            ).dict()
        }
        
        # Build the response
        response = {
            "data": products,
            "_links": links,
            "meta": {
                "category": {
                    "id": category.id,
                    "name": category.name
                },
                "total_products": len(products)
            }
        }
        
        return response
    
    @app.get("/api/v1/products/{product_id}/related", tags=["Relationships"])
    async def get_related_products(request: Request, product_id: str):
        """
        Get products related to a specific product.
        
        This endpoint demonstrates another relationship endpoint with HATEOAS links.
        """
        # Get the base URL for links
        base_url = str(request.base_url).rstrip("/")
        
        # Create a link builder
        link_builder = LinkBuilder(base_url)
        
        # Get the product
        product = await ProductModel.get(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # In a real app, you'd query related products based on some criteria
        # Here we'll just create a mock response
        related_products = [
            {
                "id": f"prod-rel-{i}",
                "name": f"Related Product {i}",
                "price": 15.99 + i,
                "category": product.category,
                "similarity_score": 0.9 - (i * 0.1)
            }
            for i in range(1, 4)
        ]
        
        # Add self links to each related product
        for related in related_products:
            related_path = f"/api/v1/products/{related['id']}"
            related["_links"] = {
                "self": link_builder.build_self_link(related_path).dict()
            }
        
        # Build links
        product_path = f"/api/v1/products/{product_id}"
        related_path = f"{product_path}/related"
        
        links = {
            "self": link_builder.build_self_link(related_path).dict(),
            "product": link_builder.build_link(
                href=product_path,
                rel=LinkRelation.PARENT,
                title=f"Original Product: {product.name}"
            ).dict(),
            "all_products": link_builder.build_link(
                href="/api/v1/products",
                rel=LinkRelation.COLLECTION,
                title="All Products"
            ).dict()
        }
        
        # Build the response
        response = {
            "data": related_products,
            "_links": links,
            "meta": {
                "product": {
                    "id": product.id,
                    "name": product.name
                },
                "relationship_type": "similar_products",
                "total_related": len(related_products)
            }
        }
        
        return response
    
    # Add the API root discovery endpoint
    @app.get("/api", tags=["API"])
    async def api_root(request: Request):
        """
        API root endpoint that provides links to available resources.
        
        This endpoint serves as the entry point for API discovery.
        """
        # Get the base URL for links
        base_url = str(request.base_url).rstrip("/")
        
        # Create a link builder
        link_builder = LinkBuilder(base_url)
        
        # Build links to main resources
        links = {
            "self": link_builder.build_self_link("/api").dict(),
            "products": link_builder.build_link(
                href="/api/v1/products",
                rel=LinkRelation.COLLECTION,
                title="Products Collection"
            ).dict(),
            "categories": link_builder.build_link(
                href="/api/v1/categories",
                rel=LinkRelation.COLLECTION,
                title="Categories Collection"
            ).dict(),
            "docs": link_builder.build_link(
                href="/docs",
                rel="documentation",
                title="API Documentation"
            ).dict(),
            "openapi": link_builder.build_link(
                href="/openapi.json",
                rel="describedby",
                title="OpenAPI Schema"
            ).dict()
        }
        
        # Build the response
        response = {
            "name": "HATEOAS Example API",
            "version": "1.0.0",
            "description": "Example API with HATEOAS links support",
            "_links": links
        }
        
        return response
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Create the app
    app = create_app()
    
    # Run the app
    uvicorn.run(app, host="127.0.0.1", port=8000)