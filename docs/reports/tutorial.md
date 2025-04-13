# Custom Reporting Tutorial

This tutorial guides you through creating a complete custom reporting workflow, from defining templates to delivering outputs.

## Prerequisites

- Basic understanding of the UNO framework
- Familiarity with Python and async/await patterns
- Access to a UNO project with the reporting module enabled

## Part 1: Planning Your Report

Before coding, define what you want your report to accomplish:

1. **Purpose**: What business question does this report answer?
2. **Data Sources**: What entities and attributes are needed?
3. **Trigger Mechanism**: How should the report be executed (manual, scheduled, event-based)?
4. **Output Format**: How should results be presented (table, chart, PDF, email)?
5. **Delivery Method**: How should the report be delivered to end users?

For this tutorial, we'll build a "Customer Purchase Analysis" report that:
- Analyzes customer purchasing patterns
- Shows product categories, total spent, and purchase frequency
- Runs automatically at the end of each month
- Delivers results via email with PDF attachment
- Includes visualization of purchasing trends

## Part 2: Creating the Report Template

Let's start by defining our report template:

```python
from uno.reports.models import ReportTemplate, ReportField
from uno.reports.services import ReportTemplateService
from uno.dependencies.container import get_container

async def create_customer_purchase_report():
    # Get the report template service from the DI container
    container = get_container()
    template_service = container.get(ReportTemplateService)
    
    # Define the report fields
    fields = [
        ReportField(
            name="customer_id",
            source="id",
            display_name="Customer ID",
            display=False  # Used for filtering but not displayed in output
        ),
        ReportField(
            name="customer_name",
            source="name",
            display_name="Customer Name"
        ),
        ReportField(
            name="email",
            source="email",
            display_name="Email"
        ),
        ReportField(
            name="join_date",
            source="created_at",
            display_name="Customer Since",
            format="date"
        ),
        ReportField(
            name="total_orders",
            source="orders.count()",
            display_name="Total Orders"
        ),
        ReportField(
            name="total_spent",
            source="orders.sum(total)",
            display_name="Total Spent",
            format="currency"
        ),
        ReportField(
            name="avg_order_value",
            type="calculated",
            calculation={
                "type": "formula",
                "expression": "total_spent / total_orders",
                "dependencies": ["total_spent", "total_orders"]
            },
            display_name="Average Order Value",
            format="currency"
        ),
        ReportField(
            name="top_categories",
            type="sql",
            sql_definition={
                "query": """
                    SELECT pc.name, COUNT(*) as purchase_count, SUM(oi.price * oi.quantity) as total_spent
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    JOIN product_categories pc ON p.category_id = pc.id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE o.customer_id = :customer_id
                    GROUP BY pc.name
                    ORDER BY total_spent DESC
                    LIMIT 3
                """,
                "parameters": ["customer_id"]
            },
            display_name="Top Product Categories",
            format="json"
        ),
        ReportField(
            name="purchase_frequency",
            type="calculated",
            calculation={
                "type": "formula",
                "expression": "total_orders / ((NOW() - join_date) / 86400 / 30)",
                "dependencies": ["total_orders", "join_date"]
            },
            display_name="Monthly Purchase Frequency",
            format="decimal"
        ),
        ReportField(
            name="last_purchase_date",
            source="orders.max(created_at)",
            display_name="Last Purchase Date",
            format="date"
        )
    ]
    
    # Create the report template
    template = ReportTemplate(
        name="Customer Purchase Analysis",
        description="Monthly analysis of customer purchasing patterns",
        entity_type="customer",
        fields=fields,
        metadata={
            "author": "System",
            "version": "1.0",
            "category": "Sales Analysis"
        }
    )
    
    # Save the template
    result = await template_service.create(template)
    if result.is_failure():
        raise Exception(f"Failed to create report template: {result.error}")
        
    return result.value
```

## Part 3: Setting Up a Monthly Trigger

Now let's set up a monthly trigger to run this report:

```python
from uno.reports.models import ReportTrigger
from uno.reports.services import ReportTriggerService
from datetime import datetime, timezone

async def setup_monthly_trigger(template_id):
    # Get the trigger service
    container = get_container()
    trigger_service = container.get(ReportTriggerService)
    
    # Create a scheduled trigger for the last day of each month
    trigger = ReportTrigger(
        template_id=template_id,
        trigger_type="schedule",
        schedule={
            "type": "cron",
            "expression": "0 0 L * *"  # Midnight on the last day of the month
        },
        parameters={
            "month_end": "{{NOW.strftime('%Y-%m-%d')}}"
        },
        enabled=True,
        metadata={
            "description": "Monthly scheduled execution",
            "created_by": "System"
        }
    )
    
    # Save the trigger
    result = await trigger_service.create(trigger)
    if result.is_failure():
        raise Exception(f"Failed to create trigger: {result.error}")
        
    return result.value
```

## Part 4: Configuring Report Outputs

Next, let's configure multiple output formats:

```python
from uno.reports.models import ReportOutput
from uno.reports.services import ReportOutputService

async def configure_outputs(template_id):
    # Get the output service
    container = get_container()
    output_service = container.get(ReportOutputService)
    
    # Configure PDF output with chart visualization
    pdf_output = ReportOutput(
        template_id=template_id,
        output_type="pdf",
        config={
            "template_path": "templates/customer_analysis.html",
            "paper_size": "A4",
            "orientation": "portrait",
            "visualizations": [
                {
                    "type": "bar_chart",
                    "title": "Spending by Category",
                    "data_field": "top_categories",
                    "x_field": "name",
                    "y_field": "total_spent",
                    "width": 600,
                    "height": 400
                },
                {
                    "type": "line_chart",
                    "title": "Purchase Trends",
                    "data_source": "customer_purchase_history",
                    "x_field": "month",
                    "y_field": "order_count",
                    "width": 600,
                    "height": 300
                }
            ]
        }
    )
    
    # Configure email delivery
    email_output = ReportOutput(
        template_id=template_id,
        output_type="email",
        config={
            "recipients": ["{{email}}", "sales@example.com"],
            "subject": "Monthly Purchase Analysis - {{customer_name}}",
            "template_path": "templates/customer_email.html",
            "include_attachments": True,
            "attachment_formats": ["pdf", "xlsx"],
            "cc": [],
            "bcc": ["reports@example.com"]
        }
    )
    
    # Configure Excel output
    excel_output = ReportOutput(
        template_id=template_id,
        output_type="xlsx",
        config={
            "sheet_name": "Purchase Analysis",
            "include_charts": True,
            "charts": [
                {
                    "type": "bar",
                    "title": "Category Spending",
                    "data_field": "top_categories",
                    "categories": "name",
                    "values": "total_spent"
                }
            ]
        }
    )
    
    # Save all outputs
    outputs = []
    for output in [pdf_output, email_output, excel_output]:
        result = await output_service.create(output)
        if result.is_failure():
            raise Exception(f"Failed to create output: {result.error}")
        outputs.append(result.value)
        
    return outputs
```

## Part 5: Data Preparation Function

Now, let's create a data preparation function that will enhance the report with additional calculations:

