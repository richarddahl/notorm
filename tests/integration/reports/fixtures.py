# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Fixtures for report integration tests."""

import uuid
from uno.reports.objs import (
    ReportFieldType,
    ReportTriggerType,
    ReportOutputType,
    ReportFormat,
)

# Sample template data
TEMPLATE_DATA = {
    "name": f"Integration Test Template {uuid.uuid4()}",
    "description": "Template for integration testing",
    "base_object_type": "customer",
    "format_config": {
        "title_format": "{name} - Generated on {date}",
        "show_footer": True
    },
    "parameter_definitions": {
        "start_date": {
            "type": "date",
            "required": True,
            "default": "today-30d"
        },
        "end_date": {
            "type": "date",
            "required": True,
            "default": "today"
        },
        "customer_type": {
            "type": "string",
            "required": False,
            "choices": ["individual", "business", "government"]
        }
    },
    "cache_policy": {
        "ttl_seconds": 3600,
        "invalidate_on_event": "customer_updated"
    },
    "version": "1.0.0"
}

# Sample field data
FIELD_DATA = {
    "name": f"test_field_{uuid.uuid4().hex[:8]}",
    "display_name": "Test Field",
    "description": "Field for integration testing",
    "field_type": ReportFieldType.DB_COLUMN,
    "field_config": {
        "table": "customer",
        "column": "name"
    },
    "order": 1,
    "format_string": None,
    "conditional_formats": None,
    "is_visible": True
}

# Sample trigger data
TRIGGER_DATA = {
    "trigger_type": ReportTriggerType.SCHEDULED,
    "trigger_config": {
        "timezone": "UTC",
        "run_on_holidays": False
    },
    "schedule": "interval:24:hours",
    "is_active": True
}

# Sample output data
OUTPUT_DATA = {
    "output_type": ReportOutputType.EMAIL,
    "output_config": {
        "recipients": ["test@example.com"],
        "subject": "Integration Test Report",
        "body": "Please find the attached report."
    },
    "format": ReportFormat.PDF,
    "format_config": {
        "page_size": "letter",
        "orientation": "portrait"
    },
    "is_active": True
}