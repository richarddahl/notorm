"""
Performance hotspot detection and analysis.

This module provides utilities for finding and analyzing performance hotspots
in Uno applications.
"""

import inspect
import time
import cProfile
import pstats
import io
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, Callable, TypeVar
from types import ModuleType
import sys

from uno.devtools.profiling.profiler import Profiler, profile


logger = logging.getLogger("uno.profiler.hotspot")


def find_hotspots(
    module: ModuleType,
    depth: int = 10,
    min_percent: float = 1.0,
    exclude_builtins: bool = True,
) -> List[Tuple[str, Dict[str, Any]]]:
    """Find performance hotspots in a module.
    
    Args:
        module: Module to analyze
        depth: Maximum callstack depth to analyze
        min_percent: Minimum percentage of total time to include
        exclude_builtins: Whether to exclude Python builtins
        
    Returns:
        List of (function_name, stats) tuples for hotspots
    """
    # Create profiler
    profiler = Profiler(detailed=True)
    
    # Find all functions in the module
    functions = []
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and obj.__module__ == module.__name__:
            functions.append((name, obj))
    
    # Also handle classes
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                if not method_name.startswith("__"):
                    functions.append((f"{name}.{method_name}", method))
    
    if not functions:
        logger.warning(f"No functions found in module {module.__name__}")
        return []
    
    # Profile each function
    logger.info(f"Profiling {len(functions)} functions in {module.__name__}")
    
    # Use cProfile directly for more detailed stats
    pr = cProfile.Profile()
    pr.enable()
    
    try:
        # Import all submodules to make sure they're available
        for finder, name, ispkg in pkgutil.iter_modules(module.__path__, module.__name__ + "."):
            __import__(name)
    except (AttributeError, NameError):
        pass
    
    # Call common module entry points if they exist
    for entry_point in ["main", "run", "app", "start", "init"]:
        if hasattr(module, entry_point) and callable(getattr(module, entry_point)):
            try:
                getattr(module, entry_point)()
            except Exception:
                pass
    
    pr.disable()
    
    # Process results
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(depth)
    
    # Parse stats output
    lines = s.getvalue().splitlines()
    
    # Find the separator line
    sep_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("   ncalls  tottime  percall  cumtime  percall filename:lineno(function)"):
            sep_idx = i
            break
    
    if sep_idx == -1:
        logger.warning("Could not parse profiler output")
        return []
    
    # Parse function stats
    hotspots = []
    total_time = 0.0
    
    for line in lines[sep_idx+2:]:
        if not line.strip():
            break
            
        parts = line.strip().split()
        if len(parts) < 6:
            continue
            
        # Extract basic stats
        if "/" in parts[0]:
            # Format: "n/m" where n is primitive calls and m is total calls
            calls = int(parts[0].split("/")[1])
        else:
            calls = int(parts[0])
            
        tottime = float(parts[1])
        cumtime = float(parts[3])
        
        # Extract function name
        func_parts = " ".join(parts[5:]).split(":")
        if len(func_parts) != 2:
            continue
            
        filename, funcname = func_parts
        funcname = funcname.strip("()")
        
        # Skip builtins if requested
        if exclude_builtins and (
            "<built-in>" in filename or 
            filename.startswith(sys.prefix) or
            filename.startswith(os.path.join(sys.prefix, "lib"))
        ):
            continue
            
        total_time += tottime
        
        # Add to hotspots
        hotspots.append((
            filename + ":" + funcname,
            {
                "ncalls": calls,
                "total_time": tottime,
                "cum_time": cumtime,
                "time_per_call": tottime / calls if calls else 0,
                "filename": filename,
                "function": funcname,
            }
        ))
    
    # Filter and sort hotspots
    if total_time > 0:
        filtered_hotspots = []
        for func_name, stats in hotspots:
            percent = (stats["total_time"] / total_time) * 100
            if percent >= min_percent:
                stats["percent"] = percent
                filtered_hotspots.append((func_name, stats))
        
        # Sort by total time
        filtered_hotspots.sort(key=lambda x: x[1]["total_time"], reverse=True)
        
        return filtered_hotspots
    
    return []


def analyze_performance(
    func: Callable,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """Analyze the performance of a function.
    
    Args:
        func: Function to analyze
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Dictionary with performance metrics
    """
    # Create profiler
    profiler = Profiler(detailed=True)
    
    # Profile the function
    logger.info(f"Profiling {func.__qualname__}")
    result = profiler.run_profile(func.__qualname__, lambda: func(*args, **kwargs))
    
    # Get profile stats
    profile_result = profiler.get_stats(func.__qualname__)
    if not profile_result:
        logger.warning(f"No profile results for {func.__qualname__}")
        return {}
    
    # Process function stats
    if not hasattr(profile_result, "function_stats"):
        logger.warning(f"No detailed stats available for {func.__qualname__}")
        return {
            "name": profile_result.name,
            "total_time": profile_result.total_time,
        }
    
    # Calculate performance metrics
    metrics = {
        "name": profile_result.name,
        "total_time": profile_result.total_time,
    }
    
    # Find bottlenecks
    if hasattr(profile_result, "function_stats"):
        bottlenecks = []
        for func_name, stats in sorted(
            profile_result.function_stats.items(),
            key=lambda x: x[1]["tottime"],
            reverse=True
        )[:10]:
            bottlenecks.append({
                "name": func_name,
                "total_time": stats["tottime"],
                "cumulative_time": stats["cumtime"],
                "calls": stats["ncalls"],
                "time_per_call": stats["tottime"] / stats["ncalls"] if stats["ncalls"] > 0 else 0,
            })
        
        metrics["bottlenecks"] = bottlenecks
    
    return metrics


# Import pkgutil late to avoid circular import
import pkgutil