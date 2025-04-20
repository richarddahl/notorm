# Result Pattern

The Result pattern is a powerful approach to error handling in the Uno framework that provides explicit success and failure paths without relying on exceptions.

## Overview

The `Result` pattern encapsulates the outcome of an operation that can either succeed or fail. Instead of using exceptions for control flow, the Result pattern makes error handling explicit and type-safe.

Key benefits:
- Clear distinction between success and failure paths
- Type safety for both success and error values
- No reliance on exceptions for expected error cases
- Improved error context and messaging
- Composable error handling with monadic operations

## Core Components

### Result Class

The `Result` class is the foundation of the pattern:

```python
from typing import Generic, TypeVar, Optional, Callable, Any
from uno.core.errors.base import BaseError

T = TypeVar('T')  # Success value type
E = TypeVar('E')  # Error value type

class Result(Generic[T, E]):
    """
    Represents the result of an operation that can either succeed with a value
    or fail with an error.
    """
    
    def __init__(self, value: Optional[T] = None, error: Optional[E] = None):
        self._value = value
        self._error = error
        self._is_success = error is None
    
    @property
    def is_success(self) -> bool:
        """Whether the result is a success."""
        return self._is_success
    
    @property
    def value(self) -> Optional[T]:
        """The success value, if any."""
        return self._value
    
    @property
    def error(self) -> Optional[E]:
        """The error value, if any."""
        return self._error
        
    def __str__(self) -> str:
        if self.is_success:
            return f"Success({self.value})"
        return f"Failure({self.error})"
```

### Success and Failure Classes

For convenience, the framework provides `Success` and `Failure` classes:

```python
class Success(Result[T, E]):
    """
    Represents a successful result with a value.
    """
    
    def __init__(self, value: T):
        super().__init__(value=value, error=None)

class Failure(Result[T, E]):
    """
    Represents a failed result with an error.
    """
    
    def __init__(self, error: E):
        super().__init__(value=None, error=error)
```

## Basic Usage

### Returning Results

```python
from uno.core.errors.result import Result, Success, Failure
from typing import List

def find_user_by_email(email: str) -> Result[User, str]:
    """Find a user by email."""
    user = user_repository.find_by_email(email)
    
    if user:
        return Success(user)
    else:
        return Failure(f"User with email {email} not found")

def get_users_by_department(department: str) -> Result[list[User], str]:
    """Get all users in a department."""
    users = user_repository.find_by_department(department)
    
    if not users:
        return Failure(f"No users found in department {department}")
    
    return Success(users)
```

### Handling Results

```python
# Check result with is_success
result = find_user_by_email("user@example.com")
if result.is_success:
    user = result.value
    # Process the user
else:
    error_message = result.error
    # Handle the error

# Pattern matching (Python 3.10+)
match find_user_by_email("user@example.com"):
    case Success(user):
        # Process the user
        print(f"Found user: {user.username}")
    case Failure(error):
        # Handle the error
        print(f"Error: {error}")
```

## Monadic Operations

The Result class provides monadic operations for composing operations that return Results:

### Map

The `map` method applies a function to the success value:

```python
from uno.core.errors.result import Result

def get_user_email(user_id: str) -> Result[str, str]:
    """Get a user's email."""
    result = find_user_by_id(user_id)
    
    # Map the user to their email if the result is a success
    return result.map(lambda user: user.email)
```

### Bind

The `bind` method chains operations that return Results:

```python
from uno.core.errors.result import Result

def reset_password(email: str, new_password: str) -> Result[bool, str]:
    """Reset a user's password."""
    # Chain multiple operations that return Results
    return (
        find_user_by_email(email)
        .bind(lambda user: update_user_password(user, new_password))
    )

# More complex example
def transfer_funds(from_account_id: str, to_account_id: str, amount: float) -> Result[Transaction, str]:
    """Transfer funds between accounts."""
    return (
        find_account_by_id(from_account_id)
        .bind(lambda from_account: validate_sufficient_funds(from_account, amount)
            .bind(lambda _: find_account_by_id(to_account_id)
                .bind(lambda to_account: create_transaction(from_account, to_account, amount))
            )
        )
    )
```

### Map Error

The `map_error` method transforms the error value:

```python
from uno.core.errors.result import Result

def find_user(user_id: str) -> Result[User, str]:
    """Find a user by ID."""
    # ... implementation
    
# Transform string errors to more structured errors
result = find_user("123").map_error(lambda err: UserNotFoundError(err))
```

### Recover

The `recover` method provides a fallback for errors:

```python
from uno.core.errors.result import Result

def get_user_profile(user_id: str) -> Result[Profile, str]:
    """Get a user's profile, falling back to a default profile if not found."""
    return find_user_profile(user_id).recover(lambda _: create_default_profile())
```

## Combining Results

### Combine Results

