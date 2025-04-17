# Enhanced Specification Pattern

This document describes the enhanced specification pattern implementation in the Uno framework, which provides a flexible, composable way to express business rules and query criteria.

## Overview

The specification pattern is a design pattern that allows you to express business rules or query criteria as first-class objects. These specifications can be combined using logical operators (AND, OR, NOT) to form complex rules. The enhanced specification pattern in Uno extends this concept with specialized specifications for common query patterns.

## Core Concepts

### Specification Interface

All specifications implement the `Specification[T]` interface, which defines a single method:

```python
def is_satisfied_by(self, entity: T) -> bool:
```

This method checks if an entity satisfies the specification's criteria.

### Composite Specifications

Specifications can be combined using logical operators:

- `AndSpecification`: A specification that is satisfied when both of its components are satisfied
- `OrSpecification`: A specification that is satisfied when either of its components is satisfied
- `NotSpecification`: A specification that is satisfied when its component is not satisfied

These composite specifications allow for building complex rules from simpler ones.

### Basic Specifications

- `AttributeSpecification`: Checks if an attribute equals a specific value
- `PredicateSpecification`: Uses a predicate function to check an entity
- `DictionarySpecification`: Checks if a dictionary matches specific conditions

## Enhanced Specifications

The enhanced specification pattern extends the basic pattern with specialized specifications for common query patterns:

### Value Comparisons

- `ComparableSpecification`: Compares an attribute to a value using various operators (eq, neq, gt, gte, lt, lte)
- `RangeSpecification`: Checks if an attribute falls within a range of values
- `NullSpecification`: Checks if an attribute is null
- `NotNullSpecification`: Checks if an attribute is not null

### Text and String Operations

- `TextMatchSpecification`: Performs text matching operations (contains, starts_with, ends_with, exact, regex)

### Collection Operations

- `InListSpecification`: Checks if an attribute is in a list of values
- `NotInListSpecification`: Checks if an attribute is not in a list of values
- `CollectionSizeSpecification`: Checks the size of a collection attribute
- `CollectionContainsSpecification`: Checks if a collection attribute contains a value

### Date and Time Operations

- `DateRangeSpecification`: Checks if a date attribute falls within a date range
- `RelativeDateSpecification`: Checks if a date attribute falls within a range relative to the current date

### Advanced Operations

- `UUIDSpecification`: Specially handles UUID field comparisons
- `JsonPathSpecification`: Accesses and compares values in JSON/dict fields using a path
- `HasAttributeSpecification`: Checks if an entity has a specific attribute

## Specification Factory

The framework provides a `specification_factory` function to create entity-specific specification factories:

```python
ProductSpec = specification_factory(Product)
```

The `enhance_specification_factory` function extends these factories with methods for all enhanced specifications:

```python
EnhancedProductSpec = enhance_specification_factory(ProductSpec)
```

## Usage Examples

### Creating and Using Basic Specifications

```python
# Create a simple specification
product_in_stock = EnhancedProductSpec.eq("in_stock", True)

# Use the specification
in_stock_products = await repository.find(product_in_stock)
```

### Combining Specifications

```python
# Create composite specifications
electronics_in_stock = (
    EnhancedProductSpec.eq("category", "Electronics")
    .and_(EnhancedProductSpec.eq("in_stock", True))
)

# Use the composite specification
electronics_in_stock_products = await repository.find(electronics_in_stock)
```

### Using Range Specifications

```python
# Create a price range specification
price_range = EnhancedProductSpec.range("price", 100, 200)

# Use the range specification
products_in_range = await repository.find(price_range)
```

### Using Text Matching

```python
# Case-insensitive text search
contains_gaming = EnhancedProductSpec.contains("name", "gaming")

# Case-sensitive regex match
regex_match = EnhancedProductSpec.regex_match("description", r"^High.*performance$", case_sensitive=True)
```

### Using Date Range Specifications

```python
# Date range specification
created_between = EnhancedProductSpec.date_range(
    "created_at", 
    datetime(2023, 1, 1), 
    datetime(2023, 12, 31)
)

# Relative date specification
created_recently = EnhancedProductSpec.created_within_days("created_at", 7)
```

### JSON Path Specifications

```python
# Query nested JSON data
supplier_spec = EnhancedProductSpec.json_path("metadata", ["supplier", "id"], "SUPP001")
on_sale_spec = EnhancedProductSpec.json_path("metadata", ["on_sale"], True)
```

### Complex Search with Multiple Criteria

```python
def search_products(
    keywords=None, 
    category=None, 
    min_price=None, 
    max_price=None, 
    in_stock_only=False
):
    specs = []
    
    if keywords:
        specs.append(EnhancedProductSpec.contains("name", keywords))
    
    if category:
        specs.append(EnhancedProductSpec.eq("category", category))
    
    if min_price is not None and max_price is not None:
        specs.append(EnhancedProductSpec.range("price", min_price, max_price))
    
    if in_stock_only:
        specs.append(EnhancedProductSpec.eq("in_stock", True))
    
    # Combine all specifications with AND
    if not specs:
        return await repository.find_all()
    
    final_spec = specs[0]
    for spec in specs[1:]:
        final_spec = final_spec.and_(spec)
    
    return await repository.find(final_spec)
```

## Integration with SQLAlchemy

The enhanced specification pattern integrates with SQLAlchemy through a translator that converts specifications to SQLAlchemy expressions. This ensures that queries using specifications are executed efficiently at the database level.

```python
# The translator converts specifications to SQLAlchemy WHERE clauses
translator = PostgreSQLSpecificationTranslator(ProductModel)
query = translator.translate(spec)
```

## Benefits

1. **Decoupling**: Separates query criteria from data access mechanisms
2. **Composability**: Enables building complex rules from simple ones
3. **Reusability**: Specifications can be reused across different parts of the application
4. **Testability**: Specifications can be tested in isolation
5. **Readability**: Expressive, domain-focused expressions of business rules
6. **Database Efficiency**: Translates to efficient SQL queries

## Implementation Details

The specification pattern implementation follows these principles:

1. Each specification type implements the `is_satisfied_by` method
2. Composite specifications delegate to their component specifications
3. The PostgreSQL translator handles the conversion of specifications to SQL expressions
4. Repository implementations use specifications for filtering
5. The specification factory creates entity-specific specification factories
6. The enhanced specification factory adds methods for all enhanced specifications

## Best Practices

1. Use entity-specific specification factories
2. Prefer named methods from enhanced specification factories over direct instantiation
3. Create domain-specific query methods in repositories that use specifications internally
4. Write unit tests for complex specifications
5. When composing specifications, start with the most restrictive ones
6. Use appropriate specification types for different query patterns
7. Leverage JSON path specifications for querying nested data structures
8. Prefer the specification pattern over raw query builders for complex domain queries

## Framework Integration

The specification pattern integrates with:

- Repository pattern implementation
- Domain model
- SQLAlchemy ORM
- PostgreSQL database
- Unit of work pattern
- Result pattern for error handling

By using the enhanced specification pattern, you can express complex business rules and query criteria in a clean, composable, and maintainable way.