# Docker Configuration

This directory contains Docker configuration for uno.

This project uses a Docker-first approach for all PostgreSQL database operations. Never use a local PostgreSQL installation for development, testing, or deployment.

## Features

- PostgreSQL 16 with all required extensions pre-installed:
  - pgvector (vector similarity search)
  - AGE (Apache Graph Extension)
  - pgjwt (JSON Web Tokens)
  - supa_audit (Audit logging)
  - Others: btree_gist, hstore, pgcrypto

## Why Docker-First?

1. **Consistency**: The same database configuration across all environments
2. **Extension management**: All required extensions (pgvector, AGE, etc.) pre-installed
3. **Isolation**: Each project can have its own PostgreSQL without conflicts
4. **Simplified setup**: No need to deal with local PostgreSQL installation issues
5. **Permission handling**: No issues with superuser privileges or file permissions

## Directory Structure

- `Dockerfile`: Builds a PostgreSQL 16 image with all required extensions
- `docker-compose.yaml`: Defines the PostgreSQL service and volume mapping
- `scripts/init-db.sh`: Initializes the database with required extensions
- `scripts/rebuild.sh`: Helper script to rebuild containers
- `scripts/setup_with_docker.sh`: Sets up the Docker environment for development
- `scripts/setup_test_docker.sh`: Sets up the Docker environment for testing
- `scripts/download_pgvector.sh`: Downloads pgvector extension
- `scripts/init-extensions.sh`: Installs PostgreSQL extensions in the container
- `pg_ext_files/`: Directory for PostgreSQL extension files

## Quick Setup

```bash
# Development environment
../scripts/setup_docker.sh

# Test environment
../scripts/setup_test_env.sh
```

Or using Hatch:

```bash
# Development environment
hatch run dev:docker-setup

# Test environment
hatch run test:docker-setup
```

## Environment Configuration

- Development: `localhost:5432` with database `uno_dev`
- Testing: `localhost:5433` with database `uno_test` (different port to allow both to run simultaneously)
- Both environments use `postgres` user with password `postgreSQLR0ck%`

## Volumes and Permissions

We use named volumes (not bind mounts) to avoid permission issues:

```yaml
volumes:
  pg_data:
    driver: local
```

And we explicitly set the user to `postgres` in the services:

```yaml
services:
  db:
    user: postgres
    volumes:
      - pg_data:/var/lib/postgresql/data
```

We also avoid setting the `PGDATA` environment variable to let PostgreSQL handle its own permissions.

## Connecting to the Database

The PostgreSQL server will be available on `localhost:5432` with the following credentials:

- **Host**: localhost
- **Port**: 5432
- **Database**: uno_dev (or uno_test for test environment)
- **Username**: postgres
- **Password**: postgreSQLR0ck%

You can connect using any PostgreSQL client or the psql command line:

```bash
psql -h localhost -p 5432 -U postgres -d uno_dev
```

## Troubleshooting

If you encounter permission errors:

```bash
# Reset the volumes
docker-compose -f docker/docker-compose.yaml down -v

# For test environment
docker-compose -f docker/test/docker-compose.yaml down -v

# Rebuild from scratch
../scripts/setup_docker.sh  # or ../scripts/setup_test_env.sh
```

### Container Logs

To view container logs:

```bash
docker logs pg16_uno
# For test environment
docker logs pg16_uno_test
```

For more detailed information, see [Docker Setup](../docs/docker_setup.md).