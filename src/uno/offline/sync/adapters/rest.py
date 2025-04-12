"""REST network adapter for synchronization.

This module provides a network adapter for communicating with REST APIs
during synchronization.
"""
import logging
import json
import time
from datetime import datetime
import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator, Union

import httpx

from ..adapter import NetworkAdapter, BatchSupportMixin
from ..errors import NetworkError, ConflictError, AdapterError

logger = logging.getLogger(__name__)


class RestAdapter(NetworkAdapter, BatchSupportMixin):
    """Network adapter for communicating with REST APIs."""
    
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
        retry_count: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize the REST adapter.
        
        Args:
            base_url: The base URL of the REST API
            headers: Optional headers to include in requests
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
            retry_count: Number of times to retry failed requests
            retry_delay: Delay between retries in seconds
        """
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        
        if auth_token:
            self.set_auth_token(auth_token)
        
        self._server_timestamp = None
    
    def set_auth_token(self, token: str) -> None:
        """Set the authentication token for this adapter.
        
        Args:
            token: The authentication token
        """
        self.headers["Authorization"] = f"Bearer {token}"
    
    async def fetch_changes(
        self,
        collection: str,
        query_params: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch changes from the server.
        
        Args:
            collection: The collection to fetch changes for
            query_params: Optional parameters to include in the request
            
        Yields:
            Each change from the server
            
        Raises:
            NetworkError: If the request fails
        """
        await self._check_online()
        
        url = f"{self.base_url}/{collection}"
        params = query_params or {}
        
        try:
            response = await self._make_request("GET", url, params=params)
            
            # Store the server timestamp for synchronization
            if "X-Server-Timestamp" in response.headers:
                self._server_timestamp = response.headers["X-Server-Timestamp"]
            
            data = response.json()
            
            if isinstance(data, list):
                # If the response is a list, yield each item
                for item in data:
                    yield item
            elif isinstance(data, dict) and "items" in data:
                # If the response is a dict with an "items" field, yield each item
                for item in data["items"]:
                    yield item
            else:
                # Otherwise, yield the whole response
                yield data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # No changes found, so we're done
                return
            raise NetworkError(f"Failed to fetch changes: {str(e)}")
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {str(e)}")
    
    async def send_change(self, collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a change to the server.
        
        Args:
            collection: The collection to send the change to
            data: The data to send
            
        Returns:
            The server's response
            
        Raises:
            NetworkError: If the request fails
            ConflictError: If there's a conflict with the server's data
        """
        await self._check_online()
        
        url = f"{self.base_url}/{collection}/{data.get('id', '')}"
        
        try:
            # Check if the record exists first
            try:
                await self._make_request("GET", url)
                # Record exists, so update it
                response = await self._make_request("PUT", url, json=data)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Record doesn't exist, so create it
                    create_url = f"{self.base_url}/{collection}"
                    response = await self._make_request("POST", create_url, json=data)
                else:
                    raise
            
            # Store the server timestamp for synchronization
            if "X-Server-Timestamp" in response.headers:
                self._server_timestamp = response.headers["X-Server-Timestamp"]
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                # Conflict, so raise a ConflictError
                try:
                    server_data = e.response.json()
                except ValueError:
                    server_data = {"error": str(e)}
                
                raise ConflictError(
                    "Conflict with server data",
                    data,
                    server_data
                )
            raise NetworkError(f"Failed to send change: {str(e)}")
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {str(e)}")
    
    async def send_batch(
        self,
        collection: str,
        batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Send a batch of changes to the server.
        
        Args:
            collection: The collection to send the changes to
            batch: The list of changes to send
            
        Returns:
            The server's responses
            
        Raises:
            NetworkError: If the request fails
        """
        await self._check_online()
        
        url = f"{self.base_url}/{collection}/batch"
        
        try:
            response = await self._make_request("POST", url, json={"items": batch})
            
            # Store the server timestamp for synchronization
            if "X-Server-Timestamp" in response.headers:
                self._server_timestamp = response.headers["X-Server-Timestamp"]
            
            result = response.json()
            
            if isinstance(result, dict) and "items" in result:
                return result["items"]
            elif isinstance(result, list):
                return result
            else:
                raise AdapterError("Invalid batch response format", "rest")
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                # Partial success with conflicts
                try:
                    result = e.response.json()
                    if "results" in result:
                        return result["results"]
                    else:
                        raise NetworkError(f"Failed to send batch: {str(e)}")
                except ValueError:
                    raise NetworkError(f"Failed to send batch: {str(e)}")
            raise NetworkError(f"Failed to send batch: {str(e)}")
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {str(e)}")
    
    async def fetch_batch(
        self,
        collection: str,
        ids: List[str],
        query_params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch a batch of records from the server.
        
        Args:
            collection: The collection to fetch records from
            ids: The IDs of the records to fetch
            query_params: Optional additional query parameters
            
        Returns:
            The fetched records
            
        Raises:
            NetworkError: If the request fails
        """
        await self._check_online()
        
        url = f"{self.base_url}/{collection}/batch"
        params = query_params or {}
        params["ids"] = ",".join(ids)
        
        try:
            response = await self._make_request("GET", url, params=params)
            
            # Store the server timestamp for synchronization
            if "X-Server-Timestamp" in response.headers:
                self._server_timestamp = response.headers["X-Server-Timestamp"]
            
            result = response.json()
            
            if isinstance(result, dict) and "items" in result:
                return result["items"]
            elif isinstance(result, list):
                return result
            else:
                raise AdapterError("Invalid batch response format", "rest")
                
        except httpx.HTTPStatusError as e:
            raise NetworkError(f"Failed to fetch batch: {str(e)}")
        except httpx.RequestError as e:
            raise NetworkError(f"Request failed: {str(e)}")
    
    async def is_online(self) -> bool:
        """Check if the server is reachable.
        
        Returns:
            True if the server is reachable, False otherwise
        """
        try:
            # Try to ping the server
            response = await self.client.get(
                f"{self.base_url}/ping",
                timeout=5.0,
                headers=self.headers
            )
            return response.status_code == 200
        except Exception:
            try:
                # Fallback: try the base URL
                response = await self.client.get(
                    self.base_url,
                    timeout=5.0,
                    headers=self.headers
                )
                return response.status_code < 500
            except Exception:
                return False
    
    def get_server_timestamp(self) -> Optional[str]:
        """Get the server's timestamp from the last response.
        
        Returns:
            The server's timestamp, or None if not available
        """
        if not self._server_timestamp:
            # If we don't have a server timestamp, use the current time
            return datetime.utcnow().isoformat() + "Z"
        
        return self._server_timestamp
    
    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Make an HTTP request with retries.
        
        Args:
            method: The HTTP method to use
            url: The URL to request
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            The HTTP response
            
        Raises:
            NetworkError: If all retries fail
        """
        headers = {**self.headers}
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        
        for i in range(self.retry_count + 1):
            try:
                response = await getattr(self.client, method.lower())(
                    url,
                    headers=headers,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if isinstance(e, httpx.HTTPStatusError):
                    # Don't retry client errors except for 429 (too many requests)
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        raise
                
                # If this was the last attempt, raise the error
                if i == self.retry_count:
                    raise
                
                # Otherwise, wait and retry
                logger.warning(f"Request failed, retrying ({i+1}/{self.retry_count}): {str(e)}")
                await asyncio.sleep(self.retry_delay * (2 ** i))  # Exponential backoff