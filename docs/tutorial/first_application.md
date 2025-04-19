# Building Your First Uno Application

This tutorial guides you through building a complete web application with the Uno framework. By the end, you'll have a working API with database integration, domain modeling, and a clean architecture.

## What We'll Build

We'll create a simple task management API with these features:

- User registration and authentication
- Task creation, updating, and deletion
- Task assignment to users
- Task filtering and search
- API documentation

## Prerequisites

- Python 3.13+
- PostgreSQL 16
- Docker (recommended for development)

## Step 1: Project Setup

First, create a new project directory and set up a virtual environment:

```bash
# Create project directory
mkdir task-manager
cd task-manager

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate.bat
```

Install the Uno framework:

```bash
pip install uno-framework
```

Set up the basic project structure:

```bash
# Create directory structure
mkdir -p src/taskmanager/{domain,application,infrastructure,api}/
mkdir -p src/taskmanager/domain/{entities,repositories,services}
mkdir -p src/taskmanager/application/{dtos,services}
mkdir -p src/taskmanager/infrastructure/{database,repositories}
mkdir -p src/taskmanager/api/endpoints
mkdir -p tests/{unit,integration}
```

## Step 2: Configure Docker and PostgreSQL

Create a Docker configuration for PostgreSQL:

```bash
mkdir -p docker
```

Create a `docker-compose.yaml` file:

```yaml
# docker/docker-compose.yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    container_name: uno-taskmanager-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: task_manager
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
```

Create an initialization script:

```sql
-- docker/init.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Create schema
CREATE SCHEMA IF NOT EXISTS task_manager;
```

Create a start script:

```bash
# docker/start.sh
#!/bin/bash
cd "$(dirname "$0")"
docker-compose up -d
```

Make it executable:

```bash
chmod +x docker/start.sh
```

## Step 3: Create Configuration

Create a configuration module:

```python
# src/taskmanager/config.py
from pydantic_settings import BaseSettings
from uno.core.di import ConfigProtocol
from functools import lru_cache
from typing import Any, Dict

class Settings(BaseSettings, ConfigProtocol):
    """Application settings."""
    
    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "task_manager"
    
    # API settings
    api_title: str = "Task Manager API"
    api_description: str = "API for managing tasks"
    api_version: str = "1.0.0"
    
    # Security settings
    jwt_secret: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 60 * 24  # minutes (1 day)
    
    # Feature flags
    enable_docs: bool = True
    enable_metrics: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def database_url(self) -> str:
        """Get the database URL."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return getattr(self, key, default)
    
    def all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.dict()

@lru_cache()
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
```

## Step 4: Define Domain Entities

Create the basic domain entities:

```python
# src/taskmanager/domain/entities/user.py
from datetime import datetime
from uno.domain.entity import EntityBase
from uuid import UUID, uuid4
from typing import Optional

class User(EntityBase[UUID]):
    """User entity."""
    
    username: str
    email: str
    password_hash: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    
    @classmethod
    def create(cls, username: str, email: str, password_hash: str, 
               first_name: Optional[str] = None, last_name: Optional[str] = None) -> "User":
        """Create a new user."""
        return cls(
            id=uuid4(),
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            created_at=datetime.now(datetime.UTC)
        )
    
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username
    
    def deactivate(self) -> None:
        """Deactivate this user."""
        if not self.is_active:
            return
            
        self.is_active = False
        self.record_event(UserDeactivated(user_id=self.id))
```

Create the task entity:

