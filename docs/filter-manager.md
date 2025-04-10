

### Dynamic Filter Generation

Generate filters dynamically based on user permissions:

```python
from fastapi import FastAPI, Depends, Security
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_user_permissions(token: str) -> List[str]:
    """Get user permissions from token."""
    # Implementation depends on your auth system
    return ["read:customers", "write:customers"]

def get_allowed_filters(permissions: List[str]) -> Dict[str, Any]:
    """Get allowed filters based on user permissions."""
    base_filters = {"name", "email"}
    
    if "admin:customers" in permissions:
        # Admins can see all fields
        return {
            "include_fields": None,  # All fields
            "exclude_fields": []
        }
    elif "read:customers" in permissions:
        # Regular users have limited fields
        return {
            "include_fields": base_filters,
            "exclude_fields": ["created_at", "modified_at", "deleted_at"]
        }
    else:
        # Minimal access
        return {
            "include_fields": ["name"],
            "exclude_fields": []
        }

@app.get("/api/v1/customers")
async def list_customers(
    token: str = Depends(oauth2_scheme)
):
    # Get user permissions
    permissions = get_user_permissions(token)
    
    # Get allowed filters
    filter_config = get_allowed_filters(permissions)
    
    # Create dynamic filter manager
    dynamic_filter_manager = UnoFilterManager()
    
    # Create filters with permissions
    if filter_config["include_fields"]:
        # Only include specific fields
        dynamic_filter_manager.create_filters_from_table(
            CustomerModel,
            exclude_fields=[f for f in CustomerModel.__table__.columns.keys() 
                           if f not in filter_config["include_fields"]]
        )
    else:
        # Include all except excluded
        dynamic_filter_manager.create_filters_from_table(
            CustomerModel,
            exclude_fields=filter_config["exclude_fields"]
        )
    
    # Create and validate parameters
    # (Implementation depends on how you're handling query params)
    
    return await Customer.filter(filters=validated_filters)
```

## Testing

When testing the filter manager, focus on validating filter creation and parameter validation:

```python
import pytest
from uno.filter_manager import UnoFilterManager, FilterValidationError

def test_filter_creation():
    """Test creating filters from a model."""
    # Setup
    filter_manager = UnoFilterManager()
    
    # Create filters
    filters = filter_manager.create_filters_from_table(CustomerModel)
    
    # Assert filters were created
    assert "NAME" in filters
    assert "EMAIL" in filters
    assert "AGE" in filters
    assert "IS_ACTIVE" in filters
    
    # Check filter properties
    assert filters["NAME"].data_type == "str"
    assert "contains" in filters["NAME"].lookups
    assert filters["AGE"].data_type == "int"
    assert "gt" in filters["AGE"].lookups
    assert filters["IS_ACTIVE"].data_type == "bool"
    assert "equal" in filters["IS_ACTIVE"].lookups

def test_filter_params_creation():
    """Test creating filter parameters."""
    # Setup
    filter_manager = UnoFilterManager()
    filter_manager.create_filters_from_table(CustomerModel)
    
    # Create filter params model
    FilterParams = filter_manager.create_filter_params(Customer)
    
    # Create params
    params = FilterParams(
        name="John",
        age__gt=25,
        is_active=True
    )
    
    # Assert params were created correctly
    assert params.name == "John"
    assert params.age__gt == 25
    assert params.is_active == True

def test_filter_validation():
    """Test filter parameter validation."""
    # Setup
    filter_manager = UnoFilterManager()
    filter_manager.create_filters_from_table(CustomerModel)
    
    # Create filter params model
    FilterParams = filter_manager.create_filter_params(Customer)
    
    # Valid params
    valid_params = FilterParams(
        name="John",
        age__gt=25,
        is_active=True
    )
    
    # Invalid params (invalid lookup)
    invalid_params = FilterParams(
        name__invalid="John"  # "invalid" is not a valid lookup
    )
    
    # Assert validation succeeds for valid params
    validated = filter_manager.validate_filter_params(valid_params, Customer)
    assert len(validated) == 3
    
    # Assert validation fails for invalid params
    with pytest.raises(FilterValidationError):
        filter_manager.validate_filter_params(invalid_params, Customer)
```

