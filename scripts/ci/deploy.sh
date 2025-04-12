#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: deploy.sh
# Description: Deploy the application to the specified environment
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./deploy.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -e, --env ENV    Specify environment (dev, test, staging, prod)
#   -d, --dry-run    Perform a dry run without making changes
#   -f, --force      Force deployment even if validation fails
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
dry_run=false
force=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Deploy the application to the specified environment" "  -h, --help       Display this help message
  -v, --verbose    Enable verbose output
  -e, --env ENV    Specify environment (dev, test, staging, prod)
  -d, --dry-run    Perform a dry run without making changes
  -f, --force      Force deployment even if validation fails"
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
        -d|--dry-run)
            dry_run=true
            shift
            ;;
        -f|--force)
            force=true
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
log_section "Deployment to $environment environment"

# Check if Docker is running
if ! docker_is_running; then
    if [[ "$force" == true ]]; then
        log_warning "Docker is not running but continuing due to --force flag"
    else
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
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

# Build the application
log_info "Building application for $environment..."
if [[ "$dry_run" == true ]]; then
    log_info "[DRY RUN] Would build application for $environment"
else
    # Build Docker image
    image_tag="${CI_REGISTRY:-localhost:5000}/notorm:${environment}-$(date +%Y%m%d%H%M%S)"
    log_info "Building Docker image: $image_tag"
    
    if [[ "$verbose" == true ]]; then
        docker build -t "$image_tag" -f "${PROJECT_ROOT}/docker/Dockerfile" "$PROJECT_ROOT"
    else
        docker build -t "$image_tag" -f "${PROJECT_ROOT}/docker/Dockerfile" "$PROJECT_ROOT" > /dev/null
    fi
    
    log_success "Docker image built successfully"
    
    # Push to registry if not local development
    if [[ "$environment" != "dev" && -n "${CI_REGISTRY:-}" ]]; then
        log_info "Pushing image to registry: $image_tag"
        docker push "$image_tag"
        log_success "Image pushed to registry"
    fi
fi

# Deploy the application
log_info "Deploying application to $environment..."
if [[ "$dry_run" == true ]]; then
    log_info "[DRY RUN] Would deploy application to $environment"
else
    case "$environment" in
        dev)
            # Deploy to local development
            log_info "Deploying to local development environment"
            "${PROJECT_ROOT}/scripts/docker/start.sh"
            ;;
        test)
            # Deploy to test environment
            log_info "Deploying to test environment"
            "${PROJECT_ROOT}/scripts/docker/test/setup.sh"
            ;;
        staging|prod)
            # Deploy to Kubernetes
            if [[ -z "${KUBE_CONFIG:-}" && "$force" != true ]]; then
                log_error "KUBE_CONFIG environment variable not set. Cannot deploy to $environment."
                exit 1
            fi
            
            log_info "Deploying to Kubernetes ($environment)"
            
            # Create or update Kubernetes deployment
            deployment_file="${PROJECT_ROOT}/docker/kubernetes/${environment}.yaml"
            
            if [[ ! -f "$deployment_file" ]]; then
                log_error "Kubernetes deployment file not found: $deployment_file"
                exit 1
            fi
            
            # Replace image tag in deployment file
            sed -i.bak "s|image:.*|image: ${image_tag}|g" "$deployment_file"
            
            # Apply Kubernetes deployment
            log_info "Applying Kubernetes deployment"
            kubectl apply -f "$deployment_file"
            
            # Verify deployment
            log_info "Verifying deployment..."
            kubectl rollout status deployment/notorm
            
            log_success "Deployment to $environment completed"
            ;;
    esac
fi

log_section "Next Steps"
log_info "1. Verify application is running correctly"
log_info "2. Check logs for any errors"
log_info "3. Run health checks"

if [[ "$environment" == "prod" ]]; then
    log_info "4. Monitor production metrics"
fi

exit 0