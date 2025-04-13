# Configuring Report Fields

Fields define what data appears in your reports. The reporting system supports a variety of field types to accommodate different data sources and processing needs.

## Field Types

The system supports these field types:

- **DB_COLUMN**: Direct database column values
- **ATTRIBUTE**: Entity attributes (which may not directly map to columns)
- **METHOD**: Results from calling methods on entity objects
- **QUERY**: Results from custom queries
- **AGGREGATE**: Aggregate calculations (sum, average, count, etc.)
- **RELATED**: Fields from related entities
- **CUSTOM**: Custom-defined fields with special handling

## Field Configuration

Each field type requires specific configuration:

### DB_COLUMN

```json
{
  "table": "customer",
  "column": "name"
}
```

### ATTRIBUTE

```json
{
  "attribute_type_id": "status"
}
```

### METHOD

```json
{
  "method": "get_full_name",
  "module": "uno.domain.customer"
}
```

### QUERY

```json
{
  "query_id": "recent_orders"
}
```

### AGGREGATE

```json
{
  "function": "sum",
  "field": "amount"
}
```

### RELATED

```json
{
  "relation": "orders",
  "field": "total"
}
```

## Adding Fields

You can add fields to a template through the API, CLI, or web interface.

### Using the Web Interface

1. Open the report template
2. Click "Add Field"
3. Fill in the field details:
   - Name: A unique identifier for the field
   - Display Name: How the field will be labeled in the report
   - Field Type: Select from the available types
   - Field Configuration: Configure the field based on its type
   - Order: Position in the report (lower numbers appear first)
   - Format String: Optional formatting (e.g., `${value:,.2f}` for currency)
   - Conditional Formats: Optional rules for conditional formatting
   - Visibility: Whether the field is visible in the report

### Using the CLI

```bash
# Add a simple DB column field
reports_cli.py fields add <template_id> "customer_name" "Customer Name" db_column \
  --config='{"table": "customer", "column": "name"}'

# Add an aggregate field
reports_cli.py fields add <template_id> "total_orders" "Total Orders" aggregate \
  --config='{"function": "count", "field": "id", "relation": "orders"}'
```

### Using the API

```python
import requests

field_data = {
    "name": "email",
    "display_name": "Email Address",
    "description": "Customer email address",
    "field_type": "db_column",
    "field_config": {
        "table": "customer",
        "column": "email"
    },
    "order": 2,
    "is_visible": True
}

response = requests.post(
    f"http://your-api-host/api/reports/templates/{template_id}/fields",
    json=field_data,
    headers={"Authorization": "Bearer YOUR_API_TOKEN"}
)

if response.status_code == 201:
    new_field = response.json()
    print(f"Field created with ID: {new_field['id']}")
else:
    print(f"Error: {response.status_code}, {response.text}")
```

## Field Formatting

You can apply formatting to field values using format strings:

- **Numbers**: `{value:,.2f}` (with comma as thousands separator and 2 decimal places)
- **Percentages**: `{value:.1%}` (as percentage with 1 decimal place)
- **Dates**: `{value:%Y-%m-%d}` (in YYYY-MM-DD format)
- **Currency**: `${value:,.2f}` (with dollar sign, comma, and 2 decimal places)

## Conditional Formatting

You can apply conditional formatting to highlight important values:

```json
{
  "conditional_formats": {
    "highlight_overdue": {
      "condition": "value < today() and status != 'paid'",
      "style": "background-color: #ffeeee; color: #cc0000;"
    },
    "highlight_large": {
      "condition": "value > 1000",
      "style": "font-weight: bold; color: #006600;"
    }
  }
}
```

## Field Hierarchy

You can create hierarchical fields by setting a parent field:

```python
# First create the parent field
parent_field = {
    "name": "address",
    "display_name": "Address",
    "field_type": "custom",
    "is_visible": True
}

parent_response = requests.post(
    f"http://your-api-host/api/reports/templates/{template_id}/fields",
    json=parent_field,
    headers={"Authorization": "Bearer YOUR_API_TOKEN"}
)

parent_id = parent_response.json()["id"]

# Then create child fields
child_field = {
    "name": "address_city",
    "display_name": "City",
    "field_type": "db_column",
    "field_config": {
        "table": "customer_address",
        "column": "city"
    },
    "parent_field_id": parent_id,
    "is_visible": True
}

requests.post(
    f"http://your-api-host/api/reports/templates/{template_id}/fields",
    json=child_field,
    headers={"Authorization": "Bearer YOUR_API_TOKEN"}
)
```

## Managing Fields

### Listing Fields

```bash
# CLI
reports_cli.py fields list <template_id>

# API
GET /api/reports/templates/{template_id}/fields
```

### Getting a Field

```bash
# CLI
reports_cli.py fields get <field_id>

# API
GET /api/reports/fields/{field_id}
```

### Updating a Field

```bash
# CLI
reports_cli.py fields update <field_id> --display_name="New Display Name" --order=3

# API
PUT /api/reports/fields/{field_id}
```

### Deleting a Field

```bash
# CLI
reports_cli.py fields delete <field_id>

# API
DELETE /api/reports/fields/{field_id}
```

## Available Fields

To see what fields are available for a given object type:

```bash
# CLI
reports_cli.py fields available <object_type>

# API
GET /api/reports/available-fields/{object_type}
```

## Next Steps

After configuring fields, you'll want to:

1. [Set up triggers](triggers.md) to determine when to run the report
2. [Configure outputs](outputs.md) to specify how to deliver the results