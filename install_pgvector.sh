#!/bin/bash
# Script to install pgvector extension for PostgreSQL

set -e  # Exit on error

echo "PostgreSQL pgvector Extension Installer"
echo "---------------------------------------"

# Check if we have PostgreSQL installed
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client found"
    PG_VERSION=$(psql --version | awk '{print $3}' | cut -d. -f1)
    echo "   PostgreSQL version: $PG_VERSION"
else
    echo "❌ PostgreSQL client not found"
    echo "   Please install PostgreSQL first"
    exit 1
fi

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    if [ -f /etc/debian_version ]; then
        DISTRO="debian"
    elif [ -f /etc/redhat-release ]; then
        DISTRO="redhat"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
fi

echo "Detected OS: $OS"
if [ "$OS" = "linux" ]; then
    echo "Detected distribution: $DISTRO"
fi

# Install pgvector based on OS
if [ "$OS" = "macos" ]; then
    echo "Installing pgvector on macOS using Homebrew..."
    
    # Check if Homebrew is installed
    if command -v brew &> /dev/null; then
        echo "✅ Homebrew found"
    else
        echo "❌ Homebrew not found"
        echo "   Please install Homebrew first: https://brew.sh/"
        exit 1
    fi
    
    # Install pgvector
    echo "Installing pgvector..."
    brew install pgvector
    
    # Restart PostgreSQL
    echo "Restarting PostgreSQL..."
    if brew services list | grep -q postgresql; then
        brew services restart postgresql
    elif brew services list | grep -q postgresql@$PG_VERSION; then
        brew services restart postgresql@$PG_VERSION
    else
        echo "⚠️ Could not automatically restart PostgreSQL"
        echo "   Please restart PostgreSQL manually"
    fi
    
elif [ "$OS" = "linux" ] && [ "$DISTRO" = "debian" ]; then
    echo "Installing pgvector on Debian/Ubuntu..."
    
    # Install dependencies
    echo "Installing dependencies..."
    sudo apt-get update
    sudo apt-get install -y postgresql-server-dev-$PG_VERSION build-essential git
    
    # Clone and build pgvector
    echo "Building pgvector..."
    mkdir -p /tmp/pgvector_build
    cd /tmp/pgvector_build
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    sudo make install
    
    # Clean up
    cd /
    rm -rf /tmp/pgvector_build
    
    # Restart PostgreSQL
    echo "Restarting PostgreSQL..."
    sudo systemctl restart postgresql
    
elif [ "$OS" = "linux" ] && [ "$DISTRO" = "redhat" ]; then
    echo "Installing pgvector on RedHat/CentOS/Fedora..."
    
    # Install dependencies
    echo "Installing dependencies..."
    sudo dnf install -y postgresql-devel git
    
    # Clone and build pgvector
    echo "Building pgvector..."
    mkdir -p /tmp/pgvector_build
    cd /tmp/pgvector_build
    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    sudo make install
    
    # Clean up
    cd /
    rm -rf /tmp/pgvector_build
    
    # Restart PostgreSQL
    echo "Restarting PostgreSQL..."
    sudo systemctl restart postgresql
    
else
    echo "❌ Unsupported operating system: $OS"
    echo "   Please install pgvector manually following the instructions in INSTALL_PGVECTOR.md"
    exit 1
fi

echo ""
echo "✅ pgvector installation completed"
echo ""
echo "To verify the installation, connect to PostgreSQL and run:"
echo "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
echo ""
echo "Next steps:"
echo "1. Run 'export ENV=dev' to set the environment"
echo "2. Run 'python src/scripts/createdb.py' to create the database with vector search capabilities"
echo ""