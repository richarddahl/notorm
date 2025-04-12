"""
Example showing how to use the migration system.

This module demonstrates how to configure and use the migration system
to manage database schema changes.
"""

import os
import asyncio
import logging
from typing import Any

from uno.core.migrations.migrator import MigrationConfig, MigrationContext, migrate, MigrationDirection
from uno.core.migrations.migration import create_migration, SqlMigration, PythonMigration
from uno.core.migrations.providers import register_provider, DirectoryMigrationProvider
from uno.core.migrations.tracker import set_migration_tracker, DatabaseMigrationTracker


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("uno.migrations.example")


# Example migrations directory
MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


# Create example migrations
def create_example_migrations():
    """Create example migration files."""
    # Create migrations directory if it doesn't exist
    os.makedirs(MIGRATIONS_DIR, exist_ok=True)
    
    # Create initial migration
    migration1_path = os.path.join(MIGRATIONS_DIR, "001_create_users_table.sql")
    with open(migration1_path, "w") as f:
        f.write("""-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on username
CREATE INDEX idx_users_username ON users(username);

-- DOWN

DROP TABLE IF EXISTS users;
""")
    
    # Create second migration
    migration2_path = os.path.join(MIGRATIONS_DIR, "002_add_user_profile.sql")
    with open(migration2_path, "w") as f:
        f.write("""-- Add user profile table
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

-- DOWN

DROP TABLE IF EXISTS user_profiles;
""")
    
    # Create third migration (Python-based)
    migration3_path = os.path.join(MIGRATIONS_DIR, "003_add_user_settings.py")
    with open(migration3_path, "w") as f:
        f.write("""# Migration: Add user settings

from typing import Any


async def up(context: Any) -> None:
    \"\"\"Apply the migration.\"\"\"
    await context.execute_sql('''
        CREATE TABLE user_settings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            theme VARCHAR(50) DEFAULT 'light',
            notifications_enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);
    ''')


async def down(context: Any) -> None:
    \"\"\"Revert the migration.\"\"\"
    await context.execute_sql('DROP TABLE IF EXISTS user_settings;')
""")
    
    logger.info("Created example migrations")


async def get_database_connection():
    """Get a database connection."""
    # For this example, we'll use SQLite via aiosqlite
    # In a real application, you'd use PostgreSQL, MySQL, etc.
    import aiosqlite
    
    # Create an in-memory database
    conn = await aiosqlite.connect(":memory:")
    
    # Add execute_sql method to the connection to make it compatible with our migration system
    async def execute_sql(sql):
        cursor = await conn.cursor()
        await cursor.executescript(sql)
        await conn.commit()
        return cursor
    
    conn.execute_sql = execute_sql
    
    return conn


async def run_example():
    """Run the migration example."""
    # Create example migrations
    create_example_migrations()
    
    # Get database connection
    connection = await get_database_connection()
    
    try:
        # Create migration config
        config = MigrationConfig(
            schema_name="main",  # For SQLite, this is usually "main"
            migration_table="uno_migrations",
            migration_paths=[MIGRATIONS_DIR],
            verbose=True
        )
        
        # Create migration context
        context = MigrationContext(
            connection=connection,
            config=config
        )
        
        # Set up migration tracker
        tracker = DatabaseMigrationTracker(
            connection=connection,
            schema_name="main",
            table_name="uno_migrations"
        )
        
        await tracker.initialize()
        set_migration_tracker(tracker)
        
        # Register migration provider
        provider = DirectoryMigrationProvider([MIGRATIONS_DIR])
        register_provider("example", provider)
        
        # Apply migrations
        logger.info("Applying migrations...")
        count, applied = await migrate(
            connection=connection,
            config=config,
            direction=MigrationDirection.UP
        )
        
        logger.info(f"Applied {count} migrations")
        for migration in applied:
            logger.info(f"  - {migration.id}: {migration.name}")
        
        # Verify the migrations worked
        logger.info("\nVerifying migrations...")
        
        # Check if users table exists
        cursor = await connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        users_table = await cursor.fetchone()
        logger.info(f"Users table exists: {users_table is not None}")
        
        # Check if user_profiles table exists
        cursor = await connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
        profiles_table = await cursor.fetchone()
        logger.info(f"User profiles table exists: {profiles_table is not None}")
        
        # Check if user_settings table exists
        cursor = await connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        settings_table = await cursor.fetchone()
        logger.info(f"User settings table exists: {settings_table is not None}")
        
        # Rollback one migration
        logger.info("\nRolling back one migration...")
        count, reverted = await migrate(
            connection=connection,
            config=config,
            direction=MigrationDirection.DOWN,
            steps=1
        )
        
        logger.info(f"Reverted {count} migrations")
        for migration in reverted:
            logger.info(f"  - {migration.id}: {migration.name}")
        
        # Verify the rollback worked
        logger.info("\nVerifying rollback...")
        
        # Check if user_settings table was dropped
        cursor = await connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        settings_table = await cursor.fetchone()
        logger.info(f"User settings table exists: {settings_table is not None}")
        
        # Show current migration state
        applied_migrations = await tracker.get_applied_migrations()
        logger.info(f"\nCurrent applied migrations: {len(applied_migrations)}")
        for migration_id in applied_migrations:
            logger.info(f"  - {migration_id}")
    
    finally:
        # Close the database connection
        await connection.close()


def main():
    """Run the migration example."""
    asyncio.run(run_example())


if __name__ == "__main__":
    main()