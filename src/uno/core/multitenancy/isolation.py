"""
Tenant isolation strategies.

This module provides mechanisms for tenant data isolation using 
PostgreSQL Row Level Security (RLS) policies.
"""

from typing import List, Dict, Optional, Any, Set, Tuple
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, Table, MetaData

from uno.core.multitenancy.models import Tenant, TenantAwareModel


class RLSIsolationStrategy:
    """
    Implements tenant isolation using PostgreSQL Row Level Security (RLS).
    
    This strategy applies RLS policies to tenant-aware tables, ensuring
    that queries only return rows belonging to the current tenant.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        schema: str = "public",
        tenant_column: str = "tenant_id",
        excluded_tables: Optional[Set[str]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the RLS isolation strategy.
        
        Args:
            session: SQLAlchemy async session
            schema: Database schema name
            tenant_column: Name of the tenant ID column
            excluded_tables: Set of table names to exclude from RLS
            logger: Optional logger instance
        """
        self.session = session
        self.schema = schema
        self.tenant_column = tenant_column
        self.excluded_tables = excluded_tables or set()
        self.logger = logger or logging.getLogger(__name__)
    
    async def enable_rls_for_table(self, table_name: str) -> bool:
        """
        Enable RLS for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if RLS was enabled, False otherwise
        """
        if table_name in self.excluded_tables:
            self.logger.info(f"Skipping RLS for excluded table: {table_name}")
            return False
        
        try:
            # Enable RLS on the table
            await self.session.execute(
                text(f'ALTER TABLE {self.schema}."{table_name}" ENABLE ROW LEVEL SECURITY')
            )
            
            # Create policy for SELECT operations
            await self.session.execute(text(
                f'CREATE POLICY select_tenant_rows ON {self.schema}."{table_name}" '
                f'FOR SELECT USING ({self.tenant_column} = current_setting(\'app.current_tenant_id\')::text)'
            ))
            
            # Create policy for INSERT operations
            await self.session.execute(text(
                f'CREATE POLICY insert_tenant_rows ON {self.schema}."{table_name}" '
                f'FOR INSERT WITH CHECK ({self.tenant_column} = current_setting(\'app.current_tenant_id\')::text)'
            ))
            
            # Create policy for UPDATE operations
            await self.session.execute(text(
                f'CREATE POLICY update_tenant_rows ON {self.schema}."{table_name}" '
                f'FOR UPDATE USING ({self.tenant_column} = current_setting(\'app.current_tenant_id\')::text) '
                f'WITH CHECK ({self.tenant_column} = current_setting(\'app.current_tenant_id\')::text)'
            ))
            
            # Create policy for DELETE operations
            await self.session.execute(text(
                f'CREATE POLICY delete_tenant_rows ON {self.schema}."{table_name}" '
                f'FOR DELETE USING ({self.tenant_column} = current_setting(\'app.current_tenant_id\')::text)'
            ))
            
            # Commit the changes
            await self.session.commit()
            
            self.logger.info(f"Enabled RLS for table: {table_name}")
            return True
        
        except Exception as e:
            # Rollback the transaction
            await self.session.rollback()
            
            self.logger.error(f"Error enabling RLS for table {table_name}: {str(e)}")
            return False
    
    async def disable_rls_for_table(self, table_name: str) -> bool:
        """
        Disable RLS for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if RLS was disabled, False otherwise
        """
        try:
            # Disable RLS on the table
            await self.session.execute(
                text(f'ALTER TABLE {self.schema}."{table_name}" DISABLE ROW LEVEL SECURITY')
            )
            
            # Drop existing policies
            await self.session.execute(text(
                f'DROP POLICY IF EXISTS select_tenant_rows ON {self.schema}."{table_name}"'
            ))
            await self.session.execute(text(
                f'DROP POLICY IF EXISTS insert_tenant_rows ON {self.schema}."{table_name}"'
            ))
            await self.session.execute(text(
                f'DROP POLICY IF EXISTS update_tenant_rows ON {self.schema}."{table_name}"'
            ))
            await self.session.execute(text(
                f'DROP POLICY IF EXISTS delete_tenant_rows ON {self.schema}."{table_name}"'
            ))
            
            # Commit the changes
            await self.session.commit()
            
            self.logger.info(f"Disabled RLS for table: {table_name}")
            return True
        
        except Exception as e:
            # Rollback the transaction
            await self.session.rollback()
            
            self.logger.error(f"Error disabling RLS for table {table_name}: {str(e)}")
            return False
    
    async def enable_rls_for_all_tenant_tables(self) -> Dict[str, bool]:
        """
        Enable RLS for all tenant-aware tables.
        
        Returns:
            Dictionary mapping table names to success status
        """
        tenant_tables = await self._get_tenant_aware_tables()
        
        results = {}
        for table_name in tenant_tables:
            success = await self.enable_rls_for_table(table_name)
            results[table_name] = success
        
        return results
    
    async def disable_rls_for_all_tenant_tables(self) -> Dict[str, bool]:
        """
        Disable RLS for all tenant-aware tables.
        
        Returns:
            Dictionary mapping table names to success status
        """
        tenant_tables = await self._get_tenant_aware_tables()
        
        results = {}
        for table_name in tenant_tables:
            success = await self.disable_rls_for_table(table_name)
            results[table_name] = success
        
        return results
    
    async def _get_tenant_aware_tables(self) -> List[str]:
        """
        Get all tenant-aware tables in the database.
        
        This method queries the database schema to find tables that have
        a tenant_id column, indicating they are tenant-aware.
        
        Returns:
            List of tenant-aware table names
        """
        # Query to find tables with tenant_id column
        query = text(f"""
            SELECT table_name 
            FROM information_schema.columns 
            WHERE table_schema = :schema 
              AND column_name = :tenant_column
              AND table_name NOT IN :excluded
        """)
        
        result = await self.session.execute(
            query, 
            {
                "schema": self.schema, 
                "tenant_column": self.tenant_column,
                "excluded": tuple(self.excluded_tables) or ('',)
            }
        )
        
        tables = [row[0] for row in result.all()]
        return tables
    
    async def create_tenant_context_functions(self) -> bool:
        """
        Create database functions for tenant context management.
        
        Returns:
            True if the functions were created successfully, False otherwise
        """
        try:
            # Function to get the current tenant ID
            await self.session.execute(text("""
                CREATE OR REPLACE FUNCTION get_current_tenant_id()
                RETURNS TEXT AS $$
                BEGIN
                    RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '');
                END;
                $$ LANGUAGE plpgsql;
            """))
            
            # Function to set the current tenant ID
            await self.session.execute(text("""
                CREATE OR REPLACE FUNCTION set_current_tenant_id(tenant_id TEXT)
                RETURNS VOID AS $$
                BEGIN
                    PERFORM set_config('app.current_tenant_id', tenant_id, FALSE);
                END;
                $$ LANGUAGE plpgsql;
            """))
            
            # Function to clear the current tenant ID
            await self.session.execute(text("""
                CREATE OR REPLACE FUNCTION clear_current_tenant_id()
                RETURNS VOID AS $$
                BEGIN
                    PERFORM set_config('app.current_tenant_id', '', FALSE);
                END;
                $$ LANGUAGE plpgsql;
            """))
            
            # Function for database superusers to bypass RLS
            await self.session.execute(text("""
                CREATE OR REPLACE FUNCTION bypass_rls()
                RETURNS VOID AS $$
                BEGIN
                    -- Only superusers can execute this function
                    IF NOT (SELECT usesuper FROM pg_user WHERE usename = current_user) THEN
                        RAISE EXCEPTION 'Only superusers can bypass RLS';
                    END IF;
                    
                    -- Temporary table for the session
                    CREATE TEMP TABLE IF NOT EXISTS _rls_bypass (bypass BOOLEAN);
                    TRUNCATE TABLE _rls_bypass;
                    INSERT INTO _rls_bypass VALUES (TRUE);
                END;
                $$ LANGUAGE plpgsql;
            """))
            
            # Commit the changes
            await self.session.commit()
            
            self.logger.info("Created tenant context functions")
            return True
        
        except Exception as e:
            # Rollback the transaction
            await self.session.rollback()
            
            self.logger.error(f"Error creating tenant context functions: {str(e)}")
            return False
    
    async def ensure_tenant_migrations(self) -> bool:
        """
        Ensure that the database has all the necessary structures for tenant isolation.
        
        Returns:
            True if the migrations were successful, False otherwise
        """
        try:
            # Create app.current_tenant_id setting if it doesn't exist
            await self.session.execute(text("""
                DO $$
                BEGIN
                    -- Create the app.current_tenant_id setting if it doesn't exist
                    BEGIN
                        PERFORM current_setting('app.current_tenant_id');
                    EXCEPTION WHEN OTHERS THEN
                        PERFORM set_config('app.current_tenant_id', '', FALSE);
                    END;
                END;
                $$;
            """))
            
            # Create context functions
            await self.create_tenant_context_functions()
            
            # Ensure all tenant-aware tables have RLS enabled
            await self.enable_rls_for_all_tenant_tables()
            
            # Commit the changes
            await self.session.commit()
            
            self.logger.info("Tenant migrations completed successfully")
            return True
        
        except Exception as e:
            # Rollback the transaction
            await self.session.rollback()
            
            self.logger.error(f"Error ensuring tenant migrations: {str(e)}")
            return False


