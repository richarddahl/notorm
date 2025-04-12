"""
Memory profiling utilities for Uno applications.

This module provides tools for tracking and analyzing memory usage in Uno applications.
"""

import time
import functools
import gc
import logging
import inspect
import os
import sys
from typing import Any, Dict, List, Optional, Set, Type, Union, Callable, TypeVar
from dataclasses import dataclass, field
from contextlib import contextmanager

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import pympler.asizeof
    PYMPLER_AVAILABLE = True
except ImportError:
    PYMPLER_AVAILABLE = False

try:
    import tracemalloc
    TRACEMALLOC_AVAILABLE = True
except ImportError:
    TRACEMALLOC_AVAILABLE = False


logger = logging.getLogger("uno.memory_profiler")


# Type variables for better typing support
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage."""
    
    timestamp: float = 0.0
    rss: Optional[int] = None  # Resident Set Size
    vms: Optional[int] = None  # Virtual Memory Size
    python_total: Optional[int] = None  # Total Python memory usage
    gc_objects: Optional[Dict[str, int]] = None  # Object counts from gc
    tracemalloc_snapshot: Optional[Any] = None  # tracemalloc snapshot
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert the snapshot to a dictionary.
        
        Returns:
            Dictionary representation of the snapshot
        """
        result = {
            "timestamp": self.timestamp,
            "rss": self.rss,
            "vms": self.vms,
            "python_total": self.python_total,
        }
        
        if self.gc_objects:
            result["gc_objects"] = self.gc_objects
        
        return result


@dataclass
class MemoryProfileResult:
    """Result of a memory profiling run."""
    
    name: str
    start_snapshot: MemorySnapshot
    end_snapshot: MemorySnapshot
    delta: Dict[str, Any] = field(default_factory=dict)
    peak: Optional[MemorySnapshot] = None
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    tracked_objects: Dict[str, Any] = field(default_factory=dict)


