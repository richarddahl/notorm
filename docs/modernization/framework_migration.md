# Migrating from Other Frameworks to uno Domain Entities

This guide provides detailed instructions for migrating applications from popular Python frameworks to uno's domain-driven design approach. Whether you're coming from Django, Flask, SQLAlchemy ORM, SQLModel, or other frameworks, this tutorial will help you transition smoothly.

## Table of Contents

1. [Migration Overview](#migration-overview)
2. [From Django to uno](#from-django-to-uno)
3. [From SQLAlchemy ORM to uno](#from-sqlalchemy-orm-to-uno)
4. [From SQLModel to uno](#from-sqlmodel-to-uno)
5. [From Flask to uno](#from-flask-to-uno)
6. [From FastAPI to uno](#from-fastapi-to-uno)
7. [Common Patterns and Solutions](#common-patterns-and-solutions)
8. [Migration Checklist](#migration-checklist)
9. [Troubleshooting](#troubleshooting)

## Migration Overview

### Core Philosophy Differences

Before diving into specific frameworks, it's important to understand the philosophical differences between traditional frameworks and uno's domain-driven design approach:

| Traditional Approach | uno Domain-Driven Design |
|----------------------|--------------------------|
| Database-centric models | Rich domain entities |
| Mixed data access and business logic | Separation of concerns |
| Framework-dependent code | Framework-agnostic domain model |
| CRUD operations | Behavior-focused design |
| Exception-based error handling | Result pattern for errors |
| Direct dependencies | Dependency injection |

### Key uno Concepts

These are the core concepts you'll be adopting:

1. **Domain Entities**: Rich business objects with behavior
2. **Value Objects**: Immutable objects with no identity
3. **Aggregates**: Clusters of entities with consistency boundaries
4. **Repositories**: Data access abstraction
5. **Domain Services**: Business logic coordination
6. **Application Services**: Orchestration across domain boundaries
7. **Result Pattern**: Explicit success/failure return values
8. **Dependency Injection**: Explicit dependencies vs. global access

## From Django to uno

Django's ORM and model system has significant differences from uno's domain-driven approach.

### Model Conversion

#### Django Model

```python
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def deactivate(self):
        self.is_active = False
        self.save()
    
    def reactivate(self):
        self.is_active = True
        self.save()
```

#### uno Domain Entity

```python
from dataclasses import dataclass, field
from datetime import datetime, UTC
from uno.domain.core import AggregateRoot, ValueObject
from typing import Optional

@dataclass(frozen=True)
class UserId(ValueObject):
    """Unique identifier for a user."""
    value: str

@dataclass
class User(AggregateRoot[UserId]):
    """Domain entity for user accounts."""
    
    id: UserId
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool = True
    date_joined: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False
    
    def reactivate(self) -> None:
        """Reactivate the user account."""
        self.is_active = True
```

### Django View to uno Endpoint

#### Django View

```python
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@require_http_methods(["GET"])
def get_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name(),
            'is_active': user.is_active
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def create_user(request):
    try:
        data = json.loads(request.body)
        user = User.objects.create(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        return JsonResponse({
            'id': user.id,
            'username': user.username,
            'email': user.email
        }, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
```

#### uno Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from uno.domain.api_integration import create_domain_router, domain_endpoint
from uno.dependencies.scoped_container import get_service
from .domain_services import UserService
from .entities import User, UserId

def create_users_router() -> APIRouter:
    router = create_domain_router(
        entity_type=User,
        service_type=UserService,
        prefix="/users",
        tags=["Users"]
    )
    
    # Custom endpoint example
    @router.get("/{user_id}")
    @domain_endpoint(entity_type=User, service_type=UserService)
    async def get_user(user_id: str, service: UserService = Depends(get_service(UserService))):
        """Get a user by ID."""
        result = await service.get_user(UserId(value=user_id))
        
        if result.is_failure:
            if "not found" in str(result.error):
                raise HTTPException(status_code=404, detail=str(result.error))
            raise HTTPException(status_code=500, detail=str(result.error))
            
        user = result.value
        return {
            'id': user.id.value,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name(),
            'is_active': user.is_active
        }
    
    return router
```

### From Django Manager to uno Repository

#### Django Manager

```python
from django.db import models

class UserManager(models.Manager):
    def active_users(self):
        return self.filter(is_active=True)
    
    def get_by_email(self, email):
        return self.get(email=email)
    
    def search_by_name(self, name):
        return self.filter(
            models.Q(first_name__icontains=name) | 
            models.Q(last_name__icontains=name)
        )

class User(models.Model):
    # ... fields
    objects = UserManager()
```

#### uno Repository

```python
from typing import List, Optional, Protocol, Runtime
from sqlalchemy.ext.asyncio import AsyncSession
from uno.core.result import Result, Success, Failure
from .entities import User, UserId

class UserRepositoryProtocol(Protocol):
    """Protocol defining the interface for UserRepository."""
    
    async def get_by_id(self, user_id: UserId) -> Result[Optional[User], str]: ...
    async def get_by_email(self, email: str) -> Result[Optional[User], str]: ...
    async def list_active_users(self) -> Result[List[User], str]: ...
    async def search_by_name(self, name: str) -> Result[List[User], str]: ...
    async def save(self, user: User) -> Result[User, str]: ...
    async def delete(self, user_id: UserId) -> Result[bool, str]: ...

class UserRepository:
    """Repository for User entity."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: UserId) -> Result[Optional[User], str]:
        try:
            query = """
            SELECT id, username, email, first_name, last_name, is_active, date_joined
            FROM users WHERE id = :user_id
            """
            result = await self.session.execute(query, {"user_id": user_id.value})
            row = result.fetchone()
            if not row:
                return Success(None)
            
            return Success(User(
                id=UserId(value=row.id),
                username=row.username,
                email=row.email,
                first_name=row.first_name,
                last_name=row.last_name,
                is_active=row.is_active,
                date_joined=row.date_joined
            ))
        except Exception as e:
            return Failure(f"Error fetching user: {str(e)}")
    
    # Other methods similarly implemented
```

### Django Form to uno Service Validation

#### Django Form

```python
from django import forms
from django.core.exceptions import ValidationError

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        
    def clean_username(self):
        username = self.cleaned_data['username']
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already in use")
        return email
```

#### uno Service Validation

```python
from typing import Dict, Any
from uno.core.result import Result, Success, Failure
from uno.dependencies.decorators import singleton, inject_params
from .entities import User, UserId
from .domain_repositories import UserRepository

@singleton
class UserService:
    """Service for managing user entities."""
    
    def __init__(self, repository: UserRepository):
        self.repository = repository
    
    async def create_user(self, data: Dict[str, Any]) -> Result[User, str]:
        """Create a new user with validation."""
        try:
            # Validate username
            username = data.get('username', '')
            if len(username) < 3:
                return Failure("Username must be at least 3 characters")
            
            # Validate email
            email = data.get('email', '')
            email_result = await self.repository.get_by_email(email)
            if email_result.is_failure:
                return Failure(f"Error checking email: {email_result.error}")
            if email_result.value is not None:
                return Failure("Email already in use")
            
            # Create user
            user = User(
                id=UserId(value=str(uuid.uuid4())),
                username=username,
                email=email,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', '')
            )
            
            # Save user
            save_result = await self.repository.save(user)
            if save_result.is_failure:
                return Failure(f"Error saving user: {save_result.error}")
                
            return Success(save_result.value)
        except Exception as e:
            return Failure(f"Error creating user: {str(e)}")
```

## From SQLAlchemy ORM to uno

SQLAlchemy is closer to uno's architecture but still differs in several key ways.

### SQLAlchemy Model to uno Entity

#### SQLAlchemy Model

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    def is_in_stock(self):
        return self.stock > 0
    
    def decrease_stock(self, quantity):
        if quantity > self.stock:
            raise ValueError("Not enough items in stock")
        self.stock -= quantity
        
    def increase_stock(self, quantity):
        self.stock += quantity
```

#### uno Domain Entity

```python
from dataclasses import dataclass, field
from datetime import datetime, UTC
from decimal import Decimal
from uno.domain.core import AggregateRoot, ValueObject
from typing import Optional

@dataclass(frozen=True)
class ProductId(ValueObject):
    """Unique identifier for a product."""
    value: int

@dataclass(frozen=True)
class Money(ValueObject):
    """Value object representing monetary value."""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        # Round to 2 decimal places
        object.__setattr__(self, "amount", round(self.amount, 2))
    
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def subtract(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(amount=self.amount - other.amount, currency=self.currency)
    
    def multiply(self, factor: Decimal) -> "Money":
        return Money(amount=self.amount * factor, currency=self.currency)

@dataclass
class Product(AggregateRoot[ProductId]):
    """Domain entity for products."""
    
    id: ProductId
    name: str
    price: Money
    stock: int = 0
    description: Optional[str] = None
    is_available: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def is_in_stock(self) -> bool:
        """Check if the product is in stock."""
        return self.stock > 0
    
    def decrease_stock(self, quantity: int) -> None:
        """Decrease the product stock."""
        if quantity > self.stock:
            raise ValueError("Not enough items in stock")
        self.stock -= quantity
        
    def increase_stock(self, quantity: int) -> None:
        """Increase the product stock."""
        self.stock += quantity
        
    def change_price(self, new_price: Money) -> None:
        """Change the product price."""
        self.price = new_price
```

### SQLAlchemy Session to uno Repository

#### SQLAlchemy Usage

```python
from sqlalchemy.orm import Session
from sqlalchemy import select

def get_product(session: Session, product_id: int):
    return session.query(Product).filter(Product.id == product_id).first()

def get_available_products(session: Session):
    return session.query(Product).filter(Product.is_available == True).all()

def save_product(session: Session, product: Product):
    if product.id is None:
        session.add(product)
    session.commit()
    return product

def delete_product(session: Session, product_id: int):
    product = get_product(session, product_id)
    if product:
        session.delete(product)
        session.commit()
        return True
    return False
```

#### uno Repository

```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uno.core.result import Result, Success, Failure
from .entities import Product, ProductId, Money
from decimal import Decimal

class ProductRepository:
    """Repository for Product entity."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, product_id: ProductId) -> Result[Optional[Product], str]:
        try:
            query = """
            SELECT id, name, description, price, stock, is_available, created_at
            FROM products WHERE id = :product_id
            """
            result = await self.session.execute(query, {"product_id": product_id.value})
            row = result.fetchone()
            if not row:
                return Success(None)
            
            return Success(Product(
                id=ProductId(value=row.id),
                name=row.name,
                description=row.description,
                price=Money(amount=Decimal(row.price)),
                stock=row.stock,
                is_available=row.is_available,
                created_at=row.created_at
            ))
        except Exception as e:
            return Failure(f"Error fetching product: {str(e)}")
    
    async def list_available(self) -> Result[List[Product], str]:
        try:
            query = """
            SELECT id, name, description, price, stock, is_available, created_at
            FROM products WHERE is_available = TRUE
            """
            result = await self.session.execute(query)
            rows = result.fetchall()
            
            products = [
                Product(
                    id=ProductId(value=row.id),
                    name=row.name,
                    description=row.description,
                    price=Money(amount=Decimal(row.price)),
                    stock=row.stock,
                    is_available=row.is_available,
                    created_at=row.created_at
                )
                for row in rows
            ]
            
            return Success(products)
        except Exception as e:
            return Failure(f"Error fetching available products: {str(e)}")
    
    async def save(self, product: Product) -> Result[Product, str]:
        try:
            # Check if product exists
            query = "SELECT 1 FROM products WHERE id = :product_id"
            result = await self.session.execute(query, {"product_id": product.id.value})
            exists = result.scalar() is not None
            
            if exists:
                # Update existing product
                query = """
                UPDATE products
                SET name = :name, description = :description, price = :price,
                    stock = :stock, is_available = :is_available
                WHERE id = :product_id
                """
                await self.session.execute(query, {
                    "product_id": product.id.value,
                    "name": product.name,
                    "description": product.description,
                    "price": str(product.price.amount),
                    "stock": product.stock,
                    "is_available": product.is_available
                })
            else:
                # Insert new product
                query = """
                INSERT INTO products (id, name, description, price, stock, is_available, created_at)
                VALUES (:product_id, :name, :description, :price, :stock, :is_available, :created_at)
                """
                await self.session.execute(query, {
                    "product_id": product.id.value,
                    "name": product.name,
                    "description": product.description,
                    "price": str(product.price.amount),
                    "stock": product.stock,
                    "is_available": product.is_available,
                    "created_at": product.created_at
                })
            
            await self.session.commit()
            return Success(product)
        except Exception as e:
            await self.session.rollback()
            return Failure(f"Error saving product: {str(e)}")
```

## From SQLModel to uno

SQLModel combines SQLAlchemy and Pydantic, making it closer to uno's approach in some ways.

### SQLModel Model to uno Entity

#### SQLModel Model

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id")
    status: str = "pending"
    total_amount: float
    shipping_address: str
    order_date: datetime = Field(default_factory=datetime.now)
    
    def can_be_cancelled(self) -> bool:
        return self.status in ["pending", "processing"]
    
    def cancel(self) -> None:
        if not self.can_be_cancelled():
            raise ValueError(f"Cannot cancel order with status: {self.status}")
        self.status = "cancelled"
```

#### uno Domain Entity

```python
from dataclasses import dataclass, field
from datetime import datetime, UTC
from decimal import Decimal
from uno.domain.core import AggregateRoot, ValueObject
from typing import Optional, List

@dataclass(frozen=True)
class OrderId(ValueObject):
    """Unique identifier for an order."""
    value: int

@dataclass(frozen=True)
class CustomerId(ValueObject):
    """Unique identifier for a customer."""
    value: int

@dataclass(frozen=True)
class Address(ValueObject):
    """Value object representing a shipping address."""
    street: str
    city: str
    zip_code: str
    country: str
    
    def __str__(self) -> str:
        return f"{self.street}, {self.city}, {self.zip_code}, {self.country}"

@dataclass(frozen=True)
class Money(ValueObject):
    """Value object representing monetary value."""
    amount: Decimal
    currency: str = "USD"

class OrderStatus:
    """Value object representing order status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    
    @classmethod
    def is_valid(cls, status: str) -> bool:
        return status in [cls.PENDING, cls.PROCESSING, cls.SHIPPED, cls.DELIVERED, cls.CANCELLED]
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        transitions = {
            cls.PENDING: [cls.PROCESSING, cls.CANCELLED],
            cls.PROCESSING: [cls.SHIPPED, cls.CANCELLED],
            cls.SHIPPED: [cls.DELIVERED],
            cls.DELIVERED: [],
            cls.CANCELLED: []
        }
        return to_status in transitions.get(from_status, [])

@dataclass
class Order(AggregateRoot[OrderId]):
    """Domain entity for orders."""
    
    id: OrderId
    customer_id: CustomerId
    total_amount: Money
    shipping_address: Address
    status: str = OrderStatus.PENDING
    order_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def __post_init__(self):
        """Validate the order after initialization."""
        if not OrderStatus.is_valid(self.status):
            raise ValueError(f"Invalid order status: {self.status}")
    
    def can_be_cancelled(self) -> bool:
        """Check if the order can be cancelled."""
        return self.status in [OrderStatus.PENDING, OrderStatus.PROCESSING]
    
    def cancel(self) -> None:
        """Cancel the order."""
        if not self.can_be_cancelled():
            raise ValueError(f"Cannot cancel order with status: {self.status}")
        self.status = OrderStatus.CANCELLED
    
    def update_status(self, new_status: str) -> None:
        """Update the order status."""
        if not OrderStatus.is_valid(new_status):
            raise ValueError(f"Invalid order status: {new_status}")
        
        if not OrderStatus.can_transition(self.status, new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        self.status = new_status
```

## From Flask to uno

Flask applications can vary widely in structure, but here's a common pattern for migration.

### Flask Route to uno Endpoint

#### Flask Route

```python
from flask import Flask, request, jsonify
from werkzeug.exceptions import NotFound, BadRequest

app = Flask(__name__)

@app.route('/tasks', methods=['GET'])
def list_tasks():
    try:
        tasks = task_service.list_tasks()
        return jsonify([t.to_dict() for t in tasks])
    except Exception as e:
        app.logger.error(f"Error listing tasks: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    try:
        task = task_service.get_task(task_id)
        if task is None:
            raise NotFound(f"Task {task_id} not found")
        return jsonify(task.to_dict())
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        app.logger.error(f"Error getting task {task_id}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/tasks', methods=['POST'])
def create_task():
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No data provided")
        
        task = task_service.create_task(data)
        return jsonify(task.to_dict()), 201
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error creating task: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
```

#### uno FastAPI Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from uno.domain.api_integration import create_domain_router, domain_endpoint
from uno.dependencies.scoped_container import get_service
from .domain_services import TaskService
from .entities import Task, TaskId

def create_tasks_router() -> APIRouter:
    """Create router for task endpoints."""
    
    # Create base CRUD router
    router = create_domain_router(
        entity_type=Task,
        service_type=TaskService,
        prefix="/tasks",
        tags=["Tasks"]
    )
    
    # Add custom endpoints
    @router.get("/", response_model=List[Dict[str, Any]])
    @domain_endpoint(entity_type=Task, service_type=TaskService)
    async def list_tasks(service: TaskService = Depends(get_service(TaskService))):
        """List all tasks."""
        result = await service.list_tasks()
        
        if result.is_failure:
            raise HTTPException(status_code=500, detail=str(result.error))
            
        return [
            {
                "id": task.id.value,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "due_date": task.due_date.isoformat() if task.due_date else None
            }
            for task in result.value
        ]
    
    @router.get("/{task_id}", response_model=Dict[str, Any])
    @domain_endpoint(entity_type=Task, service_type=TaskService)
    async def get_task(
        task_id: int, 
        service: TaskService = Depends(get_service(TaskService))
    ):
        """Get a task by ID."""
        result = await service.get_task(TaskId(value=task_id))
        
        if result.is_failure:
            raise HTTPException(status_code=500, detail=str(result.error))
            
        task = result.value
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
        return {
            "id": task.id.value,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "due_date": task.due_date.isoformat() if task.due_date else None
        }
    
    @router.post("/", response_model=Dict[str, Any], status_code=201)
    @domain_endpoint(entity_type=Task, service_type=TaskService)
    async def create_task(
        data: Dict[str, Any] = Body(...),
        service: TaskService = Depends(get_service(TaskService))
    ):
        """Create a new task."""
        result = await service.create_task(data)
        
        if result.is_failure:
            if "validation" in str(result.error).lower():
                raise HTTPException(status_code=400, detail=str(result.error))
            raise HTTPException(status_code=500, detail=str(result.error))
            
        task = result.value
        return {
            "id": task.id.value,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "due_date": task.due_date.isoformat() if task.due_date else None
        }
    
    return router
```

### Flask Service to uno Service

#### Flask Service

```python
class TaskService:
    def __init__(self, db_session):
        self.db_session = db_session
    
    def list_tasks(self):
        return self.db_session.query(Task).all()
    
    def get_task(self, task_id):
        return self.db_session.query(Task).filter(Task.id == task_id).first()
    
    def create_task(self, data):
        task = Task(
            title=data['title'],
            description=data.get('description'),
            status=data.get('status', 'pending'),
            due_date=data.get('due_date')
        )
        self.db_session.add(task)
        self.db_session.commit()
        return task
    
    def update_task(self, task_id, data):
        task = self.get_task(task_id)
        if not task:
            return None
        
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        if 'due_date' in data:
            task.due_date = data['due_date']
        
        self.db_session.commit()
        return task
    
    def delete_task(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return False
        
        self.db_session.delete(task)
        self.db_session.commit()
        return True
```

#### uno Service

```python
from typing import Dict, Any, List, Optional
from uno.core.result import Result, Success, Failure
from uno.dependencies.decorators import singleton, inject_params
from datetime import datetime
from .entities import Task, TaskId
from .domain_repositories import TaskRepository

@singleton
class TaskService:
    """Service for managing task entities."""
    
    def __init__(self, repository: TaskRepository):
        self.repository = repository
    
    async def list_tasks(self) -> Result[List[Task], str]:
        """List all tasks."""
        try:
            return await self.repository.list_all()
        except Exception as e:
            return Failure(f"Error listing tasks: {str(e)}")
    
    async def get_task(self, task_id: TaskId) -> Result[Optional[Task], str]:
        """Get a task by ID."""
        try:
            return await self.repository.get_by_id(task_id)
        except Exception as e:
            return Failure(f"Error getting task: {str(e)}")
    
    async def create_task(self, data: Dict[str, Any]) -> Result[Task, str]:
        """Create a new task with validation."""
        try:
            # Validate required fields
            if 'title' not in data or not data['title']:
                return Failure("Title is required")
            
            # Parse due date if provided
            due_date = None
            if 'due_date' in data and data['due_date']:
                try:
                    due_date = datetime.fromisoformat(data['due_date'])
                except ValueError:
                    return Failure("Invalid due date format")
            
            # Create task
            task = Task(
                id=TaskId(value=None),  # Repository will generate ID
                title=data['title'],
                description=data.get('description'),
                status=data.get('status', 'pending'),
                due_date=due_date
            )
            
            # Save task
            return await self.repository.save(task)
        except Exception as e:
            return Failure(f"Error creating task: {str(e)}")
    
    async def update_task(self, task_id: TaskId, data: Dict[str, Any]) -> Result[Task, str]:
        """Update an existing task."""
        try:
            # Get existing task
            task_result = await self.repository.get_by_id(task_id)
            if task_result.is_failure:
                return task_result
            
            task = task_result.value
            if task is None:
                return Failure(f"Task with ID {task_id.value} not found")
            
            # Update fields
            if 'title' in data:
                task.title = data['title']
            if 'description' in data:
                task.description = data['description']
            if 'status' in data:
                task.status = data['status']
            if 'due_date' in data:
                if data['due_date'] is None:
                    task.due_date = None
                else:
                    try:
                        task.due_date = datetime.fromisoformat(data['due_date'])
                    except ValueError:
                        return Failure("Invalid due date format")
            
            # Save updated task
            return await self.repository.save(task)
        except Exception as e:
            return Failure(f"Error updating task: {str(e)}")
    
    async def delete_task(self, task_id: TaskId) -> Result[bool, str]:
        """Delete a task."""
        try:
            return await self.repository.delete(task_id)
        except Exception as e:
            return Failure(f"Error deleting task: {str(e)}")
```

## From FastAPI to uno

FastAPI is already very similar to uno's API architecture.

### FastAPI Endpoint to uno Domain Endpoint

#### FastAPI Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .database import get_db
from .models import Comment
from .schemas import CommentCreate, CommentUpdate, CommentResponse

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.get("/", response_model=List[CommentResponse])
def list_comments(
    post_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List comments, optionally filtered by post ID."""
    query = db.query(Comment)
    if post_id:
        query = query.filter(Comment.post_id == post_id)
    return query.all()

@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """Get a comment by ID."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment

@router.post("/", response_model=CommentResponse, status_code=201)
def create_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db)
):
    """Create a new comment."""
    db_comment = Comment(**comment.dict())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    db: Session = Depends(get_db)
):
    """Update a comment."""
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    for key, value in comment.dict(exclude_unset=True).items():
        setattr(db_comment, key, value)
    
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """Delete a comment."""
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    db.delete(db_comment)
    db.commit()
    return {"message": "Comment deleted successfully"}
```

#### uno Domain Endpoint

```python
from fastapi import Depends, HTTPException
from typing import List, Optional, Dict, Any
from uno.domain.api_integration import create_domain_router, domain_endpoint
from uno.dependencies.scoped_container import get_service
from .domain_services import CommentService
from .entities import Comment, CommentId, PostId

def create_comments_router():
    """Create router for comment endpoints."""
    
    # Create base CRUD router
    router = create_domain_router(
        entity_type=Comment,
        service_type=CommentService,
        prefix="/comments",
        tags=["Comments"]
    )
    
    # Add custom endpoints
    @router.get("/", response_model=List[Dict[str, Any]])
    @domain_endpoint(entity_type=Comment, service_type=CommentService)
    async def list_comments(
        post_id: Optional[int] = None,
        service: CommentService = Depends(get_service(CommentService))
    ):
        """List comments, optionally filtered by post ID."""
        if post_id:
            result = await service.get_by_post(PostId(value=post_id))
        else:
            result = await service.list_all()
        
        if result.is_failure:
            raise HTTPException(status_code=500, detail=str(result.error))
        
        return [
            {
                "id": comment.id.value,
                "post_id": comment.post_id.value,
                "content": comment.content,
                "author": comment.author,
                "created_at": comment.created_at.isoformat()
            }
            for comment in result.value
        ]
    
    return router
```

## Common Patterns and Solutions

### Model Relationships

#### Django Relationships

```python
class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    published_date = models.DateField()
```

#### uno Domain Relationships

```python
@dataclass(frozen=True)
class AuthorId(ValueObject):
    value: int

@dataclass(frozen=True)
class BookId(ValueObject):
    value: int

@dataclass
class Author(AggregateRoot[AuthorId]):
    id: AuthorId
    name: str
    email: str
    # In DDD, books are not stored within the Author entity

@dataclass
class Book(AggregateRoot[BookId]):
    id: BookId
    title: str
    author_id: AuthorId  # Reference to Author
    published_date: date
```

### Validation

#### Django Validation

```python
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def clean(self):
        if self.price <= 0:
            raise ValidationError("Price must be positive")
```

#### uno Validation

```python
@dataclass
class Product(AggregateRoot[ProductId]):
    id: ProductId
    name: str
    price: Money
    
    def __post_init__(self):
        """Validate after initialization."""
        if self.price.amount <= 0:
            raise ValueError("Price must be positive")
        if not self.name:
            raise ValueError("Name is required")
```

### Database Transactions

#### Django Transactions

```python
from django.db import transaction

def transfer_funds(from_account, to_account, amount):
    with transaction.atomic():
        from_account.balance -= amount
        from_account.save()
        
        to_account.balance += amount
        to_account.save()
```

#### uno Transactions

```python
from uno.domain.uow import UnitOfWork

class TransferService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    async def transfer_funds(self, from_id: AccountId, to_id: AccountId, amount: Money) -> Result[None, str]:
        try:
            async with self.uow:
                # Get accounts
                account_repo = self.uow.get_repository(AccountRepository)
                from_result = await account_repo.get_by_id(from_id)
                to_result = await account_repo.get_by_id(to_id)
                
                if from_result.is_failure:
                    return from_result
                if to_result.is_failure:
                    return to_result
                
                from_account = from_result.value
                to_account = to_result.value
                
                if from_account is None:
                    return Failure(f"Source account {from_id.value} not found")
                if to_account is None:
                    return Failure(f"Destination account {to_id.value} not found")
                
                # Perform transfer
                if not from_account.can_withdraw(amount):
                    return Failure("Insufficient funds")
                
                from_account.withdraw(amount)
                to_account.deposit(amount)
                
                # Save changes
                await account_repo.save(from_account)
                await account_repo.save(to_account)
                
                # Create transfer record
                transfer = Transfer(
                    id=TransferId(value=str(uuid.uuid4())),
                    from_account_id=from_id,
                    to_account_id=to_id,
                    amount=amount,
                    timestamp=datetime.now(UTC)
                )
                transfer_repo = self.uow.get_repository(TransferRepository)
                await transfer_repo.save(transfer)
                
                return Success(None)
        except Exception as e:
            return Failure(f"Error transferring funds: {str(e)}")
```

## Migration Checklist

Use this checklist to track your migration progress from other frameworks to uno:

- [ ] Identify domain entities and value objects
- [ ] Convert models to domain entities
- [ ] Implement domain repositories
- [ ] Create domain services
- [ ] Implement unit of work pattern
- [ ] Configure dependency injection
- [ ] Create domain endpoints
- [ ] Use Result pattern for error handling
- [ ] Add validation logic
- [ ] Implement CQRS where appropriate
- [ ] Set up event handling
- [ ] Create integration tests
- [ ] Implement background task processing
- [ ] Configure caching strategy
- [ ] Set up logging and monitoring

## Troubleshooting

### Circular Imports

If you encounter circular import issues when migrating:

```python
# Problem: Circular imports between files
# In order.py
from .customer import Customer  # Imports customer.py

# In customer.py
from .order import Order  # Imports order.py - circular!

# Solution: Use forward references and postponed annotations
from __future__ import annotations
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .order import Order  # Only used for type checking

class Customer:
    orders: List["Order"]  # Use string literal
```

### Legacy Integration Issues

If you need to gradually migrate while maintaining compatibility:

```python
# Adapter pattern to bridge between uno domain and legacy code
class LegacyOrderAdapter:
    """Adapter to bridge legacy Order model and domain Order entity."""
    
    @staticmethod
    def to_domain(legacy_order) -> Order:
        """Convert legacy order to domain entity."""
        return Order(
            id=OrderId(value=legacy_order.id),
            customer_id=CustomerId(value=legacy_order.customer_id),
            total_amount=Money(amount=Decimal(str(legacy_order.total_amount))),
            shipping_address=Address(
                street=legacy_order.address_street,
                city=legacy_order.address_city,
                zip_code=legacy_order.address_zip,
                country=legacy_order.address_country
            ),
            status=legacy_order.status,
            order_date=legacy_order.order_date
        )
    
    @staticmethod
    def to_legacy(domain_order, legacy_model=None):
        """Convert domain entity to legacy order."""
        if legacy_model is None:
            # Create new legacy model instance
            from .legacy_models import LegacyOrder
            legacy_model = LegacyOrder()
        
        # Update legacy model fields
        legacy_model.id = domain_order.id.value
        legacy_model.customer_id = domain_order.customer_id.value
        legacy_model.total_amount = float(domain_order.total_amount.amount)
        legacy_model.status = domain_order.status
        legacy_model.order_date = domain_order.order_date
        
        # Address
        legacy_model.address_street = domain_order.shipping_address.street
        legacy_model.address_city = domain_order.shipping_address.city
        legacy_model.address_zip = domain_order.shipping_address.zip_code
        legacy_model.address_country = domain_order.shipping_address.country
        
        return legacy_model
```

### Database Schema Evolution

Migrating database schemas alongside domain model changes:

```python
# Example database migration for uno entities

# Create migration file
"""
-- Create value tables for immutable value objects
CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    country TEXT NOT NULL,
    -- Hash for quick lookups of identical addresses
    address_hash VARCHAR(64) NOT NULL,
    UNIQUE(address_hash)
);

-- Create entity tables
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    shipping_address_id INTEGER NOT NULL REFERENCES addresses(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))
);

-- Create indexes
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
"""

# Use uno migrations to apply changes
from uno.migrations import Migration

class OrderMigration(Migration):
    """Migration to create order-related tables."""
    
    version = "20231015000001"
    
    async def up(self, connection):
        """Apply the migration."""
        await connection.execute("""
            -- Migration SQL here
        """)
    
    async def down(self, connection):
        """Revert the migration."""
        await connection.execute("""
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS addresses;
        """)
```

## Conclusion

Migrating from traditional frameworks to uno's domain-driven design approach requires a shift in thinking, but the benefits are substantial:

1. **Clear Domain Modeling**: Entities that represent your business domain more accurately
2. **Improved Testability**: Pure domain logic that's easy to unit test
3. **Better Error Handling**: Explicit Result pattern instead of exceptions
4. **Enhanced Maintainability**: Clear separation of concerns 
5. **Framework Independence**: Core business logic free from framework details

Remember that migration can be gradual. Start with a small bounded context, apply the DDD patterns there, and expand outward as you become more comfortable with the approach.

For a holistic migration strategy, consider focusing first on your most critical business domains or on new features where the benefits of DDD will be most immediately apparent.

Happy coding!