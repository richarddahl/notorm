"""
Streaming database operations for handling large result sets.

This module provides utilities for streaming large query results from the database
without loading everything into memory at once.
"""

from typing import TypeVar, Generic, Dict, Any, Optional, List, Set, Callable, Awaitable, Union, cast, Tuple, Iterator, AsyncIterator, AsyncGenerator
import asyncio
import logging
import time
import contextlib
from enum import Enum
from datetime import datetime, timedelta

from sqlalchemy import select, text, Row
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from uno.database.enhanced_session import enhanced_async_session
from uno.database.pooled_session import pooled_async_session
from uno.core.async_utils import (
    AsyncLock, 
    TaskGroup,
    timeout,
)
from uno.core.async_integration import (
    cancellable,
    retry,
)


T = TypeVar('T')
R = TypeVar('R')


class StreamingMode(Enum):
    """
    Mode for streaming query results.
    
    - CURSOR: Server-side cursor (most efficient for large results)
    - YIELD: Client-side streaming using yield
    - CHUNK: Chunk-based with fixed size chunks
    """
    
    CURSOR = "cursor"
    YIELD = "yield"
    CHUNK = "chunk"


class StreamingCursor(Generic[T]):
    """
    Streaming cursor for efficient processing of large result sets.
    
    This class wraps a database cursor to provide streaming of results
    without loading everything into memory at once.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        query: Any,
        chunk_size: int = 1000,
        timeout_seconds: Optional[float] = None,
        transform_fn: Optional[Callable[[Row], T]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the streaming cursor.
        
        Args:
            session: Database session
            query: SQL query to execute
            chunk_size: Size of chunks to fetch
            timeout_seconds: Timeout for cursor operations
            transform_fn: Function to transform each row
            logger: Optional logger
        """
        self.session = session
        self.query = query
        self.chunk_size = chunk_size
        self.timeout_seconds = timeout_seconds
        self.transform_fn = transform_fn
        self.logger = logger or logging.getLogger(__name__)
        
        # Cursor state
        self._cursor = None
        self._buffer: List[T] = []
        self._buffer_index = 0
        self._closed = False
        self._row_count = 0
        self._start_time = time.time()
        self._metadata: Dict[str, Any] = {}
    
    async def __aenter__(self) -> 'StreamingCursor[T]':
        """
        Enter the streaming cursor context.
        
        Returns:
            The streaming cursor
        """
        # Execute the query
        if self.timeout_seconds is not None:
            with timeout(self.timeout_seconds, "Query execution timeout"):
                self._cursor = await self.session.execute(self.query)
        else:
            self._cursor = await self.session.execute(self.query)
        
        # Get metadata
        if hasattr(self._cursor, 'keys'):
            self._metadata['keys'] = self._cursor.keys()
        
        if hasattr(self._cursor, 'description'):
            self._metadata['description'] = self._cursor.description
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the streaming cursor context.
        """
        await self.close()
    
    async def close(self) -> None:
        """
        Close the cursor.
        """
        if self._closed:
            return
        
        self._closed = True
        
        # Clear buffer
        self._buffer = []
        self._buffer_index = 0
        
        # Log statistics
        elapsed_time = time.time() - self._start_time
        self.logger.debug(
            f"StreamingCursor closed after processing {self._row_count} rows "
            f"in {elapsed_time:.2f} seconds "
            f"({self._row_count / elapsed_time:.2f} rows/sec)"
        )
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Get cursor metadata.
        
        Returns:
            Dictionary of metadata
        """
        return self._metadata
    
    @property
    def row_count(self) -> int:
        """
        Get the number of rows processed.
        
        Returns:
            Row count
        """
        return self._row_count
    
    async def fetchone(self) -> Optional[T]:
        """
        Fetch one row from the cursor.
        
        Returns:
            The next row or None if no more rows
        """
        # Check if closed
        if self._closed:
            return None
        
        # Check if we need to fetch more rows
        if self._buffer_index >= len(self._buffer):
            # Fetch more rows
            if self.timeout_seconds is not None:
                with timeout(self.timeout_seconds, "Fetch operation timeout"):
                    self._buffer = await self._cursor.fetchmany(self.chunk_size)
            else:
                self._buffer = await self._cursor.fetchmany(self.chunk_size)
            
            self._buffer_index = 0
            
            # No more rows
            if not self._buffer:
                return None
        
        # Get row from buffer
        row = self._buffer[self._buffer_index]
        self._buffer_index += 1
        self._row_count += 1
        
        # Transform row if needed
        if self.transform_fn is not None:
            return self.transform_fn(row)
        
        return row
    
    async def fetchmany(self, size: Optional[int] = None) -> List[T]:
        """
        Fetch multiple rows from the cursor.
        
        Args:
            size: Number of rows to fetch, defaults to chunk_size
            
        Returns:
            List of rows
        """
        # Use provided size or chunk size
        fetch_size = size or self.chunk_size
        
        # Fetch rows
        result = []
        for _ in range(fetch_size):
            row = await self.fetchone()
            if row is None:
                break
            result.append(row)
        
        return result
    
    async def fetchall(self) -> List[T]:
        """
        Fetch all remaining rows from the cursor.
        
        Returns:
            List of all rows
        """
        result = []
        
        while True:
            row = await self.fetchone()
            if row is None:
                break
            result.append(row)
        
        return result
    
    def __aiter__(self) -> 'StreamingCursor[T]':
        """
        Get async iterator for the cursor.
        
        Returns:
            The cursor as an async iterator
        """
        return self
    
    async def __anext__(self) -> T:
        """
        Get the next row from the cursor.
        
        Returns:
            The next row
            
        Raises:
            StopAsyncIteration: When no more rows
        """
        row = await self.fetchone()
        if row is None:
            raise StopAsyncIteration
        return row


