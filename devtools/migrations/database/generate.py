"""Migration script generator.

This module provides utilities for generating migration scripts based on detected schema changes.
It integrates with SQLAlchemy models and Alembic to generate migration scripts.
"""
from typing import Dict, List, Optional, Set, Tuple, Any, Union, TextIO
import os
import datetime
import logging
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape
from sqlalchemy import MetaData, create_engine, Table, inspect
from sqlalchemy.engine import Engine

from uno.devtools.migrations.database.diff import SchemaDiff
from uno.core.migrations.migrator import get_revision_id  # Assuming this exists

logger = logging.getLogger(__name__)

# Templates for migration scripts
SCRIPT_TEMPLATES = {
    'python': {
        'header': '''"""{{ message }}

Revision ID: {{ revision }}
Revises: {{ down_revision or 'None' }}
Create Date: {{ create_date }}
"""
from alembic import op
import sqlalchemy as sa
{{ imports }}

# revision identifiers, used by Alembic.
revision = '{{ revision }}'
down_revision = {{ down_revision and "'%s'" % down_revision or 'None' }}
branch_labels = {{ branch_labels and 'list(%r)' % branch_labels or 'None' }}
depends_on = {{ depends_on and 'list(%r)' % depends_on or 'None' }}


def upgrade():
    {{ upgrade_ops }}


def downgrade():
    {{ downgrade_ops }}
''',
        'create_table': '''    # Create table {{ table_name }}
    op.create_table('{{ table_name }}',
        {%- for column in columns %}
        sa.Column('{{ column.name }}', {{ column.type }}, nullable={{ column.nullable }}{% if column.primary_key %}, primary_key=True{% endif %}{% if column.default %}, server_default=sa.text("{{ column.default }}"){% endif %}),
        {%- endfor %}
        {%- for constraint in constraints %}
        {{ constraint }},
        {%- endfor %}
        schema='{{ schema }}'
    )
''',
        'drop_table': '''    # Drop table {{ table_name }}
    op.drop_table('{{ table_name }}', schema='{{ schema }}')
''',
        'add_column': '''    # Add column {{ column.name }} to table {{ table_name }}
    op.add_column('{{ table_name }}', sa.Column('{{ column.name }}', {{ column.type }}, nullable={{ column.nullable }}{% if column.default %}, server_default=sa.text("{{ column.default }}"){% endif %}), schema='{{ schema }}')
''',
        'drop_column': '''    # Drop column {{ column_name }} from table {{ table_name }}
    op.drop_column('{{ table_name }}', '{{ column_name }}', schema='{{ schema }}')
''',
        'alter_column': '''    # Alter column {{ column_name }} in table {{ table_name }}
    {%- if change.get('type_changed') %}
    op.alter_column('{{ table_name }}', '{{ column_name }}', 
                    type_={{ change.get('new_type') }},
                    existing_type={{ change.get('old_type') }},
                    nullable={{ nullable }},
                    schema='{{ schema }}')
    {%- elif change.get('nullable_changed') %}
    op.alter_column('{{ table_name }}', '{{ column_name }}', 
                    nullable={{ change.get('new_nullable') }},
                    existing_nullable={{ change.get('old_nullable') }},
                    schema='{{ schema }}')
    {%- elif change.get('default_changed') %}
    op.alter_column('{{ table_name }}', '{{ column_name }}', 
                    server_default=sa.text("{{ change.get('new_default') }}"),
                    existing_server_default=sa.text("{{ change.get('old_default') }}"),
                    schema='{{ schema }}')
    {%- endif %}
''',
        'add_index': '''    # Add index on {{ table_name }}({{ columns|join(', ') }})
    op.create_index(op.f('{{ index_name }}'), '{{ table_name }}', {{ columns }}, unique={{ unique }}, schema='{{ schema }}')
''',
        'drop_index': '''    # Drop index {{ index_name }} on {{ table_name }}
    op.drop_index(op.f('{{ index_name }}'), table_name='{{ table_name }}', schema='{{ schema }}')
''',
        'add_constraint': '''    # Add constraint {{ constraint_name }} to {{ table_name }}
    op.create_{{ constraint_type }}_constraint('{{ constraint_name }}', '{{ table_name }}', {{ params }}, schema='{{ schema }}')
''',
        'drop_constraint': '''    # Drop constraint {{ constraint_name }} from {{ table_name }}
    op.drop_constraint('{{ constraint_name }}', '{{ table_name }}', type_='{{ constraint_type }}', schema='{{ schema }}')
'''
    },
    'sql': {
        'header': '''-- {{ message }}
-- Revision ID: {{ revision }}
-- Revises: {{ down_revision or 'None' }}
-- Create Date: {{ create_date }}

-- Set up transaction
BEGIN;

-- Schema operations
''',
        'footer': '''
-- Commit transaction
COMMIT;
''',
        'create_table': '''-- Create table {{ table_name }}
CREATE TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} (
    {%- for column in columns %}
    {{ column.name }} {{ column.type }}{% if not column.nullable %} NOT NULL{% endif %}{% if column.primary_key %} PRIMARY KEY{% endif %}{% if column.default %} DEFAULT {{ column.default }}{% endif %}{% if not loop.last %},{% endif %}
    {%- endfor %}
    {%- for constraint in constraints %}
    ,{{ constraint }}
    {%- endfor %}
);
''',
        'drop_table': '''-- Drop table {{ table_name }}
DROP TABLE IF EXISTS {% if schema %}{{ schema }}.{% endif %}{{ table_name }};
''',
        'add_column': '''-- Add column {{ column.name }} to table {{ table_name }}
ALTER TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} ADD COLUMN {{ column.name }} {{ column.type }}{% if not column.nullable %} NOT NULL{% endif %}{% if column.default %} DEFAULT {{ column.default }}{% endif %};
''',
        'drop_column': '''-- Drop column {{ column_name }} from table {{ table_name }}
ALTER TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} DROP COLUMN {{ column_name }};
''',
        'alter_column': '''-- Alter column {{ column_name }} in table {{ table_name }}
{%- if change.get('type_changed') %}
ALTER TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} ALTER COLUMN {{ column_name }} TYPE {{ change.get('new_type') }};
{%- endif %}
{%- if change.get('nullable_changed') %}
{% if change.get('new_nullable') %}
ALTER TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} ALTER COLUMN {{ column_name }} DROP NOT NULL;
{% else %}
ALTER TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} ALTER COLUMN {{ column_name }} SET NOT NULL;
{% endif %}
{%- endif %}
{%- if change.get('default_changed') %}
{% if change.get('new_default') %}
ALTER TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} ALTER COLUMN {{ column_name }} SET DEFAULT {{ change.get('new_default') }};
{% else %}
ALTER TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} ALTER COLUMN {{ column_name }} DROP DEFAULT;
{% endif %}
{%- endif %}
''',
        'add_index': '''-- Add index on {{ table_name }}({{ columns|join(', ') }})
CREATE {% if unique %}UNIQUE {% endif %}INDEX {{ index_name }} ON {% if schema %}{{ schema }}.{% endif %}{{ table_name }} ({{ columns|join(', ') }});
''',
        'drop_index': '''-- Drop index {{ index_name }} on {{ table_name }}
DROP INDEX IF EXISTS {% if schema %}{{ schema }}.{% endif %}{{ index_name }};
''',
        'add_constraint': '''-- Add constraint {{ constraint_name }} to {{ table_name }}
ALTER TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} ADD CONSTRAINT {{ constraint_name }} {{ constraint_def }};
''',
        'drop_constraint': '''-- Drop constraint {{ constraint_name }} from {{ table_name }}
ALTER TABLE {% if schema %}{{ schema }}.{% endif %}{{ table_name }} DROP CONSTRAINT IF EXISTS {{ constraint_name }};
'''
    }
}

