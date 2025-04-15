# Python Migrations

Python migrations provide a more flexible way to define complex database schema changes using Python code. This guide explains how to create and work with Python migrations in uno.

## When to Use Python Migrations

Python migrations are ideal for:

- Complex schema changes that are difficult to express in SQL
- Data migrations that require processing or transformation
- Schema changes that need conditional logic
- Migrations that interact with external systems
- Changes that need to be customized for different database engines

## Creating Python Migrations

### Manually

Create a new Python migration file with the following structure:

```python
# Migration: Add user profiles with generated slugs
# Description: Creates user profile table and generates slugs for existing users

from typing import Any
import re


async def up(context: Any) -> None:```

"""Apply the migration."""
# Create user profiles table
await context.execute_sql('''```

CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    slug VARCHAR(255) NOT NULL UNIQUE,
    bio TEXT,
    avatar_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
``````

```
```

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_slug ON user_profiles(slug);
```
''')
``````

```
```

# Generate slugs for existing users and create profile entries
users_result = await context.execute_sql('SELECT id, username FROM users')
users = await users_result.fetchall()
``````

```
```

for user_id, username in users:```

# Generate slug from username
slug = re.sub(r'[^a-z0-9]+', '-', username.lower()).strip('-')
``````

```
```

# Add profile entry
await context.execute_sql('''
    INSERT INTO user_profiles (user_id, slug)
    VALUES ($1, $2)
''', [user_id, slug])
```
```


async def down(context: Any) -> None:```

"""Revert the migration."""
await context.execute_sql('''```

DROP INDEX IF EXISTS idx_user_profiles_slug;
DROP INDEX IF EXISTS idx_user_profiles_user_id;
DROP TABLE IF EXISTS user_profiles;
```
''')
```
```

Save the file with a timestamp-based name: `<timestamp>_<name>.py`

For example: `1616723456_add_user_profiles.py`

### Using the CLI

The migration CLI provides a command to create Python migrations:

```bash
python -m uno.core.migrations.cli create "add user profiles" --type python --directory ./migrations
```

This creates a new migration file with the current timestamp and a template structure.

## Python Migration Format

### Function-based Migrations

The simplest Python migration format uses two functions:

- `up(context)`: Function for applying the migration
- `down(context)`: Function for reverting the migration

Example:

```python
async def up(context):```

"""Apply the migration."""
await context.execute_sql('''```

CREATE TABLE settings (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```
''')
``````

```
```

# Insert default settings
default_settings = [```

("site_name", "My Site"),
("theme", "default"),
("items_per_page", "10")
```
]
``````

```
```

for key, value in default_settings:```

await context.execute_sql(
    "INSERT INTO settings (key, value) VALUES ($1, $2)",
    [key, value]
)
```
```


async def down(context):```

"""Revert the migration."""
await context.execute_sql('DROP TABLE IF EXISTS settings;')
```
```

### Class-based Migrations

For more complex migrations, you can use a class-based approach:

```python
from uno.core.migrations.migration import Migration, MigrationBase, create_migration


class AddUserRolesMigration(Migration):```

"""Migration to add user roles and permissions."""
``````

```
```

def __init__(self):```

base = create_migration(
    name="Add User Roles",
    description="Creates tables for role-based access control",
    dependencies=["1616721123_create_users_table"]
)
super().__init__(base)
```
``````

```
```

async def apply(self, context):```

"""Apply the migration."""
# Create roles table
await context.execute_sql('''
    CREATE TABLE roles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
''')
``````

```
```

# Create user_roles table
await context.execute_sql('''
    CREATE TABLE user_roles (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(user_id, role_id)
    );
    
    CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
    CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
''')
``````

```
```

# Create permissions table
await context.execute_sql('''
    CREATE TABLE permissions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
''')
``````

```
```

# Create role_permissions table
await context.execute_sql('''
    CREATE TABLE role_permissions (
        id SERIAL PRIMARY KEY,
        role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
        permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(role_id, permission_id)
    );
    
    CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
    CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);
''')
``````

```
```

# Insert default roles
await context.execute_sql(
    "INSERT INTO roles (name, description) VALUES ($1, $2)",
    ["admin", "Administrator with full access"]
)
``````

```
```

await context.execute_sql(
    "INSERT INTO roles (name, description) VALUES ($1, $2)",
    ["user", "Regular user with limited access"]
)
```
``````

