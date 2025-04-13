# UNO Reports Module

A comprehensive reporting system for the UNO framework that allows end-users to define, configure, generate, and visualize customizable reports.

## Overview

The Reports module enables users to create report templates based on any entity type in the system. Reports can be generated on-demand, on a schedule, or in response to events. Results can be delivered in various formats, through multiple delivery methods, and visualized in interactive dashboards.

## Key Features

- **Customizable Report Templates**: Define what data to include and how to present it
- **Multiple Field Types**: Use database columns, attributes, methods, related entities, calculated fields, and custom queries
- **Flexible Triggers**: Generate reports manually, on a schedule, in response to events, or based on query conditions
- **Multiple Output Formats**: Generate reports in CSV, JSON, PDF, Excel, HTML, or text format
- **Various Delivery Methods**: Save to file, email, send to webhook, or generate notifications
- **Execution Management**: Track, monitor, and control report executions
- **Interactive Dashboards**: Create and customize dashboards with multiple report widgets
- **Data Visualization**: Display report data as charts, metrics, tables, and other visualizations
- **Data Aggregation**: Efficiently process and transform report data for dashboards and visualizations
- **Web Components**: LitElement-based components for report management and visualization

## Module Structure

- `objs.py`: Pydantic models for all report objects
- `models.py`: SQLAlchemy models for report database tables
- `repositories.py`: Data access layer for report objects
- `interfaces.py`: Protocol definitions for reports services
- `services.py`: Business logic for report operations
- `endpoints.py`: FastAPI endpoints for the reports API
- `dashboard.py`: Dashboard management and API endpoints
- `aggregation.py`: Data processing for reports and dashboards
- `sqlconfigs.py`: SQL configurations for report models
- `cli.py`: Command-line interface for report management

## Installation

The Reports module is included in the UNO package. No additional installation is required.

## Usage

### API

The Reports module exposes a comprehensive REST API for all operations. See the API documentation for details.

```python
# Example: Creating a report template via API client
from uno.client import UnoClient

client = UnoClient("https://api.example.com")
client.login("username", "password")

template_data = {
    "name": "Customer Report",
    "description": "List of all customers",
    "base_object_type": "customer",
    "format_config": {
        "title_format": "{name} - Generated on {date}",
        "show_footer": True
    },
    "fields": [
        {
            "name": "customer_id",
            "display_name": "Customer ID",
            "field_type": "db_column",
            "field_config": {
                "table": "customer",
                "column": "id"
            },
            "order": 1
        },
        {
            "name": "name",
            "display_name": "Customer Name",
            "field_type": "db_column",
            "field_config": {
                "table": "customer",
                "column": "name"
            },
            "order": 2
        }
    ]
}

response = client.reports.create_template(template_data)
template_id = response["id"]
```

### CLI

The module includes a command-line interface for managing reports.

```bash
# Example: Creating a report template via CLI
python src/scripts/reports_cli.py templates create "Customer Report" "List of all customers" customer

# Execute a report
python src/scripts/reports_cli.py execute --template-id r-1234 --param start_date=2023-01-01 --param end_date=2023-01-31

# Create a dashboard
python src/scripts/reports_cli.py dashboard create "Sales Dashboard" --report r-1234 --report r-5678
```

### Web Components

The module includes LitElement-based web components for report management and visualization:

```html
<!-- Report Builder -->
<report-builder mode="create" @template-saved="${handleSaved}"></report-builder>

<!-- Report Dashboard -->
<dashboard-controller dashboard-id="dash-123">
  <report-widget type="metric" title="Total Sales" .data="${salesData}"></report-widget>
  <report-widget type="chart" subtype="bar" title="Sales by Region" .data="${regionData}"></report-widget>
  <report-widget type="table" title="Top Products" .data="${productsData}"></report-widget>
</dashboard-controller>
```

### Direct Integration

You can also use the module's services directly in your code.

```python
# Example: Executing a report programmatically
from uno.dependencies.container import get_container
from uno.reports.services import ReportExecutionService

async def run_report(template_id, parameters):
    # Get the execution service from the DI container
    container = get_container()
    execution_service = container.get(ReportExecutionService)
    
    # Execute the report
    result = await execution_service.execute(
        template_id,
        parameters=parameters,
        trigger_type="manual",
        user_id="system"
    )
    
    if result.is_success():
        execution = result.value
        print(f"Report execution started with ID: {execution.id}")
        return execution.id
    else:
        print(f"Error executing report: {result.error}")
        return None
```

### Creating a Dashboard

