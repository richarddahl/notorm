"""
Catalog bounded context for the e-commerce application.

This module provides functionality for managing products and categories in the catalog.
It demonstrates domain-driven design principles with a clear separation between domain,
repository, services, and API layers.
"""

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.events import get_event_bus
from uno.domain.unified_services import get_service_factory
from uno.domain.unit_of_work import UnitOfWorkManager

from uno.examples.ecommerce_app.catalog.domain.entities import Product, Category
from uno.examples.ecommerce_app.catalog.repository import (
    ProductRepository,
    CategoryRepository,
)
from uno.examples.ecommerce_app.catalog.api import product_router, category_router


def setup_catalog(app: FastAPI) -> None:
    """
    Set up the catalog context in the application.

    This function:
    1. Registers repositories with the service factory
    2. Registers FastAPI routers for the API endpoints

    Args:
        app: The FastAPI application
    """
    # Get the service factory
    service_factory = get_service_factory()

    # Register entity types with their repositories
    # This allows the service factory to create entity services
    async def register_repositories(session: AsyncSession):
        # Create repositories with the provided session
        product_repo = ProductRepository(session)
        category_repo = CategoryRepository(session)

        # Register repositories with the service factory
        service_factory.register_entity_type(Product, product_repo)
        service_factory.register_entity_type(Category, category_repo)

    # Add the repository registration to the unit of work manager
    uow_manager = UnitOfWorkManager.get_instance()
    uow_manager.register_repository_factory(register_repositories)

    # Register API routers
    app.include_router(product_router)
    app.include_router(category_router)

    # Subscribe to events (for handling domain events)
    event_bus = get_event_bus()
    # Example: event_bus.subscribe("product_created", handle_product_created)

    # Log successful setup
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Catalog context set up successfully")