## Best Practices

1. **Limit Filter Complexity**: Avoid overly complex filter combinations that could impact performance.

2. **Add Pagination**: Always include limit and offset parameters to prevent returning too many results.

3. **Document Available Filters**: Document which filters and lookups are available for each endpoint.

4. **Validate Input**: Validate filter parameters before constructing database queries.

5. **Handle Errors Gracefully**: Provide clear error messages when filter validation fails.

6. **Set Reasonable Defaults**: Use sensible default values for limit and offset.

7. **Consider Security**: Implement field-level security to prevent unauthorized access to sensitive data.

8. **Optimize Queries**: Monitor query performance and optimize filters that generate inefficient queries.

9. **Test Edge Cases**: Test filter combinations, empty results, and pagination edge cases.

10. **Use Type Annotations**: Use proper type annotations for better IDE support and type checking.# UnoFilterManager

The `UnoFilterManager` class is responsible for creating and managing filters for `UnoObj` models. It provides a robust system for generating dynamic database queries based on model fields.

## Overview

The filter manager handles:

- Creating filters from model columns
- Generating filter parameter schemas for API endpoints
- Validating filter parameters
- Converting filter parameters to database queries

## Basic Usage

### Creating a Filter Manager

```python
from uno.filter_manager import UnoFilterManager

# Create a filter manager
filter_manager = UnoFilterManager()
```

### Creating Filters from a Model

```python
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column

# Define a model
class CustomerModel(UnoModel):
    __tablename__ = "customer"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    age: Mapped[int] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

# Create filters
filters = filter_manager.create_filters_from_table(CustomerModel)

# Print the available filters
for filter_name, filter_obj in filters.items():
    print(f"Filter: {filter_name}, Data Type: {filter_obj.data_type}, Lookups: {filter_obj.lookups}")
```

### Creating Filter Parameters

```python
from uno.obj import UnoObj

# Define a business object
class Customer(UnoObj[CustomerModel]):
    model = CustomerModel
    # ...

# Create filter parameters schema
FilterParamModel = filter_manager.create_filter_params(Customer)

# Create filter parameters
filter_params = FilterParamModel(
    limit=10,
    offset=0,
    name="John",
    age__gt=25,
    is_active=True
)
```

### Validating Filter Parameters

```python
# Validate filter parameters
try:
    validated_filters = filter_manager.validate_filter_params(filter_params, Customer)
    
    # Use the validated filters
    for filter_tuple in validated_filters:
        print(f"Filter: {filter_tuple.label}, Value: {filter_tuple.val}, Lookup: {filter_tuple.lookup}")
        
except FilterValidationError as e:
    print(f"Error validating filters: {e}")
```

## Filter Operations

The filter manager supports various lookup operations depending on the field type:

### Text Fields

- `equal` - Exact match
- `not_equal` - Not equal
- `contains` - Contains substring (case-sensitive)
- `i_contains` - Contains substring (case-insensitive)
- `not_contains` - Does not contain substring (case-sensitive)
- `not_i_contains` - Does not contain substring (case-insensitive)
- `starts_with` - Starts with (case-sensitive)
- `i_starts_with` - Starts with (case-insensitive)
- `ends_with` - Ends with (case-sensitive)
- `i_ends_with` - Ends with (case-insensitive)
- `null` - Is null
- `not_null` - Is not null

### Numeric Fields

- `equal` - Equal to
- `not_equal` - Not equal to
- `gt` - Greater than
- `gte` - Greater than or equal to
- `lt` - Less than
- `lte` - Less than or equal to
- `in` - In a list of values
- `not_in` - Not in a list of values
- `null` - Is null
- `not_null` - Is not null

### Boolean Fields

- `equal` - Equal to
- `not_equal` - Not equal to
- `null` - Is null
- `not_null` - Is not null

