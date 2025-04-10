# Models Overview

The Models layer in uno provides a standardized approach to defining database tables and columns with proper type annotations and constraints.

## UnoModel

The `UnoModel` class is a SQLAlchemy `DeclarativeBase` subclass that serves as the foundation for all database models in the Uno framework. It provides:

- Standardized PostgreSQL column types
- Type annotations for better editor support
- Common configuration for database constraints
- Asynchronous attribute access
- Consistent naming conventions for database objects

### Basic Usage

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class CustomerModel(UnoModel):
    __tablename__ = "customer"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(
        primary_key=True,
        doc="Unique identifier for the customer"
    )
    name: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        index=True,
        doc="Customer's full name"
    )
    email: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        unique=True,
        doc="Customer's email address"
    )
    phone: Mapped[Optional[PostgresTypes.String64]] = mapped_column(
        nullable=True,
        doc="Customer's phone number"
    )
    is_active: Mapped[PostgresTypes.Boolean] = mapped_column(
        default=True,
        doc="Whether the customer is active"
    )
```

## PostgresTypes

The `PostgresTypes` class provides standardized type annotations for PostgreSQL column types:

```python
from uno.model import PostgresTypes

# String types
String12 = PostgresTypes.String12  # VARCHAR(12)
String26 = PostgresTypes.String26  # VARCHAR(26)
String63 = PostgresTypes.String63  # VARCHAR(63)
String64 = PostgresTypes.String64  # VARCHAR(64)
String128 = PostgresTypes.String128  # VARCHAR(128)
String255 = PostgresTypes.String255  # VARCHAR(255)
Text = PostgresTypes.Text  # TEXT
UUID = PostgresTypes.UUID  # UUID

# Numeric types
BigInt = PostgresTypes.BigInt  # BIGINT
Decimal = PostgresTypes.Decimal  # NUMERIC

# Boolean type
Boolean = PostgresTypes.Boolean  # BOOLEAN

# Date and time types
Timestamp = PostgresTypes.Timestamp  # TIMESTAMP WITH TIME ZONE
Date = PostgresTypes.Date  # DATE
Time = PostgresTypes.Time  # TIME
Interval = PostgresTypes.Interval  # INTERVAL

# Binary data
ByteA = PostgresTypes.ByteA  # BYTEA

# JSON data
JSONB = PostgresTypes.JSONB  # JSONB

# Array type
Array = PostgresTypes.Array  # ARRAY

# Enum type
StrEnum = PostgresTypes.StrEnum  # ENUM
```

## Defining Relationships

### One-to-Many Relationships

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List

class DepartmentModel(UnoModel):
    __tablename__ = "department"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    
    # Relationship to employees
    employees: Mapped[List["EmployeeModel"]] = relationship(back_populates="department")

class EmployeeModel(UnoModel):
    __tablename__ = "employee"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    
    # Foreign key to department
    department_id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("department.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationship to department
    department: Mapped["DepartmentModel"] = relationship(back_populates="employees")
```

### Many-to-Many Relationships

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column
from typing import List

# Association table for many-to-many relationship
product_category_association = Table(
    "product_category",
    UnoModel.metadata,
    Column("product_id", PostgresTypes.String26, ForeignKey("product.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", PostgresTypes.String26, ForeignKey("category.id", ondelete="CASCADE"), primary_key=True)
)

class ProductModel(UnoModel):
    __tablename__ = "product"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    
    # Relationship to categories
    categories: Mapped[List["CategoryModel"]] = relationship(
        secondary=product_category_association,
        back_populates="products"
    )

class CategoryModel(UnoModel):
    __tablename__ = "category"
    
    id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    
    # Relationship to products
    products: Mapped[List["ProductModel"]] = relationship(
        secondary=product_category_association,
        back_populates="categories"
    )
```

## Best Practices

1. **Use Type Annotations**: Always use proper type annotations for columns to improve IDE support and type checking.

2. **Document Columns**: Add docstrings to your columns using the `doc` parameter to explain their purpose.

3. **Use PostgresTypes**: Use the `PostgresTypes` class for consistent column types.

4. **Define Constraints**: Add appropriate constraints (unique, foreign keys, etc.) to maintain data integrity.

5. **Include Indices**: Add indices to columns that will be frequently queried to improve performance.

6. **Follow Naming Conventions**: Use consistent naming for tables and columns.

7. **Apply Mixins**: Use mixins for common field patterns to reduce code duplication.

## Next Steps

- [UnoModel](model.md): Learn more about the UnoModel class
- [Business Logic Layer](../business_logic/overview.md): Understand how to implement business logic with UnoObj
- [Database Operations](../database/unodb.md): Learn about database operations