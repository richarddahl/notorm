# UnoModel

The `UnoModel` class is the foundation for database models in the Uno framework. It provides a standardized approach to defining database tables and columns with proper type annotations.

## Overview

`UnoModel` is a SQLAlchemy `DeclarativeBase` subclass that adds:

- Standardized PostgreSQL column types
- Type annotations for better editor support
- Common configuration for database constraints
- Asynchronous attribute access
- Consistent naming conventions for database objects

## Basic Usage

### Defining a Model

To define a database model, create a class that inherits from `UnoModel`:

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class CustomerModel(UnoModel):```

__tablename__ = "customer"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(```

primary_key=True,
doc="Unique identifier for the customer"
```
)
name: Mapped[PostgresTypes.String255] = mapped_column(```

nullable=False,
index=True,
doc="Customer's full name"
```
)
email: Mapped[PostgresTypes.String255] = mapped_column(```

nullable=False,
unique=True,
doc="Customer's email address",
info={
    "edge": "EMAIL",
    "reverse_edge": "CUSTOMER",
}
```
)
phone: Mapped[Optional[PostgresTypes.String64]] = mapped_column(```

nullable=True,
doc="Customer's phone number"
```
)
is_active: Mapped[PostgresTypes.Boolean] = mapped_column(```

default=True,
doc="Whether the customer is active"
```
)
```
```

### Using PostgreSQL Types

The `PostgresTypes` class provides standardized type annotations for PostgreSQL column types:

```python
from uno.model import PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

class ProductModel(UnoModel):```

__tablename__ = "product"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
description: Mapped[PostgresTypes.Text] = mapped_column(nullable=True)
price: Mapped[PostgresTypes.Decimal] = mapped_column(nullable=False)
image_data: Mapped[Optional[PostgresTypes.ByteA]] = mapped_column(nullable=True)
tags: Mapped[PostgresTypes.Array] = mapped_column(nullable=True)
metadata: Mapped[PostgresTypes.JSONB] = mapped_column(nullable=True)
created_at: Mapped[PostgresTypes.Timestamp] = mapped_column(nullable=False)
```
```

### Using Mixins

You can use mixins to include common fields in multiple models:

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.mixins import ModelMixin

class CustomerModel(UnoModel, ModelMixin):```

__tablename__ = "customer"
``````

```
```

# Inherits id, is_active, is_deleted, created_at, modified_at, deleted_at from ModelMixin
``````

```
```

name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)
```
```

## Advanced Usage

### Custom Metadata

You can create models with custom metadata using the `with_custom_metadata` class method:

```python
from uno.model import UnoModel, MetadataFactory
from sqlalchemy.orm import Mapped, mapped_column

# Create custom metadata for a different schema
custom_metadata = MetadataFactory.create_metadata(schema="analytics")

# Create a model with custom metadata
AnalyticsCustomerModel = UnoModel.with_custom_metadata(custom_metadata)

class CustomerAnalytics(AnalyticsCustomerModel):```

__tablename__ = "customer_analytics"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
customer_id: Mapped[PostgresTypes.String26] = mapped_column(```

nullable=False,
index=True,
doc="Reference to customer.id"
```
)
visit_count: Mapped[int] = mapped_column(default=0)
last_visit: Mapped[Optional[PostgresTypes.Timestamp]] = mapped_column(nullable=True)
```
```

### Table Constraints

You can define table-level constraints using the `__table_args__` attribute:

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UniqueConstraint, Index

class OrderModel(UnoModel):```

__tablename__ = "order"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
customer_id: Mapped[PostgresTypes.String26] = mapped_column(nullable=False)
order_number: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
region: Mapped[PostgresTypes.String64] = mapped_column(nullable=False)
``````

```
```

# Define table-level constraints
__table_args__ = (```

# Unique constraint across multiple columns
UniqueConstraint("region", "order_number", name="uq_order_region_number"),
``````

