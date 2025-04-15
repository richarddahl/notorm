# Comprehensive Docker Setup Guide

This guide provides detailed information about setting up, maintaining, and troubleshooting the Docker environment for uno development.

## Docker Environment Architecture

The uno framework uses a Docker-first approach for all database interactions. The Docker environment consists of:

1. **PostgreSQL Database Container**: PostgreSQL 16 with all required extensions (pgvector, Apache AGE, etc.)
2. **Init Scripts**: Automated initialization of databases, schemas, roles, and permissions
3. **Volume Management**: Named volumes for persistent data storage
4. **Health Checks**: Automated monitoring of container health

### Container Organization

```
uno_environment
└── docker/
    ├── Dockerfile          # PostgreSQL image with extensions
    ├── docker-compose.yaml # Main service definition
    ├── scripts/
    │   ├── init-db.sh      # Database initialization script
    │   ├── init-extensions.sh # Extension setup
    │   └── install_pgvector.sh # Vector extension installation
    ├── test/
    │   └── docker-compose.yaml # Test-specific service configuration
    └── pg_ext_files/       # Extension source files
```

## Setup Process

### 1. Development Environment Setup

The `scripts/docker/start.sh` script automates the Docker setup process:

```bash
# Basic setup
./scripts/docker/start.sh

# Verbose output with clean start
./scripts/docker/start.sh --verbose --clean

# Interactive (foreground) mode
./scripts/docker/start.sh --detached false
```

#### What happens during setup:

1. **Docker Service Check**: Verifies Docker daemon is running
2. **Container Cleanup**: Stops any existing containers
3. **Volume Management**: Optionally cleans data volumes
4. **Image Building**: Builds the PostgreSQL image with extensions
5. **Container Startup**: Launches the PostgreSQL container
6. **Health Check**: Waits for PostgreSQL to be ready
7. **Initialization**: Runs database initialization scripts

### 2. Test Environment Setup

```bash
# Set up test environment
hatch run test:docker-setup

# Run tests with test Docker environment
hatch run test:test
```

The test environment uses a separate Docker Compose configuration to create an isolated database for testing.

## Container Management

### Starting and Stopping

```bash
# Start Docker environment
./scripts/docker/start.sh

# Stop Docker environment
./scripts/docker/stop.sh

# Restart with clean data
./scripts/docker/start.sh --clean
```

### Container Monitoring

```bash
# Check container status
docker ps | grep pg16_uno

# View container logs
docker logs pg16_uno

# View container logs with follow
docker logs -f pg16_uno

# Access PostgreSQL shell
docker exec -it pg16_uno psql -U postgres -d uno_dev
```

### Health Checks

The Docker environment includes built-in health checks for PostgreSQL:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 5s
  timeout: 5s
  retries: 5
  start_period: 10s
```

You can manually check container health:

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' pg16_uno

# Verify PostgreSQL is responding
docker exec pg16_uno pg_isready -U postgres
```

## Volume Management

### Understanding Docker Volumes

The uno Docker setup uses named volumes for data persistence:

```yaml
volumes:
  pg_data:  # Named volume for PostgreSQL data
    driver: local
```

Named volumes provide several advantages:
- Persistent data storage across container restarts
- Better performance than bind mounts
- Isolation from host filesystem permissions
- Automatic cleanup when removed

### Volume Operations

```bash
# List volumes
docker volume ls | grep pg_data

# Inspect volume
docker volume inspect docker_pg_data

# Remove volume (will delete all data)
docker volume rm docker_pg_data

# Remove all unused volumes
docker volume prune
```

## Extension Management

### Included Extensions

The Docker environment includes the following PostgreSQL extensions:

- **pgvector**: Vector similarity search
- **Apache AGE**: Graph database capabilities
- **pl/pgsql**: Procedural language
- **pgcrypto**: Encryption functions
- **uuid-ossp**: UUID generation

### Adding New Extensions

To add a new PostgreSQL extension:

1. Update `docker/Dockerfile` to install the extension:
```dockerfile
# Install extension dependencies
RUN apt-get update && apt-get install -y \
    postgresql-16-new-extension \
    && rm -rf /var/lib/apt/lists/*
```

2. Update `docker/scripts/init-extensions.sh` to enable the extension:
```bash
# Enable extension in database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS "new-extension";
EOSQL
```

3. Rebuild the Docker container:
```bash
./scripts/docker/start.sh --clean
```

## Database Configuration

### PostgreSQL Configuration

The Docker environment configures PostgreSQL with optimized settings:

```yaml
environment:
  POSTGRES_PASSWORD: "postgreSQLR0ck%"
  POSTGRES_DB: "uno_dev"
  POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
  PGDATA: "/var/lib/postgresql/data/pgdata"
  POSTGRES_HOST_AUTH_METHOD: "md5"
  # Performance settings
  shared_buffers: "128MB"
  max_connections: "100"
  effective_cache_size: "512MB"
  work_mem: "4MB"
  maintenance_work_mem: "64MB"
```

### Database Users and Permissions

The Docker setup creates the following database users:

- `postgres`: Superuser for admin operations
- `uno_app`: Application user with restricted permissions
- `uno_test`: Test user with full permissions in test database
- `uno_readonly`: Read-only user for reporting and queries

### Connection Details

Default connection details:

- **Host**: localhost
- **Port**: 5432
- **Database**: uno_dev
- **User**: postgres
- **Password**: postgreSQLR0ck%

## Troubleshooting

### Common Issues and Solutions

#### 1. Container Fails to Start

**Symptoms**: `docker-compose up` fails or container stops immediately after starting

**Solutions**:
1. Check Docker logs:
```bash
docker logs pg16_uno
```

2. Verify PostgreSQL data directory permissions:
```bash
docker-compose down -v  # Remove volumes
./scripts/docker/start.sh --clean  # Start fresh
```

3. Ensure Docker has enough resources:
```bash
# For Docker Desktop, increase CPU and memory in preferences
```

#### 2. Volume Permission Issues

**Symptoms**: Errors about permission denied when accessing `/var/lib/postgresql/data`

**Solutions**:
1. Use named volumes instead of bind mounts (already configured)
2. Ensure the PostgreSQL container runs as the `postgres` user
3. Remove volumes and recreate:
```bash
docker-compose down -v
docker volume rm docker_pg_data
./scripts/docker/start.sh
```

#### 3. Port Conflicts

**Symptoms**: Error message that port 5432 is already in use

**Solutions**:
1. Stop any local PostgreSQL instances:
```bash
# macOS
sudo pkill -f postgres

# Linux
sudo systemctl stop postgresql
```

2. Change the exposed port in `docker-compose.yaml`:
```yaml
ports:
  - "5433:5432"  # Map to port 5433 instead
```

#### 4. Extension Installation Failures

**Symptoms**: Errors in logs about failing to create extensions

**Solutions**:
1. Check if extension is properly installed in container:
```bash
docker exec pg16_uno apt list --installed | grep postgresql
```

2. Verify extension files exist:
```bash
docker exec pg16_uno ls -la /usr/share/postgresql/16/extension/
```

3. Manual extension installation:
```bash
docker exec -it pg16_uno bash
apt-get update && apt-get install -y postgresql-16-extension-name
```

#### 5. Database Not Ready

**Symptoms**: Application fails to connect even though container is running

**Solutions**:
1. Check if PostgreSQL is ready:
```bash
docker exec pg16_uno pg_isready -U postgres
```

2. Verify initialization completed:
```bash
docker logs pg16_uno | grep "database system is ready to accept connections"
```

3. Manually run initialization scripts:
```bash
docker exec -it pg16_uno bash /docker-entrypoint-initdb.d/init-db.sh
```

### Diagnostic Commands

```bash
# Check PostgreSQL logs
docker exec pg16_uno cat /var/log/postgresql/postgresql-16-main.log

# Check running processes in container
docker exec pg16_uno ps -ef

# Check Docker container resources
docker stats pg16_uno

# Inspect container configuration
docker inspect pg16_uno

# Test database connection
docker exec -it pg16_uno psql -U postgres -c "SELECT version();"
```

## Best Practices

### Docker Configuration

1. **Resource Allocation**: Ensure Docker has sufficient resources (at least 2 CPU cores, 2GB RAM)
2. **Storage Optimization**: Regularly prune unused volumes and images
3. **Security**: Use environment variables for sensitive information
4. **Network Isolation**: Use Docker networks to isolate services

### Database Management

1. **Regular Backups**: Use `pg_dump` to create backups:
```bash
docker exec pg16_uno pg_dump -U postgres uno_dev > backup.sql
```

2. **Monitoring**: Use monitoring tools for production environments:
```bash
# Simple monitoring with docker stats
docker stats pg16_uno
```

3. **Connection Pooling**: For production, consider adding pgBouncer:
```yaml
services:
  pgbouncer:
    image: bitnami/pgbouncer:latest
    environment:
      - POSTGRESQL_HOST=db
      - POSTGRESQL_PORT=5432
      - PGBOUNCER_PORT=6432
      - PGBOUNCER_POOL_MODE=transaction
```

### CI/CD Integration

The Docker environment can be integrated with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgreSQLR0ck%
          POSTGRES_DB: uno_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
```

## Advanced Topics

### Custom PostgreSQL Configuration

To customize PostgreSQL configuration:

1. Create a `postgresql.conf` file:
```bash
# Example configuration
shared_buffers = 256MB
work_mem = 8MB
maintenance_work_mem = 128MB
max_connections = 200
```

2. Mount it in `docker-compose.yaml`:
```yaml
volumes:
  - ./postgresql.conf:/etc/postgresql/postgresql.conf
command: postgres -c 'config_file=/etc/postgresql/postgresql.conf'
```

### Multi-Container Setup

For advanced setups with multiple services:

```yaml
services:
  db:
    # PostgreSQL configuration
  
  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - db
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Docker Networking

For custom network configurations:

```yaml
networks:
  uno_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

services:
  db:
    networks:
      - uno_network
```

## Additional Resources

- [PostgreSQL Docker Image Documentation](https://hub.docker.com/_/postgres)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/16/admin.html)
- [Docker Networking Guide](https://docs.docker.com/network/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)