"""
Project structure generation for Uno applications.

This module provides tools for creating new projects and modules
with the recommended structure and boilerplate code.
"""

import os
import shutil
from typing import Dict, List, Optional, Any, Set

from uno.devtools.codegen.formatter import format_code


def create_project(
    name: str,
    description: str = "",
    author: str = "",
    email: str = "",
    with_docker: bool = True,
    with_github_actions: bool = False,
    output_dir: Optional[str] = None
) -> str:
    """
    Create a new Uno project with the recommended structure.
    
    Args:
        name: Project name (should be a valid Python package name)
        description: Project description
        author: Project author name
        email: Project author email
        with_docker: Include Docker configuration
        with_github_actions: Include GitHub Actions workflows
        output_dir: Output directory (defaults to current directory)
        
    Returns:
        Path to the created project
    """
    # Set default output directory to current directory if not provided
    if output_dir is None:
        output_dir = os.getcwd()
    
    # Create project directory
    project_dir = os.path.join(output_dir, name)
    os.makedirs(project_dir, exist_ok=True)
    
    # Create project structure
    create_project_structure(project_dir, name, with_docker, with_github_actions)
    
    # Create project files
    create_project_files(project_dir, name, description, author, email, with_docker, with_github_actions)
    
    return project_dir


def create_module(
    name: str,
    project_dir: str,
    with_api: bool = True,
    with_models: bool = True,
    with_repositories: bool = True,
    with_services: bool = True
) -> str:
    """
    Create a new module within an existing Uno project.
    
    Args:
        name: Module name (should be a valid Python package name)
        project_dir: Path to the project directory
        with_api: Include API endpoints
        with_models: Include models
        with_repositories: Include repositories
        with_services: Include services
        
    Returns:
        Path to the created module
    """
    # Determine the src directory
    src_dir = os.path.join(project_dir, "src")
    if not os.path.exists(src_dir):
        # Try to find a directory that might contain the source code
        candidates = [
            os.path.join(project_dir, d) for d in os.listdir(project_dir)
            if os.path.isdir(os.path.join(project_dir, d)) and not d.startswith(".")
        ]
        
        for candidate in candidates:
            if os.path.exists(os.path.join(candidate, "__init__.py")):
                src_dir = candidate
                break
    
    # Create module directory
    module_dir = os.path.join(src_dir, name)
    os.makedirs(module_dir, exist_ok=True)
    
    # Create module files
    create_module_files(module_dir, name, with_api, with_models, with_repositories, with_services)
    
    return module_dir


def create_project_structure(
    project_dir: str,
    name: str,
    with_docker: bool = True,
    with_github_actions: bool = False
) -> None:
    """
    Create the directory structure for a new Uno project.
    
    Args:
        project_dir: Path to the project directory
        name: Project name
        with_docker: Include Docker configuration
        with_github_actions: Include GitHub Actions workflows
    """
    # Create main directories
    os.makedirs(os.path.join(project_dir, "src", name), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "tests", "unit"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "tests", "integration"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "docs"), exist_ok=True)
    
    # Create source code subdirectories
    src_dir = os.path.join(project_dir, "src", name)
    os.makedirs(os.path.join(src_dir, "api"), exist_ok=True)
    os.makedirs(os.path.join(src_dir, "core"), exist_ok=True)
    os.makedirs(os.path.join(src_dir, "db"), exist_ok=True)
    os.makedirs(os.path.join(src_dir, "models"), exist_ok=True)
    os.makedirs(os.path.join(src_dir, "repositories"), exist_ok=True)
    os.makedirs(os.path.join(src_dir, "services"), exist_ok=True)
    os.makedirs(os.path.join(src_dir, "utils"), exist_ok=True)
    
    # Create Docker directories if requested
    if with_docker:
        os.makedirs(os.path.join(project_dir, "docker"), exist_ok=True)
    
    # Create GitHub Actions directories if requested
    if with_github_actions:
        os.makedirs(os.path.join(project_dir, ".github", "workflows"), exist_ok=True)


