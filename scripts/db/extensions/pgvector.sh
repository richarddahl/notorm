#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: pgvector.sh
# Description: Install and configure pgvector extension for PostgreSQL
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./pgvector.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -d, --docker     Install inside Docker container (default: detect environment)
#   -l, --local      Install on local PostgreSQL (default: detect environment)
#   -c, --container  Specify Docker container name (default: pg16_uno)
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../../common/functions.sh"

# Default values
verbose=false
mode="auto"
container_name="pg16_uno"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Install pgvector extension for PostgreSQL" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output
  -d, --docker     Install inside Docker container (default: detect environment)
  -l, --local      Install on local PostgreSQL (default: detect environment)
  -c, --container  Specify Docker container name (default: pg16_uno)"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -d|--docker)
            mode="docker"
            shift
            ;;
        -l|--local)
            mode="local"
            shift
            ;;
        -c|--container)
            container_name="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Detect installation mode if auto
if [ "$mode" = "auto" ]; then
    if docker_container_running "$container_name"; then
        log_info "Detected running Docker container. Using Docker mode."
        mode="docker"
    elif command -v psql &> /dev/null; then
        log_info "Detected local PostgreSQL. Using local mode."
        mode="local"
    else
        log_error "Could not detect installation mode. Please specify using --docker or --local."
        exit 1
    fi
fi

# Main script logic
log_section "PostgreSQL pgvector Extension Installer"

# Installation process
if [ "$mode" = "docker" ]; then
    # Docker installation
    log_info "Installing pgvector in Docker container: $container_name"
    
    # Check if container is running
    if ! docker_container_running "$container_name"; then
        log_error "Docker container '$container_name' is not running."
        log_info "Start the container first with './scripts/docker/start.sh'"
        exit 1
    fi
    
    # Install pgvector in the container
    log_info "Creating extension in database..."
    docker exec "$container_name" psql -U postgres -d uno_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
    
    # Verify installation
    if docker exec "$container_name" psql -U postgres -d uno_dev -c "SELECT * FROM pg_extension WHERE extname = 'vector';" | grep -q vector; then
        log_success "pgvector extension installed successfully in Docker container."
    else
        log_error "Failed to install pgvector extension in Docker container."
        exit 1
    fi
    
else
    # Local installation
    log_info "Installing pgvector for local PostgreSQL"
    
    # Check PostgreSQL client
    if ! command -v psql &> /dev/null; then
        log_error "PostgreSQL client not found. Please install PostgreSQL first."
        exit 1
    fi
    
    # Get PostgreSQL version
    PG_VERSION=$(psql --version | awk '{print $3}' | cut -d. -f1)
    log_info "PostgreSQL version: $PG_VERSION"
    
    # Detect OS
    OS="$(get_os_type)"
    log_info "Detected OS: $OS"
    
    if [ "$OS" = "linux" ]; then
        DISTRO="$(get_linux_distro)"
        log_info "Detected distribution: $DISTRO"
    fi
    
    # Install pgvector based on OS
    if [ "$OS" = "macos" ]; then
        log_info "Installing pgvector on macOS using Homebrew..."
        
        # Check if Homebrew is installed
        if ! command -v brew &> /dev/null; then
            log_error "Homebrew not found. Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
        
        # Install pgvector
        log_info "Installing pgvector..."
        brew install pgvector
        
        # Restart PostgreSQL
        log_info "Restarting PostgreSQL..."
        if brew services list | grep -q postgresql; then
            brew services restart postgresql
        elif brew services list | grep -q "postgresql@$PG_VERSION"; then
            brew services restart "postgresql@$PG_VERSION"
        else
            log_warning "Could not automatically restart PostgreSQL. Please restart PostgreSQL manually."
        fi
        
    elif [ "$OS" = "linux" ] && [ "$DISTRO" = "debian" ]; then
        log_info "Installing pgvector on Debian/Ubuntu..."
        
        # Install dependencies
        log_info "Installing dependencies..."
        sudo apt-get update
        sudo apt-get install -y postgresql-server-dev-$PG_VERSION build-essential git
        
        # Clone and build pgvector
        log_info "Building pgvector..."
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
        log_info "Restarting PostgreSQL..."
        sudo systemctl restart postgresql
        
    elif [ "$OS" = "linux" ] && [ "$DISTRO" = "redhat" ]; then
        log_info "Installing pgvector on RedHat/CentOS/Fedora..."
        
        # Install dependencies
        log_info "Installing dependencies..."
        sudo dnf install -y postgresql-devel git
        
        # Clone and build pgvector
        log_info "Building pgvector..."
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
        log_info "Restarting PostgreSQL..."
        sudo systemctl restart postgresql
        
    else
        log_error "Unsupported operating system: $OS"
        log_info "Please install pgvector manually following the instructions in INSTALL_PGVECTOR.md"
        exit 1
    fi
    
    # Enable extension in database
    log_info "Creating extension in database..."
    psql -U postgres -d uno_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
    
    # Verify installation
    if psql -U postgres -d uno_dev -c "SELECT * FROM pg_extension WHERE extname = 'vector';" | grep -q vector; then
        log_success "pgvector extension installed successfully."
    else
        log_error "Failed to install pgvector extension in local PostgreSQL."
        exit 1
    fi
fi

log_section "Next Steps"
log_info "1. Run 'export ENV=dev' to set the environment"
log_info "2. Run 'python src/scripts/createdb.py' to create the database with vector search capabilities"

exit 0