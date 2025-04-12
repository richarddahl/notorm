#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: build.sh
# Description: Build the application for deployment
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./build.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -e, --env ENV    Specify environment (dev, test, staging, prod)
#   -t, --tag TAG    Specify custom image tag
#   -p, --push       Push the image to registry after building
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false
environment="dev"
custom_tag=""
push_image=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Build the application for deployment" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output
  -e, --env ENV    Specify environment (dev, test, staging, prod)
  -t, --tag TAG    Specify custom image tag
  -p, --push       Push the image to registry after building"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -e|--env)
            environment="$2"
            shift 2
            ;;
        -t|--tag)
            custom_tag="$2"
            shift 2
            ;;
        -p|--push)
            push_image=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$environment" != "dev" && "$environment" != "test" && "$environment" != "staging" && "$environment" != "prod" ]]; then
    log_error "Invalid environment: $environment. Must be one of: dev, test, staging, prod"
    exit 1
fi

# Main script logic
log_section "Building application for $environment environment"

# Check if Docker is running
if ! docker_is_running; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Load environment-specific configuration
config_file="${PROJECT_ROOT}/config/${environment}.env"
if [[ -f "$config_file" ]]; then
    log_info "Loading configuration from $config_file"
    if [[ "$verbose" == true ]]; then
        cat "$config_file" | grep -v "PASSWORD\|SECRET\|KEY"
    fi
    source "$config_file"
else
    log_warning "Configuration file $config_file not found. Using default values."
fi

# Determine image tag
if [[ -n "$custom_tag" ]]; then
    image_tag="$custom_tag"
else
    registry="${CI_REGISTRY:-localhost:5000}"
    timestamp=$(date +%Y%m%d%H%M%S)
    image_tag="${registry}/notorm:${environment}-${timestamp}"
fi

# Build Docker image
log_info "Building Docker image: $image_tag"

# Determine build arguments
build_args=(
    "--build-arg ENV=${environment}"
)

# Add more build arguments based on environment
if [[ "$environment" == "prod" ]]; then
    build_args+=(
        "--build-arg OPTIMIZE=1"
        "--build-arg DEBUG=0"
    )
elif [[ "$environment" == "staging" ]]; then
    build_args+=(
        "--build-arg OPTIMIZE=1"
        "--build-arg DEBUG=1"
    )
else
    build_args+=(
        "--build-arg OPTIMIZE=0"
        "--build-arg DEBUG=1"
    )
fi

# Build the image
log_info "Running Docker build with arguments: ${build_args[*]}"

if [[ "$verbose" == true ]]; then
    docker build "${build_args[@]}" -t "$image_tag" -f "${PROJECT_ROOT}/docker/Dockerfile" "$PROJECT_ROOT"
else
    docker build "${build_args[@]}" -t "$image_tag" -f "${PROJECT_ROOT}/docker/Dockerfile" "$PROJECT_ROOT" > /dev/null
fi

log_success "Docker image built successfully: $image_tag"

# Save image tag to file for other scripts to use
echo "$image_tag" > "${PROJECT_ROOT}/.image_tag"
log_info "Image tag saved to ${PROJECT_ROOT}/.image_tag"

# Push to registry if requested
if [[ "$push_image" == true ]]; then
    if [[ -z "${CI_REGISTRY:-}" && "$registry" == "localhost:5000" ]]; then
        log_warning "No registry specified. Image will only be available locally."
    else
        log_info "Pushing image to registry: $image_tag"
        
        # Login to registry if credentials are provided
        if [[ -n "${CI_REGISTRY_USER:-}" && -n "${CI_REGISTRY_PASSWORD:-}" ]]; then
            log_info "Logging in to registry $registry"
            echo "$CI_REGISTRY_PASSWORD" | docker login "$registry" -u "$CI_REGISTRY_USER" --password-stdin
        fi
        
        # Push the image
        docker push "$image_tag"
        log_success "Image pushed to registry"
    fi
fi

log_section "Next Steps"
log_info "1. Run tests with: ./scripts/ci/test.sh"
log_info "2. Deploy with: ./scripts/ci/deploy.sh --env $environment"

exit 0