```python
from uno.reports.dashboard import DashboardConfig, DashboardWidget

async def create_sales_dashboard(sales_report_id, product_report_id):
    # Define dashboard configuration
    dashboard = DashboardConfig(
        name="Sales Overview Dashboard",
        description="Key sales metrics and trends",
        report_ids=[sales_report_id, product_report_id],
        widgets=[
            DashboardWidget(
                id="total_sales",
                type="metric",
                title="Total Sales",
                report_id=sales_report_id,
                data_key="total_sales",
                config={"format": "currency"},
                position={"x": 0, "y": 0, "w": 3, "h": 2}
            ),
            DashboardWidget(
                id="sales_trend",
                type="chart",
                title="Sales Trend",
                report_id=sales_report_id,
                data_key="daily_sales",
                config={
                    "chart_type": "line",
                    "x_field": "date",
                    "y_field": "revenue"
                },
                position={"x": 3, "y": 0, "w": 9, "h": 4}
            ),
            DashboardWidget(
                id="top_products",
                type="table",
                title="Top Products",
                report_id=product_report_id,
                data_key="top_products",
                config={"page_size": 5},
                position={"x": 0, "y": 2, "w": 12, "h": 6}
            )
        ],
        refresh_interval=300  # Refresh every 5 minutes
    )
    
    # In a real implementation:
    # result = await dashboard_service.create(dashboard)
    # return result.value
    
    # For this example:
    return dashboard
```

## Configuration

The Reports module uses the following configuration options:

- `REPORTS_CACHE_TTL`: Default cache time-to-live for report results (in seconds)
- `REPORTS_MAX_ROWS`: Maximum number of rows allowed in a report
- `REPORTS_OUTPUT_DIR`: Directory for storing report output files
- `REPORTS_TEMP_DIR`: Directory for temporary report files
- `REPORTS_ENABLE_SCHEDULING`: Whether to enable scheduled reports
- `REPORTS_ENABLE_EVENTS`: Whether to enable event-based reports
- `REPORTS_DASHBOARD_REFRESH_INTERVAL`: Default refresh interval for dashboards (in seconds)
- `REPORTS_MAX_CONCURRENT_EXECUTIONS`: Maximum number of concurrent report executions

These options can be set in your application's configuration file or environment variables.

## Extensions

The Reports module can be extended with:

- Custom field types
- Custom output formats
- Custom delivery methods
- Custom triggers
- Custom chart types
- Custom dashboard widgets

See the documentation for details on extending the module.

## Advanced Usage

### Data Aggregation

The module includes powerful data aggregation capabilities:

```python
from uno.reports.aggregation import ReportDataAggregator
from uno.dependencies.container import get_container

async def get_aggregated_data(template_id, parameters):
    container = get_container()
    execution_service = container.get(ReportExecutionService)
    
    # Create data aggregator
    aggregator = ReportDataAggregator(session, execution_service)
    
    # Define aggregations
    aggregations = [
        {
            "type": "group_by",
            "name": "sales_by_region",
            "group_by": ["region"],
            "aggregate": {"sales": "sum", "order_count": "count"}
        },
        {
            "type": "time_series",
            "name": "daily_trend",
            "date_column": "order_date",
            "value_column": "total",
            "frequency": "D"  # Daily
        }
    ]
    
    # Get aggregated data
    result = await aggregator.get_aggregated_data(
        template_id, 
        parameters, 
        aggregations
    )
    
    if result.is_success():
        return result.value
    else:
        print(f"Error: {result.error}")
        return None
```

### Custom Field Types

You can create custom field types:

```python
from uno.reports.field_types import ReportFieldType
from uno.core.result import Result, Success, Failure

class GeoDistanceField(ReportFieldType):
    """Field type that calculates distance between two geographic points"""
    
    type_name = "geo_distance"
    
    def validate_config(self, config: dict) -> Result:
        if "from_lat" not in config or "from_lng" not in config:
            return Failure("Missing source coordinates")
        if "to_lat" not in config or "to_lng" not in config:
            return Failure("Missing destination coordinates")
        return Success(config)
    
    async def compute_value(self, source_data: dict, config: dict, context: dict) -> Result:
        # Implementation details...
        pass
```

## Documentation

For complete documentation, see:

- [Reports Module Documentation](../../docs/reports/overview.md)
- [Advanced Reporting Features](../../docs/reports/advanced_features.md)
- [Report Tutorial](../../docs/reports/tutorial.md)
- [Use Cases](../../docs/reports/use_cases.md)

## License

This module is part of the UNO framework and is covered by the same license.