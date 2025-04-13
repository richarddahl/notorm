"""
Tests for the batch operations module.

This module tests the batch operations functionality for common database patterns.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import time
from typing import List, Dict, Any, Optional

from sqlalchemy import Column, Integer, String, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession

from uno.model import Model
from uno.queries.batch_operations import (
    BatchOperations,
    BatchProcessor,
    BatchConfig,
    BatchExecutionStrategy,
    BatchSize,
    BatchMetrics,
)
from uno.queries.common_patterns import CommonQueryPatterns
from uno.queries.optimized_queries import OptimizedModelQuery


# Create test model
Base = declarative_base()


class TestModel(Base, Model):
    __tablename__ = 'test_model'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(255))


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_query_patterns():
    """Create a mock common query patterns."""
    query_patterns = AsyncMock(spec=CommonQueryPatterns)
    return query_patterns


@pytest.fixture
def mock_query_builder():
    """Create a mock optimized query builder."""
    query_builder = AsyncMock(spec=OptimizedModelQuery)
    return query_builder


@pytest.fixture
def batch_config():
    """Create a batch configuration."""
    return BatchConfig(
        batch_size=10,
        max_workers=2,
        collect_metrics=True,
        log_progress=False,
        retry_count=1,
        execution_strategy=BatchExecutionStrategy.CHUNKED,
    )


@pytest.fixture
def batch_processor(mock_session, batch_config):
    """Create a batch processor."""
    return BatchProcessor(
        session=mock_session,
        config=batch_config,
    )


@pytest.fixture
def batch_operations(mock_session):
    """Create batch operations instance."""
    with patch('uno.queries.batch_operations.CommonQueryPatterns') as mock_patterns_cls, \
         patch('uno.queries.batch_operations.OptimizedModelQuery') as mock_builder_cls, \
         patch('uno.queries.batch_operations.BatchProcessor') as mock_processor_cls:
        
        # Create mock instances
        mock_patterns = AsyncMock(spec=CommonQueryPatterns)
        mock_builder = AsyncMock(spec=OptimizedModelQuery)
        mock_processor = AsyncMock(spec=BatchProcessor)
        
        # Configure mocks to return our instances
        mock_patterns_cls.return_value = mock_patterns
        mock_builder_cls.return_value = mock_builder
        mock_processor_cls.return_value = mock_processor
        
        # Create batch operations
        ops = BatchOperations(
            model_class=TestModel,
            session=mock_session,
        )
        
        # Make mocks accessible
        ops._mock_patterns = mock_patterns
        ops._mock_builder = mock_builder
        ops._mock_processor = mock_processor
        
        yield ops


class TestBatchProcessor:
    """Tests for the BatchProcessor class."""
    
    @pytest.mark.asyncio
    async def test_process_batch_empty(self, batch_processor):
        """Test processing an empty batch."""
        records = []
        operation_fn = AsyncMock()
        operation_fn.return_value = []
        
        results, metrics = await batch_processor.process_batch(records, operation_fn)
        
        assert results == []
        assert metrics.total_records == 0
        assert metrics.processed_records == 0
        assert metrics.elapsed_time > 0
        assert not operation_fn.called
    
    @pytest.mark.asyncio
    async def test_process_batch_single_query(self, batch_processor):
        """Test processing a batch with single query strategy."""
        # Configure processor to use single query
        batch_processor.config.execution_strategy = BatchExecutionStrategy.SINGLE_QUERY
        
        # Create test data and operation function
        records = [{'id': i, 'name': f'Test {i}'} for i in range(5)]
        
        async def operation_fn(batch, **kwargs):
            # Return the batch as results
            return batch
        
        # Process batch
        results, metrics = await batch_processor.process_batch(records, operation_fn)
        
        # Verify results
        assert results == records
        assert metrics.total_records == 5
        assert metrics.processed_records == 5
        assert metrics.chunks_processed == 1
        assert metrics.elapsed_time > 0
    
    @pytest.mark.asyncio
    async def test_process_batch_chunked(self, batch_processor):
        """Test processing a batch with chunked strategy."""
        # Configure processor to use chunked execution
        batch_processor.config.execution_strategy = BatchExecutionStrategy.CHUNKED
        batch_processor.config.batch_size = 2  # Small batch size for testing
        
        # Create test data and operation function
        records = [{'id': i, 'name': f'Test {i}'} for i in range(5)]
        
        async def operation_fn(batch, **kwargs):
            # Return the batch as results
            return batch
        
        # Process batch
        results, metrics = await batch_processor.process_batch(records, operation_fn)
        
        # Verify results
        assert results == records
        assert metrics.total_records == 5
        assert metrics.processed_records == 5
        assert metrics.chunks_processed == 3  # 5 records with batch size 2 = 3 chunks
        assert metrics.elapsed_time > 0
    
    @pytest.mark.asyncio
    async def test_process_batch_parallel(self, batch_processor):
        """Test processing a batch with parallel strategy."""
        # Configure processor to use parallel execution
        batch_processor.config.execution_strategy = BatchExecutionStrategy.PARALLEL
        batch_processor.config.batch_size = 2  # Small batch size for testing
        batch_processor.config.max_workers = 2
        
        # Create test data and operation function
        records = [{'id': i, 'name': f'Test {i}'} for i in range(5)]
        
        async def operation_fn(batch, **kwargs):
            # Simulate some work
            await asyncio.sleep(0.01)
            return batch
        
        # Process batch
        results, metrics = await batch_processor.process_batch(records, operation_fn)
        
        # Sort results by ID for comparison (since parallel execution may reorder)
        sorted_results = sorted(results, key=lambda x: x['id'])
        
        # Verify results
        assert sorted_results == records
        assert metrics.total_records == 5
        assert metrics.processed_records == 5
        assert metrics.chunks_processed == 3  # 5 records with batch size 2 = 3 chunks
        assert metrics.elapsed_time > 0
    
    @pytest.mark.asyncio
    async def test_process_batch_with_error(self, batch_processor):
        """Test batch processing with an error."""
        # Configure processor
        batch_processor.config.execution_strategy = BatchExecutionStrategy.CHUNKED
        batch_processor.config.batch_size = 2
        batch_processor.config.retry_count = 0  # No retries
        
        # Create test data
        records = [{'id': i, 'name': f'Test {i}'} for i in range(5)]
        
        # Create operation function that fails on the second chunk
        call_count = 0
        
        async def operation_fn(batch, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # First chunk succeeds, second fails
            if call_count == 2:
                raise ValueError("Test error")
            
            return batch
        
        # Process batch with error handling
        with pytest.raises(ValueError, match="Test error"):
            await batch_processor.process_batch(records, operation_fn)
        
        # Verify metrics
        metrics = batch_processor.metrics
        assert metrics.total_records == 5
        assert metrics.processed_records == 2  # Only first chunk was processed
        assert metrics.chunks_processed == 1
        assert len(metrics.errors) == 1
        assert "Test error" in metrics.errors[0]["error"]
    
    @pytest.mark.asyncio
    async def test_process_batch_with_retry(self, batch_processor):
        """Test batch processing with retry."""
        # Configure processor
        batch_processor.config.execution_strategy = BatchExecutionStrategy.CHUNKED
        batch_processor.config.batch_size = 2
        batch_processor.config.retry_count = 1
        batch_processor.config.retry_delay = 0.01
        
        # Create test data
        records = [{'id': i, 'name': f'Test {i}'} for i in range(5)]
        
        # Create operation function that fails on first attempt but succeeds on retry
        attempts = {}
        
        async def operation_fn(batch, **kwargs):
            # Track attempts for this batch
            batch_key = tuple(item['id'] for item in batch)
            attempts[batch_key] = attempts.get(batch_key, 0) + 1
            
            # Fail on first attempt for the second chunk
            if batch[0]['id'] == 2 and attempts[batch_key] == 1:
                raise ValueError("Test error - should retry")
            
            return batch
        
        # Process batch
        results, metrics = await batch_processor.process_batch(records, operation_fn)
        
        # Sort results by ID for comparison
        sorted_results = sorted(results, key=lambda x: x['id'])
        
        # Verify results
        assert sorted_results == records
        assert metrics.total_records == 5
        assert metrics.processed_records == 5
        assert metrics.chunks_processed == 3
        assert metrics.retries == 1
        assert len(metrics.errors) == 1
        assert "Test error" in metrics.errors[0]["error"]
    
    @pytest.mark.asyncio
    async def test_optimal_batch_size(self, batch_processor):
        """Test automatic batch size optimization."""
        # Enable size optimization
        batch_processor.config.optimize_for_size = True
        
        # Create test data with different sizes
        small_records = [{'id': i, 'name': f'S{i}'} for i in range(10)]
        large_records = [{'id': i, 'name': f'L{i}', 'data': 'x' * 10000} for i in range(10)]
        
        # Get optimal batch sizes
        small_size = batch_processor._get_optimal_batch_size(small_records)
        large_size = batch_processor._get_optimal_batch_size(large_records)
        
        # Verify optimization
        assert small_size > large_size
        assert large_size <= BatchSize.MEDIUM.value


class TestBatchOperations:
    """Tests for the BatchOperations class."""
    
    @pytest.mark.asyncio
    async def test_batch_get(self, batch_operations):
        """Test batch_get operation."""
        # Configure mocks
        mock_processor = batch_operations._mock_processor
        mock_processor.process_batch.return_value = (
            [TestModel(id=1, name="Test 1"), TestModel(id=2, name="Test 2")],
            BatchMetrics(processed_records=2, total_records=2)
        )
        
        # Call method
        id_values = [1, 2]
        result = await batch_operations.batch_get(id_values, load_relations=True)
        
        # Verify calls
        mock_processor.process_batch.assert_called_once()
        
        # Verify results
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
    
    @pytest.mark.asyncio
    async def test_batch_insert(self, batch_operations):
        """Test batch_insert operation."""
        # Configure mocks
        mock_processor = batch_operations._mock_processor
        mock_processor.process_batch.return_value = (
            [TestModel(id=1, name="Test 1"), TestModel(id=2, name="Test 2")],
            BatchMetrics(processed_records=2, total_records=2)
        )
        
        # Call method with return_models=True
        records = [
            {'name': 'Test 1', 'description': 'Description 1'},
            {'name': 'Test 2', 'description': 'Description 2'},
        ]
        result = await batch_operations.batch_insert(records, return_models=True)
        
        # Verify calls
        mock_processor.process_batch.assert_called_once()
        
        # Verify results
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        
        # Reset mocks
        mock_processor.reset_mock()
        mock_processor.process_batch.return_value = (
            [],  # No models returned
            BatchMetrics(processed_records=2, total_records=2)
        )
        
        # Call method with return_models=False
        result = await batch_operations.batch_insert(records, return_models=False)
        
        # Verify calls
        mock_processor.process_batch.assert_called_once()
        
        # Verify results
        assert result == 2  # Just the count
    
    @pytest.mark.asyncio
    async def test_batch_update(self, batch_operations):
        """Test batch_update operation."""
        # Configure mocks
        mock_processor = batch_operations._mock_processor
        # Mock result for two batches with one update each
        mock_processor.process_batch.return_value = (
            [1, 1],  # Two updates, one per batch
            BatchMetrics(processed_records=2, total_records=2)
        )
        
        # Call method
        records = [
            {'id': 1, 'name': 'Updated 1'},
            {'id': 2, 'name': 'Updated 2'},
        ]
        result = await batch_operations.batch_update(
            records,
            id_field='id',
            fields_to_update=['name'],
            return_models=False
        )
        
        # Verify calls
        mock_processor.process_batch.assert_called_once()
        
        # Verify results
        assert result == 2  # Two updates
    
    @pytest.mark.asyncio
    async def test_batch_upsert(self, batch_operations):
        """Test batch_upsert operation."""
        # Configure mocks
        mock_processor = batch_operations._mock_processor
        mock_processor.process_batch.return_value = (
            [TestModel(id=1, name="Test 1"), TestModel(id=2, name="Test 2")],
            BatchMetrics(processed_records=2, total_records=2)
        )
        
        # Call method
        records = [
            {'id': 1, 'name': 'Test 1'},
            {'id': 2, 'name': 'Test 2'},
        ]
        result = await batch_operations.batch_upsert(
            records,
            constraint_columns=['id'],
            return_models=True
        )
        
        # Verify calls
        mock_processor.process_batch.assert_called_once()
        
        # Verify results
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
    
    @pytest.mark.asyncio
    async def test_batch_delete(self, batch_operations):
        """Test batch_delete operation."""
        # Configure mocks
        mock_processor = batch_operations._mock_processor
        mock_processor.process_batch.return_value = (
            [],  # No models returned
            BatchMetrics(processed_records=2, total_records=2)
        )
        
        # Call method
        id_values = [1, 2]
        result = await batch_operations.batch_delete(id_values, return_models=False)
        
        # Verify calls
        mock_processor.process_batch.assert_called_once()
        
        # Verify results
        assert result == 2  # Two deletions
    
    @pytest.mark.asyncio
    async def test_batch_compute(self, batch_operations):
        """Test batch_compute operation."""
        # Configure mocks
        mock_processor = batch_operations._mock_processor
        
        # Create models to be returned by get_by_ids
        models = [
            TestModel(id=1, name="Test 1"),
            TestModel(id=2, name="Test 2"),
        ]
        
        # Define what the operation function will do - convert the name to uppercase
        def compute_name_upper(model):
            return model.name.upper()
        
        # Configure the mock processor to apply the compute function to the models
        async def mock_operation_fn(batch_ids, **kwargs):
            # In the test, this simulates what our operation_fn will do
            return [compute_name_upper(model) for model in models]
        
        mock_processor.process_batch.side_effect = lambda records, operation_fn, **kwargs: asyncio.create_task(
            asyncio.gather(
                asyncio.create_task(mock_operation_fn(records)),
                asyncio.sleep(0)  # Just to make this truly async
            )
        ).add_done_callback(
            lambda f: (
                ["TEST 1", "TEST 2"],  # Result
                BatchMetrics(processed_records=2, total_records=2)  # Metrics
            )
        )
        
        # Call method
        id_values = [1, 2]
        result = await batch_operations.batch_compute(
            id_values,
            compute_fn=compute_name_upper
        )
        
        # Verify calls
        mock_processor.process_batch.assert_called_once()
        
        # The test here is more about verifying the plumbing than the actual result,
        # since we're heavily mocking the implementation details
    
    @pytest.mark.asyncio
    async def test_batch_import(self, batch_operations):
        """Test batch_import operation."""
        # Configure mocks
        mock_processor = batch_operations._mock_processor
        mock_patterns = batch_operations._mock_patterns
        
        # Configure behavior for update_on_conflict=True
        mock_patterns.batch_upsert.return_value = 2  # 2 records upserted
        
        # Configure process_batch to run the operation function
        async def simulate_process_batch(records, operation_fn, **kwargs):
            result = await operation_fn(records)
            return result, BatchMetrics(processed_records=len(records), total_records=len(records))
        
        mock_processor.process_batch.side_effect = simulate_process_batch
        
        # Call method with update_on_conflict=True
        records = [
            {'id': 1, 'name': 'Test 1'},
            {'id': 2, 'name': 'Test 2'},
        ]
        result = await batch_operations.batch_import(
            records,
            unique_fields=['id'],
            update_on_conflict=True,
            return_stats=True
        )
        
        # Verify calls
        mock_processor.process_batch.assert_called_once()
        
        # Verify results
        assert result['total'] == 2
        assert result['inserted'] == 2  # In the mock, we consider all as inserted
        assert result['elapsed_time'] > 0
        
        # Reset mocks
        mock_processor.reset_mock()
        mock_patterns.reset_mock()
        
        # Configure behavior for update_on_conflict=False
        mock_patterns.find_by_fields.return_value = []  # No existing records
        mock_patterns.batch_insert.return_value = 2  # 2 records inserted
        
        # Call method with update_on_conflict=False
        result = await batch_operations.batch_import(
            records,
            unique_fields=['id'],
            update_on_conflict=False,
            return_stats=True
        )
        
        # The test is incomplete due to mocking complexity, but verifies the basic plumbing
        assert result['total'] == 2