class SuperuserBypassMixin:
    """
    Mixin that allows superusers to bypass tenant isolation.
    
    This mixin provides a context manager that temporarily bypasses
    tenant isolation for superusers, allowing them to access data
    from all tenants.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the mixin.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def __aenter__(self):
        """
        Temporarily bypass tenant isolation.
        """
        try:
            # Call the bypass_rls() function to bypass RLS
            await self.session.execute(text("SELECT bypass_rls()"))
            return self
        except Exception:
            # If this fails, the user is probably not a superuser
            # Just continue without bypassing RLS
            pass
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Restore tenant isolation.
        """
        try:
            # Drop the temporary table to restore RLS
            await self.session.execute(text("DROP TABLE IF EXISTS _rls_bypass"))
        except Exception:
            # If this fails, just continue
            pass


class AdminTenantMixin:
    """
    Mixin that allows administrators to access data from any tenant.
    
    This mixin provides methods for temporarily switching between tenants
    for administrative purposes.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the mixin.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self._original_tenant_id = None
    
    async def switch_tenant(self, tenant_id: str):
        """
        Switch to a different tenant context.
        
        Args:
            tenant_id: ID of the tenant to switch to
        """
        # Save the original tenant ID
        result = await self.session.execute(
            text("SELECT current_setting('app.current_tenant_id', TRUE)")
        )
        self._original_tenant_id = result.scalar()
        
        # Switch to the new tenant
        await self.session.execute(
            text("SELECT set_current_tenant_id(:tenant_id)"),
            {"tenant_id": tenant_id}
        )
    
    async def restore_tenant(self):
        """
        Restore the original tenant context.
        """
        if self._original_tenant_id is not None:
            await self.session.execute(
                text("SELECT set_current_tenant_id(:tenant_id)"),
                {"tenant_id": self._original_tenant_id or ""}
            )
            self._original_tenant_id = None