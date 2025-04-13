# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

uno (uno is not an orm), is a python library that integrates sqlaclhemy, pydantic, and fastapi with postgres 16.
It is designed to offload as much as can be to the postgres database using custom sql functions and triggers.
It uses apache age to duplicate the postgres relational table data into a knowledge graph used for:

- Filtering the database
- User-defined complex queries stored in the db and used for business logic.
- Retreival Augmented Generation

uno defines a number of classes.  The primary classes are:
UnoObj - Provides an interface to the data for business logic processing.
UnoModel - A customized declarative base (sqlalchemy orm) for the table structure.
UnoSchema - A pydantic model for passing the appropriate data between the UnoObj and the database and the UnoObject and the fast api endpoints.
UnoDB - A custom class used to communicate with the database using psycopg3 for synchronous data base operations and asyncpg for asynchronous data base operations.
UnoEndpoint - A custom class used to establish fastapi endpoints.
SQLEmitter - A custom class used to build and emit custom sql statements, primarily for issuing DDL to create types, functions, and triggers.

uno uses pydantic base settings when possible for configuration, variables stored in .env file for production, .env_dev for development, and .env_test for testing.

uno does not provide any authentication mechanism.  It is inteded to be used with an external authentication service.
uno does use jwt for token validation and authorization.
uno allows definition of postgres row level security using postgres session variables to control access to database records.

## Dependency Injection System

Uno implements a dependency injection system using the `inject` library. Key components include:

- **Interfaces**: Protocol classes in `uno.dependencies.interfaces` like `UnoRepositoryProtocol` and `UnoServiceProtocol`
- **Container**: Configured in `uno.dependencies.container`, provides centralized dependency management
- **Base Implementations**: `UnoRepository`, `UnoService`, and `CrudService` for common patterns
- **FastAPI Integration**: Utilities in `uno.dependencies.fastapi` to integrate with FastAPI's dependency system

When implementing new features:
1. Define interfaces using Protocol classes
2. Implement concrete classes that fulfill those protocols
3. Use constructor injection to receive dependencies
4. Register dependencies in the container or use FastAPI's Depends()
5. Use `get_db_session()` or `get_scoped_db_session()` for database access
6. Prefer `UnoRepository` for data access patterns
7. Use `inject_dependency()` for non-session dependencies

For testing with dependencies:
1. Use `TestingContainer` to configure test-specific dependencies
2. Use mock factories (`MockRepository`, `MockConfig`, etc.) for common mocks
3. Use `configure_test_container()` for quick test setup
4. Restore the original container configuration after tests
5. Use pytest fixtures to manage container lifecycle

## Key Dependencies

python 3.13.0+
postgresql 16

## Prefer modern open-source libraries

When building uno, also review the best modern, well supported, mature python libraries over building functionality from scratch.

## Docker-First Approach
This project uses a Docker-first approach for all database interactions. We never use local PostgreSQL installations for development, testing, or deployment. See DOCKER_FIRST.md for details.

## Commands
- Docker setup: `./scripts/setup_docker.sh` or `hatch run dev:docker-setup` 
- Test environment: `./scripts/setup_test_env.sh`
- Rebuild Docker: `./scripts/rebuild_docker.sh`
- Run app: `hatch run dev:app` (sets up Docker and runs the app)
- Test with Docker: `hatch run test:all` (sets up Docker and runs tests)
- Individual tests: `hatch run test:test tests/path/to/test_file.py::TestClass::test_method`
- Test (verbose): `hatch run test:testvv`
- Type check: `hatch run types:check`
- Event Store: `python src/scripts/eventstore.py create`

## Code Style Guidelines

- FOLLOW PEP8, PEP257, and PEP484 guidelines
- Separate concerns and use appropriate patterns
- Prefer composition over inheritance
- Use type hints for all functions and variables
- Use dependency injection for when practical (generally is)
  - Use the `uno.dependencies` module for dependency injection
  - Choose between UnoObj pattern (simple domains) and DI pattern (complex domains)
  - Prefer constructor injection over service location
  - Use Protocol classes for dependency interfaces
  - Use FastAPI's Depends() with our DI utilities (`get_db_session`, `get_repository`, etc.)
- Prefer Protocol over Class when possible
- Python 3.12+ with type hints throughout
- Imports: group standard lib, third-party, local imports
- Naming: PascalCase for classes, snake_case for functions/variables
- Indentation: 4 spaces, ~88-100 char line length
- Documentation: comprehensive docstrings with Args/Returns/Raises
- Error handling: use custom UnoError with context and error codes
- Testing: pytest with fixtures, TestClass and test_method naming
- Project structure: modular with separation of concerns
- Boolean tests: Always use if var is None rather than if not var