def create_project_files(
    project_dir: str,
    name: str,
    description: str,
    author: str,
    email: str,
    with_docker: bool = True,
    with_github_actions: bool = False
) -> None:
    """
    Create the boilerplate files for a new Uno project.
    
    Args:
        project_dir: Path to the project directory
        name: Project name
        description: Project description
        author: Project author name
        email: Project author email
        with_docker: Include Docker configuration
        with_github_actions: Include GitHub Actions workflows
    """
    # Create package __init__ files
    create_file(os.path.join(project_dir, "src", "__init__.py"), "")
    create_file(os.path.join(project_dir, "src", name, "__init__.py"), f'"""\\n{description}\\n"""\\n\\n__version__ = "0.1.0"\\n')
    
    # Create subdirectory __init__ files
    for subdir in ["api", "core", "db", "models", "repositories", "services", "utils"]:
        create_file(os.path.join(project_dir, "src", name, subdir, "__init__.py"), "")
    
    # Create test __init__ files
    create_file(os.path.join(project_dir, "tests", "__init__.py"), "")
    create_file(os.path.join(project_dir, "tests", "unit", "__init__.py"), "")
    create_file(os.path.join(project_dir, "tests", "integration", "__init__.py"), "")
    
    # Create README.md
    readme_content = f"""# {name}

{description}

## Installation

```bash
pip install {name}
```

## Usage

```python
import {name}

# Example usage
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/username/{name}.git
cd {name}

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\\Scripts\\activate`

# Install development dependencies
pip install -e ".[dev]"
```

### Testing

```bash
pytest
```

## License

This project is licensed under the terms of the MIT license.
"""
    create_file(os.path.join(project_dir, "README.md"), readme_content)
    
    # Create pyproject.toml
    pyproject_content = f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = "{description}"
readme = "README.md"
requires-python = ">=3.9"
license = "MIT"
authors = [
    {{ name = "{author}", email = "{email}" }}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "uno-framework",
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "pydantic>=2.0.0",
    "asyncpg",
    "python-dotenv",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "black",
    "isort",
    "mypy",
    "pre-commit",
]

[project.urls]
Homepage = "https://github.com/username/{name}"
Issues = "https://github.com/username/{name}/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/{name}"]

[tool.hatch.envs.default]
dependencies = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "black",
    "isort",
    "mypy",
]

[tool.hatch.envs.default.scripts]
test = "pytest {{args}}"
test-cov = "pytest --cov={name} {{args}}"
lint = ["black .", "isort .", "mypy src"]
format = ["black .", "isort ."]

[tool.black]
line-length = 88
target-version = ["py39"]
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
"""
    create_file(os.path.join(project_dir, "pyproject.toml"), pyproject_content)
    
    # Create main.py application entry point
    main_content = f"""#!/usr/bin/env python3
\"\"\"
{name} - {description}
\"\"\"

import logging
import os
from typing import List

import uvicorn
from fastapi import FastAPI, Depends
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI application
app = FastAPI(
    title="{name}",
    description="{description}",
    version="0.1.0",
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add API routers
# app.include_router(router1, prefix="/api")
# app.include_router(router2, prefix="/api")

@app.get("/")
async def root():
    return {{"message": "Welcome to {name}!"}}

@app.get("/health")
async def health():
    return {{"status": "ok"}}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=bool(os.getenv("DEBUG", "False") == "True"),
    )
"""
    create_file(os.path.join(project_dir, "src", name, "main.py"), main_content)
    
    # Create Docker files if requested
    if with_docker:
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \\
    PYTHONUNBUFFERED=1 \\
    PYTHONHASHSEED=random \\
    PYTHONDONTWRITEBYTECODE=1 \\
    PIP_NO_CACHE_DIR=off \\
    PIP_DISABLE_PIP_VERSION_CHECK=on \\
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy source code
COPY src/ /app/src/

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.main"]
"""
        create_file(os.path.join(project_dir, "docker", "Dockerfile"), dockerfile_content)
        
        docker_compose_content = """version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app
      - DEBUG=False
    depends_on:
      - db
    volumes:
      - ../src:/app/src
    networks:
      - app-network

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres-data:
"""
        create_file(os.path.join(project_dir, "docker", "docker-compose.yml"), docker_compose_content)
    
    # Create GitHub Actions workflow if requested
    if with_github_actions:
        github_workflow_content = """name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    - name: Lint with black and isort
      run: |
        black --check .
        isort --check .
    - name: Type check with mypy
      run: |
        mypy src
    - name: Test with pytest
      run: |
        pytest --cov=src
"""
        create_file(os.path.join(project_dir, ".github", "workflows", "ci.yml"), github_workflow_content)


