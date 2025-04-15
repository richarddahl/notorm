# Extending UnoObj for Custom Business Needs

This document provides comprehensive guidance on extending the UnoObj class to meet specific business requirements. It covers advanced customization, inheritance patterns, composition strategies, and alternative approaches.

## Core Extension Patterns

### Inheritance vs Composition

When extending UnoObj, you must decide between inheritance and composition:

**Inheritance** is appropriate when:
- You're adding business logic specific to a domain entity
- You need to override core behavior like validation or serialization
- The extended functionality is integral to the object's identity

**Composition** is better when:
- Functionality can be reused across multiple object types
- Extension is focused on a specific capability or concern
- Implementation may change independently of the object

## Inheritance-Based Extensions

### Basic Custom UnoObj

Start with a basic customization:

```python
from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchemaConfig
from datetime import datetime
from typing import Optional

# Base model
class ProductModel(UnoModel):
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    category_id: Mapped[PostgresTypes.String26] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    inventory_count: Mapped[int] = mapped_column(nullable=False, default=0)

# Basic Product business object
class Product(UnoObj[ProductModel]):
    """Business object for products."""
    
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
        "list_schema": UnoSchemaConfig(include_fields={"id", "name", "price", "category_id", "active"})
    }
    
    async def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        return self.inventory_count > 0
    
    async def reserve_inventory(self, quantity: int) -> bool:
        """Reserve inventory for an order."""
        if self.inventory_count < quantity:
            return False
        
        self.inventory_count -= quantity
        await self.save()
        return True
```

### Specialized Product Types

Create specialized product types by extending the base product class:

```python
class PhysicalProductModel(ProductModel):
    __tablename__ = "physical_products"
    
    weight: Mapped[float] = mapped_column(nullable=True)
    dimensions: Mapped[str] = mapped_column(nullable=True)
    shipping_class: Mapped[str] = mapped_column(nullable=True)

class PhysicalProduct(Product):
    """Business object for physical products with shipping attributes."""
    
    # Override model to use the physical product model
    model = PhysicalProductModel
    
    # Add additional schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
        "list_schema": UnoSchemaConfig(include_fields={"id", "name", "price", "category_id", "active"}),
        "shipping_schema": UnoSchemaConfig(include_fields={"id", "name", "weight", "dimensions", "shipping_class"})
    }
    
    async def calculate_shipping_cost(self, shipping_zone: str) -> float:
        """Calculate shipping cost based on weight and dimensions."""
        base_cost = 5.0  # Base shipping cost
        
        # Weight-based cost
        if hasattr(self, "weight") and self.weight:
            weight_cost = self.weight * 0.1  # $0.10 per unit of weight
        else:
            weight_cost = 0
        
        # Zone-based multiplier
        zone_multipliers = {
            "local": 1.0,
            "domestic": 1.5,
            "international": 3.0
        }
        zone_multiplier = zone_multipliers.get(shipping_zone, 1.5)
        
        # Shipping class adjustments
        class_adjustments = {
            "standard": 0,
            "expedited": 10.0,
            "overnight": 25.0
        }
        class_adjustment = class_adjustments.get(self.shipping_class, 0)
        
        # Calculate total shipping cost
        total_cost = (base_cost + weight_cost) * zone_multiplier + class_adjustment
        return round(total_cost, 2)
    
    async def is_shippable(self, destination: str) -> bool:
        """Check if product can be shipped to destination."""
        # Implementation would check shipping restrictions
        restricted_destinations = ["Antarctica", "North Korea"]
        return destination not in restricted_destinations

class DigitalProductModel(ProductModel):
    __tablename__ = "digital_products"
    
    file_size: Mapped[int] = mapped_column(nullable=True)  # Size in KB
    download_url: Mapped[str] = mapped_column(nullable=True)
    license_type: Mapped[str] = mapped_column(nullable=True)

class DigitalProduct(Product):
    """Business object for digital products with download attributes."""
    
    # Override model to use the digital product model
    model = DigitalProductModel
    
    # Add additional schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at"}),
        "list_schema": UnoSchemaConfig(include_fields={"id", "name", "price", "category_id", "active"}),
        "download_schema": UnoSchemaConfig(include_fields={"id", "name", "download_url", "license_type"})
    }
    
    async def generate_download_link(self, user_id: str, expiry_hours: int = 24) -> str:
        """Generate a time-limited download link for the user."""
        from datetime import datetime, timedelta
        import hashlib
        import base64
        
        # Generate expiry timestamp
        expiry_time = datetime.now() + timedelta(hours=expiry_hours)
        expiry_timestamp = int(expiry_time.timestamp())
        
        # Create signature
        signature_data = f"{self.id}:{user_id}:{expiry_timestamp}"
        signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
        # Create download token
        token_data = f"{self.id}:{user_id}:{expiry_timestamp}:{signature}"
        token = base64.urlsafe_b64encode(token_data.encode()).decode()
        
        # Construct download URL
        download_url = f"/api/download/{token}"
        return download_url
    
    async def reserve_inventory(self, quantity: int) -> bool:
        """Override to always return True for digital products."""
        # Digital products have unlimited inventory
        return True
```

