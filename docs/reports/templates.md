# Creating Report Templates

Report templates are the foundation of the reporting system. They define what data a report will contain and how it will be presented.

## Template Structure

A report template consists of:

- **Basic information**: Name, description, version
- **Base object type**: The main entity type the report is based on (e.g., "customer", "order")
- **Format configuration**: How the report should be formatted (title format, footer, etc.)
- **Parameter definitions**: User-configurable parameters for report execution
- **Cache policy**: How report results should be cached
- **Fields**: The data fields to include in the report
- **Triggers**: When and how the report should be executed
- **Outputs**: How the report results should be delivered

## Creating a Template

You can create a template through the API, CLI, or web interface.

### Using the Web Interface

1. Go to the Reports section of your application
2. Click "Create New Template"
3. Fill in the template details:
   - Name: A unique, descriptive name for the template
   - Description: A longer explanation of what the report shows
   - Base Object Type: Select the entity type this report is based on
4. Configure Format Settings:
   - Title Format: Can include variables like `{name}` and `{date}`
   - Show Footer: Whether to include a footer in the report
5. Define Parameters (optional):
   - Add parameters users can provide when running the report
   - Set default values and mark required parameters
6. Configure Cache Policy (optional):
   - TTL (Time-to-Live): How long report results should be cached
   - Invalidation Events: Events that should invalidate the cache
7. Click "Save Template"

### Using the CLI

```bash
# Create a basic template
reports_cli.py templates create "Customer List" "List of all customers" customer

# Create a template with more options
reports_cli.py templates create "Sales Report" "Monthly sales summary" order \
  --config='{"format_config": {"title_format": "{name} - {date}", "show_footer": true}, ```
```

     "parameter_definitions": {"start_date": {"type": "date", "required": true}}}'
```
```
```

### Using the API

```python
import requests
import json

template_data = {```

"name": "Inventory Report",
"description": "Current inventory levels for all products",
"base_object_type": "product",
"format_config": {```

"title_format": "{name} - Generated on {date}",
"show_footer": True
```
},
"parameter_definitions": {```

"min_stock": {
    "type": "number",
    "required": False,
    "default": 0
},
"category": {
    "type": "string",
    "required": False,
    "choices": ["electronics", "clothing", "food"]
}
```
},
"cache_policy": {```

"ttl_seconds": 3600,  # 1 hour
"invalidate_on_event": "product_updated"
```
},
"version": "1.0.0"
```
}

response = requests.post(```

"http://your-api-host/api/reports/templates/",
json=template_data,
headers={"Authorization": "Bearer YOUR_API_TOKEN"}
```
)

if response.status_code == 201:```

new_template = response.json()
print(f"Template created with ID: {new_template['id']}")
```
else:```

print(f"Error: {response.status_code}, {response.text}")
```
```

## Managing Templates

### Listing Templates

```bash
# CLI
reports_cli.py templates list

# API
GET /api/reports/templates/
```

### Getting a Template

```bash
# CLI
reports_cli.py templates get <template_id>

# API
GET /api/reports/templates/{template_id}
```

### Updating a Template

```bash
# CLI
reports_cli.py templates update <template_id> --name="New Name" --description="Updated description"

# API
PUT /api/reports/templates/{template_id}
```

### Deleting a Template

```bash
# CLI
reports_cli.py templates delete <template_id>

# API
DELETE /api/reports/templates/{template_id}
```

### Cloning a Template

```bash
# CLI
reports_cli.py templates clone <template_id> "New Template Name"

# API
POST /api/reports/templates/{template_id}/clone
```

## Next Steps

After creating a template, you'll need to:

1. [Add fields](fields.md) to define what data to include
2. [Set up triggers](advanced_features.md) to determine when to run the report
3. [Configure outputs](templates.md) to specify how to deliver the results