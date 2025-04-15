# Domain-Specific Validation and API Integration

This document provides a comprehensive guide for implementing domain-specific validation rules in business objects and integrating them with API endpoints.

## Overview

Domain-specific validation ensures that your business objects adhere to the specific rules and constraints of your application domain. When combined with API integration, this provides a powerful way to enforce business rules at every level of your application.

## Implementing Domain-Specific Validation

### Basic Validation Structure

The UnoObj base class provides a `validate` method that you can override to implement domain-specific validation rules:

```python
from uno.obj import UnoObj
from uno.core.errors import ValidationContext

class MyObject(UnoObj[MyModel]):
    def validate(self, schema_name: str) -> ValidationContext:
        # Call parent validation first
        context = super().validate(schema_name)
        
        # Implement your validation rules here
        if hasattr(self, "some_field") and self.some_field is not None:
            if not self._is_valid_value(self.some_field):
                context.add_error(
                    field="some_field",
                    message="Invalid value for this field",
                    error_code="INVALID_VALUE"
                )
        
        return context
```

### Validation Context

The `ValidationContext` class is used to collect validation errors and provides several key features:

1. **Error Collection**: Add errors with field names, messages, and error codes
2. **Nested Validation**: Create sub-contexts for nested objects
3. **Error Checking**: Check if errors exist and raise exceptions

Example usage:

```python
def validate(self, schema_name: str) -> ValidationContext:
    context = super().validate(schema_name)
    
    # Direct field validation
    if hasattr(self, "price") and self.price <= 0:
        context.add_error(
            field="price",
            message="Price must be positive",
            error_code="INVALID_PRICE"
        )
    
    # Nested validation
    if hasattr(self, "address"):
        address_context = context.nested("address")
        if not self.address.city:
            address_context.add_error(
                field="city",
                message="City is required",
                error_code="REQUIRED_FIELD"
            )
    
    return context
```

### Common Validation Patterns

#### Required Fields

Validate that required fields are present and not empty:

```python
def validate(self, schema_name: str) -> ValidationContext:
    context = super().validate(schema_name)
    
    required_fields = ["name", "email", "phone"]
    for field in required_fields:
        if not hasattr(self, field) or not getattr(self, field):
            context.add_error(
                field=field,
                message=f"{field.capitalize()} is required",
                error_code="REQUIRED_FIELD"
            )
    
    return context
```

#### Format Validation

Validate that fields match specific formats using regular expressions:

```python
import re

def validate(self, schema_name: str) -> ValidationContext:
    context = super().validate(schema_name)
    
    # Email format validation
    if hasattr(self, "email") and self.email:
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, self.email):
            context.add_error(
                field="email",
                message="Invalid email format",
                error_code="INVALID_EMAIL"
            )
    
    # Phone format validation
    if hasattr(self, "phone") and self.phone:
        phone_pattern = r"^\d{3}-\d{3}-\d{4}$"
        if not re.match(phone_pattern, self.phone):
            context.add_error(
                field="phone",
                message="Phone must be in format XXX-XXX-XXXX",
                error_code="INVALID_PHONE"
            )
    
    return context
```

#### Range Validation

Validate that numeric values are within a valid range:

```python
def validate(self, schema_name: str) -> ValidationContext:
    context = super().validate(schema_name)
    
    # Age validation
    if hasattr(self, "age") and self.age is not None:
        if self.age < 0 or self.age > 120:
            context.add_error(
                field="age",
                message="Age must be between 0 and 120",
                error_code="INVALID_AGE"
            )
    
    # Price validation
    if hasattr(self, "price") and self.price is not None:
        if self.price < 0:
            context.add_error(
                field="price",
                message="Price cannot be negative",
                error_code="INVALID_PRICE"
            )
    
    return context
```

#### Relationship Validation

Validate relationships between fields:

```python
def validate(self, schema_name: str) -> ValidationContext:
    context = super().validate(schema_name)
    
    # Start date must be before end date
    if (hasattr(self, "start_date") and hasattr(self, "end_date") and 
        self.start_date and self.end_date and self.start_date > self.end_date):
        context.add_error(
            field="end_date",
            message="End date must be after start date",
            error_code="INVALID_DATE_RANGE"
        )
    
    # Shipping address required for physical products
    if hasattr(self, "product_type") and self.product_type == "physical":
        if not hasattr(self, "shipping_address") or not self.shipping_address:
            context.add_error(
                field="shipping_address",
                message="Shipping address is required for physical products",
                error_code="MISSING_SHIPPING_ADDRESS"
            )
    
    return context
```

