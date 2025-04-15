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
uno is a brand new library, any "legacy" code was simply defined as protoypes to define capabilities, it does not have to be preserved. No developers are currently using the existing code base.

## Proposals for improvements
The PROPOSALS folder in the root is where proposals and plans for enhancements and refactoring are documented.
PROPOSALS/CODE_STANDARDIZATION_PROGRESS.md is an excellent example.

## Dependency Injection System

uno implements a dependency injection system using the `inject` library. Key components include:

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
8. Create unit tests and verify they are working
9. Create detailed documentation for developers, admins, users, etc..., as appropriate.

For testing with dependencies:
1. Use `TestingContainer` to configure test-specific dependencies
2. Use mock factories (`MockRepository`, `MockConfig`, etc.) for common mocks
3. Use `configure_test_container()` for quick test setup
4. Restore the original container configuration after tests
5. Use pytest fixtures to manage container lifecycle

## Key Dependencies

python 3.13.0+
postgresql 16
webawesome
lit
pydantic 2 # Do not use pydantic versions  < 2

## Prefer modern web-component based front end ui

When building front end ui components, use webawesome and lit to create the ui.
load lit from cdn, not using node

## Prefer modern open-source libraries

When building uno, also review the best modern, well supported, mature python libraries over building functionality from scratch.

## Prefer internal resources

Use the centralized database access utilities for database connections and sessions
Use the utilities defined within the library whenever possible.

## Prefer decimal.Decimal over float

When needing to store numerical data that is not a whole number, use decimal.Decimal not float.

## Docker-First Approach

This project uses a Docker-first approach for all database interactions. We never use local PostgreSQL installations for development, testing, or deployment. See DOCKER_FIRST.md for details.

## Commands
- Docker setup: `./scripts/setup_docker.sh` or `hatch run dev:docker-setup` 
- Test environment: `./scripts/setup_test_env.sh`
- Rebuild Docker: `./scripts/rebuild_docker.sh`
- Run app: `hatch run dev:app` (sets up Docker and runs the app)
- Test with Docker: `hatch run test:all` (sets up Docker and runs tests)
- Run integration tests: `hatch run test:integration`
- Run transaction tests: `hatch run test:test tests/integration/test_transaction.py -v`
- Run vector tests: `hatch run test:integration-vector`
- Run benchmarks: `./tests/integration/run_benchmarks.py`
- Individual tests: `hatch run test:test tests/path/to/test_file.py::TestClass::test_method`
- Test (verbose): `hatch run test:testvv`
- Type check: `hatch run types:check`
- Event Store: `python src/scripts/eventstore.py create`

## Script Documentation

### Docker Scripts
- `scripts/docker/start.sh`: Starts Docker containers for development with options for verbose, clean, and detached mode
- `scripts/docker/stop.sh`: Stops Docker containers
- `scripts/setup_docker.sh`: Legacy script that redirects to start.sh
- `scripts/rebuild_docker.sh`: Rebuilds Docker containers
- `scripts/docker/test/setup.sh`: Sets up test Docker environment

### Database Scripts
- `src/scripts/createdb.py`: Creates database with proper roles, schemas, and extensions
- `src/scripts/dropdb.py`: Drops database
- `src/scripts/createsuperuser.py`: Creates superuser account
- `src/scripts/db_init.py`: Initializes database structures
- `src/scripts/postgres_extensions.py`: Sets up PostgreSQL extensions
- `scripts/install_pgvector.sh`: Installs pgvector extension

### Setup and Environment Scripts
- `src/scripts/setup_environment.py`: Sets up development environment
- `scripts/setup_test_env.sh`: Sets up test environment
- `scripts/vector/setup_vector_search.sh`: Sets up vector search functionality
- `src/scripts/eventstore.py`: Creates/manages event store

### Testing and Validation Scripts
- `src/scripts/validate_protocols.py`: Validates protocol implementations
- `src/scripts/validate_errors.py`: Validates error handling
- `src/scripts/validate_reports.py`: Validates report generation
- `src/scripts/validate_workflows.py`: Validates workflow definitions
- `src/scripts/test_merge_function.py`: Tests merge function
- `tests/integration/run_benchmarks.py`: Runs integration test benchmarks and generates reports
- `benchmarks/dashboard/run_dashboard.sh`: Launches the benchmark visualization dashboard

### CI/CD Scripts
- `scripts/ci/build.sh`: Builds project for CI
- `scripts/ci/test.sh`: Runs tests for CI
- `scripts/ci/deploy.sh`: Deploys project
- `scripts/ci/verify.sh`: Verifies deployment
- `scripts/dev/lint.sh`: Runs linting

### Development Tools
- `scripts/launch_modeler.sh`: Launches visual data modeler
- `src/scripts/generate_docs.py`: Generates documentation
- `src/scripts/attributes_cli.py`: CLI for managing attributes
- `src/scripts/values_cli.py`: CLI for managing values
- `src/scripts/reports_cli.py`: CLI for managing reports

### Issues Identified
- Some scripts have dependency issues (e.g., generate_docs.py imports missing modules)
- Legacy scripts (setup_docker.sh) should be deprecated in favor of new ones
- Documentation for some scripts is minimal or missing
- Some scripts require specific environment setup to run successfully

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