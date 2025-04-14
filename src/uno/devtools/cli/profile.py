"""
Profiling CLI commands for Uno.

This module provides CLI commands for profiling Uno applications.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable, cast

try:
    import typer
    from typing_extensions import Annotated
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    import argparse

from uno.devtools.profiling.profiler import Profiler, profile, profile_block, get_profiler
from uno.devtools.profiling.memory import MemoryProfiler, memory_profile, memory_profile_block, get_memory_profiler
from uno.devtools.profiling.hotspot import find_hotspots, analyze_performance
from uno.devtools.profiling.visualization import visualize_profile
from uno.devtools.cli.main import setup_logging


logger = logging.getLogger("uno.cli.profile")


if TYPER_AVAILABLE:
    profile_app = typer.Typer(
        name="profile",
        help="Profiling utilities for Uno",
        add_completion=True,
    )
    
    def profile_command():
        """Setup function for the profile command."""
        return profile_app
    
    @profile_app.command("dashboard")
    def start_dashboard_command(
        host: Annotated[str, typer.Option("--host", "-h", help="Host to bind to")] = "localhost",
        port: Annotated[int, typer.Option("--port", "-p", help="Port to bind to")] = 8765,
        app_path: Annotated[Optional[str], typer.Option("--app", "-a", help="Path to ASGI application to profile")] = None,
        no_browser: Annotated[bool, typer.Option("--no-browser", help="Don't open browser")] = False,
        verbose: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")] = 0,
    ):
        """Start the performance profiling dashboard."""
        setup_logging(verbose)
        
        try:
            # Import the profiler dashboard components
            try:
                from uno.devtools.profiler.middleware.profiling_middleware import ProfilerMiddleware
                from uno.devtools.profiler.dashboard.server import initialize_dashboard
            except ImportError as e:
                logger.error(f"Failed to import profiler dashboard: {e}")
                logger.error("Make sure the dependencies are installed: fastapi uvicorn psutil")
                sys.exit(1)
            
            # Create a profiler middleware
            app = None
            if app_path:
                # Try to load the application
                try:
                    logger.info(f"Loading application from {app_path}...")
                    module_path, app_name = app_path.split(":") if ":" in app_path else (app_path, "app")
                    module = __import__(module_path, fromlist=[app_name])
                    app = getattr(module, app_name)
                    logger.info("Application loaded successfully")
                except (ImportError, AttributeError) as e:
                    logger.error(f"Failed to load application: {str(e)}")
                    logger.info("Starting dashboard with dummy profiler")
            
            # Create profiler middleware
            profiler = ProfilerMiddleware(app=app)
            
            logger.info(f"Starting profiler dashboard at http://{host}:{port}")
            logger.info("Press Ctrl+C to exit")
            
            # Initialize dashboard
            initialize_dashboard(
                profiler_middleware=profiler,
                host=host,
                port=port,
                open_browser=not no_browser,
            )
        except Exception as e:
            logger.error(f"Error starting profiler dashboard: {e}")
            sys.exit(1)
    
    @profile_app.command("run")
    def run_profile_command(
        target: Annotated[str, typer.Argument(help="Module.function to profile (e.g., 'myapp.main:run_app')")],
        output: Annotated[str, typer.Option(help="Output format: text, json, or html")] = "text",
        output_file: Annotated[Optional[Path], typer.Option(help="Output file path")] = None,
        detailed: Annotated[bool, typer.Option(help="Enable detailed profiling with cProfile")] = True,
        use_yappi: Annotated[bool, typer.Option(help="Use yappi for multi-threaded profiling")] = False,
        include_builtins: Annotated[bool, typer.Option(help="Include Python builtins in profile")] = False,
        max_depth: Annotated[int, typer.Option(help="Maximum call depth to display")] = 10,
        verbose: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")] = 0,
    ):
        """Profile a Python function or method."""
        setup_logging(verbose)
        
        # Parse target
        try:
            module_path, func_name = target.split(":")
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)
            
            if not callable(func):
                logger.error(f"{target} is not callable")
                sys.exit(1)
                
            # Create profiler
            profiler = Profiler(
                detailed=detailed,
                yappi=use_yappi,
                builtins=include_builtins,
                profile_memory=False,
            )
            
            # Run the profiler
            logger.info(f"Profiling {target}...")
            start_time = time.time()
            result = profiler.run_profile(func.__qualname__, func)
            total_time = time.time() - start_time
            
            # Format and output results
            if output == "text":
                profile_output = profiler.print_stats(func.__qualname__, top=max_depth)
                if output_file:
                    with open(output_file, "w") as f:
                        f.write(profile_output)
                    logger.info(f"Profile results written to {output_file}")
                else:
                    print("\n" + profile_output)
            elif output == "json":
                # Convert profile results to JSON
                profile_result = profiler.get_stats(func.__qualname__)
                if profile_result:
                    json_result = {
                        "name": profile_result.name,
                        "total_time": profile_result.total_time,
                        "ncalls": profile_result.ncalls,
                        "cumtime": profile_result.cumtime,
                        "detailed": detailed,
                    }
                    if hasattr(profile_result, "function_stats"):
                        # Convert function stats to serializable format
                        json_result["functions"] = {
                            name: {k: v for k, v in stats.items() if k != "callers"}
                            for name, stats in profile_result.function_stats.items()
                        }
                    
                    json_output = json.dumps(json_result, indent=2)
                    if output_file:
                        with open(output_file, "w") as f:
                            f.write(json_output)
                        logger.info(f"Profile results written to {output_file}")
                    else:
                        print(json_output)
            elif output == "html":
                # Generate HTML visualization if available
                if output_file and hasattr(visualize_profile, "__call__"):
                    profile_result = profiler.get_stats(func.__qualname__)
                    if profile_result:
                        visualize_profile(profile_result, output_file)
                        logger.info(f"HTML profile visualization written to {output_file}")
                else:
                    logger.error("HTML output requires visualization module and output file")
                    sys.exit(1)
                    
            logger.info(f"Profiling complete. Total time: {total_time:.2f}s")
            
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Error profiling {target}: {str(e)}")
            sys.exit(1)
    
    @profile_app.command("memory")
    def memory_profile_command(
        target: Annotated[str, typer.Argument(help="Module.function to profile (e.g., 'myapp.main:run_app')")],
        output: Annotated[str, typer.Option(help="Output format: text or json")] = "text",
        output_file: Annotated[Optional[Path], typer.Option(help="Output file path")] = None,
        detailed: Annotated[bool, typer.Option(help="Enable detailed memory profiling")] = False,
        track_gc: Annotated[bool, typer.Option(help="Track garbage collector objects")] = False,
        use_tracemalloc: Annotated[bool, typer.Option(help="Use tracemalloc for detailed tracking")] = False,
        interval: Annotated[float, typer.Option(help="Interval in seconds between snapshots (0 for start/end only)")] = 0.0,
        verbose: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")] = 0,
    ):
        """Profile memory usage of a Python function or method."""
        setup_logging(verbose)
        
        # Parse target
        try:
            module_path, func_name = target.split(":")
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)
            
            if not callable(func):
                logger.error(f"{target} is not callable")
                sys.exit(1)
            
            # Create memory profiler
            memory_profiler = MemoryProfiler(
                detailed=detailed,
                track_gc_objects=track_gc,
                use_tracemalloc=use_tracemalloc,
                interval=interval,
            )
            
            # Run the profiler
            logger.info(f"Memory profiling {target}...")
            start_time = time.time()
            result = memory_profiler.run_profile(func.__qualname__, func)
            total_time = time.time() - start_time
            
            # Format and output results
            if output == "text":
                profile_output = memory_profiler.print_stats(func.__qualname__)
                if output_file:
                    with open(output_file, "w") as f:
                        f.write(profile_output)
                    logger.info(f"Memory profile results written to {output_file}")
                else:
                    print("\n" + profile_output)
            elif output == "json":
                # Convert profile results to JSON
                profile_result = memory_profiler.get_stats(func.__qualname__)
                if profile_result:
                    # Convert to serializable format
                    json_result = {
                        "name": profile_result.name,
                        "start": profile_result.start_snapshot.as_dict(),
                        "end": profile_result.end_snapshot.as_dict(),
                        "delta": profile_result.delta,
                    }
                    
                    if profile_result.peak:
                        json_result["peak"] = profile_result.peak.as_dict()
                    
                    json_output = json.dumps(json_result, indent=2)
                    if output_file:
                        with open(output_file, "w") as f:
                            f.write(json_output)
                        logger.info(f"Memory profile results written to {output_file}")
                    else:
                        print(json_output)
                        
            logger.info(f"Memory profiling complete. Total time: {total_time:.2f}s")
            
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Error memory profiling {target}: {str(e)}")
            sys.exit(1)
    
    @profile_app.command("hotspots")
    def find_hotspots_command(
        target: Annotated[str, typer.Argument(help="Module to analyze for hotspots (e.g., 'myapp.models')")],
        depth: Annotated[int, typer.Option(help="Maximum callstack depth to analyze")] = 10,
        min_time: Annotated[float, typer.Option(help="Minimum percentage of total time to include")] = 1.0,
        output_file: Annotated[Optional[Path], typer.Option(help="Output file path")] = None,
        verbose: Annotated[int, typer.Option("--verbose", "-v", count=True, help="Verbosity level")] = 0,
    ):
        """Find performance hotspots in a module."""
        setup_logging(verbose)
        
        try:
            # Import module
            module = __import__(target, fromlist=["__name__"])
            
            # Find hotspots
            logger.info(f"Analyzing {target} for performance hotspots...")
            results = find_hotspots(module, depth=depth, min_percent=min_time)
            
            # Format results
            output = f"Performance hotspots in {target}:\n\n"
            for i, (func_name, stats) in enumerate(results, 1):
                output += f"{i}. {func_name}\n"
                output += f"   - Total time: {stats['total_time']:.6f}s ({stats['percent']:.2f}%)\n"
                output += f"   - Calls: {stats['ncalls']}\n"
                output += f"   - Time per call: {stats['time_per_call']:.6f}s\n"
                if "callers" in stats:
                    output += "   - Top callers:\n"
                    for caller, count in stats["callers"].items():
                        output += f"     - {caller}: {count} calls\n"
                output += "\n"
            
            # Output results
            if output_file:
                with open(output_file, "w") as f:
                    f.write(output)
                logger.info(f"Hotspot analysis written to {output_file}")
            else:
                print("\n" + output)
                
            logger.info(f"Hotspot analysis complete. Found {len(results)} hotspots.")
            
        except (ImportError, AttributeError) as e:
            logger.error(f"Error analyzing {target}: {str(e)}")
            sys.exit(1)
else:
    # Simple CLI without typer
    def setup_parser(subparsers):
        """Set up command parsers.
        
        Args:
            subparsers: Subparsers object from argparse
        """
        # Add profile parser
        profile_parser = subparsers.add_parser("profile", help="Profiling utilities for Uno")
        profile_subparsers = profile_parser.add_subparsers(dest="subcommand")
        
        # Dashboard command
        dashboard_parser = profile_subparsers.add_parser("dashboard", help="Start the performance profiling dashboard")
        dashboard_parser.add_argument("--host", "-h", default="localhost", help="Host to bind to")
        dashboard_parser.add_argument("--port", "-p", type=int, default=8765, help="Port to bind to")
        dashboard_parser.add_argument("--app", "-a", help="Path to ASGI application to profile")
        dashboard_parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
        dashboard_parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level")
        
        # Run command
        run_parser = profile_subparsers.add_parser("run", help="Profile a Python function or method")
        run_parser.add_argument("target", help="Module.function to profile (e.g., 'myapp.main:run_app')")
        run_parser.add_argument("--output", default="text", choices=["text", "json", "html"], help="Output format")
        run_parser.add_argument("--output-file", help="Output file path")
        run_parser.add_argument("--detailed", action="store_true", help="Enable detailed profiling with cProfile")
        run_parser.add_argument("--use-yappi", action="store_true", help="Use yappi for multi-threaded profiling")
        run_parser.add_argument("--include-builtins", action="store_true", help="Include Python builtins in profile")
        run_parser.add_argument("--max-depth", type=int, default=10, help="Maximum call depth to display")
        run_parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level")
        
        # Memory command
        memory_parser = profile_subparsers.add_parser("memory", help="Profile memory usage of a Python function or method")
        memory_parser.add_argument("target", help="Module.function to profile (e.g., 'myapp.main:run_app')")
        memory_parser.add_argument("--output", default="text", choices=["text", "json"], help="Output format")
        memory_parser.add_argument("--output-file", help="Output file path")
        memory_parser.add_argument("--detailed", action="store_true", help="Enable detailed memory profiling")
        memory_parser.add_argument("--track-gc", action="store_true", help="Track garbage collector objects")
        memory_parser.add_argument("--use-tracemalloc", action="store_true", help="Use tracemalloc for detailed tracking")
        memory_parser.add_argument("--interval", type=float, default=0.0, help="Interval in seconds between snapshots (0 for start/end only)")
        memory_parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level")
        
        # Hotspots command
        hotspots_parser = profile_subparsers.add_parser("hotspots", help="Find performance hotspots in a module")
        hotspots_parser.add_argument("target", help="Module to analyze for hotspots (e.g., 'myapp.models')")
        hotspots_parser.add_argument("--depth", type=int, default=10, help="Maximum callstack depth to analyze")
        hotspots_parser.add_argument("--min-time", type=float, default=1.0, help="Minimum percentage of total time to include")
        hotspots_parser.add_argument("--output-file", help="Output file path")
        hotspots_parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level")
    
    def handle_command(args):
        """Handle profile commands.
        
        Args:
            args: Command arguments
        """
        setup_logging(getattr(args, "verbose", 0))
        
        if args.subcommand == "dashboard":
            _handle_dashboard_command(args)
        elif args.subcommand == "run":
            _handle_run_command(args)
        elif args.subcommand == "memory":
            _handle_memory_command(args)
        elif args.subcommand == "hotspots":
            _handle_hotspots_command(args)
        else:
            print(f"Unknown profile subcommand: {args.subcommand}")
    
    def _handle_dashboard_command(args):
        """Handle dashboard command.
        
        Args:
            args: Command arguments
        """
        try:
            # Import the profiler dashboard components
            try:
                from uno.devtools.profiler.middleware.profiling_middleware import ProfilerMiddleware
                from uno.devtools.profiler.dashboard.server import initialize_dashboard
            except ImportError as e:
                print(f"Failed to import profiler dashboard: {e}")
                print("Make sure the dependencies are installed: fastapi uvicorn psutil")
                sys.exit(1)
            
            # Create a profiler middleware
            app = None
            if hasattr(args, "app") and args.app:
                # Try to load the application
                try:
                    print(f"Loading application from {args.app}...")
                    module_path, app_name = args.app.split(":") if ":" in args.app else (args.app, "app")
                    module = __import__(module_path, fromlist=[app_name])
                    app = getattr(module, app_name)
                    print("Application loaded successfully")
                except (ImportError, AttributeError) as e:
                    print(f"Failed to load application: {str(e)}")
                    print("Starting dashboard with dummy profiler")
            
            # Create profiler middleware
            profiler = ProfilerMiddleware(app=app)
            
            print(f"Starting profiler dashboard at http://{args.host}:{args.port}")
            print("Press Ctrl+C to exit")
            
            # Initialize dashboard
            initialize_dashboard(
                profiler_middleware=profiler,
                host=args.host,
                port=args.port,
                open_browser=not args.no_browser,
            )
        except Exception as e:
            print(f"Error starting profiler dashboard: {e}")
            sys.exit(1)
    
    def _handle_run_command(args):
        """Handle run profile command.
        
        Args:
            args: Command arguments
        """
        # Parse target
        try:
            module_path, func_name = args.target.split(":")
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)
            
            if not callable(func):
                logger.error(f"{args.target} is not callable")
                sys.exit(1)
                
            # Create profiler
            profiler = Profiler(
                detailed=args.detailed,
                yappi=args.use_yappi,
                builtins=args.include_builtins,
                profile_memory=False,
            )
            
            # Run the profiler
            logger.info(f"Profiling {args.target}...")
            start_time = time.time()
            result = profiler.run_profile(func.__qualname__, func)
            total_time = time.time() - start_time
            
            # Format and output results
            if args.output == "text":
                profile_output = profiler.print_stats(func.__qualname__, top=args.max_depth)
                if args.output_file:
                    with open(args.output_file, "w") as f:
                        f.write(profile_output)
                    logger.info(f"Profile results written to {args.output_file}")
                else:
                    print("\n" + profile_output)
            elif args.output == "json":
                # Convert profile results to JSON
                profile_result = profiler.get_stats(func.__qualname__)
                if profile_result:
                    json_result = {
                        "name": profile_result.name,
                        "total_time": profile_result.total_time,
                        "ncalls": profile_result.ncalls,
                        "cumtime": profile_result.cumtime,
                        "detailed": args.detailed,
                    }
                    if hasattr(profile_result, "function_stats"):
                        # Convert function stats to serializable format
                        json_result["functions"] = {
                            name: {k: v for k, v in stats.items() if k != "callers"}
                            for name, stats in profile_result.function_stats.items()
                        }
                    
                    json_output = json.dumps(json_result, indent=2)
                    if args.output_file:
                        with open(args.output_file, "w") as f:
                            f.write(json_output)
                        logger.info(f"Profile results written to {args.output_file}")
                    else:
                        print(json_output)
            elif args.output == "html":
                # Generate HTML visualization if available
                if args.output_file and hasattr(visualize_profile, "__call__"):
                    profile_result = profiler.get_stats(func.__qualname__)
                    if profile_result:
                        visualize_profile(profile_result, args.output_file)
                        logger.info(f"HTML profile visualization written to {args.output_file}")
                else:
                    logger.error("HTML output requires visualization module and output file")
                    sys.exit(1)
                    
            logger.info(f"Profiling complete. Total time: {total_time:.2f}s")
            
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Error profiling {args.target}: {str(e)}")
            sys.exit(1)
    
    def _handle_memory_command(args):
        """Handle memory profile command.
        
        Args:
            args: Command arguments
        """
        # Parse target
        try:
            module_path, func_name = args.target.split(":")
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)
            
            if not callable(func):
                logger.error(f"{args.target} is not callable")
                sys.exit(1)
            
            # Create memory profiler
            memory_profiler = MemoryProfiler(
                detailed=args.detailed,
                track_gc_objects=args.track_gc,
                use_tracemalloc=args.use_tracemalloc,
                interval=args.interval,
            )
            
            # Run the profiler
            logger.info(f"Memory profiling {args.target}...")
            start_time = time.time()
            result = memory_profiler.run_profile(func.__qualname__, func)
            total_time = time.time() - start_time
            
            # Format and output results
            if args.output == "text":
                profile_output = memory_profiler.print_stats(func.__qualname__)
                if args.output_file:
                    with open(args.output_file, "w") as f:
                        f.write(profile_output)
                    logger.info(f"Memory profile results written to {args.output_file}")
                else:
                    print("\n" + profile_output)
            elif args.output == "json":
                # Convert profile results to JSON
                profile_result = memory_profiler.get_stats(func.__qualname__)
                if profile_result:
                    # Convert to serializable format
                    json_result = {
                        "name": profile_result.name,
                        "start": profile_result.start_snapshot.as_dict(),
                        "end": profile_result.end_snapshot.as_dict(),
                        "delta": profile_result.delta,
                    }
                    
                    if profile_result.peak:
                        json_result["peak"] = profile_result.peak.as_dict()
                    
                    json_output = json.dumps(json_result, indent=2)
                    if args.output_file:
                        with open(args.output_file, "w") as f:
                            f.write(json_output)
                        logger.info(f"Memory profile results written to {args.output_file}")
                    else:
                        print(json_output)
                        
            logger.info(f"Memory profiling complete. Total time: {total_time:.2f}s")
            
        except (ValueError, ImportError, AttributeError) as e:
            logger.error(f"Error memory profiling {args.target}: {str(e)}")
            sys.exit(1)
    
    def _handle_hotspots_command(args):
        """Handle hotspots command.
        
        Args:
            args: Command arguments
        """
        try:
            # Import module
            module = __import__(args.target, fromlist=["__name__"])
            
            # Find hotspots
            logger.info(f"Analyzing {args.target} for performance hotspots...")
            results = find_hotspots(module, depth=args.depth, min_percent=args.min_time)
            
            # Format results
            output = f"Performance hotspots in {args.target}:\n\n"
            for i, (func_name, stats) in enumerate(results, 1):
                output += f"{i}. {func_name}\n"
                output += f"   - Total time: {stats['total_time']:.6f}s ({stats['percent']:.2f}%)\n"
                output += f"   - Calls: {stats['ncalls']}\n"
                output += f"   - Time per call: {stats['time_per_call']:.6f}s\n"
                if "callers" in stats:
                    output += "   - Top callers:\n"
                    for caller, count in stats["callers"].items():
                        output += f"     - {caller}: {count} calls\n"
                output += "\n"
            
            # Output results
            if args.output_file:
                with open(args.output_file, "w") as f:
                    f.write(output)
                logger.info(f"Hotspot analysis written to {args.output_file}")
            else:
                print("\n" + output)
                
            logger.info(f"Hotspot analysis complete. Found {len(results)} hotspots.")
            
        except (ImportError, AttributeError) as e:
            logger.error(f"Error analyzing {args.target}: {str(e)}")
            sys.exit(1)