# Reporting System Use Cases

This document provides practical examples of how to implement the UNO reporting system for common business scenarios across different domains.

## E-commerce Platform

### 1. Sales Performance Dashboard

**Purpose:** Monitor sales performance across products, categories, and time periods.

```python
from uno.reports.models import ReportTemplate, ReportField, ReportTrigger, ReportOutput
from uno.reports.services import ReportTemplateService, ReportTriggerService, ReportOutputService
from uno.dependencies.container import get_container

async def create_sales_dashboard():```

container = get_container()
template_service = container.get(ReportTemplateService)
trigger_service = container.get(ReportTriggerService)
output_service = container.get(ReportOutputService)
``````

```
```

# Template definition
fields = [```

ReportField(name="date_range", type="parameter", parameter_type="daterange"),
ReportField(name="total_sales", source="orders.sum(total)", format="currency"),
ReportField(name="order_count", source="orders.count()"),
ReportField(name="average_order_value", type="calculated", 
           calculation={"type": "formula", "expression": "total_sales / order_count"}),
ReportField(name="top_products", type="sql", 
           sql_definition={
               "query": """
                   SELECT p.name, SUM(oi.quantity) as units_sold, 
                          SUM(oi.price * oi.quantity) as revenue
                   FROM order_items oi
                   JOIN products p ON oi.product_id = p.id
                   JOIN orders o ON oi.order_id = o.id
                   WHERE o.created_at BETWEEN :start_date AND :end_date
                   GROUP BY p.name
                   ORDER BY revenue DESC
                   LIMIT 10
               """,
               "parameters": ["start_date", "end_date"]
           }),
ReportField(name="sales_by_category", type="sql",
            sql_definition={
                "query": """
                    SELECT pc.name, COUNT(DISTINCT o.id) as order_count, 
                           SUM(oi.price * oi.quantity) as revenue
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    JOIN product_categories pc ON p.category_id = pc.id
                    JOIN orders o ON oi.order_id = o.id
                    WHERE o.created_at BETWEEN :start_date AND :end_date
                    GROUP BY pc.name
                    ORDER BY revenue DESC
                """,
                "parameters": ["start_date", "end_date"]
            }),
ReportField(name="daily_sales", type="sql",
            sql_definition={
                "query": """
                    SELECT DATE_TRUNC('day', o.created_at) as date,
                           COUNT(*) as order_count,
                           SUM(o.total) as revenue
                    FROM orders o
                    WHERE o.created_at BETWEEN :start_date AND :end_date
                    GROUP BY DATE_TRUNC('day', o.created_at)
                    ORDER BY date
                """,
                "parameters": ["start_date", "end_date"]
            })
```
]
``````

```
```

template = ReportTemplate(```

name="Sales Performance Dashboard",
description="Comprehensive overview of sales performance",
entity_type="store",
fields=fields,
metadata={"category": "Sales", "refresh_frequency": "daily"}
```
)
``````

```
```

template_result = await template_service.create(template)
if template_result.is_failure():```

raise Exception(f"Failed to create template: {template_result.error}")
```
``````

```
```

template_id = template_result.value.id
``````

```
```

# Daily trigger
daily_trigger = ReportTrigger(```

template_id=template_id,
trigger_type="schedule",
schedule={"type": "cron", "expression": "0 5 * * *"},  # 5 AM daily
parameters={
    "start_date": "{{NOW.replace(hour=0,minute=0,second=0,microsecond=0) - timedelta(days=1)}}",
    "end_date": "{{NOW.replace(hour=23,minute=59,second=59,microsecond=999999) - timedelta(days=1)}}"
},
name="Daily Sales Report",
enabled=True
```
)
``````

```
```

daily_trigger_result = await trigger_service.create(daily_trigger)
``````

```
```

# Weekly trigger
weekly_trigger = ReportTrigger(```

template_id=template_id,
trigger_type="schedule",
schedule={"type": "cron", "expression": "0 6 * * 1"},  # 6 AM every Monday
parameters={
    "start_date": "{{(NOW - timedelta(days=7)).replace(hour=0,minute=0,second=0)}}",
    "end_date": "{{NOW.replace(hour=23,minute=59,second=59)}}"
},
name="Weekly Sales Report",
enabled=True
```
)
``````

```
```

weekly_trigger_result = await trigger_service.create(weekly_trigger)
``````

```
```

# Dashboard output
dashboard_output = ReportOutput(```

template_id=template_id,
output_type="dashboard",
config={
    "layout": [
        {"widget": "metric", "field": "total_sales", "title": "Total Sales", "width": 3},
        {"widget": "metric", "field": "order_count", "title": "Orders", "width": 3},
        {"widget": "metric", "field": "average_order_value", "title": "AOV", "width": 3},
        {"widget": "chart", "type": "line", "field": "daily_sales", "title": "Daily Sales Trend", 
         "x_field": "date", "y_field": "revenue", "width": 12},
        {"widget": "chart", "type": "bar", "field": "top_products", "title": "Top Products", 
         "x_field": "name", "y_field": "revenue", "width": 6},
        {"widget": "chart", "type": "pie", "field": "sales_by_category", "title": "Sales by Category", 
         "labels_field": "name", "values_field": "revenue", "width": 6}
    ]
}
```
)
``````

```
```

dashboard_output_result = await output_service.create(dashboard_output)
``````

```
```