```python
from uno.reports.hooks import register_data_hook
from uno.database.session import get_db_session

@register_data_hook("customer_purchase_analysis")
async def prepare_customer_purchase_data(data, parameters, context):
    """Enhances report data with additional calculations and historical data"""
    customer_id = data.get("customer_id")
    if not customer_id:
        return data
        
    # Add purchase history for trend analysis
    async with get_db_session() as session:
        query = """
            SELECT 
                DATE_TRUNC('month', o.created_at) as month,
                COUNT(*) as order_count,
                SUM(o.total) as monthly_spent
            FROM 
                orders o
            WHERE 
                o.customer_id = $1
                AND o.created_at >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY 
                DATE_TRUNC('month', o.created_at)
            ORDER BY 
                month
        """
        
        purchase_history = await session.fetch(query, customer_id)
        
        # Convert to list of dicts for the report
        history_data = [
            {
                "month": row["month"].strftime("%Y-%m"),
                "order_count": row["order_count"],
                "monthly_spent": row["monthly_spent"]
            }
            for row in purchase_history
        ]
        
        # Add to data
        data["customer_purchase_history"] = history_data
        
        # Calculate additional metrics
        if history_data:
            # Monthly growth rate
            months = len(history_data)
            if months > 1:
                first_month = history_data[0]["monthly_spent"]
                last_month = history_data[-1]["monthly_spent"]
                if first_month > 0:
                    growth_rate = ((last_month / first_month) ** (1 / months) - 1) * 100
                    data["monthly_growth_rate"] = round(growth_rate, 2)
        
        # Customer segment classification
        total_spent = data.get("total_spent", 0)
        purchase_frequency = data.get("purchase_frequency", 0)
        
        if total_spent > 1000 and purchase_frequency > 2:
            segment = "VIP"
        elif total_spent > 500 or purchase_frequency > 1:
            segment = "Regular"
        else:
            segment = "Occasional"
            
        data["customer_segment"] = segment
        
        return data
```

## Part 6: Custom Template for PDF Output

Create an HTML template for the PDF output:

```html
<!-- templates/customer_analysis.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Customer Purchase Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { text-align: center; margin-bottom: 20px; }
        .customer-info { margin-bottom: 30px; }
        .summary { margin-bottom: 30px; }
        .metrics { display: flex; flex-wrap: wrap; }
        .metric { width: 30%; margin: 10px; padding: 15px; border: 1px solid #eee; border-radius: 5px; }
        .metric-value { font-size: 24px; font-weight: bold; margin: 10px 0; }
        .chart-container { margin: 20px 0; }
        .segment { font-size: 18px; padding: 5px 10px; border-radius: 3px; display: inline-block; }
        .segment-VIP { background-color: #ffd700; color: #000; }
        .segment-Regular { background-color: #c0c0c0; color: #000; }
        .segment-Occasional { background-color: #cd7f32; color: #fff; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Customer Purchase Analysis</h1>
        <p>Generated on {{ NOW.strftime('%B %d, %Y') }}</p>
    </div>
    
    <div class="customer-info">
        <h2>{{ customer_name }}</h2>
        <p>Customer since: {{ join_date }}</p>
        <p>Email: {{ email }}</p>
        <p>Segment: <span class="segment segment-{{ customer_segment }}">{{ customer_segment }}</span></p>
    </div>
    
    <div class="summary">
        <h3>Purchase Summary</h3>
        <div class="metrics">
            <div class="metric">
                <div>Total Orders</div>
                <div class="metric-value">{{ total_orders }}</div>
            </div>
            <div class="metric">
                <div>Total Spent</div>
                <div class="metric-value">${{ total_spent|number_format(2) }}</div>
            </div>
            <div class="metric">
                <div>Average Order Value</div>
                <div class="metric-value">${{ avg_order_value|number_format(2) }}</div>
            </div>
            <div class="metric">
                <div>Purchase Frequency</div>
                <div class="metric-value">{{ purchase_frequency|number_format(1) }}/month</div>
            </div>
            <div class="metric">
                <div>Last Purchase</div>
                <div class="metric-value">{{ last_purchase_date }}</div>
            </div>
            {% if monthly_growth_rate is defined %}
            <div class="metric">
                <div>Monthly Growth</div>
                <div class="metric-value">{{ monthly_growth_rate }}%</div>
            </div>
            {% endif %}
        </div>
    </div>
    
    <div class="top-categories">
        <h3>Top Product Categories</h3>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Purchase Count</th>
                    <th>Total Spent</th>
                </tr>
            </thead>
            <tbody>
                {% for category in top_categories %}
                <tr>
                    <td>{{ category.name }}</td>
                    <td>{{ category.purchase_count }}</td>
                    <td>${{ category.total_spent|number_format(2) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="chart-container">
        <h3>Spending by Category</h3>
        <!-- Visualization 1 will be inserted here -->
    </div>
    
    <div class="chart-container">
        <h3>Purchase Trends (Last 12 Months)</h3>
        <!-- Visualization 2 will be inserted here -->
    </div>
    
    <div class="recommendations">
        <h3>Recommendations</h3>
        <ul>
            {% if purchase_frequency < 1 %}
            <li>Consider offering a loyalty discount to increase purchase frequency</li>
            {% endif %}
            
            {% if customer_segment == 'VIP' %}
            <li>Offer exclusive VIP promotions based on top categories</li>
            {% elif customer_segment == 'Regular' %}
            <li>Send targeted promotions to increase order value</li>
            {% else %}
            <li>Provide incentives to increase engagement</li>
            {% endif %}
            
            {% if last_purchase_date and (NOW - last_purchase_date).days > 60 %}
            <li>Send re-engagement campaign, customer hasn't purchased in over 60 days</li>
            {% endif %}
        </ul>
    </div>
    
    <div class="footer">
        <p>Confidential - For internal use only</p>
        <p>© {{ NOW.year }} Acme Corporation</p>
    </div>
</body>
</html>
```

