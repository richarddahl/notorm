"""Workers for processing jobs from the queue.

This package provides worker implementations for executing tasks,
handling results, and scaling job processing across multiple processes or machines.
"""

from uno.jobs.worker.base import Worker
from uno.jobs.worker.sync import SyncWorker
from uno.jobs.worker.thread import ThreadPoolWorker
from uno.jobs.worker.process import ProcessPoolWorker
from uno.jobs.worker.async_worker import AsyncWorker
from uno.jobs.worker.distributed import DistributedWorker
from uno.jobs.worker.pool import WorkerPool
from uno.jobs.worker.middleware import Middleware
from uno.jobs.worker.coordinator import WorkerCoordinator

__all__ = [
    "Worker",
    "SyncWorker",
    "ThreadPoolWorker",
    "ProcessPoolWorker",
    "AsyncWorker",
    "DistributedWorker",
    "WorkerPool",
    "Middleware",
    "WorkerCoordinator",
]