# Email output for weekly report
email_output = ReportOutput(```

template_id=template_id,
output_type="email",
config={
    "recipients": ["sales@example.com", "management@example.com"],
    "subject": "Weekly Sales Report: {{parameters.start_date}} to {{parameters.end_date}}",
    "template_path": "templates/sales_report_email.html",
    "include_attachments": True,
    "attachment_formats": ["pdf", "xlsx"],
    "trigger_ids": [weekly_trigger_result.value.id]  # Only send for weekly trigger
}
```
)
``````

```
```

email_output_result = await output_service.create(email_output)
``````

```
```

return {```

"template_id": template_id,
"daily_trigger_id": daily_trigger_result.value.id,
"weekly_trigger_id": weekly_trigger_result.value.id,
"dashboard_output_id": dashboard_output_result.value.id,
"email_output_id": email_output_result.value.id
```
}
```
```

### 2. Inventory Alerts

**Purpose:** Monitor inventory levels and generate alerts for low stock items.

```python
async def create_inventory_alert_report():```

# Template definition
fields = [```

ReportField(name="threshold", type="parameter", parameter_type="number", default=10),
ReportField(name="low_stock_items", type="sql", 
           sql_definition={
               "query": """
                   SELECT 
                       p.id as product_id,
                       p.name as product_name,
                       p.sku,
                       i.quantity as current_stock,
                       p.reorder_level,
                       s.name as supplier_name,
                       s.contact_email,
                       CASE 
                           WHEN i.quantity = 0 THEN 'Out of Stock'
                           WHEN i.quantity <= p.reorder_level THEN 'Reorder'
                           WHEN i.quantity <= :threshold THEN 'Low Stock'
                           ELSE 'OK'
                       END as status
                   FROM 
                       products p
                   JOIN 
                       inventory i ON p.id = i.product_id
                   LEFT JOIN
                       suppliers s ON p.primary_supplier_id = s.id
                   WHERE 
                       i.quantity <= :threshold
                   ORDER BY
                       i.quantity ASC
               """,
               "parameters": ["threshold"]
           })
```
]
``````

```
```

template = ReportTemplate(```

name="Inventory Alert Report",
description="Identifies products with low inventory levels",
entity_type="inventory",
fields=fields
```
)
``````

```
```

# Create template```
```

container = get_container()
template_service = container.get(ReportTemplateService)
trigger_service = container.get(ReportTriggerService)
output_service = container.get(ReportOutputService)
``````

```
```

template_result = await template_service.create(template)```
```

template_id = template_result.value.id
``````

```
```

# Daily check trigger
daily_trigger = ReportTrigger(```

template_id=template_id,
trigger_type="schedule",
schedule={"type": "cron", "expression": "0 7 * * *"},  # 7 AM daily
parameters={"threshold": 10},
name="Daily Inventory Check",
enabled=True
```
)
``````

```
```

daily_trigger_result = await trigger_service.create(daily_trigger)
``````

```
```

# Event-based trigger (when inventory is updated)
event_trigger = ReportTrigger(```

template_id=template_id,
trigger_type="event",
event_type="inventory.updated",
event_filter={
    "condition": "inventory.quantity <= 10"
},
parameters={"threshold": 10},
name="Real-time Inventory Alert",
enabled=True
```
)
``````

```
```

event_trigger_result = await trigger_service.create(event_trigger)
``````

```
```

# Email notifications
email_output = ReportOutput(```

template_id=template_id,
output_type="email",
config={
    "recipients": ["inventory@example.com"],
    "subject": "Inventory Alert: {{low_stock_items.length}} items below threshold",
    "template_path": "templates/inventory_alert_email.html",
    "condition": "low_stock_items.length > 0"  # Only send if there are alerts
}
```
)
``````

```
```

email_output_result = await output_service.create(email_output)
``````

```
```

# Slack/Teams notification
notification_output = ReportOutput(```

template_id=template_id,
output_type="webhook",
config={
    "url": "{{config.inventory_webhook_url}}",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": {
        "text": "🚨 Inventory Alert: {{low_stock_items.length}} items below threshold",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Inventory Alert Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "{{low_stock_items.length}} products are below the threshold of {{parameters.threshold}} units."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "{{#each low_stock_items}}\n• {{this.product_name}}: {{this.current_stock}} units ({{this.status}})\n{{/each}}"
                }
            }
        ]
    },
    "condition": "low_stock_items.length > 0"  # Only send if there are alerts
}
```
)
``````

```
```

notification_output_result = await output_service.create(notification_output)
``````

```
```

return {```

"template_id": template_id,
"daily_trigger_id": daily_trigger_result.value.id,
"event_trigger_id": event_trigger_result.value.id,
"email_output_id": email_output_result.value.id,
"notification_output_id": notification_output_result.value.id
```
}
```
```

## Healthcare System

### 1. Patient Visit Summary

**Purpose:** Generate comprehensive visit summaries for patients after appointments.

```python
async def create_patient_visit_summary():```

# Template definition
fields = [```

ReportField(name="visit_id", type="parameter", parameter_type="string"),
ReportField(name="patient_info", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       p.id, p.first_name, p.last_name, p.date_of_birth,
                       p.gender, p.phone, p.email,
                       a.street, a.city, a.state, a.postal_code
                   FROM 
                       patients p
                   LEFT JOIN 
                       patient_addresses a ON p.id = a.patient_id AND a.is_primary = true
                   WHERE 
                       p.id = (SELECT patient_id FROM visits WHERE id = :visit_id)
               """,
               "parameters": ["visit_id"]
           }),
ReportField(name="visit_details", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       v.id, v.visit_date, v.visit_type,
                       v.chief_complaint, v.diagnosis,
                       d.first_name || ' ' || d.last_name as provider_name,
                       d.specialty
                   FROM 
                       visits v
                   JOIN
                       doctors d ON v.doctor_id = d.id
                   WHERE 
                       v.id = :visit_id
               """,
               "parameters": ["visit_id"]
           }),
