# Advanced Reporting Features

This guide covers advanced features and techniques for getting the most out of the UNO reporting system.

## Complex Query-Based Triggers

Query-based triggers execute reports when a specific query returns matching data. This is useful for data-driven reporting needs like "alert when inventory falls below threshold" or "report on customers who haven't placed orders in 30 days."

### Example: Inventory Alert Report

```python
from uno.reports.models import ReportTemplate, ReportTrigger
from uno.queries.filter import FilterCondition, FilterExpression

# Create a report trigger that fires when any product inventory drops below threshold
def create_inventory_alert_report():```

# Define the query that will trigger the report
low_inventory_query = FilterExpression(```

conditions=[
    FilterCondition(field="quantity", operator="lt", value=10),
    FilterCondition(field="status", operator="eq", value="active")
],
logical_operator="and"
```
)
``````

```
```

# Create the report template
template = ReportTemplate(```

name="Low Inventory Alert",
description="Alerts when product inventory falls below threshold",
entity_type="product",
fields=[
    {"name": "product_id", "source": "id", "display_name": "Product ID"},
    {"name": "product_name", "source": "name", "display_name": "Product"},
    {"name": "quantity", "source": "quantity", "display_name": "Current Quantity"},
    {"name": "reorder_level", "source": "reorder_level", "display_name": "Reorder Level"},
]
```
)
``````

```
```

# Create the query-based trigger
trigger = ReportTrigger(```

template_id=template.id,
trigger_type="query",
query_definition=low_inventory_query.dict(),
check_interval=3600,  # Check every hour
metadata={
    "notify_roles": ["inventory_manager", "purchasing_agent"]
}
```
)
``````

```
```

return template, trigger
```
```

### Using the CLI

```bash
# Create a query-based trigger for an existing template
reports trigger create-query \
  --template-id 123 \
  --entity product \
  --condition "quantity lt 10" \
  --condition "status eq active" \
  --logical-op and \
  --check-interval 3600 \
  --metadata '{"notify_roles": ["inventory_manager", "purchasing_agent"]}'
```

## Custom Field Types

The reporting system supports custom field types beyond the standard scalar values, allowing for rich, domain-specific reporting.

### Example: Calculated Fields

```python
from uno.reports.models import ReportTemplate, ReportField
from uno.reports.field_types import CalculatedField

# Create a report with calculated fields
def create_order_profitability_report():```

template = ReportTemplate(```

name="Order Profitability Report",
description="Analyzes profitability of orders",
entity_type="order",
fields=[
    {"name": "order_id", "source": "id", "display_name": "Order ID"},
    {"name": "customer_name", "source": "customer.name", "display_name": "Customer"},
    {"name": "order_date", "source": "created_at", "display_name": "Date", "format": "date"},
    {"name": "total_revenue", "source": "total", "display_name": "Revenue", "format": "currency"},
    {
        "name": "total_cost", 
        "type": "calculated",
        "calculation": {
            "type": "sql",
            "expression": "SELECT SUM(p.cost * oi.quantity) FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = :order_id",
            "parameters": ["order_id"]
        },
        "display_name": "Cost", 
        "format": "currency"
    },
    {
        "name": "profit_margin", 
        "type": "calculated",
        "calculation": {
            "type": "formula",
            "expression": "(total_revenue - total_cost) / total_revenue * 100",
            "dependencies": ["total_revenue", "total_cost"]
        },
        "display_name": "Profit Margin", 
        "format": "percentage"
    }
]
```
)
``````

```
```

return template
```
```

### Implementing Custom Field Types

To implement a custom field type:

1. Create a class that inherits from `ReportFieldType`:

```python
from uno.reports.field_types import ReportFieldType
from uno.core.result import Result, Success, Failure

class GeoDistanceField(ReportFieldType):```

"""Field type that calculates distance between two geographic points"""
``````

```
```

type_name = "geo_distance"
``````

```
```

def validate_config(self, config: dict) -> Result:```

if "from_lat" not in config or "from_lng" not in config:
    return Failure("Missing source coordinates")
if "to_lat" not in config or "to_lng" not in config:
    return Failure("Missing destination coordinates")
return Success(config)
```
``````

```
```