```python
# src/taskmanager/domain/entities/task.py
from datetime import datetime
from uno.domain.entity import AggregateRoot
from uuid import UUID, uuid4
from typing import Optional, List

class TaskPriority:
    """Task priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskStatus:
    """Task status enum."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class Task(AggregateRoot[UUID]):
    """Task entity."""
    
    title: str
    description: str = ""
    status: str = TaskStatus.TODO
    priority: str = TaskPriority.MEDIUM
    creator_id: UUID
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    tags: List[str] = []
    created_at: datetime = None
    updated_at: datetime = None
    
    @classmethod
    def create(cls, title: str, creator_id: UUID, description: str = "", 
               priority: str = TaskPriority.MEDIUM, due_date: Optional[datetime] = None, 
               tags: List[str] = None) -> "Task":
        """Create a new task."""
        now = datetime.now(datetime.UTC)
        task = cls(
            id=uuid4(),
            title=title,
            description=description,
            status=TaskStatus.TODO,
            priority=priority,
            creator_id=creator_id,
            due_date=due_date,
            tags=tags or [],
            created_at=now,
            updated_at=now
        )
        
        # Record domain event
        from taskmanager.domain.events import TaskCreated
        task.record_event(TaskCreated(
            task_id=task.id,
            creator_id=creator_id,
            title=title
        ))
        
        return task
    
    def assign(self, assignee_id: UUID) -> None:
        """Assign this task to a user."""
        if self.assignee_id == assignee_id:
            return
            
        previous_assignee = self.assignee_id
        self.assignee_id = assignee_id
        self.updated_at = datetime.now(datetime.UTC)
        
        # Record domain event
        from taskmanager.domain.events import TaskAssigned
        self.record_event(TaskAssigned(
            task_id=self.id,
            assignee_id=assignee_id,
            previous_assignee_id=previous_assignee
        ))
    
    def update_status(self, status: str) -> None:
        """Update the task status."""
        if self.status == status:
            return
            
        if status not in (TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.CANCELLED):
            raise ValueError(f"Invalid status: {status}")
            
        previous_status = self.status
        self.status = status
        self.updated_at = datetime.now(datetime.UTC)
        
        # Record domain event
        from taskmanager.domain.events import TaskStatusChanged
        self.record_event(TaskStatusChanged(
            task_id=self.id,
            new_status=status,
            previous_status=previous_status
        ))
    
    def update_details(self, title: Optional[str] = None, description: Optional[str] = None,
                       priority: Optional[str] = None, due_date: Optional[datetime] = None,
                       tags: Optional[List[str]] = None) -> None:
        """Update task details."""
        changed = False
        
        if title is not None and title != self.title:
            self.title = title
            changed = True
            
        if description is not None and description != self.description:
            self.description = description
            changed = True
            
        if priority is not None and priority != self.priority:
            if priority not in (TaskPriority.LOW, TaskPriority.MEDIUM, TaskPriority.HIGH):
                raise ValueError(f"Invalid priority: {priority}")
            self.priority = priority
            changed = True
            
        if due_date is not None and due_date != self.due_date:
            self.due_date = due_date
            changed = True
            
        if tags is not None and tags != self.tags:
            self.tags = tags
            changed = True
            
        if changed:
            self.updated_at = datetime.now(datetime.UTC)
            
            # Record domain event
            from taskmanager.domain.events import TaskUpdated
            self.record_event(TaskUpdated(
                task_id=self.id,
                title=self.title
            ))
```

## Step 5: Define Domain Events

Create a file for domain events:

```python
# src/taskmanager/domain/events.py
from uno.core.events import Event
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class UserCreated(Event):
    """Event raised when a user is created."""
    
    user_id: UUID
    username: str
    email: str

class UserDeactivated(Event):
    """Event raised when a user is deactivated."""
    
    user_id: UUID

class TaskCreated(Event):
    """Event raised when a task is created."""
    
    task_id: UUID
    creator_id: UUID
    title: str

class TaskAssigned(Event):
    """Event raised when a task is assigned."""
    
    task_id: UUID
    assignee_id: UUID
    previous_assignee_id: Optional[UUID] = None

class TaskStatusChanged(Event):
    """Event raised when a task status changes."""
    
    task_id: UUID
    new_status: str
    previous_status: str

class TaskUpdated(Event):
    """Event raised when a task is updated."""
    
    task_id: UUID
    title: str
```

## Step 6: Create Database Models

Create database models for your entities:

```python
# src/taskmanager/infrastructure/database/models.py
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserModel(Base):
    """Database model for users."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(100), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(datetime.UTC))
    
    # Relationships
    tasks_created = relationship("TaskModel", back_populates="creator", foreign_keys="TaskModel.creator_id")
    tasks_assigned = relationship("TaskModel", back_populates="assignee", foreign_keys="TaskModel.assignee_id")

class TaskModel(Base):
    """Database model for tasks."""
    
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(100), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="todo", nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(datetime.UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(datetime.UTC))
    
    # Relationships
    creator = relationship("UserModel", back_populates="tasks_created", foreign_keys=[creator_id])
    assignee = relationship("UserModel", back_populates="tasks_assigned", foreign_keys=[assignee_id])
```

## Step 7: Create Entity Mappers

Create mappers to convert between domain entities and database models:

