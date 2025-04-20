"""
Documentation server for Uno applications.

This module provides a simple HTTP server for viewing interactive documentation
for Uno applications.
"""

import os
import sys
import webbrowser
import argparse
import json
import importlib
import pkgutil
from typing import Dict, List, Optional, Set, Tuple, Any
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading


def serve_docs(
    host: str = "localhost",
    port: int = 8088,
    open_browser: bool = True,
    theme: str = "light",
    docs_dir: str | None = None,
) -> None:
    """
    Start a documentation server for viewing Uno documentation.

    Args:
        host: Hostname to serve on
        port: Port to serve on
        open_browser: Whether to open a browser automatically
        theme: Documentation theme (light or dark)
        docs_dir: Directory containing documentation files
    """
    # If docs_dir is not provided, attempt to find it
    if not docs_dir:
        docs_dir = _find_docs_dir()

    if not os.path.exists(docs_dir):
        raise ValueError(f"Documentation directory not found: {docs_dir}")

    # Change to the docs directory
    os.chdir(docs_dir)

    # Create server
    server_address = (host, port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)

    # Start server in a separate thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    url = f"http://{host}:{port}/"
    print(f"Documentation server started at {url}")

    # Open browser if requested
    if open_browser:
        webbrowser.open(url)

    try:
        # Keep the main thread alive
        server_thread.join()
    except KeyboardInterrupt:
        print("\nShutting down documentation server...")
        httpd.shutdown()


def _find_docs_dir() -> str:
    """
    Attempt to find the documentation directory.

    Returns:
        Path to the documentation directory
    """
    # Try to find docs in common locations
    potential_paths = [
        os.path.join(os.getcwd(), "docs"),
        os.path.join(os.getcwd(), "doc"),
        os.path.join(os.getcwd(), "documentation"),
        os.path.join(os.getcwd(), "site"),
        os.path.join(os.getcwd(), "build", "docs"),
        os.path.join(os.getcwd(), "build", "documentation"),
        os.path.join(os.getcwd(), "build", "site"),
    ]

    # Add parent directories to search
    parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    potential_paths.extend(
        [
            os.path.join(parent_dir, "docs"),
            os.path.join(parent_dir, "doc"),
            os.path.join(parent_dir, "documentation"),
            os.path.join(parent_dir, "site"),
        ]
    )

    # Check each path
    for path in potential_paths:
        if os.path.exists(path) and os.path.isdir(path):
            # Look for index.html or README.md as signals of a docs directory
            if os.path.exists(os.path.join(path, "index.html")):
                return path
            if os.path.exists(os.path.join(path, "README.md")):
                return path

    # If all else fails, use the current directory
    return os.getcwd()


def main() -> None:
    """Command-line entry point for the documentation server."""
    parser = argparse.ArgumentParser(description="Uno Documentation Server")
    parser.add_argument("--host", default="localhost", help="Hostname to serve on")
    parser.add_argument("--port", type=int, default=8088, help="Port to serve on")
    parser.add_argument(
        "--no-browser", action="store_true", help="Don't open browser automatically"
    )
    parser.add_argument(
        "--theme",
        default="light",
        choices=["light", "dark"],
        help="Documentation theme",
    )
    parser.add_argument("--docs-dir", help="Directory containing documentation files")

    args = parser.parse_args()

    serve_docs(
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
        theme=args.theme,
        docs_dir=args.docs_dir,
    )


if __name__ == "__main__":
    main()
