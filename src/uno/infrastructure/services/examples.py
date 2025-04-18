"""
Examples of using the unified service pattern in the Uno framework.

This module provides examples of how to use the various service types,
factory functions, and dependency injection integration.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, ClassVar, Type, Generic, TypeVar

from uno.core.errors.result import Result, Success, Failure
from uno.core.di import inject
from uno.domain.models.base import Entity, AggregateRoot, ValueObject
from uno.domain.protocols import DomainEvent
from uno.infrastructure.repositories import RepositoryProtocol, AggregateRootRepositoryProtocol

from uno.infrastructure.services import (
    Service,
    TransactionalService,
    CrudService,
    AggregateCrudService,
    QueryService,
    ApplicationService,
    create_crud_service,
    create_aggregate_service,
    create_query_service,
    register_crud_service
)

T = TypeVar('T')


# Example domain entities and events

@dataclass
class ProductCreatedEvent(DomainEvent):
    """Event raised when a product is created."""
    product_id: str
    name: str
    price: float
    

@dataclass
class Product(Entity):
    """Example product entity."""
    name: str
    price: float
    description: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    is_active: bool = True
    stock: int = 0
    
    def activate(self) -> None:
        """Activate the product."""
        if not self.is_active:
            self.is_active = True
            self.add_event(ProductCreatedEvent(
                product_id=str(self.id),
                name=self.name,
                price=self.price
            ))
    
    def deactivate(self) -> None:
        """Deactivate the product."""
        if self.is_active:
            self.is_active = False


@dataclass
class OrderItem(ValueObject):
    """Order item value object."""
    product_id: str
    quantity: int
    price: float
    
    @property
    def total(self) -> float:
        """Calculate the total price."""
        return self.price * self.quantity


@dataclass
class Order(AggregateRoot):
    """Example order aggregate root."""
    customer_id: str
    items: List[OrderItem] = field(default_factory=list)
    status: str = "pending"
    
    def add_item(self, product_id: str, quantity: int, price: float) -> None:
        """Add an item to the order."""
        self.items.append(OrderItem(product_id, quantity, price))
        self.version += 1
    
    def remove_item(self, product_id: str) -> None:
        """Remove an item from the order."""
        self.items = [item for item in self.items if item.product_id != product_id]
        self.version += 1
    
    def complete(self) -> None:
        """Complete the order."""
        if self.status != "completed":
            self.status = "completed"
            self.version += 1
    
    def cancel(self) -> None:
        """Cancel the order."""
        if self.status != "cancelled":
            self.status = "cancelled"
            self.version += 1
    
    @property
    def total(self) -> float:
        """Calculate the total price."""
        return sum(item.total for item in self.items)


# Example service implementations

class ProductService(CrudService[Product]):
    """Example CRUD service for products."""
    
    async def activate_product(self, product_id: str) -> Result[Product]:
        """
        Activate a product.
        
        Args:
            product_id: The product ID
            
        Returns:
            Result containing the activated product
        """
        # Get the product
        product_result = await self.get_by_id(product_id)
        if product_result.is_failure:
            return product_result
        
        product = product_result.value
        
        # Activate the product
        product.activate()
        
        # Update the product
        return await self.update(product)
    
    async def deactivate_product(self, product_id: str) -> Result[Product]:
        """
        Deactivate a product.
        
        Args:
            product_id: The product ID
            
        Returns:
            Result containing the deactivated product
        """
        # Get the product
        product_result = await self.get_by_id(product_id)
        if product_result.is_failure:
            return product_result
        
        product = product_result.value
        
        # Deactivate the product
        product.deactivate()
        
        # Update the product
        return await self.update(product)
    
    async def get_active_products(self) -> Result[List[Product]]:
        """
        Get all active products.
        
        Returns:
            Result containing the list of active products
        """
        # Get all products
        products_result = await self.get_all()
        if products_result.is_failure:
            return products_result
        
        # Filter active products
        active_products = [p for p in products_result.value if p.is_active]
        
        return Success(active_products)


class OrderService(AggregateCrudService[Order]):
    """Example aggregate service for orders."""
    
    # Inject the product service
    @inject
    def __init__(
        self, 
        repository: AggregateRootRepositoryProtocol[Order],
        product_service: ProductService,
        entity_type: Type[Order] = Order,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the order service.
        
        Args:
            repository: The order repository
            product_service: The product service
            entity_type: The entity type
            logger: Optional logger
        """
        super().__init__(
            entity_type=entity_type,
            repository=repository,
            logger=logger
        )
        self.product_service = product_service
    
    async def add_item_to_order(
        self, 
        order_id: str, 
        product_id: str, 
        quantity: int
    ) -> Result[Order]:
        """
        Add an item to an order.
        
        Args:
            order_id: The order ID
            product_id: The product ID
            quantity: The quantity
            
        Returns:
            Result containing the updated order
        """
        # Get the order
        order_result = await self.get_by_id(order_id)
        if order_result.is_failure:
            return order_result
        
        order = order_result.value
        
        # Get the product
        product_result = await self.product_service.get_by_id(product_id)
        if product_result.is_failure:
            return Failure(
                error=f"Product {product_id} not found",
                code="PRODUCT_NOT_FOUND"
            )
        
        product = product_result.value
        
        # Add the item to the order
        order.add_item(product_id, quantity, product.price)
        
        # Update the order
        return await self.update(order)
    
    async def complete_order(self, order_id: str) -> Result[Order]:
        """
        Complete an order.
        
        Args:
            order_id: The order ID
            
        Returns:
            Result containing the completed order
        """
        # Get the order
        order_result = await self.get_by_id(order_id)
        if order_result.is_failure:
            return order_result
        
        order = order_result.value
        
        # Complete the order
        order.complete()
        
        # Update the order
        return await self.update(order)
    
    async def cancel_order(self, order_id: str) -> Result[Order]:
        """
        Cancel an order.
        
        Args:
            order_id: The order ID
            
        Returns:
            Result containing the cancelled order
        """
        # Get the order
        order_result = await self.get_by_id(order_id)
        if order_result.is_failure:
            return order_result
        
        order = order_result.value
        
        # Cancel the order
        order.cancel()
        
        # Update the order
        return await self.update(order)


