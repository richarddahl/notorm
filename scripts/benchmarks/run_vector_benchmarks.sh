#!/bin/bash
# -----------------------------------------------------------------------------
# Script Name: run_vector_benchmarks.sh
# Description: Run vector search benchmarks and report results
# Author: uno team
# -----------------------------------------------------------------------------
# Usage: ./run_vector_benchmarks.sh [options]
# 
# Options:
#   -h, --help       Display this help message
#   -v, --verbose    Enable verbose output
#   -o, --output DIR Output directory for benchmark results (default: ./benchmark_results)
#   -i, --iterations NUM Number of benchmark iterations (default: 3)
# -----------------------------------------------------------------------------

set -e  # Exit on error

# Script constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Source common functions
source "${SCRIPT_DIR}/../common/functions.sh"

# Default values
verbose=false
output_dir="${PROJECT_ROOT}/benchmark_results"
iterations=3

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help "$(basename "$0")" "Run vector search benchmarks and report results" "  -h, --help          Display this help message
  -v, --verbose       Enable verbose output
  -o, --output DIR    Output directory for benchmark results (default: ./benchmark_results)
  -i, --iterations    Number of benchmark iterations (default: 3)"
            exit 0
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -o|--output)
            output_dir="$2"
            shift 2
            ;;
        -i|--iterations)
            iterations="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            log_info "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Ensure the output directory exists
mkdir -p "$output_dir"

# Check if Docker is running and PostgreSQL is available
if docker_is_running; then
    log_info "Docker is running"
    
    # Check if PostgreSQL container is running
    if docker_container_running "pg16_uno"; then
        log_info "PostgreSQL container is running"
    else
        log_error "PostgreSQL container is not running"
        log_info "Start the container with: ./scripts/docker/start.sh"
        exit 1
    fi
else
    log_error "Docker is not running"
    log_info "Please start Docker and try again"
    exit 1
fi

# Main script logic
log_section "Vector Search Benchmark Runner"

# Run benchmark tests
log_info "Running vector search benchmarks..."

# Set environment variables
export ENV=test

# Run the benchmarks with pytest
timestamp=$(date +%Y%m%d_%H%M%S)
result_file="${output_dir}/vector_benchmark_${timestamp}.json"

cd "$PROJECT_ROOT"

if [[ "$verbose" == true ]]; then
    # Run with verbose output
    log_info "Running benchmarks with verbose output"
    python -m pytest tests/benchmarks/test_vector_search_performance.py -v --run-benchmark --benchmark-json="$result_file"
else
    # Run with minimal output
    log_info "Running benchmarks (use --verbose for more output)"
    python -m pytest tests/benchmarks/test_vector_search_performance.py --run-benchmark --benchmark-json="$result_file"
fi

# Check if benchmarks ran successfully
if [[ $? -eq 0 ]]; then
    log_success "Benchmarks completed successfully"
    log_info "Results saved to: $result_file"
    
    # Generate summary if jq is available
    if command -v jq &> /dev/null; then
        log_info "Benchmark Summary:"
        jq -r '.benchmarks[] | "\(.name): \(.stats.mean) seconds (±\(.stats.stddev))"' "$result_file" | sort
        
        # Save summary to a text file
        summary_file="${output_dir}/vector_benchmark_summary_${timestamp}.txt"
        echo "Vector Search Benchmark Summary ($(date))" > "$summary_file"
        echo "================================================" >> "$summary_file"
        jq -r '.benchmarks[] | "\(.name): \(.stats.mean) seconds (±\(.stats.stddev))"' "$result_file" | sort >> "$summary_file"
        echo "" >> "$summary_file"
        echo "Full details in: $result_file" >> "$summary_file"
        
        log_info "Summary saved to: $summary_file"
    else
        log_info "Install jq to see a formatted summary of benchmark results"
    fi
else
    log_error "Benchmarks failed to run correctly"
    exit 1
fi

log_section "Next Steps"
log_info "1. Analyze results in $result_file"
log_info "2. Compare with previous benchmarks to detect performance changes"
log_info "3. Profile bottlenecks with: python -m cProfile -o profile.out examples/vector_search/vector_search_example.py"

exit 0