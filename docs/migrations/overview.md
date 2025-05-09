# Schema Migration System

The uno framework includes a robust schema migration system for managing database schema changes in a versioned, repeatable way.

## Overview

The migration system allows you to:

- Define database schema changes as versioned migrations
- Apply migrations to update your database schema
- Revert migrations when needed
- Track which migrations have been applied
- Manage dependencies between migrations
- Create migrations from templates for consistency
- Securely execute SQL with parameterized queries
- Integrate with uno's dependency injection system

Migrations can be defined using SQL or Python, providing flexibility for both simple and complex schema changes.

## Key Concepts

### Migrations

A migration represents a single, atomic change to your database schema. Each migration has:

- A unique identifier
- A human-readable name
- Up and down operations (for applying and reverting the change)
- Optional dependencies on other migrations
- Optional tags for categorization

### Migration Providers

Providers are responsible for discovering and loading migrations from different sources:

- **FileMigrationProvider**: Loads migrations from individual files
- **DirectoryMigrationProvider**: Loads migrations from directories
- **ModuleMigrationProvider**: Loads migrations from Python modules

### Migration Tracker

The tracker keeps track of which migrations have been applied to the database:

- **DatabaseMigrationTracker**: Stores migration status in a database table
- **FileMigrationTracker**: Stores migration status in a JSON file

### Migrator

The migrator is responsible for applying and reverting migrations in the correct order, handling dependencies and transactions.

### Migration Templates

The system includes templates for creating consistent migrations:

- SQL migration templates with clear UP/DOWN sections
- Python migration templates with function-based and class-based options
- Custom templates can be provided for specialized migrations

### Security Features

The migration system includes important security features:

- **Parameterized Queries**: All SQL execution uses parameterized queries to prevent SQL injection vulnerabilities
- **Transaction Management**: Migrations are executed within transactions to ensure atomicity
- **Error Handling**: Comprehensive error handling with detailed logging and context information

### Dependency Injection Integration

The migration system integrates with uno's dependency injection framework:

- **MigrationServiceProvider**: Provides migration-related services to the DI container
- **Scoped Configuration**: Migration configuration can be scoped to different environments
- **Service Resolution**: Migration dependencies can be resolved from the DI container

## Creating Migrations

### SQL Migrations

SQL migrations are simple text files with SQL statements for applying and reverting changes:

```sql
-- Create users table
CREATE TABLE users (```

id SERIAL PRIMARY KEY,
username VARCHAR(255) NOT NULL UNIQUE,
email VARCHAR(255) NOT NULL UNIQUE,
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
```
);

-- DOWN

DROP TABLE IF EXISTS users;
```

The `-- DOWN` marker separates the "up" SQL (for applying the migration) from the "down" SQL (for reverting it).

### Python Migrations

Python migrations are Python modules with functions for applying and reverting changes:

```python
async def up(context):```

"""Apply the migration."""
await context.execute_sql('''```

CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    theme VARCHAR(50) DEFAULT 'light',
    notifications_enabled BOOLEAN DEFAULT TRUE
);
```
''')
```

async def down(context):```

"""Revert the migration."""
await context.execute_sql('DROP TABLE IF EXISTS user_settings;')
```
```

## Running Migrations

### Programmatically

```python
from uno.core.migrations.migrator import migrate, MigrationConfig, MigrationDirection
from uno.core.migrations.providers import register_provider, DirectoryMigrationProvider

# Configure migration system
config = MigrationConfig(```

schema_name="public",
migration_table="uno_migrations",
migration_paths=["/path/to/migrations"]
```
)

# Register migration provider
provider = DirectoryMigrationProvider(["/path/to/migrations"])
register_provider("my_app", provider)

# Apply migrations
count, applied = await migrate(```

connection=database_connection,
config=config,
direction=MigrationDirection.UP
```
)
```

### Using the CLI

The migration system includes a command-line interface for managing migrations, supporting both the Core Migration System and Alembic:

#### Core Migration Commands

```bash
# Apply all pending migrations
python -m src.scripts.migrations migrate --database-url "postgresql://user:pass@localhost/mydb" --directory ./migrations

# Revert the last migration
python -m src.scripts.migrations rollback --database-url "postgresql://user:pass@localhost/mydb" --directory ./migrations

# Create a new migration with a template
python -m src.scripts.migrations create "add users table" --type sql --directory ./migrations

# Create a migration with a custom template
python -m src.scripts.migrations create "add users table" --type sql --template ./my_template.sql --directory ./migrations

# Show migration status
python -m src.scripts.migrations status --database-url "postgresql://user:pass@localhost/mydb" --directory ./migrations

# Get detailed information about migrations
python -m src.scripts.migrations info --database-url "postgresql://user:pass@localhost/mydb" --directory ./migrations
```

#### Legacy Alembic Commands

```bash
# Initialize Alembic migration environment
python -m src.scripts.migrations alembic:init

# Generate a new Alembic migration
python -m src.scripts.migrations alembic:generate "add users table"

# Upgrade database to the latest revision
python -m src.scripts.migrations alembic:upgrade

# Downgrade database to a specific revision
python -m src.scripts.migrations alembic:downgrade base

# Show migration history
python -m src.scripts.migrations alembic:history
```

## Migration Naming and Organization

### Naming Conventions

Migration files should follow a naming convention for easy sorting and identification:

- SQL migrations: `<timestamp>_<name>.sql`
- Python migrations: `<timestamp>_<name>.py`

Examples:
- `1616721123_create_users_table.sql`
- `1616723456_add_user_settings.py`

### Directory Structure

It's recommended to organize migrations into directories by module or feature:

```
migrations/
├── auth/
│   ├── 1616721123_create_users_table.sql
│   └── 1616723456_add_user_settings.py
├── content/
│   ├── 1616725789_create_posts_table.sql
│   └── 1616728901_add_categories.sql
└── core/```

└── 1616720000_initial_schema.sql
```
```

## Best Practices

1. **Make migrations atomic**: Each migration should represent a single, coherent change
2. **Always include down migrations**: Ensure that every migration can be reverted
3. **Test migrations**: Test both applying and reverting migrations
4. **Use transactions**: Ensure migrations are wrapped in transactions when possible
5. **Document complex migrations**: Add comments explaining complex schema changes
6. **Handle data migrations carefully**: Be cautious when migrating existing data
7. **Consider dependencies**: Specify dependencies between migrations when necessary
8. **Use parameterized queries**: Always use parameter binding for dynamic values to prevent SQL injection
9. **Follow naming conventions**: Use consistent naming patterns for migrations
10. **Prefer templates**: Use the provided templates for consistent migration structure

## Next Steps

- Learn how to create [SQL migrations](sql_migrations.md)
- Explore [Python migrations](python_migrations.md) for complex changes
- Understand how to integrate migrations with dependency injection
- Use migration CLI tools to manage database schemas

## Security Considerations

The uno migration system is designed with security in mind:

1. **SQL Injection Prevention**: All SQL execution uses parameterized queries to prevent SQL injection vulnerabilities
2. **Secure Parameter Handling**: Parameters are passed separately from SQL statements
3. **Isolated Execution**: Migrations run in isolated transactions
4. **Validation**: Migration checksums ensure the integrity of migration files
5. **Access Control**: Migrations run with the proper database role permissions