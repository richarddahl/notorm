# Getting Started with uno

This guide will help you get started with uno, a comprehensive application framework for building data-driven applications with PostgreSQL and FastAPI.

## Overview

uno provides a unified approach to database operations, API definition, and business logic. It's designed to make development faster and more maintainable by offering a cohesive set of tools and patterns.

## Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.12+
- PostgreSQL 16+ 
- Docker (recommended for local development)

## Installation Options

### Option 1: Docker Setup (Recommended)

The easiest way to get started is using Docker for PostgreSQL:

```bash
# Clone the repository
git clone https://github.com/yourusername/uno.git
cd uno

# Start the Docker environment
./scripts/docker/start.sh

# Create the database
python src/scripts/createdb.py
```

### Option 2: Manual Installation

If you prefer to set up manually:

1. Install the package:

```bash
pip install uno
```

2. Install PostgreSQL 16+ on your system

3. Configure the database connection:

```bash
# Create a .env file with your database configuration
cat > .env << EOL
DB_HOST=localhost
DB_PORT=5432
DB_SCHEMA=public
DB_NAME=uno_dev
DB_USER=postgres
DB_USER_PW=your_password
EOL
```

## Quick Start Example

Here's a simple example to get you started:

```python
from uno.database.engine import DatabaseFactory
from uno.model import UnoModel, PostgresTypes
from uno.obj import UnoObj
from sqlalchemy.orm import Mapped, mapped_column

# Define a model
class User(UnoModel):```

__tablename__ = "user"
``````

```
```

id: Mapped[PostgresTypes.String26] = mapped_column(primary_key=True)
email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False, unique=True)
handle: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
full_name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
```
    
# Define business logic
class UserObj(UnoObj):```

model = User  # Link to the model class
``````

```
```

id: str
email: str
handle: str
full_name: str
``````

```
```

def validate_email(self):```

if "@" not in self.email:
    raise ValueError("Invalid email format")
```
```

# Create a database interface
from uno.database.db import UnoDBFactory
db = UnoDBFactory(obj=UserObj)

# Create a new user
async def create_user():```

user_data = {```

"email": "user@example.com",
"handle": "user123",
"full_name": "Example User"
```
}
user, created = await db.create(schema=user_data)
return user
```
```

## Creating an API

uno makes it easy to create RESTful APIs with FastAPI:

```python
from fastapi import FastAPI, Depends
from uno.api.endpoint_factory import EndpointFactory
from uno.dependencies.fastapi import get_db_session

app = FastAPI()

# Create API endpoints for the User model
user_endpoints = EndpointFactory.create_endpoints(```

obj_class=UserObj,
prefix="/users",
tag="Users",
session_dependency=get_db_session
```
)

# Add the endpoints to the app
app.include_router(user_endpoints)

# Define a custom endpoint
@app.get("/users/by-email/{email}")
async def get_user_by_email(email: str, session = Depends(get_db_session)):```

# Create a repository
from uno.database.repository import UnoBaseRepository
repo = UnoBaseRepository(session, User)
``````

```
```

# Query the database
user = await repo.get_by(User.email == email)
if not user:```

return {"error": "User not found"}
```
``````

```
```

return user
```
```

## Development Environment

### Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
# Set up test environment
./scripts/docker/test/setup.sh

# Run tests
python -m pytest
```

### View Documentation

```bash
# Serve documentation locally
mkdocs serve -a 127.0.0.1:8001
```

Then open your browser at [http://127.0.0.1:8001](http://127.0.0.1:8001).

## Key Concepts

uno is built around several key concepts:

- **UnoModel**: SQLAlchemy-based models for database mapping
- **UnoObj**: Business logic containers that wrap models
- **UnoSchema**: Pydantic models for data validation and serialization
- **UnoDB**: Database operations interface
- **UnoEndpoint**: FastAPI-based endpoints for RESTful APIs
- **SQL Emitters**: Components that generate SQL for database objects

## Next Steps

Now that you've set up the basics, explore these topics:

- [Architecture Overview](architecture/overview.md): Learn about the fundamental concepts and design principles
- [Database Layer](database/overview.md): Understand database connection management and ORM features
- [Business Logic](business_logic/overview.md): Implement domain logic with UnoObj
- [API Integration](api/overview.md): Create RESTful APIs with FastAPI
- [Vector Search](vector_search/overview.md): Implement semantic search with pgvector
- [Dependency Injection](dependency_injection/overview.md): Use the modern DI system for better testing