```python
# src/taskmanager/infrastructure/database/mappers.py
from uno.domain.entity import EntityMapper
from taskmanager.domain.entities.user import User
from taskmanager.domain.entities.task import Task
from taskmanager.infrastructure.database.models import UserModel, TaskModel

def user_model_to_entity(model: UserModel) -> User:
    """Convert user model to entity."""
    return User(
        id=model.id,
        username=model.username,
        email=model.email,
        password_hash=model.password_hash,
        first_name=model.first_name,
        last_name=model.last_name,
        is_active=model.is_active,
        created_at=model.created_at
    )

def user_entity_to_model(entity: User) -> UserModel:
    """Convert user entity to model."""
    return UserModel(
        id=entity.id,
        username=entity.username,
        email=entity.email,
        password_hash=entity.password_hash,
        first_name=entity.first_name,
        last_name=entity.last_name,
        is_active=entity.is_active,
        created_at=entity.created_at
    )

def task_model_to_entity(model: TaskModel) -> Task:
    """Convert task model to entity."""
    return Task(
        id=model.id,
        title=model.title,
        description=model.description,
        status=model.status,
        priority=model.priority,
        creator_id=model.creator_id,
        assignee_id=model.assignee_id,
        due_date=model.due_date,
        tags=model.tags or [],
        created_at=model.created_at,
        updated_at=model.updated_at
    )

def task_entity_to_model(entity: Task) -> TaskModel:
    """Convert task entity to model."""
    return TaskModel(
        id=entity.id,
        title=entity.title,
        description=entity.description,
        status=entity.status,
        priority=entity.priority,
        creator_id=entity.creator_id,
        assignee_id=entity.assignee_id,
        due_date=entity.due_date,
        tags=entity.tags,
        created_at=entity.created_at,
        updated_at=entity.updated_at
    )

# Create mappers
user_mapper = EntityMapper(
    entity_type=User,
    model_type=UserModel,
    to_entity=user_model_to_entity,
    to_model=user_entity_to_model
)

task_mapper = EntityMapper(
    entity_type=Task,
    model_type=TaskModel,
    to_entity=task_model_to_entity,
    to_model=task_entity_to_model
)
```

## Step 8: Create Repositories

Create repositories for your entities:

```python
# src/taskmanager/infrastructure/repositories/user_repository.py
from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uno.domain.entity import SQLAlchemyRepository
from taskmanager.domain.entities.user import User
from taskmanager.infrastructure.database.models import UserModel
from taskmanager.infrastructure.database.mappers import user_mapper

class UserRepository(SQLAlchemyRepository[User, UUID, UserModel]):
    """Repository for User entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, user_mapper)
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username."""
        query = select(UserModel).where(UserModel.username == username)
        result = await self._execute_query(query)
        model = result.scalars().first()
        
        if not model:
            return None
        
        return self._mapper.to_entity(model)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        query = select(UserModel).where(UserModel.email == email)
        result = await self._execute_query(query)
        model = result.scalars().first()
        
        if not model:
            return None
        
        return self._mapper.to_entity(model)
    
    async def find_active_users(self) -> List[User]:
        """Find all active users."""
        query = select(UserModel).where(UserModel.is_active == True)
        result = await self._execute_query(query)
        models = result.scalars().all()
        
        return [self._mapper.to_entity(model) for model in models]
```

Create the task repository:

```python
# src/taskmanager/infrastructure/repositories/task_repository.py
from uuid import UUID
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from uno.domain.entity import SQLAlchemyRepository
from taskmanager.domain.entities.task import Task
from taskmanager.infrastructure.database.models import TaskModel
from taskmanager.infrastructure.database.mappers import task_mapper

class TaskRepository(SQLAlchemyRepository[Task, UUID, TaskModel]):
    """Repository for Task entities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, task_mapper)
    
    async def find_by_creator(self, creator_id: UUID) -> List[Task]:
        """Find all tasks created by a user."""
        query = select(TaskModel).where(TaskModel.creator_id == creator_id)
        result = await self._execute_query(query)
        models = result.scalars().all()
        
        return [self._mapper.to_entity(model) for model in models]
    
    async def find_by_assignee(self, assignee_id: UUID) -> List[Task]:
        """Find all tasks assigned to a user."""
        query = select(TaskModel).where(TaskModel.assignee_id == assignee_id)
        result = await self._execute_query(query)
        models = result.scalars().all()
        
        return [self._mapper.to_entity(model) for model in models]
    
    async def find_by_status(self, status: str) -> List[Task]:
        """Find all tasks with a specific status."""
        query = select(TaskModel).where(TaskModel.status == status)
        result = await self._execute_query(query)
        models = result.scalars().all()
        
        return [self._mapper.to_entity(model) for model in models]
    
    async def find_by_filter(self, filters: Dict[str, Any]) -> List[Task]:
        """Find tasks matching filter criteria."""
        conditions = []
        
        if filters.get("status"):
            conditions.append(TaskModel.status == filters["status"])
        
        if filters.get("priority"):
            conditions.append(TaskModel.priority == filters["priority"])
        
        if filters.get("creator_id"):
            conditions.append(TaskModel.creator_id == filters["creator_id"])
        
        if filters.get("assignee_id"):
            conditions.append(TaskModel.assignee_id == filters["assignee_id"])
        
        if filters.get("due_before"):
            conditions.append(TaskModel.due_date <= filters["due_before"])
        
        if filters.get("due_after"):
            conditions.append(TaskModel.due_date >= filters["due_after"])
        
        if filters.get("tags"):
            for tag in filters["tags"]:
                conditions.append(TaskModel.tags.contains([tag]))
        
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            conditions.append(
                or_(
                    TaskModel.title.ilike(search_term),
                    TaskModel.description.ilike(search_term)
                )
            )
        
        if conditions:
            query = select(TaskModel).where(and_(*conditions))
        else:
            query = select(TaskModel)
        
        # Add ordering
        if filters.get("order_by"):
            field = getattr(TaskModel, filters["order_by"])
            if filters.get("order_dir") == "desc":
                query = query.order_by(field.desc())
            else:
                query = query.order_by(field.asc())
        else:
            # Default ordering
            query = query.order_by(TaskModel.updated_at.desc())
        
        # Add limit and offset for pagination
        if filters.get("limit"):
            query = query.limit(filters["limit"])
        
        if filters.get("offset"):
            query = query.offset(filters["offset"])
        
        result = await self._execute_query(query)
        models = result.scalars().all()
        
        return [self._mapper.to_entity(model) for model in models]
```

