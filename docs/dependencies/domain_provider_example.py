"""
Example of the domain provider pattern.

This module demonstrates how to implement the domain provider pattern
for dependency injection in a domain module.
"""

import logging
from functools import lru_cache
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol

from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
    Initializable,
    Disposable,
)
from uno.database.db_manager import DBManager


# Define domain entities
@dataclass
class Product:
    id: str
    name: str
    price: float
    description: Optional[str] = None


# Define repository protocol
class ProductRepositoryProtocol(Protocol):
    """Protocol for product repositories."""
    
    def get_product(self, id: str) -> Optional[Product]:
        """Get a product by ID."""
        ...
    
    def list_products(self) -> List[Product]:
        """List all products."""
        ...
    
    def save_product(self, product: Product) -> Product:
        """Save a product."""
        ...


# Implement repository
class ProductRepository(Initializable, Disposable):
    """Product repository implementation."""
    
    def __init__(self, db_factory: DBManager):
        """Initialize the repository."""
        self.db_factory = db_factory
        self.initialized = False
        self._cache: Dict[str, Product] = {}
    
    def initialize(self) -> None:
        """Initialize the repository."""
        self.initialized = True
        self._logger = logging.getLogger("product.repository")
        self._logger.info("Initialized ProductRepository")
    
    def dispose(self) -> None:
        """Dispose of the repository."""
        self._cache.clear()
        self._logger.info("Disposed ProductRepository")
    
    def get_product(self, id: str) -> Optional[Product]:
        """Get a product by ID."""
        # Try cache first
        if id in self._cache:
            return self._cache[id]
        
        # Get from database
        with self.db_factory.session() as session:
            # In a real implementation, this would use SQLAlchemy
            result = session.execute("SELECT * FROM products WHERE id = :id", {"id": id})
            row = result.fetchone()
            
            if row:
                product = Product(
                    id=row["id"],
                    name=row["name"],
                    price=row["price"],
                    description=row["description"],
                )
                self._cache[id] = product
                return product
            
            return None
    
    def list_products(self) -> List[Product]:
        """List all products."""
        with self.db_factory.session() as session:
            # In a real implementation, this would use SQLAlchemy
            result = session.execute("SELECT * FROM products")
            
            products = []
            for row in result:
                product = Product(
                    id=row["id"],
                    name=row["name"],
                    price=row["price"],
                    description=row["description"],
                )
                self._cache[product.id] = product
                products.append(product)
            
            return products
    
    def save_product(self, product: Product) -> Product:
        """Save a product."""
        with self.db_factory.session() as session:
            # In a real implementation, this would use SQLAlchemy
            session.execute(
                """
                INSERT INTO products (id, name, price, description)
                VALUES (:id, :name, :price, :description)
                ON CONFLICT (id) DO UPDATE
                SET name = :name, price = :price, description = :description
                """,
                {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "description": product.description,
                },
            )
            
            # Update cache
            self._cache[product.id] = product
            
            return product


# Define service protocol
class ProductServiceProtocol(Protocol):
    """Protocol for product services."""
    
    def get_product(self, id: str) -> Optional[Product]:
        """Get a product by ID."""
        ...
    
    def list_products(self) -> List[Product]:
        """List all products."""
        ...
    
    def create_product(self, name: str, price: float, description: Optional[str] = None) -> Product:
        """Create a new product."""
        ...
    
    def update_product(self, id: str, name: str, price: float, description: Optional[str] = None) -> Optional[Product]:
        """Update a product."""
        ...


# Implement service
class ProductService(Initializable, Disposable):
    """Product service implementation."""
    
    def __init__(self, repository: ProductRepositoryProtocol, logger: Optional[logging.Logger] = None):
        """Initialize the service."""
        self.repository = repository
        self._logger = logger or logging.getLogger("product.service")
    
    def initialize(self) -> None:
        """Initialize the service."""
        self._logger.info("Initialized ProductService")
    
    def dispose(self) -> None:
        """Dispose of the service."""
        self._logger.info("Disposed ProductService")
    
    def get_product(self, id: str) -> Optional[Product]:
        """Get a product by ID."""
        return self.repository.get_product(id)
    
    def list_products(self) -> List[Product]:
        """List all products."""
        return self.repository.list_products()
    
    def create_product(self, name: str, price: float, description: Optional[str] = None) -> Product:
        """Create a new product."""
        import uuid
        
        product = Product(
            id=str(uuid.uuid4()),
            name=name,
            price=price,
            description=description,
        )
        
        return self.repository.save_product(product)
    
    def update_product(self, id: str, name: str, price: float, description: Optional[str] = None) -> Optional[Product]:
        """Update a product."""
        product = self.repository.get_product(id)
        if not product:
            return None
        
        product.name = name
        product.price = price
        product.description = description
        
        return self.repository.save_product(product)


# Define domain provider
@lru_cache(maxsize=1)
def get_product_provider() -> UnoServiceProvider:
    """
    Get the Product domain service provider.
    
    Returns:
        A configured service provider for the Product domain
    """
    provider = UnoServiceProvider("product")
    logger = logging.getLogger("uno.product")
    
    # Register repository
    provider.register(
        ProductRepositoryProtocol,
        lambda container: ProductRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register service
    provider.register(
        ProductServiceProtocol,
        lambda container: ProductService(
            repository=container.resolve(ProductRepositoryProtocol),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider


def configure_product_services(container):
    """
    Configure Product domain services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_product_provider()
    provider.configure_container(container)


# Example usage
if __name__ == "__main__":
    # This would typically be done by the application
    from uno.dependencies.modern_provider import get_service_provider, initialize_services
    import asyncio
    
    # Initialize services
    asyncio.run(initialize_services())
    
    # Get product service
    provider = get_product_provider()
    service = provider.get_service(ProductServiceProtocol)
    
    # Use service
    product = service.create_product("Example Product", 10.99, "An example product")
    print(f"Created product: {product}")
    
    products = service.list_products()
    print(f"Found {len(products)} products")
    
    # Clean up
    asyncio.run(provider.shutdown())