"""
Example usage of the Specification pattern.

This example demonstrates how to create and compose specifications
for filtering domain objects.
"""

from dataclasses import dataclass
from typing import List
from uno.domain import (
    Specification,
    PredicateSpecification,
    specification_from_predicate,
)


@dataclass
class Product:
    """Example product class for demonstration."""

    id: int
    name: str
    price: float
    category: str
    in_stock: bool


class PremiumProductSpecification(Specification[Product]):
    """Specification for premium products (price > 1000)."""

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.price > 1000


class InStockSpecification(Specification[Product]):
    """Specification for products that are in stock."""

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.in_stock


class CategorySpecification(Specification[Product]):
    """Specification for products in a specific category."""

    def __init__(self, category: str):
        self.category = category

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.category == self.category


def main():
    # Create some sample products
    products = [
        Product(1, "Budget Laptop", 500, "Electronics", True),
        Product(2, "Premium Laptop", 2000, "Electronics", True),
        Product(3, "Smartphone", 800, "Electronics", False),
        Product(4, "Designer Watch", 1200, "Fashion", True),
        Product(5, "Basic T-shirt", 20, "Clothing", True),
    ]

    # Create specifications
    premium_spec = PremiumProductSpecification()
    in_stock_spec = InStockSpecification()
    electronics_spec = CategorySpecification("Electronics")

    # Using predicate specification (alternative to creating a class)
    cheap_spec = specification_from_predicate(lambda p: p.price < 100)

    # Compose specifications
    premium_in_stock_spec = premium_spec.and_(in_stock_spec)
    premium_or_electronics_spec = premium_spec.or_(electronics_spec)
    not_electronics_spec = electronics_spec.not_()

    # Filter products using specifications
    print("Premium products:")
    for product in filter(premium_spec.is_satisfied_by, products):
        print(f"  - {product.name} (${product.price})")

    print("\nPremium products in stock:")
    for product in filter(premium_in_stock_spec.is_satisfied_by, products):
        print(f"  - {product.name} (${product.price})")

    print("\nPremium products or electronics:")
    for product in filter(premium_or_electronics_spec.is_satisfied_by, products):
        print(f"  - {product.name} (${product.price}, {product.category})")

    print("\nNon-electronics products:")
    for product in filter(not_electronics_spec.is_satisfied_by, products):
        print(f"  - {product.name} ({product.category})")

    print("\nCheap products (using predicate specification):")
    for product in filter(cheap_spec.is_satisfied_by, products):
        print(f"  - {product.name} (${product.price})")


if __name__ == "__main__":
    main()
