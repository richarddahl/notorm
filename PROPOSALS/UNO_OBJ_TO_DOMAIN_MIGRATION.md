# Migration Guide: From UnoObj to Domain Approach

## Overview

This guide helps you migrate existing uno applications from the UnoObj pattern to the recommended Domain Layer approach. The Domain Layer offers better separation of concerns, improved testability, and cleaner architecture for complex applications.

## Core Concept Mapping

| UnoObj Concept | Domain Layer Equivalent | Notes |
|----------------|-------------------------|-------|
| `UnoObj` | `AggregateEntity` | Domain entities with identity and lifecycle |
| `UnoObj.save()` | `Repository.save()` | Data persistence moved to repository |
| `UnoObj.get_by_id()` | `Repository.get_by_id()` | Data retrieval moved to repository |
| `UnoModel` | `SQLAlchemyModel` | Database model remains similar |
| `UnoSchema` | `ValueObject`, `EntityDTO` | Domain objects & DTOs for transfer |
| `UnoObj` methods | Entity methods + Service methods | Business logic split appropriately |

## Step-by-Step Migration Process

### 1. Identify Your Domain Objects

First, analyze your current UnoObj classes to identify your core domain concepts:

```python
# Before: UnoObj approach
class Product(UnoObj):
    id: str
    name: str
    price: Decimal
    category: str
    
    # Business logic mixed with data access
    @classmethod
    async def find_by_category(cls, category: str):
        return await cls.filter(cls.category == category)
    
    def apply_discount(self, percentage: int):
        self.price = self.price * (1 - percentage/100)
        # Direct persistence in domain method
        self.save()
```

Identify:
- Core entity attributes (id, name, price, category)
- Business methods (apply_discount)
- Data access methods (find_by_category)

### 2. Create Domain Entities

Create domain entities for your core concepts:

```python
# After: Domain approach - Entity
from uno.core.domain import AggregateEntity
from typing import Optional
from decimal import Decimal
from dataclasses import dataclass

# Value Object for immutable concepts
@dataclass(frozen=True)
class Money(ValueObject):
    amount: Decimal
    currency: str = "USD"
    
    def multiply(self, factor: float) -> "Money":
        return Money(
            amount=self.amount * Decimal(str(factor)),
            currency=self.currency
        )

# Domain event
class ProductPriceChangedEvent(BaseDomainEvent):
    product_id: str
    old_price: Money
    new_price: Money
    reason: str
    
    @property
    def aggregate_id(self) -> str:
        return self.product_id

# Aggregate Entity
class Product(AggregateEntity[str]):
    def __init__(self, id: str, name: str, price: Money, category: str):
        super().__init__(id=id)
        self.name = name
        self.price = price
        self.category = category
    
    # Business logic only - no data access
    def apply_discount(self, percentage: int) -> None:
        if percentage < 0 or percentage > 100:
            raise ValueError("Discount must be between 0 and 100")
            
        old_price = self.price
        factor = 1 - (percentage / 100)
        self.price = self.price.multiply(factor)
        
        # Register domain event
        self.register_event(ProductPriceChangedEvent(
            product_id=self.id,
            old_price=old_price,
            new_price=self.price,
            reason=f"Discount of {percentage}%"
        ))
```

### 3. Implement Repository Pattern

Create repositories to handle data access:

```python
# Database model (similar to UnoModel)
class ProductModel(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    price_amount = Column(Numeric(10, 2), nullable=False)
    price_currency = Column(String(3), default="USD")
    category = Column(String, nullable=False)

# Repository
class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[Product]:
        result = await self.session.execute(
            select(ProductModel).where(ProductModel.id == id)
        )
        product_model = result.scalar_one_or_none()
        if not product_model:
            return None
            
        # Convert from database model to domain entity
        return Product(
            id=product_model.id,
            name=product_model.name,
            price=Money(
                amount=product_model.price_amount,
                currency=product_model.price_currency
            ),
            category=product_model.category
        )
    
    async def find_by_category(self, category: str) -> List[Product]:
        result = await self.session.execute(
            select(ProductModel).where(ProductModel.category == category)
        )
        product_models = result.scalars().all()
        
        # Convert all results to domain entities
        return [
            Product(
                id=model.id,
                name=model.name,
                price=Money(
                    amount=model.price_amount,
                    currency=model.price_currency
                ),
                category=model.category
            )
            for model in product_models
        ]
    
    async def save(self, product: Product) -> None:
        # Convert domain entity to database model
        product_model = ProductModel(
            id=product.id,
            name=product.name,
            price_amount=product.price.amount,
            price_currency=product.price.currency,
            category=product.category
        )
        
        self.session.merge(product_model)
        await self.session.flush()
        
        # Process domain events (example implementation)
        for event in product.events:
            # Handle each event type appropriately
            if isinstance(event, ProductPriceChangedEvent):
                await self._log_price_change(event)
        
        # Clear events after processing
        product.clear_events()
    
    async def _log_price_change(self, event: ProductPriceChangedEvent) -> None:
        # Example of event handling in repository
        price_change_log = PriceChangeLogModel(
            product_id=event.product_id,
            old_price=str(event.old_price.amount),
            new_price=str(event.new_price.amount),
            reason=event.reason,
            timestamp=datetime.utcnow()
        )
        self.session.add(price_change_log)
```

### 4. Create Application Services

Implement services to orchestrate domain logic:

```python
# Result type for error handling
from uno.core.result import Result, Success, Failure
from uno.core.async_context import db_transaction

# Application service
class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    async def get_product(self, product_id: str) -> Result[Product]:
        product = await self.repository.get_by_id(product_id)
        if not product:
            return Failure(f"Product {product_id} not found")
        return Success(product)
    
    async def list_by_category(self, category: str) -> List[Product]:
        return await self.repository.find_by_category(category)
    
    @db_transaction
    async def create_product(
        self, name: str, price: Decimal, category: str
    ) -> Result[Product]:
        try:
            product = Product(
                id=generate_id(),
                name=name,
                price=Money(amount=price),
                category=category
            )
            
            await self.repository.save(product)
            return Success(product)
        except Exception as e:
            return Failure(f"Failed to create product: {str(e)}")
    
    @db_transaction
    async def apply_discount(
        self, product_id: str, percentage: int
    ) -> Result[Product]:
        # Get the product
        product_result = await self.get_product(product_id)
        if product_result.is_failure:
            return product_result
            
        product = product_result.value
        
        try:
            # Apply business logic
            product.apply_discount(percentage)
            
            # Persist changes
            await self.repository.save(product)
            return Success(product)
        except ValueError as e:
            return Failure(str(e))
        except Exception as e:
            return Failure(f"Failed to apply discount: {str(e)}")
```

### 5. Update API Layer

Expose your domain through API endpoints:

```python
from fastapi import APIRouter, Depends, HTTPException
from uno.dependencies.database import get_db_session
from uno.dependencies.decorators import inject_params
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/products", tags=["Products"])

# Data transfer objects
class ProductDTO(BaseModel):
    id: str
    name: str
    price: float
    currency: str = "USD"
    category: str
    
    @classmethod
    def from_entity(cls, product: Product) -> "ProductDTO":
        return cls(
            id=product.id,
            name=product.name,
            price=float(product.price.amount),
            currency=product.price.currency,
            category=product.category
        )

class CreateProductRequest(BaseModel):
    name: str
    price: float
    category: str

class DiscountRequest(BaseModel):
    percentage: int

# Endpoints
@router.get("/{product_id}", response_model=ProductDTO)
async def get_product(
    product_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    repository = ProductRepository(session)
    service = ProductService(repository)
    
    result = await service.get_product(product_id)
    if result.is_failure:
        raise HTTPException(status_code=404, detail=str(result.error))
        
    return ProductDTO.from_entity(result.value)

@router.get("/category/{category}", response_model=List[ProductDTO])
async def list_products_by_category(
    category: str,
    session: AsyncSession = Depends(get_db_session)
):
    repository = ProductRepository(session)
    service = ProductService(repository)
    
    products = await service.list_by_category(category)
    return [ProductDTO.from_entity(product) for product in products]

@router.post("/", response_model=ProductDTO, status_code=201)
async def create_product(
    request: CreateProductRequest,
    session: AsyncSession = Depends(get_db_session)
):
    repository = ProductRepository(session)
    service = ProductService(repository)
    
    result = await service.create_product(
        name=request.name,
        price=Decimal(str(request.price)),
        category=request.category
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
        
    return ProductDTO.from_entity(result.value)

@router.post("/{product_id}/discount", response_model=ProductDTO)
async def apply_discount(
    product_id: str,
    request: DiscountRequest,
    session: AsyncSession = Depends(get_db_session)
):
    repository = ProductRepository(session)
    service = ProductService(repository)
    
    result = await service.apply_discount(
        product_id=product_id,
        percentage=request.percentage
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
        
    return ProductDTO.from_entity(result.value)
```

