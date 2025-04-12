# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
This module contains the global fixtures for the tests in all test modules.
Each test module has its own conftest.py file that containts the fixtures for that module.
"""
import asyncio
import logging
import re
import inspect

import pytest
import pytest_asyncio
import importlib

from psycopg import sql

from sqlalchemy import func, Column


# Helper for matching dictionaries with partial information
class PartialDictMatcher:
    """Matcher for dictionaries that contain at least the expected keys/values."""
    
    def __init__(self, expected):
        self.expected = expected
    
    def __eq__(self, actual):
        if not isinstance(actual, dict):
            return False
        
        for key, value in self.expected.items():
            if key not in actual:
                return False
            
            if isinstance(value, PartialDictMatcher):
                if not value == actual[key]:
                    return False
            elif callable(value):
                if not value(actual[key]):
                    return False
            elif actual[key] != value:
                return False
        
        return True
    
    def __repr__(self):
        return f"PartialDictMatcher({self.expected})"


# Helper for matching any string
class AnyStringMatcher:
    """Matcher for any string."""
    
    def __eq__(self, actual):
        return isinstance(actual, str)
    
    def __repr__(self):
        return "AnyString()"


# Helper for matching any number
class AnyNumberMatcher:
    """Matcher for any number."""
    
    def __eq__(self, actual):
        return isinstance(actual, (int, float))
    
    def __repr__(self):
        return "AnyNumber()"


# Helper for matching any float
class AnyFloatMatcher:
    """Matcher for any float."""
    
    def __eq__(self, actual):
        return isinstance(actual, float)
    
    def __repr__(self):
        return "AnyFloat()"


# Helper for matching any integer
class AnyIntMatcher:
    """Matcher for any integer."""
    
    def __eq__(self, actual):
        return isinstance(actual, int)
    
    def __repr__(self):
        return "AnyInt()"


# Helper for matching instance of a class
class InstanceOfMatcher:
    """Matcher for instances of a class."""
    
    def __init__(self, cls):
        self.cls = cls
    
    def __eq__(self, actual):
        return isinstance(actual, self.cls)
    
    def __repr__(self):
        return f"InstanceOf({self.cls.__name__})"


# Add the helpers to the pytest namespace
pytest.helpers = type(
    "Helpers",
    (),
    {
        "match_partial_dict": lambda expected: PartialDictMatcher(expected),
        "any_string": AnyStringMatcher(),
        "any_number": AnyNumberMatcher(),
        "any_float": AnyFloatMatcher(),
        "any_int": AnyIntMatcher(),
        "instance_of": lambda cls: InstanceOfMatcher(cls),
        "any_instance_of_object": InstanceOfMatcher(object),
    },
)

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