async def compute_value(self, source_data: dict, config: dict, context: dict) -> Result:```

try:
    # Get coordinates from source data using dot notation path
    from_lat = self._get_nested_value(source_data, config["from_lat"])
    from_lng = self._get_nested_value(source_data, config["from_lng"])
    to_lat = self._get_nested_value(source_data, config["to_lat"])
    to_lng = self._get_nested_value(source_data, config["to_lng"])
    
    # Calculate Haversine distance
    distance = self._calculate_haversine(from_lat, from_lng, to_lat, to_lng)
    
    # Apply unit conversion if specified
    unit = config.get("unit", "km")
    if unit == "miles":
        distance *= 0.621371
        
    return Success(distance)
except Exception as e:
    return Failure(f"Error calculating geo distance: {str(e)}")
    
```
def _calculate_haversine(self, lat1, lon1, lat2, lon2):```

# Haversine formula implementation
# ...calculation code here...
pass
```
```
```

2. Register the field type:

```python
from uno.reports.registry import field_type_registry

# Register the custom field type
field_type_registry.register(GeoDistanceField())
```

## Advanced Output Formatting

The reporting system supports multiple output formats with customization options.

### Example: Custom PDF Template

```python
from uno.reports.models import ReportTemplate, ReportOutput
from uno.reports.outputs import PdfOutputConfig

def create_invoice_report_with_pdf():```

template = ReportTemplate(```

name="Customer Invoice",
description="Detailed invoice for customers",
entity_type="invoice",
# ...fields defined here...
```
)
``````

```
```

# Create PDF output with custom template
pdf_output = ReportOutput(```

template_id=template.id,
output_type="pdf",
config=PdfOutputConfig(
    template_path="templates/invoice_premium.html",
    paper_size="A4",
    orientation="portrait",
    css_path="templates/invoice_styles.css",
    header_template="<header><img src='logo.png'><p>{{company_name}}</p></header>",
    footer_template="<footer>Page {{page}} of {{pages}}</footer>",
    metadata={
        "company_name": "Acme Inc.",
        "support_phone": "+1-555-123-4567",
        "support_email": "support@acme.com"
    }
).dict()
```
)
``````

```
```

return template
```, pdf_output
```

### Example: Email with Dynamic Content

```python
from uno.reports.models import ReportTemplate, ReportOutput
from uno.reports.outputs import EmailOutputConfig

def create_sales_report_with_email():```

# ...template definition...
``````

```
```

# Create email output with dynamic subject and content
email_output = ReportOutput(```

template_id=template.id,
output_type="email",
config=EmailOutputConfig(
    recipients=["sales@example.com", "{{manager_email}}"],  # Can use field values
    subject="Sales Report: {{period_start}} to {{period_end}}",
    template_path="templates/sales_report_email.html",
    include_attachments=True,
    attachment_formats=["xlsx", "pdf"],
    cc=["reports@example.com"],
    bcc=["audit@example.com"],
    reply_to="no-reply@example.com"
).dict()
```
)
``````

```
```

return email_output
```
```

## Event-Driven Reporting Pipeline

For advanced scenarios, you can connect reports to the event system to create event-driven reporting pipelines.

### Example: Order Processing Pipeline

```python
from uno.domain.events import EventHandler
from uno.reports.services import ReportExecutionService

class OrderProcessingReportHandler(EventHandler):```

"""Triggers different reports at each stage of order processing"""
``````

```
```

def __init__(self, report_execution_service: ReportExecutionService):```

self.report_service = report_execution_service
```
    
async def handle_event(self, event):```

if event.type == "order.created":
    # Generate order confirmation report
    await self.report_service.execute_by_name(
        "Order Confirmation",
        {"order_id": event.data["order_id"]}
    )
    
elif event.type == "order.shipped":
    # Generate shipping notification report
    await self.report_service.execute_by_name(
        "Shipping Notification",
        {"order_id": event.data["order_id"]}
    )
    
elif event.type == "order.delivered":
    # Generate delivery confirmation and feedback request reports
    await self.report_service.execute_by_name(
        "Delivery Confirmation",
        {"order_id": event.data["order_id"]}
    )
    
    # Wait 3 days then generate feedback request
    await self.report_service.schedule_execution(
        template_name="Customer Feedback Request",
        parameters={"order_id": event.data["order_id"]},
        delay_seconds=3 * 24 * 3600  # 3 days
    )
```
```
```

