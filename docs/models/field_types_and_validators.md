# UnoModel Field Types and Validators

This guide provides comprehensive documentation on field types and validators available for UnoModel in uno.

## PostgreSQL Field Types

UnoModel provides standardized type annotations for PostgreSQL column types through the `PostgresTypes` class. These types provide proper type hints for Python while mapping to the appropriate PostgreSQL database types.

### String Types

| Type | PostgreSQL Type | Description | Length | Example Usage |
|------|----------------|-------------|--------|---------------|
| `PostgresTypes.String12` | VARCHAR(12) | Fixed-length string (12 chars) | 12 | Codes, short IDs |
| `PostgresTypes.String26` | VARCHAR(26) | Fixed-length string (26 chars) | 26 | ULIDs, primary keys |
| `PostgresTypes.String63` | VARCHAR(63) | Fixed-length string (63 chars) | 63 | DNS labels, hostnames |
| `PostgresTypes.String64` | VARCHAR(64) | Fixed-length string (64 chars) | 64 | API keys, hash values |
| `PostgresTypes.String128` | VARCHAR(128) | Fixed-length string (128 chars) | 128 | URLs, paths |
| `PostgresTypes.String255` | VARCHAR(255) | Standard string (255 chars) | 255 | Names, titles, emails |
| `PostgresTypes.Text` | TEXT | Unlimited-length text | Unlimited | Descriptions, comments |
| `PostgresTypes.UUID` | UUID | Universally unique identifier | 36 chars (with hyphens) | Primary keys, external IDs |

**Example Usage:**
```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

class ProductModel(UnoModel):
    __tablename__ = "product"
    
    # Use String26 for primary key (ULID)
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    
    # Use String255 for names
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    
    # Use Text for longer content
    description: Mapped[PostgresTypes.Text] = mapped_column(nullable=True)
    
    # Use UUID for external references
    external_id: Mapped[Optional[PostgresTypes.UUID]] = mapped_column(nullable=True)
```

### Numeric Types

| Type | PostgreSQL Type | Description | Example Usage |
|------|----------------|-------------|---------------|
| `PostgresTypes.BigInt` | BIGINT | 64-bit integer | Large counts, IDs |
| `PostgresTypes.Decimal` | NUMERIC | Precise decimal number | Money, percentages |
| `int` | BIGINT | Standard integer, maps to BIGINT | Counts, ages |
| `float` | FLOAT | Floating-point number | Scientific measurements |

**Example Usage:**
```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class OrderModel(UnoModel):
    __tablename__ = "order"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    
    # Use BigInt for large numbers
    item_count: Mapped[PostgresTypes.BigInt] = mapped_column(nullable=False)
    
    # Use Decimal for money (ALWAYS use Decimal for financial values)
    total_amount: Mapped[PostgresTypes.Decimal] = mapped_column(nullable=False)
    
    # Direct int type (will map to BIGINT)
    shipping_days: Mapped[int] = mapped_column(nullable=False)
    
    # Use float for measurements (avoid for financial data)
    package_weight: Mapped[Optional[float]] = mapped_column(nullable=True)
```

### Boolean Type

| Type | PostgreSQL Type | Description | Example Usage |
|------|----------------|-------------|---------------|
| `PostgresTypes.Boolean` | BOOLEAN | True/false value | Flags, toggles |
| `bool` | BOOLEAN | Python boolean, maps to BOOLEAN | Active status, feature flags |

**Example Usage:**
```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

class UserModel(UnoModel):
    __tablename__ = "user"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    
    # Use Boolean for flags
    is_active: Mapped[PostgresTypes.Boolean] = mapped_column(default=True)
    
    # Direct bool type
    email_verified: Mapped[bool] = mapped_column(default=False)
```

### Date and Time Types

| Type | PostgreSQL Type | Description | Example Usage |
|------|----------------|-------------|---------------|
| `PostgresTypes.Timestamp` | TIMESTAMP WITH TIME ZONE | Date and time with timezone | Creation dates, event times |
| `PostgresTypes.Date` | DATE | Date only | Birth dates, schedule dates |
| `PostgresTypes.Time` | TIME | Time only | Scheduled times, opening hours |
| `PostgresTypes.Interval` | INTERVAL | Time duration | Durations, time spans |

