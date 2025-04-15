# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Test service utilities for integration testing.

This module provides service classes for integration testing that encapsulate
common operations for testing databases, APIs, and other Uno components.
"""

import asyncio
import json
import os
import tempfile
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Type, TypeVar, Union, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.db_manager import DBManager
from uno.database.engine import AsyncEngine


T = TypeVar("T")


class DatabaseTestService:
    """
    Service for database-related test operations.
    
    This class provides utilities for setting up test data, running
    database migrations, and other database-related test operations.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the database test service.
        
        Args:
            session: The database session to use
        """
        self.session = session
    
    async def execute_sql(self, sql: str, **params) -> Any:
        """
        Execute raw SQL against the database.
        
        Args:
            sql: The SQL statement to execute
            **params: Parameters to bind to the SQL statement
            
        Returns:
            The result of the SQL execution
        """
        result = await self.session.execute(text(sql), params)
        return result
    
    async def insert_test_data(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert test data into a table.
        
        Args:
            table: The name of the table to insert into
            data: A dictionary of column names and values
            
        Returns:
            The ID of the inserted row
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f":{k}" for k in data.keys()])
        
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        result = await self.execute_sql(sql, **data)
        
        return result.scalar_one()
    
    async def bulk_insert(self, table: str, data_list: List[Dict[str, Any]]) -> List[int]:
        """
        Insert multiple rows of test data.
        
        Args:
            table: The name of the table to insert into
            data_list: A list of dictionaries with column names and values
            
        Returns:
            The IDs of the inserted rows
        """
        if not data_list:
            return []
        
        # Get column names from the first item
        columns = data_list[0].keys()
        
        # Create individual insert statements with RETURNING
        ids = []
        for data in data_list:
            id = await self.insert_test_data(table, data)
            ids.append(id)
        
        return ids
    
    async def clear_table(self, table: str) -> None:
        """
        Clear all data from a table.
        
        Args:
            table: The name of the table to clear
        """
        await self.execute_sql(f"DELETE FROM {table}")
    
    async def get_by_id(self, table: str, id: int) -> Optional[Dict[str, Any]]:
        """
        Get a row by ID.
        
        Args:
            table: The name of the table to query
            id: The ID to look up
            
        Returns:
            The row as a dictionary, or None if not found
        """
        result = await self.execute_sql(f"SELECT * FROM {table} WHERE id = :id", id=id)
        row = result.mappings().first()
        
        if row:
            return dict(row)
        return None
    
    async def count_rows(self, table: str, where_clause: Optional[str] = None, **params) -> int:
        """
        Count rows in a table.
        
        Args:
            table: The name of the table to count
            where_clause: Optional WHERE clause
            **params: Parameters for the WHERE clause
            
        Returns:
            The number of rows
        """
        sql = f"SELECT COUNT(*) FROM {table}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        result = await self.execute_sql(sql, **params)
        return result.scalar_one()
    
    async def verify_db_structure(self, expected_tables: List[str]) -> bool:
        """
        Verify that the database has the expected structure.
        
        Args:
            expected_tables: List of table names that should exist
            
        Returns:
            True if all expected tables exist, False otherwise
        """
        # Get a list of tables in the current schema
        result = await self.execute_sql(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = current_schema()"
        )
        existing_tables = [row[0] for row in result.fetchall()]
        
        # Check that all expected tables exist
        return all(table in existing_tables for table in expected_tables)
    
    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """
        Create a savepoint for a test transaction.
        
        This allows tests to perform changes and then roll them back.
        
        Example:
            ```python
            async def test_something(db_service):
                with db_service.transaction():
                    # Make changes
                    await db_service.insert_test_data(...)
                    # Changes will be rolled back at the end of the with block
            ```
        """
        savepoint = f"test_savepoint_{os.urandom(8).hex()}"
        
        try:
            self.session.begin_nested()
            yield
        finally:
            self.session.rollback()


class ApiTestService:
    """
    Service for API-related test operations.
    
    This class provides utilities for testing API endpoints, including
    methods for making requests with authentication and parsing responses.
    """
    
    def __init__(self, client: TestClient, auth_headers: Optional[Dict[str, str]] = None):
        """
        Initialize the API test service.
        
        Args:
            client: The FastAPI test client
            auth_headers: Optional authentication headers to include in requests
        """
        self.client = client
        self.auth_headers = auth_headers or {}
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, auth: bool = True) -> Any:
        """
        Make a GET request to the API.
        
        Args:
            url: The URL to request
            params: Optional query parameters
            auth: Whether to include authentication headers
            
        Returns:
            The parsed response JSON
        """
        headers = self.auth_headers if auth else {}
        response = self.client.get(url, params=params, headers=headers)
        
        # Check for errors
        response.raise_for_status()
        
        # Parse and return the response
        return response.json()
    
    def post(self, url: str, data: Dict[str, Any], auth: bool = True) -> Any:
        """
        Make a POST request to the API.
        
        Args:
            url: The URL to request
            data: The request body
            auth: Whether to include authentication headers
            
        Returns:
            The parsed response JSON
        """
        headers = self.auth_headers if auth else {}
        response = self.client.post(url, json=data, headers=headers)
        
        # Check for errors
        response.raise_for_status()
        
        # Parse and return the response
        return response.json()
    
    def put(self, url: str, data: Dict[str, Any], auth: bool = True) -> Any:
        """
        Make a PUT request to the API.
        
        Args:
            url: The URL to request
            data: The request body
            auth: Whether to include authentication headers
            
        Returns:
            The parsed response JSON
        """
        headers = self.auth_headers if auth else {}
        response = self.client.put(url, json=data, headers=headers)
        
        # Check for errors
        response.raise_for_status()
        
        # Parse and return the response
        return response.json()
    
    def delete(self, url: str, auth: bool = True) -> Any:
        """
        Make a DELETE request to the API.
        
        Args:
            url: The URL to request
            auth: Whether to include authentication headers
            
        Returns:
            The parsed response JSON
        """
        headers = self.auth_headers if auth else {}
        response = self.client.delete(url, headers=headers)
        
        # Check for errors
        response.raise_for_status()
        
        # Parse and return the response
        return response.json()
    
    def upload_file(self, url: str, file_path: Union[str, Path], file_key: str = "file", data: Optional[Dict[str, Any]] = None, auth: bool = True) -> Any:
        """
        Upload a file to the API.
        
        Args:
            url: The URL to request
            file_path: Path to the file to upload
            file_key: The form field name for the file
            data: Additional form data
            auth: Whether to include authentication headers
            
        Returns:
            The parsed response JSON
        """
        headers = self.auth_headers.copy() if auth else {}
        
        # Remove Content-Type header as it will be set automatically for multipart/form-data
        headers.pop("Content-Type", None)
        
        with open(file_path, "rb") as f:
            files = {file_key: f}
            response = self.client.post(url, files=files, data=data or {}, headers=headers)
        
        # Check for errors
        response.raise_for_status()
        
        # Parse and return the response
        return response.json()
    
    def assert_status(self, response: Any, status_code: int) -> None:
        """
        Assert that a response has the expected status code.
        
        Args:
            response: The response to check
            status_code: The expected status code
        """
        assert response.status_code == status_code, f"Expected status code {status_code}, got {response.status_code}"
    
    def assert_json_structure(self, data: Dict[str, Any], expected_keys: List[str]) -> None:
        """
        Assert that a JSON response has the expected structure.
        
        Args:
            data: The JSON data to check
            expected_keys: List of keys that should be present in the JSON
        """
        for key in expected_keys:
            assert key in data, f"Expected key '{key}' not found in response"


class TestEnvironment:
    """
    Container for test environment components.
    
    This class provides a unified interface for accessing all test environment
    components, including the database session, API client, and other services.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        client: Optional[TestClient] = None,
        auth_headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the test environment.
        
        Args:
            session: The database session
            client: Optional FastAPI test client
            auth_headers: Optional authentication headers
        """
        self.session = session
        self.client = client
        self.auth_headers = auth_headers or {}
        self.db = DatabaseTestService(session)
        self.api = ApiTestService(client, auth_headers) if client else None
        self._repositories: Dict[Type, Any] = {}
        self._services: Dict[Any, Any] = {}
    
    def get_repository(self, repo_type: Type[T]) -> T:
        """
        Get or create a repository of the specified type.
        
        Args:
            repo_type: The repository class
            
        Returns:
            An instance of the repository
        """
        if repo_type not in self._repositories:
            # Create the repository with the session
            repo = repo_type(self.session)
            self._repositories[repo_type] = repo
        
        return cast(T, self._repositories[repo_type])
    
    def get_service(self, service_type: Type[T], **kwargs) -> T:
        """
        Get or create a service of the specified type.
        
        Args:
            service_type: The service class
            **kwargs: Additional constructor arguments
            
        Returns:
            An instance of the service
        """
        if service_type not in self._services:
            # Get dependencies from the service_type's constructor
            import inspect
            
            sig = inspect.signature(service_type.__init__)
            params = {}
            
            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                
                if name in kwargs:
                    params[name] = kwargs[name]
                elif param.annotation is AsyncSession:
                    params[name] = self.session
                elif param.default is not inspect.Parameter.empty:
                    params[name] = param.default
            
            # Create the service with dependencies
            service = service_type(**params)
            self._services[service_type] = service
        
        return cast(T, self._services[service_type])
    
    async def setup_test_data(self, data_file: Union[str, Path]) -> None:
        """
        Set up test data from a JSON file.
        
        Args:
            data_file: Path to a JSON file with test data
        """
        with open(data_file, "r") as f:
            data = json.load(f)
        
        # Process data in the order specified by the file
        for table_name, rows in data.items():
            for row in rows:
                await self.db.insert_test_data(table_name, row)
    
    async def teardown(self) -> None:
        """Clean up the test environment."""
        # Roll back any pending transactions
        await self.session.rollback()
        
        # Close repositories and services
        for repo in self._repositories.values():
            if hasattr(repo, "close"):
                await repo.close()
        
        for service in self._services.values():
            if hasattr(service, "close"):
                await service.close()