## Step 9: Create Domain Services

Create a password utility:

```python
# src/taskmanager/infrastructure/security/password.py
import bcrypt
from typing import Tuple

def hash_password(password: str) -> str:
    """Hash a password."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)
```

Create a user service:

```python
# src/taskmanager/domain/services/user_service.py
from uuid import UUID
from typing import Optional
from uno.domain.entity import DomainService
from uno.core.errors.result import Result, Success, Failure
from taskmanager.domain.entities.user import User
from taskmanager.infrastructure.repositories.user_repository import UserRepository
from taskmanager.infrastructure.security.password import hash_password, verify_password

class UserService(DomainService[User, UUID]):
    """Service for user operations."""
    
    def __init__(self, repository: UserRepository):
        super().__init__(repository)
    
    async def create_user(self, username: str, email: str, password: str, 
                          first_name: Optional[str] = None, last_name: Optional[str] = None) -> Result[User, str]:
        """Create a new user."""
        # Check if username exists
        existing_user = await self._repository.find_by_username(username)
        if existing_user:
            return Failure(f"Username '{username}' is already taken")
        
        # Check if email exists
        existing_email = await self._repository.find_by_email(email)
        if existing_email:
            return Failure(f"Email '{email}' is already registered")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = User.create(
            username=username,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name
        )
        
        # Save user
        created_user = await self._repository.add(user)
        
        return Success(created_user)
    
    async def authenticate(self, username: str, password: str) -> Result[User, str]:
        """Authenticate a user with username and password."""
        # Find user
        user = await self._repository.find_by_username(username)
        if not user:
            return Failure("Invalid username or password")
        
        # Check if user is active
        if not user.is_active:
            return Failure("User account is deactivated")
        
        # Verify password
        if not verify_password(password, user.password_hash):
            return Failure("Invalid username or password")
        
        return Success(user)
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        return await self._repository.get_by_id(user_id)
    
    async def deactivate_user(self, user_id: UUID) -> Result[User, str]:
        """Deactivate a user."""
        user = await self._repository.get_by_id(user_id)
        if not user:
            return Failure(f"User with ID {user_id} not found")
        
        user.deactivate()
        await self._repository.update(user)
        
        return Success(user)
```

Create a task service:

```python
# src/taskmanager/domain/services/task_service.py
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from uno.domain.entity import DomainService
from uno.core.errors.result import Result, Success, Failure
from taskmanager.domain.entities.task import Task
from taskmanager.infrastructure.repositories.task_repository import TaskRepository
from taskmanager.domain.entities.user import User
from taskmanager.infrastructure.repositories.user_repository import UserRepository

class TaskService(DomainService[Task, UUID]):
    """Service for task operations."""
    
    def __init__(self, repository: TaskRepository, user_repository: UserRepository):
        super().__init__(repository)
        self.user_repository = user_repository
    
    async def create_task(self, title: str, creator_id: UUID, description: str = "",
                          priority: str = "medium", due_date: Optional[datetime] = None,
                          tags: List[str] = None) -> Result[Task, str]:
        """Create a new task."""
        # Validate creator exists
        creator = await self.user_repository.get_by_id(creator_id)
        if not creator:
            return Failure(f"Creator with ID {creator_id} not found")
        
        # Create task
        task = Task.create(
            title=title,
            creator_id=creator_id,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags
        )
        
        # Save task
        created_task = await self._repository.add(task)
        
        return Success(created_task)
    
    async def assign_task(self, task_id: UUID, assignee_id: UUID) -> Result[Task, str]:
        """Assign a task to a user."""
        # Get task
        task = await self._repository.get_by_id(task_id)
        if not task:
            return Failure(f"Task with ID {task_id} not found")
        
        # Validate assignee exists
        assignee = await self.user_repository.get_by_id(assignee_id)
        if not assignee:
            return Failure(f"Assignee with ID {assignee_id} not found")
        
        # Assign task
        task.assign(assignee_id)
        
        # Save task
        await self._repository.update(task)
        
        return Success(task)
    
    async def update_task_status(self, task_id: UUID, status: str) -> Result[Task, str]:
        """Update a task's status."""
        # Get task
        task = await self._repository.get_by_id(task_id)
        if not task:
            return Failure(f"Task with ID {task_id} not found")
        
        # Update status
        try:
            task.update_status(status)
        except ValueError as e:
            return Failure(str(e))
        
        # Save task
        await self._repository.update(task)
        
        return Success(task)
    
    async def update_task(self, task_id: UUID, title: Optional[str] = None,
                         description: Optional[str] = None, priority: Optional[str] = None,
                         due_date: Optional[datetime] = None,
                         tags: Optional[List[str]] = None) -> Result[Task, str]:
        """Update a task's details."""
        # Get task
        task = await self._repository.get_by_id(task_id)
        if not task:
            return Failure(f"Task with ID {task_id} not found")
        
        # Update task
        try:
            task.update_details(
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
                tags=tags
            )
        except ValueError as e:
            return Failure(str(e))
        
        # Save task
        await self._repository.update(task)
        
        return Success(task)
    
    async def find_tasks(self, filters: Dict[str, Any]) -> List[Task]:
        """Find tasks matching filter criteria."""
        return await self._repository.find_by_filter(filters)
    
    async def get_user_tasks(self, user_id: UUID, include_created: bool = True,
                           include_assigned: bool = True) -> List[Task]:
        """Get all tasks related to a user."""
        tasks = []
        
        if include_created:
            created_tasks = await self._repository.find_by_creator(user_id)
            tasks.extend(created_tasks)
        
        if include_assigned:
            assigned_tasks = await self._repository.find_by_assignee(user_id)
            # Filter out duplicates
            assigned_tasks = [t for t in assigned_tasks if t.creator_id != user_id]
            tasks.extend(assigned_tasks)
        
        return tasks
```