def create_module_files(
    module_dir: str,
    name: str,
    with_api: bool = True,
    with_models: bool = True,
    with_repositories: bool = True,
    with_services: bool = True
) -> None:
    """
    Create the boilerplate files for a new module.
    
    Args:
        module_dir: Path to the module directory
        name: Module name
        with_api: Include API endpoints
        with_models: Include models
        with_repositories: Include repositories
        with_services: Include services
    """
    # Create __init__.py
    create_file(os.path.join(module_dir, "__init__.py"), f'"""\\n{name} module\\n"""\\n')
    
    # Create subdirectories and files
    if with_models:
        os.makedirs(os.path.join(module_dir, "models"), exist_ok=True)
        create_file(os.path.join(module_dir, "models", "__init__.py"), "")
        
        # Create a sample model
        model_content = f"""from typing import Optional, List
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from uno.database.model import UnoModel


class {name.capitalize()}(UnoModel):
    \"\"\"
    {name.capitalize()} model
    \"\"\"
    __tablename__ = "{name.lower()}s"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<{name.capitalize()}(id={self.id}, name={self.name})>"
"""
        create_file(os.path.join(module_dir, "models", f"{name.lower()}.py"), model_content)
    
    if with_repositories:
        os.makedirs(os.path.join(module_dir, "repositories"), exist_ok=True)
        create_file(os.path.join(module_dir, "repositories", "__init__.py"), "")
        
        # Create a sample repository
        repository_content = f"""from typing import List, Optional, Dict, Any, Union
from uno.database.repository import UnoRepository
from uno.core.result import Result, Success, Failure

from ..models.{name.lower()} import {name.capitalize()}


class {name.capitalize()}Repository(UnoRepository):
    \"\"\"
    Repository for {name.capitalize()} entities
    \"\"\"
    
    async def get_by_id(self, id: int) -> Result[Optional[{name.capitalize()}]]:
        \"\"\"
        Get a {name.lower()} by ID
        \"\"\"
        try:
            query = self.session.query({name.capitalize()}).filter({name.capitalize()}.id == id)
            result = await self.session.execute(query)
            item = result.scalars().first()
            return Success(item)
        except Exception as e:
            return Failure(e)
    
    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Result[List[{name.capitalize()}]]:
        \"\"\"
        List {name.lower()}s with optional filtering
        \"\"\"
        try:
            query = self.session.query({name.capitalize()})
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if hasattr({name.capitalize()}, field):
                        query = query.filter(getattr({name.capitalize()}, field) == value)
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            items = result.scalars().all()
            return Success(items)
        except Exception as e:
            return Failure(e)
    
    async def create(self, item: {name.capitalize()}) -> Result[{name.capitalize()}]:
        \"\"\"
        Create a new {name.lower()}
        \"\"\"
        try:
            self.session.add(item)
            await self.session.flush()
            await self.session.refresh(item)
            return Success(item)
        except Exception as e:
            return Failure(e)
    
    async def update(self, item: {name.capitalize()}) -> Result[{name.capitalize()}]:
        \"\"\"
        Update an existing {name.lower()}
        \"\"\"
        try:
            await self.session.merge(item)
            await self.session.flush()
            await self.session.refresh(item)
            return Success(item)
        except Exception as e:
            return Failure(e)
    
    async def delete(self, id: int) -> Result[bool]:
        \"\"\"
        Delete a {name.lower()} by ID
        \"\"\"
        try:
            query = self.session.query({name.capitalize()}).filter({name.capitalize()}.id == id)
            result = await self.session.execute(query)
            item = result.scalars().first()
            
            if not item:
                return Failure(f"{name.capitalize()} with id {{id}} not found")
            
            await self.session.delete(item)
            return Success(True)
        except Exception as e:
            return Failure(e)
"""
        create_file(os.path.join(module_dir, "repositories", f"{name.lower()}_repository.py"), repository_content)
    
    if with_services:
        os.makedirs(os.path.join(module_dir, "services"), exist_ok=True)
        create_file(os.path.join(module_dir, "services", "__init__.py"), "")
        
        # Create a sample service
        service_content = f"""from typing import List, Optional, Dict, Any, Union
from uno.core.result import Result, Success, Failure

from ..models.{name.lower()} import {name.capitalize()}
from ..repositories.{name.lower()}_repository import {name.capitalize()}Repository


class {name.capitalize()}Service:
    \"\"\"
    Service for {name.capitalize()} operations
    \"\"\"
    
    def __init__(self, repository: {name.capitalize()}Repository):
        self.repository = repository
    
    async def get_by_id(self, id: int) -> Result[Optional[{name.capitalize()}]]:
        \"\"\"
        Get a {name.lower()} by ID
        \"\"\"
        return await self.repository.get_by_id(id)
    
    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Result[List[{name.capitalize()}]]:
        \"\"\"
        List {name.lower()}s with optional filtering
        \"\"\"
        return await self.repository.list(limit=limit, offset=offset, filters=filters)
    
    async def create(self, item: {name.capitalize()}) -> Result[{name.capitalize()}]:
        \"\"\"
        Create a new {name.lower()}
        \"\"\"
        return await self.repository.create(item)
    
    async def update(self, item: {name.capitalize()}) -> Result[{name.capitalize()}]:
        \"\"\"
        Update an existing {name.lower()}
        \"\"\"
        return await self.repository.update(item)
    
    async def delete(self, id: int) -> Result[bool]:
        \"\"\"
        Delete a {name.lower()} by ID
        \"\"\"
        return await self.repository.delete(id)
"""
        create_file(os.path.join(module_dir, "services", f"{name.lower()}_service.py"), service_content)
    
    if with_api:
        os.makedirs(os.path.join(module_dir, "api"), exist_ok=True)
        create_file(os.path.join(module_dir, "api", "__init__.py"), "")
        
        # Create a sample API router
        api_content = f"""from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime

from uno.dependencies import get_db_session
from ..models.{name.lower()} import {name.capitalize()}
from ..repositories.{name.lower()}_repository import {name.capitalize()}Repository
from ..services.{name.lower()}_service import {name.capitalize()}Service


# Pydantic models for API
class {name.capitalize()}Base(BaseModel):
    name: str
    description: Optional[str] = None


class {name.capitalize()}Create({name.capitalize()}Base):
    pass


class {name.capitalize()}Update({name.capitalize()}Base):
    pass


class {name.capitalize()}Read({name.capitalize()}Base):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Create router
router = APIRouter(
    prefix="/{name.lower()}s",
    tags=["{name.capitalize()}s"],
)


# Dependency to get service
def get_{name.lower()}_service(session=Depends(get_db_session)):
    repository = {name.capitalize()}Repository(session)
    return {name.capitalize()}Service(repository)


@router.get("/", response_model=List[{name.capitalize()}Read])
async def list_{name.lower()}s(
    limit: int = 100,
    offset: int = 0,
    service: {name.capitalize()}Service = Depends(get_{name.lower()}_service)
):
    \"\"\"
    List all {name.lower()}s
    \"\"\"
    result = await service.list(limit=limit, offset=offset)
    
    if result.is_failure():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result.error)
        )
    
    return result.value


@router.get("/{{id}}", response_model={name.capitalize()}Read)
async def get_{name.lower()}(
    id: int,
    service: {name.capitalize()}Service = Depends(get_{name.lower()}_service)
):
    \"\"\"
    Get a {name.lower()} by ID
    \"\"\"
    result = await service.get_by_id(id)
    
    if result.is_failure():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result.error)
        )
    
    if not result.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{name.capitalize()} with ID {{id}} not found"
        )
    
    return result.value


@router.post("/", response_model={name.capitalize()}Read, status_code=status.HTTP_201_CREATED)
async def create_{name.lower()}(
    data: {name.capitalize()}Create,
    service: {name.capitalize()}Service = Depends(get_{name.lower()}_service)
):
    \"\"\"
    Create a new {name.lower()}
    \"\"\"
    # Create model instance
    item = {name.capitalize()}(
        name=data.name,
        description=data.description
    )
    
    result = await service.create(item)
    
    if result.is_failure():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result.error)
        )
    
    return result.value


@router.put("/{{id}}", response_model={name.capitalize()}Read)
async def update_{name.lower()}(
    id: int,
    data: {name.capitalize()}Update,
    service: {name.capitalize()}Service = Depends(get_{name.lower()}_service)
):
    \"\"\"
    Update a {name.lower()} by ID
    \"\"\"
    # Get existing item
    get_result = await service.get_by_id(id)
    
    if get_result.is_failure():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(get_result.error)
        )
    
    if not get_result.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{name.capitalize()} with ID {{id}} not found"
        )
    
    # Update fields
    item = get_result.value
    item.name = data.name
    item.description = data.description
    
    # Save changes
    result = await service.update(item)
    
    if result.is_failure():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result.error)
        )
    
    return result.value


@router.delete("/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{name.lower()}(
    id: int,
    service: {name.capitalize()}Service = Depends(get_{name.lower()}_service)
):
    \"\"\"
    Delete a {name.lower()} by ID
    \"\"\"
    result = await service.delete(id)
    
    if result.is_failure():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(result.error)
        )
    
    if not result.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{name.capitalize()} with ID {{id}} not found"
        )
"""
        create_file(os.path.join(module_dir, "api", f"{name.lower()}_api.py"), api_content)


def create_file(path: str, content: str) -> None:
    """
    Create a file with the given content.
    
    Args:
        path: Path to the file
        content: Content to write to the file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Write content to file
    with open(path, "w") as f:
        f.write(content)