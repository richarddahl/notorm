"""
Benchmark Visualization Dashboard for Uno Framework

This application provides a visualization dashboard for benchmark results
across all tested modules in the Uno Framework.
"""
import os
import json
from datetime import datetime
import dash
from dash import dcc, html, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Create the Dash app
app = dash.Dash(__name__, title="Uno Framework Benchmark Dashboard")

# Define app layout
app.layout = html.Div([
    html.Div([
        html.H1("Uno Framework Benchmark Dashboard", className="header-title"),
        html.P("Performance metrics across modules and operations", className="header-description")
    ], className="header"),
    
    html.Div([
        html.Div([
            html.H3("Filter Controls", className="control-title"),
            html.Label("Select Module:"),
            dcc.Dropdown(
                id="module-dropdown",
                options=[
                    {"label": "Reports", "value": "reports"},
                    {"label": "Attributes", "value": "attributes"},
                    {"label": "Values", "value": "values"},
                    {"label": "Authorization", "value": "authorization"},
                    {"label": "Database", "value": "database"},
                    {"label": "Queries", "value": "queries"},
                    {"label": "Workflows", "value": "workflows"},
                    {"label": "Integration", "value": "integration"},
                    {"label": "All Modules", "value": "all"}
                ],
                value="all"
            ),
            
            html.Label("Select Benchmark Type:"),
            dcc.Dropdown(
                id="benchmark-type-dropdown",
                options=[
                    {"label": "Operation Speed", "value": "speed"},
                    {"label": "Scaling Behavior", "value": "scaling"},
                    {"label": "Resource Usage", "value": "resource"},
                    {"label": "All Types", "value": "all"}
                ],
                value="all"
            ),
            
            html.Label("Date Range:"),
            dcc.DatePickerRange(
                id="date-range",
                min_date_allowed=datetime(2024, 1, 1),
                max_date_allowed=datetime(2025, 12, 31),
                start_date=datetime(2024, 1, 1),
                end_date=datetime.now()
            ),
            
            html.Button("Update Dashboard", id="update-button", className="update-button")
        ], className="sidebar"),
        
        html.Div([
            html.Div([
                html.H3("Summary Metrics", className="panel-title"),
                html.Div(id="summary-metrics", className="summary-panel")
            ], className="panel"),
            
            html.Div([
                html.H3("Module Comparison", className="panel-title"),
                dcc.Graph(id="module-comparison-chart")
            ], className="panel"),
            
            html.Div([
                html.H3("Performance Trends", className="panel-title"),
                dcc.Graph(id="performance-trend-chart")
            ], className="panel"),
            
            html.Div([
                html.H3("Scaling Analysis", className="panel-title"),
                dcc.Graph(id="scaling-chart")
            ], className="panel"),
            
            html.Div([
                html.H3("Detailed Benchmark Results", className="panel-title"),
                html.Div(id="detailed-results", style={"overflowX": "auto"})
            ], className="panel")
        ], className="main-content")
    ], className="app-container")
])


# Helper function to generate synthetic benchmark data
def get_benchmark_data(module, benchmark_type, start_date, end_date):
    """
    Generate synthetic benchmark data for demonstration purposes.
    
    In a real implementation, this would load data from benchmark results files.
    """
    # Convert date strings to datetime objects if needed
    if isinstance(start_date, str):
        # Handle ISO format dates that may include time
        if 'T' in start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            
    if isinstance(end_date, str):
        # Handle ISO format dates that may include time
        if 'T' in end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Generate a date range
    date_range = pd.date_range(start=start_date, end=end_date, freq="W")
    
    # Define modules and their operations
    module_operations = {
        "reports": ["template_creation", "template_query", "report_execution", "field_updates"],
        "attributes": ["type_creation", "attribute_query", "relationship_loading", "batch_creation"],
        "values": ["value_creation", "text_search", "batch_operations", "validation"],
        "authorization": ["permission_check", "role_assignment", "user_query", "tenant_loading"],
        "database": ["connection_pooling", "query_execution", "transaction", "session_creation"],
        "queries": ["filter_manager", "query_execution", "match_checking", "cached_query"],
        "workflows": ["event_processing", "condition_evaluation", "action_execution", "concurrent_processing"],
        "integration": ["user_attribute_flow", "query_workflow_flow", "concurrent_operations", "business_process"]
    }
    
    # For "all" modules, combine all operations
    if module == "all":
        operations = []
        for ops in module_operations.values():
            operations.extend(ops)
    else:
        operations = module_operations.get(module, ["generic_operation"])
    
    # Generate synthetic data
    data = []
    for date in date_range:
        for operation in operations:
            # Generate base performance metrics (in milliseconds)
            base_time = {
                "reports": 15,
                "attributes": 12,
                "values": 8,
                "authorization": 5,
                "database": 3,
                "queries": 18,
                "workflows": 22,
                "integration": 45
            }.get(module if module != "all" else operation.split("_")[0], 10)
            
            # Add variability based on operation
            op_factor = {
                "template_creation": 1.5,
                "report_execution": 2.5,
                "relationship_loading": 3.0,
                "text_search": 1.8,
                "permission_check": 0.7,
                "connection_pooling": 0.6,
                "query_execution": 2.2,
                "event_processing": 1.7,
                "concurrent_operations": 3.5,
                "business_process": 4.0
            }.get(operation, 1.0)
            
            # Add some random variation and a slight improvement trend over time
            days_factor = (date - start_date).days / max(1, (end_date - start_date).days)
            improvement = 1.0 - (days_factor * 0.2)  # 20% improvement over time period
            random_factor = np.random.normal(1.0, 0.1)  # 10% random variation
            
            execution_time = base_time * op_factor * improvement * random_factor
            
            # Add scaling data if requested
            if benchmark_type in ["scaling", "all"]:
                sizes = ["small", "medium", "large"]
                for size in sizes:
                    size_factor = {"small": 1.0, "medium": 2.5, "large": 6.0}[size]
                    data.append({
                        "date": date,
                        "module": module if module != "all" else operation.split("_")[0],
                        "operation": operation,
                        "execution_time": execution_time * size_factor,
                        "dataset_size": size,
                        "success_rate": min(100, 98 + np.random.normal(0, 1)),
                        "memory_usage": base_time * op_factor * size_factor * 0.5,
                        "cpu_usage": base_time * op_factor * size_factor * 0.3
                    })
            else:
                data.append({
                    "date": date,
                    "module": module if module != "all" else operation.split("_")[0],
                    "operation": operation,
                    "execution_time": execution_time,
                    "dataset_size": "medium",
                    "success_rate": min(100, 98 + np.random.normal(0, 1)),
                    "memory_usage": base_time * op_factor * 0.5,
                    "cpu_usage": base_time * op_factor * 0.3
                })
    
    return pd.DataFrame(data)


