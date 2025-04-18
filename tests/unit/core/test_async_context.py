"""
Tests for the enhanced async context management primitives.

This module tests the functionality of the AsyncContextGroup, async_contextmanager
decorator, and other async context utilities.
"""

import asyncio
import logging
import pytest
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from uno.core.asynchronous.context import (
    AsyncContextGroup,
    async_contextmanager,
    AsyncExitStack,
)


# =============================================================================
# Test Context Managers
# =============================================================================

class TestContextManager:
    """A simple test context manager for testing."""
    
    def __init__(self, name: str, raise_on_enter: bool = False, raise_on_exit: bool = False):
        self.name = name
        self.entered = False
        self.exited = False
        self.raise_on_enter = raise_on_enter
        self.raise_on_exit = raise_on_exit
        self.exc_info = None
    
    async def __aenter__(self):
        if self.raise_on_enter:
            raise ValueError(f"Error entering {self.name}")
        self.entered = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exited = True
        self.exc_info = (exc_type, exc_val, exc_tb)
        if self.raise_on_exit:
            raise ValueError(f"Error exiting {self.name}")
        return False  # Don't suppress exceptions


@async_contextmanager
async def test_context(name: str, raise_on_yield: bool = False, raise_after_yield: bool = False):
    """Test async context manager function."""
    try:
        if raise_on_yield:
            raise ValueError(f"Error before yield in {name}")
        yield name
        if raise_after_yield:
            raise ValueError(f"Error after yield in {name}")
    except Exception as e:
        raise


# =============================================================================
# Test Cases
# =============================================================================

class TestAsyncContextGroup:
    """Tests for the AsyncContextGroup class."""
    
    @pytest.mark.asyncio
    async def test_context_group_basic(self):
        """Test basic functionality of AsyncContextGroup."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2")
        group = AsyncContextGroup(ctx1, ctx2, name="TestGroup")
        
        # Act
        async with group as g:
            # Assert
            assert ctx1.entered
            assert not ctx1.exited
            assert ctx2.entered
            assert not ctx2.exited
            assert g.results[ctx1] == ctx1
            assert g.results[ctx2] == ctx2
        
        # Assert after context exit
        assert ctx1.exited
        assert ctx2.exited
    
    @pytest.mark.asyncio
    async def test_context_group_error_on_enter(self):
        """Test AsyncContextGroup with error during enter."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2", raise_on_enter=True)
        ctx3 = TestContextManager("ctx3")
        group = AsyncContextGroup(ctx1, ctx2, ctx3, name="TestGroup")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Error entering ctx2"):
            async with group:
                pass
        
        # Check that ctx1 was entered and then exited
        assert ctx1.entered
        assert ctx1.exited
        
        # Check that ctx2 was not successfully entered
        assert not ctx2.entered
        
        # Check that ctx3 was not entered at all
        assert not ctx3.entered
    
    @pytest.mark.asyncio
    async def test_context_group_error_on_exit(self):
        """Test AsyncContextGroup with error during exit."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2", raise_on_exit=True)
        ctx3 = TestContextManager("ctx3")
        group = AsyncContextGroup(ctx1, ctx2, ctx3, name="TestGroup")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Error exiting ctx2"):
            async with group:
                pass
        
        # Check that all were entered
        assert ctx1.entered
        assert ctx2.entered
        assert ctx3.entered
        
        # Check that all were exited (even though ctx2 exit failed)
        assert ctx1.exited
        assert ctx2.exited
        assert ctx3.exited
    
    @pytest.mark.asyncio
    async def test_context_group_exception_in_body(self):
        """Test AsyncContextGroup with exception in the context body."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2")
        group = AsyncContextGroup(ctx1, ctx2, name="TestGroup")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Error in body"):
            async with group:
                raise ValueError("Error in body")
        
        # Check that all were entered and exited
        assert ctx1.entered and ctx1.exited
        assert ctx2.entered and ctx2.exited
        
        # Check that exception was propagated to exit handlers
        assert ctx1.exc_info[0] is ValueError
        assert str(ctx1.exc_info[1]) == "Error in body"
    
    @pytest.mark.asyncio
    async def test_context_group_dynamic_add(self):
        """Test adding contexts dynamically to AsyncContextGroup."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2")
        group = AsyncContextGroup(ctx1, name="TestGroup")
        
        # Act
        async with group as g:
            assert ctx1.entered
            assert g.results[ctx1] == ctx1
            
            # Add ctx2 dynamically
            ctx2_result = await g.enter_async_context(ctx2)
            
            # Assert
            assert ctx2.entered
            assert ctx2_result == ctx2
            assert g.results[ctx2] == ctx2
        
        # Assert after context exit
        assert ctx1.exited
        assert ctx2.exited
    
    @pytest.mark.asyncio
    async def test_context_group_add_before_enter(self):
        """Test adding a context before entering the group."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2")
        group = AsyncContextGroup(ctx1, name="TestGroup")
        
        # Add ctx2 before entering
        group.add(ctx2)
        
        # Act
        async with group as g:
            # Assert
            assert ctx1.entered
            assert ctx2.entered
            assert g.results[ctx1] == ctx1
            assert g.results[ctx2] == ctx2
        
        # Assert after context exit
        assert ctx1.exited
        assert ctx2.exited
    
    @pytest.mark.asyncio
    async def test_context_group_add_after_enter_error(self):
        """Test that adding after entering raises an error."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2")
        group = AsyncContextGroup(ctx1, name="TestGroup")
        
        # Act & Assert
        async with group as g:
            with pytest.raises(RuntimeError, match="Cannot add context to group"):
                group.add(ctx2)
    
    @pytest.mark.asyncio
    async def test_context_group_enter_context_before_group_entered(self):
        """Test that enter_async_context before group is entered raises an error."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2")
        group = AsyncContextGroup(ctx1, name="TestGroup")
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="AsyncContextGroup must be entered"):
            await group.enter_async_context(ctx2)


