#!/bin/bash
# -----------------------------------------------------------------------------
# Common shell functions for uno scripts
# -----------------------------------------------------------------------------

# Exit immediately if a command exits with a non-zero status
set -e

# Colors and formatting
RESET="\033[0m"
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
CYAN="\033[36m"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${RESET} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${RESET} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${RESET} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${RESET} $1" >&2
}

log_section() {
    echo -e "\n${BOLD}${CYAN}===== $1 =====${RESET}\n"
}

# Docker functions
docker_is_running() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        return 1
    fi
    return 0
}

docker_container_running() {
    local container_name="$1"
    if docker ps -q -f name="$container_name" | grep -q .; then
        return 0
    else
        return 1
    fi
}

docker_wait_for_postgres() {
    local container_name="$1"
    local max_attempts="$2"
    local attempt=1
    
    log_info "Waiting for PostgreSQL to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if docker exec "$container_name" pg_isready -U postgres > /dev/null 2>&1; then
            log_success "PostgreSQL is ready!"
            return 0
        fi
        
        log_info "Waiting for PostgreSQL to be ready (attempt $attempt/$max_attempts)..."
        sleep 2
        attempt=$((attempt + 1))
        
        if [ $attempt -gt $max_attempts ]; then
            log_error "PostgreSQL did not become ready in time. Check Docker logs:"
            docker logs "$container_name"
            return 1
        fi
    done
}

# Environment functions
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command '$1' not found."
        return 1
    fi
    return 0
}

get_os_type() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

get_linux_distro() {
    if [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "redhat"
    else
        echo "unknown"
    fi
}

# Script helper functions
show_help() {
    local script_name="$1"
    local description="$2"
    local options="$3"
    
    echo -e "${BOLD}$script_name${RESET} - $description"
    echo
    echo "Usage: $script_name [options]"
    echo
    echo "Options:"
    echo "$options"
    echo
}

confirm() {
    local prompt="$1"
    local default="${2:-n}"
    
    # Set default prompt display
    if [ "$default" = "y" ]; then
        local yn_prompt="Y/n"
    else
        local yn_prompt="y/N"
    fi
    
    # Check if running non-interactively
    if [ ! -t 0 ]; then
        log_info "Non-interactive mode detected. Using default: $default"
        if [ "$default" = "y" ]; then
            return 0
        else
            return 1
        fi
    fi
    
    # Interactive mode
    read -p "$prompt [$yn_prompt]: " response
    if [ -z "$response" ]; then
        response=$default
    fi
    
    if [[ $response =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}