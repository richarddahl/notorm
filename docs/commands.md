# Uno CLI Commands

Uno provides a set of command-line tools to help you manage your application. These commands are available through Hatch, the project's build system.

## Database Management

### createdb

Creates the database with all roles, schemas, extensions, tables and initial data.

```bash
hatch run createdb
```

### dropdb

Drops the database and all associated roles.

```bash
hatch run dropdb
```

### createsuperuser

Creates a superuser account in the database.

```bash
hatch run createsuperuser
```

### createquerypaths

Creates predefined query paths.

```bash
hatch run createquerypaths
```

## Migration Commands

Uno provides a complete set of migration commands powered by Alembic. See the [Migrations](db/migrations.md) documentation for detailed usage.

### migrate-init

Initializes the migration environment (usually run automatically by createdb).

```bash
hatch run migrate-init
```

### migrate-generate

Generates a new migration based on model changes.

```bash
hatch run migrate-generate "Description of changes"
```

### migrate-up

Upgrades the database to the latest revision or a specific revision.

```bash
# Upgrade to latest
hatch run migrate-up

# Upgrade to specific revision
hatch run migrate-up abc123def456
```

### migrate-down

Downgrades the database to a previous revision.

```bash
hatch run migrate-down abc123def456
```

### migrate-current

Shows the current migration version.

```bash
hatch run migrate-current
```

### migrate-history

Shows migration history.

```bash
hatch run migrate-history
```

### migrate-revisions

Lists all available revisions.

```bash
hatch run migrate-revisions
```

## Development Commands

### main

Runs the development server with auto-reload.

```bash
hatch run main
```

## Testing Commands

### test

Runs tests without detailed output.

```bash
hatch run test
```

### testv

Runs tests with moderate verbosity.

```bash
hatch run testv
```

### testvv

Runs tests with high verbosity.

```bash
hatch run testvv
```

### test-cov

Runs tests with coverage measurement.

```bash
hatch run test-cov
```

### cov-report

Displays coverage report.

```bash
hatch run cov-report
```

## Documentation Commands

### docs:build

Builds the documentation site.

```bash
hatch run docs:build
```

### docs:serve

Serves the documentation site locally.

```bash
hatch run docs:serve
```