## Step 10: Create Application Services

Create a file for authentication DTOs:

```python
# src/taskmanager/application/dtos/auth_dtos.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserRegisterDTO(BaseModel):
    """DTO for user registration."""
    
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLoginDTO(BaseModel):
    """DTO for user login."""
    
    username: str
    password: str

class UserResponseDTO(BaseModel):
    """DTO for user response."""
    
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool

class TokenResponseDTO(BaseModel):
    """DTO for token response."""
    
    access_token: str
    token_type: str = "bearer"
    user: UserResponseDTO
```

Create a file for task DTOs:

```python
# src/taskmanager/application/dtos/task_dtos.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TaskCreateDTO(BaseModel):
    """DTO for task creation."""
    
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: Optional[datetime] = None
    tags: List[str] = []

class TaskUpdateDTO(BaseModel):
    """DTO for task update."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None

class TaskAssignDTO(BaseModel):
    """DTO for task assignment."""
    
    assignee_id: str

class TaskStatusDTO(BaseModel):
    """DTO for task status update."""
    
    status: str

class TaskResponseDTO(BaseModel):
    """DTO for task response."""
    
    id: str
    title: str
    description: str
    status: str
    priority: str
    creator_id: str
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: List[str]
    created_at: datetime
    updated_at: datetime

class TaskFilterDTO(BaseModel):
    """DTO for task filtering."""
    
    status: Optional[str] = None
    priority: Optional[str] = None
    creator_id: Optional[str] = None
    assignee_id: Optional[str] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    order_by: Optional[str] = "updated_at"
    order_dir: Optional[str] = "desc"
    limit: Optional[int] = 20
    offset: Optional[int] = 0
```

Create an auth service:

```python
# src/taskmanager/application/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import jwt
from uno.core.errors.result import Result, Success, Failure
from taskmanager.application.dtos.auth_dtos import (
    UserRegisterDTO, UserLoginDTO, UserResponseDTO, TokenResponseDTO
)
from taskmanager.domain.services.user_service import UserService
from taskmanager.domain.entities.user import User
from taskmanager.config import get_settings

class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.config = get_settings()
    
    async def register(self, data: UserRegisterDTO) -> Result[UserResponseDTO, str]:
        """Register a new user."""
        result = await self.user_service.create_user(
            username=data.username,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name
        )
        
        if not result.is_success:
            return Failure(result.error)
        
        user = result.value
        return Success(self._user_to_dto(user))
    
    async def login(self, data: UserLoginDTO) -> Result[TokenResponseDTO, str]:
        """Login a user."""
        result = await self.user_service.authenticate(
            username=data.username,
            password=data.password
        )
        
        if not result.is_success:
            return Failure(result.error)
        
        user = result.value
        
        # Generate token
        token = self._create_token(user.id)
        
        # Return token and user
        return Success(TokenResponseDTO(
            access_token=token,
            user=self._user_to_dto(user)
        ))
    
    def _create_token(self, user_id: UUID) -> str:
        """Create a JWT token for a user."""
        expires_delta = timedelta(minutes=self.config.jwt_expiration)
        expire = datetime.now(datetime.UTC) + expires_delta
        
        payload = {
            "sub": str(user_id),
            "exp": expire.timestamp()
        }
        
        token = jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm
        )
        
        return token
    
    def verify_token(self, token: str) -> Result[UUID, str]:
        """Verify a JWT token and return the user ID."""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            
            user_id = UUID(payload["sub"])
            return Success(user_id)
        except jwt.PyJWTError as e:
            return Failure(f"Invalid token: {str(e)}")
    
    def _user_to_dto(self, user: User) -> UserResponseDTO:
        """Convert a user entity to a DTO."""
        return UserResponseDTO(
            id=str(user.id),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active
        )
```

