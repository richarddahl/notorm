# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Migration templates for the Uno migration system.

This module provides templates for creating SQL and Python migrations.
"""

import os
import string
import datetime
from typing import Dict, Any

# Directory where templates are stored
TEMPLATES_DIR = os.path.dirname(os.path.abspath(__file__))


def get_template_path(template_name: str) -> str:
    """
    Get the path to a template file.
    
    Args:
        template_name: Name of the template (e.g., "sql_migration.tpl")
        
    Returns:
        Path to the template file
    """
    return os.path.join(TEMPLATES_DIR, template_name)


def get_default_sql_template() -> str:
    """
    Get the default SQL migration template.
    
    Returns:
        Content of the template
    """
    template_path = get_template_path("sql_migration.tpl")
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            return f.read()
    else:
        # Fallback template if file doesn't exist
        return """-- Migration: ${name}
-- Created at: ${created_at}
-- Description: ${description}

-- === UP MIGRATION ===
-- Write your UP SQL migration script below this line
-- This script will be executed when applying the migration


-- === DOWN MIGRATION ===
-- Write your DOWN SQL migration script below this line
-- This script will be executed when reverting the migration
"""


def get_default_python_template() -> str:
    """
    Get the default Python migration template.
    
    Returns:
        Content of the template
    """
    template_path = get_template_path("python_migration.tpl")
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            return f.read()
    else:
        # Fallback template if file doesn't exist
        return """# Migration: ${name}
# Created at: ${created_at}
# Description: ${description}

from typing import Any
from uno.core.migrations.migration import Migration, MigrationBase, create_migration

# Function-based migration
async def up(context: Any) -> None:
    \"\"\"
    Apply the migration.
    
    Args:
        context: Migration context with database connection
    \"\"\"
    # Execute SQL or perform other migration steps
    pass

async def down(context: Any) -> None:
    \"\"\"
    Revert the migration.
    
    Args:
        context: Migration context with database connection
    \"\"\"
    # Execute SQL or perform other migration steps
    pass

# Alternatively, you can define a class-based migration:
# class ${class_name}(Migration):
#     def __init__(self):
#         base = create_migration(
#             name="${name}",
#             description="${description}"
#         )
#         super().__init__(base)
#     
#     async def apply(self, context: Any) -> None:
#         # Write your UP migration code here
#         pass
#     
#     async def revert(self, context: Any) -> None:
#         # Write your DOWN migration code here
#         pass
#     
#     def get_checksum(self) -> str:
#         import hashlib
#         return hashlib.md5(b"${name}").hexdigest()
"""


def render_template(template: str, context: Dict[str, Any]) -> str:
    """
    Render a template with the given context.
    
    Args:
        template: Template string
        context: Context variables for the template
        
    Returns:
        Rendered template
    """
    # Create a template and render it
    template = string.Template(template)
    return template.safe_substitute(context)


def create_migration_content(
    name: str,
    template_path: str = None,
    template_type: str = "sql",
    description: str = ""
) -> str:
    """
    Create migration content from a template.
    
    Args:
        name: Name of the migration
        template_path: Path to template file (optional)
        template_type: Type of migration (sql or python)
        description: Description of the migration
        
    Returns:
        Migration content
    """
    # Get the template content
    if template_path and os.path.exists(template_path):
        with open(template_path, 'r') as f:
            template = f.read()
    elif template_type == "sql":
        template = get_default_sql_template()
    else:
        template = get_default_python_template()
    
    # Create context for template rendering
    context = {
        "name": name,
        "description": description or f"Migration for {name}",
        "created_at": datetime.datetime.now().isoformat(),
        "class_name": "".join(word.title() for word in name.split("_"))
    }
    
    # Render the template
    return render_template(template, context)