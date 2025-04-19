# Specification Pattern in UNO

This document explains the Specification pattern implementation in the UNO framework's domain entity package. It covers the different specification types, how to compose them, and how to use them effectively for querying and filtering data.

## Overview

The Specification pattern in the UNO framework is implemented in the `uno.domain.entity.specification` package and includes the following components:

- **Specification**: Base abstract class that defines the specification interface
- **PredicateSpecification**: Specification based on a predicate function
- **AttributeSpecification**: Specification that checks attribute values
- **CompositeSpecification**: Base class for composite specifications
- **AndSpecification**, **OrSpecification**, **NotSpecification**: Composite logic operators
- **AllSpecification**, **AnySpecification**: Composite specifications for multiple conditions
- **SpecificationTranslator**: Translators to convert specifications to different query formats

The Specification pattern allows for encapsulating query criteria in reusable, composable objects, making complex queries more maintainable and testable.

## Core Concepts

### Specification Interface

The `Specification` class defines the core interface for all specifications:

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar('T')

class Specification(Generic[T], ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if the candidate satisfies this specification."""
        pass
    
    def and_(self, other: 'Specification[T]') -> 'Specification[T]':
        """Combine this specification with another using logical AND."""
        from uno.domain.entity.specification.composite import AndSpecification
        return AndSpecification(self, other)
    
    def or_(self, other: 'Specification[T]') -> 'Specification[T]':
        """Combine this specification with another using logical OR."""
        from uno.domain.entity.specification.composite import OrSpecification
        return OrSpecification(self, other)
    
    def not_(self) -> 'Specification[T]':
        """Negate this specification."""
        from uno.domain.entity.specification.composite import NotSpecification
        return NotSpecification(self)
```

### Custom Specifications

You can create custom specifications by extending the `Specification` class:

```python
from uno.domain.entity.specification import Specification
from datetime import datetime, timedelta

class User:
    def __init__(self, name: str, created_at: datetime, is_active: bool = True):
        self.name = name
        self.created_at = created_at
        self.is_active = is_active

class ActiveUserSpecification(Specification[User]):
    def is_satisfied_by(self, candidate: User) -> bool:
        return candidate.is_active

class RecentUserSpecification(Specification[User]):
    def __init__(self, days: int = 30):
        self.days = days
    
    def is_satisfied_by(self, candidate: User) -> bool:
        cutoff = datetime.now() - timedelta(days=self.days)
        return candidate.created_at >= cutoff
```

### Built-in Specifications

The framework provides built-in specifications for common use cases:

#### PredicateSpecification

Specification based on a predicate function:

```python
from uno.domain.entity.specification import PredicateSpecification

# Using a lambda function
admin_spec = PredicateSpecification(lambda user: user.role == 'admin')

# Using a named function
def is_premium(user):
    return user.subscription_level == 'premium'

premium_spec = PredicateSpecification(is_premium)
```

#### AttributeSpecification

Specification that checks an attribute value:

```python
from uno.domain.entity.specification import AttributeSpecification

# Simple equality check
name_spec = AttributeSpecification('name', 'John')

# With custom comparator
min_age_spec = AttributeSpecification(
    'age', 
    18, 
    comparator=lambda actual, expected: actual >= expected
)
```

### Composite Specifications

Specifications can be combined to create complex queries:

#### AndSpecification

Combines two specifications with logical AND:

```python
from uno.domain.entity.specification.composite import AndSpecification

# Explicit creation
active_admin_spec = AndSpecification(
    ActiveUserSpecification(), 
    PredicateSpecification(lambda user: user.role == 'admin')
)

# Using the and_ method
active_admin_spec = ActiveUserSpecification().and_(
    PredicateSpecification(lambda user: user.role == 'admin')
)
```

#### OrSpecification

Combines two specifications with logical OR:

```python
from uno.domain.entity.specification.composite import OrSpecification

# Explicit creation
admin_or_premium_spec = OrSpecification(
    AttributeSpecification('role', 'admin'),
    AttributeSpecification('subscription', 'premium')
)

# Using the or_ method
admin_or_premium_spec = AttributeSpecification('role', 'admin').or_(
    AttributeSpecification('subscription', 'premium')
)
```

#### NotSpecification

Negates a specification:

```python
from uno.domain.entity.specification.composite import NotSpecification

# Explicit creation
inactive_spec = NotSpecification(ActiveUserSpecification())

# Using the not_ method
inactive_spec = ActiveUserSpecification().not_()
```

#### AllSpecification and AnySpecification

Work with multiple specifications at once:

```python
from uno.domain.entity.specification.composite import AllSpecification, AnySpecification

# All specifications must be satisfied (AND)
all_spec = AllSpecification([
    ActiveUserSpecification(),
    RecentUserSpecification(),
    AttributeSpecification('role', 'admin')
])

# Any specification can be satisfied (OR)
any_spec = AnySpecification([
    AttributeSpecification('role', 'admin'),
    AttributeSpecification('role', 'manager'),
    AttributeSpecification('role', 'supervisor')
])
```

## Specification Translators

Specification translators convert specifications to different query formats:

### InMemorySpecificationTranslator

Applies specifications to in-memory collections:

```python
from uno.domain.entity.specification.translator import InMemorySpecificationTranslator

translator = InMemorySpecificationTranslator[User]()
specification = ActiveUserSpecification().and_(RecentUserSpecification())

# Get a function that filters a list
filter_func = translator.translate(specification)

# Apply the filter
filtered_users = filter_func(all_users)
```

### SQLSpecificationTranslator

Converts specifications to SQL filter criteria:

```python
from uno.domain.entity.specification.translator import SQLSpecificationTranslator

translator = SQLSpecificationTranslator[User]()
specification = ActiveUserSpecification().and_(
    AttributeSpecification('role', 'admin')
)

# Get SQL filter criteria as a dictionary
sql_filters = translator.translate(specification)
# Result: {'is_active': True, 'role': 'admin'}
```

### PostgreSQLSpecificationTranslator

Extends SQL translator with PostgreSQL-specific features:

```python
from uno.domain.entity.specification.translator import PostgreSQLSpecificationTranslator

translator = PostgreSQLSpecificationTranslator[User]()
specification = AttributeSpecification(
    'name', 
    'John',
    lambda name, value: name.startswith(value)
)

# Get PostgreSQL filter criteria
pg_filters = translator.translate(specification)
# Result: {'name__startswith': 'John'}
```

## Using Specifications with Repositories

Specifications work seamlessly with the Repository pattern:

```python
from uno.domain.entity.repository import EntityRepository
from uno.domain.entity.specification import Specification, AttributeSpecification

# Define specifications
active_spec = AttributeSpecification('is_active', True)
admin_spec = AttributeSpecification('role', 'admin')
recent_spec = RecentUserSpecification(days=7)

# Combine specifications
active_admin_spec = active_spec.and_(admin_spec)
active_recent_admin_spec = active_admin_spec.and_(recent_spec)

# Use with repository
async def find_users():
    # Find all active admins
    active_admins = await user_repository.find(active_admin_spec)
    
    # Find a single user by email
    john = await user_repository.find_one(
        AttributeSpecification('email', 'john@example.com')
    )
    
    # Count users matching a specification
    admin_count = await user_repository.count(admin_spec)
```

## Advanced Techniques

### Custom Comparison Logic

You can create specifications with custom comparison logic:

```python
from uno.domain.entity.specification import AttributeSpecification

# Range comparison
price_range_spec = AttributeSpecification(
    'price',
    (10.0, 50.0),
    lambda price, range_: range_[0] <= price <= range_[1]
)

# String operations
contains_spec = AttributeSpecification(
    'description',
    'premium',
    lambda desc, value: value.lower() in desc.lower()
)

# Date comparison
from datetime import datetime, timedelta

today = datetime.now()
yesterday = today - timedelta(days=1)

recent_order_spec = AttributeSpecification(
    'order_date',
    yesterday,
    lambda date, cutoff: date >= cutoff
)
```

### Combining with the Factory Pattern

You can create a factory to simplify specification creation:

```python
class UserSpecificationFactory:
    @staticmethod
    def active():
        return AttributeSpecification('is_active', True)
    
    @staticmethod
    def admin():
        return AttributeSpecification('role', 'admin')
    
    @staticmethod
    def premium():
        return AttributeSpecification('subscription', 'premium')
    
    @staticmethod
    def recent(days: int = 30):
        return RecentUserSpecification(days)
    
    @staticmethod
    def with_email(email: str):
        return AttributeSpecification('email', email)

# Usage
factory = UserSpecificationFactory()
spec = factory.active().and_(factory.admin().or_(factory.premium()))
```

### Extending the Repository to Work with Translators

Repositories can be extended to handle automatic translation:

```python
from uno.domain.entity.repository import EntityRepository
from uno.domain.entity.specification.translator import SQLSpecificationTranslator

class SQLRepository(EntityRepository[User, UUID]):
    def __init__(self):
        self.translator = SQLSpecificationTranslator[User]()
    
    async def find(self, specification: Specification[User]) -> List[User]:
        # Translate specification to SQL filters
        filters = self.translator.translate(specification)
        
        # Use filters in SQL query
        sql = "SELECT * FROM users WHERE "
        sql += " AND ".join(f"{key} = %s" for key in filters.keys())
        
        # Execute query with filter values
        # ...
```

## Best Practices

### Specification Design

1. Create small, focused specifications that do one thing well
2. Prefer composition over complex, monolithic specifications
3. Add meaningful names and descriptions to your specifications
4. Use factory methods or classes to centralize specification creation
5. Consider performance implications when combining many specifications

### Repository Integration

1. Use specifications for all repository queries
2. Implement efficient translators for your data sources
3. Handle specifications that can't be directly translated
4. Cache common specifications for better performance
5. Document which specifications work with direct translation

### Testing

1. Write unit tests for your custom specifications
2. Test specification combinations thoroughly
3. Verify that translators produce the expected queries
4. Create repository integration tests using specifications
5. Test edge cases with empty and complex specifications

## Example: Domain-Driven Queries

The Specification pattern shines when implementing complex domain queries:

```python
# Define domain-specific specifications
class Product(EntityBase[UUID]):
    name: str
    price: float
    category: str
    inventory_count: int
    is_active: bool

class InStockSpecification(Specification[Product]):
    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.inventory_count > 0

class AffordableSpecification(Specification[Product]):
    def __init__(self, max_price: float):
        self.max_price = max_price
    
    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.price <= self.max_price

class CategorySpecification(Specification[Product]):
    def __init__(self, category: str):
        self.category = category
    
    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.category == self.category

# Create domain queries using composition
def available_products_specification():
    return InStockSpecification().and_(
        AttributeSpecification('is_active', True)
    )

def budget_electronics_specification(budget: float):
    return available_products_specification().and_(
        CategorySpecification('electronics').and_(
            AffordableSpecification(budget)
        )
    )

# Use in repository
async def find_available_budget_electronics(budget: float = 100.0):
    spec = budget_electronics_specification(budget)
    return await product_repository.find(spec)
```

## Real-World Example: E-commerce Filters

Here's how specifications can be used to implement e-commerce filtering:

```python
from uno.domain.entity.specification import (
    Specification, AttributeSpecification, AllSpecification
)

# Define filter specifications
def price_range_specification(min_price: float, max_price: float):
    return AttributeSpecification(
        'price',
        (min_price, max_price),
        lambda price, range_: range_[0] <= price <= range_[1]
    )

def category_specification(category: str):
    return AttributeSpecification('category', category)

def brand_specification(brands: List[str]):
    return AttributeSpecification(
        'brand',
        brands,
        lambda brand, brands: brand in brands
    )

def rating_specification(min_rating: float):
    return AttributeSpecification(
        'rating',
        min_rating,
        lambda rating, min_: rating >= min_
    )

def in_stock_specification():
    return AttributeSpecification(
        'inventory_count',
        0,
        lambda count, _: count > 0
    )

# Apply filters from user input
async def filter_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    brands: Optional[List[str]] = None,
    min_rating: Optional[float] = None,
    in_stock_only: bool = False
):
    specs = []
    
    if category:
        specs.append(category_specification(category))
    
    if min_price is not None and max_price is not None:
        specs.append(price_range_specification(min_price, max_price))
    
    if brands:
        specs.append(brand_specification(brands))
    
    if min_rating is not None:
        specs.append(rating_specification(min_rating))
    
    if in_stock_only:
        specs.append(in_stock_specification())
    
    # Combine all filters with AND
    if specs:
        combined_spec = AllSpecification(specs)
        return await product_repository.find(combined_spec)
    else:
        return await product_repository.list()
```

## Further Reading

- [Specification Pattern by Eric Evans and Martin Fowler](https://martinfowler.com/apsupp/spec.pdf)
- [Domain-Driven Design](https://domaindrivendesign.org/)
- [Repository Pattern](docs/domain/repository_pattern.md)
- [Entity Framework](docs/domain/entity_framework.md)