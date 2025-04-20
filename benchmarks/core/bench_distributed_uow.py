"""
Distributed Unit of Work Benchmarks

This module contains benchmarks for the distributed unit of work implementation.
It measures performance of distributed transactions with varying numbers of participants.
"""

import asyncio
import uuid
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from benchmarks.core.benchmark_runner import Benchmark, register_benchmark

# Import required UNO components
from uno.core.uow import DistributedUnitOfWork, TransactionParticipant
from uno.core.errors import Result, Error


# Mock participant for benchmarking
class MockParticipant(TransactionParticipant):
    """Mock participant for benchmarking."""

    def __init__(
        self,
        name: str,
        prepare_latency: float = 0.001,
        commit_latency: float = 0.001,
        rollback_latency: float = 0.001,
        prepare_success_rate: float = 0.99,
        commit_success_rate: float = 0.99,
    ):
        """
        Initialize the mock participant.

        Args:
            name: Participant name
            prepare_latency: Simulated prepare latency in seconds
            commit_latency: Simulated commit latency in seconds
            rollback_latency: Simulated rollback latency in seconds
            prepare_success_rate: Probability of prepare success
            commit_success_rate: Probability of commit success
        """
        self.name = name
        self.prepare_latency = prepare_latency
        self.commit_latency = commit_latency
        self.rollback_latency = rollback_latency
        self.prepare_success_rate = prepare_success_rate
        self.commit_success_rate = commit_success_rate
        self.prepared_transactions: dict[str, bool] = {}

    async def prepare(self, transaction_id: str) -> Result[bool, Error]:
        """Prepare for a transaction."""
        # Simulate latency
        await asyncio.sleep(self.prepare_latency)

        # Simulate random failures
        if random.random() > self.prepare_success_rate:
            return Result.err(
                Error(
                    message=f"Simulated prepare failure for participant {self.name}",
                    error_code="PREPARE_FAILED",
                )
            )

        # Mark as prepared
        self.prepared_transactions[transaction_id] = True
        return Result.ok(True)

    async def commit(self, transaction_id: str) -> Result[bool, Error]:
        """Commit the transaction."""
        # Check if prepared
        if transaction_id not in self.prepared_transactions:
            return Result.err(
                Error(
                    message=f"Transaction {transaction_id} not prepared for participant {self.name}",
                    error_code="NOT_PREPARED",
                )
            )

        # Simulate latency
        await asyncio.sleep(self.commit_latency)

        # Simulate random failures
        if random.random() > self.commit_success_rate:
            return Result.err(
                Error(
                    message=f"Simulated commit failure for participant {self.name}",
                    error_code="COMMIT_FAILED",
                )
            )

        # Remove from prepared
        del self.prepared_transactions[transaction_id]
        return Result.ok(True)

    async def rollback(self, transaction_id: str) -> Result[bool, Error]:
        """Rollback the transaction."""
        # Check if prepared
        if transaction_id not in self.prepared_transactions:
            return Result.err(
                Error(
                    message=f"Transaction {transaction_id} not prepared for participant {self.name}",
                    error_code="NOT_PREPARED",
                )
            )

        # Simulate latency
        await asyncio.sleep(self.rollback_latency)

        # Remove from prepared
        del self.prepared_transactions[transaction_id]
        return Result.ok(True)


@register_benchmark
class DistributedUowSmallBenchmark(Benchmark):
    """Benchmark for distributed unit of work with a small number of participants."""

    category = "uow"
    name = "distributed_uow_small"
    description = (
        "Measures the performance of distributed unit of work with 3 participants"
    )
    tags = ["uow", "distributed", "core"]

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Create participants
        self.participants = [
            MockParticipant(
                name=f"participant_{i}",
                prepare_latency=0.001,
                commit_latency=0.001,
                rollback_latency=0.001,
                prepare_success_rate=0.99,
                commit_success_rate=0.99,
            )
            for i in range(3)
        ]

    async def run_iteration(self) -> dict[str, Any]:
        """Run a single benchmark iteration."""
        # Create a distributed UoW
        uow = DistributedUnitOfWork()

        # Register participants
        participant_ids = []
        for participant in self.participants:
            participant_id = uow.register_participant(participant.name, participant)
            participant_ids.append(participant_id)

        # Execute the transaction
        start_time = asyncio.get_event_loop().time()
        success = True
        try:
            async with uow:
                # Simulate some work
                await asyncio.sleep(0.001)
        except Exception:
            success = False

        end_time = asyncio.get_event_loop().time()

        # Get transaction status
        status = uow.get_transaction_status()

        # Return metrics
        return {
            "transaction_success": success,
            "transaction_duration": (end_time - start_time),
            "participant_count": len(participant_ids),
            "transaction_status": status["status"],
            "prepared_count": status["prepared_count"],
            "committed_count": status["committed_count"],
        }


@register_benchmark
class DistributedUowMediumBenchmark(Benchmark):
    """Benchmark for distributed unit of work with a medium number of participants."""

    category = "uow"
    name = "distributed_uow_medium"
    description = (
        "Measures the performance of distributed unit of work with 10 participants"
    )
    tags = ["uow", "distributed", "core"]

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Create participants
        self.participants = [
            MockParticipant(
                name=f"participant_{i}",
                prepare_latency=0.001,
                commit_latency=0.001,
                rollback_latency=0.001,
                prepare_success_rate=0.99,
                commit_success_rate=0.99,
            )
            for i in range(10)
        ]

    async def run_iteration(self) -> dict[str, Any]:
        """Run a single benchmark iteration."""
        # Create a distributed UoW
        uow = DistributedUnitOfWork()

        # Register participants
        participant_ids = []
        for participant in self.participants:
            participant_id = uow.register_participant(participant.name, participant)
            participant_ids.append(participant_id)

        # Execute the transaction
        start_time = asyncio.get_event_loop().time()
        success = True
        try:
            async with uow:
                # Simulate some work
                await asyncio.sleep(0.001)
        except Exception:
            success = False

        end_time = asyncio.get_event_loop().time()

        # Get transaction status
        status = uow.get_transaction_status()

        # Return metrics
        return {
            "transaction_success": success,
            "transaction_duration": (end_time - start_time),
            "participant_count": len(participant_ids),
            "transaction_status": status["status"],
            "prepared_count": status["prepared_count"],
            "committed_count": status["committed_count"],
        }