Create a task application service:

```python
# src/taskmanager/application/services/task_application_service.py
from uuid import UUID
from typing import List, Optional
from uno.core.errors.result import Result, Success, Failure
from taskmanager.application.dtos.task_dtos import (
    TaskCreateDTO, TaskUpdateDTO, TaskAssignDTO, 
    TaskStatusDTO, TaskResponseDTO, TaskFilterDTO
)
from taskmanager.domain.services.task_service import TaskService
from taskmanager.domain.entities.task import Task

class TaskApplicationService:
    """Application service for task operations."""
    
    def __init__(self, task_service: TaskService):
        self.task_service = task_service
    
    async def create_task(self, data: TaskCreateDTO, creator_id: UUID) -> Result[TaskResponseDTO, str]:
        """Create a new task."""
        result = await self.task_service.create_task(
            title=data.title,
            creator_id=creator_id,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            tags=data.tags
        )
        
        if not result.is_success:
            return Failure(result.error)
        
        task = result.value
        return Success(self._task_to_dto(task))
    
    async def update_task(self, task_id: UUID, data: TaskUpdateDTO) -> Result[TaskResponseDTO, str]:
        """Update a task."""
        result = await self.task_service.update_task(
            task_id=task_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            tags=data.tags
        )
        
        if not result.is_success:
            return Failure(result.error)
        
        task = result.value
        return Success(self._task_to_dto(task))
    
    async def assign_task(self, task_id: UUID, data: TaskAssignDTO) -> Result[TaskResponseDTO, str]:
        """Assign a task to a user."""
        result = await self.task_service.assign_task(
            task_id=task_id,
            assignee_id=UUID(data.assignee_id)
        )
        
        if not result.is_success:
            return Failure(result.error)
        
        task = result.value
        return Success(self._task_to_dto(task))
    
    async def update_task_status(self, task_id: UUID, data: TaskStatusDTO) -> Result[TaskResponseDTO, str]:
        """Update a task's status."""
        result = await self.task_service.update_task_status(
            task_id=task_id,
            status=data.status
        )
        
        if not result.is_success:
            return Failure(result.error)
        
        task = result.value
        return Success(self._task_to_dto(task))
    
    async def get_task(self, task_id: UUID) -> Result[TaskResponseDTO, str]:
        """Get a task by ID."""
        task = await self.task_service.get_by_id(task_id)
        
        if not task:
            return Failure(f"Task with ID {task_id} not found")
        
        return Success(self._task_to_dto(task))
    
    async def find_tasks(self, filter_dto: TaskFilterDTO) -> List[TaskResponseDTO]:
        """Find tasks matching filter criteria."""
        # Convert DTO to filter dict
        filters = filter_dto.dict(exclude_none=True)
        
        # Convert string IDs to UUIDs
        if filters.get("creator_id"):
            filters["creator_id"] = UUID(filters["creator_id"])
        
        if filters.get("assignee_id"):
            filters["assignee_id"] = UUID(filters["assignee_id"])
        
        # Get tasks
        tasks = await self.task_service.find_tasks(filters)
        
        # Convert to DTOs
        return [self._task_to_dto(task) for task in tasks]
    
    async def get_user_tasks(self, user_id: UUID, include_created: bool = True,
                          include_assigned: bool = True) -> List[TaskResponseDTO]:
        """Get all tasks related to a user."""
        tasks = await self.task_service.get_user_tasks(
            user_id=user_id,
            include_created=include_created,
            include_assigned=include_assigned
        )
        
        return [self._task_to_dto(task) for task in tasks]
    
    def _task_to_dto(self, task: Task) -> TaskResponseDTO:
        """Convert a task entity to a DTO."""
        return TaskResponseDTO(
            id=str(task.id),
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            creator_id=str(task.creator_id),
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            due_date=task.due_date,
            tags=task.tags,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
```

## Step 11: Create API Endpoints

Create authentication middleware:

```python
# src/taskmanager/api/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from uuid import UUID
from taskmanager.application.services.auth_service import AuthService
from taskmanager.domain.services.user_service import UserService
from taskmanager.domain.entities.user import User
from uno.core.di import get_dependency

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_dependency(AuthService)),
    user_service: UserService = Depends(get_dependency(UserService))
) -> User:
    """Get the current authenticated user."""
    # Verify token
    result = auth_service.verify_token(token)
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = result.value
    
    # Get user
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user
```

Create auth endpoints:

