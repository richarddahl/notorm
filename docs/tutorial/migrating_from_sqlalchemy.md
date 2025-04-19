# Migrating from SQLAlchemy to Uno

This guide will help you migrate an existing SQLAlchemy application to the Uno framework.

## Overview

Migrating from SQLAlchemy to Uno is a structured process that involves several steps:

1. Setting up the Uno infrastructure
2. Converting models to domain entities
3. Implementing repositories
4. Refactoring services to use domain-driven design
5. Setting up API endpoints

Uno builds on SQLAlchemy but adds a rich domain model, event-driven architecture, and clean separation of concerns.

## Prerequisites

Before starting the migration:

- A working SQLAlchemy application
- PostgreSQL 16 database
- Python 3.13+
- Docker (recommended)

## Step 1: Project Setup

First, set up the Uno infrastructure in your existing project.

### Install Uno Dependencies

```bash
pip install uno-framework
```

### Configure Docker for Development

Copy the Uno Docker configuration to your project:

```bash
# Create Docker directories
mkdir -p docker/scripts

# Copy Docker configuration from the Uno repository
# (Assuming you've cloned it or have access to the files)
cp -r /path/to/uno/docker/docker-compose.yaml docker/
cp -r /path/to/uno/docker/scripts/* docker/scripts/
```

### Start the Development Environment

```bash
# Start PostgreSQL with extensions
./docker/scripts/start.sh
```

## Step 2: Configuration

Create a configuration class that implements the Uno ConfigProtocol:

```python
# config.py
from pydantic_settings import BaseSettings
from uno.core.di import ConfigProtocol
from functools import lru_cache

class Settings(BaseSettings, ConfigProtocol):
    database_url: str  # Use your existing database URL
    # Add other configuration options
    
    class Config:
        env_file = ".env"
        
    def get(self, key, default=None):
        """Implement ConfigProtocol."""
        return getattr(self, key, default)
    
    def all(self):
        """Implement ConfigProtocol."""
        return self.dict()

@lru_cache()
def get_settings():
    return Settings()
```

## Step 3: Convert SQLAlchemy Models to Domain Entities

In SQLAlchemy, you might have models like this:

```python
# Original SQLAlchemy model
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    created_at = Column(DateTime)
```

Convert these to Uno domain entities:

```python
# Uno domain entity
from uuid import UUID, uuid4
from datetime import datetime
from uno.domain.entity import EntityBase

class User(EntityBase[UUID]):
    """User domain entity."""
    
    name: str
    email: str
    created_at: datetime = None
    
    @classmethod
    def create(cls, name: str, email: str) -> "User":
        """Create a new user."""
        return cls(
            id=uuid4(),
            name=name,
            email=email,
            created_at=datetime.now(datetime.UTC)
        )
        
    def update_email(self, email: str) -> None:
        """Update the user's email."""
        if email == self.email:
            return
            
        self.email = email
        # Record domain event
        from myapp.domain.events import UserEmailUpdated
        self.record_event(UserEmailUpdated(
            user_id=self.id,
            old_email=self.email,
            new_email=email
        ))
```

### Create Database Model for ORM

```python
# domain/models/user_model.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uno.domain.base.model import BaseModel

class UserModel(BaseModel):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
```

### Create a Mapper Between Domain and ORM

```python
# domain/mappers/user_mapper.py
from uuid import UUID
from myapp.domain.entities.user import User
from myapp.domain.models.user_model import UserModel
from uno.domain.entity import EntityMapper

def model_to_entity(model: UserModel) -> User:
    """Convert ORM model to domain entity."""
    return User(
        id=model.id,
        name=model.name,
        email=model.email,
        created_at=model.created_at
    )

def entity_to_model(entity: User) -> UserModel:
    """Convert domain entity to ORM model."""
    return UserModel(
        id=entity.id,
        name=entity.name,
        email=entity.email,
        created_at=entity.created_at
    )

user_mapper = EntityMapper(
    entity_type=User,
    model_type=UserModel,
    to_entity=model_to_entity,
    to_model=entity_to_model
)
```

## Step 4: Implement Repositories

In SQLAlchemy, you might access data directly:

```python
# Original SQLAlchemy data access
from sqlalchemy.orm import Session

def get_user_by_email(session: Session, email: str):
    return session.query(User).filter(User.email == email).first()
```

Convert this to a Uno repository:

```python
# domain/repositories/user_repository.py
from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from uno.domain.entity import SQLAlchemyRepository
from myapp.domain.entities.user import User
from myapp.domain.models.user_model import UserModel
from myapp.domain.mappers.user_mapper import user_mapper

class UserRepository(SQLAlchemyRepository[User, UUID, UserModel]):
    """Repository for User entity."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, user_mapper)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        query = self._build_query().filter(UserModel.email == email)
        result = await self._execute_query(query)
        models = result.scalars().all()
        
        if not models:
            return None
            
        return self._mapper.to_entity(models[0])
```

## Step 5: Implement Domain Services

In SQLAlchemy, business logic might be mixed with data access:

```python
# Original SQLAlchemy service logic
def create_user(session: Session, name: str, email: str):
    existing = get_user_by_email(session, email)
    if existing:
        raise ValueError(f"User with email {email} already exists")
    
    user = User(name=name, email=email, created_at=datetime.utcnow())
    session.add(user)
    session.commit()
    return user
```

Convert this to a Uno domain service:

