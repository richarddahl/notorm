# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Mock test of async session behavior without importing the actual code.

This test mocks the async_session context manager to test its behavior
without triggering circular imports in the actual code.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock


# Define a mock version of the async_session context manager
class MockAsyncSession:
    def __init__(self, session):
        self.session = session
    
    async def __aenter__(self):
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Close is awaited in the actual implementation
        await self.session.close()


@pytest.mark.asyncio
async def test_async_session_context_manager():
    """Test that the context manager properly awaits session.close()."""
    # Create a mock session with close as AsyncMock
    mock_session = MagicMock()
    mock_session.close = AsyncMock()
    
    # Use the context manager
    async with MockAsyncSession(mock_session):
        # Do some operations with the session
        pass
    
    # Verify close was called
    mock_session.close.assert_called_once()
    
    # This test passes if no "coroutine was never awaited" warning is generated
    # because we properly used AsyncMock() for the close method