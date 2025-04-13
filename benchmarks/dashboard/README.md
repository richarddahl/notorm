# Uno Framework Benchmark Dashboard

A visualization dashboard for monitoring and analyzing benchmark performance metrics across the Uno Framework modules.

## Features

- **Module Comparison**: Compare performance across different modules
- **Performance Trends**: Track performance changes over time
- **Scaling Analysis**: Visualize how operations scale with different dataset sizes
- **Detailed Results**: View detailed benchmark results for specific operations
- **Custom Filtering**: Filter by module, benchmark type, and date range

## Installation

1. Ensure you have Python 3.8+ installed
2. Clone this repository
3. Run the setup script:

```bash
./run_dashboard.sh
```

This will:
- Create a virtual environment
- Install required dependencies
- Process benchmark results
- Start the dashboard server

## Usage

After starting the dashboard, access it at: http://127.0.0.1:8050/

### Dashboard Controls

- **Module Selection**: Filter results by specific module or view all modules
- **Benchmark Type**: Select specific benchmark types (operation speed, scaling behavior, resource usage)
- **Date Range**: Filter results within a specific date range
- **Update Button**: Refresh the dashboard with the selected filters

## Data Processing

The dashboard uses benchmark data from pytest-benchmark runs. To process new benchmark results:

```bash
python process_results.py --results-dir PATH_TO_RESULTS --output OUTPUT_FILE --summaries SUMMARIES_DIR
```

Parameters:
- `--results-dir`: Directory containing benchmark JSON results (default: `../.benchmarks`)
- `--output`: Output CSV file for processed benchmark data (default: `./data/benchmark_results.csv`)
- `--summaries`: Directory to store module summary files (default: `./data/summaries`)

## Configuration

Dashboard settings can be customized by editing `config.json`:

- **Dashboard Title and Description**: Customize the dashboard appearance
- **Module Colors and Names**: Define colors and display names for modules
- **Operation Lists**: Define operations for each module
- **Performance Thresholds**: Set thresholds for performance classification
- **Alert Thresholds**: Configure thresholds for performance regression alerts

## Integration with CI/CD

To integrate the dashboard with CI/CD pipelines:

1. Add a step to run benchmarks and save results:

```bash
pytest tests/benchmarks --benchmark-json=.benchmarks/results_$(date +%Y%m%d).json
```

2. Process results and generate summaries:

```bash
python benchmarks/dashboard/process_results.py
```

3. Archive the results for dashboard use:

```bash
cp -r benchmarks/dashboard/data /path/to/artifacts
```

## Benchmark Performance Analysis

The dashboard helps identify:

1. **Performance Regressions**: Detect when operations become slower over time
2. **Scaling Issues**: Identify operations that don't scale linearly with dataset size
3. **Optimization Opportunities**: Find the slowest operations for prioritizing optimizations
4. **Impact of Changes**: Measure the impact of code changes on performance

## Adding New Benchmarks

When adding new benchmark modules:

1. Add the module configuration to `config.json`
2. Run the new benchmarks with the `--benchmark-json` flag
3. Process the results using `process_results.py`
4. Restart the dashboard to see the new module data

## Interpreting Results

- **Green**: Performance better than historical average
- **Yellow**: Performance within normal range
- **Red**: Performance regression detected
- **Gray**: Insufficient data for comparison

## Troubleshooting

- **Missing Data**: Ensure benchmark results are in the expected location and format
- **Processing Errors**: Check the Python error output for details on processing issues
- **Display Issues**: Verify that the dashboard is running on the correct port
- **Configuration Problems**: Validate that config.json has the correct format

## Contributing

To improve the dashboard:

1. Fork the repository
2. Make your changes
3. Submit a pull request with a clear description of the improvements