@register_benchmark
class DistributedUowFailureBenchmark(Benchmark):
    """Benchmark for distributed unit of work with participant failures."""

    category = "uow"
    name = "distributed_uow_failure"
    description = (
        "Measures the performance of distributed unit of work with participant failures"
    )
    tags = ["uow", "distributed", "core"]

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Create reliable participants
        self.reliable_participants = [
            MockParticipant(
                name=f"reliable_{i}",
                prepare_latency=0.001,
                commit_latency=0.001,
                rollback_latency=0.001,
                prepare_success_rate=0.99,
                commit_success_rate=0.99,
            )
            for i in range(3)
        ]

        # Create unreliable participants
        self.unreliable_participants = [
            MockParticipant(
                name=f"unreliable_{i}",
                prepare_latency=0.002,
                commit_latency=0.002,
                rollback_latency=0.001,
                prepare_success_rate=0.5,  # 50% prepare failure
                commit_success_rate=0.7,  # 30% commit failure
            )
            for i in range(2)
        ]

        # Combine all participants
        self.participants = self.reliable_participants + self.unreliable_participants

    async def run_iteration(self) -> dict[str, Any]:
        """Run a single benchmark iteration."""
        # Create a distributed UoW
        uow = DistributedUnitOfWork()

        # Register participants
        participant_ids = []
        for participant in self.participants:
            participant_id = uow.register_participant(participant.name, participant)
            participant_ids.append(participant_id)

        # Execute the transaction
        start_time = asyncio.get_event_loop().time()
        success = True
        try:
            async with uow:
                # Simulate some work
                await asyncio.sleep(0.001)
        except Exception:
            success = False

        end_time = asyncio.get_event_loop().time()

        # Get transaction status
        status = uow.get_transaction_status()

        # Return metrics
        return {
            "transaction_success": success,
            "transaction_duration": (end_time - start_time),
            "participant_count": len(participant_ids),
            "transaction_status": status["status"],
            "prepared_count": status["prepared_count"],
            "committed_count": status["committed_count"],
            "rolled_back_count": status["rolled_back_count"],
        }


@register_benchmark
class DistributedUowParallelBenchmark(Benchmark):
    """Benchmark for parallel distributed unit of work transactions."""

    category = "uow"
    name = "distributed_uow_parallel"
    description = (
        "Measures the performance of multiple parallel distributed transactions"
    )
    tags = ["uow", "distributed", "concurrency", "core"]

    async def setup(self) -> None:
        """Set up the benchmark environment."""
        # Define the number of parallel transactions
        self.num_transactions = 5

        # Create participants (each transaction has its own set)
        self.participant_sets = [
            [
                MockParticipant(
                    name=f"tx{tx}_participant_{i}",
                    prepare_latency=0.001,
                    commit_latency=0.001,
                    rollback_latency=0.001,
                    prepare_success_rate=0.95,
                    commit_success_rate=0.95,
                )
                for i in range(3)
            ]
            for tx in range(self.num_transactions)
        ]

    async def run_transaction(self, tx_id: int) -> dict[str, Any]:
        """
        Run a single distributed transaction.

        Args:
            tx_id: Transaction identifier

        Returns:
            Transaction metrics
        """
        # Get participants for this transaction
        participants = self.participant_sets[tx_id]

        # Create a distributed UoW
        uow = DistributedUnitOfWork()

        # Register participants
        participant_ids = []
        for participant in participants:
            participant_id = uow.register_participant(participant.name, participant)
            participant_ids.append(participant_id)

        # Execute the transaction
        start_time = asyncio.get_event_loop().time()
        success = True
        try:
            async with uow:
                # Simulate some work
                await asyncio.sleep(0.001)
        except Exception:
            success = False

        end_time = asyncio.get_event_loop().time()

        # Get transaction status
        status = uow.get_transaction_status()

        return {
            "tx_id": tx_id,
            "transaction_success": success,
            "transaction_duration": (end_time - start_time),
            "participant_count": len(participant_ids),
            "transaction_status": status["status"],
            "prepared_count": status["prepared_count"],
            "committed_count": status["committed_count"],
        }

    async def run_iteration(self) -> dict[str, Any]:
        """Run a single benchmark iteration."""
        # Create tasks for parallel transactions
        tasks = [self.run_transaction(tx_id) for tx_id in range(self.num_transactions)]

        # Execute all transactions in parallel
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        # Calculate success rate
        success_count = sum(1 for r in results if r["transaction_success"])
        success_rate = success_count / len(results)

        # Calculate average transaction duration
        avg_duration = sum(r["transaction_duration"] for r in results) / len(results)

        # Return metrics
        return {
            "total_transactions": len(results),
            "successful_transactions": success_count,
            "success_rate": success_rate,
            "total_duration": (end_time - start_time),
            "avg_transaction_duration": avg_duration,
            "max_transaction_duration": max(r["transaction_duration"] for r in results),
            "min_transaction_duration": min(r["transaction_duration"] for r in results),
        }
