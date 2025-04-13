#!/bin/bash
# Benchmark Dashboard CI Integration Script

# Exit on error
set -e

# Configuration
BENCHMARKS_DIR=".benchmarks"
DASHBOARD_DIR="benchmarks/dashboard"
ARTIFACTS_DIR="benchmark_artifacts"
DATE_TAG=$(date +%Y%m%d)
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
COMMIT_ID=$(git rev-parse --short HEAD)

# Create directories
mkdir -p "$BENCHMARKS_DIR"
mkdir -p "$ARTIFACTS_DIR"

# Display information
echo "Running benchmarks for branch: $BRANCH_NAME ($COMMIT_ID)"
echo "Date: $DATE_TAG"

# Run all benchmarks and save results
echo "Running benchmarks..."
python -m pytest tests/benchmarks --benchmark-json="$BENCHMARKS_DIR/results_${BRANCH_NAME}_${DATE_TAG}_${COMMIT_ID}.json"

# Generate comparison against main branch if this is a feature branch
if [ "$BRANCH_NAME" != "main" ] && [ -f "$BENCHMARKS_DIR/results_main_latest.json" ]; then
    echo "Generating comparison against main branch..."
    python -m pytest-benchmark compare "$BENCHMARKS_DIR/results_main_latest.json" "$BENCHMARKS_DIR/results_${BRANCH_NAME}_${DATE_TAG}_${COMMIT_ID}.json" --csv="$ARTIFACTS_DIR/comparison_${BRANCH_NAME}_vs_main.csv"
fi

# If this is the main branch, create a "latest" copy
if [ "$BRANCH_NAME" = "main" ]; then
    echo "Updating main branch latest results..."
    cp "$BENCHMARKS_DIR/results_${BRANCH_NAME}_${DATE_TAG}_${COMMIT_ID}.json" "$BENCHMARKS_DIR/results_main_latest.json"
fi

# Process results for dashboard
echo "Processing benchmark results for dashboard..."
cd "$DASHBOARD_DIR"
python process_results.py --results-dir="../../$BENCHMARKS_DIR" --output="../../$ARTIFACTS_DIR/benchmark_results_${BRANCH_NAME}_${DATE_TAG}.csv" --summaries="../../$ARTIFACTS_DIR/summaries_${BRANCH_NAME}_${DATE_TAG}"

# Create dashboard snapshot
echo "Creating dashboard snapshot..."
mkdir -p "../../$ARTIFACTS_DIR/dashboard_snapshot"
cp -r app.py config.json assets "../../$ARTIFACTS_DIR/dashboard_snapshot/"
cp "../../$ARTIFACTS_DIR/benchmark_results_${BRANCH_NAME}_${DATE_TAG}.csv" "../../$ARTIFACTS_DIR/dashboard_snapshot/data/benchmark_results.csv"
cp -r "../../$ARTIFACTS_DIR/summaries_${BRANCH_NAME}_${DATE_TAG}" "../../$ARTIFACTS_DIR/dashboard_snapshot/data/summaries"

echo "Benchmark process complete. Results stored in $ARTIFACTS_DIR"

# Generate performance report
echo "Generating performance report..."
cat > "../../$ARTIFACTS_DIR/performance_report_${BRANCH_NAME}_${DATE_TAG}.md" << EOF
# Performance Benchmark Report

## Overview
- **Branch**: $BRANCH_NAME
- **Commit**: $COMMIT_ID
- **Date**: $DATE_TAG

## Summary
$(python -c "
import json, os, sys
latest_file = sorted([f for f in os.listdir('../../$BENCHMARKS_DIR') if f.startswith('results_${BRANCH_NAME}_')])[-1]
with open(os.path.join('../../$BENCHMARKS_DIR', latest_file)) as f:
    data = json.load(f)
    benchmarks = data.get('benchmarks', [])
    if benchmarks:
        total = len(benchmarks)
        avg_time = sum(b['stats']['mean'] for b in benchmarks) / total * 1000
        min_time = min(b['stats']['min'] for b in benchmarks) * 1000
        max_time = max(b['stats']['max'] for b in benchmarks) * 1000
        slowest = sorted([(b['name'], b['stats']['mean'] * 1000) for b in benchmarks], key=lambda x: x[1], reverse=True)[:5]
        print(f'- **Total Benchmarks**: {total}')
        print(f'- **Average Time**: {avg_time:.2f} ms')
        print(f'- **Minimum Time**: {min_time:.2f} ms')
        print(f'- **Maximum Time**: {max_time:.2f} ms')
        print('\\n## Slowest Operations')
        for name, time in slowest:
            print(f'- **{name}**: {time:.2f} ms')
    else:
        print('No benchmark data available')
")

## Module Performance
$(python -c "
import os, json, sys
summaries_dir = '../../$ARTIFACTS_DIR/summaries_${BRANCH_NAME}_${DATE_TAG}'
if os.path.exists(os.path.join(summaries_dir, 'all_modules_summary.json')):
    with open(os.path.join(summaries_dir, 'all_modules_summary.json')) as f:
        data = json.load(f)
        modules = data.get('module_summaries', {})
        print('| Module | Operations | Avg Time (ms) | Max Time (ms) |')
        print('|--------|------------|---------------|---------------|')
        for module, summary in modules.items():
            print(f'| {module} | {summary.get(\"operation_count\", 0)} | {summary.get(\"mean_execution_time\", 0):.2f} | {summary.get(\"max_execution_time\", 0):.2f} |')
else:
    print('Module summary data not available')
")

## Performance Comparison
$([ "$BRANCH_NAME" != "main" ] && [ -f "$ARTIFACTS_DIR/comparison_${BRANCH_NAME}_vs_main.csv" ] && python -c "
import os, csv, sys
with open('../../$ARTIFACTS_DIR/comparison_${BRANCH_NAME}_vs_main.csv') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    if rows:
        print('| Benchmark | This Branch (ms) | Main Branch (ms) | Difference (%) |')
        print('|-----------|------------------|------------------|----------------|')
        for row in rows[:10]:  # Show top 10 for brevity
            name = row.get('name', 'Unknown')
            new = float(row.get('new', 0)) * 1000
            old = float(row.get('old', 0)) * 1000
            diff = ((new - old) / old * 100) if old else 0
            print(f'| {name} | {new:.2f} | {old:.2f} | {diff:+.2f}% |')
    else:
        print('No comparison data available')
" || echo "Comparison with main branch not available")

## Next Steps
- Review slowest operations for optimization opportunities
- Check operations with significant performance differences
- Consider scaling behavior for large dataset operations
EOF

echo "Performance report generated: $ARTIFACTS_DIR/performance_report_${BRANCH_NAME}_${DATE_TAG}.md"