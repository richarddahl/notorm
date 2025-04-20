"""
Domain services for the catalog context.

This module provides services for working with products and categories in the catalog context.
These services encapsulate business logic and provide high-level operations for manipulating
the domain model.
"""

import logging
from typing import List, Optional, Dict, Any, Type, Union
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, UTC
from pydantic import BaseModel, Field, validator, field_validator

from uno.core.errors.result import Result
from uno.domain.unified_services import DomainService, ReadOnlyDomainService
from uno.domain.unit_of_work import UnitOfWork
from uno.domain.specifications import (
    AndSpecification,
    OrSpecification,
    NotSpecification,
)

from uno.examples.ecommerce_app.catalog.domain.entities import (
    Product,
    Category,
    ProductVariant,
    ProductImage,
)
from uno.examples.ecommerce_app.catalog.domain.value_objects import (
    ProductStatus,
    Dimensions,
    Weight,
    Inventory,
)
from uno.examples.ecommerce_app.shared.value_objects import Money
from uno.examples.ecommerce_app.catalog.repository.specifications import (
    ProductByStatusSpecification,
    ProductByCategorySpecification,
    ProductByPriceRangeSpecification,
    ProductByNameSpecification,
)


# ----- Command/Query Data Transfer Objects -----


class ProductVariantDTO(BaseModel):
    """Data transfer object for product variant."""

    id: str | None = None
    sku: str
    name: str
    price_amount: Decimal
    price_currency: str = "USD"
    inventory_quantity: int = 0
    inventory_reserved: int = 0
    inventory_backorderable: bool = False
    inventory_restock_threshold: int | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ProductImageDTO(BaseModel):
    """Data transfer object for product image."""

    id: str | None = None
    url: str
    alt_text: str | None = None
    sort_order: int = 0
    is_primary: bool = False


class ProductDimensionsDTO(BaseModel):
    """Data transfer object for product dimensions."""

    length: Decimal
    width: Decimal
    height: Decimal
    unit: str = "cm"

    @field_validator("length", "width", "height")
    @classmethod
    def validate_dimensions(cls, v: Decimal) -> Decimal:
        """Validate dimensions are positive."""
        if v <= 0:
            raise ValueError("Dimensions must be positive")
        return v


class ProductWeightDTO(BaseModel):
    """Data transfer object for product weight."""

    value: Decimal
    unit: str = "kg"

    @field_validator("value")
    @classmethod
    def validate_weight(cls, v: Decimal) -> Decimal:
        """Validate weight is positive."""
        if v < 0:
            raise ValueError("Weight cannot be negative")
        return v


class ProductCreateCommand(BaseModel):
    """Command for creating a new product."""

    name: str
    slug: str
    description: str | None = None
    sku: str
    price_amount: Decimal
    price_currency: str = "USD"
    status: ProductStatus = ProductStatus.DRAFT

    # Inventory
    inventory_quantity: int = 0
    inventory_reserved: int = 0
    inventory_backorderable: bool = False
    inventory_restock_threshold: int | None = None

    # Physical attributes
    weight: Optional[ProductWeightDTO] = None
    dimensions: Optional[ProductDimensionsDTO] = None

    # Relationships
    category_ids: list[str] = Field(default_factory=list)

    # Attributes and metadata
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    seo_title: str | None = None
    seo_description: str | None = None

    # Child entities
    variants: list[ProductVariantDTO] = Field(default_factory=list)
    images: list[ProductImageDTO] = Field(default_factory=list)


class ProductUpdateCommand(BaseModel):
    """Command for updating an existing product."""

    id: str
    version: int
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    sku: str | None = None
    price_amount: Optional[Decimal] = None
    price_currency: str | None = None
    status: Optional[ProductStatus] = None

    # Inventory
    inventory_quantity: int | None = None
    inventory_reserved: int | None = None
    inventory_backorderable: Optional[bool] = None
    inventory_restock_threshold: int | None = None

    # Physical attributes
    weight: Optional[ProductWeightDTO] = None
    dimensions: Optional[ProductDimensionsDTO] = None

    # Relationships
    category_ids: list[str] | None = None

    # Attributes and metadata
    attributes: dict[str, Any] | None = None
    tags: list[str] | None = None
    seo_title: str | None = None
    seo_description: str | None = None

    # Child entities
    variants: Optional[list[ProductVariantDTO]] = None
    images: Optional[list[ProductImageDTO]] = None