class MemoryProfiler:
    """Profiler for tracking memory usage in functions and applications."""
    
    def __init__(
        self,
        detailed: bool = False,
        track_gc_objects: bool = False,
        use_tracemalloc: bool = False,
        interval: float = 0.0,
    ):
        """Initialize the memory profiler.
        
        Args:
            detailed: Whether to collect detailed memory information
            track_gc_objects: Whether to track garbage collector objects
            use_tracemalloc: Whether to use tracemalloc for detailed memory tracking
            interval: Interval in seconds between snapshots (0 for start/end only)
        """
        self.detailed = detailed
        self.track_gc_objects = track_gc_objects
        self.use_tracemalloc = use_tracemalloc and TRACEMALLOC_AVAILABLE
        self.interval = interval
        
        self.results: Dict[str, MemoryProfileResult] = {}
        self.current_run: Optional[str] = None
        self.tracking_thread = None
        
        # Start tracemalloc if requested
        if self.use_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()
    
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
        """Run a memory profiling session.
        
        Args:
            name: Name for the profiling session
            func: Function to profile
            
        Returns:
            The result of the function
        """
        self.current_run = name
        
        # Take initial snapshot
        start_snapshot = self._take_snapshot()
        
        # Start interval tracking if requested
        if self.interval > 0:
            self._start_interval_tracking(name)
        
        try:
            # Run the function
            result = func()
            return result
        finally:
            # Take final snapshot
            end_snapshot = self._take_snapshot()
            
            # Stop interval tracking
            if self.interval > 0:
                self._stop_interval_tracking()
            
            # Calculate delta
            delta = self._calculate_delta(start_snapshot, end_snapshot)
            
            # Find peak memory usage
            peak = None
            snapshots = []
            
            # Store the result
            self.results[name] = MemoryProfileResult(
                name=name,
                start_snapshot=start_snapshot,
                end_snapshot=end_snapshot,
                delta=delta,
                peak=peak,
                snapshots=snapshots,
            )
            
            self.current_run = None
    
    def _take_snapshot(self) -> MemorySnapshot:
        """Take a snapshot of current memory usage.
        
        Returns:
            Memory usage snapshot
        """
        snapshot = MemorySnapshot(timestamp=time.time())
        
        # Get process memory usage
        if PSUTIL_AVAILABLE:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            snapshot.rss = mem_info.rss
            snapshot.vms = mem_info.vms
        
        # Get Python memory usage
        if self.detailed and PYMPLER_AVAILABLE:
            snapshot.python_total = pympler.asizeof.asizeof(sys.modules)
        
        # Get garbage collector objects
        if self.track_gc_objects:
            gc_objects = {}
            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                gc_objects[obj_type] = gc_objects.get(obj_type, 0) + 1
            snapshot.gc_objects = gc_objects
        
        # Get tracemalloc snapshot
        if self.use_tracemalloc:
            snapshot.tracemalloc_snapshot = tracemalloc.take_snapshot()
        
        return snapshot
    
    def _calculate_delta(self, start: MemorySnapshot, end: MemorySnapshot) -> Dict[str, Any]:
        """Calculate the difference between two memory snapshots.
        
        Args:
            start: Starting memory snapshot
            end: Ending memory snapshot
            
        Returns:
            Dictionary with memory usage differences
        """
        delta = {}
        
        if start.rss is not None and end.rss is not None:
            delta["rss"] = end.rss - start.rss
        
        if start.vms is not None and end.vms is not None:
            delta["vms"] = end.vms - start.vms
        
        if start.python_total is not None and end.python_total is not None:
            delta["python_total"] = end.python_total - start.python_total
        
        # Calculate GC object differences
        if start.gc_objects and end.gc_objects:
            gc_delta = {}
            all_types = set(list(start.gc_objects.keys()) + list(end.gc_objects.keys()))
            
            for obj_type in all_types:
                start_count = start.gc_objects.get(obj_type, 0)
                end_count = end.gc_objects.get(obj_type, 0)
                if start_count != end_count:
                    gc_delta[obj_type] = end_count - start_count
            
            delta["gc_objects"] = gc_delta
        
        # Calculate tracemalloc differences
        if self.use_tracemalloc and start.tracemalloc_snapshot and end.tracemalloc_snapshot:
            try:
                stats = end.tracemalloc_snapshot.compare_to(start.tracemalloc_snapshot, 'lineno')
                tracemalloc_delta = []
                
                for stat in stats[:10]:  # Top 10 differences
                    frame = stat.traceback[0]
                    tracemalloc_delta.append({
                        "file": frame.filename,
                        "line": frame.lineno,
                        "size": stat.size,
                        "count": stat.count,
                    })
                
                delta["tracemalloc"] = tracemalloc_delta
            except Exception as e:
                logger.error(f"Error calculating tracemalloc delta: {str(e)}")
        
        return delta
    
    def _start_interval_tracking(self, name: str) -> None:
        """Start taking memory snapshots at regular intervals.
        
        Args:
            name: Name of the profiling session
        """
        import threading
        
        def _take_snapshots():
            snapshots = []
            peak_rss = 0
            peak_snapshot = None
            
            while getattr(self.tracking_thread, "running", True):
                snapshot = self._take_snapshot()
                snapshots.append(snapshot)
                
                # Check if this is the peak
                if snapshot.rss and snapshot.rss > peak_rss:
                    peak_rss = snapshot.rss
                    peak_snapshot = snapshot
                
                # Store in the current result if available
                if name in self.results:
                    self.results[name].snapshots = list(snapshots)
                    self.results[name].peak = peak_snapshot
                
                time.sleep(self.interval)
        
        self.tracking_thread = threading.Thread(target=_take_snapshots)
        self.tracking_thread.running = True
        self.tracking_thread.daemon = True
        self.tracking_thread.start()
    
    def _stop_interval_tracking(self) -> None:
        """Stop the interval tracking thread."""
        if self.tracking_thread:
            self.tracking_thread.running = False
            self.tracking_thread.join(timeout=1.0)
            self.tracking_thread = None
    
    def clear(self) -> None:
        """Clear all profiling results."""
        self.results = {}
    
    def print_stats(self, name: Optional[str] = None) -> str:
        """Format and print memory profiling statistics.
        
        Args:
            name: Name of the profiling run to print stats for (None for all)
            
        Returns:
            Formatted statistics as a string
        """
        from io import StringIO
        
        def _format_bytes(num_bytes: Optional[int]) -> str:
            """Format bytes as human-readable string."""
            if num_bytes is None:
                return "N/A"
            
            for unit in ['B', 'KB', 'MB', 'GB']:
                if abs(num_bytes) < 1024.0 or unit == 'GB':
                    return f"{num_bytes:.2f} {unit}"
                num_bytes /= 1024.0
            
            return f"{num_bytes:.2f} GB"
        
        output = StringIO()
        
        if name and name in self.results:
            result = self.results[name]
            output.write(f"Memory profile for: {name}\n")
            output.write(f"RSS: {_format_bytes(result.start_snapshot.rss)} -> {_format_bytes(result.end_snapshot.rss)} ")
            if "rss" in result.delta:
                output.write(f"(Δ {_format_bytes(result.delta['rss'])})\n")
            else:
                output.write("\n")
            
            output.write(f"VMS: {_format_bytes(result.start_snapshot.vms)} -> {_format_bytes(result.end_snapshot.vms)} ")
            if "vms" in result.delta:
                output.write(f"(Δ {_format_bytes(result.delta['vms'])})\n")
            else:
                output.write("\n")
            
            if result.start_snapshot.python_total is not None:
                output.write(f"Python memory: {_format_bytes(result.start_snapshot.python_total)} -> {_format_bytes(result.end_snapshot.python_total)} ")
                if "python_total" in result.delta:
                    output.write(f"(Δ {_format_bytes(result.delta['python_total'])})\n")
                else:
                    output.write("\n")
            
            # Print peak memory if available
            if result.peak:
                output.write(f"Peak RSS: {_format_bytes(result.peak.rss)}\n")
            
            # Print GC object changes
            if "gc_objects" in result.delta:
                output.write("\nGC Object Changes:\n")
                sorted_changes = sorted(
                    result.delta["gc_objects"].items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )
                for obj_type, count in sorted_changes[:20]:  # Top 20 changes
                    output.write(f"  {obj_type}: {'+' if count > 0 else ''}{count}\n")
            
            # Print tracemalloc changes
            if "tracemalloc" in result.delta:
                output.write("\nMemory Allocation Changes (tracemalloc):\n")
                for item in result.delta["tracemalloc"]:
                    output.write(f"  {item['file']}:{item['line']} - {_format_bytes(item['size'])} ({item['count']} objects)\n")
        elif name:
            output.write(f"No memory profile found for: {name}")
        else:
            # Print summary of all profiles
            output.write("Memory profile summary:\n")
            
            for result_name, result in sorted(self.results.items()):
                output.write(f"{result_name}:\n")
                output.write(f"  RSS change: {_format_bytes(result.delta.get('rss', 0))}\n")
                if result.peak:
                    output.write(f"  Peak RSS: {_format_bytes(result.peak.rss)}\n")
        
        return output.getvalue()
    
    def get_stats(self, name: Optional[str] = None) -> Union[Dict[str, MemoryProfileResult], Optional[MemoryProfileResult]]:
        """Get memory profiling statistics.
        
        Args:
            name: Name of the profiling run to get stats for (None for all)
            
        Returns:
            Profile results for the requested run(s)
        """
        if name:
            return self.results.get(name)
        return self.results
    
    @contextmanager
    def profile_block(self, name: str) -> None:
        """Context manager for profiling a block of code.
        
        Args:
            name: Name for the profiling session
        """
        self.current_run = name
        
        # Take initial snapshot
        start_snapshot = self._take_snapshot()
        
        # Start interval tracking if requested
        if self.interval > 0:
            self._start_interval_tracking(name)
        
        try:
            yield
        finally:
            # Take final snapshot
            end_snapshot = self._take_snapshot()
            
            # Stop interval tracking
            if self.interval > 0:
                self._stop_interval_tracking()
            
            # Calculate delta
            delta = self._calculate_delta(start_snapshot, end_snapshot)
            
            # Find peak memory usage
            peak = None
            snapshots = []
            
            # Store the result
            self.results[name] = MemoryProfileResult(
                name=name,
                start_snapshot=start_snapshot,
                end_snapshot=end_snapshot,
                delta=delta,
                peak=peak,
                snapshots=snapshots,
            )
            
            self.current_run = None