```python
# src/taskmanager/api/endpoints/auth_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status
from uno.api.endpoint import BaseEndpoint
from uno.api.endpoint.response import DataResponse
from uno.core.di import get_dependency
from taskmanager.application.services.auth_service import AuthService
from taskmanager.application.dtos.auth_dtos import (
    UserRegisterDTO, UserLoginDTO, UserResponseDTO, TokenResponseDTO
)

router = APIRouter()

auth_endpoint = BaseEndpoint(router=router, tags=["Authentication"])

@auth_endpoint.router.post("/register", response_model=DataResponse[UserResponseDTO])
async def register(
    data: UserRegisterDTO,
    auth_service: AuthService = Depends(get_dependency(AuthService))
) -> DataResponse[UserResponseDTO]:
    """Register a new user."""
    result = await auth_service.register(data)
    
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    
    return DataResponse(data=result.value)

@auth_endpoint.router.post("/token", response_model=DataResponse[TokenResponseDTO])
async def login(
    data: UserLoginDTO,
    auth_service: AuthService = Depends(get_dependency(AuthService))
) -> DataResponse[TokenResponseDTO]:
    """Login to get an access token."""
    result = await auth_service.login(data)
    
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.error,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return DataResponse(data=result.value)
```

Create task endpoints:

```python
# src/taskmanager/api/endpoints/task_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uno.api.endpoint import BaseEndpoint
from uno.api.endpoint.response import DataResponse
from uno.core.di import get_dependency
from uuid import UUID
from typing import List, Optional
from taskmanager.application.services.task_application_service import TaskApplicationService
from taskmanager.application.dtos.task_dtos import (
    TaskCreateDTO, TaskUpdateDTO, TaskAssignDTO,
    TaskStatusDTO, TaskResponseDTO, TaskFilterDTO
)
from taskmanager.api.auth import get_current_user
from taskmanager.domain.entities.user import User

router = APIRouter()

task_endpoint = BaseEndpoint(router=router, tags=["Tasks"])

@task_endpoint.router.post("", response_model=DataResponse[TaskResponseDTO])
async def create_task(
    data: TaskCreateDTO,
    current_user: User = Depends(get_current_user),
    task_service: TaskApplicationService = Depends(get_dependency(TaskApplicationService))
) -> DataResponse[TaskResponseDTO]:
    """Create a new task."""
    result = await task_service.create_task(data, current_user.id)
    
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    
    return DataResponse(data=result.value)

@task_endpoint.router.get("", response_model=DataResponse[List[TaskResponseDTO]])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    creator_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    search: Optional[str] = None,
    order_by: Optional[str] = "updated_at",
    order_dir: Optional[str] = "desc",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    task_service: TaskApplicationService = Depends(get_dependency(TaskApplicationService))
) -> DataResponse[List[TaskResponseDTO]]:
    """List tasks with filters."""
    # Build filter
    filter_dto = TaskFilterDTO(
        status=status,
        priority=priority,
        creator_id=creator_id,
        assignee_id=assignee_id,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        limit=limit,
        offset=offset
    )
    
    tasks = await task_service.find_tasks(filter_dto)
    
    return DataResponse(data=tasks)

@task_endpoint.router.get("/me", response_model=DataResponse[List[TaskResponseDTO]])
async def get_my_tasks(
    include_created: bool = True,
    include_assigned: bool = True,
    current_user: User = Depends(get_current_user),
    task_service: TaskApplicationService = Depends(get_dependency(TaskApplicationService))
) -> DataResponse[List[TaskResponseDTO]]:
    """Get tasks related to the current user."""
    tasks = await task_service.get_user_tasks(
        user_id=current_user.id,
        include_created=include_created,
        include_assigned=include_assigned
    )
    
    return DataResponse(data=tasks)

@task_endpoint.router.get("/{task_id}", response_model=DataResponse[TaskResponseDTO])
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskApplicationService = Depends(get_dependency(TaskApplicationService))
) -> DataResponse[TaskResponseDTO]:
    """Get a task by ID."""
    result = await task_service.get_task(task_id)
    
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.error
        )
    
    return DataResponse(data=result.value)

@task_endpoint.router.put("/{task_id}", response_model=DataResponse[TaskResponseDTO])
async def update_task(
    task_id: UUID,
    data: TaskUpdateDTO,
    current_user: User = Depends(get_current_user),
    task_service: TaskApplicationService = Depends(get_dependency(TaskApplicationService))
) -> DataResponse[TaskResponseDTO]:
    """Update a task."""
    result = await task_service.update_task(task_id, data)
    
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    
    return DataResponse(data=result.value)

@task_endpoint.router.put("/{task_id}/assign", response_model=DataResponse[TaskResponseDTO])
async def assign_task(
    task_id: UUID,
    data: TaskAssignDTO,
    current_user: User = Depends(get_current_user),
    task_service: TaskApplicationService = Depends(get_dependency(TaskApplicationService))
) -> DataResponse[TaskResponseDTO]:
    """Assign a task to a user."""
    result = await task_service.assign_task(task_id, data)
    
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    
    return DataResponse(data=result.value)

@task_endpoint.router.put("/{task_id}/status", response_model=DataResponse[TaskResponseDTO])
async def update_task_status(
    task_id: UUID,
    data: TaskStatusDTO,
    current_user: User = Depends(get_current_user),
    task_service: TaskApplicationService = Depends(get_dependency(TaskApplicationService))
) -> DataResponse[TaskResponseDTO]:
    """Update a task's status."""
    result = await task_service.update_task_status(task_id, data)
    
    if not result.is_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
    
    return DataResponse(data=result.value)
```