ReportField(name="vitals", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       weight, height, temperature, 
                       blood_pressure_systolic, blood_pressure_diastolic,
                       pulse, respiratory_rate, oxygen_saturation
                   FROM 
                       vitals
                   WHERE 
                       visit_id = :visit_id
                   ORDER BY 
                       recorded_at DESC
                   LIMIT 1
               """,
               "parameters": ["visit_id"]
           }),
ReportField(name="medications", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       m.name, p.dosage, p.frequency, p.instructions,
                       p.start_date, p.end_date
                   FROM 
                       prescriptions p
                   JOIN
                       medications m ON p.medication_id = m.id
                   WHERE 
                       p.visit_id = :visit_id
                   ORDER BY
                       p.created_at DESC
               """,
               "parameters": ["visit_id"]
           }),
ReportField(name="lab_results", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       l.test_name, l.result, l.unit, l.reference_range,
                       l.performed_date, l.is_abnormal
                   FROM 
                       lab_results l
                   WHERE 
                       l.visit_id = :visit_id
                   ORDER BY
                       l.performed_date DESC
               """,
               "parameters": ["visit_id"]
           }),
ReportField(name="followup_instructions", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       fi.instructions, fi.followup_date,
                       CASE 
                           WHEN a.id IS NOT NULL THEN TRUE
                           ELSE FALSE
                       END as has_appointment
                   FROM 
                       followup_instructions fi
                   LEFT JOIN
                       appointments a ON fi.visit_id = a.related_visit_id AND a.status = 'scheduled'
                   WHERE 
                       fi.visit_id = :visit_id
               """,
               "parameters": ["visit_id"]
           })
```
]
``````

```
```

template = ReportTemplate(```

name="Patient Visit Summary",
description="Comprehensive summary of a patient visit",
entity_type="visit",
fields=fields
```
)
``````

```
```

# Create template```
```

container = get_container()
template_service = container.get(ReportTemplateService)
trigger_service = container.get(ReportTriggerService)
output_service = container.get(ReportOutputService)
``````

```
```

template_result = await template_service.create(template)```
```

template_id = template_result.value.id
``````

```
```

# Event-based trigger (when visit is completed)
event_trigger = ReportTrigger(```

template_id=template_id,
trigger_type="event",
event_type="visit.completed",
parameters={"visit_id": "{{event.data.visit_id}}"},
name="Visit Completion Summary",
enabled=True
```
)
``````

```
```

event_trigger_result = await trigger_service.create(event_trigger)
``````

```
```

# PDF output
pdf_output = ReportOutput(```

template_id=template_id,
output_type="pdf",
config={
    "template_path": "templates/visit_summary.html",
    "paper_size": "Letter",
    "orientation": "portrait",
    "filename": "Visit_Summary_{{visit_details.visit_date}}.pdf"
}
```
)
``````

```
```

pdf_output_result = await output_service.create(pdf_output)
``````

```
```

# Email output
email_output = ReportOutput(```

template_id=template_id,
output_type="email",
config={
    "recipients": ["{{patient_info.email}}"],
    "subject": "Your Visit Summary for {{visit_details.visit_date}}",
    "template_path": "templates/visit_summary_email.html",
    "include_attachments": True,
    "attachment_formats": ["pdf"]
}
```
)
``````

```
```

email_output_result = await output_service.create(email_output)
``````

```
```

# Portal output
portal_output = ReportOutput(```

template_id=template_id,
output_type="portal",
config={
    "destination": "patient_documents",
    "category": "visit_summaries",
    "patient_id_field": "patient_info.id"
}
```
)
``````

```
```

portal_output_result = await output_service.create(portal_output)
``````

```
```

return {```

"template_id": template_id,
"event_trigger_id": event_trigger_result.value.id,
"pdf_output_id": pdf_output_result.value.id,
"email_output_id": email_output_result.value.id,
"portal_output_id": portal_output_result.value.id
```
}
```
```

### 2. Provider Performance Metrics

**Purpose:** Track and analyze provider performance metrics for quality improvement.

```python
async def create_provider_performance_report():```

# Template definition
fields = [```

