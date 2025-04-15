# Installing pgvector for the uno Framework

This guide explains how to install the pgvector extension for your local PostgreSQL database
or Docker setup to support vector search capabilities.

## Option 1: Install pgvector on your local PostgreSQL (Recommended)

### macOS with Homebrew

```bash
# Install pgvector extension
brew install pgvector

# Restart PostgreSQL to apply changes
brew services restart postgresql@16  # Replace 16 with your PostgreSQL version
```

### Ubuntu/Debian

```bash
# Install build dependencies
sudo apt-get update
sudo apt-get install -y postgresql-server-dev-16 git build-essential  # Replace 16 with your PostgreSQL version

# Download and build pgvector
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### RHEL/CentOS/Fedora

```bash
# Install build dependencies
sudo dnf install -y postgresql-devel git
 
# Download and build pgvector
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### Windows

1. Download pre-built binaries from: https://github.com/pgvector/pgvector/releases
2. Extract the files to your PostgreSQL installation directory
3. Restart the PostgreSQL service

## Option 2: Use the Docker setup with pgvector

We've updated the Docker configuration to use an official pgvector image:

1. Rebuild your Docker container:
   ```bash
   cd docker
   docker-compose down
   docker-compose up -d
   ```

This will start a PostgreSQL container with pgvector already installed.

## Creating the database

After installing pgvector, create the database with all the vector functionality:

```bash
# Set the environment to development
export ENV=dev

# Create the database and set up vector search
python src/scripts/createdb.py
```

## Troubleshooting

### Error: "extension vector is not available"

If you see this error when running `createdb.py`:

```
psycopg.errors.FeatureNotSupported: extension "vector" is not available
DETAIL: Could not open extension control file "/usr/local/share/postgresql/extension/vector.control": No such file or directory.
HINT: The extension must first be installed on the system where PostgreSQL is running.
```

It means pgvector is not properly installed. Review the installation steps above.

### Verifying Installation

You can verify that pgvector is installed correctly by connecting to your PostgreSQL database and running:

```sql
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

You should see 'vector' in the results.