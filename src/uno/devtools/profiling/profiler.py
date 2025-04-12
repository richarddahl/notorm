"""
Profiler for timing and analyzing function execution.

This module provides a profiler for measuring function execution time and
identifying performance bottlenecks.
"""

import time
import functools
import cProfile
import pstats
import io
import logging
import inspect
import os
from typing import Any, Dict, List, Optional, Set, Type, Union, Callable, TypeVar
from dataclasses import dataclass, field
from collections import defaultdict
from contextlib import contextmanager

try:
    import yappi
    YAPPI_AVAILABLE = True
except ImportError:
    YAPPI_AVAILABLE = False


logger = logging.getLogger("uno.profiler")


# Type variables for better typing support
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')


@dataclass
class ProfileResult:
    """Result of a profiling run."""
    
    name: str
    total_time: float
    ncalls: int = 1
    cumtime: float = 0.0
    percall: float = 0.0
    filename: Optional[str] = None
    lineno: Optional[int] = None
    function_type: str = "function"
    callers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    callees: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class Profiler:
    """Profiler for timing and analyzing function execution."""
    
    def __init__(
        self,
        detailed: bool = False,
        yappi: bool = False,
        builtins: bool = False,
        profile_memory: bool = False,
    ):
        """Initialize the profiler.
        
        Args:
            detailed: Whether to use cProfile for detailed profiling
            yappi: Whether to use yappi for multithreaded profiling
            builtins: Whether to profile Python builtins
            profile_memory: Whether to profile memory usage
        """
        self.detailed = detailed
        self.use_yappi = yappi and YAPPI_AVAILABLE
        self.builtins = builtins
        self.profile_memory = profile_memory
        
        self.profiler = None
        if self.detailed:
            self.profiler = cProfile.Profile()
        elif self.use_yappi:
            self.profiler = yappi
        
        self.results: Dict[str, ProfileResult] = {}
        self.current_run: Optional[str] = None
    
    def __call__(self, func: F) -> F:
        """Make the profiler callable as a decorator.
        
        Args:
            func: The function to profile
            
        Returns:
            The wrapped function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.run_profile(func.__qualname__, lambda: func(*args, **kwargs))
        
        return wrapper
    
    def run_profile(self, name: str, func: Callable[[], T]) -> T:
        """Run a profiling session.
        
        Args:
            name: Name for the profiling session
            func: Function to profile
            
        Returns:
            The result of the function
        """
        self.current_run = name
        
        if self.detailed:
            self.profiler.enable()
            try:
                start_time = time.time()
                result = func()
                end_time = time.time()
                
                # Store basic timing info
                self.results[name] = ProfileResult(
                    name=name,
                    total_time=end_time - start_time,
                )
                
                return result
            finally:
                self.profiler.disable()
                # Process detailed stats
                self._process_detailed_stats(name)
                self.current_run = None
        elif self.use_yappi:
            yappi.start(builtins=self.builtins)
            try:
                start_time = time.time()
                result = func()
                end_time = time.time()
                
                # Store basic timing info
                self.results[name] = ProfileResult(
                    name=name,
                    total_time=end_time - start_time,
                )
                
                return result
            finally:
                yappi.stop()
                # Process yappi stats
                self._process_yappi_stats(name)
                self.current_run = None
        else:
            # Simple timing with time.time()
            start_time = time.time()
            result = func()
            end_time = time.time()
            
            # Store basic timing info
            self.results[name] = ProfileResult(
                name=name,
                total_time=end_time - start_time,
            )
            
            return result
    
    def clear(self) -> None:
        """Clear all profiling results."""
        self.results = {}
        if self.detailed:
            self.profiler = cProfile.Profile()
        elif self.use_yappi:
            yappi.clear_stats()
    
    def print_stats(self, name: Optional[str] = None, top: int = 10) -> str:
        """Format and print profiling statistics.
        
        Args:
            name: Name of the profiling run to print stats for (None for all)
            top: Number of top functions to include
            
        Returns:
            Formatted statistics as a string
        """
        if name and name in self.results:
            stats = io.StringIO()
            stats.write(f"Profile results for: {name}\n")
            stats.write(f"Total time: {self.results[name].total_time:.6f}s\n")
            
            if hasattr(self.results[name], "stats"):
                stats.write("\nDetailed profile:\n")
                stats.write(self.results[name].stats)
            
            return stats.getvalue()
        elif name:
            return f"No profile results found for: {name}"
        else:
            # Print summary of all profiles
            stats = io.StringIO()
            stats.write("Profile summary:\n")
            
            # Sort by total time
            sorted_results = sorted(
                self.results.items(),
                key=lambda x: x[1].total_time,
                reverse=True
            )
            
            for name, result in sorted_results:
                stats.write(f"{name}: {result.total_time:.6f}s\n")
            
            # Include detailed stats for the slowest run
            if sorted_results and hasattr(sorted_results[0][1], "stats"):
                stats.write(f"\nDetailed profile for slowest run ({sorted_results[0][0]}):\n")
                stats.write(sorted_results[0][1].stats)
            
            return stats.getvalue()
    
    def get_stats(self, name: Optional[str] = None) -> Union[Dict[str, ProfileResult], Optional[ProfileResult]]:
        """Get profiling statistics.
        
        Args:
            name: Name of the profiling run to get stats for (None for all)
            
        Returns:
            Profile results for the requested run(s)
        """
        if name:
            return self.results.get(name)
        return self.results
    
    def _process_detailed_stats(self, name: str) -> None:
        """Process detailed profiling statistics from cProfile.
        
        Args:
            name: Name of the profiling run
        """
        if name not in self.results:
            return
        
        # Create a Stats object
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats("cumulative")
        ps.print_stats(20)  # Print top 20 functions
        
        # Store the detailed stats
        self.results[name].stats = s.getvalue()
        
        # Extract function-level stats
        function_stats = {}
        for func, (cc, nc, tt, ct, callers) in self.profiler.stats.items():
            function_name = f"{func[0]}:{func[1]}({func[2]})"
            function_stats[function_name] = {
                "ncalls": nc,
                "tottime": tt,
                "percall": tt / nc if nc > 0 else 0,
                "cumtime": ct,
                "filename": func[0],
                "lineno": func[1],
                "function": func[2],
                "callers": {
                    f"{caller[0]}:{caller[1]}({caller[2]})": {
                        "ncalls": stats[0],
                        "tottime": stats[1],
                        "cumtime": stats[2],
                    }
                    for caller, stats in callers.items()
                }
            }
        
        # Attach the function stats to the result
        self.results[name].function_stats = function_stats
    
    def _process_yappi_stats(self, name: str) -> None:
        """Process profiling statistics from yappi.
        
        Args:
            name: Name of the profiling run
        """
        if not self.use_yappi or name not in self.results:
            return
        
        # Create a Stats object
        s = io.StringIO()
        yappi.get_func_stats().print_all(out=s)
        
        # Store the detailed stats
        self.results[name].stats = s.getvalue()
        
        # Attach thread stats
        thread_s = io.StringIO()
        yappi.get_thread_stats().print_all(out=thread_s)
        self.results[name].thread_stats = thread_s.getvalue()
    
    @contextmanager
    def profile_block(self, name: str) -> None:
        """Context manager for profiling a block of code.
        
        Args:
            name: Name for the profiling session
        """
        self.current_run = name
        
        if self.detailed:
            self.profiler.enable()
            start_time = time.time()
            try:
                yield
            finally:
                end_time = time.time()
                self.profiler.disable()
                
                # Store basic timing info
                self.results[name] = ProfileResult(
                    name=name,
                    total_time=end_time - start_time,
                )
                
                # Process detailed stats
                self._process_detailed_stats(name)
                self.current_run = None
        elif self.use_yappi:
            yappi.start(builtins=self.builtins)
            start_time = time.time()
            try:
                yield
            finally:
                end_time = time.time()
                yappi.stop()
                
                # Store basic timing info
                self.results[name] = ProfileResult(
                    name=name,
                    total_time=end_time - start_time,
                )
                
                # Process yappi stats
                self._process_yappi_stats(name)
                self.current_run = None
        else:
            # Simple timing with time.time()
            start_time = time.time()
            try:
                yield
            finally:
                end_time = time.time()
                
                # Store basic timing info
                self.results[name] = ProfileResult(
                    name=name,
                    total_time=end_time - start_time,
                )
                
                self.current_run = None


# Global profiler instance
_profiler = Profiler()


def get_profiler() -> Profiler:
    """Get the global profiler instance.
    
    Returns:
        The global Profiler instance
    """
    return _profiler


def profile(
    func: Optional[F] = None,
    *,
    detailed: bool = False,
    yappi: bool = False,
    builtins: bool = False,
    profile_memory: bool = False,
) -> Union[F, Callable[[F], F]]:
    """Decorator for profiling functions.
    
    This can be used as:
    @profile
    def my_function():
        ...
    
    Or with parameters:
    @profile(detailed=True)
    def my_function():
        ...
    
    Args:
        func: The function to decorate (when used without arguments)
        detailed: Whether to use cProfile for detailed profiling
        yappi: Whether to use yappi for multithreaded profiling
        builtins: Whether to profile Python builtins
        profile_memory: Whether to profile memory usage
        
    Returns:
        The decorated function or a decorator function
    """
    def create_profiler(f: F) -> F:
        profiler = Profiler(
            detailed=detailed,
            yappi=yappi,
            builtins=builtins,
            profile_memory=profile_memory,
        )
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return profiler.run_profile(f.__qualname__, lambda: f(*args, **kwargs))
        
        # Attach the profiler to the function for retrieval
        wrapper._profiler = profiler
        
        return wrapper
    
    if func is None:
        return create_profiler
    
    return create_profiler(func)


@contextmanager
def profile_block(
    name: str,
    detailed: bool = False,
    yappi: bool = False,
    builtins: bool = False,
    profile_memory: bool = False,
) -> Profiler:
    """Context manager for profiling a block of code.
    
    Args:
        name: Name for the profiling session
        detailed: Whether to use cProfile for detailed profiling
        yappi: Whether to use yappi for multithreaded profiling
        builtins: Whether to profile Python builtins
        profile_memory: Whether to profile memory usage
        
    Returns:
        The profiler instance
    """
    profiler = Profiler(
        detailed=detailed,
        yappi=yappi,
        builtins=builtins,
        profile_memory=profile_memory,
    )
    
    with profiler.profile_block(name):
        yield profiler
    
    return profiler