"""
Integration tests for the database migration system.

These tests verify that the migration system can correctly apply and revert
migrations, handle dependencies between migrations, and manage migration state.
"""

import os
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, AsyncGenerator, Optional

import pytest
from uno.core.migrations import (
    Migrator, MigrationConfig, MigrationContext, Migration,
    SqlMigration, PythonMigration, MigrationDirection,
    migrate, create_migration, register_migration,
    DirectoryMigrationProvider, register_provider,
    DatabaseMigrationTracker, set_migration_tracker
)
from uno.database.session import async_session
from uno.database.engine import get_async_engine


@pytest.fixture(scope="function")
async def test_migrations_dir() -> AsyncGenerator[Path, None]:
    """Create a temporary directory for test migrations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        migrations_dir = Path(temp_dir) / "migrations"
        migrations_dir.mkdir(exist_ok=True)
        yield migrations_dir
        # Directory will be automatically cleaned up after the test


@pytest.fixture(scope="function")
async def migration_context() -> AsyncGenerator[MigrationContext, None]:
    """Create a database connection and migration context for testing."""
    # Use the async_session from the framework
    async with async_session() as connection:
        # Create test schema if it doesn't exist
        await connection.execute("CREATE SCHEMA IF NOT EXISTS test_migrations")
        
        # Configure migration system
        config = MigrationConfig(
            schema_name="test_migrations",
            migration_table="test_migrations_history",
            verbose=True,
            require_transactional=True,
        )
        
        # Create context
        context = MigrationContext(
            connection=connection,
            config=config
        )
        
        # Set up migration tracker
        tracker = DatabaseMigrationTracker(
            connection=connection,
            schema_name="test_migrations",
            table_name="test_migrations_history"
        )
        
        await tracker.initialize()
        set_migration_tracker(tracker)
        
        # Return context for tests
        yield context
        
        # Clean up
        await connection.execute("DROP SCHEMA IF EXISTS test_migrations CASCADE")


@pytest.fixture(scope="function")
async def clear_migration_registry():
    """Clear the global migration registry before and after each test."""
    # Store the original registry
    from uno.core.migrations.migrator import migration_registry
    original_registry = migration_registry.copy()
    
    # Clear registry for test
    migration_registry.clear()
    
    yield
    
    # Restore original registry
    migration_registry.clear()
    migration_registry.update(original_registry)


@pytest.mark.integration
class TestDatabaseMigrations:
    """Integration tests for database migrations."""
    
    @pytest.mark.asyncio
    async def test_sql_migration_apply_revert(
        self, migration_context: MigrationContext, clear_migration_registry
    ):
        """Test that SQL migrations can be applied and reverted correctly."""
        # Create a simple SQL migration
        migration = SqlMigration(
            id="20250101_000001",
            name="create_test_table",
            description="Create a test table for migration testing",
            up_sql="""
            CREATE TABLE test_migrations.test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX idx_test_table_name ON test_migrations.test_table(name);
            """,
            down_sql="""
            DROP TABLE IF EXISTS test_migrations.test_table;
            """
        )
        
        # Register migration
        register_migration(migration)
        
        # Apply migration
        migrator = Migrator(migration_context.config)
        await migrator.ensure_migration_table(migration_context)
        await migrator._apply_single_migration(migration_context, migration)
        
        # Verify table was created
        result = await migration_context.execute_sql(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'test_migrations' AND table_name = 'test_table')"
        )
        rows = await result.fetchall()
        assert rows[0][0] is True, "Test table was not created"
        
        # Verify migration was recorded
        applied_ids = await migrator.get_applied_migration_ids(migration_context)
        assert migration.id in applied_ids, "Migration was not recorded"
        
        # Revert migration
        await migrator._revert_single_migration(migration_context, migration)
        
        # Verify table was dropped
        result = await migration_context.execute_sql(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'test_migrations' AND table_name = 'test_table')"
        )
        rows = await result.fetchall()
        assert rows[0][0] is False, "Test table was not dropped"
        
        # Verify migration record was removed
        applied_ids = await migrator.get_applied_migration_ids(migration_context)
        assert migration.id not in applied_ids, "Migration record was not removed"
    
    @pytest.mark.asyncio
    async def test_python_migration_apply_revert(
        self, migration_context: MigrationContext, clear_migration_registry
    ):
        """Test that Python migrations can be applied and reverted correctly."""
        
        # Define up and down functions
        async def up_func(context: MigrationContext) -> None:
            await context.execute_sql("""
            CREATE TABLE test_migrations.py_test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Create an index
            CREATE INDEX idx_py_test_table_name ON test_migrations.py_test_table(name);
            """)
        
        async def down_func(context: MigrationContext) -> None:
            await context.execute_sql("DROP TABLE IF EXISTS test_migrations.py_test_table;")
        
        # Create a Python migration
        migration = PythonMigration(
            id="20250101_000002",
            name="create_py_test_table",
            description="Create a test table using Python migration",
            up_func=up_func,
            down_func=down_func
        )
        
        # Register migration
        register_migration(migration)
        
        # Apply migration
        migrator = Migrator(migration_context.config)
        await migrator.ensure_migration_table(migration_context)
        await migrator._apply_single_migration(migration_context, migration)
        
        # Verify table was created
        result = await migration_context.execute_sql(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'test_migrations' AND table_name = 'py_test_table')"
        )
        rows = await result.fetchall()
        assert rows[0][0] is True, "Python migration test table was not created"
        
        # Revert migration
        await migrator._revert_single_migration(migration_context, migration)
        
        # Verify table was dropped
        result = await migration_context.execute_sql(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'test_migrations' AND table_name = 'py_test_table')"
        )
        rows = await result.fetchall()
        assert rows[0][0] is False, "Python migration test table was not dropped"
    
    @pytest.mark.asyncio
    async def test_migration_dependencies(
        self, migration_context: MigrationContext, clear_migration_registry
    ):
        """Test that migrations with dependencies are applied in the correct order."""
        # Create base table migration
        base_migration = SqlMigration(
            id="20250101_000003",
            name="create_parent_table",
            description="Create a parent table",
            up_sql="""
            CREATE TABLE test_migrations.parent_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
            """,
            down_sql="DROP TABLE IF EXISTS test_migrations.parent_table;"
        )
        
        # Create dependent table migration
        dependent_migration = SqlMigration(
            id="20250101_000004",
            name="create_child_table",
            description="Create a child table with foreign key",
            dependencies=[base_migration.id],
            up_sql="""
            CREATE TABLE test_migrations.child_table (
                id SERIAL PRIMARY KEY,
                parent_id INTEGER NOT NULL REFERENCES test_migrations.parent_table(id),
                name VARCHAR(255) NOT NULL
            );
            """,
            down_sql="DROP TABLE IF EXISTS test_migrations.child_table;"
        )
        
        # Register migrations
        register_migration(base_migration)
        register_migration(dependent_migration)
        
        # Create migrator
        migrator = Migrator(migration_context.config)
        await migrator.ensure_migration_table(migration_context)
        
        # Apply migrations (only specifying the dependent migration)
        count, applied = await migrator.apply_migrations(
            migration_context, 
            migrations=[dependent_migration]
        )
        
        # Verify both migrations were applied
        assert count == 2, "Expected 2 migrations to be applied"
        assert len(applied) == 2, "Expected 2 migrations in the applied list"
        
        # Verify they were applied in the correct order
        assert applied[0].id == base_migration.id, "Base migration should be applied first"
        assert applied[1].id == dependent_migration.id, "Dependent migration should be applied second"
        
        # Verify both tables exist
        result = await migration_context.execute_sql(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'test_migrations' ORDER BY table_name"
        )
        rows = await result.fetchall()
        tables = [row[0] for row in rows if row[0] not in ('test_migrations_history')]
        assert 'parent_table' in tables, "Parent table was not created"
        assert 'child_table' in tables, "Child table was not created"
        
        # Revert migrations (should revert in reverse dependency order)
        count, reverted = await migrator.revert_migrations(
            migration_context,
            steps=2  # Revert both migrations
        )
        
        # Verify both migrations were reverted
        assert count == 2, "Expected 2 migrations to be reverted"
        assert len(reverted) == 2, "Expected 2 migrations in the reverted list"
        
        # Verify they were reverted in the correct order
        assert reverted[0].id == dependent_migration.id, "Dependent migration should be reverted first"
        assert reverted[1].id == base_migration.id, "Base migration should be reverted second"
        
        # Verify both tables were dropped
        result = await migration_context.execute_sql(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'test_migrations'"
        )
        rows = await result.fetchall()
        tables = [row[0] for row in rows if row[0] not in ('test_migrations_history')]
        assert 'parent_table' not in tables, "Parent table was not dropped"
        assert 'child_table' not in tables, "Child table was not dropped"
    
    @pytest.mark.asyncio
    async def test_file_migrations(
        self, migration_context: MigrationContext, test_migrations_dir: Path, clear_migration_registry
    ):
        """Test that migrations can be loaded from files."""
        # Create SQL migration file
        sql_file = test_migrations_dir / "001_create_products_table.sql"
        sql_file.write_text("""-- Create products table