class ProductListQuery(BaseModel):
    """Query for listing products."""

    status: str | None = None
    category_id: str | None = None
    search_term: str | None = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    limit: int | None = None
    offset: int | None = None
    sort_by: str | None = None
    sort_direction: str | None = "asc"


class ProductDetailQuery(BaseModel):
    """Query for retrieving product details."""

    id: str


class CategoryCreateCommand(BaseModel):
    """Command for creating a new category."""

    name: str
    slug: str
    description: str | None = None
    parent_id: str | None = None
    image_url: str | None = None
    is_active: bool = True
    sort_order: int = 0


class CategoryUpdateCommand(BaseModel):
    """Command for updating an existing category."""

    id: str
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    parent_id: str | None = None
    image_url: str | None = None
    is_active: Optional[bool] = None
    sort_order: int | None = None


class CategoryListQuery(BaseModel):
    """Query for listing categories."""

    parent_id: str | None = None
    is_active: Optional[bool] = None
    limit: int | None = None
    offset: int | None = None


# ----- Domain Services -----


class ProductService(
    DomainService[
        Union[ProductCreateCommand, ProductUpdateCommand], Product, UnitOfWork
    ]
):
    """Service for working with products."""

    async def _execute_internal(
        self, input_data: Union[ProductCreateCommand, ProductUpdateCommand]
    ) -> Result[Product]:
        """Execute the product service command."""
        if isinstance(input_data, ProductCreateCommand):
            return await self._create_product(input_data)
        elif isinstance(input_data, ProductUpdateCommand):
            return await self._update_product(input_data)

        return Failure("Unsupported command type")

    async def _create_product(self, command: ProductCreateCommand) -> Result[Product]:
        """Create a new product."""
        try:
            # Create product domain entity
            product = Product(
                id=str(uuid4()),
                name=command.name,
                slug=command.slug,
                description=command.description,
                sku=command.sku,
                price=Money(
                    amount=command.price_amount, currency=command.price_currency
                ),
                status=command.status,
                inventory=Inventory(
                    quantity=command.inventory_quantity,
                    reserved=command.inventory_reserved,
                    backorderable=command.inventory_backorderable,
                    restock_threshold=command.inventory_restock_threshold,
                ),
                category_ids=command.category_ids,
                attributes=command.attributes,
                tags=command.tags,
                seo_title=command.seo_title,
                seo_description=command.seo_description,
            )

            # Add weight if provided
            if command.weight:
                product.weight = Weight(
                    value=command.weight.value, unit=command.weight.unit
                )

            # Add dimensions if provided
            if command.dimensions:
                product.dimensions = Dimensions(
                    length=command.dimensions.length,
                    width=command.dimensions.width,
                    height=command.dimensions.height,
                    unit=command.dimensions.unit,
                )

            # Add variants
            for variant_dto in command.variants:
                variant = ProductVariant(
                    id=variant_dto.id or str(uuid4()),
                    product_id=product.id,
                    sku=variant_dto.sku,
                    name=variant_dto.name,
                    price=Money(
                        amount=variant_dto.price_amount,
                        currency=variant_dto.price_currency,
                    ),
                    inventory=Inventory(
                        quantity=variant_dto.inventory_quantity,
                        reserved=variant_dto.inventory_reserved,
                        backorderable=variant_dto.inventory_backorderable,
                        restock_threshold=variant_dto.inventory_restock_threshold,
                    ),
                    attributes=variant_dto.attributes,
                    is_active=variant_dto.is_active,
                )
                product.add_variant(variant)

            # Add images
            for image_dto in command.images:
                image = ProductImage(
                    id=image_dto.id or str(uuid4()),
                    product_id=product.id,
                    url=image_dto.url,
                    alt_text=image_dto.alt_text,
                    sort_order=image_dto.sort_order,
                    is_primary=image_dto.is_primary,
                )
                product.add_image(image)

            # Check invariants
            product.check_invariants()

            # Persist the product
            from uno.examples.ecommerce_app.catalog.repository import ProductRepository

            product_repo = self.uow.get_repository(ProductRepository)
            saved_product = await product_repo.add(product)

            return Success(saved_product)
        except Exception as e:
            self.logger.error(f"Error creating product: {str(e)}", exc_info=True)
            return Failure(str(e))

    async def _update_product(self, command: ProductUpdateCommand) -> Result[Product]:
        """Update an existing product."""
        try:
            # Get the product
            from uno.examples.ecommerce_app.catalog.repository import ProductRepository

            product_repo = self.uow.get_repository(ProductRepository)
            product_result = await product_repo.get_by_id(command.id)

            if product_result.is_failure:
                return Failure(f"Product with ID {command.id} not found")

            product = product_result.value

            # Check version for optimistic concurrency
            if product.version != command.version:
                return Failure(
                    f"Concurrency conflict: expected version {command.version}, found {product.version}"
                )

            # Update fields if provided
            if command.name is not None:
                product.name = command.name

            if command.slug is not None:
                product.slug = command.slug

            if command.description is not None:
                product.description = command.description

            if command.sku is not None:
                product.sku = command.sku

            if command.price_amount is not None and command.price_currency is not None:
                product.update_price(
                    Money(amount=command.price_amount, currency=command.price_currency)
                )
            elif command.price_amount is not None:
                product.update_price(
                    Money(amount=command.price_amount, currency=product.price.currency)
                )
            elif command.price_currency is not None:
                product.update_price(
                    Money(amount=product.price.amount, currency=command.price_currency)
                )

            if command.status is not None:
                if command.status == ProductStatus.ACTIVE:
                    product.activate()
                elif command.status == ProductStatus.INACTIVE:
                    product.deactivate()
                else:
                    product.status = command.status
                    product.update()

            # Update inventory if any inventory fields are provided
            if any(
                [
                    command.inventory_quantity is not None,
                    command.inventory_reserved is not None,
                    command.inventory_backorderable is not None,
                    command.inventory_restock_threshold is not None,
                ]
            ):
                new_inventory = Inventory(
                    quantity=(
                        command.inventory_quantity
                        if command.inventory_quantity is not None
                        else product.inventory.quantity
                    ),
                    reserved=(
                        command.inventory_reserved
                        if command.inventory_reserved is not None
                        else product.inventory.reserved
                    ),
                    backorderable=(
                        command.inventory_backorderable
                        if command.inventory_backorderable is not None
                        else product.inventory.backorderable
                    ),
                    restock_threshold=(
                        command.inventory_restock_threshold
                        if command.inventory_restock_threshold is not None
                        else product.inventory.restock_threshold
                    ),
                )
                product.update_inventory(new_inventory)

            # Update weight
            if command.weight is not None:
                product.weight = Weight(
                    value=command.weight.value, unit=command.weight.unit
                )

            # Update dimensions
            if command.dimensions is not None:
                product.dimensions = Dimensions(
                    length=command.dimensions.length,
                    width=command.dimensions.width,
                    height=command.dimensions.height,
                    unit=command.dimensions.unit,
                )

            # Update category relationships
            if command.category_ids is not None:
                # First, remove from all current categories
                for cat_id in list(
                    product.category_ids
                ):  # Create a copy to avoid modifying during iteration
                    product.remove_from_category(cat_id)

                # Then add to new categories
                for cat_id in command.category_ids:
                    product.add_to_category(cat_id)

            # Update attributes and metadata
            if command.attributes is not None:
                product.attributes = command.attributes
                product.update()

            if command.tags is not None:
                product.tags = command.tags
                product.update()

            if command.seo_title is not None:
                product.seo_title = command.seo_title
                product.update()

            if command.seo_description is not None:
                product.seo_description = command.seo_description
                product.update()

            # Update variants if provided
            if command.variants is not None:
                # Clear existing variants
                product.variants.clear()

                # Add new variants
                for variant_dto in command.variants:
                    variant = ProductVariant(
                        id=variant_dto.id or str(uuid4()),
                        product_id=product.id,
                        sku=variant_dto.sku,
                        name=variant_dto.name,
                        price=Money(
                            amount=variant_dto.price_amount,
                            currency=variant_dto.price_currency,
                        ),
                        inventory=Inventory(
                            quantity=variant_dto.inventory_quantity,
                            reserved=variant_dto.inventory_reserved,
                            backorderable=variant_dto.inventory_backorderable,
                            restock_threshold=variant_dto.inventory_restock_threshold,
                        ),
                        attributes=variant_dto.attributes,
                        is_active=variant_dto.is_active,
                    )
                    product.add_variant(variant)

            # Update images if provided
            if command.images is not None:
                # Clear existing images
                product.images.clear()

                # Add new images
                for image_dto in command.images:
                    image = ProductImage(
                        id=image_dto.id or str(uuid4()),
                        product_id=product.id,
                        url=image_dto.url,
                        alt_text=image_dto.alt_text,
                        sort_order=image_dto.sort_order,
                        is_primary=image_dto.is_primary,
                    )
                    product.add_image(image)

            # Check invariants
            product.check_invariants()

            # Persist the updated product
            updated_product = await product_repo.update(product)

            return Success(updated_product)
        except Exception as e:
            self.logger.error(f"Error updating product: {str(e)}", exc_info=True)
            return Failure(str(e))


