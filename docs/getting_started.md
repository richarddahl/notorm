# Getting Started with Uno

This guide will help you set up a new project with Uno and understand its basic concepts.

## Prerequisites

- Python 3.13+
- PostgreSQL 16
- Docker (recommended for development)

## Installation

### 1. Create a new Python project

```bash
mkdir myapp
cd myapp
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Uno

```bash
pip install uno-framework
```

### 3. Set up a development environment with Docker

Uno includes scripts to set up a complete development environment using Docker:

```bash
# Clone the repository to get the scripts
git clone https://github.com/username/uno.git uno-scripts
cp -r uno-scripts/scripts .
cp uno-scripts/docker/* docker/

# Start the development environment
./scripts/docker/start.sh
```

This will:
- Start PostgreSQL with all required extensions (including Apache AGE)
- Configure the database with proper roles and schemas
- Set up a development user

## Project Structure

A typical Uno project follows this structure:

```
myapp/
├── docker/               # Docker configuration
├── migrations/           # Database migrations
├── src/
│   ├── myapp/
│   │   ├── __init__.py
│   │   ├── domain/       # Domain model
│   │   │   ├── __init__.py
│   │   │   ├── entities/ # Domain entities
│   │   │   ├── services/ # Domain services
│   │   │   └── events/   # Domain events
│   │   ├── application/  # Application services
│   │   ├── infrastructure/ # Technical implementations
│   │   └── api/          # API endpoints
│   └── config.py         # Configuration
├── tests/
│   ├── unit/
│   └── integration/
├── pyproject.toml
└── README.md
```

## Configuration

Uno uses Pydantic settings for configuration. Create a `.env` file in your project root:

```
# .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/myapp
JWT_SECRET=your-secret-key
DEBUG=true
```

Then create a config.py file:

```python
from pydantic_settings import BaseSettings
from uno.core.di import ConfigProtocol
from functools import lru_cache

class Settings(BaseSettings, ConfigProtocol):
    database_url: str
    jwt_secret: str
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def get(self, key, default=None):
        """Implement ConfigProtocol."""
        return getattr(self, key, default)
    
    def all(self):
        """Implement ConfigProtocol."""
        return self.dict()

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

## Creating Your First Domain Entity

Let's create a simple domain entity:

```python
# src/myapp/domain/entities/user.py
from uuid import UUID, uuid4
from datetime import datetime
from uno.domain.entity import EntityBase

class User(EntityBase[UUID]):
    """User domain entity."""
    
    name: str
    email: str
    created_at: datetime
    
    @classmethod
    def create(cls, name: str, email: str) -> "User":
        """Create a new user."""
        return cls(
            id=uuid4(),
            name=name,
            email=email,
            created_at=datetime.now(datetime.UTC)
        )
```

## Setting Up a Repository

Create a repository for the User entity:

```python
# src/myapp/domain/repositories/user_repository.py
from uuid import UUID
from typing import Optional, List
from uno.domain.entity import EntityRepository
from myapp.domain.entities.user import User

class UserRepository(EntityRepository[User, UUID]):
    """Repository for User entity."""
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        users = await self.find(lambda user: user.email == email)
        return users[0] if users else None
```

## Creating a Domain Service

```python
# src/myapp/domain/services/user_service.py
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

## Setting Up an API Endpoint

```python
# src/myapp/api/endpoints/user_endpoints.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from uno.api.endpoint import BaseEndpoint, CrudEndpoint
from uno.api.endpoint.response import DataResponse
from myapp.domain.services.user_service import UserService
from myapp.domain.entities.user import User
from uno.core.di import get_dependency

router = APIRouter()

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

# Create an endpoint
user_endpoint = CrudEndpoint(
    service=get_dependency(UserService),
    create_model=UserCreateDTO,
    response_model=UserResponseDTO,
    path="/users",
    tags=["Users"]
)

# Register with router
user_endpoint.register(router)
```

## Setting Up the Application

```python
# src/myapp/app.py
from fastapi import FastAPI
from myapp.api.endpoints.user_endpoints import router as user_router
from uno.api.endpoint.middleware import setup_error_handlers
from uno.dependencies.modern_provider import configure_container
from myapp.config import get_settings

def create_app() -> FastAPI:
    app = FastAPI(title="My Uno App")
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup dependency injection
    configure_container(get_settings())
    
    # Register routers
    app.include_router(user_router, prefix="/api")
    
    return app

app = create_app()
```

## Running the Application

Create a `main.py` file in your project root:

```python
import uvicorn
from myapp.app import app

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

Then run your application:

```bash
python main.py
```

Visit `http://localhost:8000/docs` to see your API documentation.

## Next Steps

Now that you have a basic Uno application, explore these topics:

- [Domain Entity Framework](domain/entity_framework.md): Learn more about domain entities
- [Repository Pattern](domain/repository_pattern.md): Advanced repository usage
- [Unit of Work](core/uow/index.md): Transaction management
- [Event System](core/events/index.md): Event-driven architecture
- [Endpoint Framework](api/endpoint/unified_endpoint_framework.md): Advanced API endpoints

For a complete example application, see the [Tutorial](tutorial/index.md).