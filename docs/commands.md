# Command Reference

uno provides a set of command-line tools to help you manage your application. These commands are available through either direct Python script execution or as part of the package's command line interface.

## Database Management

### Create Database

Creates the database with all roles, schemas, extensions, tables, and initial data.

```bash
# Using Python script
python src/scripts/createdb.py

# Using environment variables for configuration
DB_HOST=localhost DB_PORT=5432 DB_USER=postgres DB_PASSWORD=postgres python src/scripts/createdb.py
```

### Drop Database

Drops the database and all associated roles.

```bash
python src/scripts/dropdb.py
```

### Create Superuser

Creates a superuser account in the database.

```bash
python src/scripts/createsuperuser.py
```

### Create Query Paths

Creates predefined query paths for filter management.

```bash
python src/scripts/createquerypaths.py
```

## Migration Commands

uno provides a complete set of migration commands powered by Alembic. See the Migrations documentation for detailed usage.

### Run Migrations

Runs database migrations to update the schema.

```bash
python src/scripts/migrations.py upgrade head
```

### Generate Migration

Generates a new migration based on model changes.

```bash
python src/scripts/migrations.py revision --autogenerate -m "Description of changes"
```

### Migration Status

Shows the current migration status.

```bash
python src/scripts/migrations.py current
```

### Migration History

Shows migration history.

```bash
python src/scripts/migrations.py history
```

## Development Commands

### Run Development Server

Runs the development server with auto-reload.

```bash
# Start the FastAPI development server
uvicorn main:app --reload

# With a specific host and port
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Testing Commands

### Run Tests

Run tests using pytest.

```bash
# Run all tests
ENV=test pytest

# Run with verbose output
ENV=test pytest -vv --capture=tee-sys --show-capture=all

# Run a specific test file
ENV=test pytest tests/path/to/test_file.py

# Run a specific test class
ENV=test pytest tests/path/to/test_file.py::TestClass

# Run a specific test method
ENV=test pytest tests/path/to/test_file.py::TestClass::test_method
```

### Type Checking

Run mypy for type checking.

```bash
mypy --install-types --non-interactive src/uno tests
```

### Coverage

Run tests with coverage measurement.

```bash
# Run tests with coverage
ENV=test pytest --cov=src

# Generate a coverage report
ENV=test pytest --cov=src --cov-report=html
```

## Documentation Commands

### Build Documentation

Builds the documentation site using MkDocs.

```bash
mkdocs build
```

### Serve Documentation

Serves the documentation site locally for development.

```bash
# Default port (8000)
mkdocs serve

# Custom port
mkdocs serve -a 127.0.0.1:8001
```

## Docker Commands

### Build Docker Image

Builds the PostgreSQL Docker image with uno extensions.

```bash
cd docker
docker build -t pg16_uno .
```

### Start Docker Container

Starts the PostgreSQL container using docker-compose.

```bash
cd docker
docker-compose up
```

### Stop Docker Container

Stops and removes the PostgreSQL container.

```bash
cd docker
docker-compose down
```

## Environment Variables

uno respects the following environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `DB_USER` | Database user | postgres |
| `DB_PASSWORD` | Database password | postgres |
| `DB_NAME` | Database name | uno |
| `DB_SCHEMA` | Database schema | public |
| `ENV` | Environment (dev, test, prod) | dev |
| `LOG_LEVEL` | Logging level | INFO |