```python
from uno.core.errors.result import Result, combine_results
from typing import List

def get_all_team_members(team_id: str) -> Result[list[User], str]:
    """Get all members of a team."""
    # Get the team
    team_result = find_team_by_id(team_id)
    if not team_result.is_success:
        return team_result.map_error(lambda err: f"Team error: {err}")
    
    team = team_result.value
    
    # Get all members
    member_results = [find_user_by_id(member_id) for member_id in team.member_ids]
    
    # Combine all results
    combined_result = combine_results(member_results)
    
    return combined_result
```

### Collect Results

```python
from uno.core.errors.result import Result, collect_results
from typing import List, Dict

def validate_order(order_data: Dict[str, Any]) -> Result[Dict[str, Any], list[str]]:
    """Validate an order, collecting all validation errors."""
    validation_results = [
        validate_customer(order_data.get("customer_id")),
        validate_items(order_data.get("items")),
        validate_shipping_address(order_data.get("shipping_address")),
        validate_payment_method(order_data.get("payment_method"))
    ]
    
    # Collect all errors
    result = collect_results(validation_results)
    
    if result.is_success:
        return Success(order_data)
    else:
        return Failure(result.error)
```

## Async Support

The framework provides support for async functions that return Results:

```python
from uno.core.errors.result import Result, async_result
from typing import List

@async_result
async def find_user_by_email(email: str) -> Result[User, str]:
    """Find a user by email asynchronously."""
    user = await user_repository.find_by_email(email)
    
    if user:
        return Success(user)
    else:
        return Failure(f"User with email {email} not found")

# Using async Results
async def process_user(email: str) -> None:
    result = await find_user_by_email(email)
    
    if result.is_success:
        user = result.value
        await process_user_data(user)
    else:
        await log_error(result.error)
```

### Async Bind

```python
from uno.core.errors.result import Result, Success, Failure

async def reset_password(email: str, new_password: str) -> Result[bool, str]:
    """Reset a user's password asynchronously."""
    # Find user
    user_result = await find_user_by_email(email)
    if not user_result.is_success:
        return user_result
    
    # Update password
    update_result = await update_user_password(user_result.value, new_password)
    return update_result

# Alternative with async_bind
from uno.core.errors.result import async_bind

async def reset_password_v2(email: str, new_password: str) -> Result[bool, str]:
    """Reset a user's password using async_bind."""
    return await async_bind(
        await find_user_by_email(email),
        lambda user: update_user_password(user, new_password)
    )
```

## Integration with FastAPI

The Result pattern integrates well with FastAPI:

```python
from fastapi import APIRouter, HTTPException
from uno.api.endpoint import BaseEndpoint
from uno.api.endpoint.response import DataResponse
from uno.core.errors.result import Result

router = APIRouter()
endpoint = BaseEndpoint(router=router)

@endpoint.router.get("/users/{user_id}")
async def get_user(user_id: str):
    result = await user_service.get_user(user_id)
    
    if result.is_success:
        return DataResponse(data=result.value)
    else:
        raise HTTPException(status_code=404, detail=result.error)

# More elegant with middleware
from uno.api.endpoint.middleware import setup_error_handlers

# In your FastAPI app setup
app = FastAPI()
setup_error_handlers(app)

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    result = await user_service.get_user(user_id)
    
    if not result.is_success:
        # The error handler will convert this to the appropriate HTTP response
        raise result.error
    
    return result.value
```

## Working with Custom Error Types

You can use custom error types with Results:

```python
from uno.core.errors.base import BaseError
from uno.core.errors.result import Result, Success, Failure

class UserError(BaseError):
    """Base class for user-related errors."""
    pass

class UserNotFoundError(UserError):
    """Error raised when a user is not found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            f"User with ID {user_id} not found",
            "USER_NOT_FOUND",
            status_code=404
        )
        self.user_id = user_id

def find_user(user_id: str) -> Result[User, UserError]:
    """Find a user by ID."""
    user = user_repository.find_by_id(user_id)
    
    if user:
        return Success(user)
    else:
        return Failure(UserNotFoundError(user_id))
```

## Result Conversion Utilities

### From Option

Convert an Optional value to a Result:

```python
from uno.core.errors.result import Result, from_option
from typing import Optional

def find_user(user_id: str) -> Optional[User]:
    """Find a user by ID, returning None if not found."""
    return user_repository.find_by_id(user_id)

# Convert to Result
result = from_option(find_user("123"), lambda: f"User with ID 123 not found")
```

### From Exception

Convert exception-based code to Result:

```python
from uno.core.errors.result import Result, from_exception

def divide(a: float, b: float) -> Result[float, str]:
    """Divide a by b, returning a Result."""
    return from_exception(
        lambda: a / b,
        lambda e: f"Division error: {str(e)}"
    )
```

### To Option

Convert a Result to an Optional value:

```python
from typing import Optional
from uno.core.errors.result import Result, to_option

def get_user_email(user_id: str) -> Optional[str]:
    """Get a user's email, returning None if the user is not found."""
    result = find_user_by_id(user_id).map(lambda user: user.email)
    return to_option(result)
```

## Domain Service Example