#### Conditional Validation

Apply validation rules based on object state or other conditions:

```python
def validate(self, schema_name: str) -> ValidationContext:
    context = super().validate(schema_name)
    
    # Different validation depending on schema
    if schema_name == "edit_schema":
        # Additional validations for editing
        if hasattr(self, "id") and not self.id:
            context.add_error(
                field="id",
                message="ID is required for editing",
                error_code="MISSING_ID"
            )
    
    # Status-dependent validation
    if hasattr(self, "status") and self.status == "published":
        # Published items need additional validation
        if not hasattr(self, "published_date") or not self.published_date:
            context.add_error(
                field="published_date",
                message="Published date is required for published items",
                error_code="MISSING_PUBLISHED_DATE"
            )
    
    return context
```

## Integrating with API Endpoints

### Standard Error Handling

When integrating UnoObj validation with API endpoints, use a consistent pattern for error handling:

```python
from fastapi import FastAPI, HTTPException
from uno.core.errors.validation import ValidationError
from uno.core.errors import UnoError

app = FastAPI()

@app.post("/items")
async def create_item(item_data: dict):
    try:
        # Create item object
        item = Item(**item_data)
        
        # Validate item
        validation_context = item.validate("edit_schema")
        validation_context.raise_if_errors()
        
        # Save item
        await item.save()
        
        # Return success response
        return {"status": "success", "data": item.dict()}
    
    except ValidationError as e:
        # Return validation errors
        return {
            "status": "error",
            "message": "Validation failed",
            "errors": e.validation_errors
        }
    
    except UnoError as e:
        # Return other business errors
        return {
            "status": "error",
            "message": str(e),
            "code": e.error_code
        }
    
    except Exception as e:
        # Log unexpected errors and return generic message
        logger.exception("Unexpected error in create_item")
        return {"status": "error", "message": "An unexpected error occurred"}
```

### Business Logic in Endpoints

When implementing business logic in API endpoints, separate the logic into service classes for better organization and testability:

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# Product service with business logic
class ProductService:
    async def get_product(self, product_id: str):
        # Get product from database
        product = await Product.get(id=product_id)
        return product
    
    async def update_inventory(self, product_id: str, quantity_change: int):
        # Get product
        product = await self.get_product(product_id)
        
        # Calculate new inventory
        new_inventory = product.inventory_count + quantity_change
        
        # Validate new inventory
        if new_inventory < 0:
            raise UnoError(
                "Inventory cannot be negative",
                ErrorCode.BUSINESS_RULE,
                current_inventory=product.inventory_count,
                requested_change=quantity_change
            )
        
        # Update product
        product.inventory_count = new_inventory
        await product.save()
        
        return product

# Dependency for injecting the service
def get_product_service():
    return ProductService()

# API endpoint using the service
@app.post("/products/{product_id}/inventory")
async def update_inventory(
    product_id: str,
    data: dict,
    product_service: ProductService = Depends(get_product_service)
):
    try:
        quantity_change = data.get("quantity_change", 0)
        product = await product_service.update_inventory(product_id, quantity_change)
        return {"status": "success", "data": product.dict()}
    except UnoError as e:
        return {"status": "error", "message": str(e), "code": e.error_code}
    except Exception as e:
        return {"status": "error", "message": "An unexpected error occurred"}
```

## Testing Strategy

### Unit Testing Validation Rules

Unit test validation rules by creating test objects and checking the validation results:

```python
import pytest
from decimal import Decimal

def test_product_validation():
    """Test product validation rules."""
    # Test valid product
    product = Product(
        name="Test Product",
        price=Decimal("19.99"),
        sku="ABC-12345",
        category="Electronics",
        inventory_count=100
    )
    
    # Validate product
    validation_context = product.validate("edit_schema")
    assert not validation_context.has_errors()
    
    # Test invalid product
    invalid_product = Product(
        name="Invalid Product",
        price=Decimal("-10.00"),  # Invalid price
        sku="invalid-sku",  # Invalid SKU format
        category="Invalid",  # Invalid category
        inventory_count=100
    )
    
    # Validate product
    validation_context = invalid_product.validate("edit_schema")
    assert validation_context.has_errors()
    
    # Check specific errors
    errors = validation_context.errors
    error_fields = [error["field"] for error in errors]
    
    assert "price" in error_fields
    assert "sku" in error_fields
    assert "category" in error_fields
