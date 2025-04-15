#!/usr/bin/env python3
"""
Integration test benchmark runner.

This script runs all performance-related tests in the integration test suite
and generates a summary report of the results.
"""

import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


BENCHMARK_PATTERNS = [
    "test_*_performance.py",          # Dedicated performance test files
    "*test_*_benchmark*",             # Any test with benchmark in the name
    "*test_performance_*"             # Performance-specific test methods
]

# Performance test functions in regular test files
BENCHMARK_FUNCTIONS = [
    "test_query_optimizer.py::test_slow_query_detection",
    "test_query_optimizer.py::test_execute_optimized_query",
    "test_distributed_cache.py::test_high_concurrency_cache_access",
    "test_batch_operations.py::test_performance_comparison",
    "test_vector_search.py::test_search_performance",
    "test_connection_pool.py::test_connection_pool_performance"
]


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run integration test benchmarks")
    parser.add_argument("--output", "-o", default="benchmark_results.json",
                       help="Output file for benchmark results")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--csv", action="store_true",
                       help="Also output results as CSV")
    parser.add_argument("--compare", "-c", default=None,
                       help="Compare with previous benchmark results file")
    return parser.parse_args()


def find_benchmark_tests(root_dir: str = "tests/integration") -> List[str]:
    """Find all benchmark tests in the integration test directory."""
    benchmark_tests = []
    
    # Add known benchmark functions
    benchmark_tests.extend(BENCHMARK_FUNCTIONS)
    
    # Find matching files
    root = Path(root_dir)
    for pattern in BENCHMARK_PATTERNS:
        for path in root.glob(pattern):
            if path.is_file():
                benchmark_tests.append(str(path.relative_to(root.parent.parent)))
    
    return benchmark_tests