## Step 12: Create Database Setup

Create a file to manage database connections:

```python
# src/taskmanager/infrastructure/database/setup.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from taskmanager.infrastructure.database.models import Base
from taskmanager.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=5,
    max_overflow=10
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_session() -> AsyncSession:
    """Get a database session."""
    async with async_session_factory() as session:
        yield session

async def init_db() -> None:
    """Initialize the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

## Step 13: Create Application Factory

Create the application factory:

```python
# src/taskmanager/app.py
from fastapi import FastAPI
from uno.api.endpoint.middleware import setup_error_handlers
from uno.core.di import configure_container
from typing import List, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from taskmanager.config import get_settings
from taskmanager.infrastructure.database.setup import get_session, init_db
from taskmanager.api.endpoints.auth_endpoints import auth_endpoint
from taskmanager.api.endpoints.task_endpoints import task_endpoint
from taskmanager.application.services.auth_service import AuthService
from taskmanager.application.services.task_application_service import TaskApplicationService
from taskmanager.domain.services.user_service import UserService
from taskmanager.domain.services.task_service import TaskService
from taskmanager.infrastructure.repositories.user_repository import UserRepository
from taskmanager.infrastructure.repositories.task_repository import TaskRepository

def create_app() -> FastAPI:
    """Create the FastAPI application."""
    # Get settings
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None
    )
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup dependency injection
    configure_container()
    configure_dependencies()
    
    # Add startup and shutdown events
    app.add_event_handler("startup", startup_handler)
    
    # Register endpoints
    auth_endpoint.register(app, prefix="/api/auth")
    task_endpoint.register(app, prefix="/api/tasks")
    
    return app

def configure_dependencies() -> None:
    """Configure dependency injection."""
    from uno.core.di import container
    from fastapi import Depends
    
    # Register session
    container.register(AsyncSession, factory=get_session)
    
    # Register repositories
    container.register(UserRepository, lambda: UserRepository(Depends(get_session)))
    container.register(TaskRepository, lambda: TaskRepository(Depends(get_session)))
    
    # Register domain services
    container.register(UserService, lambda: UserService(Depends(UserRepository)))
    container.register(TaskService, lambda: TaskService(
        Depends(TaskRepository),
        Depends(UserRepository)
    ))
    
    # Register application services
    container.register(AuthService, lambda: AuthService(Depends(UserService)))
    container.register(TaskApplicationService, lambda: TaskApplicationService(Depends(TaskService)))

async def startup_handler() -> None:
    """Handle application startup."""
    # Initialize database
    await init_db()
```

## Step 14: Create Main Entry Point

Create a main.py file:

```python
# main.py
import uvicorn
from taskmanager.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

## Step 15: Run the Application

Start the Docker environment:

```bash
./docker/start.sh
```

Run the application:

```bash
python main.py
```

Your API should now be accessible at http://localhost:8000.

To test your API, go to http://localhost:8000/docs to see the Swagger UI and interact with your endpoints.

## What We've Built

We've created a task management API with:

1. **Clean Architecture**
   - Domain layer with entities and services
   - Application layer with DTOs and services
   - Infrastructure layer with repositories
   - API layer with endpoints

2. **Domain-Driven Design**
   - Rich domain model with business rules
   - Value objects and entities
   - Domain events
   - Repositories and services

3. **Event-Driven Architecture**
   - Domain events for significant changes
   - Event recording and publishing

4. **Modern API Design**
   - RESTful endpoints
   - CRUD operations
   - Filtering and pagination
   - Authentication

## Next Steps

Here's how you can extend your application:

1. **Add Access Control**: Implement fine-grained permissions
2. **Add Notifications**: Create a notification system for task assignments
3. **Implement Projections**: Create specialized read models for complex queries
4. **Add Event Handlers**: Handle domain events for side effects
5. **Create a Frontend**: Build a web or mobile frontend using the API

## Conclusion

This tutorial has demonstrated how to build a complete web application with the Uno framework. You've learned how to:

- Create a domain model with entities and value objects
- Implement business logic in domain services
- Use repositories for data access
- Create application services for use case handling
- Build a REST API with FastAPI
- Implement authentication and validation
- Structure a clean, maintainable application

You now have a solid foundation for building more complex applications using DDD principles and clean architecture with the Uno framework.