### Extending with Mixins

Use mixins to add reusable functionality:

```python
class AuditableMixin:
    """Mixin to add auditing capabilities to UnoObj classes."""
    
    async def log_access(self, user_id: str, action: str) -> None:
        """Log access to this object."""
        from datetime import datetime
        
        # Create audit log entry
        from your_module import AuditLog
        
        audit_log = AuditLog(
            object_id=self.id,
            object_type=self.__class__.__name__,
            user_id=user_id,
            action=action,
            timestamp=datetime.now()
        )
        await audit_log.save()
    
    @classmethod
    async def get_audit_trail(cls, object_id: str) -> list:
        """Get audit trail for this object."""
        from your_module import AuditLog
        
        audit_logs = await AuditLog.filter({
            "object_id": object_id,
            "object_type": cls.__name__
        })
        return audit_logs

class VersionedMixin:
    """Mixin to add versioning capabilities to UnoObj classes."""
    
    version: int = 1  # Version field
    
    async def save(self) -> None:
        """Override save to handle versioning."""
        # Increment version on save
        if hasattr(self, "version"):
            self.version += 1
        
        # Archive current version before saving
        await self._archive_version()
        
        # Call parent save method
        await super().save()
    
    async def _archive_version(self) -> None:
        """Archive the current version of the object."""
        from your_module import ObjectVersion
        
        # Convert object to dict for storage
        data = self.dict()
        
        # Create version record
        version_record = ObjectVersion(
            object_id=self.id,
            object_type=self.__class__.__name__,
            version=self.version,
            data=data,
            created_at=datetime.now()
        )
        await version_record.save()
    
    @classmethod
    async def get_version(cls, object_id: str, version: int) -> Optional['UnoObj']:
        """Get specific version of an object."""
        from your_module import ObjectVersion
        
        # Retrieve version record
        version_record = await ObjectVersion.filter({
            "object_id": object_id,
            "object_type": cls.__name__,
            "version": version
        })
        
        if not version_record:
            return None
        
        # Construct object from version data
        instance = cls(**version_record[0].data)
        return instance
    
    @classmethod
    async def get_version_history(cls, object_id: str) -> list:
        """Get version history for this object."""
        from your_module import ObjectVersion
        
        version_records = await ObjectVersion.filter({
            "object_id": object_id,
            "object_type": cls.__name__
        })
        return version_records

# Combined usage with both mixins
class Document(UnoObj[DocumentModel], AuditableMixin, VersionedMixin):
    """Business object for documents with auditing and versioning."""
    
    async def view(self, user_id: str) -> str:
        """View document and log access."""
        # Log the view action
        await self.log_access(user_id, "view")
        
        # Return document content
        return self.content
    
    async def update_content(self, user_id: str, new_content: str) -> None:
        """Update document content with versioning and auditing."""
        # Update the content
        self.content = new_content
        
        # Save (versioning happens in overridden save method)
        await self.save()
        
        # Log the update action
        await self.log_access(user_id, "update")
```

### Complex Validation Extensions

Extend validation capabilities:

