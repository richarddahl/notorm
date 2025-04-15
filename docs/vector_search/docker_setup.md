# Docker Setup for Vector Search

This guide explains how to set up the Docker environment for uno Framework with vector search capabilities using PostgreSQL and pgvector.

## Quick Setup

The easiest way to get started is to use the provided setup script:

```bash
# Using Hatch (recommended)
hatch run dev:docker-setup

# Or directly
./setup_with_docker.sh
```

This script will:
1. Build and start the Docker container
2. Wait for PostgreSQL to be ready
3. Create the database with vector search capabilities
4. Display connection information

## Running the Application with Docker

To run the application with Docker-based PostgreSQL:

```bash
# This will set up Docker and run the app
hatch run dev:app
```

## Overview

The Docker setup for uno creates a PostgreSQL 16 container with the following extensions:

- **pgvector**: For vector similarity search
- **AGE** (Apache Graph Extension): For graph database functionality
- **pgjwt**: For JSON Web Token support
- **supa_audit**: For audit logging
- Additional extensions: btree_gist, hstore, pgcrypto

## Dockerfile Configuration

The `Dockerfile` builds PostgreSQL 16 with all required extensions:

```dockerfile
FROM postgres:16-alpine

# Install required packages
RUN apk add --no-cache unzip make gcc g++ musl-dev postgresql16-dev ...

# Clone and build extensions from source
RUN git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && \```

cd pgvector && make && make install
```

# Configure symbolic links for extensions
RUN mkdir -p /usr/local/lib/postgresql/plugins
RUN ln -s /usr/local/lib/postgresql/vector.so /usr/local/lib/postgresql/plugins/vector.so
```

## Docker Compose Configuration

The `docker-compose.yaml` file configures:

- PostgreSQL container based on the custom Dockerfile
- Local volume mapping to persist data
- Environment variables and port mappings

```yaml
services:
  db:
    container_name: "pg16_uno"
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ../data/postgresql:/var/lib/postgresql/data:z
    ports:
      - "5432:5432"
```

## Getting Started

### Setting Up the Docker Environment

1. Navigate to the docker directory:
   ```bash
   cd /path/to/notorm/docker
   ```

2. Run the rebuild script to set up the environment:
   ```bash
   ./rebuild.sh
   ```
   
   This script:
   - Stops any existing containers
   - Optionally clears existing PostgreSQL data
   - Rebuilds the Docker image without using cache
   - Starts the container

3. Wait for PostgreSQL to initialize (about 5-10 seconds)

### Creating the Database with Vector Support

1. Set the environment to development:
   ```bash
   export ENV=dev
   ```

2. Run the database creation script:
   ```bash
   cd /path/to/notorm
   python src/scripts/createdb.py
   ```

   This script:
   - Creates the database structure
   - Sets up roles and permissions
   - Creates vector functions and triggers
   - Configures the documents table for RAG

## Data Persistence

The database data is stored in the `data/postgresql` directory, which is:

1. Mounted as a volume in the container
2. Excluded from Git via `.gitignore`
3. Persisted between container restarts

## Initialization Script

When the container starts, the `init-db.sh` script runs automatically to:

1. Enable all required extensions including pgvector
2. Create the graph database structure
3. Configure initial settings

## Troubleshooting

### Permission Issues

If you encounter permission errors with the data directory:

```bash
sudo chown -R $(id -u):$(id -g) /path/to/notorm/data/postgresql
```

### Checking Extension Status

Connect to the database and verify extensions are installed:

```bash
psql -h localhost -p 5432 -U postgres
postgres=# SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

### Rebuilding the Container

If you need to completely rebuild the environment:

```bash
cd /path/to/notorm/docker
./rebuild.sh
```

### Checking Container Logs

```bash
docker-compose logs db
```

## Advanced Configuration

### Changing Vector Dimensions

The default vector dimension is 1536 (OpenAI Ada 2). To change it:

1. Edit `.env_dev` file:
   ```
   VECTOR_DIMENSIONS=384  # Example for smaller dimensions
   ```

2. Update vector tables by modifying the `vector.py` emitter.

### Modifying Index Types

You can switch between different index types:

- **HNSW**: Faster search but slower indexing
- **IVF-Flat**: Better balance between speed and accuracy

Edit `.env_dev` file:
```
VECTOR_INDEX_TYPE="ivfflat"  # Change to IVF-Flat
```