## Performance Optimization Techniques

For large reports or high-volume reporting needs, consider these optimization techniques:

### Batched Processing

```python
from uno.reports.services import ReportExecutionService
from uno.reports.models import BatchExecutionConfig

async def process_monthly_customer_reports(execution_service: ReportExecutionService):```

# Get all active customers
customers = await customer_repository.get_all_active()
``````

```
```

# Configure batch processing
batch_config = BatchExecutionConfig(```

batch_size=100,  # Process 100 customers at a time
max_concurrent=5,  # Run up to 5 batches concurrently
timeout=3600,  # Time limit for the entire operation (1 hour)
error_handling="continue"  # Continue processing if some reports fail
```
)
``````

```
```

# Schedule batch execution
batch_result = await execution_service.batch_execute(```

template_name="Monthly Customer Statement",
parameter_sets=[{"customer_id": customer.id} for customer in customers],
config=batch_config
```
)
``````

```
```

# Analyze results
success_count = len(batch_result.successful)
failed_count = len(batch_result.failed)
``````

```
```

return {```

"total": len(customers),
"success": success_count,
"failed": failed_count,
"success_rate": success_count / len(customers) * 100 if customers else 0
```
}
```
```

### Data Caching

For reports that require expensive data calculations:

```python
from uno.caching.decorators import cached
from uno.reports.field_types import ReportFieldType

class CachedCalculationField(ReportFieldType):```

"""Field that caches expensive calculations"""
``````

```
```

type_name = "cached_calculation"
``````

```
```

@cached(ttl=3600, key_pattern="report:calc:{config[calculation_id]}:{source_data[id]}")
async def compute_value(self, source_data: dict, config: dict, context: dict) -> Result:```

# Expensive calculation that will be cached for an hour
# ...calculation code here...
pass
```
```
```

## Integration with Vector Search

For AI-enhanced reporting with similarity search capabilities:

```python
from uno.reports.models import ReportTemplate
from uno.vector_search.integration import VectorSearchField

def create_document_similarity_report():```

template = ReportTemplate(```

name="Document Similarity Analysis",
description="Finds similar documents based on content",
entity_type="document",
fields=[
    {"name": "document_id", "source": "id", "display_name": "Document ID"},
    {"name": "title", "source": "title", "display_name": "Title"},
    {"name": "created_at", "source": "created_at", "display_name": "Created", "format": "date"},
    {
        "name": "content_embedding", 
        "type": "vector", 
        "vector_config": {
            "source_field": "content",
            "model": "text-embedding-3-small",
            "dimensions": 1536
        },
        "display": False  # Don't show the embedding in the report
    },
    {
        "name": "similar_documents",
        "type": "vector_search",
        "search_config": {
            "vector_field": "content_embedding",
            "collection": "documents",
            "k": 5,  # Find top 5 similar documents
            "min_score": 0.75
        },
        "display_name": "Similar Documents"
    }
]
```
)
``````

```
```

return template
```
```

## Extending with Plugins

The reporting system supports plugins for custom functionality:

```python
from uno.reports.plugins import ReportPlugin
from uno.plugins.registry import plugin_registry

class ExternalDataPlugin(ReportPlugin):```

"""Plugin that fetches data from external APIs for reports"""
``````

```
```

plugin_name = "external_data"
plugin_version = "1.0.0"
``````

```
```

def initialize(self, config: dict):```

self.api_key = config.get("api_key")
self.base_url = config.get("base_url")
# Initialize API client
```
    
async def fetch_data(self, source: str, parameters: dict) -> Result:```

# Implementation to fetch data from external source
pass
```
    
# Register extension points
def register_extension_points(self):```

return {
    "data_sources": self.fetch_data,
    "field_types": [ExternalDataField]
}
```
    
```
# Register the plugin
plugin_registry.register(ExternalDataPlugin())
```

## Next Steps

After exploring these advanced features, consider:

1. Developing a custom reporting strategy for your specific domain
2. Creating reusable report templates for common reporting needs
3. Setting up automated reporting workflows with event triggers
4. Integrating reports with your notification systems
5. Implementing access controls for report templates and outputs

For more information, see the [API Reference](../api/reports.md) or [Contact Support](../support.md).