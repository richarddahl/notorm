# Database Migrations

Uno provides a robust database migration system powered by Alembic that allows you to:

1. Track schema changes over time
2. Generate migrations automatically or manually
3. Upgrade and downgrade database schemas
4. Maintain compatibility between application versions

This migration system is designed to work seamlessly with Uno's custom SQL emitters, providing the best of both worlds: versioned schema management with Alembic and PostgreSQL-specific features through Uno's emitter system.

## How Migrations Work

When you create a database with `createdb`, Uno performs the following steps:

1. Create database roles, schemas, and extensions using SQL emitters
2. Set up tables, privileges, and custom PostgreSQL objects
3. Initialize the Alembic migration system with a baseline "stamp"

From this point forward, schema changes should be managed through the migration system rather than by modifying the database directly.

## Role-Based Security

Uno uses a strict security model with different database roles:

- `{db_name}_login`: Role with connect permission but limited privileges
- `{db_name}_admin`: Role with permissions to perform DDL operations
- `{db_name}_writer`: Role for data modifications
- `{db_name}_reader`: Role for read-only operations

The migration system connects using the `{db_name}_login` role and then uses `SET ROLE {db_name}_admin` to elevate privileges for schema changes. This approach maintains security while allowing migrations to work properly.

## Creating Migrations

To create a new migration after changing your models:

```bash
hatch run migrate-generate "Description of your change"
```

This command will:
1. Scan your models for changes compared to the database
2. Generate a new migration script with upgrade and downgrade functions
3. Place the script in `src/uno/migrations/versions/`

The generated migration will include:
- Table creation/modification/deletion
- Column changes
- Index and constraint modifications

## Applying Migrations

To apply all pending migrations to the database:

```bash
hatch run migrate-up
```

To upgrade to a specific version:

```bash
hatch run migrate-up your_revision_id
```

## Rolling Back Migrations

To downgrade the database to a previous version:

```bash
hatch run migrate-down previous_revision_id
```

## Checking Migration Status

To see the current migration version:

```bash
hatch run migrate-current
```

To view migration history:

```bash
hatch run migrate-history
```

To list all available revisions:

```bash
hatch run migrate-revisions
```

## Writing Custom Migrations

While Alembic can auto-generate most migrations, sometimes you'll want to add custom SQL or operations to a migration. To do this:

1. Generate a migration normally
2. Edit the generated file in `src/uno/migrations/versions/`
3. Add your custom operations using `op.execute()` with SQLAlchemy's text() function

Example with custom SQL:

```python
def upgrade():
    # Auto-generated operations
    op.create_table(...)
    
    # Custom operations with SQLAlchemy text() function
    from sqlalchemy import text
    op.execute(text("""
    CREATE OR REPLACE FUNCTION my_custom_function()
    RETURNS VOID
    LANGUAGE plpgsql
    AS $$
    BEGIN
        -- function logic
    END;
    $$;
    """))

def downgrade():
    # Cleanup custom operations
    from sqlalchemy import text
    op.execute(text("DROP FUNCTION IF EXISTS my_custom_function();"))
    
    # Auto-generated downgrades
    op.drop_table(...)
```

## Integration with SQL Emitters

You can use Uno's SQL emitters directly in custom migrations:

```python
from uno.sql.emitters.table import InsertMetaRecordFunction
from uno.settings import uno_settings
from sqlalchemy import text

def upgrade():
    # Set proper role for admin operations
    from uno.settings import uno_settings
    admin_role = f"{uno_settings.DB_NAME}_admin"
    op.execute(text(f"SET ROLE {admin_role};"))
    
    # Table operations
    op.create_table(...)
    
    # Use SQL emitter
    emitter = InsertMetaRecordFunction(config=uno_settings)
    statements = emitter.generate_sql()
    for stmt in statements:
        op.execute(text(stmt.sql))
```

## Best Practices

1. **Generate migrations for schema changes** - Always use Alembic for changes to tables, columns, indexes, etc.

2. **Use emitters for PostgreSQL-specific features** - Use SQL emitters for complex PostgreSQL features that Alembic doesn't handle well

3. **Always use the text() function** - When executing raw SQL with Alembic's op.execute(), always wrap SQL in SQLAlchemy's text() function

4. **Test migrations** - Always test upgrades and downgrades in a development environment before applying to production

5. **Version control migrations** - Always commit migration scripts to your version control system

6. **Be careful with data migrations** - When migrating data, consider performance and transactions to avoid data loss

## Troubleshooting

### "Not an executable object" Error

This usually means you've passed a raw SQL string without using SQLAlchemy's text() function. Always use:

```python
from sqlalchemy import text
op.execute(text("YOUR SQL HERE"))
```

### "Can't locate revision identified by..."

This typically means the revision ID you specified doesn't exist. Use `hatch run migrate-revisions` to see available revisions.

### "Multiple head revisions"

If you have multiple head revisions (parallel migration branches), you need to merge them:

```bash
hatch run python src/scripts/migrations.py merge_heads "Merge migration branches"
```

### Connection or Permission Errors

If you encounter permission errors, check that:

1. The migrations system is using the login role to connect (this is automatic)
2. The `SET ROLE` statement is being executed before operations
3. The admin role has proper permissions to perform the operations

### Migration fails to apply

If a migration fails during application:
1. Check the error message for details
2. Fix any issues in your migration script
3. Retry the migration