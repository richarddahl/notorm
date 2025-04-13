# Benchmark Dashboard

## Overview

The Uno Framework Benchmark Dashboard provides a comprehensive visualization and analysis tool for monitoring performance across all framework modules. It allows developers and stakeholders to track performance trends, identify bottlenecks, and measure the impact of optimizations.

![Dashboard Overview](../assets/images/benchmark_dashboard_overview.png)

## Installation

The benchmark dashboard is located in the `benchmarks/dashboard` directory and can be run using the included script:

```bash
cd benchmarks/dashboard
./run_dashboard.sh
```

This will:
1. Create a virtual environment
2. Install dependencies
3. Process benchmark results
4. Start the dashboard server at http://127.0.0.1:8050/

## Dashboard Components

The dashboard consists of several key components:

### 1. Filter Controls

Located in the sidebar, these allow you to customize the dashboard view:

- **Module Selection**: Filter results by a specific module or view all modules
- **Benchmark Type**: Focus on operation speed, scaling behavior, or resource usage
- **Date Range**: Filter results within a specific timeframe
- **Update Button**: Refresh the dashboard with the selected filters

### 2. Summary Metrics

At the top of the main panel, displays key performance indicators:

- **Average Time**: Mean execution time across selected benchmarks
- **Maximum Time**: Slowest execution time in the selection
- **Minimum Time**: Fastest execution time in the selection
- **Success Rate**: Percentage of successful benchmark runs

### 3. Module Comparison Chart

Compares performance across different modules or operations:

- When viewing all modules: Shows average execution time by module
- When viewing a specific module: Shows average execution time by operation

### 4. Performance Trends Chart

Tracks performance changes over time:

- X-axis: Dates when benchmarks were run
- Y-axis: Execution time in milliseconds
- Color-coded by module or operation

### 5. Scaling Analysis Chart

Shows how performance scales with different dataset sizes:

- Grouped bars showing small, medium, and large dataset performance
- Helps identify operations with non-linear scaling characteristics

### 6. Detailed Results Table

Displays raw benchmark data for closer inspection:

- Date, module/operation, execution time, dataset size, and success rate
- Shows the most recent benchmark runs

## Using the Dashboard

### Tracking Performance Over Time

To monitor how performance changes over time:

1. Select the module of interest (or "All Modules")
2. Set benchmark type to "Operation Speed"
3. Choose a date range to monitor
4. Focus on the "Performance Trends" chart

This helps identify gradual performance degradation or improvements from optimizations.

### Comparing Module Performance

To compare performance across different modules:

1. Select "All Modules" from the module dropdown
2. Keep the default "All Types" for benchmark type
3. Examine the "Module Comparison" chart

This highlights which modules might need optimization priority.

### Analyzing Scaling Behavior

To understand how operations scale with dataset size:

1. Select the module of interest
2. Set benchmark type to "Scaling Behavior"
3. Focus on the "Scaling Analysis" chart

Operations showing disproportionate growth with dataset size indicate potential scaling issues.

### Investigating Specific Operations

To dive deep into specific operations:

1. Select the module containing the operation
2. Examine the operation-specific bars in the "Module Comparison" chart
3. Check the "Detailed Results" table for raw performance data

This helps identify exactly which operations are underperforming.

## Adding New Benchmark Data

The dashboard automatically processes benchmark results from pytest-benchmark. To add new data:

1. Run benchmarks with the JSON output flag:

```bash
pytest tests/benchmarks/test_your_module_performance.py --benchmark-json=.benchmarks/results_$(date +%Y%m%d).json
```

2. Process the results:

```bash
cd benchmarks/dashboard
python process_results.py
```

3. Restart or refresh the dashboard to see the new data.

## Configuration

The dashboard configuration is stored in `benchmarks/dashboard/config.json`. Key settings include:

- **Dashboard appearance**: Title, description, theme
- **Module configurations**: Display names, colors, operation lists
- **Performance thresholds**: Thresholds for performance classification
- **Alert thresholds**: Configuration for performance regression alerts

## Docker Deployment

For shared team access, you can deploy the dashboard using Docker:

```bash
cd benchmarks/dashboard
docker-compose up -d
```

This will build and start the dashboard container, making it available at http://server-address:8050/.

## Interpreting Results

When analyzing dashboard data, consider these guidelines:

1. **Performance Trends**: Look for sudden changes that might indicate regressions or improvements
2. **Module Comparisons**: Focus optimization efforts on the slowest modules
3. **Scaling Analysis**: Prioritize operations that show poor scaling characteristics
4. **Execution Time**: For user-facing operations, aim for sub-100ms response times

## Troubleshooting

If you encounter issues with the dashboard:

- **No data appears**: Ensure benchmark results exist in the `.benchmarks` directory
- **Processing errors**: Check Python error output for details
- **Missing modules**: Verify module configuration in `config.json`
- **Docker issues**: Check container logs with `docker-compose logs`

## Next Steps

Future dashboard enhancements planned include:

1. Automated performance regression detection
2. Benchmark comparison between branches
3. Resource utilization tracking (memory, CPU)
4. Integration with CI/CD for continuous performance monitoring