class ProductQueryService(QueryService[Product]):
    """Example query service for products."""
    
    async def get_by_category(self, category: str) -> Result[List[Product]]:
        """
        Get products by category.
        
        Args:
            category: The category
            
        Returns:
            Result containing the list of products in the category
        """
        # Get all products
        products_result = await self.get_all()
        if products_result.is_failure:
            return products_result
        
        # Filter by category
        products = [p for p in products_result.value if category in p.categories]
        
        return Success(products)
    
    async def get_by_price_range(self, min_price: float, max_price: float) -> Result[List[Product]]:
        """
        Get products by price range.
        
        Args:
            min_price: The minimum price
            max_price: The maximum price
            
        Returns:
            Result containing the list of products in the price range
        """
        # Get all products
        products_result = await self.get_all()
        if products_result.is_failure:
            return products_result
        
        # Filter by price range
        products = [
            p for p in products_result.value 
            if min_price <= p.price <= max_price
        ]
        
        return Success(products)


class OrderProcessingService(ApplicationService):
    """Example application service for order processing."""
    
    # Inject the order and product services
    @inject
    def __init__(
        self, 
        order_service: OrderService,
        product_service: ProductService,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the order processing service.
        
        Args:
            order_service: The order service
            product_service: The product service
            logger: Optional logger
        """
        super().__init__(logger=logger)
        self.order_service = order_service
        self.product_service = product_service
    
    async def create_order_with_items(
        self, 
        customer_id: str, 
        items: List[Dict[str, Any]]
    ) -> Result[Order]:
        """
        Create an order with items.
        
        Args:
            customer_id: The customer ID
            items: List of items, each with product_id and quantity
            
        Returns:
            Result containing the created order
        """
        # Create the order
        order = Order(customer_id=customer_id)
        
        # Save the order to get an ID
        order_result = await self.order_service.create(order)
        if order_result.is_failure:
            return order_result
        
        order = order_result.value
        
        # Add items to the order
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Get the product
            product_result = await self.product_service.get_by_id(product_id)
            if product_result.is_failure:
                # Rollback by deleting the order
                await self.order_service.delete(order.id)
                return Failure(
                    error=f"Product {product_id} not found",
                    code="PRODUCT_NOT_FOUND"
                )
            
            product = product_result.value
            
            # Add the item to the order
            order.add_item(product_id, quantity, product.price)
        
        # Update the order
        return await self.order_service.update(order)
    
    async def process_order(self, order_id: str) -> Result[Order]:
        """
        Process an order.
        
        Args:
            order_id: The order ID
            
        Returns:
            Result containing the processed order
        """
        # Get the order
        order_result = await self.order_service.get_by_id(order_id)
        if order_result.is_failure:
            return order_result
        
        order = order_result.value
        
        # Check if the order can be processed
        if order.status != "pending":
            return Failure(
                error=f"Order {order_id} is not pending",
                code="ORDER_NOT_PENDING"
            )
        
        # Check product availability
        for item in order.items:
            product_result = await self.product_service.get_by_id(item.product_id)
            if product_result.is_failure:
                return Failure(
                    error=f"Product {item.product_id} not found",
                    code="PRODUCT_NOT_FOUND"
                )
            
            product = product_result.value
            
            if not product.is_active:
                return Failure(
                    error=f"Product {item.product_id} is not active",
                    code="PRODUCT_NOT_ACTIVE"
                )
            
            if product.stock < item.quantity:
                return Failure(
                    error=f"Not enough stock for product {item.product_id}",
                    code="INSUFFICIENT_STOCK"
                )
        
        # Complete the order
        complete_result = await self.order_service.complete_order(order_id)
        if complete_result.is_failure:
            return complete_result
        
        # Update product stock
        for item in order.items:
            product_result = await self.product_service.get_by_id(item.product_id)
            if product_result.is_failure:
                continue  # Skip if product not found
            
            product = product_result.value
            product.stock -= item.quantity
            
            await self.product_service.update(product)
        
        return complete_result


# Examples of using the service factory

async def example_using_factory():
    """Example of using the service factory."""
    
    # Create a product repository
    from uno.infrastructure.repositories import create_repository
    product_repo = create_repository(Product)
    
    # Create a product service using the factory
    product_service = create_crud_service(Product, repository=product_repo)
    
    # Create an order repository
    order_repo = create_repository(Order, aggregate=True)
    
    # Create an order service using the factory
    order_service = create_aggregate_service(Order, repository=order_repo)
    
    # Create a product query service
    product_query = create_query_service(Product, repository=product_repo)
    
    # Register the product service with DI
    register_crud_service(Product, ProductService)
    
    # Create and use an application service
    order_processing = OrderProcessingService(
        order_service=order_service,
        product_service=product_service
    )
    
    # Example usage
    result = await order_processing.create_order_with_items(
        customer_id="customer1",
        items=[
            {"product_id": "product1", "quantity": 2},
            {"product_id": "product2", "quantity": 1}
        ]
    )
    
    if result.is_success:
        order = result.value
        print(f"Created order: {order.id} with total: {order.total}")
    else:
        print(f"Error: {result.error}")


# Example of using the services with dependency injection

@inject
async def example_using_di(
    product_service: ProductService,
    order_service: OrderService,
    order_processing: OrderProcessingService
):
    """Example of using services with dependency injection."""
    
    # Create a product
    product = Product(name="Test Product", price=19.99, stock=10)
    product_result = await product_service.create(product)
    
    if product_result.is_success:
        product = product_result.value
        print(f"Created product: {product.id}")
        
        # Create an order with the product
        result = await order_processing.create_order_with_items(
            customer_id="customer1",
            items=[{"product_id": product.id, "quantity": 2}]
        )
        
        if result.is_success:
            order = result.value
            print(f"Created order: {order.id} with total: {order.total}")
            
            # Process the order
            process_result = await order_processing.process_order(order.id)
            
            if process_result.is_success:
                print(f"Order processed: {order.id}")
            else:
                print(f"Error processing order: {process_result.error}")
        else:
            print(f"Error creating order: {result.error}")
    else:
        print(f"Error creating product: {product_result.error}")