# Global memory profiler instance
_memory_profiler = MemoryProfiler()


def get_memory_profiler() -> MemoryProfiler:
    """Get the global memory profiler instance.
    
    Returns:
        The global MemoryProfiler instance
    """
    return _memory_profiler


def memory_profile(
    func: Optional[F] = None,
    *,
    detailed: bool = False,
    track_gc_objects: bool = False,
    use_tracemalloc: bool = False,
    interval: float = 0.0,
) -> Union[F, Callable[[F], F]]:
    """Decorator for profiling function memory usage.
    
    This can be used as:
    @memory_profile
    def my_function():
        ...
    
    Or with parameters:
    @memory_profile(detailed=True)
    def my_function():
        ...
    
    Args:
        func: The function to decorate (when used without arguments)
        detailed: Whether to collect detailed memory information
        track_gc_objects: Whether to track garbage collector objects
        use_tracemalloc: Whether to use tracemalloc for detailed memory tracking
        interval: Interval in seconds between snapshots (0 for start/end only)
        
    Returns:
        The decorated function or a decorator function
    """
    def create_profiler(f: F) -> F:
        profiler = MemoryProfiler(
            detailed=detailed,
            track_gc_objects=track_gc_objects,
            use_tracemalloc=use_tracemalloc,
            interval=interval,
        )
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return profiler.run_profile(f.__qualname__, lambda: f(*args, **kwargs))
        
        # Attach the profiler to the function for retrieval
        wrapper._memory_profiler = profiler
        
        return wrapper
    
    if func is None:
        return create_profiler
    
    return create_profiler(func)


@contextmanager
def memory_profile_block(
    name: str,
    detailed: bool = False,
    track_gc_objects: bool = False,
    use_tracemalloc: bool = False,
    interval: float = 0.0,
) -> MemoryProfiler:
    """Context manager for profiling memory usage in a block of code.
    
    Args:
        name: Name for the profiling session
        detailed: Whether to collect detailed memory information
        track_gc_objects: Whether to track garbage collector objects
        use_tracemalloc: Whether to use tracemalloc for detailed memory tracking
        interval: Interval in seconds between snapshots (0 for start/end only)
        
    Returns:
        The memory profiler instance
    """
    profiler = MemoryProfiler(
        detailed=detailed,
        track_gc_objects=track_gc_objects,
        use_tracemalloc=use_tracemalloc,
        interval=interval,
    )
    
    with profiler.profile_block(name):
        yield profiler
    
    return profiler