## Part 7: Creating a CLI Command

Add a CLI command to manually execute the report:

```python
# src/scripts/reports_cli.py (add to existing file)

def register_customer_report_commands(subparsers):
    """Register customer report specific commands"""
    customer_parser = subparsers.add_parser('customer-analysis', help='Customer purchase analysis commands')
    customer_subparsers = customer_parser.add_subparsers(dest='customer_command')
    
    # Generate report for a specific customer
    generate_parser = customer_subparsers.add_parser('generate', help='Generate customer purchase analysis report')
    generate_parser.add_argument('--customer-id', required=True, help='Customer ID')
    generate_parser.add_argument('--email', action='store_true', help='Send email with report')
    generate_parser.add_argument('--output-dir', help='Directory to save report files')
    
    # Generate report for all VIP customers
    generate_vip_parser = customer_subparsers.add_parser('generate-vip', help='Generate reports for all VIP customers')
    generate_vip_parser.add_argument('--min-spent', type=float, default=1000, help='Minimum total spent')
    generate_vip_parser.add_argument('--min-frequency', type=float, default=2, help='Minimum purchase frequency')
    generate_vip_parser.add_argument('--email', action='store_true', help='Send email with reports')
    
    return customer_parser

async def handle_customer_report_command(args):
    """Handle customer report commands"""
    if args.customer_command == 'generate':
        await handle_generate_customer_report(args)
    elif args.customer_command == 'generate-vip':
        await handle_generate_vip_reports(args)
    else:
        print("Invalid customer report command")

async def handle_generate_customer_report(args):
    """Generate a report for a specific customer"""
    try:
        container = get_container()
        execution_service = container.get(ReportExecutionService)
        
        # Find the report template
        template_service = container.get(ReportTemplateService)
        template_result = await template_service.get_by_name("Customer Purchase Analysis")
        if template_result.is_failure():
            print(f"Error: Report template not found: {template_result.error}")
            return
            
        template = template_result.value
        
        # Execute the report
        execution_result = await execution_service.execute(
            template_id=template.id,
            parameters={"customer_id": args.customer_id}
        )
        
        if execution_result.is_failure():
            print(f"Error generating report: {execution_result.error}")
            return
            
        execution = execution_result.value
        print(f"Report execution started: {execution.id}")
        
        # If the execution is completed synchronously
        if execution.status == "completed":
            print("Report generated successfully")
            
            # Handle outputs
            if args.output_dir:
                # Save outputs to directory
                output_paths = []
                for output in execution.outputs:
                    if output.output_type in ["pdf", "xlsx"]:
                        output_path = os.path.join(args.output_dir, f"{execution.id}_{output.output_type}.{output.output_type}")
                        with open(output_path, 'wb') as f:
                            f.write(output.content)
                        output_paths.append(output_path)
                        print(f"Saved {output.output_type} to {output_path}")
                
            # Handle email
            if args.email:
                # Find email output
                email_output = next((o for o in execution.outputs if o.output_type == "email"), None)
                if email_output:
                    print(f"Email sent to {', '.join(email_output.recipients)}")
                else:
                    print("No email output configured")
        else:
            print(f"Report execution in progress with status: {execution.status}")
            print(f"Check status with: reports execution get --id {execution.id}")
    
    except Exception as e:
        print(f"Error: {str(e)}")

# Add to main parser registration
def register_commands(parser):
    # Existing commands...
    
    # Register customer report commands
    customer_parser = register_customer_report_commands(subparsers)
    
    # Map commands to handlers
    command_handlers = {
        # Existing handlers...
        'customer-analysis': handle_customer_report_command,
    }
    
    return command_handlers
```