def _format_date() -> str:
    """Format the current date for migration scripts."""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def _get_template_env():
    """Get the Jinja template environment."""
    # Try to use PackageLoader if templates are installed as a package
    try:
        return Environment(
            loader=PackageLoader('uno.devtools.migrations', 'templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
    except (ImportError, ModuleNotFoundError):
        # Fall back to dict-based templates
        class DictLoader:
            def __init__(self, templates):
                self.templates = templates
                
            def get_source(self, environment, template):
                if template not in self.templates:
                    raise Exception(f"Template {template} not found")
                source = self.templates[template]
                return source, None, lambda: True
        
        return Environment(
            loader=DictLoader(SCRIPT_TEMPLATES),
            autoescape=select_autoescape(['html', 'xml'])
        )

def generate_migration_script(
    diff: SchemaDiff, 
    output_dir: Union[str, Path],
    message: str,
    format: str = 'python',
    down_revision: Optional[str] = None,
    branch_labels: Optional[List[str]] = None,
    depends_on: Optional[List[str]] = None,
    schema: str = 'public'
) -> Path:
    """Generate a migration script from a schema diff.
    
    Args:
        diff: SchemaDiff instance with detected differences
        output_dir: Directory where the migration script will be saved
        message: Message describing the migration
        format: Format of the migration script ('python' or 'sql')
        down_revision: Previous revision ID (for alembic)
        branch_labels: Branch labels (for alembic)
        depends_on: Dependencies (for alembic)
        schema: Database schema name
        
    Returns:
        Path to the generated migration script
    """
    if not diff.has_changes:
        logger.info("No changes detected, skipping migration script generation")
        return None
    
    # Ensure the output directory exists
    output_dir = Path(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Get a new revision ID
    revision = get_revision_id()
    
    # Choose template format
    templates = SCRIPT_TEMPLATES.get(format, SCRIPT_TEMPLATES['python'])
    
    # Create content
    env = _get_template_env()
    
    # Generate upgrade and downgrade operations
    upgrade_ops = []
    downgrade_ops = []
    
    # Handle table additions/removals
    for table_name in diff.added_tables:
        # For now, just add placeholder - detailed implementation would need table structure
        if format == 'python':
            upgrade_ops.append(f"    # TODO: Create table {table_name}")
            downgrade_ops.append(f"    # TODO: Drop table {table_name}")
        else:  # SQL
            upgrade_ops.append(f"-- TODO: Create table {table_name}")
            downgrade_ops.append(f"-- TODO: Drop table {table_name}")
    
    for table_name in diff.removed_tables:
        if format == 'python':
            upgrade_ops.append(f"    # TODO: Drop table {table_name}")
            downgrade_ops.append(f"    # TODO: Create table {table_name}")
        else:  # SQL
            upgrade_ops.append(f"-- TODO: Drop table {table_name}")
            downgrade_ops.append(f"-- TODO: Create table {table_name}")
    
    # Handle column additions/removals
    for table_name, columns in diff.added_columns.items():
        for col_name in columns:
            if format == 'python':
                upgrade_ops.append(f"    # TODO: Add column {col_name} to table {table_name}")
                downgrade_ops.append(f"    # TODO: Drop column {col_name} from table {table_name}")
            else:  # SQL
                upgrade_ops.append(f"-- TODO: Add column {col_name} to table {table_name}")
                downgrade_ops.append(f"-- TODO: Drop column {col_name} from table {table_name}")
    
    for table_name, columns in diff.removed_columns.items():
        for col_name in columns:
            if format == 'python':
                upgrade_ops.append(f"    # TODO: Drop column {col_name} from table {table_name}")
                downgrade_ops.append(f"    # TODO: Add column {col_name} to table {table_name}")
            else:  # SQL
                upgrade_ops.append(f"-- TODO: Drop column {col_name} from table {table_name}")
                downgrade_ops.append(f"-- TODO: Add column {col_name} to table {table_name}")
    
    # Handle column modifications
    for table_name, columns in diff.modified_columns.items():
        for col_name, changes in columns.items():
            if format == 'python':
                upgrade_ops.append(f"    # TODO: Modify column {col_name} in table {table_name}")
                downgrade_ops.append(f"    # TODO: Revert changes to column {col_name} in table {table_name}")
            else:  # SQL
                upgrade_ops.append(f"-- TODO: Modify column {col_name} in table {table_name}")
                downgrade_ops.append(f"-- TODO: Revert changes to column {col_name} in table {table_name}")
    
    # Generate the full script
    if format == 'python':
        # Join operations
        upgrade_operations = "\n".join(upgrade_ops)
        downgrade_operations = "\n".join(downgrade_ops)
        
        # Generate imports section
        imports = ["import sqlalchemy as sa"]
        
        # Generate the script content
        script_content = env.from_string(templates['header']).render(
            message=message,
            revision=revision,
            down_revision=down_revision,
            create_date=_format_date(),
            imports="\n".join(imports),
            branch_labels=branch_labels,
            depends_on=depends_on,
            upgrade_ops=upgrade_operations,
            downgrade_ops=downgrade_operations
        )
        
        # Generate filename
        script_filename = f"{revision}_{message.lower().replace(' ', '_')}.py"
    else:  # SQL
        # Join operations
        upgrade_operations = "\n".join(upgrade_ops)
        downgrade_operations = "\n".join(["-- Downgrade operations would be here"])
        
        # Generate the script content
        script_content = (
            env.from_string(templates['header']).render(
                message=message,
                revision=revision,
                down_revision=down_revision,
                create_date=_format_date()
            ) +
            upgrade_operations +
            env.from_string(templates['footer']).render()
        )
        
        # Generate filename
        script_filename = f"{revision}_{message.lower().replace(' ', '_')}.sql"
    
    # Write the script to a file
    script_path = output_dir / script_filename
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    logger.info(f"Generated migration script: {script_path}")
    return script_path


def generate_migration_plan(
    diff: SchemaDiff,
    format: str = 'markdown'
) -> str:
    """Generate a human-readable migration plan from a schema diff.
    
    Args:
        diff: SchemaDiff instance with detected differences
        format: Format of the migration plan ('markdown' or 'text')
        
    Returns:
        Migration plan as a string
    """
    if not diff.has_changes:
        return "No changes detected, no migration needed."
    
    # Markdown format
    if format == 'markdown':
        parts = ["# Database Migration Plan\n"]
        
        parts.append("## Summary\n")
        parts.append(diff.summary().replace("\n", "\n\n"))
        
        if diff.added_tables:
            parts.append("\n## Table Additions\n")
            for table in diff.added_tables:
                parts.append(f"- Create new table `{table}`")
        
        if diff.removed_tables:
            parts.append("\n## Table Removals\n")
            for table in diff.removed_tables:
                parts.append(f"- Remove table `{table}`")
        
        if diff.added_columns:
            parts.append("\n## Column Additions\n")
            for table, columns in diff.added_columns.items():
                parts.append(f"### Table: `{table}`\n")
                for column in columns:
                    parts.append(f"- Add column `{column}`")
        
        if diff.removed_columns:
            parts.append("\n## Column Removals\n")
            for table, columns in diff.removed_columns.items():
                parts.append(f"### Table: `{table}`\n")
                for column in columns:
                    parts.append(f"- Remove column `{column}`")
        
        if diff.modified_columns:
            parts.append("\n## Column Modifications\n")
            for table, columns in diff.modified_columns.items():
                parts.append(f"### Table: `{table}`\n")
                for column, changes in columns.items():
                    parts.append(f"- Modify column `{column}`:")
                    for change_type, details in changes.items():
                        if change_type == 'type_changed':
                            parts.append(f"  - Change type from `{changes.get('old_type')}` to `{changes.get('new_type')}`")
                        elif change_type == 'nullable_changed':
                            old_nullable = changes.get('old_nullable')
                            new_nullable = changes.get('new_nullable')
                            parts.append(f"  - Change nullable from `{old_nullable}` to `{new_nullable}`")
                        elif change_type == 'default_changed':
                            parts.append(f"  - Change default value")
        
        return "\n".join(parts)
    
    # Text format (or any other format)
    else:
        return diff.summary()


def compare_and_generate(
    source: Union[List[Any], Engine],
    target: Engine,
    output_dir: Union[str, Path],
    message: str,
    format: str = 'python',
    down_revision: Optional[str] = None,
    schema: str = 'public'
) -> Path:
    """Compare source to target and generate a migration script.
    
    This is a convenience function that combines diff detection and migration generation.
    
    Args:
        source: SQLAlchemy models or engine for the source database
        target: SQLAlchemy engine for the target database
        output_dir: Directory where the migration script will be saved
        message: Message describing the migration
        format: Format of the migration script ('python' or 'sql')
        down_revision: Previous revision ID (for alembic)
        schema: Database schema name
        
    Returns:
        Path to the generated migration script or None if no changes detected
    """
    # Detect differences
    if isinstance(source, Engine):
        # Compare two databases
        from uno.devtools.migrations.database.diff import diff_db_to_db
        diff = diff_db_to_db(source, target, schema=schema)
    else:
        # Compare models to database
        from uno.devtools.migrations.database.diff import diff_model_to_db
        diff = diff_model_to_db(source, target, schema=schema)
    
    # Generate migration script if there are changes
    if diff.has_changes:
        return generate_migration_script(
            diff, 
            output_dir, 
            message, 
            format=format,
            down_revision=down_revision,
            schema=schema
        )
    
    return None