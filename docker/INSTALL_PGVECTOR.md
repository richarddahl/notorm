# Installing pgvector for PostgreSQL

There are two ways to install the pgvector extension:

## Option 1: Install pgvector directly on your PostgreSQL server

If you're running PostgreSQL directly on your host machine (not in Docker), follow these steps:

### For macOS (with Homebrew)

```bash
brew install pgvector
```

### For Ubuntu/Debian

```bash
sudo apt-get install postgresql-server-dev-15  # Replace 15 with your PostgreSQL version
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### For RHEL/CentOS/Fedora

```bash
sudo dnf install postgresql-devel
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

## Option 2: For Docker setup

1. Download the pgvector extension ZIP file from GitHub:
   - Go to https://github.com/pgvector/pgvector/archive/refs/heads/master.zip
   - Save the file to `docker/pg_ext_files/pgvector-master.zip` in your project

2. Rebuild your Docker container:
   ```bash
   cd docker
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Option 3: Use a PostgreSQL image with pgvector pre-installed

If you prefer a simpler approach, you can modify your `docker-compose.yaml` to use the pgvector-enabled image:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    # rest of your configuration...
```

## Verify Installation

After installing, verify the extension is available with:

```sql
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

You should see 'vector' in the results.

## Troubleshooting

If you encounter the error:
```
psycopg.errors.FeatureNotSupported: extension "vector" is not available
```

It means the pgvector extension isn't properly installed. Follow the steps above to install it.

If you're using Docker, make sure:
1. The extension ZIP file is correctly placed in the `pg_ext_files` directory
2. The Dockerfile is correctly set up to install the extension
3. The Docker container has been rebuilt after adding the extension files