## Part 8: Creating a Web Component

Create a web component for viewing customer reports:

```javascript
// src/static/components/reports/customer-analysis-view.js
import { LitElement, html, css } from 'lit-element';
import { Chart } from 'chart.js/auto';

class CustomerAnalysisView extends LitElement {
  static get properties() {
    return {
      customerId: { type: String },
      reportData: { type: Object },
      loading: { type: Boolean },
      error: { type: String }
    };
  }

  static get styles() {
    return css`
      :host {
        display: block;
        font-family: Arial, sans-serif;
      }
      .report-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
      }
      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
      }
      .metrics {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin-bottom: 30px;
      }
      .metric-card {
        background: #f9f9f9;
        border-radius: 8px;
        padding: 20px;
        min-width: 200px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
      }
      .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin: 10px 0;
      }
      .chart-container {
        margin: 30px 0;
        height: 400px;
      }
      .segment {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 4px;
        font-weight: bold;
      }
      .segment-VIP {
        background-color: #ffd700;
        color: #000;
      }
      .segment-Regular {
        background-color: #c0c0c0;
        color: #000;
      }
      .segment-Occasional {
        background-color: #cd7f32;
        color: #fff;
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
      }
      th {
        background-color: #f2f2f2;
      }
      .actions {
        display: flex;
        gap: 10px;
        margin-top: 20px;
      }
      button {
        padding: 8px 16px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }
      button:hover {
        background-color: #45a049;
      }
      .error {
        color: red;
        padding: 10px;
        background-color: #ffeeee;
        border-radius: 4px;
      }
      .loading {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 200px;
      }
    `;
  }

  constructor() {
    super();
    this.customerId = '';
    this.reportData = null;
    this.loading = false;
    this.error = null;
    this.charts = [];
  }

  connectedCallback() {
    super.connectedCallback();
    if (this.customerId) {
      this.loadReport();
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    // Destroy charts to prevent memory leaks
    this.charts.forEach(chart => chart.destroy());
  }

  updated(changedProperties) {
    if (changedProperties.has('customerId') && this.customerId) {
      this.loadReport();
    }
    
    if (changedProperties.has('reportData') && this.reportData) {
      // Wait for DOM to update before rendering charts
      setTimeout(() => this.renderCharts(), 0);
    }
  }

  async loadReport() {
    this.loading = true;
    this.error = null;
    
    try {
      const response = await fetch(`/api/reports/customer-analysis/${this.customerId}`);
      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${await response.text()}`);
      }
      
      this.reportData = await response.json();
    } catch (err) {
      this.error = `Failed to load report: ${err.message}`;
      console.error(err);
    } finally {
      this.loading = false;
    }
  }

  renderCharts() {
    // Clean up existing charts
    this.charts.forEach(chart => chart.destroy());
    this.charts = [];
    
    if (!this.reportData) return;
    
    // Category spending chart
    const categoryCtx = this.shadowRoot.getElementById('categoryChart');
    if (categoryCtx && this.reportData.top_categories) {
      const categoryChart = new Chart(categoryCtx, {
        type: 'bar',
        data: {
          labels: this.reportData.top_categories.map(c => c.name),
          datasets: [{
            label: 'Total Spent',
            data: this.reportData.top_categories.map(c => c.total_spent),
            backgroundColor: ['rgba(54, 162, 235, 0.8)', 'rgba(255, 99, 132, 0.8)', 'rgba(255, 206, 86, 0.8)']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      });
      this.charts.push(categoryChart);
    }
    
    // Purchase history chart
    const historyCtx = this.shadowRoot.getElementById('historyChart');
    if (historyCtx && this.reportData.customer_purchase_history) {
      const historyChart = new Chart(historyCtx, {
        type: 'line',
        data: {
          labels: this.reportData.customer_purchase_history.map(h => h.month),
          datasets: [
            {
              label: 'Order Count',
              data: this.reportData.customer_purchase_history.map(h => h.order_count),
              borderColor: 'rgba(54, 162, 235, 1)',
              backgroundColor: 'rgba(54, 162, 235, 0.2)',
              yAxisID: 'y'
            },
            {
              label: 'Monthly Spent',
              data: this.reportData.customer_purchase_history.map(h => h.monthly_spent),
              borderColor: 'rgba(255, 99, 132, 1)',
              backgroundColor: 'rgba(255, 99, 132, 0.2)',
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              type: 'linear',
              display: true,
              position: 'left',
              title: {
                display: true,
                text: 'Order Count'
              }
            },
            y1: {
              type: 'linear',
              display: true,
              position: 'right',
              title: {
                display: true,
                text: 'Amount ($)'
              }
            }
          }
        }
      });
      this.charts.push(historyChart);
    }
  }

  formatCurrency(value) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
  }

  formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
  }

  handleRefresh() {
    this.loadReport();
  }

  handleExport(format) {
    window.open(`/api/reports/customer-analysis/${this.customerId}/export?format=${format}`, '_blank');
  }

  renderLoading() {
    return html`
      <div class="loading">
        <p>Loading report data...</p>
      </div>
    `;
  }

  renderError() {
    return html`
      <div class="error">
        <p>${this.error}</p>
        <button @click=${this.handleRefresh}>Retry</button>
      </div>
    `;
  }

  renderReport() {
    const data = this.reportData;
    return html`
      <div class="report-container">
        <div class="header">
          <div>
            <h1>${data.customer_name}</h1>
            <p>Customer since: ${this.formatDate(data.join_date)}</p>
            <p>Segment: <span class="segment segment-${data.customer_segment}">${data.customer_segment}</span></p>
          </div>
          <div class="actions">
            <button @click=${this.handleRefresh}>Refresh</button>
            <button @click=${() => this.handleExport('pdf')}>Export PDF</button>
            <button @click=${() => this.handleExport('xlsx')}>Export Excel</button>
          </div>
        </div>
        
        <div class="metrics">
          <div class="metric-card">
            <div>Total Orders</div>
            <div class="metric-value">${data.total_orders}</div>
          </div>
          <div class="metric-card">
            <div>Total Spent</div>
            <div class="metric-value">${this.formatCurrency(data.total_spent)}</div>
          </div>
          <div class="metric-card">
            <div>Average Order Value</div>
            <div class="metric-value">${this.formatCurrency(data.avg_order_value)}</div>
          </div>
          <div class="metric-card">
            <div>Purchase Frequency</div>
            <div class="metric-value">${data.purchase_frequency.toFixed(1)}/month</div>
          </div>
          <div class="metric-card">
            <div>Last Purchase</div>
            <div class="metric-value">${this.formatDate(data.last_purchase_date)}</div>
          </div>
          ${data.monthly_growth_rate ? html`
            <div class="metric-card">
              <div>Monthly Growth</div>
              <div class="metric-value">${data.monthly_growth_rate}%</div>
            </div>
          ` : ''}
        </div>
        
        <h2>Top Product Categories</h2>
        <table>
          <thead>
            <tr>
              <th>Category</th>
              <th>Purchase Count</th>
              <th>Total Spent</th>
            </tr>
          </thead>
          <tbody>
            ${data.top_categories.map(category => html`
              <tr>
                <td>${category.name}</td>
                <td>${category.purchase_count}</td>
                <td>${this.formatCurrency(category.total_spent)}</td>
              </tr>
            `)}
          </tbody>
        </table>
        
        <div class="chart-container">
          <h2>Spending by Category</h2>
          <canvas id="categoryChart"></canvas>
        </div>
        
        <div class="chart-container">
          <h2>Purchase Trends (Last 12 Months)</h2>
          <canvas id="historyChart"></canvas>
        </div>
        
        <h2>Recommendations</h2>
        <ul>
          ${data.purchase_frequency < 1 ? html`
            <li>Consider offering a loyalty discount to increase purchase frequency</li>
          ` : ''}
          
          ${data.customer_segment === 'VIP' ? html`
            <li>Offer exclusive VIP promotions based on top categories</li>
          ` : data.customer_segment === 'Regular' ? html`
            <li>Send targeted promotions to increase order value</li>
          ` : html`
            <li>Provide incentives to increase engagement</li>
          `}
          
          ${new Date() - new Date(data.last_purchase_date) > 60 * 24 * 60 * 60 * 1000 ? html`
            <li>Send re-engagement campaign, customer hasn't purchased in over 60 days</li>
          ` : ''}
        </ul>
      </div>
    `;
  }

  render() {
    if (this.loading) {
      return this.renderLoading();
    }
    
    if (this.error) {
      return this.renderError();
    }
    
    if (!this.reportData) {
      return html`<p>No report data available</p>`;
    }
    
    return this.renderReport();
  }
}