```python
from uuid import UUID
from uno.domain.entity import DomainService
from uno.core.errors.result import Result, Success, Failure
from typing import List

class UserService(DomainService[User, UUID]):
    """Domain service for user operations."""
    
    async def create_user(self, username: str, email: str, password: str) -> Result[User, str]:
        """Create a new user."""
        # Check if username exists
        existing_user = await self._repository.find_by_username(username)
        if existing_user:
            return Failure(f"Username '{username}' is already taken")
        
        # Check if email exists
        existing_email = await self._repository.find_by_email(email)
        if existing_email:
            return Failure(f"Email '{email}' is already registered")
        
        # Create user
        user = User.create(username, email, password_hash)
        created_user = await self._repository.add(user)
        
        return Success(created_user)
    
    async def update_email(self, user_id: UUID, new_email: str) -> Result[User, str]:
        """Update a user's email."""
        # Get user
        user = await self._repository.get_by_id(user_id)
        if not user:
            return Failure(f"User with ID {user_id} not found")
        
        # Check if email exists
        existing_email = await self._repository.find_by_email(new_email)
        if existing_email and existing_email.id != user_id:
            return Failure(f"Email '{new_email}' is already registered")
        
        # Update email
        user.email = new_email
        updated_user = await self._repository.update(user)
        
        return Success(updated_user)
```

## Application Service Example

```python
from uuid import UUID
from uno.application.service import ApplicationService
from uno.core.errors.result import Result, Success, Failure
from uno.core.uow import UnitOfWork

class OrderApplicationService(ApplicationService):
    """Application service for order operations."""
    
    def __init__(
        self,
        order_service: OrderService,
        inventory_service: InventoryService,
        payment_service: PaymentService,
        unit_of_work: UnitOfWork
    ):
        self.order_service = order_service
        self.inventory_service = inventory_service
        self.payment_service = payment_service
        self.unit_of_work = unit_of_work
    
    async def place_order(
        self, 
        customer_id: UUID, 
        items: list[dict[str, Any]],
        payment_details: Dict[str, Any]
    ) -> Result[OrderDTO, str]:
        """Place an order with payment."""
        
        async with self.unit_of_work:
            # Validate inventory
            inventory_result = await self.inventory_service.check_availability(items)
            if not inventory_result.is_success:
                return Failure(f"Inventory check failed: {inventory_result.error}")
            
            # Create order
            order_result = await self.order_service.create_order(
                customer_id=customer_id,
                items=items
            )
            
            if not order_result.is_success:
                return Failure(f"Order creation failed: {order_result.error}")
            
            order = order_result.value
            
            # Process payment
            payment_result = await self.payment_service.process_payment(
                order_id=order.id,
                amount=order.total_amount,
                payment_details=payment_details
            )
            
            if not payment_result.is_success:
                return Failure(f"Payment failed: {payment_result.error}")
            
            # Update inventory
            await self.inventory_service.reserve_items(items)
            
            # Convert to DTO
            order_dto = OrderDTO.from_entity(order)
            
            return Success(order_dto)
```

## Error Handling Strategy

When using the Result pattern, consider these strategies:

1. **Domain Services**: Return Results for all operations that can fail
2. **Application Services**: Handle Results from domain services, returning DTOs
3. **API Layer**: Convert Results to HTTP responses
4. **Infrastructure Layer**: Wrap third-party exceptions in Results

Here's a tiered approach to error handling:

```
┌──────────────────┐
│ API Layer        │ ◄── Converts Results to HTTP responses
├──────────────────┤
│ Application      │ ◄── Orchestrates operations, handles Results from domain
├──────────────────┤
│ Domain           │ ◄── Returns Results for business rule violations
├──────────────────┤
│ Infrastructure   │ ◄── Wraps exceptions in Results
└──────────────────┘
```

## Best Practices

1. **Return Results Consistently**: Use Results for any operation that can fail predictably
2. **Use Strong Types**: Prefer strongly typed errors over strings
3. **Provide Context**: Include contextual information in error messages
4. **Chain Operations**: Use `bind` to chain operations that return Results
5. **Transform Errors**: Use `map_error` to convert errors between layers
6. **Combine Multiple Results**: Use `combine_results` when needed
7. **Handle All Cases**: Always handle both success and failure paths
8. **Avoid Mixing Paradigms**: Don't mix Results with exceptions for control flow
9. **Be Descriptive**: Use clear error messages that provide actionable information
10. **Keep It Simple**: Don't overuse monadic operations if simple conditionals are clearer

## Conclusion

The Result pattern provides a powerful way to handle errors in a type-safe, explicit manner. By using Results, you can:

- Clearly separate success and failure paths
- Provide rich context for errors
- Compose operations with monadic functions
- Create more maintainable code with explicit error handling

For more information, see the related documentation:

- [Error Handling Framework](overview.md): Overview of error handling in Uno
- [Error Catalog](catalog.md): Working with the error catalog
- [Domain Services](../../domain/service_pattern.md): Using Results in domain services