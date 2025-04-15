# Result Pattern

The Uno framework implements the Result pattern (also known as the Either pattern) for functional error handling. This pattern allows handling errors in a more explicit and functional way, without relying on exceptions.

## Core Concepts

- **Result**: A type that represents either a successful result (`Success`) or a failure (`Failure`)
- **Success**: A successful result with a value
- **Failure**: A failed result with an error
- **Monadic operations**: Operations that allow chaining operations on Results (`map`, `flat_map`)
- **Unwrapping**: Extracting values from Results with fallbacks

## Using Results

### Creating Results

```python
from uno.core.errors import Success, Failure, of, failure, UnoError, ErrorCode

# Create a Success
success = Success(42)  # Explicit constructor
success = of(42)       # Helper function

# Create a Failure
error = UnoError("Something went wrong", ErrorCode.INTERNAL_ERROR)
failure_result = Failure(error)  # Explicit constructor
failure_result = failure(error)  # Helper function
```

### Checking Result Type

```python
result = some_operation()

if result.is_success:```

value = result.value
print(f"Operation succeeded with value: {value}")
```
else:```

error = result.error
print(f"Operation failed with error: {error}")
```
```

### Transforming Results

```python
# Map a success value
result = Success(21)
doubled = result.map(lambda x: x * 2)  # Success(42)

# Map a failure (does nothing)
result = Failure(UnoError("Error", ErrorCode.INTERNAL_ERROR))
doubled = result.map(lambda x: x * 2)  # Still the same Failure

# Flat map (for operations that return Results)
result = Success(21)
doubled = result.flat_map(lambda x: Success(x * 2))  # Success(42)
```

### Extracting Values

```python
# Unwrap (raises if failure)
result = Success(42)
value = result.unwrap()  # 42

# Unwrap with default
result = Failure(error)
value = result.unwrap_or(0)  # 0

# Unwrap with computed default
result = Failure(error)
value = result.unwrap_or_else(lambda e: len(e.message))  # Length of error message
```

### Side Effects

```python
# Execute code on success
result = Success(42)
result.on_success(lambda x: print(f"Got value: {x}"))

# Execute code on failure
result = Failure(error)
result.on_failure(lambda e: print(f"Got error: {e}"))

# Chain these
result.on_success(lambda x: print(f"Got value: {x}")).on_failure(lambda e: print(f"Got error: {e}"))
```

### Converting to Dictionary

```python
# Convert to dictionary (useful for HTTP responses)
result = Success({"id": 1, "name": "John"})
result_dict = result.to_dict()
# {"status": "success", "data": {"id": 1, "name": "John"}}

result = Failure(UnoError("Not found", ErrorCode.RESOURCE_NOT_FOUND))
result_dict = result.to_dict()
# {"status": "error", "error": {"message": "Not found", "error_code": "CORE-0005", "context": {}}}
```

## Converting Exception-Based Code

### Using the from_exception Decorator

```python
from uno.core.errors import from_exception

# Original function that uses exceptions
def divide(a, b):```

if b == 0:```

raise ValueError("Division by zero")
```
return a / b
```

# Converted function that returns a Result
@from_exception
def safe_divide(a, b):```

if b == 0:```

raise ValueError("Division by zero")
```
return a / b
```

# Usage
result = safe_divide(10, 2)  # Success(5.0)
result = safe_divide(10, 0)  # Failure(ValueError("Division by zero"))
```

### Converting Async Functions

```python
from uno.core.errors import from_awaitable
import asyncio

async def fetch_data(url):```

# Some async operation that might fail
if "invalid" in url:```

raise ValueError("Invalid URL")
```
return {"data": "some data"}
```

async def safe_fetch_data(url):```

# Convert awaitable to Result
return await from_awaitable(fetch_data(url))
```

# Usage
async def main():```

result = await safe_fetch_data("https://example.com")  # Success({"data": "some data"})
result = await safe_fetch_data("https://invalid.com")  # Failure(ValueError("Invalid URL"))
```
```

## Combining Multiple Results

### Combining Lists of Results

```python
from uno.core.errors import combine

# All success
results = [Success(1), Success(2), Success(3)]
combined = combine(results)  # Success([1, 2, 3])

# With failure
results = [Success(1), Failure(error), Success(3)]
combined = combine(results)  # Failure(error)
```

### Combining Dictionaries of Results

```python
from uno.core.errors import combine_dict

# All success
results = {```

"a": Success(1),
"b": Success(2),
"c": Success(3)
```
}
combined = combine_dict(results)  # Success({"a": 1, "b": 2, "c": 3})

# With failure
results = {```

"a": Success(1),
"b": Failure(error),
"c": Success(3)
```
}
combined = combine_dict(results)  # Failure(error)
```

## Best Practices

1. **Use Results for operations that can fail**: This makes error handling more explicit
2. **Return early**: Return failures as soon as possible
3. **Use `map` and `flat_map` for transformations**: This maintains the Result context
4. **Provide meaningful defaults with `unwrap_or`**: This makes error handling cleaner
5. **Use the Result pattern in service methods**: This allows callers to decide how to handle errors
6. **Be consistent**: If a function returns a Result, all similar functions should too
7. **Convert to HTTP responses**: Use the `to_dict` method to convert Results to HTTP responses