**Example Usage:**
```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import datetime

class EventModel(UnoModel):
    __tablename__ = "event"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    
    # Use Timestamp for date and time with timezone
    created_at: Mapped[PostgresTypes.Timestamp] = mapped_column(nullable=False)
    
    # Use Date for date-only values
    event_date: Mapped[PostgresTypes.Date] = mapped_column(nullable=False)
    
    # Use Time for time-only values
    start_time: Mapped[PostgresTypes.Time] = mapped_column(nullable=False)
    
    # Use Interval for durations
    duration: Mapped[PostgresTypes.Interval] = mapped_column(nullable=False)
    
    # Use Optional for nullable fields
    end_time: Mapped[Optional[PostgresTypes.Timestamp]] = mapped_column(nullable=True)
```

### Binary and JSON Types

| Type | PostgreSQL Type | Description | Example Usage |
|------|----------------|-------------|---------------|
| `PostgresTypes.ByteA` | BYTEA | Binary data | Files, images, encrypted data |
| `PostgresTypes.JSONB` | JSONB | JSON binary format | Structured data, settings |

**Example Usage:**
```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, Dict, Any

class ProfileModel(UnoModel):
    __tablename__ = "profile"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    
    # Use ByteA for binary data
    profile_image: Mapped[Optional[PostgresTypes.ByteA]] = mapped_column(nullable=True)
    
    # Use JSONB for settings or flexible schema data
    settings: Mapped[PostgresTypes.JSONB] = mapped_column(default=dict)
    
    # JSONB for structured metadata
    metadata: Mapped[Dict[str, Any]] = mapped_column(
        PostgresTypes.JSONB, 
        default=dict
    )
```

### Collection and Enum Types

| Type | PostgreSQL Type | Description | Example Usage |
|------|----------------|-------------|---------------|
| `PostgresTypes.Array` | ARRAY | Array of values | Tags, categories, permissions |
| `PostgresTypes.StrEnum` | ENUM | String enumeration | Statuses, types, categories |

**Example Usage:**
```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
import enum
from typing import List

# Define an enum type
class OrderStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderModel(UnoModel):
    __tablename__ = "order"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    
    # Use StrEnum for enumerated values
    status: Mapped[OrderStatus] = mapped_column(
        default=OrderStatus.PENDING
    )
    
    # Use Array for collections of values
    tags: Mapped[List[str]] = mapped_column(
        ARRAY(PostgresTypes.String63),
        default=list
    )
```

## Column Definition Options

When defining columns using `mapped_column()`, you can specify various configuration options:

### Basic Column Options

| Option | Description | Example |
|--------|-------------|---------|
| `primary_key` | Designates the column as a primary key | `primary_key=True` |
| `nullable` | Whether the column can be NULL | `nullable=False` |
| `unique` | Whether the column must have unique values | `unique=True` |
| `index` | Whether to create an index on this column | `index=True` |
| `default` | Default value for the column | `default="pending"` |
| `server_default` | Default value set by the database | `server_default=text("now()")` |
| `onupdate` | Value to set on updates | `onupdate=lambda: datetime.now(datetime.UTC)` |
| `doc` | Documentation string for the column | `doc="User's email address"` |

**Example Usage:**
```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text
from typing import Optional
import datetime

class UserModel(UnoModel):
    __tablename__ = "user"
    
    # Primary key with auto-generated value
    id: Mapped[PostgresTypes.String26] = mapped_column(
        primary_key=True,
        nullable=False,
        doc="Unique identifier for the user"
    )
    
    # Required field with index for faster lookups
    email: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
        doc="User's email address"
    )
    
    # Field with default value
    is_active: Mapped[bool] = mapped_column(
        default=True,
        doc="Whether the user account is active"
    )
    
    # Server-generated timestamp
    created_at: Mapped[PostgresTypes.Timestamp] = mapped_column(
        nullable=False,
        server_default=text("now()"),
        doc="When the user was created"
    )
    
    # Timestamp that updates automatically
    updated_at: Mapped[PostgresTypes.Timestamp] = mapped_column(
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(datetime.UTC),
        doc="When the user was last updated"
    )
```

