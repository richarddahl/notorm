# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
This module contains the global fixtures for the tests in all test modules.
Each test module has its own conftest.py file that containts the fixtures for that module.
"""
import asyncio
import logging

import pytest
import pytest_asyncio
import importlib

from psycopg import sql

from sqlalchemy import func, Column

from uno.database.manager import DBManager
from uno.settings import uno_settings

from uno.database.engine import sync_connection
# Import async_session from session to avoid circular imports
from uno.database.session import async_session
from uno.settings import uno_settings
from uno.database.engine import SyncEngineFactory
from uno.database.manager import DBManager
from uno.sql.emitters.database import (
    DropDatabaseAndRoles,
    CreateRolesAndDatabase,
    CreateSchemasAndExtensions,
    RevokeAndGrantPrivilegesAndSetSearchPaths,
    CreatePGULID,
    CreateTokenSecret,
    GrantPrivileges,
    SetRole,
)
from uno.sql.emitters.table import InsertMetaRecordFunction
from uno.meta.sqlconfigs import MetaTypeSQLConfig


def db_column(
    db_inspector, table_name: str, col_name: str, schema: str = uno_settings.DB_SCHEMA
) -> Column | None:
    for col in db_inspector.get_columns(table_name, schema=schema):
        if col.get("name") == col_name:
            return col
    return None


@pytest.fixture(scope="module")
def test_db():
    # Initialize a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Initialize the engine factory with the logger
    engine_factory = SyncEngineFactory(logger=logger)

    # Define all needed SQL emitters
    sql_emitters = {
        "drop_database_and_roles": DropDatabaseAndRoles,
        "create_roles_and_database": CreateRolesAndDatabase,
        "create_schemas_and_extensions": CreateSchemasAndExtensions,
        "revoke_and_grant_privileges": RevokeAndGrantPrivilegesAndSetSearchPaths,
        "set_role": SetRole,
        "create_token_secret": CreateTokenSecret,
        "create_pgulid": CreatePGULID,
        "grant_privileges": GrantPrivileges,
        "insert_meta_record": InsertMetaRecordFunction,
        "meta_type": MetaTypeSQLConfig,
    }

    # Instantiate DBManager with all required parameters
    db_manager = DBManager(
        config=uno_settings,
        logger=logger,
        engine_factory=engine_factory,
        sql_emitters=sql_emitters,
    )

    db_manager.drop_db()
    db_manager.create_db()
    return True


@pytest.fixture(scope="function")
def connection():
    """
    Fixture that provides a database connection for tests.
    """
    with sync_connection() as conn:
        yield conn


@pytest_asyncio.fixture(scope="function")
async def session(test_db):
    """
    Fixture that provides an async database session for tests.
    This is an async context manager that yields a SQLAlchemy AsyncSession.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()