customElements.define('customer-analysis-view', CustomerAnalysisView);
```

## Part 9: Creating API Endpoints

Finally, let's create API endpoints for the report:

```python
# src/uno/reports/api/customer_analysis.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from io import BytesIO

from uno.reports.services import ReportExecutionService, ReportTemplateService
from uno.dependencies.fastapi import get_service
from uno.api.endpoint import UnoEndpoint
from uno.database.session import get_db_session

router = APIRouter(prefix="/reports/customer-analysis", tags=["reports"])

@router.get("/{customer_id}")
async def get_customer_analysis(
    customer_id: str,
    execution_service: ReportExecutionService = Depends(get_service(ReportExecutionService)),
    template_service: ReportTemplateService = Depends(get_service(ReportTemplateService))
):
    """Get customer purchase analysis report data"""
    # Find the report template
    template_result = await template_service.get_by_name("Customer Purchase Analysis")
    if template_result.is_failure():
        raise HTTPException(status_code=404, detail="Report template not found")
    
    template = template_result.value
    
    # Execute the report
    execution_result = await execution_service.execute(
        template_id=template.id,
        parameters={"customer_id": customer_id}
    )
    
    if execution_result.is_failure():
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {execution_result.error}")
    
    execution = execution_result.value
    
    # Wait for the report to complete if needed
    if execution.status not in ["completed", "success"]:
        # For a real implementation, you might want to return a 202 Accepted
        # with a URL to poll for the result instead of waiting
        execution = await execution_service.wait_for_completion(execution.id, timeout=30)
    
    if execution.status not in ["completed", "success"]:
        raise HTTPException(
            status_code=500, 
            detail=f"Report execution not completed: {execution.status}"
        )
    
    # Return the report data
    return execution.data

