# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Deployment pipeline.

This module provides a pipeline abstraction for orchestrating deployment tasks.
The pipeline consists of stages, which in turn consist of tasks to be executed.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any, Set, Union
from enum import Enum, auto


class TaskStatus(Enum):
    """Status of a task."""
    
    PENDING = auto()
    RUNNING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class Task:
    """
    A task to be executed in a deployment pipeline.
    
    Each task represents a single unit of work in the deployment process,
    such as running tests, building the application, or deploying to a platform.
    """
    
    name: str
    description: str
    action: Callable[[Dict[str, Any]], bool]
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    skip_on_failure: bool = False
    timeout: Optional[int] = None  # Timeout in seconds
    
    def run(self, context: Dict[str, Any], logger: logging.Logger) -> bool:
        """
        Run the task.
        
        Args:
            context: Context data shared between tasks
            logger: Logger instance
            
        Returns:
            True if the task succeeded, False otherwise
        """
        if self.status == TaskStatus.SKIPPED:
            logger.info(f"Task '{self.name}' skipped")
            return True
        
        logger.info(f"Starting task '{self.name}': {self.description}")
        self.status = TaskStatus.RUNNING
        start_time = time.time()
        
        try:
            # Run the task with timeout if specified
            if self.timeout:
                # Simple implementation of timeout (could be improved)
                original_time = time.time()
                result = self.action(context)
                if time.time() - original_time > self.timeout:
                    logger.error(f"Task '{self.name}' timed out after {self.timeout} seconds")
                    self.status = TaskStatus.FAILED
                    return False
            else:
                result = self.action(context)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result:
                logger.info(f"Task '{self.name}' succeeded in {duration:.2f} seconds")
                self.status = TaskStatus.SUCCEEDED
                return True
            else:
                logger.error(f"Task '{self.name}' failed after {duration:.2f} seconds")
                self.status = TaskStatus.FAILED
                return False
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.exception(f"Task '{self.name}' failed with exception after {duration:.2f} seconds: {str(e)}")
            self.status = TaskStatus.FAILED
            return False


@dataclass
class Stage:
    """
    A stage in a deployment pipeline.
    
    Each stage represents a phase in the deployment process, such as
    preparation, building, deployment, or verification.
    """
    
    name: str
    description: str
    tasks: List[Task] = field(default_factory=list)
    fail_fast: bool = True
    
    def add_task(self, task: Task) -> None:
        """
        Add a task to the stage.
        
        Args:
            task: The task to add
        """
        self.tasks.append(task)
    
    def run(self, context: Dict[str, Any], logger: logging.Logger) -> bool:
        """
        Run all tasks in the stage.
        
        Args:
            context: Context data shared between tasks
            logger: Logger instance
            
        Returns:
            True if all tasks succeeded, False otherwise
        """
        logger.info(f"Starting stage '{self.name}': {self.description}")
        start_time = time.time()
        
        success = True
        for task in self.tasks:
            task_success = task.run(context, logger)
            
            if not task_success:
                success = False
                if self.fail_fast:
                    logger.error(f"Stage '{self.name}' failed due to task '{task.name}'")
                    break
        
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            logger.info(f"Stage '{self.name}' completed successfully in {duration:.2f} seconds")
        else:
            logger.error(f"Stage '{self.name}' failed after {duration:.2f} seconds")
        
        return success


class Pipeline:
    """
    A deployment pipeline.
    
    The pipeline is responsible for executing a series of stages and tasks
    to deploy an application.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a deployment pipeline.
        
        Args:
            name: Pipeline name
            description: Pipeline description
            logger: Logger instance (creates a new one if not provided)
        """
        self.name = name
        self.description = description
        self.logger = logger or self._create_logger()
        self.stages: List[Stage] = []
        self.context: Dict[str, Any] = {}
    
    def _create_logger(self) -> logging.Logger:
        """Create a logger for the pipeline."""
        logger = logging.getLogger(f"uno.pipeline.{self.name}")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def add_stage(self, stage: Stage) -> None:
        """
        Add a stage to the pipeline.
        
        Args:
            stage: The stage to add
        """
        self.stages.append(stage)
    
    def run(self) -> bool:
        """
        Run the pipeline.
        
        Returns:
            True if all stages succeeded, False otherwise
        """
        self.logger.info(f"Starting pipeline '{self.name}': {self.description}")
        start_time = time.time()
        
        success = True
        for stage in self.stages:
            stage_success = stage.run(self.context, self.logger)
            if not stage_success:
                success = False
                self.logger.error(f"Pipeline '{self.name}' failed due to stage '{stage.name}'")
                break
        
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            self.logger.info(f"Pipeline '{self.name}' completed successfully in {duration:.2f} seconds")
        else:
            self.logger.error(f"Pipeline '{self.name}' failed after {duration:.2f} seconds")
        
        return success
    
    def get_status(self) -> Dict[str, Dict[str, TaskStatus]]:
        """
        Get the status of all tasks in the pipeline.
        
        Returns:
            A dictionary mapping stage names to dictionaries mapping task names to task statuses
        """
        status = {}
        for stage in self.stages:
            stage_status = {}
            for task in stage.tasks:
                stage_status[task.name] = task.status
            status[stage.name] = stage_status
        
        return status