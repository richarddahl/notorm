"""
Mapper functions for the e-commerce API.

This module contains functions for mapping between domain entities and DTOs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from examples.ecommerce.domain.entities import (
    User, Product, Order, OrderItem, Payment, OrderStatus
)
from examples.ecommerce.domain.value_objects import (
    Money, Address, Rating, EmailAddress, PhoneNumber
)

from examples.ecommerce.api.dto.common import AddressDTO, MoneyDTO
from examples.ecommerce.api.dto.user import UserResponse
from examples.ecommerce.api.dto.product import ProductResponse
from examples.ecommerce.api.dto.order import (
    OrderResponse, OrderItemResponse, PaymentResponse
)


def map_address_to_dto(address: Address) -> AddressDTO:
    """Map domain Address to AddressDTO."""
    if not address:
        return None
        
    return AddressDTO(
        street=address.street,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        country=address.country
    )


def map_dto_to_address(address_dto: AddressDTO) -> Address:
    """Map AddressDTO to domain Address."""
    if not address_dto:
        return None
        
    return Address(
        street=address_dto.street,
        city=address_dto.city,
        state=address_dto.state,
        postal_code=address_dto.postal_code,
        country=address_dto.country
    )


def map_money_to_dto(money: Money) -> MoneyDTO:
    """Map domain Money to MoneyDTO."""
    if not money:
        return None
        
    return MoneyDTO(
        amount=money.amount,
        currency=money.currency
    )


def map_user_to_response(user: User) -> UserResponse:
    """Map User entity to UserResponse DTO."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email.address if user.email else None,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone.number if user.phone else None,
        billing_address=map_address_to_dto(user.billing_address),
        shipping_address=map_address_to_dto(user.shipping_address),
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at.isoformat() if user.created_at else None
    )


def map_product_to_response(product: Product) -> ProductResponse:
    """Map Product entity to ProductResponse DTO."""
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=map_money_to_dto(product.price),
        category_id=product.category_id,
        inventory_count=product.inventory_count,
        is_active=product.is_active,
        is_in_stock=product.is_in_stock(),
        attributes=product.attributes or {},
        average_rating=product.get_average_rating(),
        ratings_count=len(product.ratings),
        created_at=product.created_at.isoformat() if product.created_at else None
    )


def map_order_item_to_response(item: OrderItem) -> OrderItemResponse:
    """Map OrderItem entity to OrderItemResponse DTO."""
    return OrderItemResponse(
        id=item.id,
        product_id=item.product_id,
        product_name=item.product_name,
        price=map_money_to_dto(item.price),
        quantity=item.quantity,
        total_price=map_money_to_dto(item.total_price)
    )


def map_payment_to_response(payment: Payment) -> PaymentResponse:
    """Map Payment entity to PaymentResponse DTO."""
    if not payment:
        return None
        
    return PaymentResponse(
        id=payment.id,
        amount=map_money_to_dto(payment.amount),
        method=payment.method,
        status=payment.status,
        transaction_id=payment.transaction_id,
        created_at=payment.created_at.isoformat() if payment.created_at else None
    )


def map_order_to_response(order: Order) -> OrderResponse:
    """Map Order entity to OrderResponse DTO."""
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        items=[map_order_item_to_response(item) for item in order.items],
        shipping_address=map_address_to_dto(order.shipping_address),
        billing_address=map_address_to_dto(order.billing_address),
        status=order.status,
        subtotal=map_money_to_dto(order.subtotal),
        payment=map_payment_to_response(order.payment),
        created_at=order.created_at.isoformat() if order.created_at else None,
        shipped_at=order.shipped_at.isoformat() if order.shipped_at else None,
        delivered_at=order.delivered_at.isoformat() if order.delivered_at else None,
        cancelled_at=order.cancelled_at.isoformat() if order.cancelled_at else None,
        notes=order.notes
    )