ReportField(name="date_range", type="parameter", parameter_type="daterange"),
ReportField(name="provider_id", type="parameter", parameter_type="string", required=False),
ReportField(name="provider_metrics", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       d.id as provider_id,
                       d.first_name || ' ' || d.last_name as provider_name,
                       d.specialty,
                       COUNT(v.id) as visit_count,
                       AVG(EXTRACT(EPOCH FROM (v.end_time - v.start_time))/60) as avg_visit_duration,
                       AVG(s.satisfaction_score) as avg_satisfaction,
                       COUNT(DISTINCT p.id) as unique_patients,
                       SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END) as no_shows,
                       COUNT(a.id) as total_appointments,
                       SUM(CASE WHEN a.status = 'no_show' THEN 1 ELSE 0 END)::float / COUNT(a.id) as no_show_rate
                   FROM 
                       doctors d
                   LEFT JOIN
                       visits v ON d.id = v.doctor_id AND 
                                  v.visit_date BETWEEN :start_date AND :end_date
                   LEFT JOIN
                       patients p ON v.patient_id = p.id
                   LEFT JOIN
                       satisfaction_surveys s ON v.id = s.visit_id
                   LEFT JOIN
                       appointments a ON d.id = a.doctor_id AND 
                                        a.appointment_date BETWEEN :start_date AND :end_date
                   WHERE
                       d.id = COALESCE(:provider_id, d.id)
                   GROUP BY
                       d.id, d.first_name, d.last_name, d.specialty
                   ORDER BY
                       visit_count DESC
               """,
               "parameters": ["start_date", "end_date", "provider_id"]
           }),
ReportField(name="visit_types", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       d.id as provider_id,
                       d.first_name || ' ' || d.last_name as provider_name,
                       v.visit_type,
                       COUNT(v.id) as count,
                       COUNT(v.id)::float / SUM(COUNT(v.id)) OVER (PARTITION BY d.id) as percentage
                   FROM 
                       doctors d
                   JOIN
                       visits v ON d.id = v.doctor_id AND 
                                  v.visit_date BETWEEN :start_date AND :end_date
                   WHERE
                       d.id = COALESCE(:provider_id, d.id)
                   GROUP BY
                       d.id, d.first_name, d.last_name, v.visit_type
                   ORDER BY
                       d.id, count DESC
               """,
               "parameters": ["start_date", "end_date", "provider_id"]
           }),
ReportField(name="common_diagnoses", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       d.id as provider_id,
                       d.first_name || ' ' || d.last_name as provider_name,
                       v.diagnosis,
                       COUNT(v.id) as count,
                       COUNT(v.id)::float / SUM(COUNT(v.id)) OVER (PARTITION BY d.id) as percentage
                   FROM 
                       doctors d
                   JOIN
                       visits v ON d.id = v.doctor_id AND 
                                  v.visit_date BETWEEN :start_date AND :end_date
                   WHERE
                       d.id = COALESCE(:provider_id, d.id) AND
                       v.diagnosis IS NOT NULL
                   GROUP BY
                       d.id, d.first_name, d.last_name, v.diagnosis
                   ORDER BY
                       d.id, count DESC
                   LIMIT 20
               """,
               "parameters": ["start_date", "end_date", "provider_id"]
           }),
ReportField(name="satisfaction_trend", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       d.id as provider_id,
                       d.first_name || ' ' || d.last_name as provider_name,
                       DATE_TRUNC('week', v.visit_date) as week,
                       AVG(s.satisfaction_score) as avg_satisfaction,
                       COUNT(s.id) as survey_count
                   FROM 
                       doctors d
                   JOIN
                       visits v ON d.id = v.doctor_id AND 
                                  v.visit_date BETWEEN :start_date AND :end_date
                   JOIN
                       satisfaction_surveys s ON v.id = s.visit_id
                   WHERE
                       d.id = COALESCE(:provider_id, d.id)
                   GROUP BY
                       d.id, d.first_name, d.last_name, week
                   ORDER BY
                       d.id, week
               """,
               "parameters": ["start_date", "end_date", "provider_id"]
           })
```
]
``````

```
```

template = ReportTemplate(```

name="Provider Performance Metrics",
description="Analytics on provider performance and patient satisfaction",
entity_type="provider",
fields=fields
```
)
``````

```
```

# Create template```
```

container = get_container()
template_service = container.get(ReportTemplateService)
trigger_service = container.get(ReportTriggerService)
output_service = container.get(ReportOutputService)
``````

```
```

template_result = await template_service.create(template)```
```

template_id = template_result.value.id
``````

```
```

# Monthly schedule trigger
monthly_trigger = ReportTrigger(```

template_id=template_id,
trigger_type="schedule",
schedule={"type": "cron", "expression": "0 5 1 * *"},  # 5 AM on the 1st of each month
parameters={
    "start_date": "{{(NOW.replace(day=1) - timedelta(days=1)).replace(day=1)}}",  # First day of previous month
    "end_date": "{{NOW.replace(day=1) - timedelta(days=1)}}"  # Last day of previous month
},
name="Monthly Provider Performance",
enabled=True
```
)
``````

```
```

monthly_trigger_result = await trigger_service.create(monthly_trigger)
``````

```
```

# Dashboard output
dashboard_output = ReportOutput(```

template_id=template_id,
output_type="dashboard",
config={
    "layout": [
        {"widget": "table", "field": "provider_metrics", "title": "Provider Metrics Overview", "width": 12},
        {"widget": "chart", "type": "bar", "field": "visit_types", "title": "Visit Types by Provider", 
         "x_field": "provider_name", "y_field": "count", "group_by": "visit_type", "width": 6},
        {"widget": "chart", "type": "line", "field": "satisfaction_trend", "title": "Satisfaction Trends", 
         "x_field": "week", "y_field": "avg_satisfaction", "group_by": "provider_name", "width": 6},
        {"widget": "chart", "type": "horizontal_bar", "field": "common_diagnoses", "title": "Top Diagnoses", 
         "x_field": "diagnosis", "y_field": "count", "limit": 10, "width": 12}
    ]
}
```
)
``````

```
```

dashboard_output_result = await output_service.create(dashboard_output)
``````

```
```

# PDF output for individual provider reports
pdf_output = ReportOutput(```

