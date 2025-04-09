# Uno Framework Overview

The Uno Framework is a comprehensive Python framework for building web applications with FastAPI and SQLAlchemy. It provides a structured approach to creating database models, business logic, and RESTful APIs.

## Key Components

The Uno Framework consists of several key components:

1. **UnoModel** - SQLAlchemy base model with standardized PostgreSQL types
2. **UnoObj** - Business logic layer with active record pattern
3. **UnoRegistry** - Central registry for model classes
4. **UnoSchemaManager** - Schema creation and validation
5. **UnoFilterManager** - Filter creation and validation
6. **UnoEndpointFactory** - FastAPI endpoint generation
7. **UnoDB** - Database operations and queries

These components work together to provide a cohesive framework for application development.

## Architecture

The Uno Framework follows a layered architecture:

1. **Database Layer** - SQLAlchemy models and database operations
2. **Business Logic Layer** - Business objects and domain logic
3. **Schema Layer** - Data validation and serialization
4. **API Layer** - RESTful API endpoints

This separation of concerns makes applications more maintainable and testable.

## Core Principles

The Uno Framework is built on several core principles:

1. **Dependency Injection** - Components are designed for dependency injection
2. **Separation of Concerns** - Each component has a single responsibility
3. **Consistency** - Standardized patterns for models, schemas, and APIs
4. **Testability** - Components are easily testable in isolation
5. **Performance** - Optimized database operations and connection pooling
6. **Security** - Built-in protection against common vulnerabilities

These principles ensure that applications built with Uno are robust, maintainable, and secure.

## Getting Started

To get started with the Uno Framework, first install it from PyPI:

```bash
pip install notorm
```

Then create your first model and business object:

```python
from uno.model import UnoModel, PostgresTypes
from uno.obj import UnoObj
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchemaConfig
from uno.mixins import ModelMixin

# Define your model
class UserModel(UnoModel, ModelMixin):
    __tablename__ = "user"
    
    # Inherits id, is_active, is_deleted, created_at, modified_at, deleted_at from ModelMixin
    
    username: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        unique=True,
        doc="User's username"
    )
    email: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        unique=True,
        doc="User's email address"
    )
    full_name: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=True,
        doc="User's full name"
    )

# Define your business object
class User(UnoObj[UserModel]):
    model = UserModel
    
    schema_configs = {
        "view_schema": UnoSchemaConfig(),  # All fields
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at", "deleted_at"}),
    }
    
    # Add business logic methods
    async def send_welcome_email(self):
        """Send a welcome email to the user."""
        if not self.email:
            raise ValueError("User has no email address")
            
        # Email sending logic here
        print(f"Sending welcome email to {self.email}")
        return True
```

Create a FastAPI application with endpoints:

```python
from fastapi import FastAPI

# Create the app
app = FastAPI(title="Uno Example App")

# Configure the User model
User.configure(app)

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Complete Example

Here's a complete example of a simple Uno application:

```python
from fastapi import FastAPI
from uno.model import UnoModel, PostgresTypes
from uno.obj import UnoObj
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchemaConfig
from uno.mixins import ModelMixin
from typing import Optional, List

# Define models
class TodoModel(UnoModel, ModelMixin):
    __tablename__ = "todo"
    
    title: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        doc="Todo title"
    )
    description: Mapped[Optional[PostgresTypes.Text]] = mapped_column(
        nullable=True,
        doc="Todo description"
    )
    completed: Mapped[bool] = mapped_column(
        default=False,
        doc="Whether the todo is completed"
    )
    
class TodoListModel(UnoModel, ModelMixin):
    __tablename__ = "todo_list"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        doc="Todo list name"
    )
    
    # Relationship to todos
    # This would typically use SQLAlchemy relationship(), but simplifying for the example

# Define business objects
class Todo(UnoObj[TodoModel]):
    model = TodoModel
    
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at", "deleted_at"}),
    }
    
    async def mark_completed(self):
        """Mark the todo as completed."""
        self.completed = True
        await self.save()
        return self

class TodoList(UnoObj[TodoListModel]):
    model = TodoListModel
    
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "modified_at", "deleted_at"}),
    }
    
    async def get_todos(self):
        """Get all todos in this list."""
        # This would typically use a relationship, but simplifying for the example
        filter_params = Todo.create_filter_params()(
            todo_list_id=self.id,
            limit=100
        )
        return await Todo.filter(filters=filter_params)
    
    async def add_todo(self, title: str, description: Optional[str] = None):
        """Add a new todo to this list."""
        todo = Todo(
            todo_list_id=self.id,
            title=title,
            description=description,
            completed=False
        )
        await todo.save()
        return todo

