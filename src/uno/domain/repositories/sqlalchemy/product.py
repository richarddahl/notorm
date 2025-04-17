"""
Product repository implementation for SQLAlchemy with enhanced specifications.

This module demonstrates the use of enhanced specifications for common query patterns
in a domain-specific repository.
"""

from typing import List, Optional, Callable, Dict, Any, Type, cast
from datetime import datetime, timezone, timedelta
import logging
import json

from sqlalchemy import select, func, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession

from uno.domain.repository_results import FindResult
from uno.domain.specifications import (
    AttributeSpecification, AndSpecification, OrSpecification, NotSpecification,
    RangeSpecification, ComparableSpecification, TextMatchSpecification,
    DateRangeSpecification, RelativeDateSpecification, InListSpecification,
    NotInListSpecification, NullSpecification, NotNullSpecification,
    specification_factory, enhance_specification_factory
)
from uno.domain.repositories.sqlalchemy.base import SQLAlchemyRepository
from uno.domain.models import Product, ProductCategory
from uno.model import UnoModel


class ProductModel(UnoModel):
    """SQLAlchemy model for products."""
    
    __tablename__ = "products"
    
    id = UnoModel.Column(UnoModel.String, primary_key=True)
    name = UnoModel.Column(UnoModel.String, nullable=False)
    description = UnoModel.Column(UnoModel.Text, nullable=True)
    price = UnoModel.Column(UnoModel.Numeric(10, 2), nullable=False)
    category = UnoModel.Column(UnoModel.String, nullable=False)
    sku = UnoModel.Column(UnoModel.String, unique=True, nullable=False)
    in_stock = UnoModel.Column(UnoModel.Boolean, default=True)
    stock_quantity = UnoModel.Column(UnoModel.Integer, default=0)
    tags = UnoModel.Column(UnoModel.ARRAY(UnoModel.String), default=list)
    metadata = UnoModel.Column(UnoModel.JSON, nullable=True)
    created_at = UnoModel.Column(UnoModel.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = UnoModel.Column(UnoModel.DateTime(timezone=True), nullable=True)


# Create a product-specific specification factory
ProductSpec = specification_factory(Product)
# Enhance it with additional methods
EnhancedProductSpec = enhance_specification_factory(ProductSpec)


class ProductRepository(SQLAlchemyRepository[Product, ProductModel]):
    """Repository for Product entities with enhanced specifications."""
    
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the product repository.
        
        Args:
            session_factory: Factory function for creating SQLAlchemy sessions
            logger: Optional logger for diagnostic output
        """
        super().__init__(
            entity_type=Product,
            model_class=ProductModel,
            session_factory=session_factory,
            logger=logger or logging.getLogger(__name__)
        )
    
    async def find_by_category(self, category: ProductCategory) -> List[Product]:
        """
        Find products by category.
        
        Args:
            category: The category to search for
            
        Returns:
            List of products in the specified category
        """
        spec = EnhancedProductSpec.eq("category", category.value)
        return await self.find(spec)
    
    async def find_by_sku(self, sku: str) -> Optional[Product]:
        """
        Find a product by SKU.
        
        Args:
            sku: The SKU to search for
            
        Returns:
            The product if found, None otherwise
        """
        spec = EnhancedProductSpec.eq("sku", sku)
        return await self.find_one(spec)
    
    async def find_in_stock(self) -> List[Product]:
        """
        Find all in-stock products.
        
        Returns:
            List of in-stock products
        """
        spec = EnhancedProductSpec.eq("in_stock", True)
        return await self.find(spec)
    
    async def find_in_stock_by_category(self, category: ProductCategory) -> List[Product]:
        """
        Find in-stock products by category.
        
        Args:
            category: The category to search for
            
        Returns:
            List of in-stock products in the specified category
        """
        spec = EnhancedProductSpec.eq("in_stock", True).and_(
               EnhancedProductSpec.eq("category", category.value))
        return await self.find(spec)
    
    async def find_by_price_range(self, min_price: float, max_price: float) -> List[Product]:
        """
        Find products in a price range.
        
        Args:
            min_price: The minimum price
            max_price: The maximum price
            
        Returns:
            List of products in the price range
        """
        # Use the enhanced range specification
        spec = EnhancedProductSpec.range("price", min_price, max_price)
        return await self.find(spec)
    
    async def find_by_name_pattern(self, pattern: str, case_sensitive: bool = False) -> List[Product]:
        """
        Find products by name pattern.
        
        Args:
            pattern: The pattern to search for
            case_sensitive: Whether the search is case-sensitive
            
        Returns:
            List of products matching the pattern
        """
        spec = EnhancedProductSpec.contains("name", pattern, case_sensitive)
        return await self.find(spec)
    
    async def find_by_tags(self, tags: List[str]) -> List[Product]:
        """
        Find products with specific tags.
        
        Args:
            tags: The tags to search for
            
        Returns:
            List of products with the specified tags
        """
        # Use collection contains for array fields
        tag_specs = [EnhancedProductSpec.collection_contains("tags", tag) for tag in tags]
        
        # Combine with OR to find products with any of the tags
        spec = tag_specs[0]
        for tag_spec in tag_specs[1:]:
            spec = spec.or_(tag_spec)
            
        return await self.find(spec)
    
    async def find_recently_added(self, days: int = 30) -> List[Product]:
        """
        Find products added within the specified number of days.
        
        Args:
            days: The number of days to look back
            
        Returns:
            List of products added within the time period
        """
        spec = EnhancedProductSpec.created_within_days("created_at", days)
        return await self.find(spec)
    
    async def find_with_specific_metadata(self, supplier_id: str) -> List[Product]:
        """
        Find products with a specific supplier in metadata.
        
        Args:
            supplier_id: The supplier ID to search for
            
        Returns:
            List of products with the specified supplier
        """
        # Use JSON path for querying metadata fields
        spec = EnhancedProductSpec.json_path("metadata", ["supplier", "id"], supplier_id)
        return await self.find(spec)
    
    async def find_products_on_sale(self) -> List[Product]:
        """
        Find products that are on sale according to metadata.
        
        Returns:
            List of products on sale
        """
        spec = EnhancedProductSpec.json_path("metadata", ["on_sale"], True)
        return await self.find(spec)
    
    async def find_low_stock(self, threshold: int = 10) -> List[Product]:
        """
        Find products with low stock.
        
        Args:
            threshold: The stock threshold
            
        Returns:
            List of products with stock below the threshold
        """
        # Use the compare specification with lt operator
        spec = EnhancedProductSpec.lt("stock_quantity", threshold).and_(
               EnhancedProductSpec.eq("in_stock", True))
        return await self.find(spec)
    
    async def find_products_not_in_categories(self, excluded_categories: List[ProductCategory]) -> List[Product]:
        """
        Find products not in certain categories.
        
        Args:
            excluded_categories: The categories to exclude
            
        Returns:
            List of products not in the specified categories
        """
        # Convert enum values to strings
        category_values = [category.value for category in excluded_categories]
        
        # Use not_in_list specification
        spec = EnhancedProductSpec.not_in_list("category", category_values)
        return await self.find(spec)
    
    async def find_products_without_description(self) -> List[Product]:
        """
        Find products that don't have a description.
        
        Returns:
            List of products without a description
        """
        # Use is_null specification
        spec = EnhancedProductSpec.is_null("description")
        return await self.find(spec)
    
    async def find_products_with_text_in_description(self, text: str) -> List[Product]:
        """
        Find products with specific text in their description.
        
        Args:
            text: The text to search for
            
        Returns:
            List of products with the text in their description
        """
        # Use text_match specification for full text search
        spec = EnhancedProductSpec.contains("description", text)
        return await self.find(spec)
    
    async def search_products(
        self, 
        keywords: Optional[str] = None,
        category: Optional[ProductCategory] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[Product]:
        """
        Search products with multiple criteria.
        
        This method demonstrates composing complex queries with enhanced specifications.
        
        Args:
            keywords: Optional keywords to search in name and description
            category: Optional category to filter by
            min_price: Optional minimum price
            max_price: Optional maximum price
            in_stock_only: Whether to return only in-stock products
            tags: Optional list of tags to filter by
            
        Returns:
            List of products matching the criteria
        """
        # Build a composite specification based on the provided criteria
        specs = []
        
        if keywords:
            # Search in both name and description
            name_spec = EnhancedProductSpec.contains("name", keywords)
            desc_spec = EnhancedProductSpec.contains("description", keywords)
            specs.append(name_spec.or_(desc_spec))
        
        if category:
            specs.append(EnhancedProductSpec.eq("category", category.value))
        
        if min_price is not None and max_price is not None:
            specs.append(EnhancedProductSpec.range("price", min_price, max_price))
        elif min_price is not None:
            specs.append(EnhancedProductSpec.gte("price", min_price))
        elif max_price is not None:
            specs.append(EnhancedProductSpec.lte("price", max_price))
        
        if in_stock_only:
            specs.append(EnhancedProductSpec.eq("in_stock", True))
        
        if tags:
            tag_specs = [EnhancedProductSpec.collection_contains("tags", tag) for tag in tags]
            combined_tag_spec = tag_specs[0]
            for tag_spec in tag_specs[1:]:
                combined_tag_spec = combined_tag_spec.or_(tag_spec)
            specs.append(combined_tag_spec)
        
        # Combine all specifications with AND
        if not specs:
            # Return all products if no criteria specified
            return await self.find(AttributeSpecification("id", AttributeSpecification("id", None)).not_())
        
        final_spec = specs[0]
        for spec in specs[1:]:
            final_spec = final_spec.and_(spec)
        
        return await self.find(final_spec)
    
    async def update_stock_quantity(self, product: Product, quantity: int) -> None:
        """
        Update a product's stock quantity.
        
        Args:
            product: The product to update
            quantity: The new stock quantity
        """
        product.stock_quantity = quantity
        product.in_stock = quantity > 0
        product.updated_at = datetime.now(timezone.utc)
        await self.update(product)