```

### Integration Testing API Endpoints

Integration test API endpoints by using a test client to send requests and checking the responses:

```python
from fastapi.testclient import TestClient

def test_create_product(test_client):
    """Test creating a product."""
    # Test valid product
    valid_product = {
        "name": "New Product",
        "price": "29.99",
        "sku": "ABC-12345",
        "category": "Electronics",
        "inventory_count": 100
    }
    
    response = test_client.post("/products", json=valid_product)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["name"] == "New Product"
    
    # Test invalid product
    invalid_product = {
        "name": "Invalid Product",
        "price": "-10.00",  # Invalid price
        "sku": "invalid",  # Invalid SKU
        "category": "Invalid",  # Invalid category
        "inventory_count": 100
    }
    
    response = test_client.post("/products", json=invalid_product)
    assert response.status_code == 200  # We handle the error in the endpoint
    data = response.json()
    assert data["status"] == "error"
    assert "errors" in data
    
    # Check specific errors
    error_fields = [error["field"] for error in data["errors"]]
    assert "price" in error_fields
    assert "sku" in error_fields
    assert "category" in error_fields
```

## Advanced Validation Techniques

### Custom Validation Decorators

Create decorators for commonly used validation rules:

```python
from functools import wraps
from uno.core.errors import ValidationContext

def validate_required_fields(fields):
    """Decorator for adding required field validation."""
    def decorator(validate_method):
        @wraps(validate_method)
        def wrapper(self, schema_name):
            context = validate_method(self, schema_name)
            
            for field in fields:
                if not hasattr(self, field) or not getattr(self, field):
                    context.add_error(
                        field=field,
                        message=f"{field.capitalize()} is required",
                        error_code="REQUIRED_FIELD"
                    )
            
            return context
        return wrapper
    return decorator

def validate_numeric_ranges(ranges):
    """Decorator for adding numeric range validation."""
    def decorator(validate_method):
        @wraps(validate_method)
        def wrapper(self, schema_name):
            context = validate_method(self, schema_name)
            
            for field, min_value, max_value in ranges:
                if hasattr(self, field) and getattr(self, field) is not None:
                    value = getattr(self, field)
                    if value < min_value or value > max_value:
                        context.add_error(
                            field=field,
                            message=f"{field.capitalize()} must be between {min_value} and {max_value}",
                            error_code="INVALID_RANGE"
                        )
            
            return context
        return wrapper
    return decorator

# Using the decorators
class Product(UnoObj[ProductModel]):
    @validate_required_fields(["name", "price", "sku"])
    @validate_numeric_ranges([("price", 0.01, 9999.99), ("inventory_count", 0, 9999)])
    def validate(self, schema_name: str) -> ValidationContext:
        # Call parent validation
        context = super().validate(schema_name)
        
        # Additional validation logic
        # ...
        
        return context
```

### Validation Factories

Create a validation factory for more complex validation rules:

```python
class ValidationRule:
    """Base class for validation rules."""
    
    def validate(self, obj, field, context):
        """
        Validate a field on an object.
        
        Args:
            obj: The object to validate
            field: The field name to validate
            context: The validation context
        """
        pass

class RequiredRule(ValidationRule):
    """Rule for required fields."""
    
    def validate(self, obj, field, context):
        if not hasattr(obj, field) or not getattr(obj, field):
            context.add_error(
                field=field,
                message=f"{field.capitalize()} is required",
                error_code="REQUIRED_FIELD"
            )

class RangeRule(ValidationRule):
    """Rule for numeric ranges."""
    
    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, obj, field, context):
        if hasattr(obj, field) and getattr(obj, field) is not None:
            value = getattr(obj, field)
            if value < self.min_value or value > self.max_value:
                context.add_error(
                    field=field,
                    message=f"{field.capitalize()} must be between {self.min_value} and {self.max_value}",
                    error_code="INVALID_RANGE"
                )