```
```

async def revert(self, context):```

"""Revert the migration."""
await context.execute_sql('''
    DROP TABLE IF EXISTS role_permissions;
    DROP TABLE IF EXISTS permissions;
    DROP TABLE IF EXISTS user_roles;
    DROP TABLE IF EXISTS roles;
''')
```
``````

```
```

def get_checksum(self):```

"""Calculate a checksum for the migration."""
import hashlib
content = "add_user_roles_migration"
return hashlib.md5(content.encode('utf-8')).hexdigest()
```
```
```

## Migration Context

The migration context provides access to the database connection and other utilities:

### Executing SQL

```python
# Execute a simple SQL statement
await context.execute_sql("CREATE TABLE example (id SERIAL PRIMARY KEY)")

# Execute a parameterized SQL statement
await context.execute_sql(```

"INSERT INTO users (username, email) VALUES ($1, $2)",
["johndoe", "john@example.com"]
```
)

# Execute multiple statements
await context.execute_sql('''```

CREATE TABLE categories (id SERIAL PRIMARY KEY, name VARCHAR(100));
CREATE INDEX idx_categories_name ON categories(name);
```
''')
```

### Transactions

For operations that need to be atomic:

```python
async def up(context):```

async def perform_migration():```

# All operations here will be in a transaction
await context.execute_sql("CREATE TABLE example (...)")
``````

```
```

# Process some data
result = await context.execute_sql("SELECT id FROM users")
users = await result.fetchall()
``````

```
```

for user_id in users:
    await context.execute_sql(
        "INSERT INTO user_settings (user_id) VALUES ($1)",
        [user_id]
    )
```
``````

```
```

# Execute the function in a transaction
await context.execute_transaction(perform_migration)
```
```

## Complex Migration Examples

### Data Migration

```python
async def up(context):```

"""Normalize user email addresses."""
# Get all users
result = await context.execute_sql("SELECT id, email FROM users")
users = await result.fetchall()
``````

```
```

# Update emails to lowercase
for user_id, email in users:```

normalized_email = email.lower().strip()
await context.execute_sql(
    "UPDATE users SET email = $1, updated_at = NOW() WHERE id = $2",
    [normalized_email, user_id]
)
```
```


async def down(context):```

"""Nothing to revert for this migration."""
# This migration can't be reverted since it's a data cleanup
pass
```
```

### Multi-database Support

```python
async def up(context):```

"""Create audit log table with database-specific settings."""
# Detect database type
db_type = await get_database_type(context)
``````

```
```

if db_type == "postgresql":```

await context.execute_sql('''
    CREATE TABLE audit_logs (
        id SERIAL PRIMARY KEY,
        action VARCHAR(100) NOT NULL,
        entity_type VARCHAR(100) NOT NULL,
        entity_id VARCHAR(100) NOT NULL,
        user_id INTEGER REFERENCES users(id),
        changes JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
''')
```
elif db_type == "mysql":```

await context.execute_sql('''
    CREATE TABLE audit_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        action VARCHAR(100) NOT NULL,
        entity_type VARCHAR(100) NOT NULL,
        entity_id VARCHAR(100) NOT NULL,
        user_id INTEGER REFERENCES users(id),
        changes JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')
```
elif db_type == "sqlite":```

await context.execute_sql('''
    CREATE TABLE audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action VARCHAR(100) NOT NULL,
        entity_type VARCHAR(100) NOT NULL,
        entity_id VARCHAR(100) NOT NULL,
        user_id INTEGER REFERENCES users(id),
        changes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
''')
```
``````

```
```

# Create common indexes
await context.execute_sql('''```

CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
```
''')
```


async def get_database_type(context):```