class ProductQueryService(
    ReadOnlyDomainService[
        Union[ProductListQuery, ProductDetailQuery],
        Union[list[Product], Product],
        UnitOfWork,
    ]
):
    """Service for querying products."""

    async def _execute_internal(
        self, input_data: Union[ProductListQuery, ProductDetailQuery]
    ) -> Result[Union[list[Product], Product]]:
        """Execute the product query."""
        if isinstance(input_data, ProductListQuery):
            return await self._list_products(input_data)
        elif isinstance(input_data, ProductDetailQuery):
            return await self._get_product_detail(input_data)

        return Failure("Unsupported query type")

    async def _list_products(self, query: ProductListQuery) -> Result[list[Product]]:
        """List products based on query criteria."""
        try:
            from uno.examples.ecommerce_app.catalog.repository import ProductRepository

            product_repo = self.uow.get_repository(ProductRepository)

            # Build specifications based on query parameters
            specifications = []

            if query.status:
                specifications.append(ProductByStatusSpecification(query.status))

            if query.category_id:
                specifications.append(ProductByCategorySpecification(query.category_id))

            if query.min_price is not None or query.max_price is not None:
                specifications.append(
                    ProductByPriceRangeSpecification(
                        min_price=query.min_price, max_price=query.max_price
                    )
                )

            if query.search_term:
                specifications.append(ProductByNameSpecification(query.search_term))

            # Combine specifications with AND logic
            combined_spec = None
            for spec in specifications:
                if combined_spec is None:
                    combined_spec = spec
                else:
                    combined_spec = AndSpecification(combined_spec, spec)

            # Execute query
            if combined_spec:
                products = await product_repo.find(combined_spec)
            else:
                # If no specifications, use list with pagination
                order_by = None
                if query.sort_by:
                    prefix = "-" if query.sort_direction == "desc" else ""
                    order_by = [f"{prefix}{query.sort_by}"]

                products = await product_repo.list(
                    filters={},
                    order_by=order_by,
                    limit=query.limit,
                    offset=query.offset,
                )

            return Success(products)
        except Exception as e:
            self.logger.error(f"Error listing products: {str(e)}", exc_info=True)
            return Failure(str(e))

    async def _get_product_detail(self, query: ProductDetailQuery) -> Result[Product]:
        """Get detailed information for a specific product."""
        try:
            from uno.examples.ecommerce_app.catalog.repository import ProductRepository

            product_repo = self.uow.get_repository(ProductRepository)

            product_result = await product_repo.get_by_id(query.id)
            if product_result.is_failure:
                return Failure(f"Product with ID {query.id} not found")

            return Success(product_result.value)
        except Exception as e:
            self.logger.error(f"Error getting product detail: {str(e)}", exc_info=True)
            return Failure(str(e))