### Advanced Column Options

| Option | Description | Example |
|--------|-------------|---------|
| `info` | Additional metadata for the column | `info={"graph_excludes": True}` |
| `comment` | Database comment for the column | `comment="Stores user's full name"` |
| `autoincrement` | Auto-incrementing value | `autoincrement=True` |
| `insert_default` | Value to use for insert if none provided | `insert_default="default"` |
| `foreign_keys` | Foreign key references | `foreign_keys=[ForeignKey("users.id")]` |

**Example Usage:**
```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, text

class CommentModel(UnoModel):
    __tablename__ = "comment"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    
    # Foreign key with cascading delete
    post_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("post.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the parent post",
        info={
            "edge": "POST",  # Graph relationship name
            "reverse_edge": "COMMENTS"
        }
    )
    
    # Content with additional metadata
    content: Mapped[PostgresTypes.Text] = mapped_column(
        nullable=False,
        comment="The comment text content",
        info={
            "searchable": True,  # Custom metadata for search indexing
            "max_length": 5000
        }
    )
    
    # Sensitive data that should be excluded from graph queries
    ip_address: Mapped[Optional[PostgresTypes.String63]] = mapped_column(
        nullable=True,
        comment="IP address of commenter",
        info={
            "graph_excludes": True,  # Exclude from graph queries
            "sensitive": True
        }
    )
```

## Table-Level Options

You can set table-level options using the `__table_args__` attribute:

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UniqueConstraint, Index, CheckConstraint, text

class OrderModel(UnoModel):
    __tablename__ = "order"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    region: Mapped[PostgresTypes.String64] = mapped_column(nullable=False)
    order_number: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    amount: Mapped[PostgresTypes.Decimal] = mapped_column(nullable=False)
    
    # Table-level constraints and configuration
    __table_args__ = (
        # Unique constraint across multiple columns
        UniqueConstraint("region", "order_number", name="uq_order_region_number"),
        
        # Custom composite index
        Index("ix_order_region_amount", "region", "amount"),
        
        # Check constraint
        CheckConstraint("amount > 0", name="ck_order_positive_amount"),
        
        # Table comment
        {"comment": "Orders placed by customers"}
    )
```

## Common Field Patterns Using Mixins

uno provides mixins to include common fields in your models:

### ModelMixin

The `ModelMixin` adds standard fields for tracking creation, modification, and deletion:

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.mixins import ModelMixin

class ProductModel(UnoModel, ModelMixin):
    __tablename__ = "product"
    
    # ModelMixin adds these fields automatically:
    # - id: Primary key with ForeignKey to meta_record.id
    # - is_active: Boolean flag for active status
    # - is_deleted: Boolean flag for soft deletion
    # - created_at: Timestamp when record was created
    # - modified_at: Timestamp when record was last modified
    # - deleted_at: Timestamp when record was soft deleted (nullable)
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    price: Mapped[PostgresTypes.Decimal] = mapped_column(nullable=False)
```

### DefaultModelMixin (from Authorization)

The `DefaultModelMixin` from the authorization module adds owner/creator tracking:

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.authorization.mixins import DefaultModelMixin

class DocumentModel(UnoModel, DefaultModelMixin):
    __tablename__ = "document"
    
    # DefaultModelMixin adds these fields automatically:
    # - All fields from ModelMixin
    # - created_by: The user who created the record
    # - modified_by: The user who last modified the record
    # - deleted_by: The user who deleted the record (nullable)
    # - owner_id: The owner of the record
    
    title: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    content: Mapped[PostgresTypes.Text] = mapped_column(nullable=True)
```

## Field Validators

SQLAlchemy and Pydantic offer several approaches to field validation. In uno, you can use:

### 1. Field Validators (Pydantic)

For domain entities and schemas that extend Pydantic models:

```python
from pydantic import BaseModel, field_validator

