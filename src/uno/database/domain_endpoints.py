# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain endpoints for the Database module.

This module defines FastAPI endpoints for the Database module,
providing an HTTP API for database operations, query execution,
optimization, and monitoring.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body

from uno.core.errors.result import Failure
from uno.database.entities import (
    ConnectionConfig, TransactionId, TransactionIsolationLevel,
    QueryRequest, QueryResponse, ConnectionTestRequest, ConnectionTestResponse,
    OptimizationRequest, OptimizationResponse, TransactionRequest, TransactionResponse,
    IndexRecommendation, IndexType
)
from uno.database.domain_services import (
    DatabaseManagerServiceProtocol,
    QueryExecutionServiceProtocol,
    QueryOptimizerServiceProtocol,
    QueryCacheServiceProtocol,
    TransactionServiceProtocol,
    ConnectionPoolServiceProtocol
)
from uno.database.domain_provider import DatabaseProvider


# Dependency Injection

def get_database_manager() -> DatabaseManagerServiceProtocol:
    """Get the database manager service."""
    return DatabaseProvider.get_database_manager()


def get_query_execution() -> QueryExecutionServiceProtocol:
    """Get the query execution service."""
    return DatabaseProvider.get_query_execution()


def get_query_optimizer() -> QueryOptimizerServiceProtocol:
    """Get the query optimizer service."""
    return DatabaseProvider.get_query_optimizer()


def get_query_cache() -> QueryCacheServiceProtocol:
    """Get the query cache service."""
    return DatabaseProvider.get_query_cache()


def get_transaction() -> TransactionServiceProtocol:
    """Get the transaction service."""
    return DatabaseProvider.get_transaction()


def get_connection_pool() -> ConnectionPoolServiceProtocol:
    """Get the connection pool service."""
    return DatabaseProvider.get_connection_pool()


# Router

router = APIRouter(prefix="/api/database", tags=["database"])


# Connection Management Endpoints

@router.post("/connection/test", response_model=ConnectionTestResponse)
async def test_connection(
    request: ConnectionTestRequest,
    db_manager: DatabaseManagerServiceProtocol = Depends(get_database_manager)
) -> ConnectionTestResponse:
    """
    Test a database connection.
    
    Args:
        request: Connection test request
        db_manager: Database manager service
        
    Returns:
        Connection test response
    """
    result = await db_manager.test_connection(request.config)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return result.value


@router.post("/connection/create")
async def create_database(
    config: ConnectionConfig,
    db_manager: DatabaseManagerServiceProtocol = Depends(get_database_manager)
) -> Dict[str, Any]:
    """
    Create a new database.
    
    Args:
        config: Connection configuration
        db_manager: Database manager service
        
    Returns:
        Success message
    """
    result = await db_manager.create_database(config)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return {"message": f"Database {config.db_name} created successfully"}


@router.post("/connection/drop")
async def drop_database(
    config: ConnectionConfig,
    db_manager: DatabaseManagerServiceProtocol = Depends(get_database_manager)
) -> Dict[str, Any]:
    """
    Drop a database.
    
    Args:
        config: Connection configuration
        db_manager: Database manager service
        
    Returns:
        Success message
    """
    result = await db_manager.drop_database(config)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return {"message": f"Database {config.db_name} dropped successfully"}


@router.post("/script")
async def execute_script(
    script: str = Body(..., media_type="text/plain"),
    db_manager: DatabaseManagerServiceProtocol = Depends(get_database_manager)
) -> Dict[str, Any]:
    """
    Execute a SQL script.
    
    Args:
        script: SQL script to execute
        db_manager: Database manager service
        
    Returns:
        Success message
    """
    result = await db_manager.execute_script(script)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return {"message": "Script executed successfully"}


@router.post("/extension")
async def create_extension(
    extension_name: str,
    schema: Optional[str] = None,
    db_manager: DatabaseManagerServiceProtocol = Depends(get_database_manager)
) -> Dict[str, Any]:
    """
    Create a database extension.
    
    Args:
        extension_name: Extension name
        schema: Optional schema name
        db_manager: Database manager service
        
    Returns:
        Success message
    """
    result = await db_manager.create_extension(extension_name, schema)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return {"message": f"Extension {extension_name} created successfully"}


# Query Execution Endpoints

@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    query_execution: QueryExecutionServiceProtocol = Depends(get_query_execution)
) -> QueryResponse:
    """
    Execute a database query.
    
    Args:
        request: Query request
        query_execution: Query execution service
        
    Returns:
        Query response
    """
    result = await query_execution.execute_query(request)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return result.value