# Create the app
app = FastAPI(title="Todo App")

# Configure models
Todo.configure(app)
TodoList.configure(app)

# Add custom endpoints
@app.get("/api/v1/todo-lists/{list_id}/todos")
async def get_todos_in_list(list_id: str):
    """Get all todos in a list."""
    todo_list = await TodoList.get(id=list_id)
    return await todo_list.get_todos()

@app.post("/api/v1/todo-lists/{list_id}/todos")
async def add_todo_to_list(list_id: str, title: str, description: Optional[str] = None):
    """Add a new todo to a list."""
    todo_list = await TodoList.get(id=list_id)
    return await todo_list.add_todo(title, description)

@app.post("/api/v1/todos/{todo_id}/complete")
async def complete_todo(todo_id: str):
    """Mark a todo as completed."""
    todo = await Todo.get(id=todo_id)
    return await todo.mark_completed()

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Integration with Other Libraries

The Uno Framework is designed to integrate with other libraries in the Python ecosystem:

### Authentication with OAuth2

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import bcrypt
import jwt
from datetime import datetime, timedelta

# Define user model
class UserModel(UnoModel, ModelMixin):
    __tablename__ = "user"
    
    username: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        unique=True
    )
    email: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False,
        unique=True
    )
    password_hash: Mapped[PostgresTypes.String255] = mapped_column(
        nullable=False
    )

# Define user business object
class User(UnoObj[UserModel]):
    model = UserModel
    
    schema_configs = {
        "view_schema": UnoSchemaConfig(exclude_fields={"password_hash"}),
        "edit_schema": UnoSchemaConfig(exclude_fields={"password_hash", "created_at", "modified_at", "deleted_at"}),
    }
    
    @classmethod
    async def authenticate(cls, username: str, password: str):
        """Authenticate a user."""
        try:
            user = await cls.get(username=username)
            if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                return user
        except Exception:
            pass
        return None
    
    @classmethod
    async def create_user(cls, username: str, email: str, password: str):
        """Create a new user."""
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        # Create the user
        user = cls(
            username=username,
            email=email,
            password_hash=password_hash
        )
        await user.save()
        return user
    
    def create_access_token(self, expires_delta: Optional[timedelta] = None):
        """Create an access token for the user."""
        expires_delta = expires_delta or timedelta(minutes=15)
        expires = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": self.username,
            "exp": expires
        }
        
        return jwt.encode(payload, "your-secret-key", algorithm="HS256")

# Create the app
app = FastAPI(title="Auth Example")

# Configure the User model
User.configure(app)

# OAuth2 password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from the token."""
    try:
        payload = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await User.get(username=username)
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get an access token."""
    user = await User.authenticate(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = user.create_access_token()
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def register(username: str, email: str, password: str):
    """Register a new user."""
    try:
        user = await User.create_user(username, email, password)
        return {"message": "User created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get the current user."""
    return current_user
```

## Additional Resources

For more information about the Uno Framework, refer to the following resources:

- [UnoModel Documentation](./uno_model.md) - Database models
- [UnoObj Documentation](./uno_obj.md) - Business logic layer
- [UnoRegistry Documentation](./uno_registry.md) - Model registry
- [UnoSchemaManager Documentation](./uno_schema_manager.md) - Schema management
- [UnoFilterManager Documentation](./uno_filter_manager.md) - Filter management
- [UnoEndpointFactory Documentation](./uno_endpoint_factory.md) - API endpoints
- [UnoDB Documentation](./uno_db.md) - Database operations

## Best Practices

When working with the Uno Framework, follow these best practices:

1. **Organize by Domain** - Group models, business objects, and schemas by domain
2. **Keep Business Logic in UnoObj** - Put domain logic in UnoObj methods, not in endpoints
3. **Use Dependency Injection** - Inject dependencies for better testability
4. **Write Tests** - Test each layer independently
5. **Document Your Code** - Add docstrings to classes and methods
6. **Follow SQLAlchemy Patterns** - Leverage SQLAlchemy's best practices
7. **Validate Input Data** - Use Pydantic validation in schemas
8. **Handle Errors Gracefully** - Catch and handle specific exceptions
9. **Monitor Performance** - Watch for slow queries and optimize
10. **Keep Security in Mind** - Implement proper authentication and authorization