template_id=template_id,
output_type="pdf",
config={
    "template_path": "templates/provider_performance.html",
    "paper_size": "Letter",
    "orientation": "portrait",
    "group_by": "provider_metrics.provider_id",  # Generate separate PDFs for each provider
    "filename": "Performance_{{provider_metrics.provider_name}}_{{parameters.start_date}}_to_{{parameters.end_date}}.pdf"
}
```
)
``````

```
```

pdf_output_result = await output_service.create(pdf_output)
``````

```
```

# Email output
email_output = ReportOutput(```

template_id=template_id,
output_type="email",
config={
    "recipients": ["management@example.com"],
    "subject": "Provider Performance Report: {{parameters.start_date}} to {{parameters.end_date}}",
    "template_path": "templates/provider_performance_email.html",
    "include_attachments": True,
    "attachment_formats": ["pdf"]
}
```
)
``````

```
```

email_output_result = await output_service.create(email_output)
``````

```
```

return {```

"template_id": template_id,
"monthly_trigger_id": monthly_trigger_result.value.id,
"dashboard_output_id": dashboard_output_result.value.id,
"pdf_output_id": pdf_output_result.value.id,
"email_output_id": email_output_result.value.id
```
}
```
```

## Financial Services

### 1. Investment Portfolio Analysis

**Purpose:** Provide clients with detailed analysis of their investment portfolios.

```python
async def create_portfolio_analysis_report():```

# Template definition
fields = [```

ReportField(name="client_id", type="parameter", parameter_type="string"),
ReportField(name="client_info", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       c.id, c.first_name, c.last_name, c.email,
                       c.risk_profile, c.investment_goal
                   FROM 
                       clients c
                   WHERE 
                       c.id = :client_id
               """,
               "parameters": ["client_id"]
           }),
ReportField(name="portfolio_summary", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       SUM(p.current_value) as total_value,
                       SUM(p.invested_amount) as total_invested,
                       (SUM(p.current_value) - SUM(p.invested_amount)) as total_gain_loss,
                       ((SUM(p.current_value) - SUM(p.invested_amount)) / SUM(p.invested_amount) * 100) as total_return_percentage,
                       AVG(p.annual_return) as avg_annual_return
                   FROM 
                       portfolios p
                   WHERE 
                       p.client_id = :client_id AND p.is_active = true
               """,
               "parameters": ["client_id"]
           }),
ReportField(name="asset_allocation", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       a.asset_class,
                       SUM(h.current_value) as value,
                       SUM(h.current_value) / (
                           SELECT SUM(h2.current_value) 
                           FROM holdings h2 
                           JOIN assets a2 ON h2.asset_id = a2.id
                           JOIN portfolios p2 ON h2.portfolio_id = p2.id
                           WHERE p2.client_id = :client_id AND p2.is_active = true
                       ) * 100 as percentage
                   FROM 
                       holdings h
                   JOIN
                       assets a ON h.asset_id = a.id
                   JOIN
                       portfolios p ON h.portfolio_id = p.id
                   WHERE 
                       p.client_id = :client_id AND p.is_active = true
                   GROUP BY
                       a.asset_class
                   ORDER BY
                       value DESC
               """,
               "parameters": ["client_id"]
           }),
ReportField(name="top_holdings", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       a.symbol, a.name, a.asset_class,
                       h.shares, h.current_value,
                       h.current_value / (
                           SELECT SUM(h2.current_value) 
                           FROM holdings h2 
                           JOIN portfolios p2 ON h2.portfolio_id = p2.id
                           WHERE p2.client_id = :client_id AND p2.is_active = true
                       ) * 100 as percentage,
                       h.purchase_price, h.current_price,
                       ((h.current_price - h.purchase_price) / h.purchase_price * 100) as price_change_percent
                   FROM 
                       holdings h
                   JOIN
                       assets a ON h.asset_id = a.id
                   JOIN
                       portfolios p ON h.portfolio_id = p.id
                   WHERE 
                       p.client_id = :client_id AND p.is_active = true
                   ORDER BY
                       h.current_value DESC
                   LIMIT 10
               """,
               "parameters": ["client_id"]
           }),
ReportField(name="performance_history", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       ph.date,
                       SUM(ph.value) as portfolio_value,
                       SUM(ph.invested_amount) as invested_amount,
                       (SUM(ph.value) - SUM(ph.invested_amount)) / SUM(ph.invested_amount) * 100 as return_percentage
                   FROM 
                       portfolio_history ph
                   JOIN
                       portfolios p ON ph.portfolio_id = p.id
                   WHERE 
                       p.client_id = :client_id AND p.is_active = true
                       AND ph.date >= CURRENT_DATE - INTERVAL '1 year'
                   GROUP BY
                       ph.date
                   ORDER BY
                       ph.date
               """,
               "parameters": ["client_id"]
           }),
ReportField(name="risk_metrics", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       AVG(a.volatility) as avg_volatility,
                       AVG(a.beta) as avg_beta,
                       SUM(a.beta * h.current_value) / SUM(h.current_value) as portfolio_beta,
                       AVG(a.sharpe_ratio) as avg_sharpe_ratio
                   FROM 
                       holdings h
                   JOIN
                       assets a ON h.asset_id = a.id
                   JOIN
                       portfolios p ON h.portfolio_id = p.id
                   WHERE 
                       p.client_id = :client_id AND p.is_active = true
               """,
               "parameters": ["client_id"]
           }),
