#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: setup_vector_search.sh
# Description: Set up vector search functionality for an Uno project
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./setup_vector_search.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -d, --db-name    Database name (default: uno_dev)
#   -D, --dimensions Embedding dimensions (default: 1536)
#   -i, --index-type Index type to use: hnsw or ivfflat (default: hnsw)
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false
db_name="${DB_NAME:-uno_dev}"
dimensions=1536
index_type="hnsw"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Set up vector search functionality for an Uno project" "  -h, --help          Display this help message
  -v, --verbose       Enable verbose output
  -d, --db-name       Database name (default: uno_dev)
  -D, --dimensions    Embedding dimensions (default: 1536)
  -i, --index-type    Index type to use: hnsw or ivfflat (default: hnsw)"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -d|--db-name)
            db_name="$2"
            shift 2
            ;;
        -D|--dimensions)
            dimensions="$2"
            shift 2
            ;;
        -i|--index-type)
            index_type="$2"
            if [[ "$index_type" != "hnsw" && "$index_type" != "ivfflat" ]]; then
                log_error "Invalid index type: $index_type. Must be 'hnsw' or 'ivfflat'"
                exit 1
            fi
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Main script logic
log_section "Vector Search Setup"

# Step 1: Check if PostgreSQL is available
log_info "Checking PostgreSQL availability..."

if docker_container_running "pg16_uno"; then
    log_info "PostgreSQL container is running"
else
    log_error "PostgreSQL container is not running"
    log_info "Start the container with: ./scripts/docker/start.sh"
    exit 1
fi

# Step 2: Check if pgvector extension is installed
log_info "Checking pgvector extension..."

pgvector_check=$(docker exec pg16_uno psql -U postgres -d "$db_name" -c "SELECT 1 FROM pg_extension WHERE extname = 'vector'" -t | tr -d ' ')

if [ "$pgvector_check" = "1" ]; then
    log_info "pgvector extension is already installed"
else
    log_info "Installing pgvector extension..."
    # Use the pgvector.sh script from the db/extensions directory
    "${SCRIPT_DIR}/../db/extensions/pgvector.sh" --db-name "$db_name"
fi

# Step 3: Create vector search configuration
log_info "Creating vector search configuration..."

# Create a .env file with vector search settings
vector_env_file="${PROJECT_ROOT}/.env_vector"

echo "# Vector Search Configuration" > "$vector_env_file"
echo "VECTOR_DIMENSIONS=$dimensions" >> "$vector_env_file"
echo "VECTOR_INDEX_TYPE=$index_type" >> "$vector_env_file"
echo "VECTOR_BATCH_SIZE=50" >> "$vector_env_file"
echo "VECTOR_UPDATE_INTERVAL=1.0" >> "$vector_env_file"
echo "VECTOR_AUTO_START=True" >> "$vector_env_file"
echo "" >> "$vector_env_file"
echo "# Entity Configuration" >> "$vector_env_file"
echo "VECTOR_ENTITIES={" >> "$vector_env_file"
echo "    \"document\": {" >> "$vector_env_file"
echo "        \"fields\": [\"title\", \"content\"]," >> "$vector_env_file"
echo "        \"dimensions\": $dimensions," >> "$vector_env_file"
echo "        \"index_type\": \"$index_type\"" >> "$vector_env_file"
echo "    }" >> "$vector_env_file"
echo "}" >> "$vector_env_file"

log_success "Vector search configuration created at $vector_env_file"

# Step 4: Create example documents
log_info "Setting up example documents..."

# Create a .env file with the current settings for the script
export ENV="dev"
export DB_NAME="$db_name"
export VECTOR_DIMENSIONS="$dimensions"
export VECTOR_INDEX_TYPE="$index_type"

# Create example documents using the vector_demo.py script
cd "$PROJECT_ROOT"
python src/scripts/vector_demo.py setup

# Step 5: Run a test search
log_info "Testing vector search functionality..."

# Run a simple search using the vector_demo.py script
python src/scripts/vector_demo.py search "vector database" 5

log_section "Next Steps"
log_info "1. Add vector search configuration to your settings:"
log_info "   - Copy settings from $vector_env_file to your .env file"
log_info "   - Or source it directly: source $vector_env_file"
log_info ""
log_info "2. Try the vector search example:"
log_info "   python examples/vector_search/vector_search_example.py"
log_info ""
log_info "3. Run performance benchmarks:"
log_info "   hatch run test:benchmark"
log_info ""
log_info "4. Read the documentation:"
log_info "   docs/vector_search/overview.md"

exit 0