"""
Factories for the e-commerce domain.

This module contains factories for creating domain entities,
repositories, and services for the e-commerce domain.
"""

import logging
from typing import Dict, Any, Optional

from uno.domain.factory import DomainRegistry
from uno.domain.repository import UnoDBRepository
from uno.domain.events import EventPublisher

from examples.ecommerce.domain.entities import User, Product, Order
from examples.ecommerce.domain.services import UserService, ProductService, OrderService


class EcommerceServiceFactory:
    """
    Factory for creating e-commerce domain services.
    
    This factory provides methods for creating properly configured
    service instances for the e-commerce domain.
    """
    
    def __init__(
        self,
        domain_registry: DomainRegistry,
        event_publisher: EventPublisher,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the e-commerce service factory.
        
        Args:
            domain_registry: The domain registry for creating repositories
            event_publisher: The event publisher for domain events
            logger: Optional logger
        """
        self.domain_registry = domain_registry
        self.event_publisher = event_publisher
        self.logger = logger or logging.getLogger(__name__)
        self._services: Dict[str, Any] = {}
    
    def create_user_service(self) -> UserService:
        """
        Create a user service.
        
        Returns:
            A configured user service
        """
        if "user" not in self._services:
            # Get the user repository from the domain registry
            user_repository = self.domain_registry.get_repository(User)
            
            # Create and store the user service
            self._services["user"] = UserService(
                repository=user_repository,
                event_publisher=self.event_publisher,
                logger=self.logger.getChild("UserService")
            )
            
        return self._services["user"]
    
    def create_product_service(self) -> ProductService:
        """
        Create a product service.
        
        Returns:
            A configured product service
        """
        if "product" not in self._services:
            # Get the product repository from the domain registry
            product_repository = self.domain_registry.get_repository(Product)
            
            # Create and store the product service
            self._services["product"] = ProductService(
                repository=product_repository,
                event_publisher=self.event_publisher,
                logger=self.logger.getChild("ProductService")
            )
            
        return self._services["product"]
    
    def create_order_service(self) -> OrderService:
        """
        Create an order service.
        
        Returns:
            A configured order service
        """
        if "order" not in self._services:
            # Get the order repository from the domain registry
            order_repository = self.domain_registry.get_repository(Order)
            
            # Get or create the product service
            product_service = self.create_product_service()
            
            # Create and store the order service
            self._services["order"] = OrderService(
                repository=order_repository,
                product_service=product_service,
                event_publisher=self.event_publisher,
                logger=self.logger.getChild("OrderService")
            )
            
        return self._services["order"]
    
    def create_all_services(self) -> Dict[str, Any]:
        """
        Create all e-commerce services.
        
        Returns:
            Dictionary of service name to service instance
        """
        self.create_user_service()
        self.create_product_service()
        self.create_order_service()
        return self._services