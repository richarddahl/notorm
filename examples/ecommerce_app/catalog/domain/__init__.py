"""Domain layer for the catalog context."""

from uno.examples.ecommerce_app.catalog.domain.entities import (
    Product, 
    Category, 
    ProductVariant, 
    ProductImage
)

from uno.examples.ecommerce_app.catalog.domain.events import (
    ProductCreatedEvent,
    ProductUpdatedEvent,
    ProductPriceChangedEvent,
    ProductInventoryUpdatedEvent,
    CategoryCreatedEvent
)

from uno.examples.ecommerce_app.catalog.domain.value_objects import (
    ProductStatus,
    Dimensions,
    Weight,
    Inventory
)