class TestAsyncContextManager:
    """Tests for the async_contextmanager decorator."""
    
    @pytest.mark.asyncio
    async def test_async_context_manager_basic(self):
        """Test basic functionality of async_contextmanager."""
        # Arrange & Act
        result = None
        async with test_context("test") as name:
            result = name
        
        # Assert
        assert result == "test"
    
    @pytest.mark.asyncio
    async def test_async_context_manager_error_before_yield(self):
        """Test async_contextmanager with error before yield."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Error before yield in test"):
            async with test_context("test", raise_on_yield=True):
                pass
    
    @pytest.mark.asyncio
    async def test_async_context_manager_error_after_yield(self):
        """Test async_contextmanager with error after yield."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Error after yield in test"):
            async with test_context("test", raise_after_yield=True):
                pass
    
    @pytest.mark.asyncio
    async def test_async_context_manager_exception_in_body(self):
        """Test async_contextmanager with exception in the context body."""
        # Arrange
        body_executed = False
        after_body_executed = False
        
        # Create a context manager that will check if exception was received
        @async_contextmanager
        async def context_with_exc_check():
            try:
                yield "test"
                after_body_executed = True  # This should not execute
            except ValueError as e:
                assert str(e) == "Error in body"
                raise  # Re-raise the exception
        
        # Act & Assert
        with pytest.raises(ValueError, match="Error in body"):
            async with context_with_exc_check():
                body_executed = True
                raise ValueError("Error in body")
        
        # Check execution flow
        assert body_executed
        assert not after_body_executed


class TestAsyncExitStack:
    """Tests for AsyncExitStack."""
    
    @pytest.mark.asyncio
    async def test_async_exit_stack(self):
        """Test AsyncExitStack functionality."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2")
        
        # Act
        async with AsyncExitStack() as stack:
            await stack.enter_async_context(ctx1)
            await stack.enter_async_context(ctx2)
            
            # Assert during context
            assert ctx1.entered
            assert ctx2.entered
        
        # Assert after exit
        assert ctx1.exited
        assert ctx2.exited
    
    @pytest.mark.asyncio
    async def test_async_exit_stack_exception(self):
        """Test AsyncExitStack with exception propagation."""
        # Arrange
        ctx1 = TestContextManager("ctx1")
        ctx2 = TestContextManager("ctx2")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Test exception"):
            async with AsyncExitStack() as stack:
                await stack.enter_async_context(ctx1)
                await stack.enter_async_context(ctx2)
                raise ValueError("Test exception")
        
        # Verify contexts were exited
        assert ctx1.exited
        assert ctx2.exited
        
        # Check that exception was propagated to exit handlers
        assert ctx1.exc_info[0] is ValueError
        assert str(ctx1.exc_info[1]) == "Test exception"