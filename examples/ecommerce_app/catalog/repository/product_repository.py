"""
Product repository implementation for the catalog context.

This module provides implementations of the repository pattern for product and
category entities using SQLAlchemy.
"""

from typing import Optional, List, Dict, Any, cast
from decimal import Decimal
from sqlalchemy import select, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import BinaryExpression

from uno.core.base.respository import (
    SQLAlchemyAggregateRepository,
    SQLAlchemyRepository,
)
from uno.domain.specifications import Specification, SqlAlchemySpecification
from uno.domain.specifications.base import CompositeSpecification

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
from uno.examples.ecommerce_app.catalog.repository.models import (
    ProductModel,
    CategoryModel,
    ProductVariantModel,
    ProductImageModel,
    product_category_association,
)


class ProductRepository(SQLAlchemyAggregateRepository[Product, ProductModel]):
    """Repository for Product aggregate root."""

    def __init__(self, session: AsyncSession):
        """Initialize the product repository."""
        super().__init__(Product, session, ProductModel)

    def _to_entity(self, model: ProductModel) -> Product:
        """Convert a product model to a domain entity."""
        # Create the base product entity
        product = Product(
            id=model.id,
            name=model.name,
            slug=model.slug,
            description=model.description,
            sku=model.sku,
            price=Money(
                amount=Decimal(str(model.price_amount)), currency=model.price_currency
            ),
            status=ProductStatus(model.status),
            inventory=Inventory(
                quantity=model.inventory_quantity,
                reserved=model.inventory_reserved,
                backorderable=model.inventory_backorderable,
                restock_threshold=model.inventory_restock_threshold,
            ),
            category_ids=[category.id for category in model.categories],
            attributes=model.attributes,
            tags=model.tags,
            seo_title=model.seo_title,
            seo_description=model.seo_description,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )

        # Add weight if available
        if model.weight_value is not None and model.weight_unit is not None:
            product.weight = Weight(
                value=Decimal(str(model.weight_value)), unit=model.weight_unit
            )

        # Add dimensions if available
        if (
            model.dimensions_length is not None
            and model.dimensions_width is not None
            and model.dimensions_height is not None
        ):
            product.dimensions = Dimensions(
                length=Decimal(str(model.dimensions_length)),
                width=Decimal(str(model.dimensions_width)),
                height=Decimal(str(model.dimensions_height)),
                unit=model.dimensions_unit or "cm",
            )

        # Add variants
        for variant_model in model.variants:
            product.variants.append(
                ProductVariant(
                    id=variant_model.id,
                    product_id=variant_model.product_id,
                    sku=variant_model.sku,
                    name=variant_model.name,
                    price=Money(
                        amount=Decimal(str(variant_model.price_amount)),
                        currency=variant_model.price_currency,
                    ),
                    inventory=Inventory(
                        quantity=variant_model.inventory_quantity,
                        reserved=variant_model.inventory_reserved,
                        backorderable=variant_model.inventory_backorderable,
                        restock_threshold=variant_model.inventory_restock_threshold,
                    ),
                    attributes=variant_model.attributes,
                    is_active=variant_model.is_active,
                    created_at=variant_model.created_at,
                    updated_at=variant_model.updated_at,
                )
            )

        # Add images
        for image_model in model.images:
            product.images.append(
                ProductImage(
                    id=image_model.id,
                    product_id=image_model.product_id,
                    url=image_model.url,
                    alt_text=image_model.alt_text,
                    sort_order=image_model.sort_order,
                    is_primary=image_model.is_primary,
                    created_at=image_model.created_at,
                    updated_at=image_model.updated_at,
                )
            )

        return product

    def _to_model_data(self, entity: Product) -> dict[str, Any]:
        """Convert a product entity to model data."""
        # Extract basic data
        data = {
            "id": entity.id,
            "name": entity.name,
            "slug": entity.slug,
            "description": entity.description,
            "sku": entity.sku,
            "price_amount": float(entity.price.amount),
            "price_currency": entity.price.currency,
            "status": entity.status.value,
            "inventory_quantity": entity.inventory.quantity,
            "inventory_reserved": entity.inventory.reserved,
            "inventory_backorderable": entity.inventory.backorderable,
            "inventory_restock_threshold": entity.inventory.restock_threshold,
            "attributes": entity.attributes,
            "tags": entity.tags,
            "seo_title": entity.seo_title,
            "seo_description": entity.seo_description,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "version": entity.version,
        }

        # Add weight if available
        if entity.weight is not None:
            data["weight_value"] = float(entity.weight.value)
            data["weight_unit"] = entity.weight.unit

        # Add dimensions if available
        if entity.dimensions is not None:
            data["dimensions_length"] = float(entity.dimensions.length)
            data["dimensions_width"] = float(entity.dimensions.width)
            data["dimensions_height"] = float(entity.dimensions.height)
            data["dimensions_unit"] = entity.dimensions.unit

        return data

    async def add(self, entity: Product) -> Product:
        """Add a new product with its variants and images."""
        # Collect events first
        self._collect_events(entity)

        # Add the product
        product_data = self._to_model_data(entity)
        product_model = ProductModel(**product_data)
        self.session.add(product_model)

        # Associate categories
        if entity.category_ids:
            for category_id in entity.category_ids:
                stmt = select(CategoryModel).where(CategoryModel.id == category_id)
                result = await self.session.execute(stmt)
                category_model = result.scalars().first()
                if category_model:
                    product_model.categories.append(category_model)

        # Add variants
        for variant in entity.variants:
            variant_data = {
                "id": variant.id,
                "product_id": entity.id,
                "sku": variant.sku,
                "name": variant.name,
                "price_amount": float(variant.price.amount),
                "price_currency": variant.price.currency,
                "inventory_quantity": variant.inventory.quantity,
                "inventory_reserved": variant.inventory.reserved,
                "inventory_backorderable": variant.inventory.backorderable,
                "inventory_restock_threshold": variant.inventory.restock_threshold,
                "attributes": variant.attributes,
                "is_active": variant.is_active,
                "created_at": variant.created_at,
                "updated_at": variant.updated_at,
            }
            variant_model = ProductVariantModel(**variant_data)
            self.session.add(variant_model)

        # Add images
        for image in entity.images:
            image_data = {
                "id": image.id,
                "product_id": entity.id,
                "url": image.url,
                "alt_text": image.alt_text,
                "sort_order": image.sort_order,
                "is_primary": image.is_primary,
                "created_at": image.created_at,
                "updated_at": image.updated_at,
            }
            image_model = ProductImageModel(**image_data)
            self.session.add(image_model)

        await self.session.flush()

        # Get the complete product with relationships
        stmt = (
            select(ProductModel)
            .where(ProductModel.id == entity.id)
            .options(
                # Include relationships
            )
        )
        result = await self.session.execute(stmt)
        product_model = result.scalars().first()

        return self._to_entity(product_model)

    async def update(self, entity: Product) -> Product:
        """Update an existing product with its variants and images."""
        # Collect events first
        self._collect_events(entity)

        # Get the existing product
        stmt = select(ProductModel).where(ProductModel.id == entity.id)
        result = await self.session.execute(stmt)
        product_model = result.scalars().first()

        if not product_model:
            raise ValueError(f"Product with ID {entity.id} not found")

        # Check version for optimistic concurrency
        if product_model.version != entity.version - 1:
            raise ValueError(f"Concurrency conflict for product {entity.id}")

        # Update product fields
        product_data = self._to_model_data(entity)
        for key, value in product_data.items():
            setattr(product_model, key, value)

        # Update category associations
        # First, clear existing associations
        product_model.categories = []

        # Then add new associations
        if entity.category_ids:
            for category_id in entity.category_ids:
                stmt = select(CategoryModel).where(CategoryModel.id == category_id)
                result = await self.session.execute(stmt)
                category_model = result.scalars().first()
                if category_model:
                    product_model.categories.append(category_model)

        # Update variants
        # First, delete variants that are no longer present
        existing_variant_ids = [v.id for v in entity.variants]
        for variant_model in product_model.variants:
            if variant_model.id not in existing_variant_ids:
                await self.session.delete(variant_model)

        # Then, update or create variants
        for variant in entity.variants:
            # Check if variant exists
            variant_stmt = select(ProductVariantModel).where(
                ProductVariantModel.id == variant.id
            )
            variant_result = await self.session.execute(variant_stmt)
            variant_model = variant_result.scalars().first()

            variant_data = {
                "id": variant.id,
                "product_id": entity.id,
                "sku": variant.sku,
                "name": variant.name,
                "price_amount": float(variant.price.amount),
                "price_currency": variant.price.currency,
                "inventory_quantity": variant.inventory.quantity,
                "inventory_reserved": variant.inventory.reserved,
                "inventory_backorderable": variant.inventory.backorderable,
                "inventory_restock_threshold": variant.inventory.restock_threshold,
                "attributes": variant.attributes,
                "is_active": variant.is_active,
                "created_at": variant.created_at,
                "updated_at": variant.updated_at,
            }

            if variant_model:
                # Update existing variant
                for key, value in variant_data.items():
                    setattr(variant_model, key, value)
            else:
                # Create new variant
                variant_model = ProductVariantModel(**variant_data)
                self.session.add(variant_model)

        # Update images
        # First, delete images that are no longer present
        existing_image_ids = [img.id for img in entity.images]
        for image_model in product_model.images:
            if image_model.id not in existing_image_ids:
                await self.session.delete(image_model)

        # Then, update or create images
        for image in entity.images:
            # Check if image exists
            image_stmt = select(ProductImageModel).where(
                ProductImageModel.id == image.id
            )
            image_result = await self.session.execute(image_stmt)
            image_model = image_result.scalars().first()

            image_data = {
                "id": image.id,
                "product_id": entity.id,
                "url": image.url,
                "alt_text": image.alt_text,
                "sort_order": image.sort_order,
                "is_primary": image.is_primary,
                "created_at": image.created_at,
                "updated_at": image.updated_at,
            }

            if image_model:
                # Update existing image
                for key, value in image_data.items():
                    setattr(image_model, key, value)
            else:
                # Create new image
                image_model = ProductImageModel(**image_data)
                self.session.add(image_model)

        await self.session.flush()

        # Get the updated product with all relationships
        stmt = select(ProductModel).where(ProductModel.id == entity.id)
        result = await self.session.execute(stmt)
        updated_product_model = result.scalars().first()

        return self._to_entity(updated_product_model)

    def _specification_to_criteria(
        self, specification: Specification[Product]
    ) -> Optional[BinaryExpression]:
        """Convert a specification to SQLAlchemy criteria."""
        # Handle SqlAlchemySpecification
        if isinstance(specification, SqlAlchemySpecification):
            return specification.to_expression()

        # Handle composite specifications
        if isinstance(specification, CompositeSpecification):
            if hasattr(specification, "left") and hasattr(specification, "right"):
                left_expr = self._specification_to_criteria(specification.left)
                right_expr = self._specification_to_criteria(specification.right)

                if left_expr is None or right_expr is None:
                    return None

                if (
                    hasattr(specification, "__class__")
                    and specification.__class__.__name__ == "AndSpecification"
                ):
                    return and_(left_expr, right_expr)
                elif (
                    hasattr(specification, "__class__")
                    and specification.__class__.__name__ == "OrSpecification"
                ):
                    return or_(left_expr, right_expr)

            if hasattr(specification, "specification"):
                expr = self._specification_to_criteria(specification.specification)

                if expr is None:
                    return None

                if (
                    hasattr(specification, "__class__")
                    and specification.__class__.__name__ == "NotSpecification"
                ):
                    return not_(expr)

        # Unable to convert to criteria
        return None


