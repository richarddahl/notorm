"""Workflow composition for tasks in the background processing system.

This module provides functions for composing tasks into workflows like
chains and groups.
"""

from typing import Any, Dict, List, Optional, Sequence, Union, cast


def chain(*tasks: Union[Dict[str, Any], Sequence[Dict[str, Any]]]) -> Dict[str, Any]:
    """Create a chain of tasks to be executed sequentially.
    
    This function creates a workflow where tasks are executed in sequence,
    with the result of each task passed as the first argument to the next task.
    
    Args:
        *tasks: Task signatures to be executed in sequence
        
    Returns:
        Chain workflow signature
        
    Raises:
        ValueError: If no tasks are provided
    """
    # Flatten task list (handle nested sequences)
    flat_tasks = []
    for task in tasks:
        if isinstance(task, dict) and "task" in task:
            flat_tasks.append(task)
        elif isinstance(task, (list, tuple)):
            flat_tasks.extend(task)
        else:
            raise ValueError(f"Invalid task specification: {task}")
    
    if not flat_tasks:
        raise ValueError("No tasks provided for chain")
    
    return {
        "task": "uno.jobs.workflows.chain",
        "args": [],
        "kwargs": {
            "tasks": flat_tasks
        }
    }


def group(tasks: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a group of tasks to be executed in parallel.
    
    This function creates a workflow where tasks are executed concurrently,
    and the results are collected into a list.
    
    Args:
        tasks: Sequence of task signatures to be executed in parallel
        
    Returns:
        Group workflow signature
        
    Raises:
        ValueError: If no tasks are provided
    """
    if not tasks:
        raise ValueError("No tasks provided for group")
    
    return {
        "task": "uno.jobs.workflows.group",
        "args": [],
        "kwargs": {
            "tasks": list(tasks)
        }
    }