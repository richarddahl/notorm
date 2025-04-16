# Business Logic Layer

The Business Logic Layer in uno provides a clean interface for implementing business rules and validation logic, while abstracting away database operations. It forms the core of your application, implementing the domain logic that drives your business processes.

## In This Section

- [Domain Guide](guide.md) - Guide to Domain-Driven Design approach
- [Schema](schema.md) - Schema management for flexible data serialization

## Overview

The Business Logic Layer in uno is designed using Domain-Driven Design principles to separate business concerns from database and API concerns, allowing you to focus on implementing domain-specific behavior. It provides a rich set of tools for modeling your business domain, ensuring data integrity, and integrating with your application's infrastructure.

## Key Concepts

### Domain Entities

Domain entities are the core building blocks of your business domain. They represent the key concepts in your domain and encapsulate both data and behavior:

- **Identity**: Each entity has a unique identity that distinguishes it from other entities
- **Lifecycle**: Entities have a lifecycle that includes creation, modification, and potentially deletion
- **Business Rules**: Entities enforce business rules and invariants
- **Domain Events**: Entities can emit domain events to indicate significant state changes

### Value Objects

Value objects represent concepts in your domain that are defined by their attributes rather than their identity:

- **Immutability**: Value objects are immutable once created
- **Validation**: Validation is performed during construction
- **No Identity**: Value objects are equal when all their attributes are equal
- **Self-Contained**: Value objects can contain business logic related to the concept they represent

### Aggregates

Aggregates group entities and value objects into a consistency boundary:

- **Aggregate Root**: An entity that acts as the entry point to the aggregate
- **Consistency Boundary**: Ensures business rules that span multiple entities are enforced
- **Transactional Unit**: Operations on an aggregate should be atomic
- **Reference by Identity**: Other aggregates refer to aggregates by their identity

### Repositories

Repositories provide a collection-like interface to access domain entities:

- **Data Access Abstraction**: Hide the details of how entities are stored and retrieved
- **Domain-Focused API**: Provide methods that match domain concepts
- **Persistence Ignorance**: Domain objects are not coupled to persistence mechanisms
- **Transaction Support**: Support for atomic operations

### Domain Services

Domain services implement operations that don't naturally belong to any entity:

- **Stateless Operations**: Services are typically stateless
- **Domain Logic**: Implement complex operations that involve multiple entities
- **Dependency Injection**: Receive dependencies through constructor injection
- **Pure Domain Logic**: Focus on business rules, not infrastructure concerns

### Application Services

Application services coordinate domain operations and infrastructure:

- **Orchestration**: Coordinate domain objects and infrastructure services
- **Transaction Management**: Manage transactions for domain operations
- **Security**: Apply authorization and authentication
- **Error Handling**: Provide standardized error handling
- **Input/Output Transformation**: Transform between DTOs and domain objects

## Getting Started

### 1. Define Your Domain Entities and Value Objects

```python
from uno.domain.core import Entity, ValueObject
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4

# Define a value object
@dataclass(frozen=True)
class EmailAddress(ValueObject):
    value: str
    
    def __post_init__(self):
        if not self.value or "@" not in self.value:
            raise ValueError("Invalid email address")
    
    def get_domain(self) -> str:
        return self.value.split("@")[1]

# Define an entity
class Customer(Entity[UUID]):
    def __init__(
        self,
        id: UUID,
        name: str,
        email: EmailAddress,
        phone: Optional[str] = None
    ):
        super().__init__(id=id)
        
        # Validate invariants
        if not name:
            raise ValueError("Customer name cannot be empty")
            
        # Set properties
        self.name = name
        self.email = email
        self.phone = phone
        
    @classmethod
    def create(cls, name: str, email: str, phone: Optional[str] = None) -> "Customer":
        """Factory method to create a new customer."""
        return cls(
            id=uuid4(),
            name=name,
            email=EmailAddress(email),
            phone=phone
        )
        
    def update_email(self, new_email: str) -> None:
        """Update customer email address."""
        old_email = self.email
        self.email = EmailAddress(new_email)
        
        # Register a domain event
        self.register_event(CustomerEmailUpdatedEvent(
            customer_id=self.id,
            old_email=old_email.value,
            new_email=new_email
        ))
```

### 2. Define Your Repositories

```python
from uno.domain.repository import Repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

class CustomerRepository(Repository[Customer, UUID]):
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get(self, id: UUID) -> Optional[Customer]:
        """Get a customer by ID."""
        result = await self.session.execute(
            select(CustomerModel).where(CustomerModel.id == str(id))
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
            
        return self._to_entity(model)
        
    async def find_by_email(self, email: str) -> Optional[Customer]:
        """Find a customer by email address."""
        result = await self.session.execute(
            select(CustomerModel).where(CustomerModel.email == email)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
            
        return self._to_entity(model)
        
    async def save(self, customer: Customer) -> None:
        """Save a customer to the database."""
        model = CustomerModel(
            id=str(customer.id),
            name=customer.name,
            email=customer.email.value,
            phone=customer.phone
        )
        self.session.merge(model)
        await self.session.flush()
        
        # Process domain events
        await self._process_events(customer)
        
    def _to_entity(self, model: CustomerModel) -> Customer:
        """Convert a database model to a domain entity."""
        return Customer(
            id=UUID(model.id),
            name=model.name,
            email=EmailAddress(model.email),
            phone=model.phone
        )
        
    async def _process_events(self, customer: Customer) -> None:
        """Process domain events."""
        for event in customer.events:
            # Handle each event appropriately
            if isinstance(event, CustomerEmailUpdatedEvent):
                # Process email update event
                pass
                
        # Clear processed events
        customer.clear_events()
```