@router.get("/{customer_id}/export")
async def export_customer_analysis(
    customer_id: str,
    format: str = Query(..., regex="^(pdf|xlsx|csv)$"),
    execution_service: ReportExecutionService = Depends(get_service(ReportExecutionService)),
    template_service: ReportTemplateService = Depends(get_service(ReportTemplateService))
):
    """Export customer purchase analysis report in specified format"""
    # Find the report template
    template_result = await template_service.get_by_name("Customer Purchase Analysis")
    if template_result.is_failure():
        raise HTTPException(status_code=404, detail="Report template not found")
    
    template = template_result.value
    
    # Execute the report
    execution_result = await execution_service.execute(
        template_id=template.id,
        parameters={"customer_id": customer_id}
    )
    
    if execution_result.is_failure():
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {execution_result.error}")
    
    execution = execution_result.value
    
    # Wait for the report to complete if needed
    if execution.status not in ["completed", "success"]:
        execution = await execution_service.wait_for_completion(execution.id, timeout=30)
    
    if execution.status not in ["completed", "success"]:
        raise HTTPException(
            status_code=500, 
            detail=f"Report execution not completed: {execution.status}"
        )
    
    # Find the requested output format
    output = next((o for o in execution.outputs if o.output_type == format), None)
    if not output:
        raise HTTPException(status_code=404, detail=f"Output format {format} not available")
    
    # Return the file
    content_types = {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv"
    }
    
    filename = f"customer_analysis_{customer_id}.{format}"
    
    return StreamingResponse(
        BytesIO(output.content),
        media_type=content_types[format],
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/aggregate")
async def get_customer_segments(
    db_session = Depends(get_db_session)
):
    """Get aggregate customer segment information"""
    # This would be implemented with your actual database schema
    query = """
    WITH customer_metrics AS (
        SELECT 
            c.id,
            c.name,
            COUNT(o.id) as total_orders,
            SUM(o.total) as total_spent,
            COUNT(o.id) / 
                (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - c.created_at)) / 86400 / 30) as purchase_frequency
        FROM 
            customers c
        LEFT JOIN 
            orders o ON c.id = o.customer_id
        GROUP BY 
            c.id, c.name, c.created_at
    ),
    segments AS (
        SELECT
            id,
            name,
            total_orders,
            total_spent,
            purchase_frequency,
            CASE
                WHEN total_spent > 1000 AND purchase_frequency > 2 THEN 'VIP'
                WHEN total_spent > 500 OR purchase_frequency > 1 THEN 'Regular'
                ELSE 'Occasional'
            END as segment
        FROM 
            customer_metrics
    )
    SELECT
        segment,
        COUNT(*) as customer_count,
        SUM(total_spent) as segment_revenue,
        AVG(total_spent) as avg_spent_per_customer,
        AVG(total_orders) as avg_orders_per_customer
    FROM
        segments
    GROUP BY
        segment
    ORDER BY
        segment_revenue DESC
    """
    
    results = await db_session.fetch(query)
    
    return [dict(row) for row in results]

# Add to your main FastAPI app
def register_report_endpoints(app):
    app.include_router(router)
```

## Part 10: Putting It All Together

Let's create a main function that sets up the complete reporting workflow:

```python
async def setup_customer_analysis_reporting():
    """Set up the complete customer analysis reporting workflow"""
    # Create the report template
    template = await create_customer_purchase_report()
    print(f"Created report template: {template.id}")
    
    # Set up monthly trigger
    trigger = await setup_monthly_trigger(template.id)
    print(f"Created monthly trigger: {trigger.id}")
    
    # Configure outputs
    outputs = await configure_outputs(template.id)
    print(f"Created {len(outputs)} output configurations")
    
    print("\nCustomer Analysis Report setup complete!")
    print("You can now:")
    print("1. Access the report data through the API: /api/reports/customer-analysis/{customer_id}")
    print("2. View the report in the web UI with the <customer-analysis-view> component")
    print("3. Generate reports from the CLI: reports customer-analysis generate --customer-id <id>")
    print("4. Wait for automatic monthly execution on the last day of each month")
    
    return {
        "template_id": template.id,
        "trigger_id": trigger.id,
        "output_ids": [o.id for o in outputs]
    }

# To run the setup
if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_customer_analysis_reporting())
```

## Conclusion

You've now created a complete custom reporting workflow that includes:

1. A comprehensive report template with calculated fields and SQL queries
2. A scheduled monthly trigger
3. Multiple output formats including PDF with visualizations
4. Data preparation hooks for advanced analytics
5. A CLI command for manual report generation
6. A web component for viewing reports
7. API endpoints for accessing report data and exports

This implementation demonstrates the flexibility and power of the UNO reporting system. You can extend this pattern to create additional reports tailored to your specific business needs.

### Next Steps

- Create additional report templates for other business domains
- Implement more advanced data visualizations
- Set up event-based triggers for real-time reporting
- Create dashboards that combine multiple reports
- Implement access controls for sensitive report data

For more advanced features, refer to the [Advanced Reporting Features](advanced_features.md) documentation.