```python
# domain/services/user_service.py
from uuid import UUID
from uno.domain.entity import DomainService
from uno.core.errors.result import Result, Success, Failure
from myapp.domain.entities.user import User
from myapp.domain.repositories.user_repository import UserRepository

class UserService(DomainService[User, UUID]):
    """Service for user operations."""
    
    async def create_user(self, name: str, email: str) -> Result[User, str]:
        """Create a new user."""
        # Check if user already exists
        repository = self._ensure_repository()
        existing_user = await repository.find_by_email(email)
        
        if existing_user:
            return Failure(f"User with email {email} already exists")
        
        # Create and save user
        user = User.create(name, email)
        user = await repository.add(user)
        
        return Success(user)
```

## Step 6: Add Unit of Work for Transactions

In SQLAlchemy, you would manage transactions directly:

```python
# Original SQLAlchemy transaction management
with Session() as session:
    try:
        user = create_user(session, "John", "john@example.com")
        session.commit()
    except Exception as e:
        session.rollback()
        raise
```

With Uno, use the Unit of Work pattern:

```python
# Application service with Unit of Work
from uno.core.uow import UnitOfWork
from uno.domain.entity import DomainServiceWithUnitOfWork

class UserApplicationService(DomainServiceWithUnitOfWork[User, UUID]):
    """Application service for user operations."""
    
    async def register_user(self, name: str, email: str) -> Result[User, str]:
        """Register a new user with transaction support."""
        async with self.unit_of_work:
            # This code runs in a transaction
            user_repo = self.unit_of_work.get_repository(UserRepository)
            
            # Check if user exists
            existing_user = await user_repo.find_by_email(email)
            if existing_user:
                return Failure(f"User with email {email} already exists")
            
            # Create user
            user = User.create(name, email)
            user = await user_repo.add(user)
            
            # Create additional entities or perform other operations
            # All changes will be committed or rolled back together
            
            return Success(user)
```

## Step 7: Set Up API Endpoints

Convert your API endpoints to use Uno's unified endpoint framework:

```python
# api/endpoints/user_endpoints.py
from pydantic import BaseModel, EmailStr
from uno.api.endpoint import CrudEndpoint
from myapp.domain.services.user_service import UserService
from myapp.domain.entities.user import User

# Create DTOs
class UserCreateDTO(BaseModel):
    name: str
    email: EmailStr

class UserResponseDTO(BaseModel):
    id: str
    name: str
    email: str
    
    @classmethod
    def from_entity(cls, user: User) -> "UserResponseDTO":
        return cls(
            id=str(user.id),
            name=user.name,
            email=user.email
        )

# Create an endpoint with dependency injection
user_endpoint = CrudEndpoint(
    service=get_dependency(UserService),
    create_model=UserCreateDTO,
    response_model=UserResponseDTO,
    path="/users",
    tags=["Users"]
)
```

## Step 8: Configure Dependency Injection

Set up the dependency injection container:

```python
# app.py
from uno.dependencies.modern_provider import configure_container
from myapp.config import get_settings
from myapp.domain.repositories.user_repository import UserRepository
from myapp.domain.services.user_service import UserService

def setup_dependencies():
    # Configure the DI container
    settings = get_settings()
    container = configure_container(settings)
    
    # Register repositories and services
    container.register_factory(
        UserRepository,
        lambda: UserRepository(get_db_session())
    )
    
    container.register_factory(
        UserService,
        lambda: UserService(get_dependency(UserRepository))
    )
```

## Step 9: Set Up the Main Application

```python
# app.py
from fastapi import FastAPI
from myapp.api.endpoints.user_endpoints import user_endpoint
from uno.api.endpoint.middleware import setup_error_handlers

def create_app():
    # Create FastAPI app
    app = FastAPI(title="My Migrated App")
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup dependencies
    setup_dependencies()
    
    # Register endpoints
    user_endpoint.register(app)
    
    return app

app = create_app()
```

## Step 10: Database Migrations

Migrate your database schema using Uno's migration tools:

```bash
# Generate a migration
python -m uno.core.migrations.cli generate "convert_users_table"

# Apply the migration
python -m uno.core.migrations.cli apply
```

## Handling Query Complexity

For complex queries, use Uno's specification pattern:

```python
# domain/specifications/user_specifications.py
from uno.domain.entity.specification import Specification, AttributeSpecification
from myapp.domain.entities.user import User

class ActiveUserSpecification(Specification[User]):
    def is_satisfied_by(self, user: User) -> bool:
        return user.is_active
        
class EmailDomainSpecification(Specification[User]):
    def __init__(self, domain: str):
        self.domain = domain
        
    def is_satisfied_by(self, user: User) -> bool:
        return user.email.endswith(f"@{self.domain}")

# Usage
active_gmail_users = ActiveUserSpecification().and_(
    EmailDomainSpecification("gmail.com")
)
```

## Integrating with Event System

Add event handling to your application:

```python
# domain/events/user_events.py
from uno.core.events import Event
from uuid import UUID

class UserCreated(Event):
    user_id: UUID
    name: str
    email: str

# Event handler
async def handle_user_created(event: UserCreated):
    # Send welcome email, update analytics, etc.
    print(f"New user created: {event.name} <{event.email}>")

# Register handler with event bus
event_bus = get_dependency(EventBus)
event_bus.subscribe("user_created", handle_user_created)
```

## Conclusion

By following these steps, you've successfully migrated from a basic SQLAlchemy application to a full-featured Uno application with:

- Domain-driven design
- Clean architecture with separation of concerns
- Repository pattern for data access
- Unit of Work pattern for transactions
- Event-driven architecture
- Modern FastAPI endpoints

## Next Steps

- [Domain Entity Framework](../domain/entity_framework.md): Learn more about domain entities
- [Repository Pattern](../domain/repository_pattern.md): Advanced repository usage
- [Unit of Work](../core/uow/index.md): Transaction management
- [Event System](../core/events/index.md): Event-driven architecture