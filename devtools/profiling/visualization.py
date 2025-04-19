"""
Visualization utilities for profiling data.

This module provides utilities for visualizing profiling results.
"""

import os
import json
import logging
import tempfile
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from uno.devtools.profiling.profiler import ProfileResult


logger = logging.getLogger("uno.profiler.visualization")


def visualize_profile(
    profile_result: Union[ProfileResult, Dict[str, Any]], 
    output_file: Union[str, Path],
    include_callers: bool = True,
    include_callees: bool = True,
) -> None:
    """Generate a visualization of profiling results.
    
    Args:
        profile_result: Profiling result to visualize
        output_file: Path to write the visualization to
        include_callers: Whether to include callers in the visualization
        include_callees: Whether to include callees in the visualization
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        HAS_PLOTLY = True
    except ImportError:
        logger.warning("Plotly not available. Install with 'pip install plotly'")
        HAS_PLOTLY = False
        
    # Basic HTML fallback if plotly is not available
    if not HAS_PLOTLY:
        _generate_basic_html(profile_result, output_file)
        return
    
    # Convert profile result to a dictionary if it's not already
    if isinstance(profile_result, ProfileResult):
        data = {
            "name": profile_result.name,
            "total_time": profile_result.total_time,
            "ncalls": profile_result.ncalls,
            "cumtime": profile_result.cumtime,
            "function_stats": getattr(profile_result, "function_stats", {})
        }
    else:
        data = profile_result
    
    # Create plotly figure
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Function Time Distribution", "Function Call Count"),
        vertical_spacing=0.2
    )
    
    # Extract function stats
    function_stats = data.get("function_stats", {})
    if not function_stats:
        logger.warning("No detailed function stats available for visualization")
        _generate_basic_html(profile_result, output_file)
        return
    
    # Prepare data for visualization
    func_names = []
    total_times = []
    cum_times = []
    call_counts = []
    
    # Sort by total time
    sorted_stats = sorted(
        function_stats.items(),
        key=lambda x: x[1].get("tottime", 0),
        reverse=True
    )
    
    # Take top 20 functions
    for name, stats in sorted_stats[:20]:
        func_names.append(name.split(":")[-1])  # Extract function name without module
        total_times.append(stats.get("tottime", 0))
        cum_times.append(stats.get("cumtime", 0))
        call_counts.append(stats.get("ncalls", 0))
    
    # Time distribution bar chart
    fig.add_trace(
        go.Bar(
            x=func_names,
            y=total_times,
            name="Total Time",
            marker_color="rgb(55, 83, 109)"
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=func_names,
            y=cum_times,
            name="Cumulative Time",
            marker_color="rgb(26, 118, 255)"
        ),
        row=1, col=1
    )
    
    # Call count bar chart
    fig.add_trace(
        go.Bar(
            x=func_names,
            y=call_counts,
            name="Call Count",
            marker_color="rgb(34, 139, 34)"
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title_text=f"Profile Results for {data.get('name', 'Unknown')}",
        title_font_size=24,
        height=800,
        width=1000,
        bargap=0.15,
        bargroupgap=0.1
    )
    
    # Add annotations
    total_run_time = data.get("total_time", 0)
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.5, y=1.15,
        text=f"Total Run Time: {total_run_time:.6f}s",
        showarrow=False,
        font=dict(size=16)
    )
    
    # Save to HTML file
    try:
        fig.write_html(output_file)
        logger.info(f"Visualization saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving visualization: {e}")
        _generate_basic_html(profile_result, output_file)


def _generate_basic_html(
    profile_result: Union[ProfileResult, Dict[str, Any]],
    output_file: Union[str, Path]
) -> None:
    """Generate a basic HTML visualization of profiling results.
    
    Args:
        profile_result: Profiling result to visualize
        output_file: Path to write the visualization to
    """
    # Convert profile result to a dictionary if it's not already
    if isinstance(profile_result, ProfileResult):
        data = {
            "name": profile_result.name,
            "total_time": profile_result.total_time,
            "ncalls": profile_result.ncalls,
            "cumtime": profile_result.cumtime,
            "function_stats": getattr(profile_result, "function_stats", {})
        }
    else:
        data = profile_result
    
    # Generate HTML
    html = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "    <title>Profile Results</title>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; margin: 20px; }",
        "        h1 { color: #333; }",
        "        table { border-collapse: collapse; width: 100%; }",
        "        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "        th { background-color: #f2f2f2; }",
        "        tr:nth-child(even) { background-color: #f9f9f9; }",
        "        .summary { margin-bottom: 20px; padding: 10px; background-color: #e9f7fe; border-radius: 5px; }",
        "    </style>",
        "</head>",
        "<body>",
        f"    <h1>Profile Results for {data.get('name', 'Unknown')}</h1>",
        "    <div class='summary'>",
        f"        <p><strong>Total Time:</strong> {data.get('total_time', 0):.6f}s</p>",
        f"        <p><strong>Call Count:</strong> {data.get('ncalls', 0)}</p>",
        f"        <p><strong>Cumulative Time:</strong> {data.get('cumtime', 0):.6f}s</p>",
        "    </div>",
        "    <h2>Function Statistics</h2>",
        "    <table>",
        "        <tr>",
        "            <th>Function</th>",
        "            <th>Calls</th>",
        "            <th>Total Time (s)</th>",
        "            <th>Per Call (s)</th>",
        "            <th>Cumulative Time (s)</th>",
        "        </tr>"
    ]
    
    # Add function stats
    function_stats = data.get("function_stats", {})
    if function_stats:
        # Sort by total time
        sorted_stats = sorted(
            function_stats.items(),
            key=lambda x: x[1].get("tottime", 0),
            reverse=True
        )
        
        for name, stats in sorted_stats:
            tottime = stats.get("tottime", 0)
            ncalls = stats.get("ncalls", 0)
            percall = tottime / ncalls if ncalls > 0 else 0
            cumtime = stats.get("cumtime", 0)
            
            html.append("        <tr>")
            html.append(f"            <td>{name}</td>")
            html.append(f"            <td>{ncalls}</td>")
            html.append(f"            <td>{tottime:.6f}</td>")
            html.append(f"            <td>{percall:.6f}</td>")
            html.append(f"            <td>{cumtime:.6f}</td>")
            html.append("        </tr>")
    else:
        html.append("        <tr><td colspan='5'>No detailed function stats available</td></tr>")
    
    # Complete HTML
    html.extend([
        "    </table>",
        "</body>",
        "</html>"
    ])
    
    # Write to file
    try:
        with open(output_file, "w") as f:
            f.write("\n".join(html))
        logger.info(f"Basic HTML visualization saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving basic HTML visualization: {e}")