"""
Domain services for the e-commerce domain.

This module contains domain services that implement business logic
that doesn't naturally fit within domain entities.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from uno.domain.service import DomainService
from uno.domain.repository import Repository
from uno.domain.core import DomainEvent
from uno.domain.events import EventPublisher

from examples.ecommerce.domain.entities import (
    User, Product, Order, OrderStatus, Payment, PaymentMethod
)
from examples.ecommerce.domain.value_objects import Money, Address, CreditCard
from examples.ecommerce.domain.events import (
    PaymentProcessedEvent, OrderStatusChangedEvent, ProductInventoryChangedEvent
)


class UserService(DomainService[User]):
    """
    Service for user-related operations.
    
    This service handles user registration, authentication, and profile management.
    """
    
    def __init__(
        self, 
        repository: Repository[User],
        event_publisher: EventPublisher,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the user service."""
        super().__init__(repository, logger)
        self.event_publisher = event_publisher
    
    async def register_user(self, user_data: Dict[str, Any]) -> User:
        """
        Register a new user.
        
        Args:
            user_data: User data dictionary containing all required fields
            
        Returns:
            The registered user
        """
        # Create the user entity
        user = User.register(
            username=user_data["username"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            phone=user_data.get("phone"),
            billing_address=user_data.get("billing_address"),
            shipping_address=user_data.get("shipping_address")
        )
        
        # Save the user to the repository
        saved_user = await self.save(user)
        
        # Publish any domain events
        await self.event_publisher.publish_all(user.clear_events())
        
        return saved_user
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user.
        
        Note: This is a placeholder - real implementation would
        validate credentials against secure storage.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            The authenticated user if successful, None otherwise
        """
        # In a real implementation, this would check credentials
        # Here we just fetch the user by username
        users = await self.list(filters={"username": username})
        if users and len(users) == 1:
            return users[0]
        return None
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            The user if found, None otherwise
        """
        users = await self.list(filters={"email.address": email})
        if users and len(users) == 1:
            return users[0]
        return None
    
    async def change_user_address(
        self, 
        user_id: str, 
        billing_address: Optional[Address] = None,
        shipping_address: Optional[Address] = None,
        use_billing_for_shipping: bool = False
    ) -> Optional[User]:
        """
        Change a user's address information.
        
        Args:
            user_id: The user ID
            billing_address: Optional new billing address
            shipping_address: Optional new shipping address
            use_billing_for_shipping: Whether to use billing address for shipping
            
        Returns:
            The updated user if successful, None otherwise
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
            
        user.update_addresses(
            billing_address=billing_address,
            shipping_address=shipping_address,
            use_billing_for_shipping=use_billing_for_shipping
        )
        
        return await self.save(user)


class ProductService(DomainService[Product]):
    """
    Service for product-related operations.
    
    This service handles product creation, inventory management, and search.
    """
    
    def __init__(
        self, 
        repository: Repository[Product],
        event_publisher: EventPublisher,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the product service."""
        super().__init__(repository, logger)
        self.event_publisher = event_publisher
    
    async def create_product(self, product_data: Dict[str, Any]) -> Product:
        """
        Create a new product.
        
        Args:
            product_data: Product data dictionary
            
        Returns:
            The created product
        """
        # Create the product entity
        product = Product.create(
            name=product_data["name"],
            description=product_data["description"],
            price=product_data["price"],
            category_id=product_data.get("category_id"),
            inventory_count=product_data.get("inventory_count", 0),
            currency=product_data.get("currency", "USD"),
            attributes=product_data.get("attributes")
        )
        
        # Save the product
        saved_product = await self.save(product)
        
        # Publish any domain events
        await self.event_publisher.publish_all(product.clear_events())
        
        return saved_product
    
    async def update_inventory(
        self, 
        product_id: str, 
        change: int, 
        reason: str
    ) -> Optional[Product]:
        """
        Update product inventory.
        
        Args:
            product_id: The product ID
            change: The inventory change amount (positive for add, negative for remove)
            reason: The reason for the inventory change
            
        Returns:
            The updated product if successful, None otherwise
        """
        product = await self.get_by_id(product_id)
        if not product:
            return None
            
        previous_count = product.inventory_count
        
        try:
            if change > 0:
                product.add_inventory(change)
            elif change < 0:
                product.remove_inventory(abs(change))
            # Zero change is a no-op
        except ValueError as e:
            self.logger.error(f"Inventory update failed: {str(e)}")
            return None
            
        # Create event for inventory change
        event = ProductInventoryChangedEvent(
            product_id=product.id,
            previous_count=previous_count,
            new_count=product.inventory_count,
            change_amount=change,
            timestamp=datetime.utcnow()
        )
        product.add_event(event)
        
        # Save the product
        saved_product = await self.save(product)
        
        # Publish any domain events
        await self.event_publisher.publish_all(product.clear_events())
        
        return saved_product
    
    async def search_products(
        self,
        query: Optional[str] = None,
        category_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Product]:
        """
        Search for products based on criteria.
        
        Args:
            query: Optional search query
            category_id: Optional category ID
            min_price: Optional minimum price
            max_price: Optional maximum price
            in_stock_only: If True, only include products in stock
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching products
        """
        filters = {"is_active": True}
        
        if category_id:
            filters["category_id"] = category_id
            
        if in_stock_only:
            filters["inventory_count__gt"] = 0
            
        # Note: This is a simplified implementation
        # In a real system, you'd use more sophisticated search mechanisms
        products = await self.list(filters=filters, limit=limit, offset=offset)
        
        # Apply price filters in memory (for demo purposes)
        # In a real implementation, these would be part of the database query
        result = []
        for product in products:
            if min_price is not None and product.price.amount < min_price:
                continue
            if max_price is not None and product.price.amount > max_price:
                continue
            if query and query.lower() not in product.name.lower() and query.lower() not in product.description.lower():
                continue
            result.append(product)
            
        return result


class OrderService(DomainService[Order]):
    """
    Service for order-related operations.
    
    This service handles order creation, processing, and status management.
    """
    
    def __init__(
        self, 
        repository: Repository[Order],
        product_service: ProductService,
        event_publisher: EventPublisher,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the order service."""
        super().__init__(repository, logger)
        self.product_service = product_service
        self.event_publisher = event_publisher
    
    async def create_order(
        self, 
        user_id: str,
        shipping_address: Address,
        billing_address: Address,
        items: List[Dict[str, Any]]
    ) -> Tuple[Order, List[str]]:
        """
        Create a new order.
        
        Args:
            user_id: The user ID
            shipping_address: The shipping address
            billing_address: The billing address
            items: List of items to add to the order
            
        Returns:
            Tuple of (order, error_messages)
        """
        # Validate items and collect product data
        order_items = []
        error_messages = []
        
        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            
            # Get the product
            product = await self.product_service.get_by_id(product_id)
            if not product:
                error_messages.append(f"Product not found: {product_id}")
                continue
                
            if not product.is_active:
                error_messages.append(f"Product is not active: {product.name}")
                continue
                
            if quantity > product.inventory_count:
                error_messages.append(f"Insufficient inventory for {product.name}: requested {quantity}, available {product.inventory_count}")
                continue
                
            # Add to order items
            order_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "price": product.price.amount,
                "currency": product.price.currency,
                "quantity": quantity
            })
        
        # If there are any errors, return them
        if error_messages and not order_items:
            return None, error_messages
            
        # Create the order
        order = Order.create(
            user_id=user_id,
            shipping_address=shipping_address,
            billing_address=billing_address,
            items=order_items
        )
        
        # Save the order
        saved_order = await self.save(order)
        
        # Publish any domain events
        await self.event_publisher.publish_all(order.clear_events())
        
        return saved_order, error_messages
    
    async def process_payment(
        self,
        order_id: str,
        payment_method: str,
        payment_details: Dict[str, Any]
    ) -> Tuple[Optional[Order], Optional[str]]:
        """
        Process a payment for an order.
        
        Args:
            order_id: The order ID
            payment_method: The payment method
            payment_details: Payment details (depends on method)
            
        Returns:
            Tuple of (updated_order, error_message)
        """
        order = await self.get_by_id(order_id)
        if not order:
            return None, "Order not found"
            
        # Process payment based on method
        try:
            if payment_method == PaymentMethod.CREDIT_CARD:
                # Validate credit card details (simplified)
                cc_number = payment_details.get("card_number")
                cc_exp_month = payment_details.get("expiry_month")
                cc_exp_year = payment_details.get("expiry_year")
                cc_holder = payment_details.get("holder_name")
                
                if not all([cc_number, cc_exp_month, cc_exp_year, cc_holder]):
                    return None, "Missing credit card details"
                    
                # Create credit card object (includes validation)
                try:
                    credit_card = CreditCard(
                        number=cc_number,
                        expiry_month=int(cc_exp_month),
                        expiry_year=int(cc_exp_year),
                        holder_name=cc_holder
                    )
                    
                    if credit_card.is_expired():
                        return None, "Credit card is expired"
                except ValueError as e:
                    return None, f"Invalid credit card: {str(e)}"
                
                # Process payment (in a real implementation, this would call a payment gateway)
                transaction_id = f"cc-{datetime.utcnow().timestamp()}"
                
            elif payment_method == PaymentMethod.PAYPAL:
                # Validate PayPal details (simplified)
                paypal_id = payment_details.get("paypal_id")
                if not paypal_id:
                    return None, "Missing PayPal ID"
                    
                # Process payment (in a real implementation, this would call PayPal API)
                transaction_id = f"pp-{datetime.utcnow().timestamp()}"
                
            elif payment_method == PaymentMethod.BANK_TRANSFER:
                # Validate bank transfer details (simplified)
                bank_ref = payment_details.get("reference")
                if not bank_ref:
                    return None, "Missing bank transfer reference"
                    
                # Process payment (in a real implementation, this would check bank transfer)
                transaction_id = f"bt-{datetime.utcnow().timestamp()}"
                
            else:
                return None, f"Unsupported payment method: {payment_method}"
                
            # Process the payment on the order
            order.process_payment(
                method=payment_method,
                amount=order.subtotal,  # Simplified: using subtotal as total
                payment_details=payment_details
            )
            
            # Mark payment as completed
            order.payment.complete(transaction_id)
            
            # Update order status to paid
            order.update_status(OrderStatus.PAID)
            
            # Update inventory for each item
            for item in order.items:
                await self.product_service.update_inventory(
                    product_id=item.product_id,
                    change=-item.quantity,
                    reason=f"Order {order.id}"
                )
            
            # Save the order
            saved_order = await self.save(order)
            
            # Publish any domain events
            await self.event_publisher.publish_all(order.clear_events())
            
            return saved_order, None
            
        except Exception as e:
            self.logger.error(f"Payment processing error: {str(e)}")
            return None, f"Payment processing error: {str(e)}"
    
    async def update_order_status(
        self,
        order_id: str,
        new_status: str,
        notes: Optional[str] = None
    ) -> Tuple[Optional[Order], Optional[str]]:
        """
        Update an order's status.
        
        Args:
            order_id: The order ID
            new_status: The new status
            notes: Optional notes about the status change
            
        Returns:
            Tuple of (updated_order, error_message)
        """
        order = await self.get_by_id(order_id)
        if not order:
            return None, "Order not found"
            
        try:
            order.update_status(new_status, notes)
            
            # Save the order
            saved_order = await self.save(order)
            
            # Publish any domain events
            await self.event_publisher.publish_all(order.clear_events())
            
            return saved_order, None
        except ValueError as e:
            return None, str(e)
    
    async def cancel_order(
        self,
        order_id: str,
        reason: Optional[str] = None
    ) -> Tuple[Optional[Order], Optional[str]]:
        """
        Cancel an order.
        
        Args:
            order_id: The order ID
            reason: Optional reason for cancellation
            
        Returns:
            Tuple of (updated_order, error_message)
        """
        order = await self.get_by_id(order_id)
        if not order:
            return None, "Order not found"
            
        try:
            # Cancel the order
            order.cancel(reason)
            
            # Return inventory for each item
            for item in order.items:
                await self.product_service.update_inventory(
                    product_id=item.product_id,
                    change=item.quantity,
                    reason=f"Order {order.id} cancelled"
                )
            
            # Save the order
            saved_order = await self.save(order)
            
            # Publish any domain events
            await self.event_publisher.publish_all(order.clear_events())
            
            return saved_order, None
        except ValueError as e:
            return None, str(e)
    
    async def get_orders_for_user(
        self,
        user_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Order]:
        """
        Get all orders for a user.
        
        Args:
            user_id: The user ID
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of orders for the user
        """
        return await self.list(
            filters={"user_id": user_id},
            order_by=["-created_at"],  # Most recent first
            limit=limit,
            offset=offset
        )