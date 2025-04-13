# Reports CLI

This folder contains command-line tools for managing the reports system.

## Main CLI Tool

The main CLI tool is `reports_cli.py` located in the parent directory. It provides a comprehensive interface for managing all aspects of the reporting system.

### Installation

No special installation is required. Just ensure you have the necessary dependencies:

```bash
pip install docopt tabulate 
```

### Usage

The CLI provides commands for managing:

- **Templates**: Create, list, get, update, delete, and clone report templates
- **Fields**: Add, list, get, update, and delete report fields
- **Triggers**: Create, list, get, update, enable, disable, and delete report triggers
- **Outputs**: Configure, list, get, update, and delete report output settings
- **Executions**: Execute reports, check status, get results, and cancel executions
- **Scheduler**: Run scheduled reports
- **Events**: Trigger event-based reports

For detailed usage information, run:

```bash
python src/scripts/reports_cli.py --help
```

## Example Commands

### Templates

```bash
# List all templates
python src/scripts/reports_cli.py templates list

# Get template details
python src/scripts/reports_cli.py templates get <template_id>

# Create a new template
python src/scripts/reports_cli.py templates create "Monthly Sales" "Monthly sales report" order
```

### Fields

```bash
# List fields for a template
python src/scripts/reports_cli.py fields list <template_id>

# Add a field to a template
python src/scripts/reports_cli.py fields add <template_id> "total" "Total" aggregate --config='{"function":"sum","field":"amount"}'
```

### Triggers

```bash
# Set up a scheduled trigger
python src/scripts/reports_cli.py triggers add <template_id> scheduled --schedule="interval:24:hours"

# Enable/disable a trigger
python src/scripts/reports_cli.py triggers enable <trigger_id>
python src/scripts/reports_cli.py triggers disable <trigger_id>
```

### Execution

```bash
# Execute a report
python src/scripts/reports_cli.py execute <template_id> --parameters='{"start_date":"2023-01-01","end_date":"2023-12-31"}'

# Check execution status
python src/scripts/reports_cli.py executions get <execution_id>

# Get execution result
python src/scripts/reports_cli.py executions result <execution_id> --format=csv --output=report.csv
```

### Scheduler and Events

```bash
# Run the scheduler to process due reports
python src/scripts/reports_cli.py scheduler run

# Trigger an event
python src/scripts/reports_cli.py event trigger "order_created" '{"entity_type":"order","entity_id":"ORD123"}'
```

## Additional Tools

This directory may contain additional specialized scripts for specific reporting tasks, such as:

- Background worker scripts for report execution
- Maintenance scripts for report data
- Migration utilities for report configurations
- Diagnostic tools for troubleshooting

Check individual script documentation for details on their usage.