### 3. Implement Application Services

```python
from uno.core.result import Result, Success, Failure
from uno.core.async_context import db_transaction

class CustomerService:
    def __init__(self, repository: CustomerRepository):
        self.repository = repository
        
    async def get_customer(self, customer_id: UUID) -> Result[Customer]:
        """Get a customer by ID."""
        customer = await self.repository.get(customer_id)
        if not customer:
            return Failure(f"Customer {customer_id} not found")
        return Success(customer)
        
    @db_transaction
    async def create_customer(
        self, name: str, email: str, phone: Optional[str] = None
    ) -> Result[Customer]:
        """Create a new customer."""
        try:
            # Check for existing customer with same email
            existing = await self.repository.find_by_email(email)
            if existing:
                return Failure("A customer with this email already exists")
                
            # Create new customer
            customer = Customer.create(name=name, email=email, phone=phone)
            
            # Save to repository
            await self.repository.save(customer)
            return Success(customer)
        except ValueError as e:
            return Failure(str(e))
        except Exception as e:
            return Failure(f"Failed to create customer: {str(e)}")
            
    @db_transaction
    async def update_email(
        self, customer_id: UUID, new_email: str
    ) -> Result[Customer]:
        """Update a customer's email address."""
        # Get the customer
        result = await self.get_customer(customer_id)
        if result.is_failure:
            return result
            
        customer = result.value
        
        try:
            # Update email
            customer.update_email(new_email)
            
            # Save changes
            await self.repository.save(customer)
            return Success(customer)
        except ValueError as e:
            return Failure(str(e))
        except Exception as e:
            return Failure(f"Failed to update email: {str(e)}")
```

### 4. Integrate with API Layer

```python
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from uno.dependencies.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from uno.domain.api_integration import domain_endpoint

router = APIRouter(prefix="/customers", tags=["Customers"])

# Data transfer objects
class CustomerDTO(BaseModel):
    id: UUID
    name: str
    email: str
    phone: Optional[str] = None
    
    @classmethod
    def from_entity(cls, customer: Customer) -> "CustomerDTO":
        return cls(
            id=customer.id,
            name=customer.name,
            email=customer.email.value,
            phone=customer.phone
        )

class CreateCustomerRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

# Endpoints
@router.get("/{customer_id}", response_model=CustomerDTO)
@domain_endpoint
async def get_customer(
    customer_id: UUID,
    customer_service: CustomerService = Depends()
):
    """Get a customer by ID."""
    result = await customer_service.get_customer(customer_id)
    return CustomerDTO.from_entity(result.value)

@router.post("/", response_model=CustomerDTO, status_code=201)
@domain_endpoint
async def create_customer(
    request: CreateCustomerRequest,
    customer_service: CustomerService = Depends()
):
    """Create a new customer."""
    result = await customer_service.create_customer(
        name=request.name,
        email=request.email,
        phone=request.phone
    )
    return CustomerDTO.from_entity(result.value)
```

## Best Practices

1. **Focus on the Domain**: Model your business domain accurately, focusing on the language and concepts used by domain experts.

2. **Enforce Invariants**: Domain entities should enforce their own invariants (business rules that must always be true).

   ```python
   def __init__(self, id: UUID, name: str, balance: Decimal):
       super().__init__(id=id)
       if balance < Decimal("0"):
           raise ValueError("Balance cannot be negative")
       self.name = name
       self.balance = balance
   ```

3. **Use Value Objects**: Represent concepts that are defined by their attributes as value objects.

   ```python
   @dataclass(frozen=True)
   class Money(ValueObject):
       amount: Decimal
       currency: str = "USD"
       
       def __post_init__(self):
           if self.amount < 0:
               raise ValueError("Amount cannot be negative")
   ```

4. **Aggregate Boundaries**: Define clear aggregate boundaries to ensure consistency.

5. **Domain Events**: Use domain events to capture and communicate significant state changes.

   ```python
   def withdraw(self, amount: Money) -> None:
       if amount.amount > self.balance:
           raise InsufficientFundsError(
               requested=amount.amount, available=self.balance
           )
       self.balance -= amount.amount
       self.register_event(
           FundsWithdrawnEvent(account_id=self.id, amount=amount)
       )
   ```

6. **Repository Abstractions**: Use repositories to abstract away data access details.

7. **Service Orchestration**: Use application services to orchestrate complex operations.

8. **Error Handling**: Use the Result type for predictable error handling.

## Related Sections

- [API Layer](/docs/api/overview.md) - Learn how to expose your domain through API endpoints
- [Database Layer](/docs/database/overview.md) - Understand how domain entities interact with the database
- [Schema Management](/docs/schema/schema_service.md) - Advanced schema management techniques