ReportField(name="recommendations", type="sql",
           sql_definition={
               "query": """
                   WITH client_profile AS (
                       SELECT risk_profile, investment_goal FROM clients WHERE id = :client_id
                   ),
                   client_holdings AS (
                       SELECT a.id as asset_id
                       FROM holdings h
                       JOIN assets a ON h.asset_id = a.id
                       JOIN portfolios p ON h.portfolio_id = p.id
                       WHERE p.client_id = :client_id AND p.is_active = true
                   )
                   SELECT 
                       a.symbol, a.name, a.asset_class,
                       a.current_price, a.target_price,
                       ((a.target_price - a.current_price) / a.current_price * 100) as potential_return,
                       r.recommendation_type, r.rationale
                   FROM 
                       asset_recommendations r
                   JOIN
                       assets a ON r.asset_id = a.id
                   CROSS JOIN
                       client_profile cp
                   LEFT JOIN
                       client_holdings ch ON a.id = ch.asset_id
                   WHERE 
                       r.risk_profile = cp.risk_profile
                       AND r.is_active = true
                       AND ch.asset_id IS NULL
                   ORDER BY
                       potential_return DESC
                   LIMIT 5
               """,
               "parameters": ["client_id"]
           })
```
]
``````

```
```

template = ReportTemplate(```

name="Investment Portfolio Analysis",
description="Detailed analysis of client investment portfolio",
entity_type="portfolio",
fields=fields
```
)
``````

```
```

# Create template```
```

container = get_container()
template_service = container.get(ReportTemplateService)
trigger_service = container.get(ReportTriggerService)
output_service = container.get(ReportOutputService)
``````

```
```

template_result = await template_service.create(template)```
```

template_id = template_result.value.id
``````

```
```

# Quarterly schedule trigger
quarterly_trigger = ReportTrigger(```

template_id=template_id,
trigger_type="schedule",
schedule={"type": "cron", "expression": "0 7 1 1,4,7,10 *"},  # Jan, Apr, Jul, Oct 1st
parameters={
    "client_id": "{{loop.clients.id}}"  # Loop through all active clients
},
loop_config={
    "entity": "clients",
    "filter": {"is_active": True},
    "batch_size": 50,
    "pause_between_batches": 300  # 5 minutes between batches
},
name="Quarterly Portfolio Analysis",
enabled=True
```
)
``````

```
```

quarterly_trigger_result = await trigger_service.create(quarterly_trigger)
``````

```
```

# On-demand API trigger (for client portal)
api_trigger = ReportTrigger(```

template_id=template_id,
trigger_type="api",
required_parameters=["client_id"],
name="On-demand Portfolio Analysis",
enabled=True
```
)
``````

```
```

api_trigger_result = await trigger_service.create(api_trigger)
``````

```
```

# PDF output
pdf_output = ReportOutput(```

template_id=template_id,
output_type="pdf",
config={
    "template_path": "templates/portfolio_analysis.html",
    "paper_size": "Letter",
    "orientation": "portrait",
    "filename": "Portfolio_Analysis_{{client_info.last_name}}_{{NOW.strftime('%Y-%m-%d')}}.pdf",
    "visualizations": [
        {
            "type": "pie_chart",
            "title": "Asset Allocation",
            "data_field": "asset_allocation",
            "labels_field": "asset_class",
            "values_field": "percentage"
        },
        {
            "type": "line_chart",
            "title": "Performance History",
            "data_field": "performance_history",
            "x_field": "date",
            "y_field": "portfolio_value"
        }
    ]
}
```
)
``````

```
```

pdf_output_result = await output_service.create(pdf_output)
``````

```
```

# Email output
email_output = ReportOutput(```

template_id=template_id,
output_type="email",
config={
    "recipients": ["{{client_info.email}}"],
    "subject": "Your Quarterly Portfolio Analysis",
    "template_path": "templates/portfolio_email.html",
    "include_attachments": True,
    "attachment_formats": ["pdf"],
    "cc": ["{{client_info.advisor_email}}"]
}
```
)
``````

```
```

email_output_result = await output_service.create(email_output)
``````

```
```

# Client portal output
portal_output = ReportOutput(```

template_id=template_id,
output_type="portal",
config={
    "destination": "client_reports",
    "dashboard_config": {
        "widgets": [
            {"type": "stats", "field": "portfolio_summary", "title": "Portfolio Summary"},
            {"type": "pie_chart", "field": "asset_allocation", "title": "Asset Allocation"},
            {"type": "table", "field": "top_holdings", "title": "Top Holdings"},
            {"type": "line_chart", "field": "performance_history", "title": "Performance History"},
            {"type": "recommendations", "field": "recommendations", "title": "Recommendations"}
        ]
    }
}
```
)
``````

```
```

portal_output_result = await output_service.create(portal_output)
``````

```
```

return {```

"template_id": template_id,
"quarterly_trigger_id": quarterly_trigger_result.value.id,
"api_trigger_id": api_trigger_result.value.id,
"pdf_output_id": pdf_output_result.value.id,
"email_output_id": email_output_result.value.id,
"portal_output_id": portal_output_result.value.id
```
}
```
```

## Manufacturing & Supply Chain

### 1. Production Efficiency Report

**Purpose:** Monitor production efficiency across multiple facilities.

```python
async def create_production_efficiency_report():```

# Template definition
fields = [```

