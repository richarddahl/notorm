# Getting Started with uno

This guide will help you get started with uno, a comprehensive application framework for building data-driven applications with PostgreSQL and FastAPI.

## Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.12+
- PostgreSQL 16+
- Docker (optional, for local development)

## Installation

### 1. Install the Package

```console
pip install uno
```

### 2. Set Up the Database

Uno works best with PostgreSQL 16+. You can set up a PostgreSQL instance using Docker:

```console
cd uno/docker
docker build -t pg16_uno .
docker-compose up
```

Alternatively, you can use an existing PostgreSQL instance.

## Quick Start Example

Here's a simple example to get you started:

```python
from uno.database.engine import DatabaseFactory
from uno.model import UnoModel
from uno.obj import UnoObj

# Initialize the database factory
db_factory = DatabaseFactory()

# Define a model
class User(UnoModel):
    __tablename__ = "user"
    
    id: str
    email: str
    handle: str
    full_name: str
    
# Define business logic
class UserObj(UnoObj):
    model = User  # Link to the model class
    
    id: str
    email: str
    handle: str
    full_name: str
    
    def validate_email(self):
        if "@" not in self.email:
            raise ValueError("Invalid email format")
```

## Setting Up the Environment

### Create a Virtual Environment

```console
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Development Dependencies

```console
pip install -e ".[dev]"
```

## Documentation

The documentation can be viewed locally at 127.0.0.1:8001 in a browser after running:

```console
mkdocs serve -a 127.0.0.1:8001
```

from a (virtual environment-enabled) shell.

## Next Steps

Now that you've set up the basics, you might want to explore:

- [Core Concepts](architecture/overview.md): Learn about the fundamental concepts of the framework
- [Database Layer](database/overview.md): Understand the database connection management
- [Models](models/overview.md): Learn how to define data models
- [Business Logic](business_logic/overview.md): Understand how to implement business logic with UnoObj
- [API Integration](api/overview.md): Learn how to expose your business logic through API endpoints