class Product(BaseModel):
    id: str
    name: str
    price: float
    inventory_count: int
    
    @field_validator("inventory_count")
    def inventory_count_non_negative(cls, v):
        """Validate that inventory count is non-negative."""
        if v < 0:
            raise ValueError("Inventory count must be non-negative")
        return v
    
    @field_validator("price")
    def price_non_negative(cls, v):
        """Validate that price is non-negative."""
        if v < 0:
            raise ValueError("Price must be non-negative")
        return v
```

### 2. Model Validators (Pydantic)

For validations involving multiple fields:

```python
from pydantic import BaseModel, model_validator

class OrderItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float
    discount_percent: float = 0
    total_price: float
    
    @model_validator(mode='after')
    def validate_total_price(self) -> 'OrderItem':
        """Validate that the total price calculation is correct."""
        expected_total = self.quantity * self.unit_price * (1 - self.discount_percent / 100)
        if abs(self.total_price - expected_total) > 0.01:
            raise ValueError("Total price does not match quantity * unit price with discount")
        return self
```

### 3. SQLAlchemy Validators

For direct validation in SQLAlchemy models:

```python
from sqlalchemy.orm import validates
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

class ProductModel(UnoModel):
    __tablename__ = "product"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    price: Mapped[PostgresTypes.Decimal] = mapped_column(nullable=False)
    inventory_count: Mapped[int] = mapped_column(default=0)
    
    @validates('price')
    def validate_price(self, key, price):
        """Validate that price is positive."""
        if price <= 0:
            raise ValueError("Price must be positive")
        return price
    
    @validates('inventory_count')
    def validate_inventory_count(self, key, count):
        """Validate that inventory count is non-negative."""
        if count < 0:
            raise ValueError("Inventory count must be non-negative")
        return count
```

### 4. Domain Validators

For more complex validation, use the `ValidationResult` pattern:

```python
from uno.domain.validation import ValidationResult, ValidationSeverity, FieldValidator

class ProductValidator(FieldValidator):
    """Validator for product entities."""
    
    def validate_product(self, product, result: ValidationResult) -> None:
        """Validate a product entity."""
        # Check required fields
        self.required(product, "id", result)
        self.required(product, "name", result)
        self.required(product, "price", result)
        
        # Validate string lengths
        self.min_length(product, "name", 3, result)
        self.max_length(product, "name", 255, result)
        
        # Validate numeric ranges
        if hasattr(product, "price") and product.price is not None:
            if product.price <= 0:
                result.add_message(
                    "Price must be positive",
                    ValidationSeverity.ERROR
                )
                
        # Validate relationships and business rules
        if hasattr(product, "category_id") and not product.category_id:
            result.add_message(
                "Product should belong to a category",
                ValidationSeverity.WARNING
            )

# Usage
validator = ProductValidator()
product = Product(id="1", name="Sample", price=-10)
result = validator.validate(product)

if result.has_errors:
    print("Validation errors:", result.errors)
```

## Check Constraints

PostgreSQL check constraints provide database-level validation:

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import CheckConstraint

class ProductModel(UnoModel):
    __tablename__ = "product"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    price: Mapped[PostgresTypes.Decimal] = mapped_column(nullable=False)
    discount_price: Mapped[Optional[PostgresTypes.Decimal]] = mapped_column(nullable=True)
    
    # Column-level check constraint
    weight: Mapped[float] = mapped_column(
        CheckConstraint("weight > 0", name="ck_product_positive_weight"),
        nullable=False
    )
    
    # Table-level check constraints
    __table_args__ = (
        # Ensure discount price is less than regular price
        CheckConstraint(
            "discount_price IS NULL OR discount_price < price",
            name="ck_product_discount_less_than_price"
        ),
    )
```

## Best Practices

1. **Use Appropriate Types**: Choose the right PostgreSQL type for each field to optimize storage and performance.

2. **Document Fields**: Add `doc` strings to all columns to document their purpose and constraints.

3. **Set Proper Nullability**: Be explicit about which fields can be NULL. Default to `nullable=False` unless a field is truly optional.