ReportField(name="date_range", type="parameter", parameter_type="daterange"),
ReportField(name="facility_id", type="parameter", parameter_type="string", required=False),
ReportField(name="production_summary", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       f.id as facility_id,
                       f.name as facility_name,
                       f.location,
                       COUNT(p.id) as production_runs,
                       SUM(p.units_produced) as total_units,
                       SUM(p.actual_runtime_hours) as total_runtime,
                       SUM(p.units_produced) / NULLIF(SUM(p.actual_runtime_hours), 0) as units_per_hour,
                       AVG(p.efficiency_percentage) as avg_efficiency,
                       SUM(p.defect_count) as total_defects,
                       SUM(p.defect_count)::float / NULLIF(SUM(p.units_produced), 0) * 100 as defect_rate,
                       SUM(p.downtime_hours) as total_downtime,
                       SUM(p.downtime_hours) / NULLIF(SUM(p.actual_runtime_hours + p.downtime_hours), 0) * 100 as downtime_percentage
                   FROM 
                       facilities f
                   LEFT JOIN
                       production_runs p ON f.id = p.facility_id AND 
                                           p.production_date BETWEEN :start_date AND :end_date
                   WHERE
                       f.id = COALESCE(:facility_id, f.id)
                   GROUP BY
                       f.id, f.name, f.location
                   ORDER BY
                       f.name
               """,
               "parameters": ["start_date", "end_date", "facility_id"]
           }),
ReportField(name="product_performance", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       pr.product_id,
                       p.name as product_name,
                       p.category,
                       SUM(pr.units_produced) as total_units,
                       SUM(pr.actual_runtime_hours) as total_runtime,
                       SUM(pr.units_produced) / NULLIF(SUM(pr.actual_runtime_hours), 0) as units_per_hour,
                       AVG(pr.efficiency_percentage) as avg_efficiency,
                       SUM(pr.defect_count) as total_defects,
                       SUM(pr.defect_count)::float / NULLIF(SUM(pr.units_produced), 0) * 100 as defect_rate
                   FROM 
                       production_runs pr
                   JOIN
                       products p ON pr.product_id = p.id
                   JOIN
                       facilities f ON pr.facility_id = f.id
                   WHERE
                       pr.production_date BETWEEN :start_date AND :end_date AND
                       f.id = COALESCE(:facility_id, f.id)
                   GROUP BY
                       pr.product_id, p.name, p.category
                   ORDER BY
                       total_units DESC
               """,
               "parameters": ["start_date", "end_date", "facility_id"]
           }),
ReportField(name="downtime_reasons", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       d.reason_category,
                       SUM(d.hours) as total_hours,
                       COUNT(d.id) as incident_count,
                       SUM(d.hours) / (
                           SELECT SUM(d2.hours) 
                           FROM downtime_incidents d2
                           JOIN production_runs pr2 ON d2.production_run_id = pr2.id
                           JOIN facilities f2 ON pr2.facility_id = f2.id
                           WHERE pr2.production_date BETWEEN :start_date AND :end_date AND
                                 f2.id = COALESCE(:facility_id, f2.id)
                       ) * 100 as percentage
                   FROM 
                       downtime_incidents d
                   JOIN
                       production_runs pr ON d.production_run_id = pr.id
                   JOIN
                       facilities f ON pr.facility_id = f.id
                   WHERE
                       pr.production_date BETWEEN :start_date AND :end_date AND
                       f.id = COALESCE(:facility_id, f.id)
                   GROUP BY
                       d.reason_category
                   ORDER BY
                       total_hours DESC
               """,
               "parameters": ["start_date", "end_date", "facility_id"]
           }),
ReportField(name="efficiency_trend", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       DATE_TRUNC('day', pr.production_date) as date,
                       f.id as facility_id,
                       f.name as facility_name,
                       AVG(pr.efficiency_percentage) as avg_efficiency,
                       SUM(pr.units_produced) as units_produced,
                       SUM(pr.defect_count)::float / NULLIF(SUM(pr.units_produced), 0) * 100 as defect_rate
                   FROM 
                       production_runs pr
                   JOIN
                       facilities f ON pr.facility_id = f.id
                   WHERE
                       pr.production_date BETWEEN :start_date AND :end_date AND
                       f.id = COALESCE(:facility_id, f.id)
                   GROUP BY
                       date, f.id, f.name
                   ORDER BY
                       date
               """,
               "parameters": ["start_date", "end_date", "facility_id"]
           }),
ReportField(name="shift_comparison", type="sql",
           sql_definition={
               "query": """
                   SELECT 
                       pr.shift,
                       f.name as facility_name,
                       COUNT(pr.id) as production_runs,
                       SUM(pr.units_produced) as total_units,
                       AVG(pr.efficiency_percentage) as avg_efficiency,
                       SUM(pr.defect_count)::float / NULLIF(SUM(pr.units_produced), 0) * 100 as defect_rate,
                       SUM(pr.downtime_hours) / NULLIF(SUM(pr.actual_runtime_hours + pr.downtime_hours), 0) * 100 as downtime_percentage
                   FROM 
                       production_runs pr
                   JOIN
                       facilities f ON pr.facility_id = f.id
                   WHERE
                       pr.production_date BETWEEN :start_date AND :end_date AND
                       f.id = COALESCE(:facility_id, f.id)
                   GROUP BY
                       pr.shift, f.name
                   ORDER BY
                       f.name, pr.shift
               """,
               "parameters": ["start_date", "end_date", "facility_id"]
           })
