# Migrating from Django to Uno

This guide will help you migrate an existing Django application to the Uno framework.

## Overview

Migrating from Django to Uno involves several steps to transition from Django's model-view-template pattern to Uno's domain-driven architecture:

1. Setting up the Uno infrastructure
2. Converting Django models to domain entities
3. Replacing Django ORM with Uno repositories
4. Refactoring business logic into domain services
5. Converting Django views to Uno API endpoints
6. Migrating authentication and authorization

## Prerequisites

Before starting the migration:

- A working Django application
- PostgreSQL 16 database
- Python 3.13+
- Docker (recommended)

## Step 1: Project Setup

First, set up the Uno infrastructure alongside your existing Django project.

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
cp -r /path/to/uno/docker/docker-compose.yaml docker/
cp -r /path/to/uno/docker/scripts/* docker/scripts/
```

### Start the Development Environment

```bash
# Start PostgreSQL with extensions
./docker/scripts/start.sh
```

## Step 2: Project Structure

Create a new directory structure for your Uno components:

```
myproject/
├── django_app/        # Your existing Django app
├── uno_app/           # New Uno application
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/  # Domain entities
│   │   ├── services/  # Domain services
│   │   └── events/    # Domain events
│   ├── application/   # Application services
│   ├── infrastructure/ # Technical implementations
│   └── api/           # API endpoints
```

## Step 3: Configuration

Create a configuration class that implements the Uno ConfigProtocol:

```python
# uno_app/config.py
from pydantic_settings import BaseSettings
from uno.core.di import ConfigProtocol
from functools import lru_cache
import os
from django.conf import settings as django_settings

class Settings(BaseSettings, ConfigProtocol):
    # You can use your Django settings as a base
    database_url: str = f"postgresql+asyncpg://{django_settings.DATABASES['default']['USER']}:{django_settings.DATABASES['default']['PASSWORD']}@{django_settings.DATABASES['default']['HOST']}:{django_settings.DATABASES['default']['PORT']}/{django_settings.DATABASES['default']['NAME']}"
    debug: bool = django_settings.DEBUG
    
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

## Step 4: Convert Django Models to Domain Entities

In Django, you might have models like this:

```python
# Original Django model
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
```

Convert these to Uno domain entities:

```python
# uno_app/domain/entities/user.py
from uuid import UUID, uuid4
from datetime import datetime
from uno.domain.entity import EntityBase
from typing import Optional

class User(EntityBase[UUID]):
    """User domain entity."""
    
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    
    @classmethod
    def create(cls, username: str, email: str, **kwargs) -> "User":
        """Create a new user."""
        return cls(
            id=uuid4(),
            username=username,
            email=email,
            created_at=datetime.now(datetime.UTC),
            **kwargs
        )
        
    def get_full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
        
    def update_profile(self, **kwargs) -> None:
        """Update the user's profile."""
        changed = False
        for key, value in kwargs.items():
            if hasattr(self, key) and getattr(self, key) != value:
                setattr(self, key, value)
                changed = True
                
        if changed:
            # Record domain event
            from uno_app.domain.events import UserProfileUpdated
            self.record_event(UserProfileUpdated(
                user_id=self.id,
                changes=kwargs
            ))
```

### Create Database Model for ORM

```python
# uno_app/domain/models/user_model.py
from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uno.domain.base.model import BaseModel

class UserModel(BaseModel):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
```

### Create a Mapper Between Domain and ORM

```python
# uno_app/domain/mappers/user_mapper.py
from uuid import UUID
from uno_app.domain.entities.user import User
from uno_app.domain.models.user_model import UserModel
from uno.domain.entity import EntityMapper

def model_to_entity(model: UserModel) -> User:
    """Convert ORM model to domain entity."""
    return User(
        id=model.id,
        username=model.username,
        email=model.email,
        first_name=model.first_name,
        last_name=model.last_name,
        bio=model.bio,
        profile_picture_url=model.profile_picture_url,
        is_active=model.is_active,
        created_at=model.created_at
    )

def entity_to_model(entity: User) -> UserModel:
    """Convert domain entity to ORM model."""
    return UserModel(
        id=entity.id,
        username=entity.username,
        email=entity.email,
        first_name=entity.first_name,
        last_name=entity.last_name,
        bio=entity.bio,
        profile_picture_url=entity.profile_picture_url,
        is_active=entity.is_active,
        created_at=entity.created_at
    )

user_mapper = EntityMapper(
    entity_type=User,
    model_type=UserModel,
    to_entity=model_to_entity,
    to_model=entity_to_model
)
```

## Step 5: Implement Repositories

In Django, you might access data using the ORM:

```python
# Original Django data access
user = User.objects.get(username='johndoe')
users = User.objects.filter(is_active=True)
```

Convert this to a Uno repository:

```python
# uno_app/domain/repositories/user_repository.py
from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from uno.domain.entity import SQLAlchemyRepository
from uno_app.domain.entities.user import User
from uno_app.domain.models.user_model import UserModel
from uno_app.domain.mappers.user_mapper import user_mapper

class UserRepository(SQLAlchemyRepository[User, UUID, UserModel]):
    """Repository for User entity."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, user_mapper)
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username."""
        query = self._build_query().filter(UserModel.username == username)
        result = await self._execute_query(query)
        models = result.scalars().all()
        
        if not models:
            return None
            
        return self._mapper.to_entity(models[0])
        
    async def find_active_users(self) -> List[User]:
        """Find all active users."""
        query = self._build_query().filter(UserModel.is_active == True)
        result = await self._execute_query(query)
        models = result.scalars().all()
        
        return [self._mapper.to_entity(model) for model in models]
```

## Step 6: Implement Domain Services

In Django, business logic might be in models, managers, or views:

```python
# Original Django views or manager methods
def create_user(username, email, password):
    if User.objects.filter(username=username).exists():
        raise ValueError("Username already taken")
    
    user = User.objects.create_user(
        username=username, 
        email=email, 
        password=password
    )
    return user
```

Convert this to a Uno domain service:

```python
# uno_app/domain/services/user_service.py
from uuid import UUID
from uno.domain.entity import DomainService
from uno.core.errors.result import Result, Success, Failure
from uno_app.domain.entities.user import User
from uno_app.domain.repositories.user_repository import UserRepository

class UserService(DomainService[User, UUID]):
    """Service for user operations."""
    
    async def create_user(self, username: str, email: str, **kwargs) -> Result[User, str]:
        """Create a new user."""
        # Check if username is taken
        repository = self._ensure_repository()
        existing_user = await repository.find_by_username(username)
        
        if existing_user:
            return Failure(f"Username '{username}' is already taken")
        
        # Create and save user
        user = User.create(username, email, **kwargs)
        user = await repository.add(user)
        
        return Success(user)
```

## Step 7: Add Unit of Work for Transactions

In Django, you would manage transactions using:

```python
# Original Django transaction management
from django.db import transaction

with transaction.atomic():
    user = User.objects.create(username='john', email='john@example.com')
    profile = Profile.objects.create(user=user, bio='Developer')
```

With Uno, use the Unit of Work pattern:

```python
# uno_app/application/services/user_application_service.py
from uno.core.uow import UnitOfWork
from uno.domain.entity import DomainServiceWithUnitOfWork
from uno_app.domain.entities.user import User
from uno_app.domain.entities.profile import Profile
from uno_app.domain.repositories.user_repository import UserRepository
from uno_app.domain.repositories.profile_repository import ProfileRepository
from uuid import UUID

class UserApplicationService(DomainServiceWithUnitOfWork[User, UUID]):
    """Application service for user operations."""
    
    async def register_user(self, username: str, email: str, bio: str = None) -> Result[User, str]:
        """Register a new user with transaction support."""
        async with self.unit_of_work:
            # This code runs in a transaction
            user_repo = self.unit_of_work.get_repository(UserRepository)
            
            # Check if username is taken
            existing_user = await user_repo.find_by_username(username)
            if existing_user:
                return Failure(f"Username '{username}' is already taken")
            
            # Create user
            user = User.create(username, email, bio=bio)
            user = await user_repo.add(user)
            
            # Any additional entities would be created here
            # and would be part of the same transaction
            
            return Success(user)
```

## Step 8: Convert Django Views to Uno API Endpoints

In Django, you might have views like:

```python
# Original Django views
from django.views import View
from django.http import JsonResponse
import json

class UserView(View):
    def post(self, request):
        data = json.loads(request.body)
        try:
            user = create_user(
                data['username'], 
                data['email'], 
                data['password']
            )
            return JsonResponse({
                'id': user.id,
                'username': user.username,
                'email': user.email
            })
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
```

Convert this to a Uno endpoint:

```python
# uno_app/api/endpoints/user_endpoints.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from uno.api.endpoint import CrudEndpoint
from uno.api.endpoint.response import DataResponse
from uno_app.domain.services.user_service import UserService
from uno_app.domain.entities.user import User
from uno.core.di import get_dependency

# Create DTOs
class UserCreateDTO(BaseModel):
    username: str
    email: EmailStr
    first_name: str = None
    last_name: str = None
    bio: str = None

class UserResponseDTO(BaseModel):
    id: str
    username: str
    email: str
    first_name: str = None
    last_name: str = None
    bio: str = None
    profile_picture_url: str = None
    
    @classmethod
    def from_entity(cls, user: User) -> "UserResponseDTO":
        return cls(
            id=str(user.id),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            bio=user.bio,
            profile_picture_url=user.profile_picture_url
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

## Step 9: Migrate Authentication

If you're using Django's authentication system, you'll need to migrate to Uno's authentication:

```python
# uno_app/domain/services/auth_service.py
from uno.core.errors.result import Result, Success, Failure
from uno_app.domain.entities.user import User
from uno_app.domain.repositories.user_repository import UserRepository
import bcrypt
import jwt
from datetime import datetime, timedelta

class AuthService:
    """Service for authentication operations."""
    
    def __init__(
        self, 
        user_repository: UserRepository, 
        jwt_secret: str,
        token_expiry: int = 24  # hours
    ):
        self.user_repository = user_repository
        self.jwt_secret = jwt_secret
        self.token_expiry = token_expiry
    
    async def authenticate(self, username: str, password: str) -> Result[dict, str]:
        """Authenticate a user and return a JWT token."""
        user = await self.user_repository.find_by_username(username)
        
        if not user:
            return Failure("Invalid username or password")
        
        if not self._verify_password(user, password):
            return Failure("Invalid username or password")
        
        token = self._generate_token(user)
        
        return Success({
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username
            }
        })
    
    def _verify_password(self, user: User, password: str) -> bool:
        """Verify a password against the user's stored hash."""
        # In a real implementation, check against stored hash
        # This is a placeholder
        return True
    
    def _generate_token(self, user: User) -> str:
        """Generate a JWT token for the user."""
        expiry = datetime.now(datetime.UTC) + timedelta(hours=self.token_expiry)
        
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "exp": expiry.timestamp()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
```

### Create authentication endpoints:

```python
# uno_app/api/endpoints/auth_endpoints.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from uno.api.endpoint import BaseEndpoint
from uno.api.endpoint.response import DataResponse
from uno_app.domain.services.auth_service import AuthService
from uno.core.di import get_dependency

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Create endpoints
auth_endpoint = BaseEndpoint(
    router=router,
    tags=["Authentication"]
)

@auth_endpoint.router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_dependency(AuthService))
):
    """Login endpoint that returns a JWT token."""
    result = await auth_service.authenticate(
        form_data.username, 
        form_data.password
    )
    
    if not result.is_success:
        raise HTTPException(
            status_code=401,
            detail=result.error,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return result.value
```

## Step 10: Set Up Dependency Injection

Configure the dependency injection container:

```python
# uno_app/app.py
from uno.dependencies.modern_provider import configure_container
from uno_app.config import get_settings
from uno_app.domain.repositories.user_repository import UserRepository
from uno_app.domain.services.user_service import UserService
from uno_app.domain.services.auth_service import AuthService

def setup_dependencies():
    # Configure the DI container
    settings = get_settings()
    container = configure_container(settings)
    
    # Register repositories
    container.register_factory(
        UserRepository,
        lambda: UserRepository(get_db_session())
    )
    
    # Register services
    container.register_factory(
        UserService,
        lambda: UserService(get_dependency(UserRepository))
    )
    
    container.register_factory(
        AuthService,
        lambda: AuthService(
            get_dependency(UserRepository),
            settings.get("JWT_SECRET")
        )
    )
```

## Step 11: Integrate with FastAPI

Create a FastAPI application:

```python
# uno_app/app.py
from fastapi import FastAPI
from uno_app.api.endpoints.user_endpoints import user_endpoint
from uno_app.api.endpoints.auth_endpoints import auth_endpoint
from uno.api.endpoint.middleware import setup_error_handlers

def create_app():
    # Create FastAPI app
    app = FastAPI(title="My Migrated Django App")
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup dependencies
    setup_dependencies()
    
    # Register endpoints
    app.include_router(auth_endpoint.router, prefix="/api/auth")
    user_endpoint.register(app)
    
    return app

app = create_app()
```

## Step 12: Database Migrations

For the transition period, you might need to maintain both Django migrations and Uno migrations:

```bash
# Django migrations (for existing tables)
python manage.py makemigrations
python manage.py migrate

# Uno migrations (for new tables)
python -m uno.core.migrations.cli generate "create_new_tables"
python -m uno.core.migrations.cli apply
```

## Step 13: Connect FastAPI to Django (Optional Transition)

During migration, you might want to run both Django and FastAPI side by side:

```python
# main.py
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware
from starlette.middleware.wsgi import WSGIMiddleware
from starlette.middleware.cors import CORSMiddleware
from django.core.wsgi import get_wsgi_application
from uno_app.app import app as fastapi_app

# Create Django WSGI application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project.settings")
django_app = get_wsgi_application()

# Mount both applications
app = Starlette(
    routes=[
        Mount("/api", app=fastapi_app),
        Mount("/", app=WSGIMiddleware(django_app))
    ],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"])
    ]
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

## Moving Templates and Static Files

If your Django app uses templates and static files, you'll need to consider how to handle those:

1. **Option 1: Keep Django views for HTML rendering**
   - Use Django for server-rendered pages
   - Use Uno for API endpoints

2. **Option 2: Modern frontend framework**
   - Create a separate frontend with React, Vue, or Angular
   - Use Uno API endpoints for data

3. **Option 3: Server-side rendering with Jinja2**
   - FastAPI can use Jinja2 templates
   - Migrate Django templates to Jinja2

## Conclusion

By following these steps, you've successfully migrated from a Django application to a full-featured Uno application with:

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
- [Authentication](../security/authentication.md): More authentication options