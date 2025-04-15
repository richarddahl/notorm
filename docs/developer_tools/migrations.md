# Migration Assistance Utilities

The Migration Assistance Utilities provide tools for working with database schema migrations and codebase transformations. These utilities help with detecting schema differences, generating migration scripts, applying migrations safely, and migrating code patterns.

## Database Schema Migrations

### Comparing Schemas

The schema diff tool allows you to compare your SQLAlchemy models to your database schema to detect differences:

```bash
uno-dev migrations diff-schema --connection postgresql://user:password@localhost/dbname --models your_project.models
```

This will show you a summary of the differences between your models and the database schema, including:

- Added tables (tables in your models that don't exist in the database)
- Removed tables (tables in the database that don't exist in your models)
- Modified tables (tables with different columns or column types)
- Added, removed, or modified columns
- Added or removed indexes and constraints

You can output the results in different formats:

```bash
# Output in markdown format
uno-dev migrations diff-schema --connection postgresql://user:password@localhost/dbname --models your_project.models --format markdown

# Save the output to a file
uno-dev migrations diff-schema --connection postgresql://user:password@localhost/dbname --models your_project.models --output diff.md
```

### Generating Migration Scripts

Once you've identified schema differences, you can generate a migration script to apply the changes:

```bash
uno-dev migrations generate-migration \
  --connection postgresql://user:password@localhost/dbname \
  --models your_project.models \
  --output-dir migrations \
  --message "Add user table"
```

This will create a new migration script in the specified directory. The script will include:

- Upgrade operations to apply the changes (creating tables, adding columns, etc.)
- Downgrade operations to revert the changes
- Metadata such as revision ID, message, and creation date

You can generate scripts in different formats:

```bash
# Generate a SQL migration script
uno-dev migrations generate-migration \
  --connection postgresql://user:password@localhost/dbname \
  --models your_project.models \
  --output-dir migrations \
  --message "Add user table" \
  --format sql
```

Use the `--dry-run` flag to preview the migration script without creating it:

```bash
uno-dev migrations generate-migration \
  --connection postgresql://user:password@localhost/dbname \
  --models your_project.models \
  --output-dir migrations \
  --message "Add user table" \
  --dry-run
```

### Applying Migrations

To apply a migration script to your database:

```bash
uno-dev migrations apply-migration \
  path/to/migration_script.py \
  --connection postgresql://user:password@localhost/dbname
```

By default, a backup of the database is created before applying the migration. You can disable this with `--no-backup`:

```bash
uno-dev migrations apply-migration \
  path/to/migration_script.py \
  --connection postgresql://user:password@localhost/dbname \
  --no-backup
```

Use the `--dry-run` flag to preview the migration without applying it:

```bash
uno-dev migrations apply-migration \
  path/to/migration_script.py \
  --connection postgresql://user:password@localhost/dbname \
  --dry-run
```

### Rolling Back Migrations

If you need to roll back a migration:

```bash
uno-dev migrations rollback-migration \
  path/to/migration_script.py \
  --connection postgresql://user:password@localhost/dbname
```

Similar to applying migrations, you can use `--dry-run` and `--no-backup` options.

## Codebase Migrations

### Analyzing Code

The code analyzer helps identify patterns in your code that might need migration:

```bash
uno-dev migrations analyze-code path/to/your/code
```

This will search for patterns such as:

- Deprecated APIs and imports
- Python version compatibility issues
- Missing type annotations
- Improper error handling
- Service locator patterns (which could be replaced with dependency injection)
- Improper async patterns

You can output the results in different formats:

```bash
# Output in markdown format
uno-dev migrations analyze-code path/to/your/code --format markdown

# Output in JSON format
uno-dev migrations analyze-code path/to/your/code --format json

# Save the output to a file
uno-dev migrations analyze-code path/to/your/code --output analysis.md
```

You can also specify particular patterns to check for:

```bash
uno-dev migrations analyze-code path/to/your/code --pattern deprecated_apis --pattern async_patterns
```

### Transforming Code

After analyzing your code, you can apply transformations to fix the identified issues:

```bash
uno-dev migrations transform-code path/to/your/code
```

By default, this runs in dry-run mode, showing you what changes would be made without actually modifying files. To apply the changes:

```bash
uno-dev migrations transform-code path/to/your/code --no-dry-run
```

You can specify particular transformations to apply:

```bash
uno-dev migrations transform-code path/to/your/code --transform deprecated_apis --transform type_annotations
```

And view the changes in different formats:

```bash
# Show diffs of the changes
uno-dev migrations transform-code path/to/your/code --format diff

# Output results in JSON format
uno-dev migrations transform-code path/to/your/code --format json
```

### Backups and Restoration

Before making changes to your code, it's important to create backups. The transformation tools automatically create backups when run with `--no-dry-run`, but you can also restore from backups if needed:

```bash
uno-dev migrations restore-backup path/to/backups
```

Use the `--force` flag to overwrite existing files:

```bash
uno-dev migrations restore-backup path/to/backups --force
```

Or specify a different target directory:

```bash
uno-dev migrations restore-backup path/to/backups --target path/to/restore
```

## Integration with CI/CD

The migration utilities can be integrated with your CI/CD pipeline to automate schema checks and migrations. For example, you can add a step to your CI pipeline to check for schema differences:

```yaml
# In your GitHub Actions workflow
- name: Check schema differences
  run: |```

uno-dev migrations diff-schema \
  --connection ${{ secrets.DATABASE_URL }} \
  --models your_project.models \
  --output schema_diff.md
```
```

Or generate and apply migrations automatically:

```yaml
# In your deployment workflow
- name: Apply database migrations
  run: |```

# Generate migration
uno-dev migrations generate-migration \
  --connection ${{ secrets.DATABASE_URL }} \
  --models your_project.models \
  --output-dir migrations \
  --message "Automatic migration"
``````

```
```

# Apply the most recent migration
MIGRATION=$(ls -t migrations/*.py | head -1)
uno-dev migrations apply-migration \
  $MIGRATION \
  --connection ${{ secrets.DATABASE_URL }}
```
```

## Best Practices

1. **Always use `--dry-run` first**: Before applying migrations or code transformations, use the `--dry-run` flag to preview the changes.

2. **Create backups**: While the tools automatically create backups, it's always good practice to have additional backups of your database and code.

3. **Test migrations in development**: Always test migrations in a development environment before applying them to production.

4. **Use version control**: Keep your migration scripts in version control to track database schema changes over time.

5. **Code reviews**: Have team members review generated migration scripts to ensure they're correct and won't cause data loss.

6. **Understand the changes**: Don't blindly apply migrations or code transformations. Take time to understand what changes are being made and why.

## Troubleshooting

### Migration Script Generation Fails

If generating a migration script fails:

- Check that your database connection is correct
- Ensure your SQLAlchemy models are properly defined
- Check for syntax errors in your models

### Migration Application Fails

If applying a migration fails:

- Check the error message for clues
- Ensure your database user has the necessary permissions
- Check if the migration is trying to modify tables with data constraints
- If using a rollback, ensure the downgrade function is correctly implemented

### Code Transformation Issues

If code transformations are causing issues:

- Use `--dry-run` to preview changes before applying them
- Apply transformations one at a time using the `--transform` option
- If transformations break your code, use `restore-backup` to revert changes