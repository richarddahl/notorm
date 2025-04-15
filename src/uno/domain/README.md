# Domain-Driven Design for uno Framework

This module implements a domain-driven design (DDD) approach for uno, providing a clear separation of concerns and a rich domain model.

## Architecture Overview

The domain layer is structured using the following components:

### Domain Models

Domain models represent the core business entities in your application. They are implemented as Pydantic models with:

- Strong typing
- Built-in validation
- Clear business semantics
- Rich domain-specific behavior

### Value Objects

Value objects are immutable objects that contain attributes but lack a conceptual identity. They are used to represent concepts within your domain that are defined by their attributes rather than by an identity.

### Aggregates

Aggregates are clusters of domain objects that are treated as a single unit. They encapsulate related domain objects and define boundaries for transactions and consistency.

### Repositories

Repositories provide data access for aggregates, hiding the complexity of data retrieval and persistence behind a collection-like interface.

### Services

Domain services implement business logic that doesn't naturally fit within domain models, especially when the logic operates on multiple aggregates or involves complex workflows.

## Usage Example

```python
from uno.domain.models import User, Address
from uno.domain.repositories import UserRepository
from uno.domain.services import UserService, AuthenticationService
from uno.dependencies import get_service_provider

# Get services from the provider
provider = get_service_provider()
user_service = provider.get_service(UserService)
auth_service = provider.get_service(AuthenticationService)

# Use the services
user = await user_service.get_by_id("user123")
auth_result = await auth_service.authenticate("username", "password")

# Domain model behavior
user.change_email("new@example.com")
await user_service.save(user)

# Complex service operations
new_user = User(
    username="newuser",
    email="user@example.com",
    address=Address(
        street="123 Main St",
        city="Anytown",
        state="CA",
        zip_code="12345"
    )
)
await user_service.register(new_user, send_welcome_email=True)
```

## Key Principles

The domain layer follows these key principles:

1. **Rich Domain Models**: Domain models contain both data and behavior, encapsulating business rules.
2. **Ubiquitous Language**: The code reflects the language of the domain experts.
3. **Bounded Contexts**: Clear boundaries between different parts of the domain.
4. **Dependency Injection**: Services and repositories are designed for DI.
5. **Testability**: All components are designed to be easily testable in isolation.

## Integration with uno Framework

The domain layer integrates with other parts of uno:

- **Database**: Through repositories and the DB manager
- **API Layer**: Through domain services that are used by API endpoints
- **Dependency Injection**: Through the service provider pattern