@router.post("/query/batch", response_model=List[QueryResponse])
async def execute_batch_queries(
    requests: List[QueryRequest],
    query_execution: QueryExecutionServiceProtocol = Depends(get_query_execution)
) -> List[QueryResponse]:
    """
    Execute multiple queries in batch.
    
    Args:
        requests: List of query requests
        query_execution: Query execution service
        
    Returns:
        List of query responses
    """
    result = await query_execution.execute_batch_queries(requests)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return result.value


# Query Optimization Endpoints

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_query(
    request: OptimizationRequest,
    query_optimizer: QueryOptimizerServiceProtocol = Depends(get_query_optimizer)
) -> OptimizationResponse:
    """
    Optimize a database query.
    
    Args:
        request: Optimization request
        query_optimizer: Query optimizer service
        
    Returns:
        Optimization response
    """
    result = await query_optimizer.optimize_query(request)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return result.value


@router.get("/optimize/recommendations", response_model=List[Dict[str, Any]])
async def get_index_recommendations(
    table_name: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    query_optimizer: QueryOptimizerServiceProtocol = Depends(get_query_optimizer)
) -> List[Dict[str, Any]]:
    """
    Get index recommendations.
    
    Args:
        table_name: Optional table to get recommendations for
        limit: Maximum number of recommendations
        query_optimizer: Query optimizer service
        
    Returns:
        List of index recommendations
    """
    result = await query_optimizer.get_index_recommendations(table_name, limit)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    # Convert recommendations to dictionary
    return [
        {
            "table_name": r.table_name,
            "column_names": r.column_names,
            "index_type": r.index_type.name,
            "estimated_improvement": r.estimated_improvement,
            "rationale": r.rationale,
            "priority": r.priority,
            "creation_sql": r.to_sql()
        }
        for r in result.value
    ]


@router.post("/optimize/apply_recommendation")
async def apply_index_recommendation(
    recommendation: Dict[str, Any],
    query_optimizer: QueryOptimizerServiceProtocol = Depends(get_query_optimizer)
) -> Dict[str, Any]:
    """
    Apply an index recommendation.
    
    Args:
        recommendation: Index recommendation
        query_optimizer: Query optimizer service
        
    Returns:
        Success message
    """
    # Convert dictionary to IndexRecommendation
    index_recommendation = IndexRecommendation(
        table_name=recommendation["table_name"],
        column_names=recommendation["column_names"],
        index_type=IndexType[recommendation["index_type"]],
        estimated_improvement=recommendation.get("estimated_improvement", 0.0),
        rationale=recommendation.get("rationale", ""),
        priority=recommendation.get("priority", 0),
        creation_sql=recommendation.get("creation_sql")
    )
    
    result = await query_optimizer.apply_index_recommendation(index_recommendation)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return {"message": "Index recommendation applied successfully"}


@router.get("/optimize/metrics", response_model=Dict[str, Any])
async def get_optimizer_metrics(
    query_optimizer: QueryOptimizerServiceProtocol = Depends(get_query_optimizer)
) -> Dict[str, Any]:
    """
    Get optimizer metrics.
    
    Args:
        query_optimizer: Query optimizer service
        
    Returns:
        Optimizer metrics
    """
    result = await query_optimizer.get_optimizer_metrics()
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    metrics = result.value
    return {
        "timestamp": metrics.timestamp.isoformat(),
        "query_count": metrics.query_count,
        "slow_query_count": metrics.slow_query_count,
        "average_execution_time": metrics.average_execution_time,
        "max_execution_time": metrics.max_execution_time,
        "total_rows_processed": metrics.total_rows_processed,
        "index_recommendations": metrics.index_recommendations,
        "query_rewrites": metrics.query_rewrites
    }


# Query Cache Endpoints