### 6. Implement Testing

Write comprehensive tests for your domain components:

```python
# Testing a domain entity
def test_product_apply_discount():
    # Arrange
    product = Product(
        id="prod-123",
        name="Test Product",
        price=Money(amount=Decimal("100.00")),
        category="test"
    )
    
    # Act
    product.apply_discount(20)
    
    # Assert
    assert product.price.amount == Decimal("80.00")
    assert len(product.events) == 1
    assert isinstance(product.events[0], ProductPriceChangedEvent)
    assert product.events[0].old_price.amount == Decimal("100.00")
    assert product.events[0].new_price.amount == Decimal("80.00")

# Testing with mocks
@pytest.mark.asyncio
async def test_product_service_apply_discount():
    # Arrange
    product = Product(
        id="prod-123",
        name="Test Product",
        price=Money(amount=Decimal("100.00")),
        category="test"
    )
    
    # Mock repository
    repository = MagicMock(spec=ProductRepository)
    repository.get_by_id.return_value = product
    
    # Create service with mock
    service = ProductService(repository)
    
    # Act
    result = await service.apply_discount("prod-123", 20)
    
    # Assert
    assert result.is_success
    assert result.value.price.amount == Decimal("80.00")
    repository.save.assert_called_once()
```

## Common Patterns and Conversions

### Factory Methods

**Before (UnoObj):**
```python
@classmethod
async def create_with_defaults(cls, name: str) -> "Product":
    return await cls.create(
        name=name,
        price=Decimal("9.99"),
        category="default"
    )
```

**After (Domain):**
```python
# In entity
@classmethod
def create_with_defaults(cls, name: str) -> "Product":
    return cls(
        id=generate_id(),
        name=name,
        price=Money(amount=Decimal("9.99")),
        category="default"
    )

# In service
async def create_default_product(self, name: str) -> Result[Product]:
    product = Product.create_with_defaults(name)
    await self.repository.save(product)
    return Success(product)
```

### Filtering and Queries

**Before (UnoObj):**
```python
@classmethod
async def find_expensive(cls, threshold: Decimal = Decimal("100.00")):
    return await cls.filter(cls.price > threshold)
```

**After (Domain):**
```python
# In repository
async def find_expensive(self, threshold: Decimal = Decimal("100.00")) -> List[Product]:
    result = await self.session.execute(
        select(ProductModel).where(ProductModel.price_amount > threshold)
    )
    models = result.scalars().all()
    
    return [self._to_entity(model) for model in models]

# In service
async def get_expensive_products(
    self, threshold: Decimal = Decimal("100.00")
) -> List[Product]:
    return await self.repository.find_expensive(threshold)
```

### Validation

**Before (UnoObj):**
```python
def validate(self):
    if not self.name:
        raise ValidationError("Name is required")
    if self.price <= 0:
        raise ValidationError("Price must be positive")
```

**After (Domain):**
```python
# In entity constructor
def __init__(self, id: str, name: str, price: Money, category: str):
    super().__init__(id=id)
    
    # Validation
    if not name:
        raise ValueError("Name is required")
    if price.amount <= 0:
        raise ValueError("Price must be positive")
        
    self.name = name
    self.price = price
    self.category = category
```

### Relationships

**Before (UnoObj):**
```python
@classmethod
async def get_with_reviews(cls, product_id: str):
    product = await cls.get_by_id(product_id)
    product.reviews = await Review.filter(Review.product_id == product_id)
    return product
```