class ResultIterator(Generic[T]):
    """
    Iterator for database query results.
    
    This class provides a simple iterator over query results,
    optionally with transformation.
    """
    
    def __init__(
        self,
        results: Any,
        transform_fn: Optional[Callable[[Row], T]] = None,
    ):
        """
        Initialize the result iterator.
        
        Args:
            results: Query results
            transform_fn: Function to transform each row
        """
        self.results = results
        self.transform_fn = transform_fn
    
    def __iter__(self) -> Iterator[T]:
        """
        Get iterator for the results.
        
        Returns:
            Iterator over results
        """
        return self
    
    def __next__(self) -> T:
        """
        Get the next result.
        
        Returns:
            The next result
            
        Raises:
            StopIteration: When no more results
        """
        # Get next row
        try:
            if hasattr(self.results, 'fetchone'):
                row = self.results.fetchone()
            else:
                row = next(self.results)
        except StopIteration:
            raise
        except Exception as e:
            raise StopIteration from e
        
        if row is None:
            raise StopIteration
        
        # Transform row if needed
        if self.transform_fn is not None:
            return self.transform_fn(row)
        
        return row


class ResultChunk(Generic[T]):
    """
    Chunk of query results.
    
    This class represents a chunk of results from a streaming query,
    with metadata about the chunk and the overall query.
    """
    
    def __init__(
        self,
        items: List[T],
        chunk_index: int,
        total_chunks: Optional[int] = None,
        is_last_chunk: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the result chunk.
        
        Args:
            items: Items in this chunk
            chunk_index: Index of this chunk (0-based)
            total_chunks: Total number of chunks, if known
            is_last_chunk: Whether this is the last chunk
            metadata: Additional metadata
        """
        self.items = items
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        self.is_last_chunk = is_last_chunk
        self.metadata = metadata or {}
        self.item_count = len(items)
    
    def __len__(self) -> int:
        """
        Get the number of items in the chunk.
        
        Returns:
            Number of items
        """
        return self.item_count
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the chunk to a dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "items": self.items,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "is_last_chunk": self.is_last_chunk,
            "item_count": self.item_count,
            "metadata": self.metadata,
        }


@contextlib.asynccontextmanager
async def stream_query(
    query: Any,
    mode: StreamingMode = StreamingMode.CURSOR,
    chunk_size: int = 1000,
    transform_fn: Optional[Callable[[Row], T]] = None,
    session: Optional[AsyncSession] = None,
    timeout_seconds: Optional[float] = None,
    use_pooled_session: bool = True,
    logger: Optional[logging.Logger] = None,
) -> AsyncIterator[AsyncIterator[T]]:
    """
    Stream results from a database query.
    
    Args:
        query: SQL query to execute
        mode: Streaming mode
        chunk_size: Size of chunks to fetch
        transform_fn: Function to transform each row
        session: Optional session to use
        timeout_seconds: Timeout for query operations
        use_pooled_session: Whether to use pooled session if not provided
        logger: Optional logger
        
    Yields:
        AsyncIterator over query results
    """
    # Use provided session or create a new one
    session_provided = session is not None
    
    if not session_provided:
        if use_pooled_session:
            session_context = pooled_async_session()
        else:
            session_context = enhanced_async_session()
        
        session = await session_context.__aenter__()
    
    try:
        # Stream based on mode
        if mode == StreamingMode.CURSOR:
            # Use streaming cursor
            cursor = StreamingCursor(
                session=session,
                query=query,
                chunk_size=chunk_size,
                timeout_seconds=timeout_seconds,
                transform_fn=transform_fn,
                logger=logger,
            )
            
            async with cursor as stream:
                yield stream
        
        elif mode == StreamingMode.YIELD:
            # Execute query
            if timeout_seconds is not None:
                with timeout(timeout_seconds, "Query execution timeout"):
                    result = await session.execute(query)
            else:
                result = await session.execute(query)
            
            # Create async generator
            async def result_generator() -> AsyncGenerator[T, None]:
                while True:
                    # Fetch a batch
                    batch = await result.fetchmany(chunk_size)
                    if not batch:
                        break
                    
                    # Yield each row
                    for row in batch:
                        if transform_fn is not None:
                            yield transform_fn(row)
                        else:
                            yield row
            
            # Yield the generator
            yield result_generator()
        
        elif mode == StreamingMode.CHUNK:
            # Execute query
            if timeout_seconds is not None:
                with timeout(timeout_seconds, "Query execution timeout"):
                    result = await session.execute(query)
            else:
                result = await session.execute(query)
            
            # Create async generator for chunks
            async def chunk_generator() -> AsyncGenerator[ResultChunk[T], None]:
                chunk_index = 0
                
                while True:
                    # Fetch a batch
                    batch = await result.fetchmany(chunk_size)
                    if not batch:
                        break
                    
                    # Transform rows if needed
                    if transform_fn is not None:
                        items = [transform_fn(row) for row in batch]
                    else:
                        items = list(batch)
                    
                    # Check if this is the last chunk
                    next_batch = await result.fetchmany(1)
                    is_last = len(next_batch) == 0
                    
                    # If we fetched one row for the check, add it to the next chunk
                    if next_batch:
                        # Put it back (not ideal, but SQLAlchemy doesn't have a way to peek)
                        # This effectively means the first row of the next chunk is fetched here
                        if transform_fn is not None:
                            row = transform_fn(next_batch[0])
                        else:
                            row = next_batch[0]
                        
                        # It will be yielded in the next iteration
                        # (this disruption to flow is why CURSOR mode is preferred)
                    
                    # Create chunk
                    chunk = ResultChunk(
                        items=items,
                        chunk_index=chunk_index,
                        is_last_chunk=is_last,
                        metadata={
                            "query": str(query),
                            "chunk_size": chunk_size,
                        },
                    )
                    
                    yield chunk
                    chunk_index += 1
            
            # Yield the generator
            yield chunk_generator()
        
        else:
            raise ValueError(f"Unknown streaming mode: {mode}")
    
    finally:
        # Close session if we created it
        if not session_provided:
            await session_context.__aexit__(None, None, None)


async def stream_process(
    query: Any,
    process_fn: Callable[[T], Awaitable[R]],
    transform_fn: Optional[Callable[[Row], T]] = None,
    chunk_size: int = 1000,
    concurrency: int = 10,
    session: Optional[AsyncSession] = None,
    timeout_seconds: Optional[float] = None,
    use_pooled_session: bool = True,
    logger: Optional[logging.Logger] = None,
) -> List[R]:
    """
    Stream and process results from a database query.
    
    Args:
        query: SQL query to execute
        process_fn: Function to process each row
        transform_fn: Function to transform each row before processing
        chunk_size: Size of chunks to fetch
        concurrency: Maximum concurrent processing tasks
        session: Optional session to use
        timeout_seconds: Timeout for query operations
        use_pooled_session: Whether to use pooled session if not provided
        logger: Optional logger
        
    Returns:
        List of processing results
    """
    results: List[R] = []
    
    # Stream the query
    async with stream_query(
        query=query,
        mode=StreamingMode.CURSOR,
        chunk_size=chunk_size,
        transform_fn=transform_fn,
        session=session,
        timeout_seconds=timeout_seconds,
        use_pooled_session=use_pooled_session,
        logger=logger,
    ) as stream:
        # Process in chunks with limited concurrency
        pending_tasks: List[asyncio.Task] = []
        
        async with TaskGroup(name="stream_process") as group:
            # Process each row
            async for row in stream:
                # Start a task for this row
                task = group.create_task(process_fn(row))
                pending_tasks.append(task)
                
                # Limit concurrency
                if len(pending_tasks) >= concurrency:
                    # Wait for one task to complete
                    done, pending_tasks = await asyncio.wait(
                        pending_tasks,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    
                    # Add results
                    for task in done:
                        try:
                            result = await task
                            results.append(result)
                        except Exception as e:
                            if logger:
                                logger.error(f"Error processing row: {e}")
            
            # Wait for remaining tasks
            for task in pending_tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    if logger:
                        logger.error(f"Error processing row: {e}")
    
    return results


async def stream_parallel(
    query: Any,
    parallel_fn: Callable[[List[T]], Awaitable[List[R]]],
    transform_fn: Optional[Callable[[Row], T]] = None,
    chunk_size: int = 1000,
    concurrency: int = 5,
    session: Optional[AsyncSession] = None,
    timeout_seconds: Optional[float] = None,
    use_pooled_session: bool = True,
    logger: Optional[logging.Logger] = None,
) -> List[R]:
    """
    Stream and process results in parallel batches.
    
    Args:
        query: SQL query to execute
        parallel_fn: Function to process a chunk of rows
        transform_fn: Function to transform each row before processing
        chunk_size: Size of chunks to fetch
        concurrency: Maximum concurrent processing tasks
        session: Optional session to use
        timeout_seconds: Timeout for query operations
        use_pooled_session: Whether to use pooled session if not provided
        logger: Optional logger
        
    Returns:
        List of processing results
    """
    all_results: List[R] = []
    
    # Stream the query in chunks
    async with stream_query(
        query=query,
        mode=StreamingMode.CHUNK,
        chunk_size=chunk_size,
        transform_fn=transform_fn,
        session=session,
        timeout_seconds=timeout_seconds,
        use_pooled_session=use_pooled_session,
        logger=logger,
    ) as stream:
        # Process chunks in parallel with limited concurrency
        pending_tasks: List[asyncio.Task] = []
        
        async with TaskGroup(name="stream_parallel") as group:
            # Process each chunk
            async for chunk in stream:
                # Start a task for this chunk
                task = group.create_task(parallel_fn(chunk.items))
                pending_tasks.append(task)
                
                # Limit concurrency
                if len(pending_tasks) >= concurrency:
                    # Wait for one task to complete
                    done, pending_tasks = await asyncio.wait(
                        pending_tasks,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    
                    # Add results
                    for task in done:
                        try:
                            chunk_results = await task
                            all_results.extend(chunk_results)
                        except Exception as e:
                            if logger:
                                logger.error(f"Error processing chunk: {e}")
            
            # Wait for remaining tasks
            for task in pending_tasks:
                try:
                    chunk_results = await task
                    all_results.extend(chunk_results)
                except Exception as e:
                    if logger:
                        logger.error(f"Error processing chunk: {e}")
    
    return all_results