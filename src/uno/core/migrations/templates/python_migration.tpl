# Migration: ${name}
# Created at: ${created_at}
# Description: ${description}

from typing import Any
from uno.core.migrations.migration import Migration, MigrationBase, create_migration

# === Function-based migration approach ===
# This is the simpler approach, good for most migrations

async def up(context: Any) -> None:
    """
    Apply the migration.
    
    This function will be called when the migration is being applied.
    
    Args:
        context: Migration context with database connection
    """
    # Execute SQL or perform other migration steps
    # Example: await context.execute_sql('''
    #     CREATE TABLE example (
    #         id SERIAL PRIMARY KEY,
    #         name VARCHAR(255) NOT NULL
    #     )
    # ''')
    pass


async def down(context: Any) -> None:
    """
    Revert the migration.
    
    This function will be called when the migration is being reverted.
    
    Args:
        context: Migration context with database connection
    """
    # Execute SQL or perform other migration steps
    # Example: await context.execute_sql('DROP TABLE example')
    pass


# === Class-based migration approach ===
# Uncomment and modify this code if you prefer a class-based approach
# This is more suitable for complex migrations with dependencies

# class ${class_name}(Migration):
#     """${name} migration class."""
#     
#     def __init__(self):
#         """Initialize the migration."""
#         base = create_migration(
#             name="${name}",
#             description="${description}",
#             # Add dependencies if needed:
#             # dependencies=["20240101_previous_migration"]
#         )
#         super().__init__(base)
#     
#     async def apply(self, context: Any) -> None:
#         """
#         Apply the migration.
#         
#         Args:
#             context: Migration context with database connection
#         """
#         # Execute SQL or perform other migration steps
#         # Example:
#         # await context.execute_sql('''
#         #     CREATE TABLE example (
#         #         id SERIAL PRIMARY KEY,
#         #         name VARCHAR(255) NOT NULL
#         #     )
#         # ''')
#         pass
#     
#     async def revert(self, context: Any) -> None:
#         """
#         Revert the migration.
#         
#         Args:
#             context: Migration context with database connection
#         """
#         # Execute SQL or perform other migration steps
#         # Example:
#         # await context.execute_sql('DROP TABLE example')
#         pass
#     
#     def get_checksum(self) -> str:
#         """
#         Calculate a checksum for the migration content.
#         
#         Returns:
#             Checksum string
#         """
#         import hashlib
#         # Create a predictable string to hash
#         content = f"{self.id}:{self.name}:{self.description}"
#         return hashlib.md5(content.encode('utf-8')).hexdigest()