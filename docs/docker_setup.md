# Docker-First Development Approach

This project follows a Docker-first approach for all database interactions. We **never** use local PostgreSQL installations for development, testing, or deployment.

## Why Docker-First?

1. **Consistency across environments**: The same database configuration works in development, testing, and production
2. **Reduced dependency issues**: No need to install and configure PostgreSQL locally
3. **Extension management**: All required extensions (pgvector, AGE, etc.) are pre-installed
4. **Isolated environments**: Each project can have its own PostgreSQL version and configuration
5. **Simplified setup**: New team members can get started quickly

## Quick Start

Set up the Docker environment and run the application:

```bash
# Set up Docker and run the app
hatch run dev:app
```

Or just set up the Docker environment:

```bash
# Set up Docker environment only
hatch run dev:docker-setup
```

## Docker Configuration

The Docker setup includes:

- PostgreSQL 16 with all required extensions
- Automatic initialization of schemas and tables
- Named volumes for persistent data
- Pre-configured users and permissions

We use Docker named volumes (not bind mounts) to avoid permission issues, particularly on macOS. This is configured in the `docker-compose.yaml` files with entries like:

```yaml
volumes:
  pg_data:  # Named volume for PostgreSQL data```

driver: local
```
```

And then used in the services with specific user settings:

```yaml
services:
  db:
    user: postgres  # Ensures proper permissions
    volumes:
      - pg_data:/var/lib/postgresql/data
```

Note: We intentionally avoid setting the `PGDATA` environment variable to let PostgreSQL use its default location and permissions logic.

## Environment-Specific Setup

### Development

```bash
# Start the development environment
hatch run dev:docker-setup

# Run the application with Docker PostgreSQL
hatch run dev:main
```

### Testing

```bash
# Set up the test database
hatch run test:docker-setup

# Run tests with Docker PostgreSQL
hatch run test:test
```

### Production

For production, we use Docker Compose or Kubernetes configurations that include PostgreSQL containers with the same setup as development.

## Repository Structure

- `docker/`: Contains all Docker-related files
  - `Dockerfile`: PostgreSQL image with extensions
  - `docker-compose.yaml`: Service definition
  - `init-db.sh`: Initialization script
  - `rebuild.sh`: Helper script to rebuild containers

## Adding New Extensions

To add a new PostgreSQL extension:

1. Update the `Dockerfile` to install the extension
2. Update the `init-db.sh` script to enable the extension
3. Rebuild the Docker container: `hatch run dev:docker-setup`

## Troubleshooting

### Volume Permission Issues

If you encounter permission errors such as:

```
initdb: error: could not change permissions of directory "/var/lib/postgresql/data": Operation not permitted
```

This is a common issue with Docker volumes, especially on macOS. Our solution is to:

1. Use named volumes instead of bind mounts
2. Explicitly set the user to `postgres` in the docker-compose file
3. Avoid setting the `PGDATA` environment variable
4. Let PostgreSQL handle its own directory permissions

If you still experience issues:

```bash
# Remove the volumes completely
docker-compose down -v

# Rebuild from scratch
hatch run dev:docker-setup
```

For stubborn permission issues, you may need to manually remove Docker volumes:

```bash
# List all Docker volumes
docker volume ls

# Remove specific volumes
docker volume rm docker_pg_data docker_pg_test_data

# Or remove all unused volumes (be careful!)
docker volume prune
```

### Container Not Starting

If the container doesn't start properly:

```bash
# Check the logs
docker logs pg16_uno

# For the test container
docker logs pg16_uno_test
```