class CategoryService(
    DomainService[
        Union[CategoryCreateCommand, CategoryUpdateCommand], Category, UnitOfWork
    ]
):
    """Service for working with categories."""

    async def _execute_internal(
        self, input_data: Union[CategoryCreateCommand, CategoryUpdateCommand]
    ) -> Result[Category]:
        """Execute the category service command."""
        if isinstance(input_data, CategoryCreateCommand):
            return await self._create_category(input_data)
        elif isinstance(input_data, CategoryUpdateCommand):
            return await self._update_category(input_data)

        return Failure("Unsupported command type")

    async def _create_category(
        self, command: CategoryCreateCommand
    ) -> Result[Category]:
        """Create a new category."""
        try:
            # Create category domain entity
            category = Category(
                id=str(uuid4()),
                name=command.name,
                slug=command.slug,
                description=command.description,
                parent_id=command.parent_id,
                image_url=command.image_url,
                is_active=command.is_active,
                sort_order=command.sort_order,
            )

            # Persist the category
            from uno.examples.ecommerce_app.catalog.repository import CategoryRepository

            category_repo = self.uow.get_repository(CategoryRepository)
            saved_category = await category_repo.add(category)

            return Success(saved_category)
        except Exception as e:
            self.logger.error(f"Error creating category: {str(e)}", exc_info=True)
            return Failure(str(e))

    async def _update_category(
        self, command: CategoryUpdateCommand
    ) -> Result[Category]:
        """Update an existing category."""
        try:
            # Get the category
            from uno.examples.ecommerce_app.catalog.repository import CategoryRepository

            category_repo = self.uow.get_repository(CategoryRepository)
            category_result = await category_repo.get_by_id(command.id)

            if category_result.is_failure:
                return Failure(f"Category with ID {command.id} not found")

            category = category_result.value

            # Update fields if provided
            if command.name is not None:
                category.name = command.name
                category.update()

            if command.slug is not None:
                category.slug = command.slug
                category.update()

            if command.description is not None:
                category.description = command.description
                category.update()

            if command.parent_id is not None:
                category.parent_id = command.parent_id
                category.update()

            if command.image_url is not None:
                category.image_url = command.image_url
                category.update()

            if command.is_active is not None:
                category.is_active = command.is_active
                category.update()

            if command.sort_order is not None:
                category.sort_order = command.sort_order
                category.update()

            # Persist the updated category
            updated_category = await category_repo.update(category)

            return Success(updated_category)
        except Exception as e:
            self.logger.error(f"Error updating category: {str(e)}", exc_info=True)
            return Failure(str(e))