@router.get("/cache/statistics", response_model=Dict[str, Any])
async def get_cache_statistics(
    query_cache: QueryCacheServiceProtocol = Depends(get_query_cache)
) -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Args:
        query_cache: Query cache service
        
    Returns:
        Cache statistics
    """
    result = await query_cache.get_cache_statistics()
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return result.value


@router.post("/cache/invalidate")
async def invalidate_cache(
    table_names: Optional[List[str]] = None,
    query_cache: QueryCacheServiceProtocol = Depends(get_query_cache)
) -> Dict[str, Any]:
    """
    Invalidate cache entries.
    
    Args:
        table_names: Optional list of tables to invalidate cache for
        query_cache: Query cache service
        
    Returns:
        Success message with the number of invalidated entries
    """
    result = await query_cache.invalidate_cache(table_names)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return {"message": f"Cache invalidated ({result.value} entries)"}


# Transaction Endpoints

@router.post("/transaction/begin", response_model=TransactionResponse)
async def begin_transaction(
    request: TransactionRequest,
    transaction_service: TransactionServiceProtocol = Depends(get_transaction)
) -> TransactionResponse:
    """
    Begin a new transaction.
    
    Args:
        request: Transaction request
        transaction_service: Transaction service
        
    Returns:
        Transaction response
    """
    result = await transaction_service.begin_transaction(request)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return result.value


@router.post("/transaction/{transaction_id}/commit", response_model=TransactionResponse)
async def commit_transaction(
    transaction_id: str,
    transaction_service: TransactionServiceProtocol = Depends(get_transaction)
) -> TransactionResponse:
    """
    Commit a transaction.
    
    Args:
        transaction_id: Transaction ID
        transaction_service: Transaction service
        
    Returns:
        Transaction response
    """
    result = await transaction_service.commit_transaction(TransactionId(transaction_id))
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return result.value


@router.post("/transaction/{transaction_id}/rollback", response_model=TransactionResponse)
async def rollback_transaction(
    transaction_id: str,
    transaction_service: TransactionServiceProtocol = Depends(get_transaction)
) -> TransactionResponse:
    """
    Rollback a transaction.
    
    Args:
        transaction_id: Transaction ID
        transaction_service: Transaction service
        
    Returns:
        Transaction response
    """
    result = await transaction_service.rollback_transaction(TransactionId(transaction_id))
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return result.value


# Connection Pool Endpoints

@router.get("/pool/statistics", response_model=Dict[str, Any])
async def get_pool_statistics(
    pool_service: ConnectionPoolServiceProtocol = Depends(get_connection_pool)
) -> Dict[str, Any]:
    """
    Get current pool statistics.
    
    Args:
        pool_service: Connection pool service
        
    Returns:
        Pool statistics
    """
    result = await pool_service.get_pool_statistics()
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    stats = result.value
    return {
        "pool_size": stats.pool_size,
        "active_connections": stats.active_connections,
        "idle_connections": stats.idle_connections,
        "max_overflow": stats.max_overflow,
        "overflow_count": stats.overflow_count,
        "checked_out": stats.checked_out,
        "checkins": stats.checkins,
        "checkouts": stats.checkouts,
        "connection_errors": stats.connection_errors,
        "timeout_errors": stats.timeout_errors,
        "utilization_rate": stats.utilization_rate,
        "is_under_pressure": stats.is_under_pressure,
        "timestamp": stats.timestamp.isoformat()
    }


@router.get("/pool/historical_statistics", response_model=List[Dict[str, Any]])
async def get_historical_pool_statistics(
    limit: int = Query(100, ge=1, le=1000),
    pool_service: ConnectionPoolServiceProtocol = Depends(get_connection_pool)
) -> List[Dict[str, Any]]:
    """
    Get historical pool statistics.
    
    Args:
        limit: Maximum number of statistics to return
        pool_service: Connection pool service
        
    Returns:
        List of historical pool statistics
    """
    result = await pool_service.get_historical_statistics(limit)
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    # Convert to dictionary for JSON serialization
    return [
        {
            "pool_size": stats.pool_size,
            "active_connections": stats.active_connections,
            "idle_connections": stats.idle_connections,
            "max_overflow": stats.max_overflow,
            "overflow_count": stats.overflow_count,
            "checked_out": stats.checked_out,
            "checkins": stats.checkins,
            "checkouts": stats.checkouts,
            "connection_errors": stats.connection_errors,
            "timeout_errors": stats.timeout_errors,
            "utilization_rate": stats.utilization_rate,
            "is_under_pressure": stats.is_under_pressure,
            "timestamp": stats.timestamp.isoformat()
        }
        for stats in result.value
    ]


@router.post("/pool/optimize")
async def optimize_pool_size(
    pool_service: ConnectionPoolServiceProtocol = Depends(get_connection_pool)
) -> Dict[str, Any]:
    """
    Optimize the connection pool size based on usage.
    
    Args:
        pool_service: Connection pool service
        
    Returns:
        Optimized pool configuration
    """
    result = await pool_service.optimize_pool_size()
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    config = result.value
    return {
        "strategy": config.strategy.name,
        "pool_size": config.pool_size,
        "max_overflow": config.max_overflow,
        "pool_timeout": config.pool_timeout,
        "pool_recycle": config.pool_recycle,
        "pool_pre_ping": config.pool_pre_ping,
        "max_idle_time": config.max_idle_time,
        "health_check_interval": config.health_check_interval
    }


@router.post("/pool/reset")
async def reset_pool(
    pool_service: ConnectionPoolServiceProtocol = Depends(get_connection_pool)
) -> Dict[str, Any]:
    """
    Reset the connection pool.
    
    Args:
        pool_service: Connection pool service
        
    Returns:
        Success message
    """
    result = await pool_service.reset_pool()
    
    if isinstance(result, Failure):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error.message
        )
    
    return {"message": "Connection pool has been reset"}