```python
from uno.core.errors import ValidationContext, ValidationError

class ValidatableMixin:
    """Mixin to add enhanced validation capabilities to UnoObj classes."""
    
    # Store validation rules
    _validation_rules: ClassVar[Dict[str, List[Callable]]] = {}
    
    @classmethod
    def add_validation_rule(cls, field: str, rule: Callable[[Any], Optional[str]]) -> None:
        """Add a validation rule for a field."""
        if field not in cls._validation_rules:
            cls._validation_rules[field] = []
        cls._validation_rules[field].append(rule)
    
    def validate(self, schema_name: str) -> ValidationContext:
        """Enhanced validation with custom rules."""
        # Call parent validation
        context = super().validate(schema_name)
        
        # Apply custom validation rules
        for field, rules in self._validation_rules.items():
            if hasattr(self, field):
                value = getattr(self, field)
                for rule in rules:
                    error_message = rule(value)
                    if error_message:
                        context.add_error(
                            field=field,
                            message=error_message,
                            error_code="CUSTOM_VALIDATION_ERROR"
                        )
        
        return context

# Define reusable validation rules
def email_validation_rule(value: str) -> Optional[str]:
    """Validate email format."""
    if not value:
        return None
    
    if "@" not in value or "." not in value:
        return "Invalid email format"
    
    return None

def min_length_rule(min_length: int) -> Callable[[str], Optional[str]]:
    """Rule factory for minimum length validation."""
    def validate(value: str) -> Optional[str]:
        if not value:
            return None
        
        if len(value) < min_length:
            return f"Value must be at least {min_length} characters long"
        
        return None
    
    return validate

def max_length_rule(max_length: int) -> Callable[[str], Optional[str]]:
    """Rule factory for maximum length validation."""
    def validate(value: str) -> Optional[str]:
        if not value:
            return None
        
        if len(value) > max_length:
            return f"Value must be at most {max_length} characters long"
        
        return None
    
    return validate

# Enhanced User class with validation
class EnhancedUser(UnoObj[UserModel], ValidatableMixin):
    """User business object with enhanced validation."""
    
    # Add validation rules
    add_validation_rule("email", email_validation_rule)
    add_validation_rule("username", min_length_rule(3))
    add_validation_rule("username", max_length_rule(50))
    add_validation_rule("password", min_length_rule(8))
    
    # Additional password complexity rule
    @classmethod
    def password_complexity_rule(cls, value: str) -> Optional[str]:
        """Validate password complexity."""
        if not value:
            return None
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in value):
            return "Password must contain at least one uppercase letter"
        
        # Check for at least one digit
        if not any(c.isdigit() for c in value):
            return "Password must contain at least one digit"
        
        # Check for at least one special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/"
        if not any(c in special_chars for c in value):
            return "Password must contain at least one special character"
        
        return None
    
    # Add the password complexity rule
    add_validation_rule("password", password_complexity_rule)
```

## Composition-Based Extensions

### Using Service Objects

Implement service objects to extend functionality without inheritance:

```python
from typing import Generic, TypeVar, Type

T = TypeVar('T', bound=UnoObj)

class ProductService(Generic[T]):
    """Service for working with product objects."""
    
    def __init__(self, product_class: Type[T]):
        self.product_class = product_class
    
    async def search_by_category(self, category_id: str, active_only: bool = True) -> List[T]:
        """Search for products by category."""
        filters = {"category_id": category_id}
        
        if active_only:
            filters["active"] = True
        
        return await self.product_class.filter(filters)
    
    async def get_top_products(self, limit: int = 10) -> List[T]:
        """Get top products by sales."""
        # This would typically involve a more complex query
        # For example, joining with sales data or using a custom query
        
        # Simplified implementation
        filters = {"active": True}
        sorting = ["-sales_count"]  # Assuming there's a sales_count field
        
        return await self.product_class.filter(filters, sort=sorting, limit=limit)
    
    async def update_prices(self, category_id: str, price_adjustment: float) -> int:
        """Update prices for products in a category."""
        # Get products in category
        products = await self.search_by_category(category_id)
        
        # Update prices
        count = 0
        for product in products:
            # Apply price adjustment
            product.price = product.price * (1 + price_adjustment)
            await product.save()
            count += 1
        
        return count

# Usage with multiple product types
physical_product_service = ProductService(PhysicalProduct)
digital_product_service = ProductService(DigitalProduct)

# Get top physical products
top_physical_products = await physical_product_service.get_top_products(5)

# Get top digital products
top_digital_products = await digital_product_service.get_top_products(5)
```

### Delegating to Helpers

Use delegate objects to handle specific concerns:

```python
class InventoryManager:
    """Helper class for inventory management."""
    
    def __init__(self, product: Product):
        self.product = product
    
    async def check_availability(self, quantity: int) -> bool:
        """Check if the requested quantity is available."""
        return self.product.inventory_count >= quantity
    
    async def reserve(self, quantity: int) -> bool:
        """Reserve inventory for an order."""
        if not await self.check_availability(quantity):
            return False
        
        self.product.inventory_count -= quantity
        await self.product.save()
        return True
    
    async def release(self, quantity: int) -> bool:
        """Release previously reserved inventory."""
        self.product.inventory_count += quantity
        await self.product.save()
        return True
    
    async def restock(self, quantity: int) -> bool:
        """Restock product inventory."""
        self.product.inventory_count += quantity
        await self.product.save()
        return True

class PricingManager:
    """Helper class for pricing calculations."""
    
    def __init__(self, product: Product):
        self.product = product
    
    async def get_base_price(self) -> Decimal:
        """Get the base price for the product."""
        return self.product.price
    
    async def calculate_price_with_tax(self, tax_rate: Decimal) -> Decimal:
        """Calculate price including tax."""
        return self.product.price * (Decimal('1.0') + tax_rate)
    
    async def calculate_discounted_price(self, discount_percentage: Decimal) -> Decimal:
        """Calculate discounted price."""
        discount_factor = Decimal('1.0') - (discount_percentage / Decimal('100.0'))
        return self.product.price * discount_factor
    
    async def apply_discount(self, discount_percentage: Decimal) -> None:
        """Apply a permanent discount to the product."""
        discounted_price = await self.calculate_discounted_price(discount_percentage)
        self.product.price = discounted_price
        await self.product.save()

# Enhanced Product with managers
class EnhancedProduct(Product):
    """Product with enhanced capabilities through managers."""
    
    def __init__(self, **data):
        super().__init__(**data)
        self.inventory = InventoryManager(self)
        self.pricing = PricingManager(self)
    
    # Rest of the class implementation
```