class PatternRule(ValidationRule):
    """Rule for pattern matching."""
    
    def __init__(self, pattern, error_message):
        self.pattern = pattern
        self.error_message = error_message
    
    def validate(self, obj, field, context):
        import re
        if hasattr(obj, field) and getattr(obj, field) is not None:
            value = getattr(obj, field)
            if isinstance(value, str) and not re.match(self.pattern, value):
                context.add_error(
                    field=field,
                    message=self.error_message,
                    error_code="INVALID_FORMAT"
                )

class ValidationFactory:
    """Factory for creating validation rules."""
    
    @staticmethod
    def required():
        return RequiredRule()
    
    @staticmethod
    def range(min_value, max_value):
        return RangeRule(min_value, max_value)
    
    @staticmethod
    def pattern(pattern, error_message):
        return PatternRule(pattern, error_message)
    
    @staticmethod
    def email():
        return PatternRule(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "Invalid email format"
        )
    
    @staticmethod
    def phone():
        return PatternRule(
            r"^\d{3}-\d{3}-\d{4}$",
            "Phone must be in format XXX-XXX-XXXX"
        )

# Using the validation factory
class Customer(UnoObj[CustomerModel]):
    def validate(self, schema_name: str) -> ValidationContext:
        context = super().validate(schema_name)
        
        # Create validation rules
        rules = {
            "first_name": [ValidationFactory.required()],
            "last_name": [ValidationFactory.required()],
            "email": [ValidationFactory.required(), ValidationFactory.email()],
            "phone": [ValidationFactory.phone()],
            "age": [ValidationFactory.range(18, 120)]
        }
        
        # Apply rules
        for field, field_rules in rules.items():
            for rule in field_rules:
                rule.validate(self, field, context)
        
        return context
```

## Real-World Example: E-commerce Domain

Here's a comprehensive example of domain-specific validation for a typical e-commerce application:

### Product Domain

```python
class Product(UnoObj[ProductModel]):
    """Product business object with domain-specific validation."""
    
    def validate(self, schema_name: str) -> ValidationContext:
        context = super().validate(schema_name)
        
        # Price validation
        if hasattr(self, "price") and self.price is not None:
            if self.price <= Decimal("0.00"):
                context.add_error(
                    field="price",
                    message="Price must be greater than zero",
                    error_code="INVALID_PRICE"
                )
        
        # SKU validation - must follow pattern ABC-12345
        if hasattr(self, "sku") and self.sku:
            sku_pattern = r"^[A-Z]{3}-\d{5}$"
            if not re.match(sku_pattern, self.sku):
                context.add_error(
                    field="sku",
                    message="SKU must follow pattern ABC-12345 (3 uppercase letters, dash, 5 digits)",
                    error_code="INVALID_SKU_FORMAT"
                )
        
        # Category validation
        if hasattr(self, "category") and self.category:
            valid_categories = ["Electronics", "Clothing", "Books", "Home", "Toys"]
            if self.category not in valid_categories:
                context.add_error(
                    field="category",
                    message=f"Invalid category. Must be one of {', '.join(valid_categories)}",
                    error_code="INVALID_CATEGORY"
                )
        
        # Weight validation for physical products
        if hasattr(self, "product_type") and self.product_type == "physical":
            if not hasattr(self, "weight") or self.weight is None:
                context.add_error(
                    field="weight",
                    message="Weight is required for physical products",
                    error_code="MISSING_WEIGHT"
                )
            elif self.weight <= 0:
                context.add_error(
                    field="weight",
                    message="Weight must be greater than zero",
                    error_code="INVALID_WEIGHT"
                )
        
        # Digital product validation
        if hasattr(self, "product_type") and self.product_type == "digital":
            if not hasattr(self, "download_url") or not self.download_url:
                context.add_error(
                    field="download_url",
                    message="Download URL is required for digital products",
                    error_code="MISSING_DOWNLOAD_URL"
                )
        
        # Release date validation
        if hasattr(self, "release_date") and self.release_date:
            today = date.today()
            if self.release_date < today and not self.id:
                context.add_error(
                    field="release_date",
                    message="Release date cannot be in the past for new products",
                    error_code="INVALID_RELEASE_DATE"
                )
        
        return context