```
```

# Custom index
Index("ix_order_customer_region", "customer_id", "region"),
```
)
```
```

### Column Metadata

You can add metadata to columns using the `info` parameter:

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

class UserModel(UnoModel):```

__tablename__ = "user"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
``````

```
```

# Add metadata for graph relationships
department_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(```

nullable=True,
index=True,
doc="The department this user belongs to",
info={
    "edge": "DEPARTMENT",  # Name of the relationship
    "reverse_edge": "USERS",  # Name of the reverse relationship
    "graph_excludes": False,  # Include in graph queries
}
```
)
``````

```
```

# Exclude from graph queries
password_hash: Mapped[PostgresTypes.String255] = mapped_column(```

nullable=False,
doc="Hashed password (never exposed)",
info={
    "graph_excludes": True,  # Exclude from graph queries
}
```
)
```
```

### Enum Types

You can use enum types for columns:

```python
import enum
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

class OrderStatus(enum.StrEnum):```

PENDING = "pending"
PROCESSING = "processing"
SHIPPED = "shipped"
DELIVERED = "delivered"
CANCELLED = "cancelled"
```

class OrderModel(UnoModel):```

__tablename__ = "order"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
``````

status: Mapped[OrderStatus] = mapped_column(
    default=OrderStatus.PENDING,
    doc="Current status of the order"
)
```
```

## Common Patterns

### One-to-Many Relationships

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List

class DepartmentModel(UnoModel):```

__tablename__ = "department"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
```
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)```

```
```

# Relationship to employees
employees: Mapped[List["EmployeeModel"]] = relationship(back_populates="department")
```

class EmployeeModel(UnoModel):```

__tablename__ = "employee"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
```
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)```

```
```

# Foreign key to department
department_id: Mapped[PostgresTypes.String26] = mapped_column(```

ForeignKey("department.id", ondelete="CASCADE"),
nullable=False,
index=True
```
)
``````

```
```

# Relationship to department
department: Mapped["DepartmentModel"] = relationship(back_populates="employees")
```
```

### Many-to-Many Relationships

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column
from typing import List

# Association table for many-to-many relationship
product_category_association = Table(```

"product_category",
UnoModel.metadata,
Column("product_id", PostgresTypes.String26, ForeignKey("product.id", ondelete="CASCADE"), primary_key=True),
Column("category_id", PostgresTypes.String26, ForeignKey("category.id", ondelete="CASCADE"), primary_key=True)
```
)

class ProductModel(UnoModel):```

__tablename__ = "product"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
```
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)```

```
```

# Relationship to categories
categories: Mapped[List["CategoryModel"]] = relationship(```

secondary=product_category_association,
back_populates="products"
```
)
```

class CategoryModel(UnoModel):```

__tablename__ = "category"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
```
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)```

```
```

# Relationship to products
products: Mapped[List["ProductModel"]] = relationship(```

secondary=product_category_association,
back_populates="categories"
```
)
```
```

## Best Practices

1. **Use Type Annotations**: Always use proper type annotations for columns to improve IDE support and type checking.

2. **Document Columns**: Add docstrings to your columns using the `doc` parameter to explain their purpose.

3. **Use PostgresTypes**: Use the `PostgresTypes` class for consistent column types.

4. **Define Constraints**: Add appropriate constraints (unique, foreign keys, etc.) to maintain data integrity.

5. **Include Indices**: Add indices to columns that will be frequently queried to improve performance.

6. **Use Naming Conventions**: Follow consistent naming conventions for tables, columns, and constraints.

7. **Apply Mixins**: Use mixins for common field patterns to reduce code duplication.

8. **Set Nullable Properly**: Be explicit about which columns can be null.

9. **Use Metadata Properties**: Add metadata to columns using the `info` parameter to store additional information.

10. **Follow SQLAlchemy Best Practices**: Adhere to SQLAlchemy's recommended patterns and practices.