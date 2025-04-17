# Specification Translators

The specification pattern in domain-driven design allows us to define business rules as first-class objects. Specification translators convert these domain-level rules into database-specific queries, maintaining the separation between domain logic and data access concerns.

## Overview

The Uno framework's specification translator system offers a clean, flexible way to translate domain specifications into database-specific queries. This approach:

1. Keeps domain logic pure and focused on business rules
2. Eliminates repetitive query-building code
3. Enables composable, reusable business rules
4. Provides database-specific optimizations without contaminating the domain layer

## PostgreSQL Specification Translator

### Purpose

The `PostgreSQLSpecificationTranslator` translates domain specifications into SQLAlchemy expressions optimized for PostgreSQL 16+. It handles the conversion of domain-level business rules into efficient SQL queries.

### Features

- Translates specifications to SQLAlchemy SELECT statements
- Supports complex logical operations (AND, OR, NOT)
- Handles attribute-based specifications for property comparisons
- Integrates with SQLAlchemy's type system for proper value handling
- Optimized for PostgreSQL 16+ features

### Usage

```python
from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from uno.domain.specifications import AttributeSpecification, specification_factory
from uno.domain.specification_translators import PostgreSQLSpecificationTranslator

# Define your domain entity
class Product:
    id: str
    name: str
    price: float
    in_stock: bool

# Create a specification factory for Product
ProductSpecification = specification_factory(Product)

# Define your SQLAlchemy model
Base = declarative_base()

class ProductModel(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    price = Column(Integer)
    in_stock = Column(Boolean)

# Create specifications
premium_products = ProductSpecification.attribute("price", 100).and_(
    ProductSpecification.attribute("in_stock", True)
)

# Create a translator
translator = PostgreSQLSpecificationTranslator(ProductModel)

# Translate the specification to a SQLAlchemy query
query = translator.translate(premium_products)

# Execute the query with SQLAlchemy
session.execute(query)
```

## PostgreSQL Repository

The framework also provides ready-to-use repository implementations that leverage the specification translator:

### PostgreSQLRepository

A base repository implementation that translates specifications to SQLAlchemy queries and executes them against PostgreSQL.

```python
from uno.domain.specification_translators import PostgreSQLRepository

# Create a repository
repository = PostgreSQLRepository(
    entity_type=Product,
    model_class=ProductModel,
    session_factory=lambda: Session()
)

# Find products matching a specification
products = repository.find_by_specification(premium_products)
```

### AsyncPostgreSQLRepository

An asynchronous repository implementation that provides async methods for working with PostgreSQL:

```python
from uno.domain.specification_translators import AsyncPostgreSQLRepository
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Create an async session factory
async def session_factory():
    engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/dbname")
    async_session = AsyncSession(engine)
    return async_session

# Create an async repository
repository = AsyncPostgreSQLRepository(
    entity_type=Product,
    model_class=ProductModel,
    session_factory=session_factory
)

# Find products asynchronously
products = await repository.find_by_specification(premium_products)

# Count products matching a specification
count = await repository.count_by_specification(premium_products)
```

## Benefits

Using specification translators provides several benefits:

1. **Clean domain logic**: Business rules stay in the domain layer, free of data access concerns
2. **Testability**: Domain specifications can be tested in isolation without database dependencies
3. **Flexibility**: The same specifications can be used with different data stores
4. **Performance**: Database-specific optimizations happen in the translator, not in domain logic
5. **Maintainability**: Changes to database access don't affect domain logic

## Best Practices

- Keep specifications focused on business rules, not data access
- Compose complex specifications from simpler ones
- Create domain-specific specification factories for readability
- Use the translator pattern to separate domain logic from infrastructure concerns
- Prefer AsyncPostgreSQLRepository for modern async applications