### Feature Toggles and Extensions

Create dynamic extension mechanisms:

```python
class FeatureToggle:
    """Feature toggle for enabling/disabling features."""
    
    _features: ClassVar[Dict[str, bool]] = {}
    
    @classmethod
    def enable_feature(cls, feature_name: str) -> None:
        """Enable a feature."""
        cls._features[feature_name] = True
    
    @classmethod
    def disable_feature(cls, feature_name: str) -> None:
        """Disable a feature."""
        cls._features[feature_name] = False
    
    @classmethod
    def is_enabled(cls, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return cls._features.get(feature_name, False)

class ExtensibleProduct(Product):
    """Product with extensible features."""
    
    _extensions: Dict[str, Any] = {}
    
    def add_extension(self, name: str, extension: Any) -> None:
        """Add an extension to this product."""
        self._extensions[name] = extension
    
    def get_extension(self, name: str) -> Optional[Any]:
        """Get an extension by name."""
        return self._extensions.get(name)
    
    def has_extension(self, name: str) -> bool:
        """Check if an extension exists."""
        return name in self._extensions
    
    async def process_order(self, quantity: int) -> bool:
        """Process an order with extensions."""
        # Base processing
        if not await self.reserve_inventory(quantity):
            return False
        
        # Run through extensions
        for name, extension in self._extensions.items():
            if hasattr(extension, 'on_order'):
                result = await extension.on_order(self, quantity)
                if not result:
                    # Rollback inventory reservation
                    await self.release_inventory(quantity)
                    return False
        
        return True

# Example extensions

class TaxExtension:
    """Extension for tax calculations."""
    
    def __init__(self, tax_rate: Decimal):
        self.tax_rate = tax_rate
    
    async def calculate_tax(self, product: Product, quantity: int) -> Decimal:
        """Calculate tax for a product order."""
        return product.price * quantity * self.tax_rate
    
    async def on_order(self, product: Product, quantity: int) -> bool:
        """Handle order processing."""
        # Just log tax information for now
        tax_amount = await self.calculate_tax(product, quantity)
        print(f"Tax amount for {product.name}: {tax_amount}")
        return True

class AnalyticsExtension:
    """Extension for tracking analytics."""
    
    async def track_view(self, product: Product) -> None:
        """Track product view."""
        # Implementation would send analytics event
        print(f"Tracking view for {product.name}")
    
    async def on_order(self, product: Product, quantity: int) -> bool:
        """Handle order tracking."""
        # Implementation would send analytics event
        print(f"Tracking order for {product.name}, quantity: {quantity}")
        return True

# Usage
product = ExtensibleProduct(name="Extensible Product", price=Decimal("29.99"))
await product.save()

# Add extensions
product.add_extension("tax", TaxExtension(Decimal("0.07")))
product.add_extension("analytics", AnalyticsExtension())

# Process an order
success = await product.process_order(2)
```

## Protocol-Based Extensions

### Protocol Implementation

Define protocols for type-safe extensions:

```python
from typing import Protocol, runtime_checkable
from decimal import Decimal

@runtime_checkable
class PricingProtocol(Protocol):
    """Protocol for pricing functionality."""
    
    async def get_price(self) -> Decimal:
        """Get the price."""
        ...
    
    async def calculate_tax(self, tax_rate: Decimal) -> Decimal:
        """Calculate tax for the price."""
        ...

@runtime_checkable
class InventoryProtocol(Protocol):
    """Protocol for inventory functionality."""
    
    async def check_availability(self, quantity: int) -> bool:
        """Check if the requested quantity is available."""
        ...
    
    async def reserve(self, quantity: int) -> bool:
        """Reserve the requested quantity."""
        ...

@runtime_checkable
class ShippableProtocol(Protocol):
    """Protocol for shippable items."""
    
    async def get_weight(self) -> float:
        """Get the weight of the item."""
        ...
    
    async def get_dimensions(self) -> tuple:
        """Get the dimensions of the item."""
        ...
    
    async def calculate_shipping_cost(self, shipping_zone: str) -> Decimal:
        """Calculate shipping cost for the item."""
        ...

class ProtocolProduct(UnoObj[ProductModel]):
    """Product implementing multiple protocols."""
    
    # Implement PricingProtocol
    async def get_price(self) -> Decimal:
        """Get the price."""
        return self.price
    
    async def calculate_tax(self, tax_rate: Decimal) -> Decimal:
        """Calculate tax for the price."""
        return self.price * tax_rate
    
    # Implement InventoryProtocol
    async def check_availability(self, quantity: int) -> bool:
        """Check if the requested quantity is available."""
        return self.inventory_count >= quantity
    
    async def reserve(self, quantity: int) -> bool:
        """Reserve the requested quantity."""
        if not await self.check_availability(quantity):
            return False
        
        self.inventory_count -= quantity
        await self.save()
        return True

class ProtocolPhysicalProduct(ProtocolProduct):
    """Physical product implementing ShippableProtocol."""
    
    # Implement ShippableProtocol
    async def get_weight(self) -> float:
        """Get the weight of the item."""
        return self.weight
    
    async def get_dimensions(self) -> tuple:
        """Get the dimensions of the item."""
        # Parse dimensions string (e.g., "10x5x3")
        dimensions = self.dimensions.split("x")
        return tuple(float(d) for d in dimensions)
    
    async def calculate_shipping_cost(self, shipping_zone: str) -> Decimal:
        """Calculate shipping cost for the item."""
        # Implementation of shipping cost calculation
        # ...
        return Decimal("5.99")

# Generic function that works with any object implementing the protocols
async def process_order(
    product: PricingProtocol & InventoryProtocol,
    quantity: int,
    tax_rate: Decimal
) -> Dict[str, Decimal]:
    """Process an order for any product implementing the required protocols."""
    # Check availability
    if hasattr(product, "check_availability"):
        if not await product.check_availability(quantity):
            raise ValueError("Product not available in requested quantity")
    
    # Calculate base price
    base_price = await product.get_price() * Decimal(quantity)
    
    # Calculate tax
    tax = await product.calculate_tax(tax_rate) * Decimal(quantity)
    
    # Calculate shipping if applicable
    shipping = Decimal("0.00")
    if isinstance(product, ShippableProtocol):
        shipping = await product.calculate_shipping_cost("domestic")
    
    # Reserve inventory if applicable
    if hasattr(product, "reserve"):
        await product.reserve(quantity)
    
    # Return the order details
    return {
        "base_price": base_price,
        "tax": tax,
        "shipping": shipping,
        "total": base_price + tax + shipping
    }
```

## Advanced Extension Techniques

### Factory Pattern

Create factory methods for object creation:

```python
class ProductFactory:
    """Factory for creating product objects."""
    
    @classmethod
    async def create_product(cls, product_type: str, **data) -> Product:
        """Create a product of the specified type."""
        product_classes = {
            "physical": PhysicalProduct,
            "digital": DigitalProduct,
            "subscription": SubscriptionProduct
        }
        
        if product_type not in product_classes:
            raise ValueError(f"Unknown product type: {product_type}")
        
        product_class = product_classes[product_type]
        product = product_class(**data)
        await product.save()
        
        return product
    
    @classmethod
    async def create_from_template(cls, template_id: str, **override_data) -> Product:
        """Create a product from a template."""
        # Get the template
        template = await ProductTemplate.get(id=template_id)
        
        # Create product data by combining template with overrides
        product_data = template.to_dict()
        product_data.update(override_data)
        
        # Create product
        return await cls.create_product(template.product_type, **product_data)
```

### Plugin Architecture

Implement a plugin architecture for extensibility:

```python
from typing import Dict, List, Type, Callable, Any
import inspect

class ProductPlugin:
    """Base class for product plugins."""
    
    # Hook points
    async def before_save(self, product: Product) -> None:
        """Hook called before a product is saved."""
        pass
    
    async def after_save(self, product: Product) -> None:
        """Hook called after a product is saved."""
        pass
    
    async def before_delete(self, product: Product) -> None:
        """Hook called before a product is deleted."""
        pass
    
    async def after_delete(self, product: Product) -> None:
        """Hook called after a product is deleted."""
        pass
    
    async def on_price_change(self, product: Product, old_price: Decimal, new_price: Decimal) -> None:
        """Hook called when a product's price changes."""
        pass
    
    async def on_inventory_change(self, product: Product, old_count: int, new_count: int) -> None:
        """Hook called when a product's inventory changes."""
        pass

class ProductPluginManager:
    """Manager for product plugins."""
    
    _plugins: List[ProductPlugin] = []
    _hook_cache: Dict[str, List[Callable]] = {}
    
    @classmethod
    def register_plugin(cls, plugin: ProductPlugin) -> None:
        """Register a plugin."""
        cls._plugins.append(plugin)
        cls._build_hook_cache()
    
    @classmethod
    def _build_hook_cache(cls) -> None:
        """Build cache of hook methods."""
        cls._hook_cache = {}
        
        # Find all hook methods in the ProductPlugin class
        hook_methods = [
            name for name, _ in inspect.getmembers(ProductPlugin, predicate=inspect.isfunction)
            if not name.startswith("_")
        ]
        
        # Build cache for each hook
        for hook_name in hook_methods:
            cls._hook_cache[hook_name] = [
                getattr(plugin, hook_name) for plugin in cls._plugins
                if hasattr(plugin, hook_name)
            ]
    
    @classmethod
    async def run_hook(cls, hook_name: str, *args, **kwargs) -> None:
        """Run a hook with all registered plugins."""
        if hook_name not in cls._hook_cache:
            return
        
        for hook in cls._hook_cache[hook_name]:
            await hook(*args, **kwargs)

class PluggableProduct(Product):
    """Product with plugin support."""
    
    async def save(self) -> None:
        """Save the product with plugin hooks."""
        # Run before_save hook
        await ProductPluginManager.run_hook("before_save", self)
        
        # Check if price has changed
        if self.id:
            try:
                old_product = await self.__class__.get(id=self.id)
                if old_product.price != self.price:
                    await ProductPluginManager.run_hook(
                        "on_price_change", self, old_product.price, self.price
                    )
                
                if old_product.inventory_count != self.inventory_count:
                    await ProductPluginManager.run_hook(
                        "on_inventory_change", self, old_product.inventory_count, self.inventory_count
                    )
            except Exception:
                # If we can't get the old product, continue without running change hooks
                pass
        
        # Save the product
        await super().save()
        
        # Run after_save hook
        await ProductPluginManager.run_hook("after_save", self)
    
    async def delete(self) -> None:
        """Delete the product with plugin hooks."""
        # Run before_delete hook
        await ProductPluginManager.run_hook("before_delete", self)
        
        # Delete the product
        await super().delete()
        
        # Run after_delete hook
        await ProductPluginManager.run_hook("after_delete", self)

# Example plugins

class AuditPlugin(ProductPlugin):
    """Plugin for auditing product changes."""
    
    async def after_save(self, product: Product) -> None:
        """Log product save event."""
        # Implementation would log to audit system
        print(f"Audit: Product {product.id} - {product.name} was saved")
    
    async def after_delete(self, product: Product) -> None:
        """Log product delete event."""
        print(f"Audit: Product {product.id} - {product.name} was deleted")
    
    async def on_price_change(self, product: Product, old_price: Decimal, new_price: Decimal) -> None:
        """Log price change event."""
        print(f"Audit: Product {product.id} price changed from {old_price} to {new_price}")

class NotificationPlugin(ProductPlugin):
    """Plugin for sending notifications on product changes."""
    
    async def on_inventory_change(self, product: Product, old_count: int, new_count: int) -> None:
        """Send notification when inventory changes."""
        # Check for low inventory
        if new_count < 10 and old_count >= 10:
            # Implementation would send alert
            print(f"Alert: Product {product.name} inventory low: {new_count}")
        
        # Check for out of stock
        if new_count == 0 and old_count > 0:
            print(f"Alert: Product {product.name} is out of stock")

# Register plugins
ProductPluginManager.register_plugin(AuditPlugin())
ProductPluginManager.register_plugin(NotificationPlugin())
```

### Event-Driven Extensions

Use events for loose coupling:

```python
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProductEvent:
    """Base class for product events."""
    product_id: str
    timestamp: datetime = datetime.now()

@dataclass
class ProductCreatedEvent(ProductEvent):
    """Event for product creation."""
    name: str
    price: Decimal

@dataclass
class ProductUpdatedEvent(ProductEvent):
    """Event for product updates."""
    changes: Dict[str, Any]

@dataclass
class ProductDeletedEvent(ProductEvent):
    """Event for product deletion."""
    pass

@dataclass
class PriceChangedEvent(ProductEvent):
    """Event for price changes."""
    old_price: Decimal
    new_price: Decimal

@dataclass
class InventoryChangedEvent(ProductEvent):
    """Event for inventory changes."""
    old_count: int
    new_count: int

class EventBus:
    """Simple event bus for publishing and subscribing to events."""
    
    _subscribers: Dict[type, List[Callable]] = {}
    
    @classmethod
    def subscribe(cls, event_type: type, handler: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)
    
    @classmethod
    async def publish(cls, event: Any) -> None:
        """Publish an event."""
        event_type = type(event)
        
        # Call handlers for this event type
        if event_type in cls._subscribers:
            for handler in cls._subscribers[event_type]:
                await handler(event)
        
        # Call handlers for parent event types
        for parent_type, handlers in cls._subscribers.items():
            if issubclass(event_type, parent_type) and parent_type != event_type:
                for handler in handlers:
                    await handler(event)

class EventDrivenProduct(Product):
    """Product with event-driven architecture."""
    
    async def save(self) -> None:
        """Save the product and publish events."""
        is_new = not self.id
        
        # Check for changes if not new
        if not is_new:
            try:
                old_product = await self.__class__.get(id=self.id)
                
                # Check for price change
                if old_product.price != self.price:
                    await EventBus.publish(PriceChangedEvent(
                        product_id=self.id,
                        old_price=old_product.price,
                        new_price=self.price
                    ))
                
                # Check for inventory change
                if old_product.inventory_count != self.inventory_count:
                    await EventBus.publish(InventoryChangedEvent(
                        product_id=self.id,
                        old_count=old_product.inventory_count,
                        new_count=self.inventory_count
                    ))
                
                # Collect all changes
                changes = {}
                for field, value in self.dict().items():
                    old_value = getattr(old_product, field, None)
                    if value != old_value:
                        changes[field] = {"old": old_value, "new": value}
                
                if changes:
                    await EventBus.publish(ProductUpdatedEvent(
                        product_id=self.id,
                        changes=changes
                    ))
            except Exception:
                # If we can't get the old product, continue without publishing change events
                pass
        
        # Save the product
        await super().save()
        
        # Publish created event if new
        if is_new:
            await EventBus.publish(ProductCreatedEvent(
                product_id=self.id,
                name=self.name,
                price=self.price
            ))
    
    async def delete(self) -> None:
        """Delete the product and publish events."""
        product_id = self.id
        
        # Delete the product
        await super().delete()
        
        # Publish deleted event
        await EventBus.publish(ProductDeletedEvent(product_id=product_id))

# Example event handlers

async def log_product_events(event: ProductEvent) -> None:
    """Log all product events."""
    event_type = type(event).__name__
    print(f"Event: {event_type} for product {event.product_id}")

async def notify_price_changes(event: PriceChangedEvent) -> None:
    """Send notifications for price changes."""
    price_diff = event.new_price - event.old_price
    percentage = (price_diff / event.old_price) * 100
    
    if price_diff < 0:
        print(f"Price alert: Product {event.product_id} price reduced by {abs(percentage):.2f}%")
    else:
        print(f"Price alert: Product {event.product_id} price increased by {percentage:.2f}%")

async def handle_inventory_changes(event: InventoryChangedEvent) -> None:
    """Handle inventory change events."""
    # Send low inventory alerts
    if event.new_count < 10 and event.old_count >= 10:
        print(f"Inventory alert: Product {event.product_id} inventory low: {event.new_count}")
    
    # Send out of stock alerts
    if event.new_count == 0 and event.old_count > 0:
        print(f"Inventory alert: Product {event.product_id} is out of stock")
    
    # Send restock alerts
    if event.new_count > 0 and event.old_count == 0:
        print(f"Inventory alert: Product {event.product_id} is back in stock")

# Subscribe to events
EventBus.subscribe(ProductEvent, log_product_events)
EventBus.subscribe(PriceChangedEvent, notify_price_changes)
EventBus.subscribe(InventoryChangedEvent, handle_inventory_changes)
```

## Combining Approaches

Create a comprehensive extension strategy by combining multiple approaches:

```python
# Flexible product class that combines multiple extension approaches
class FlexibleProduct(UnoObj[ProductModel]):
    """Product with multiple extension mechanisms."""
    
    # Plugin architecture
    _plugins: ClassVar[List[Any]] = []
    
    # Event system
    _event_handlers: ClassVar[Dict[str, List[Callable]]] = {}
    
    # Feature toggles
    _features: ClassVar[Dict[str, bool]] = {
        "inventory_management": True,
        "pricing_rules": True,
        "auditing": False,
        "versioning": False
    }
    
    # Extensions mechanism
    _extensions: Dict[str, Any] = {}
    
    @classmethod
    def register_plugin(cls, plugin: Any) -> None:
        """Register a plugin."""
        cls._plugins.append(plugin)
    
    @classmethod
    def on(cls, event_name: str) -> Callable:
        """Decorator for registering event handlers."""
        def decorator(func: Callable) -> Callable:
            if event_name not in cls._event_handlers:
                cls._event_handlers[event_name] = []
            cls._event_handlers[event_name].append(func)
            return func
        return decorator
    
    @classmethod
    def enable_feature(cls, feature_name: str) -> None:
        """Enable a feature."""
        cls._features[feature_name] = True
    
    @classmethod
    def disable_feature(cls, feature_name: str) -> None:
        """Disable a feature."""
        cls._features[feature_name] = False
    
    @classmethod
    def is_feature_enabled(cls, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return cls._features.get(feature_name, False)
    
    def add_extension(self, name: str, extension: Any) -> None:
        """Add an extension to this product."""
        self._extensions[name] = extension
    
    def get_extension(self, name: str) -> Optional[Any]:
        """Get an extension by name."""
        return self._extensions.get(name)
    
    async def trigger_event(self, event_name: str, **event_data) -> None:
        """Trigger an event."""
        if event_name not in self._event_handlers:
            return
        
        for handler in self._event_handlers[event_name]:
            if inspect.iscoroutinefunction(handler):
                await handler(self, **event_data)
            else:
                handler(self, **event_data)
    
    async def save(self) -> None:
        """Save the product with all extension mechanisms."""
        # Check if this is a new or existing product
        is_new = not self.id
        
        # Run plugin before_save hooks
        for plugin in self._plugins:
            if hasattr(plugin, 'before_save'):
                await plugin.before_save(self)
        
        # Trigger before_save event
        await self.trigger_event('before_save')
        
        # Get old state for change detection
        old_state = None
        if not is_new:
            try:
                old_state = await self.__class__.get(id=self.id)
            except Exception:
                pass
        
        # Versioning feature
        if self.is_feature_enabled('versioning') and old_state:
            # Archive current version
            version_extension = self.get_extension('versioning')
            if version_extension:
                await version_extension.archive_version(self, old_state)
        
        # Run extensions before save
        for name, extension in self._extensions.items():
            if hasattr(extension, 'before_save'):
                await extension.before_save(self)
        
        # Save the product
        await super().save()
        
        # Run extensions after save
        for name, extension in self._extensions.items():
            if hasattr(extension, 'after_save'):
                await extension.after_save(self)
        
        # Detect changes and trigger events
        if old_state:
            # Check for price change
            if old_state.price != self.price:
                await self.trigger_event('price_changed', 
                                        old_price=old_state.price, 
                                        new_price=self.price)
            
            # Check for inventory change
            if old_state.inventory_count != self.inventory_count:
                await self.trigger_event('inventory_changed', 
                                         old_count=old_state.inventory_count, 
                                         new_count=self.inventory_count)
            
            # Trigger generic updated event
            await self.trigger_event('updated')
        else:
            # Trigger created event
            await self.trigger_event('created')
        
        # Run plugin after_save hooks
        for plugin in self._plugins:
            if hasattr(plugin, 'after_save'):
                await plugin.after_save(self)
        
        # Trigger after_save event
        await self.trigger_event('after_save')
        
        # Auditing feature
        if self.is_feature_enabled('auditing'):
            audit_extension = self.get_extension('auditing')
            if audit_extension:
                event_type = 'create' if is_new else 'update'
                await audit_extension.log_event(self, event_type)
    
    async def delete(self) -> None:
        """Delete the product with all extension mechanisms."""
        # Run plugin before_delete hooks
        for plugin in self._plugins:
            if hasattr(plugin, 'before_delete'):
                await plugin.before_delete(self)
        
        # Trigger before_delete event
        await self.trigger_event('before_delete')
        
        # Run extensions before delete
        for name, extension in self._extensions.items():
            if hasattr(extension, 'before_delete'):
                await extension.before_delete(self)
        
        # Store id before deletion
        product_id = self.id
        
        # Delete the product
        await super().delete()
        
        # Run extensions after delete
        for name, extension in self._extensions.items():
            if hasattr(extension, 'after_delete'):
                await extension.after_delete(self)
        
        # Trigger deleted event
        await self.trigger_event('deleted', product_id=product_id)
        
        # Run plugin after_delete hooks
        for plugin in self._plugins:
            if hasattr(plugin, 'after_delete'):
                await plugin.after_delete(self)
        
        # Trigger after_delete event
        await self.trigger_event('after_delete', product_id=product_id)
        
        # Auditing feature
        if self.is_feature_enabled('auditing'):
            audit_extension = self.get_extension('auditing')
            if audit_extension:
                await audit_extension.log_event(self, 'delete')
```

## Best Practices for Extending UnoObj

1. **Favor Composition Over Inheritance**
   - Use inheritance only when extending core behavior or identity
   - Use composition for reusable functionality and optional features
   - Consider service objects for complex operations

2. **Keep Extensions Modular**
   - Design extensions with clear boundaries
   - Avoid tight coupling between extensions
   - Use interfaces or protocols to define extension points

3. **Use Progressive Enhancement**
   - Start with simple extensions and add complexity as needed
   - Provide sensible defaults and optional advanced features
   - Enable features through configuration rather than hardcoding

4. **Maintain Domain Focus**
   - Keep business logic in domain objects
   - Move technical concerns to services or helpers
   - Ensure extensions enhance rather than obscure domain logic

5. **Consider Performance**
   - Use lazy loading for related objects
   - Avoid circular dependencies
   - Be mindful of the cost of complex extension mechanisms

6. **Test Extensions Thoroughly**
   - Write unit tests for each extension
   - Create integration tests for extension interactions
   - Test both happy paths and edge cases

## See Also

- [UnoObj Reference](unoobj.md) - Core UnoObj class documentation
- [Business Logic Best Practices](best_practices.md) - General best practices for business logic
- [Registry System](registry.md) - Type-safe registry for business objects