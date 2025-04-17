"""
Order repository implementation for SQLAlchemy.
"""

from typing import List, Optional, Callable, Dict, Any, Type, cast
from datetime import datetime, timezone
import logging
import json

from sqlalchemy import select, func, and_, or_, Column, ForeignKey, Table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from uno.domain.repository_results import FindResult
from uno.domain.specifications import AttributeSpecification, AndSpecification, OrSpecification
from uno.domain.repositories.sqlalchemy.base import SQLAlchemyRepository
from uno.domain.models import Order, OrderStatus, OrderItem
from uno.model import UnoModel


# Association table for order items
order_items = Table(
    'order_items',
    UnoModel.metadata,
    Column('order_id', UnoModel.String, ForeignKey('orders.id'), primary_key=True),
    Column('item_id', UnoModel.String, primary_key=True),
    Column('product_id', UnoModel.String, nullable=False),
    Column('quantity', UnoModel.Integer, nullable=False),
    Column('unit_price', UnoModel.Numeric(10, 2), nullable=False),
    Column('total_price', UnoModel.Numeric(10, 2), nullable=False),
)


class OrderItemModel(UnoModel):
    """SQLAlchemy model for order items."""
    
    __tablename__ = "order_item_details"
    
    id = UnoModel.Column(UnoModel.String, primary_key=True)
    product_id = UnoModel.Column(UnoModel.String, nullable=False)
    quantity = UnoModel.Column(UnoModel.Integer, nullable=False)
    unit_price = UnoModel.Column(UnoModel.Numeric(10, 2), nullable=False)
    total_price = UnoModel.Column(UnoModel.Numeric(10, 2), nullable=False)
    created_at = UnoModel.Column(UnoModel.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class OrderModel(UnoModel):
    """SQLAlchemy model for orders."""
    
    __tablename__ = "orders"
    
    id = UnoModel.Column(UnoModel.String, primary_key=True)
    user_id = UnoModel.Column(UnoModel.String, nullable=False)
    status = UnoModel.Column(UnoModel.String, nullable=False)
    total_amount = UnoModel.Column(UnoModel.Numeric(10, 2), nullable=False)
    shipping_address = UnoModel.Column(UnoModel.JSON, nullable=True)
    payment_method = UnoModel.Column(UnoModel.String, nullable=True)
    order_date = UnoModel.Column(UnoModel.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = UnoModel.Column(UnoModel.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = UnoModel.Column(UnoModel.DateTime(timezone=True), nullable=True)
    
    # Relationship with order items
    items = relationship("OrderItemModel", secondary=order_items, lazy="selectin")


class OrderRepository(SQLAlchemyRepository[Order, OrderModel]):
    """Repository for Order entities."""
    
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the order repository.
        
        Args:
            session_factory: Factory function for creating SQLAlchemy sessions
            logger: Optional logger for diagnostic output
        """
        super().__init__(
            entity_type=Order,
            model_class=OrderModel,
            session_factory=session_factory,
            logger=logger or logging.getLogger(__name__)
        )
    
    async def find_by_user(self, user_id: str) -> List[Order]:
        """
        Find orders by user ID.
        
        Args:
            user_id: The user ID to search for
            
        Returns:
            List of orders for the specified user
        """
        spec = AttributeSpecification("user_id", user_id)
        return await self.find(spec)
    
    async def find_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Find orders by status.
        
        Args:
            status: The status to search for
            
        Returns:
            List of orders with the specified status
        """
        spec = AttributeSpecification("status", status.value)
        return await self.find(spec)
    
    async def find_by_user_and_status(self, user_id: str, status: OrderStatus) -> List[Order]:
        """
        Find orders by user ID and status.
        
        Args:
            user_id: The user ID to search for
            status: The status to search for
            
        Returns:
            List of orders for the specified user with the specified status
        """
        spec = AndSpecification(
            AttributeSpecification("user_id", user_id),
            AttributeSpecification("status", status.value)
        )
        return await self.find(spec)
    
    async def update_status(self, order: Order, status: OrderStatus) -> None:
        """
        Update an order's status.
        
        Args:
            order: The order to update
            status: The new status
        """
        order.status = status
        order.updated_at = datetime.now(timezone.utc)
        await self.update(order)
    
    def _to_entity(self, model: OrderModel) -> Order:
        """
        Convert a model to a domain entity.
        
        Args:
            model: The model to convert
            
        Returns:
            The corresponding domain entity
        """
        # Extract base data from model
        data = self._model_to_dict(model)
        
        # Extract items data
        items = []
        if hasattr(model, 'items') and model.items:
            for item_model in model.items:
                item_data = {
                    'id': item_model.id,
                    'product_id': item_model.product_id,
                    'quantity': item_model.quantity,
                    'unit_price': float(item_model.unit_price),
                    'total_price': float(item_model.total_price),
                }
                items.append(OrderItem(**item_data))
        
        # Add items to data
        data['items'] = items
        
        # Convert shipping_address from JSON to dict if needed
        if isinstance(data.get('shipping_address'), str):
            data['shipping_address'] = json.loads(data['shipping_address'])
        
        # Create order entity
        return Order(**data)
    
    def _to_model(self, entity: Order) -> OrderModel:
        """
        Convert a domain entity to a model.
        
        Args:
            entity: The entity to convert
            
        Returns:
            The corresponding model
        """
        # Extract base data from entity
        data = self._entity_to_dict(entity)
        
        # Remove items from data (handled separately)
        items_data = data.pop('items', [])
        
        # Convert shipping_address to JSON if needed
        if isinstance(data.get('shipping_address'), dict):
            data['shipping_address'] = json.dumps(data['shipping_address'])
        
        # Create order model
        order_model = OrderModel(**data)
        
        # Add items to order
        items = []
        for item_data in items_data:
            if isinstance(item_data, dict):
                items.append(OrderItemModel(**item_data))
            elif isinstance(item_data, OrderItem):
                items.append(OrderItemModel(
                    id=item_data.id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    total_price=item_data.total_price
                ))
        
        order_model.items = items
        
        return order_model
    
    async def _add(self, entity: Order) -> None:
        """
        Internal method to add a new order.
        
        Args:
            entity: The order to add
        """
        # Convert entity to model
        model = self._to_model(entity)
        
        # Add model to session with special handling for items
        async with self.session_factory() as session:
            # Add main order
            session.add(model)
            
            # Add order items
            for item in model.items:
                session.add(item)
                
                # Add association
                await session.execute(
                    order_items.insert().values(
                        order_id=model.id,
                        item_id=item.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.total_price
                    )
                )
            
            # Commit all changes
            await session.commit()