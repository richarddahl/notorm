"""
Example of using semantic search functionality in the Uno framework.

This module provides a complete example of how to use the semantic search
functionality, including integration with FastAPI and domain entities.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, UTC

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field

from uno.ai.semantic_search import SemanticSearchEngine, create_search_router
from uno.ai.semantic_search.integration import EntityIndexer, connect_entity_events
from uno.core.unified_events import EventBus, UnoDomainEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Uno Semantic Search Example")


# Sample domain entity
class Product(BaseModel):
    """Product entity with searchable content."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.UTC))
    updated_at: Optional[datetime] = None

    def update(self, **kwargs: Any) -> None:
        """Update product fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.updated_at = datetime.now(datetime.UTC)


# Events for product lifecycle
class ProductCreatedEvent(UnoDomainEvent):
    """Event fired when a product is created."""

    entity: Product


class ProductUpdatedEvent(UnoDomainEvent):
    """Event fired when a product is updated."""

    entity: Product


class ProductDeletedEvent(UnoDomainEvent):
    """Event fired when a product is deleted."""

    entity_id: UUID
    entity_type: str = "product"


# Simple in-memory repository
class ProductRepository:
    """Simple in-memory repository for products."""

    def __init__(self):
        """Initialize the repository."""
        self.products: Dict[UUID, Product] = {}
        self.event_bus = EventBus()

    async def get_by_id(self, id: UUID) -> Optional[Product]:
        """Get a product by ID."""
        return self.products.get(id)

    async def list(self) -> List[Product]:
        """List all products."""
        return list(self.products.values())

    async def create(self, product: Product) -> Product:
        """Create a new product."""
        self.products[product.id] = product

        # Fire created event
        await self.event_bus.publish(ProductCreatedEvent(entity=product))

        return product

    async def update(self, product: Product) -> Product:
        """Update an existing product."""
        if product.id not in self.products:
            raise ValueError(f"Product {product.id} not found")

        self.products[product.id] = product

        # Fire updated event
        await self.event_bus.publish(ProductUpdatedEvent(entity=product))

        return product

    async def delete(self, id: UUID) -> bool:
        """Delete a product."""
        if id not in self.products:
            return False

        del self.products[id]

        # Fire deleted event
        await self.event_bus.publish(ProductDeletedEvent(entity_id=id))

        return True


# Request and response models
class ProductCreate(BaseModel):
    """Model for creating a product."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    category: str = Field(..., description="Product category")


class ProductUpdate(BaseModel):
    """Model for updating a product."""

    name: Optional[str] = Field(None, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[float] = Field(None, gt=0, description="Product price")
    category: Optional[str] = Field(None, description="Product category")


class ProductSearchResult(BaseModel):
    """Model for a product search result."""

    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    similarity: float = Field(..., description="Similarity score (0-1)")


# Create repository and dependencies
product_repository = ProductRepository()


def get_repository():
    """Get the product repository."""
    return product_repository


# Create search engine
async def setup_search():
    """Set up the search engine and integration."""
    # Create search engine
    engine = SemanticSearchEngine(
        connection_string="postgresql://postgres:postgres@localhost:5432/uno"
    )

    # Initialize search engine
    await engine.initialize()

    # Create entity indexer
    indexer = EntityIndexer(
        engine=engine,
        entity_type="product",
        text_extractor=lambda p: f"{p.name} {p.description} {p.category}",
        metadata_extractor=lambda p: {
            "name": p.name,
            "price": p.price,
            "category": p.category,
        },
        entity_class=Product,
    )

    # Connect to events
    connect_entity_events(
        indexer=indexer,
        event_bus=product_repository.event_bus,
        entity_created_event=ProductCreatedEvent,
        entity_updated_event=ProductUpdatedEvent,
        entity_deleted_event=ProductDeletedEvent,
    )

    # Create router
    router = create_search_router(engine)

    # Add router to app
    app.include_router(router, prefix="/api")

    return engine


# Create and register product routes
product_router = APIRouter(prefix="/api/products", tags=["products"])


@product_router.post("", response_model=Product, status_code=201)
async def create_product(
    data: ProductCreate, repository: ProductRepository = Depends(get_repository)
):
    """Create a new product."""
    product = Product(**data.dict())
    return await repository.create(product)


@product_router.get("", response_model=List[Product])
async def list_products(repository: ProductRepository = Depends(get_repository)):
    """List all products."""
    return await repository.list()


@product_router.get("/{id}", response_model=Product)
async def get_product(
    id: UUID, repository: ProductRepository = Depends(get_repository)
):
    """Get a product by ID."""
    product = await repository.get_by_id(id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@product_router.patch("/{id}", response_model=Product)
async def update_product(
    id: UUID,
    data: ProductUpdate,
    repository: ProductRepository = Depends(get_repository),
):
    """Update a product."""
    product = await repository.get_by_id(id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Filter out None values
    update_data = {k: v for k, v in data.dict().items() if v is not None}

    # Update product
    product.update(**update_data)

    return await repository.update(product)


@product_router.delete("/{id}", status_code=204)
async def delete_product(
    id: UUID, repository: ProductRepository = Depends(get_repository)
):
    """Delete a product."""
    deleted = await repository.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return None


@product_router.get("/search/{query}", response_model=List[ProductSearchResult])
async def search_products(
    query: str, engine: SemanticSearchEngine = Depends(lambda: app.state.search_engine)
):
    """
    Search for products.

    This demonstrates how to combine semantic search with domain entities.
    """
    # Search for products
    results = await engine.search(
        query=query, entity_type="product", limit=10, similarity_threshold=0.6
    )

    # Convert to response models
    search_results = []
    for result in results:
        # Get product ID from entity_id
        product_id = UUID(result["entity_id"])

        # Get product from repository
        product = await product_repository.get_by_id(product_id)
        if product:
            search_results.append(
                ProductSearchResult(
                    id=product.id,
                    name=product.name,
                    description=product.description,
                    price=product.price,
                    category=product.category,
                    similarity=result["similarity"],
                )
            )

    return search_results


# Add product router to app
app.include_router(product_router)


# Startup and shutdown events
@app.on_event("startup")
async def startup():
    """Initialize search engine on startup."""
    app.state.search_engine = await setup_search()
    logger.info("Semantic search engine initialized")


@app.on_event("shutdown")
async def shutdown():
    """Close search engine on shutdown."""
    if hasattr(app.state, "search_engine"):
        await app.state.search_engine.close()
        logger.info("Semantic search engine closed")


# Main function
def main():
    """Run the example application."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
