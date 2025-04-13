"""
Benchmark results processor for Uno Framework.

This script processes the JSON output from pytest-benchmark into a format
suitable for visualization in the dashboard.
"""
import os
import json
import glob
import argparse
from datetime import datetime
import pandas as pd


def find_benchmark_files(results_dir):
    """Find all benchmark JSON result files in the given directory."""
    # Find all .json files in the directory
    json_files = glob.glob(os.path.join(results_dir, "*.json"))
    return [f for f in json_files if os.path.isfile(f)]


def parse_benchmark_file(file_path):
    """Parse a benchmark JSON file and extract relevant metrics."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Extract commit information
    commit_info = data.get('commit_info', {})
    commit_date = commit_info.get('time', datetime.now().isoformat())
    
    # Try to parse the date
    try:
        date = datetime.fromisoformat(commit_date.replace('Z', '+00:00'))
    except ValueError:
        # Fall back to file modification time if commit date parsing fails
        date = datetime.fromtimestamp(os.path.getmtime(file_path))
    
    # Extract benchmark results
    benchmarks = data.get('benchmarks', [])
    results = []
    
    for bench in benchmarks:
        # Extract test name and parameters
        fullname = bench.get('fullname', '')
        name = bench.get('name', '')
        
        # Parse module and operation from the test name
        module = "unknown"
        operation = name
        
        # Try to extract module from test file name
        if "test_" in fullname:
            test_file = fullname.split('::')[0]
            if "test_" in test_file:
                module_name = test_file.split('test_')[1].split('_performance')[0]
                module = module_name
        
        # Extract parameters if any
        params = bench.get('params', {})
        dataset_size = params.get('size', 'medium')
        if isinstance(dataset_size, (int, float)):
            # Convert numeric sizes to categories
            if dataset_size <= 100:
                dataset_size = 'small'
            elif dataset_size <= 1000:
                dataset_size = 'medium'
            else:
                dataset_size = 'large'
        
        # Extract performance metrics
        stats = bench.get('stats', {})
        result = {
            'date': date,
            'module': module,
            'operation': operation,
            'execution_time': stats.get('mean', 0) * 1000,  # Convert seconds to ms
            'min_time': stats.get('min', 0) * 1000,
            'max_time': stats.get('max', 0) * 1000,
            'stddev': stats.get('stddev', 0) * 1000,
            'median': stats.get('median', 0) * 1000,
            'dataset_size': dataset_size,
            'success_rate': 100,  # Assuming all benchmarks that ran were successful
            'iterations': stats.get('iterations', 0),
            'commit_id': commit_info.get('id', 'unknown'),
            'commit_branch': commit_info.get('branch', 'unknown')
        }
        
        results.append(result)
    
    return results


def process_all_benchmarks(results_dir, output_file):
    """Process all benchmark files and compile them into a single dataset."""
    benchmark_files = find_benchmark_files(results_dir)
    all_results = []
    
    for file_path in benchmark_files:
        try:
            results = parse_benchmark_file(file_path)
            all_results.extend(results)
            print(f"Processed {file_path}, found {len(results)} benchmark results")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    if all_results:
        # Convert to DataFrame and save
        df = pd.DataFrame(all_results)
        df.to_csv(output_file, index=False)
        print(f"Saved {len(all_results)} benchmark results to {output_file}")
        return df
    else:
        print("No benchmark results found")
        return None


def create_module_summaries(df, output_dir):
    """Create summary files for each module."""
    if df is None or df.empty:
        print("No data available for summaries")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Group by module and get statistics
    module_summaries = {}
    
    for module, group in df.groupby('module'):
        summary = {
            'operation_count': len(group['operation'].unique()),
            'total_benchmarks': len(group),
            'mean_execution_time': group['execution_time'].mean(),
            'median_execution_time': group['execution_time'].median(),
            'min_execution_time': group['execution_time'].min(),
            'max_execution_time': group['execution_time'].max(),
            'latest_date': group['date'].max().strftime("%Y-%m-%d"),
            'operations': {}
        }
        
        # Get statistics for each operation
        for op, op_group in group.groupby('operation'):
            summary['operations'][op] = {
                'mean_execution_time': op_group['execution_time'].mean(),
                'median_execution_time': op_group['execution_time'].median(),
                'min_execution_time': op_group['execution_time'].min(),
                'max_execution_time': op_group['execution_time'].max(),
                'benchmark_count': len(op_group)
            }
        
        module_summaries[module] = summary
        
        # Save individual module summary
        with open(os.path.join(output_dir, f"{module}_summary.json"), 'w') as f:
            json.dump(summary, f, indent=2)
    
    # Save overall summary
    with open(os.path.join(output_dir, "all_modules_summary.json"), 'w') as f:
        json.dump({
            'module_count': len(module_summaries),
            'total_operations': sum(s['operation_count'] for s in module_summaries.values()),
            'total_benchmarks': len(df),
            'module_summaries': module_summaries
        }, f, indent=2)
    
    print(f"Created summaries for {len(module_summaries)} modules in {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Process benchmark results for visualization")
    parser.add_argument("--results-dir", dest="results_dir", default="../.benchmarks",
                        help="Directory containing benchmark JSON results")
    parser.add_argument("--output", dest="output_file", default="./data/benchmark_results.csv",
                        help="Output CSV file for processed benchmark data")
    parser.add_argument("--summaries", dest="summaries_dir", default="./data/summaries",
                        help="Directory to store module summary files")
    parser.add_argument("--sample", dest="use_sample", action="store_true",
                        help="Use sample benchmark data for demonstration")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    
    # First try normal benchmark files
    df = process_all_benchmarks(args.results_dir, args.output_file)
    
    # If no benchmarks found or --sample flag is used, try sample file
    if df is None or df.empty or args.use_sample:
        print("Using sample benchmark data...")
        sample_file = "./data/sample_benchmark.json"
        if os.path.exists(sample_file):
            try:
                results = parse_benchmark_file(sample_file)
                if results:
                    df = pd.DataFrame(results)
                    df.to_csv(args.output_file, index=False)
                    print(f"Saved {len(results)} sample benchmark results to {args.output_file}")
            except Exception as e:
                print(f"Error processing sample file: {e}")
    
    # Create module summaries
    create_module_summaries(df, args.summaries_dir)


if __name__ == "__main__":
    main()