```
]
``````

```
```

template = ReportTemplate(```

name="Production Efficiency Report",
description="Analysis of manufacturing efficiency and performance",
entity_type="production",
fields=fields
```
)
``````

```
```

# Create template```
```

container = get_container()
template_service = container.get(ReportTemplateService)
trigger_service = container.get(ReportTriggerService)
output_service = container.get(ReportOutputService)
``````

```
```

template_result = await template_service.create(template)```
```

template_id = template_result.value.id
``````

```
```

# Weekly schedule trigger
weekly_trigger = ReportTrigger(```

template_id=template_id,
trigger_type="schedule",
schedule={"type": "cron", "expression": "0 6 * * 1"},  # 6 AM every Monday
parameters={
    "start_date": "{{(NOW - timedelta(days=7)).replace(hour=0,minute=0,second=0)}}",
    "end_date": "{{(NOW - timedelta(days=1)).replace(hour=23,minute=59,second=59)}}",
},
name="Weekly Production Report",
enabled=True
```
)
``````

```
```

weekly_trigger_result = await trigger_service.create(weekly_trigger)
``````

```
```

# Dashboard output
dashboard_output = ReportOutput(```

template_id=template_id,
output_type="dashboard",
config={
    "layout": [
        {"widget": "table", "field": "production_summary", "title": "Facility Production Summary", "width": 12},
        {"widget": "chart", "type": "line", "field": "efficiency_trend", "title": "Efficiency Trend", 
         "x_field": "date", "y_field": "avg_efficiency", "group_by": "facility_name", "width": 6},
        {"widget": "chart", "type": "line", "field": "efficiency_trend", "title": "Defect Rate Trend", 
         "x_field": "date", "y_field": "defect_rate", "group_by": "facility_name", "width": 6},
        {"widget": "chart", "type": "bar", "field": "product_performance", "title": "Product Performance", 
         "x_field": "product_name", "y_field": "units_per_hour", "limit": 10, "width": 6},
        {"widget": "chart", "type": "pie", "field": "downtime_reasons", "title": "Downtime Reasons", 
         "labels_field": "reason_category", "values_field": "percentage", "width": 6},
        {"widget": "chart", "type": "bar", "field": "shift_comparison", "title": "Shift Comparison", 
         "x_field": "shift", "y_field": "avg_efficiency", "group_by": "facility_name", "width": 12}
    ]
}
```
)
``````

```
```

dashboard_output_result = await output_service.create(dashboard_output)
``````

```
```

# Email output
email_output = ReportOutput(```

template_id=template_id,
output_type="email",
config={
    "recipients": ["operations@example.com", "facility_managers@example.com"],
    "subject": "Weekly Production Efficiency Report: {{parameters.start_date}} to {{parameters.end_date}}",
    "template_path": "templates/production_report_email.html",
    "include_attachments": True,
    "attachment_formats": ["pdf", "xlsx"]
}
```
)
``````

```
```

email_output_result = await output_service.create(email_output)
``````

```
```

# PDF output (per facility)
pdf_output = ReportOutput(```

template_id=template_id,
output_type="pdf",
config={
    "template_path": "templates/production_report.html",
    "paper_size": "A4",
    "orientation": "landscape",
    "group_by": "production_summary.facility_id",  # Generate separate PDFs for each facility
    "filename": "Production_Report_{{production_summary.facility_name}}_{{parameters.start_date}}_to_{{parameters.end_date}}.pdf"
}
```
)
``````

```
```

pdf_output_result = await output_service.create(pdf_output)
``````

```
```

return {```

"template_id": template_id,
"weekly_trigger_id": weekly_trigger_result.value.id,
"dashboard_output_id": dashboard_output_result.value.id,
"email_output_id": email_output_result.value.id,
"pdf_output_id": pdf_output_result.value.id
```
}
```
```

## Further Examples

For additional industry-specific report templates, see these resources:

1. [Education Reporting Templates](../project/examples/education_reports.md)
2. [Real Estate Analytics](../project/examples/real_estate_reports.md)
3. [Energy Consumption Reports](../project/examples/energy_reports.md)
4. [Logistics and Shipping Analytics](../project/examples/logistics_reports.md)

## Best Practices

When implementing custom reports for your domain:

1. **Start with the business question** - Identify the specific insights users need
2. **Design for the end-user** - Consider how the report will be consumed and by whom
3. **Optimize queries** - Use appropriate indexes and SQL optimization techniques
4. **Test with real data** - Validate reports with realistic data volumes
5. **Consider scalability** - Design reports to handle growing data volumes
6. **Implement security** - Ensure reports respect data access permissions
7. **Add visualizations** - Include relevant charts to highlight key insights
8. **Schedule appropriately** - Balance freshness needs with system load
9. **Provide context** - Include explanatory text and benchmarks where helpful
10. **Gather feedback** - Continuously improve based on user feedback

## Integration Patterns

Common integration patterns for the reporting system:

1. **Event-driven reporting** - Trigger reports based on business events
2. **ETL pipeline integration** - Generate reports after data warehouse updates
3. **API-based integration** - Allow third-party systems to request reports
4. **Embedded dashboards** - Integrate report visualizations in applications
5. **Alert systems** - Connect reports to notification systems for anomalies
6. **Mobile delivery** - Optimize reports for mobile consumption
7. **CRM integration** - Push customer reports to CRM systems
8. **BI tool integration** - Export report data to BI tools for further analysis