class CategoryRepository(SQLAlchemyRepository[Category, CategoryModel]):
    """Repository for Category entity."""

    def __init__(self, session: AsyncSession):
        """Initialize the category repository."""
        super().__init__(Category, session, CategoryModel)

    def _to_entity(self, model: CategoryModel) -> Category:
        """Convert a category model to a domain entity."""
        return Category(
            id=model.id,
            name=model.name,
            slug=model.slug,
            description=model.description,
            parent_id=model.parent_id,
            image_url=model.image_url,
            is_active=model.is_active,
            sort_order=model.sort_order,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model_data(self, entity: Category) -> dict[str, Any]:
        """Convert a category entity to model data."""
        return {
            "id": entity.id,
            "name": entity.name,
            "slug": entity.slug,
            "description": entity.description,
            "parent_id": entity.parent_id,
            "image_url": entity.image_url,
            "is_active": entity.is_active,
            "sort_order": entity.sort_order,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    def _specification_to_criteria(
        self, specification: Specification[Category]
    ) -> Optional[BinaryExpression]:
        """Convert a specification to SQLAlchemy criteria."""
        # Handle SqlAlchemySpecification
        if isinstance(specification, SqlAlchemySpecification):
            return specification.to_expression()

        # Handle composite specifications
        if isinstance(specification, CompositeSpecification):
            if hasattr(specification, "left") and hasattr(specification, "right"):
                left_expr = self._specification_to_criteria(specification.left)
                right_expr = self._specification_to_criteria(specification.right)

                if left_expr is None or right_expr is None:
                    return None

                if (
                    hasattr(specification, "__class__")
                    and specification.__class__.__name__ == "AndSpecification"
                ):
                    return and_(left_expr, right_expr)
                elif (
                    hasattr(specification, "__class__")
                    and specification.__class__.__name__ == "OrSpecification"
                ):
                    return or_(left_expr, right_expr)

            if hasattr(specification, "specification"):
                expr = self._specification_to_criteria(specification.specification)

                if expr is None:
                    return None

                if (
                    hasattr(specification, "__class__")
                    and specification.__class__.__name__ == "NotSpecification"
                ):
                    return not_(expr)

        # Unable to convert to criteria
        return None
