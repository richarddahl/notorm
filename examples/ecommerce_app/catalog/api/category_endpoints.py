"""
Category API endpoints for the catalog context.

This module defines the REST API endpoints for working with categories.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path

from uno.api.service_endpoint_adapter import DomainServiceAdapter
from uno.core.errors.result import Result
from uno.domain.unit_of_work import UnitOfWorkManager

from uno.examples.ecommerce_app.catalog.domain.entities import Category
from uno.examples.ecommerce_app.catalog.services.product_service import (
    CategoryService,
    CategoryQueryService,
    CategoryCreateCommand,
    CategoryUpdateCommand,
    CategoryListQuery,
)


# Create router
router = APIRouter(prefix="/api/catalog/categories", tags=["catalog"])


# DTO models for API responses
class CategoryResponse(CategoryCreateCommand):
    """Category response model."""

    id: str
    created_at: str
    updated_at: str | None = None


# Dependency functions
def get_category_service(uow_manager: UnitOfWorkManager = Depends()) -> CategoryService:
    """Get category service as a FastAPI dependency."""
    uow = uow_manager.create_uow()
    return CategoryService(uow=uow)


def get_category_query_service(
    uow_manager: UnitOfWorkManager = Depends(),
) -> CategoryQueryService:
    """Get category query service as a FastAPI dependency."""
    uow = uow_manager.create_uow()
    return CategoryQueryService(uow=uow)


# Adapter functions
def category_to_response(category: Category) -> CategoryResponse:
    """Convert a category entity to API response model."""
    return CategoryResponse(
        id=str(category.id),
        name=category.name,
        slug=category.slug,
        description=category.description,
        parent_id=category.parent_id,
        image_url=category.image_url,
        is_active=category.is_active,
        sort_order=category.sort_order,
        created_at=category.created_at.isoformat() if category.created_at else None,
        updated_at=category.updated_at.isoformat() if category.updated_at else None,
    )


def category_list_to_response(categories: list[Category]) -> list[CategoryResponse]:
    """Convert a list of category entities to API response model."""
    return [category_to_response(category) for category in categories]


# API endpoints
@router.get("/", response_model=list[CategoryResponse])
async def list_categories(
    parent_id: str | None = Query(None, description="Filter by parent category ID"),
    active_only: bool = Query(True, description="Only show active categories"),
    limit: Optional[int] = Query(
        100, description="Maximum number of categories to return"
    ),
    offset: Optional[int] = Query(0, description="Number of categories to skip"),
    query_service: CategoryQueryService = Depends(get_category_query_service),
):
    """
    List categories with filtering and pagination.

    Parameters:
    - parent_id: Filter by parent category ID (None for top-level categories)
    - active_only: Only show active categories
    - limit: Maximum number of categories to return
    - offset: Number of categories to skip
    """
    query = CategoryListQuery(
        parent_id=parent_id,
        is_active=True if active_only else None,
        limit=limit,
        offset=offset,
    )

    adapter = DomainServiceAdapter[CategoryListQuery, list[Category]](query_service)
    result: Result[list[Category]] = await adapter.execute(query)

    if result.is_failure:
        raise HTTPException(status_code=400, detail=result.error)

    return category_list_to_response(result.value)


@router.get("/hierarchy", response_model=list[CategoryResponse])
async def get_category_hierarchy(
    query_service: CategoryQueryService = Depends(get_category_query_service),
):
    """
    Get the category hierarchy.

    Returns all top-level categories (categories with no parent).
    """
    result: Result[list[Category]] = await query_service.get_hierarchy()

    if result.is_failure:
        raise HTTPException(status_code=400, detail=result.error)

    return category_list_to_response(result.value)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str = Path(..., description="The ID of the category"),
    query_service: CategoryQueryService = Depends(get_category_query_service),
):
    """
    Get detailed information for a specific category.

    Parameters:
    - category_id: The ID of the category
    """
    # Create query using standard repository methods
    from uno.examples.ecommerce_app.catalog.repository import CategoryRepository

    uow = query_service.uow
    category_repo = uow.get_repository(CategoryRepository)
    category_result = await category_repo.get_by_id(category_id)

    if category_result.is_failure:
        raise HTTPException(
            status_code=404, detail=f"Category not found: {category_result.error}"
        )

    return category_to_response(category_result.value)


@router.post("/", response_model=CategoryResponse, status_code=201)
async def create_category(
    command: CategoryCreateCommand,
    service: CategoryService = Depends(get_category_service),
):
    """
    Create a new category.

    The request body should contain all required category details.
    """
    adapter = DomainServiceAdapter[CategoryCreateCommand, Category](service)
    result: Result[Category] = await adapter.execute(command)

    if result.is_failure:
        raise HTTPException(status_code=400, detail=result.error)

    return category_to_response(result.value)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str = Path(..., description="The ID of the category"),
    command: CategoryUpdateCommand = None,
    service: CategoryService = Depends(get_category_service),
):
    """
    Update an existing category.

    Parameters:
    - category_id: The ID of the category to update

    The request body should contain the fields to update.
    """
    # Ensure category_id in path matches the one in the command
    if command.id != category_id:
        raise HTTPException(
            status_code=400,
            detail="Category ID in path does not match ID in request body",
        )

    adapter = DomainServiceAdapter[CategoryUpdateCommand, Category](service)
    result: Result[Category] = await adapter.execute(command)

    if result.is_failure:
        if "not found" in result.error:
            raise HTTPException(status_code=404, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)

    return category_to_response(result.value)