"""Detect the database type from the connection."""
# Implementation would depend on your connection object
conn = context.connection
if hasattr(conn, "dialect") and hasattr(conn.dialect, "name"):```

return conn.dialect.name
```
elif "postgresql" in str(conn.__class__):```

return "postgresql"
```
elif "mysql" in str(conn.__class__):```

return "mysql"
```
elif "sqlite" in str(conn.__class__):```

return "sqlite"
```
else:```

return "unknown"
```
```
```

### Generating Complex Schema

```python
async def up(context):```

"""Generate a tagging system with dynamic tag types."""
tag_types = ["product", "article", "user", "category"]
``````

```
```

# Create tags table
await context.execute_sql('''```

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
``````

```
```

CREATE INDEX idx_tags_slug ON tags(slug);
CREATE INDEX idx_tags_type ON tags(type);
```
''')
``````

```
```

# Create a taggable junction table for each tag type
for tag_type in tag_types:```

table_name = f"{tag_type}_tags"
entity_id_field = f"{tag_type}_id"
``````

```
```

await context.execute_sql(f'''
    CREATE TABLE {table_name} (
        id SERIAL PRIMARY KEY,
        {entity_id_field} INTEGER NOT NULL,
        tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE({entity_id_field}, tag_id)
    );
    
    CREATE INDEX idx_{table_name}_{entity_id_field} ON {table_name}({entity_id_field});
    CREATE INDEX idx_{table_name}_tag_id ON {table_name}(tag_id);
''')
```
```


async def down(context):```

"""Remove the tagging system."""
tag_types = ["product", "article", "user", "category"]
``````

```
```

# Drop junction tables first
for tag_type in tag_types:```

table_name = f"{tag_type}_tags"
await context.execute_sql(f"DROP TABLE IF EXISTS {table_name}")
```
``````

```
```

# Then drop the tags table
await context.execute_sql("DROP TABLE IF EXISTS tags")
```
```

## Python Migration Best Practices

1. **Keep SQL in SQL migrations when possible**: Use Python migrations only when you need the additional flexibility
2. **Handle errors gracefully**: Add error handling for operations that might fail
3. **Use transactions**: Wrap related operations in transactions for atomicity
4. **Add logging**: Log important steps for debugging
5. **Test both up and down migrations**: Ensure that migrations can be applied and reverted correctly
6. **Document complex logic**: Add comments explaining complex operations
7. **Minimize dependencies**: Keep migrations as self-contained as possible

## Common Patterns

### Logging During Migration

```python
async def up(context):```

logger = context.logger
``````

```
```

logger.info("Starting migration: Add user profiles")
``````

```
```

logger.info("Creating user_profiles table")
await context.execute_sql("CREATE TABLE user_profiles (...)")
``````

```
```

logger.info("Migrating existing user data")
# Migration logic here...
``````

```
```

logger.info("Migration completed successfully")
```
```

### Conditional Schema Changes

```python
async def up(context):```

# Check if the column already exists
result = await context.execute_sql("""```

SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'status'
```
""")
``````

```
```

if not await result.fetchone():```

# Column doesn't exist, add it
await context.execute_sql("""
    ALTER TABLE users 
    ADD COLUMN status VARCHAR(50) DEFAULT 'active' NOT NULL
""")
```
```
```

### Batched Data Processing

```python
async def up(context):```

# Process users in batches to avoid memory issues
batch_size = 1000
offset = 0
``````

```
```

while True:```

result = await context.execute_sql(
    "SELECT id, email FROM users ORDER BY id LIMIT $1 OFFSET $2",
    [batch_size, offset]
)
```
    ```

users = await result.fetchall()
if not users:
    break
```
    ```

for user_id, email in users:
    # Process each user
    normalized_email = email.lower().strip()
    await context.execute_sql(
        "UPDATE users SET email = $1 WHERE id = $2",
        [normalized_email, user_id]
    )
```
    ```

offset += batch_size
```
```
```

## Conclusion

Python migrations offer powerful capabilities for handling complex schema changes and data migrations. By using Python code, you can implement migrations that would be difficult or impossible with SQL alone, while still maintaining the benefits of versioned, repeatable database changes.