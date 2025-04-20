"""
Category repository implementation for the catalog context.

This module provides the repository implementation for category entities.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import BinaryExpression

from uno.core.base.respository import SQLAlchemyRepository
from uno.domain.specifications import Specification, SqlAlchemySpecification
from uno.domain.specifications.base import CompositeSpecification

from uno.examples.ecommerce_app.catalog.domain.entities import Category
from uno.examples.ecommerce_app.catalog.repository.models import CategoryModel


class CategoryRepository(SQLAlchemyRepository[Category, CategoryModel]):
    """Repository for Category entity."""

    def __init__(self, session: AsyncSession):
        """Initialize the category repository."""
        super().__init__(Category, session, CategoryModel)

    async def add(self, entity: Category) -> Category:
        # Gather all existing slugs for uniqueness check
        stmt = select(CategoryModel.slug)
        result = await self.session.execute(stmt)
        existing_slugs = set(row[0] for row in result.all() if row[0] != entity.slug)

        async def parent_lookup(parent_id: str) -> Category | None:
            stmt = select(CategoryModel).where(CategoryModel.id == parent_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

        entity.check_invariants(
            existing_slugs=existing_slugs, parent_lookup=parent_lookup
        )
        return await super().add(entity)

    async def update(self, entity: Category) -> Category:
        # Gather all existing slugs except this entity's slug
        stmt = select(CategoryModel.slug, CategoryModel.id)
        result = await self.session.execute(stmt)
        existing_slugs = set(row[0] for row in result.all() if row[1] != entity.id)

        async def parent_lookup(parent_id: str) -> Category | None:
            stmt = select(CategoryModel).where(CategoryModel.id == parent_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

        entity.check_invariants(
            existing_slugs=existing_slugs, parent_lookup=parent_lookup
        )
        return await super().update(entity)

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

    def _to_model_data(self, entity: Category) -> Dict[str, Any]:
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

    async def get_hierarchy(self) -> list[Category]:
        """
        Get the category hierarchy.

        Returns:
            List of top-level categories (categories with no parent)
        """
        stmt = select(CategoryModel).where(CategoryModel.parent_id.is_(None))
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_children(self, parent_id: str) -> list[Category]:
        """
        Get child categories for a parent category.

        Args:
            parent_id: ID of the parent category

        Returns:
            List of child categories
        """
        stmt = select(CategoryModel).where(CategoryModel.parent_id == parent_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

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