```

### Order Domain

```python
class Order(UnoObj[OrderModel]):
    """Order business object with domain-specific validation."""
    
    # Order status constants
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    
    def validate(self, schema_name: str) -> ValidationContext:
        context = super().validate(schema_name)
        
        # Status validation
        if hasattr(self, "status") and self.status:
            valid_statuses = [
                self.STATUS_PENDING, self.STATUS_CONFIRMED, self.STATUS_PROCESSING,
                self.STATUS_SHIPPED, self.STATUS_DELIVERED, self.STATUS_CANCELLED
            ]
            if self.status not in valid_statuses:
                context.add_error(
                    field="status",
                    message=f"Invalid status. Must be one of {', '.join(valid_statuses)}",
                    error_code="INVALID_STATUS"
                )
        
        # Item validation
        if hasattr(self, "items") and self.items:
            if len(self.items) == 0:
                context.add_error(
                    field="items",
                    message="Order must have at least one item",
                    error_code="EMPTY_ORDER"
                )
        
        # Shipping validation for physical products
        if hasattr(self, "contains_physical_items") and self.contains_physical_items:
            # Check shipping address
            if not hasattr(self, "shipping_address") or not self.shipping_address:
                context.add_error(
                    field="shipping_address",
                    message="Shipping address is required for orders with physical items",
                    error_code="MISSING_SHIPPING_ADDRESS"
                )
            
            # Check shipping method
            if not hasattr(self, "shipping_method") or not self.shipping_method:
                context.add_error(
                    field="shipping_method",
                    message="Shipping method is required for orders with physical items",
                    error_code="MISSING_SHIPPING_METHOD"
                )
        
        # Payment validation for non-pending orders
        if (hasattr(self, "status") and self.status != self.STATUS_PENDING and 
            (not hasattr(self, "payment") or not self.payment)):
            context.add_error(
                field="payment",
                message="Payment is required for non-pending orders",
                error_code="MISSING_PAYMENT"
            )
        
        # Tracking number validation for shipped orders
        if (hasattr(self, "status") and self.status == self.STATUS_SHIPPED and 
            (not hasattr(self, "tracking_number") or not self.tracking_number)):
            context.add_error(
                field="tracking_number",
                message="Tracking number is required for shipped orders",
                error_code="MISSING_TRACKING_NUMBER"
            )
        
        return context
    
    async def confirm(self) -> bool:
        """Confirm the order."""
        if self.status != self.STATUS_PENDING:
            raise UnoError(
                f"Cannot confirm order that is not pending (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=self.STATUS_PENDING
            )
        
        if not hasattr(self, "payment") or not self.payment:
            raise UnoError(
                "Payment is required to confirm order",
                ErrorCode.VALIDATION_ERROR,
                field="payment"
            )
        
        # Update status
        self.status = self.STATUS_CONFIRMED
        await self.save()
        return True
    
    async def ship(self, tracking_number: str) -> bool:
        """Mark order as shipped."""
        if self.status != self.STATUS_CONFIRMED and self.status != self.STATUS_PROCESSING:
            raise UnoError(
                f"Cannot ship order that is not confirmed or processing (current status: {self.status})",
                ErrorCode.BUSINESS_RULE,
                current_status=self.status,
                expected_status=[self.STATUS_CONFIRMED, self.STATUS_PROCESSING]
            )
        
        # Update status
        self.status = self.STATUS_SHIPPED
        self.tracking_number = tracking_number
        await self.save()
        return True
```

## API Integration Example

```python
from fastapi import FastAPI, Depends, HTTPException
from typing import Dict, List, Optional, Any

app = FastAPI()