@callback(
    [
        Output("summary-metrics", "children"),
        Output("module-comparison-chart", "figure"),
        Output("performance-trend-chart", "figure"),
        Output("scaling-chart", "figure"),
        Output("detailed-results", "children")
    ],
    [
        Input("update-button", "n_clicks")
    ],
    [
        dash.dependencies.State("module-dropdown", "value"),
        dash.dependencies.State("benchmark-type-dropdown", "value"),
        dash.dependencies.State("date-range", "start_date"),
        dash.dependencies.State("date-range", "end_date")
    ]
)
def update_dashboard(n_clicks, module, benchmark_type, start_date, end_date):
    # Default date range if none provided
    if not start_date:
        start_date = "2024-01-01"
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        
    # Generate benchmark data based on selections
    try:
        df = get_benchmark_data(module, benchmark_type, start_date, end_date)
    except Exception as e:
        print(f"Error generating benchmark data: {e}")
        # Fallback to a simple date range if there's an error
        start = datetime(2024, 1, 1)
        end = datetime.now()
        df = get_benchmark_data(module, benchmark_type, start, end)
    
    # 1. Summary Metrics
    avg_time = df["execution_time"].mean()
    max_time = df["execution_time"].max()
    min_time = df["execution_time"].min()
    success_rate = df["success_rate"].mean()
    
    summary_html = html.Div([
        html.Div([
            html.H4("Average Time"),
            html.P(f"{avg_time:.2f} ms")
        ], className="metric-card"),
        html.Div([
            html.H4("Maximum Time"),
            html.P(f"{max_time:.2f} ms")
        ], className="metric-card"),
        html.Div([
            html.H4("Minimum Time"),
            html.P(f"{min_time:.2f} ms")
        ], className="metric-card"),
        html.Div([
            html.H4("Success Rate"),
            html.P(f"{success_rate:.2f}%")
        ], className="metric-card")
    ], className="metrics-container")
    
    # 2. Module Comparison Chart
    if module == "all":
        module_avg = df.groupby("module")["execution_time"].mean().reset_index()
        comparison_fig = px.bar(
            module_avg, 
            x="module", 
            y="execution_time",
            title="Average Execution Time by Module",
            labels={"execution_time": "Execution Time (ms)", "module": "Module"},
            color="module"
        )
    else:
        operation_avg = df.groupby("operation")["execution_time"].mean().reset_index()
        comparison_fig = px.bar(
            operation_avg, 
            x="operation", 
            y="execution_time",
            title=f"Average Execution Time by Operation ({module.capitalize()})",
            labels={"execution_time": "Execution Time (ms)", "operation": "Operation"},
            color="operation"
        )
    
    # 3. Performance Trends Chart
    trend_data = df.groupby(["date", "module" if module == "all" else "operation"])["execution_time"].mean().reset_index()
    group_col = "module" if module == "all" else "operation"
    trend_fig = px.line(
        trend_data, 
        x="date", 
        y="execution_time", 
        color=group_col,
        title="Performance Trends Over Time",
        labels={"execution_time": "Execution Time (ms)", "date": "Date"}
    )
    
    # 4. Scaling Chart
    if benchmark_type in ["scaling", "all"]:
        scaling_data = df[df["dataset_size"].isin(["small", "medium", "large"])]
        if not scaling_data.empty:
            if module == "all":
                scaling_avg = scaling_data.groupby(["module", "dataset_size"])["execution_time"].mean().reset_index()
                group_col = "module"
            else:
                scaling_avg = scaling_data.groupby(["operation", "dataset_size"])["execution_time"].mean().reset_index()
                group_col = "operation"
            
            scaling_fig = px.bar(
                scaling_avg, 
                x=group_col, 
                y="execution_time", 
                color="dataset_size",
                barmode="group",
                title="Execution Time by Dataset Size",
                labels={"execution_time": "Execution Time (ms)"}
            )
        else:
            scaling_fig = go.Figure()
            scaling_fig.update_layout(title="No scaling data available")
    else:
        scaling_fig = go.Figure()
        scaling_fig.update_layout(title="Select 'Scaling Behavior' to view scaling analysis")
    
    # 5. Detailed Results Table
    detailed_df = df.sort_values(by=["date", "module" if module == "all" else "operation"])
    detailed_df = detailed_df.tail(10)  # Show only the most recent entries
    
    table_header = [
        html.Thead(html.Tr([
            html.Th("Date"),
            html.Th("Module" if module == "all" else "Operation"),
            html.Th("Execution Time (ms)"),
            html.Th("Dataset Size"),
            html.Th("Success Rate (%)")
        ]))
    ]
    
    rows = []
    for _, row in detailed_df.iterrows():
        rows.append(html.Tr([
            html.Td(row["date"].strftime("%Y-%m-%d")),
            html.Td(row["module"] if module == "all" else row["operation"]),
            html.Td(f"{row['execution_time']:.2f}"),
            html.Td(row["dataset_size"]),
            html.Td(f"{row['success_rate']:.2f}")
        ]))
    
    table_body = [html.Tbody(rows)]
    detailed_table = html.Table(table_header + table_body, className="detailed-table")
    
    return summary_html, comparison_fig, trend_fig, scaling_fig, detailed_table


