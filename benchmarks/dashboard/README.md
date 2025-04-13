# Uno Framework Benchmark Dashboard

This dashboard visualizes performance metrics from the Uno Framework benchmark tests.

## Features

- Module comparison visualization
- Performance trend analysis
- Scaling behavior analysis
- Detailed benchmark results table

## Installation

```bash
# Install required packages
pip install -r requirements.txt
```

## Usage

```bash
# Run the dashboard application
python app.py
```

Then open your browser to http://127.0.0.1:8050/ to view the dashboard.

## Configuration

To configure the data source, edit the `get_benchmark_data` function in `app.py`.
This function should connect to your benchmark results database or load results from files.

## Adding New Benchmark Data

After running new benchmarks, the data will automatically appear in the dashboard on the next refresh.