class CategoryQueryService(
    ReadOnlyDomainService[CategoryListQuery, list[Category], UnitOfWork]
):
    """Service for querying categories."""

    async def _execute_internal(
        self, input_data: CategoryListQuery
    ) -> Result[list[Category]]:
        """Execute the category query."""
        try:
            from uno.examples.ecommerce_app.catalog.repository import CategoryRepository

            category_repo = self.uow.get_repository(CategoryRepository)

            filters = {}

            if input_data.parent_id is not None:
                filters["parent_id"] = input_data.parent_id

            if input_data.is_active is not None:
                filters["is_active"] = input_data.is_active

            categories = await category_repo.list(
                filters=filters,
                limit=input_data.limit,
                offset=input_data.offset,
                order_by=["sort_order", "name"],
            )

            return Success(categories)
        except Exception as e:
            self.logger.error(f"Error listing categories: {str(e)}", exc_info=True)
            return Failure(str(e))

    async def get_hierarchy(self) -> Result[list[Category]]:
        """Get the category hierarchy."""
        try:
            from uno.examples.ecommerce_app.catalog.repository import CategoryRepository

            category_repo = self.uow.get_repository(CategoryRepository)

            root_categories = await category_repo.get_hierarchy()
            return Success(root_categories)
        except Exception as e:
            self.logger.error(
                f"Error getting category hierarchy: {str(e)}", exc_info=True
            )
            return Failure(str(e))