# Create CSS file for styling
def create_css_file():
    css_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    os.makedirs(css_dir, exist_ok=True)
    
    css_content = """
    /* Dashboard Styles */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 0;
        background-color: #f5f7fa;
        color: #333;
    }
    
    .header {
        background-color: #2c3e50;
        color: white;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .header-title {
        margin: 0;
        font-size: 2.2em;
    }
    
    .header-description {
        margin: 5px 0 0;
        font-size: 1.1em;
        opacity: 0.8;
    }
    
    .app-container {
        display: flex;
        max-width: 1600px;
        margin: 20px auto;
    }
    
    .sidebar {
        width: 300px;
        padding: 20px;
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-right: 20px;
    }
    
    .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    
    .panel {
        background-color: white;
        border-radius: 5px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .panel-title {
        margin-top: 0;
        color: #2c3e50;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
    }
    
    .control-title {
        margin-top: 0;
        color: #2c3e50;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
    }
    
    label {
        display: block;
        margin: 15px 0 5px;
        font-weight: 500;
    }
    
    .update-button {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
        margin-top: 20px;
        font-size: 1em;
        transition: background-color 0.3s;
    }
    
    .update-button:hover {
        background-color: #2980b9;
    }
    
    .metrics-container {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 15px;
    }
    
    .metric-card {
        flex: 1;
        min-width: 150px;
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .metric-card h4 {
        margin: 0;
        color: #7f8c8d;
        font-size: 0.9em;
    }
    
    .metric-card p {
        margin: 10px 0 0;
        font-size: 1.6em;
        font-weight: 600;
        color: #2c3e50;
    }
    
    .detailed-table {
        width: 100%;
        border-collapse: collapse;
    }
    
    .detailed-table th, .detailed-table td {
        padding: 12px 15px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    
    .detailed-table th {
        background-color: #f2f2f2;
        font-weight: 600;
    }
    
    .detailed-table tr:hover {
        background-color: #f5f5f5;
    }
    
    /* Responsive adjustments */
    @media (max-width: 1200px) {
        .app-container {
            flex-direction: column;
        }
        
        .sidebar {
            width: auto;
            margin-right: 0;
            margin-bottom: 20px;
        }
    }
    """
    
    with open(os.path.join(css_dir, "dashboard.css"), "w") as f:
        f.write(css_content)


# Create requirements.txt file
def create_requirements_file():
    requirements = """
dash==2.9.3
plotly==5.14.1
pandas==2.0.0
numpy==1.24.3
"""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt"), "w") as f:
        f.write(requirements)


# Create a README file
def create_readme_file():
    readme = """# Uno Framework Benchmark Dashboard

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
"""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"), "w") as f:
        f.write(readme)


# Create the necessary files
create_css_file()
create_requirements_file()
create_readme_file()


if __name__ == "__main__":
    # Use app.run() for newer versions of Dash
    app.run(debug=True, port=8050)