**After (Domain):**
```python
# In repository
async def get_with_reviews(self, product_id: str) -> Optional[ProductWithReviews]:
    # Use proper join or separate queries
    product_result = await self.session.execute(
        select(ProductModel).where(ProductModel.id == product_id)
    )
    product_model = product_result.scalar_one_or_none()
    if not product_model:
        return None
        
    reviews_result = await self.session.execute(
        select(ReviewModel).where(ReviewModel.product_id == product_id)
    )
    review_models = reviews_result.scalars().all()
    
    # Convert to domain objects
    product = self._to_entity(product_model)
    reviews = [
        Review(
            id=model.id,
            product_id=model.product_id,
            rating=model.rating,
            comment=model.comment
        )
        for model in review_models
    ]
    
    return ProductWithReviews(product=product, reviews=reviews)

# In service
async def get_product_with_reviews(self, product_id: str) -> Result[ProductWithReviews]:
    result = await self.repository.get_with_reviews(product_id)
    if not result:
        return Failure(f"Product {product_id} not found")
    return Success(result)
```

## Benefits of Migration

1. **Clean Separation of Concerns**
   - Domain logic isolated from data access
   - Clear boundaries between layers
   - Better organization of code

2. **Improved Testability**
   - Domain logic can be tested without database
   - Easier to mock repositories
   - More focused tests

3. **Better Domain Modeling**
   - Value objects for immutable concepts
   - Explicit aggregates for consistency boundaries
   - Events for side effects

4. **More Maintainable**
   - Each class has a single responsibility
   - Easier to understand and extend
   - Better organization for growing applications

5. **Enhanced Performance**
   - More control over database operations
   - Explicit control of transaction boundaries
   - Optimized queries when needed

## Migration Completion

**Status: COMPLETED**

As of April 16, 2025, the migration from UnoObj to the Domain pattern has been fully completed. All UnoObj-related code has been removed from the codebase, including:

- Core UnoObj implementation files
  - `src/uno/obj.py`
  - `src/uno/obj_errors.py`
  - `src/uno/registry.py`
  - `src/uno/registry_errors.py`
- UnoObj-specific error handling
- UnoRegistry system 
- Domain-specific UnoObj implementations (`objs.py` files in various modules)
- Legacy service implementations (`services.py` files in various modules)
- Legacy dependency provider implementations (`providers.py` files in various modules)
- Entity services framework (entire `src/uno/entity_services/` directory)
- All import and reference usages throughout the codebase
- UnoObj tests and example implementations
- Documentation focused on UnoObj pattern

All related systems have been updated to work with the Domain-Driven Design approach:

- Schema Manager now works directly with domain entities and DTOs
- Endpoint Factory creates endpoints for domain entities
- Filter system operates on domain entities
- Documentation now reflects the Domain-Driven Design approach

The codebase now exclusively uses the Domain-Driven Design approach with proper separation of concerns between:

- Domain entities with business logic
- Repositories for data access
- Application services for orchestration
- DTOs for API interface
- Explicit dependency injection for services and repositories

This migration represents a significant architectural improvement, providing better maintainability, testability, and scalability for the entire framework. The removal of UnoObj has simplified the architecture, reduced cognitive load, and enables faster onboarding of new developers to the project.

### Benefits Realized

The migration has already demonstrated several key benefits:

1. **Simplified Architecture**: Removing UnoObj eliminated a layer of indirection
2. **Better Domain Modeling**: Proper domain entities and aggregates provide more accurate modeling
3. **Improved Separation of Concerns**: Clear boundaries between domain, data access, and services
4. **Enhanced Testability**: Domain logic can be tested in isolation without data access
5. **Modern Patterns**: Alignment with industry-standard Domain-Driven Design practices

### Future Enhancements

Now that UnoObj has been removed, the following improvements are possible:

1. Further refinement of domain entity implementation
2. Enhanced event-driven architecture capabilities
3. More sophisticated aggregate root patterns
4. Additional repository implementations for different storage mechanisms
5. Improved read model projection capabilities

The technical debt from the UnoObj pattern has been fully addressed, allowing for more agile development moving forward.