"""
Specifications for the catalog context.

This module defines specifications for building queries against the product and
category repositories. Specifications encapsulate query criteria in reusable objects.
"""

from typing import List, Optional
from decimal import Decimal

from sqlalchemy import and_, or_, not_
from sqlalchemy.sql.expression import BinaryExpression

from uno.domain.specifications import (
    Specification, 
    SqlAlchemySpecification,
    AndSpecification,
    OrSpecification,
    NotSpecification
)
from uno.examples.ecommerce_app.catalog.domain.entities import Product
from uno.examples.ecommerce_app.catalog.repository.models import ProductModel


class ProductByStatusSpecification(SqlAlchemySpecification[Product]):
    """Specification for finding products by status."""
    
    def __init__(self, status: str):
        """Initialize with status."""
        self.status = status
        
    def to_expression(self) -> BinaryExpression:
        """Convert to SQLAlchemy expression."""
        return ProductModel.status == self.status
        
    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product satisfies the specification."""
        return product.status == self.status


class ProductByCategorySpecification(SqlAlchemySpecification[Product]):
    """Specification for finding products by category."""
    
    def __init__(self, category_id: str):
        """Initialize with category ID."""
        self.category_id = category_id
        
    def to_expression(self) -> BinaryExpression:
        """Convert to SQLAlchemy expression."""
        # This is more complex in SQL, as it involves a join
        # In a real implementation, you'd need a custom query
        # This is a placeholder
        return ProductModel.id.in_(
            "SELECT product_id FROM catalog_product_category WHERE category_id = :category_id"
        )
        
    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product satisfies the specification."""
        return self.category_id in product.category_ids


class ProductByPriceRangeSpecification(SqlAlchemySpecification[Product]):
    """Specification for finding products within a price range."""
    
    def __init__(self, min_price: Optional[Decimal] = None, max_price: Optional[Decimal] = None):
        """Initialize with price range."""
        self.min_price = min_price
        self.max_price = max_price
        
    def to_expression(self) -> BinaryExpression:
        """Convert to SQLAlchemy expression."""
        expressions = []
        
        if self.min_price is not None:
            expressions.append(ProductModel.price_amount >= float(self.min_price))
            
        if self.max_price is not None:
            expressions.append(ProductModel.price_amount <= float(self.max_price))
            
        return and_(*expressions)
        
    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product satisfies the specification."""
        if self.min_price is not None and product.price.amount < self.min_price:
            return False
            
        if self.max_price is not None and product.price.amount > self.max_price:
            return False
            
        return True


class ProductByNameSpecification(SqlAlchemySpecification[Product]):
    """Specification for finding products by name."""
    
    def __init__(self, search_term: str):
        """Initialize with search term."""
        self.search_term = search_term.lower()
        
    def to_expression(self) -> BinaryExpression:
        """Convert to SQLAlchemy expression."""
        return ProductModel.name.ilike(f"%{self.search_term}%")
        
    def is_satisfied_by(self, product: Product) -> bool:
        """Check if product satisfies the specification."""
        return self.search_term in product.name.lower()