def run_benchmark(test_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Run a single benchmark test and return the results."""
    print(f"Running benchmark: {test_path}")
    
    start_time = time.time()
    cmd = ["pytest", test_path, "--run-integration", "--run-pgvector", "-v"]
    
    try:
        if verbose:
            # Run with output visible
            result = subprocess.run(cmd, check=False)
            success = result.returncode == 0
        else:
            # Capture output
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            success = result.returncode == 0
        
        duration = time.time() - start_time
        
        # Extract metrics from output if they exist
        metrics = {}
        if hasattr(result, "stdout") and result.stdout:
            # Look for lines with benchmark metrics
            for line in result.stdout.splitlines():
                if "BENCHMARK:" in line:
                    try:
                        # Parse benchmark output format: BENCHMARK: name=value
                        parts = line.split("BENCHMARK:")[1].strip().split("=")
                        if len(parts) == 2:
                            name, value = parts[0].strip(), parts[1].strip()
                            try:
                                # Try to convert to number
                                metrics[name] = float(value)
                            except ValueError:
                                metrics[name] = value
                    except Exception:
                        pass
        
        return {
            "test": test_path,
            "success": success,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
    except Exception as e:
        return {
            "test": test_path,
            "success": False,
            "duration": time.time() - start_time,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "metrics": {}
        }


def run_all_benchmarks(verbose: bool = False) -> List[Dict[str, Any]]:
    """Run all benchmark tests and return results."""
    results = []
    
    # Find all benchmark tests
    benchmark_tests = find_benchmark_tests()
    
    # Run each test
    for test in benchmark_tests:
        result = run_benchmark(test, verbose)
        results.append(result)
    
    return results


def save_results(results: List[Dict[str, Any]], output_file: str, csv_output: bool = False):
    """Save benchmark results to file."""
    # Save JSON results
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"Results saved to {output_file}")
    
    # Save CSV if requested
    if csv_output:
        csv_file = output_file.replace(".json", ".csv")
        with open(csv_file, "w") as f:
            # Write header
            f.write("Test,Success,Duration,Timestamp")
            
            # Find all metric names
            metric_names = set()
            for result in results:
                metric_names.update(result.get("metrics", {}).keys())
            
            # Add metric names to header
            for name in sorted(metric_names):
                f.write(f",{name}")
            f.write("\n")
            
            # Write data rows
            for result in results:
                f.write(f"{result['test']},{result['success']},{result['duration']},{result['timestamp']}")
                
                # Add metrics
                metrics = result.get("metrics", {})
                for name in sorted(metric_names):
                    value = metrics.get(name, "")
                    f.write(f",{value}")
                f.write("\n")
        
        print(f"CSV results saved to {csv_file}")


def compare_results(current_results: List[Dict[str, Any]], previous_file: str):
    """Compare current results with previous benchmark results."""
    try:
        with open(previous_file, "r") as f:
            previous_data = json.load(f)
            previous_results = previous_data.get("results", [])
        
        # Create lookup for previous results
        prev_lookup = {r["test"]: r for r in previous_results}
        
        print("\n=== Benchmark Comparison ===")
        print(f"Previous: {previous_file} ({previous_data.get('timestamp', 'unknown')})")
        print(f"Current:  {datetime.now().isoformat()}")
        print("\n{:<50} {:<10} {:<10} {:<10}".format("Test", "Previous", "Current", "Change"))
        print("-" * 80)
        
        for result in current_results:
            test_name = result["test"]
            current_duration = result["duration"]
            
            if test_name in prev_lookup:
                prev_result = prev_lookup[test_name]
                prev_duration = prev_result.get("duration", 0)
                
                if prev_duration > 0:
                    change_pct = (current_duration - prev_duration) / prev_duration * 100
                    change_str = f"{change_pct:+.1f}%"
                else:
                    change_str = "N/A"
                
                print("{:<50} {:<10.3f} {:<10.3f} {:<10}".format(
                    test_name, prev_duration, current_duration, change_str
                ))
                
                # Compare metrics if available
                current_metrics = result.get("metrics", {})
                prev_metrics = prev_result.get("metrics", {})
                
                for metric_name in sorted(set(current_metrics.keys()) | set(prev_metrics.keys())):
                    if metric_name in current_metrics and metric_name in prev_metrics:
                        curr_val = current_metrics[metric_name]
                        prev_val = prev_metrics[metric_name]
                        
                        if isinstance(curr_val, (int, float)) and isinstance(prev_val, (int, float)):
                            if prev_val > 0:
                                change_pct = (curr_val - prev_val) / prev_val * 100
                                change_str = f"{change_pct:+.1f}%"
                            else:
                                change_str = "N/A"
                            
                            print("  {:<48} {:<10.3f} {:<10.3f} {:<10}".format(
                                metric_name, prev_val, curr_val, change_str
                            ))
            else:
                print("{:<50} {:<10} {:<10.3f} {:<10}".format(
                    test_name, "N/A", current_duration, "NEW"
                ))
        
        # Find removed tests
        for test_name in prev_lookup:
            if not any(r["test"] == test_name for r in current_results):
                print("{:<50} {:<10.3f} {:<10} {:<10}".format(
                    test_name, prev_lookup[test_name].get("duration", 0), "N/A", "REMOVED"
                ))
        
    except Exception as e:
        print(f"Error comparing results: {e}")


def main():
    """Main function to run benchmarks."""
    args = parse_args()
    
    print("=== UNO Integration Test Benchmarks ===")
    
    # Run all benchmarks
    results = run_all_benchmarks(args.verbose)
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Tests run: {len(results)}")
    successful = sum(1 for r in results if r["success"])
    print(f"Successful: {successful}/{len(results)}")
    print(f"Total duration: {sum(r['duration'] for r in results):.2f} seconds")
    
    # Save results
    save_results(results, args.output, args.csv)
    
    # Compare with previous results if requested
    if args.compare and os.path.exists(args.compare):
        compare_results(results, args.compare)
    
    # Return success if all tests passed
    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())