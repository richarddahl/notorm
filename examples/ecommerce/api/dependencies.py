"""
FastAPI dependencies for the e-commerce API.

This module defines dependencies used by the API endpoints,
such as getting current user information from the JWT token.
"""

import logging
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from uno.dependencies import (
    get_domain_registry, 
    get_event_publisher,
    get_domain_service
)
from uno.domain.factory import DomainRegistry
from uno.domain.events import EventPublisher

from examples.ecommerce.domain.entities import User, Product, Order
from examples.ecommerce.domain.services import UserService, ProductService, OrderService
from examples.ecommerce.domain.factories import EcommerceServiceFactory


# Security scheme for JWT
security = HTTPBearer()

# Logger
logger = logging.getLogger("ecommerce_api")


async def get_current_user_email(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract the user's email from the JWT token.
    
    Note: In a real implementation, this would validate and decode the JWT.
    For simplicity, we'll assume the token is the email address.
    
    Args:
        credentials: HTTP Authorization credentials containing the JWT
        
    Returns:
        The user's email address
    """
    # In a real implementation, you would decode and validate the JWT
    # token = credentials.credentials
    # decoded = jwt.decode(token, key, algorithms=["HS256"])
    # return decoded.get("email")
    
    # For this example, we'll just return a placeholder email
    return "john@example.com"


async def get_service_factory() -> EcommerceServiceFactory:
    """
    Get the e-commerce service factory.
    
    Returns:
        The e-commerce service factory
    """
    domain_registry = get_domain_registry()
    event_publisher = get_event_publisher()
    
    return EcommerceServiceFactory(
        domain_registry=domain_registry,
        event_publisher=event_publisher,
        logger=logger
    )


async def get_user_service(
    factory: EcommerceServiceFactory = Depends(get_service_factory)
) -> UserService:
    """
    Get the user service.
    
    Args:
        factory: The e-commerce service factory
        
    Returns:
        The user service
    """
    return factory.create_user_service()


async def get_product_service(
    factory: EcommerceServiceFactory = Depends(get_service_factory)
) -> ProductService:
    """
    Get the product service.
    
    Args:
        factory: The e-commerce service factory
        
    Returns:
        The product service
    """
    return factory.create_product_service()


async def get_order_service(
    factory: EcommerceServiceFactory = Depends(get_service_factory)
) -> OrderService:
    """
    Get the order service.
    
    Args:
        factory: The e-commerce service factory
        
    Returns:
        The order service
    """
    return factory.create_order_service()


async def get_current_user(
    email: str = Depends(get_current_user_email),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        email: The user's email address
        user_service: The user service
        
    Returns:
        The user entity
        
    Raises:
        HTTPException: If the user is not found
    """
    user = await user_service.find_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user