4. **Add Constraints**: Use unique constraints, foreign keys, and check constraints to maintain data integrity.

5. **Include Indices**: Add indices to columns that will be frequently queried to improve performance.

6. **Apply Mixins**: Use mixins for common field patterns to reduce code duplication.

7. **Validate at Multiple Levels**:
   - Domain validation: For business rules
   - Schema validation: For API input/output
   - Database constraints: For ultimate data integrity

8. **Use Standard Lengths**: Follow the standard string lengths provided by `PostgresTypes` for consistency.

9. **Use Decimal for Money**: Always use `PostgresTypes.Decimal` for monetary values, never `float`.

10. **Ensure Foreign Key Consistency**: Set appropriate `ondelete` behavior for foreign keys (typically `CASCADE` or `SET NULL`).

11. **Add Metadata With info**: Use the `info` parameter to add custom metadata to columns for framework features.

12. **Follow Naming Conventions**:
    - Table names: singular noun (`user` not `users`)
    - Column names: snake_case
    - Constraint names: follow the convention defined in `MetadataFactory`

## Real-World Examples

### User Model with Authentication

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text, CheckConstraint
from typing import Optional
import datetime

class UserModel(UnoModel):
    __tablename__ = "user"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(
        primary_key=True,
        doc="Unique identifier for the user"
    )
    email: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
        doc="User's email address"
    )
    username: Mapped[PostgresTypes.String64] = mapped_column(
        nullable=False,
        unique=True,
        doc="User's username for login"
    )
    password_hash: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        doc="Hashed password",
        info={"sensitive": True, "graph_excludes": True}
    )
    email_verified: Mapped[bool] = mapped_column(
        default=False,
        doc="Whether the email has been verified"
    )
    last_login: Mapped[Optional[PostgresTypes.Timestamp]] = mapped_column(
        nullable=True,
        doc="When the user last logged in"
    )
    created_at: Mapped[PostgresTypes.Timestamp] = mapped_column(
        nullable=False,
        server_default=text("now()"),
        doc="When the user was created"
    )
    
    __table_args__ = (
        # Ensure username follows pattern
        CheckConstraint(
            "username ~ '^[a-zA-Z0-9_]+$'",
            name="ck_user_username_pattern"
        ),
        {"comment": "User accounts for authentication"}
    )
```

### E-commerce Order System

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, CheckConstraint, text
from typing import List, Optional

class OrderModel(UnoModel):
    __tablename__ = "order"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    user_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The user who placed the order"
    )
    status: Mapped[str] = mapped_column(
        doc="Order status",
        default="pending"
    )
    total_amount: Mapped[PostgresTypes.Decimal] = mapped_column(
        nullable=False,
        doc="Total order amount"
    )
    shipping_address: Mapped[PostgresTypes.JSONB] = mapped_column(
        nullable=False,
        doc="Shipping address as a JSON object"
    )
    created_at: Mapped[PostgresTypes.Timestamp] = mapped_column(
        nullable=False,
        server_default=text("now()"),
        doc="When the order was created"
    )
    
    # Relationships
    items: Mapped[List["OrderItemModel"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="ck_order_positive_amount"
        ),
    )

class OrderItemModel(UnoModel):
    __tablename__ = "order_item"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    order_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("order.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The order this item belongs to"
    )
    product_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("product.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="The product for this item"
    )
    quantity: Mapped[int] = mapped_column(
        nullable=False,
        doc="Quantity of the product"
    )
    unit_price: Mapped[PostgresTypes.Decimal] = mapped_column(
        nullable=False,
        doc="Price per unit at time of order"
    )
    
    # Relationships
    order: Mapped["OrderModel"] = relationship(back_populates="items")
    
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_order_item_positive_quantity"
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_order_item_positive_price"
        ),
    )
```

## Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [PostgreSQL Data Types](https://www.postgresql.org/docs/current/datatype.html)
- [SQLAlchemy Column API](https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.Column)
- [Pydantic Field Validators](https://docs.pydantic.dev/latest/usage/validators/)