# Product service
class ProductService:
    async def get_product(self, product_id: str) -> Product:
        """Get a product by ID."""
        try:
            return await Product.get(id=product_id)
        except UnoError as e:
            if e.error_code == ErrorCode.RESOURCE_NOT_FOUND:
                raise HTTPException(404, f"Product not found: {product_id}")
            raise
    
    async def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create a new product."""
        # Create product
        product = Product(**product_data)
        
        # Validate product
        validation_context = product.validate("edit_schema")
        validation_context.raise_if_errors()
        
        # Save product
        await product.save()
        return product
    
    async def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Product:
        """Update an existing product."""
        # Get product
        product = await self.get_product(product_id)
        
        # Update product attributes
        for key, value in product_data.items():
            setattr(product, key, value)
        
        # Validate product
        validation_context = product.validate("edit_schema")
        validation_context.raise_if_errors()
        
        # Save product
        await product.save()
        return product
    
    async def list_products(self, category: Optional[str] = None, active_only: bool = True) -> List[Product]:
        """List products with optional filtering."""
        # Create filter
        filters = {}
        if category:
            filters["category"] = category
        if active_only:
            filters["is_active"] = True
        
        # Get products
        return await Product.filter(filters)
    
    async def reserve_inventory(self, product_id: str, quantity: int) -> bool:
        """Reserve inventory for a product."""
        if quantity <= 0:
            raise UnoError(
                "Quantity must be greater than zero",
                ErrorCode.VALIDATION_ERROR,
                field="quantity"
            )
        
        # Get product
        product = await self.get_product(product_id)
        
        # Reserve inventory
        return await product.reserve_inventory(quantity)

# Order service
class OrderService:
    def __init__(self, product_service: ProductService):
        self.product_service = product_service
    
    async def create_order(self, order_data: Dict[str, Any]) -> Order:
        """Create a new order."""
        # Extract items
        items = order_data.pop("items", [])
        if not items:
            raise UnoError(
                "Order must have at least one item",
                ErrorCode.VALIDATION_ERROR,
                field="items"
            )
        
        # Check if order contains physical items
        physical_items = False
        for item in items:
            product = await self.product_service.get_product(item["product_id"])
            if getattr(product, "product_type", "physical") == "physical":
                physical_items = True
                break
        
        # Create order
        order_data["contains_physical_items"] = physical_items
        order_data["status"] = Order.STATUS_PENDING
        order = Order(**order_data)
        
        # Validate order
        validation_context = order.validate("edit_schema")
        validation_context.raise_if_errors()
        
        # Save order
        await order.save()
        
        # Add items to order
        for item in items:
            await self._add_item_to_order(order.id, item)
        
        return order
    
    async def _add_item_to_order(self, order_id: str, item_data: Dict[str, Any]) -> OrderItem:
        """Add an item to an order."""
        # Get product
        product = await self.product_service.get_product(item_data["product_id"])
        
        # Check quantity
        quantity = item_data.get("quantity", 1)
        if quantity <= 0:
            raise UnoError(
                "Quantity must be greater than zero",
                ErrorCode.VALIDATION_ERROR,
                field="quantity"
            )
        
        # Reserve inventory
        await self.product_service.reserve_inventory(product.id, quantity)
        
        # Create order item
        item = OrderItem(
            order_id=order_id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price,
            subtotal=product.price * quantity
        )
        
        # Validate item
        validation_context = item.validate("edit_schema")
        validation_context.raise_if_errors()
        
        # Save item
        await item.save()
        return item

# Dependency injection
def get_product_service():
    return ProductService()

def get_order_service(product_service: ProductService = Depends(get_product_service)):
    return OrderService(product_service)

# API endpoints
@app.post("/products")
async def create_product(
    product_data: Dict[str, Any],
    product_service: ProductService = Depends(get_product_service)
):
    try:
        product = await product_service.create_product(product_data)
        return {"status": "success", "data": product.dict()}
    except ValidationError as e:
        return {"status": "error", "message": str(e), "errors": e.validation_errors}
    except UnoError as e:
        return {"status": "error", "message": str(e), "code": e.error_code}
    except Exception as e:
        return {"status": "error", "message": "An unexpected error occurred"}

@app.post("/orders")
async def create_order(
    order_data: Dict[str, Any],
    order_service: OrderService = Depends(get_order_service)
):
    try:
        order = await order_service.create_order(order_data)
        return {"status": "success", "data": order.dict()}
    except ValidationError as e:
        return {"status": "error", "message": str(e), "errors": e.validation_errors}
    except UnoError as e:
        return {"status": "error", "message": str(e), "code": e.error_code}
    except Exception as e:
        return {"status": "error", "message": "An unexpected error occurred"}
```

## Conclusion

Domain-specific validation and API integration are essential for building robust applications that enforce business rules at every level. By implementing these patterns in your UnoObj business objects and API endpoints, you can ensure data integrity, improve error handling, and create a better user experience.

## See Also

- [UnoObj Reference](unoobj.md) - Core UnoObj class documentation
- [Business Logic Best Practices](best_practices.md) - General best practices for business logic
- [Extending UnoObj](extending_unoobj.md) - Patterns for extending UnoObj
- [API Layer](../api/overview.md) - API layer documentation