CREATE TABLE test_migrations.products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- DOWN

DROP TABLE IF EXISTS test_migrations.products;
""")
        
        # Create Python migration file
        py_file = test_migrations_dir / "002_create_categories_table.py"
        py_file.write_text("""# Migration: Create categories table

from typing import Any

async def up(context: Any) -> None:
    \"\"\"Apply the migration.\"\"\"
    await context.execute_sql('''
        CREATE TABLE test_migrations.categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    ''')

async def down(context: Any) -> None:
    \"\"\"Revert the migration.\"\"\"
    await context.execute_sql('DROP TABLE IF EXISTS test_migrations.categories;')
""")
        
        # Register directory provider
        provider = DirectoryMigrationProvider([str(test_migrations_dir)])
        register_provider("test_provider", provider)
        
        # Discover migrations
        from uno.core.migrations.providers import discover_migrations
        discovered = await discover_migrations()
        
        # Verify migrations were discovered
        assert len(discovered) >= 2, "Expected at least 2 migrations to be discovered"
        
        # Apply migrations
        migrator = Migrator(migration_context.config)
        count, applied = await migrator.apply_migrations(migration_context)
        
        # Verify migrations were applied
        assert count >= 2, "Expected at least 2 migrations to be applied"
        
        # Verify tables were created
        result = await migration_context.execute_sql(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'test_migrations' ORDER BY table_name"
        )
        rows = await result.fetchall()
        tables = [row[0] for row in rows if row[0] not in ('test_migrations_history')]
        assert 'products' in tables, "Products table was not created"
        assert 'categories' in tables, "Categories table was not created"
        
        # Revert migrations
        count, reverted = await migrator.revert_migrations(
            migration_context,
            steps=2
        )
        
        # Verify migrations were reverted
        assert count >= 2, "Expected at least 2 migrations to be reverted"
        
        # Verify tables were dropped
        result = await migration_context.execute_sql(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'test_migrations'"
        )
        rows = await result.fetchall()
        tables = [row[0] for row in rows if row[0] not in ('test_migrations_history')]
        assert 'products' not in tables, "Products table was not dropped"
        assert 'categories' not in tables, "Categories table was not dropped"


if __name__ == "__main__":
    # For manual running of tests
    pytest.main(["-xvs", __file__])