### DateTime Fields

- `equal` - Equal to
- `not_equal` - Not equal to
- `after` - After date
- `at_or_after` - At or after date
- `before` - Before date
- `at_or_before` - At or before date
- `in` - In a list of dates
- `not_in` - Not in a list of dates
- `null` - Is null
- `not_null` - Is not null

## Advanced Usage

### Excluding Fields from Filtering

You can exclude specific fields from generating filters:

```python
# Exclude certain fields
excluded_fields = ["created_at", "modified_at", "deleted_at"]
filters = filter_manager.create_filters_from_table(
    CustomerModel,
    exclude_fields=excluded_fields
)
```

### Excluding Models from Filtering

You can exclude entire models from generating filters:

```python
# Exclude entire model
filters = filter_manager.create_filters_from_table(
    CustomerModel,
    exclude_from_filters=True
)
```

### Custom Filter Creation

You can create filters manually for special cases:

```python
from uno.filter import UnoFilter, text_lookups
from uno.utilities import snake_to_camel

# Create a custom filter
custom_filter = UnoFilter(
    source_node_label=snake_to_camel("customer"),
    source_meta_type_id="customer",
    label="CUSTOM_FILTER",
    target_node_label=snake_to_camel("custom"),
    target_meta_type_id="customer",
    data_type="str",
    raw_data_type=str,
    lookups=text_lookups,
    source_path_fragment="(s:Customer)-[:CUSTOM_FILTER]",
    middle_path_fragment="(:Customer)-[:CUSTOM_FILTER]",
    target_path_fragment="(t:Custom)",
    documentation="A custom filter for special queries"
)

# Add to filter manager
filter_manager.filters["CUSTOM_FILTER"] = custom_filter
```

## Integration with FastAPI

The filter manager integrates with FastAPI to provide query parameter validation:

```python
from fastapi import FastAPI, Depends
from typing import List

app = FastAPI()

# Define the filter parameters
FilterParams = filter_manager.create_filter_params(Customer)

@app.get("/api/v1/customers")
async def list_customers(
    filters: FilterParams = Depends()
):
    # Validate filters
    validated_filters = filter_manager.validate_filter_params(filters, Customer)
    
    # Get customers with filters
    customers = await Customer.filter(filters=validated_filters)
    
    # Return results
    return customers
```

## Common Patterns

### Combined Filters

Build complex queries by combining multiple filters:

```python
# Create filter parameters for a complex query
filter_params = FilterParamModel(
    # Pagination
    limit=20,
    offset=0,
    
    # Sorting
    order_by="name",
    
    # Filtering
    name__contains="Smith",
    age__gte=21,
    age__lte=65,
    is_active=True,
    created_at__after="2023-01-01T00:00:00Z",
)
```

### Search Across Multiple Fields

Create a search endpoint that looks across multiple fields:

```python
from fastapi import FastAPI, Query
from typing import List, Optional

app = FastAPI()

@app.get("/api/v1/customers/search")
async def search_customers(
    q: Optional[str] = Query(None, min_length=3),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Search customers across multiple fields."""
    if not q:
        # Return paginated results if no search term
        filter_params = FilterParamModel(limit=limit, offset=offset)
    else:
        # Build OR conditions across multiple fields
        # Note: This would require custom implementation in the filter_manager
        # to support OR conditions between different fields
        name_params = FilterParamModel(name__i_contains=q, limit=limit, offset=offset)
        email_params = FilterParamModel(email__i_contains=q, limit=limit, offset=offset)
        
        # Combine results (would need implementation)
        # This is a simplified example - actual implementation would depend on your database
        name_results = await Customer.filter(filters=name_params)
        email_results = await Customer.filter(filters=email_params)
        
        # Deduplicate and return combined results
        # (simplified implementation)
        return list({c.id: c for c in name_results + email_results}.values())
    
    # Standard filtering
    validated_filters = filter_manager.validate_filter_params(filter_params, Customer)
    return await Customer.filter(filters=validated_filters)