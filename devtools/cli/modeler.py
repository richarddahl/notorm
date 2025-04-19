"""
CLI commands for the data modeler tool.

This module provides CLI commands for the visual data modeling tool.
"""

import os
import logging
import sys
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)

# Console for rich output
console = Console() if TYPER_AVAILABLE else None


if TYPER_AVAILABLE:
    modeler_app = typer.Typer(help="Visual data modeling tools")
    
    @modeler_app.command("start")
    def start_modeler(
        host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
        port: int = typer.Option(8765, "--port", "-p", help="Port to bind to"),
        no_browser: bool = typer.Option(False, "--no-browser", help="Don't open browser"),
        project_dir: Optional[Path] = typer.Option(None, "--project", "-d", help="Project directory")
    ):
        """Start the visual data modeling tool."""
        try:
            from uno.devtools.modeler.server import start_server
            
            # Set project directory if provided
            if project_dir:
                if not project_dir.exists():
                    console.print(f"[bold red]Error:[/bold red] Project directory {project_dir} does not exist")
                    sys.exit(1)
                os.environ["UNO_PROJECT_DIR"] = str(project_dir)
            
            console.print(Panel(f"Starting Uno Data Modeler at http://{host}:{port}", expand=False))
            console.print("Press Ctrl+C to exit")
            
            start_server(host=host, port=port, open_browser=not no_browser)
        except ImportError as e:
            console.print(f"[bold red]Error:[/bold red] Failed to import modeler server. Make sure dependencies are installed.")
            console.print(f"Missing: {e}")
            console.print("Try: pip install fastapi uvicorn jinja2")
            sys.exit(1)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
    
    
    @modeler_app.command("analyze")
    def analyze_project(
        project_dir: Path = typer.Argument(
            ..., help="Project directory to analyze", exists=True, file_okay=False, dir_okay=True
        ),
        output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for model"),
        model_type: str = typer.Option("entity", "--type", "-t", help="Type of model to analyze (entity, repository, service, all)")
    ):
        """Analyze a project and extract data models."""
        try:
            from uno.devtools.modeler.analyzer import AnalyzeCodebase, ModelType
            import json
            
            console.print(f"Analyzing project at {project_dir}...")
            
            analyzer = AnalyzeCodebase(project_dir)
            result = analyzer.analyze(ModelType(model_type))
            
            if output:
                with open(output, "w") as f:
                    json.dump(result, f, indent=2)
                console.print(f"[bold green]✓[/bold green] Model saved to {output}")
            else:
                console.print("[bold]Extracted Model:[/bold]")
                console.print(f"Entities: {len(result['entities'])}")
                console.print(f"Relationships: {len(result['relationships'])}")
                
                for entity in result["entities"]:
                    console.print(f"\n[bold]{entity.name}[/bold]")
                    for field in entity.fields:
                        console.print(f"  - {field.name}: {field.type}")
        
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)


def setup_parser(subparsers):
    """Set up the argument parser for the modeler command."""
    modeler_parser = subparsers.add_parser("modeler", help="Visual data modeling tools")
    modeler_subparsers = modeler_parser.add_subparsers(dest="subcommand")
    
    # Start command
    start_parser = modeler_subparsers.add_parser("start", help="Start the visual data modeling tool")
    start_parser.add_argument("--host", "-h", default="localhost", help="Host to bind to")
    start_parser.add_argument("--port", "-p", type=int, default=8765, help="Port to bind to")
    start_parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    start_parser.add_argument("--project", "-d", type=Path, help="Project directory")
    
    # Analyze command
    analyze_parser = modeler_subparsers.add_parser("analyze", help="Analyze a project and extract data models")
    analyze_parser.add_argument("project_dir", type=Path, help="Project directory to analyze")
    analyze_parser.add_argument("--output", "-o", type=Path, help="Output file for model")
    analyze_parser.add_argument("--type", "-t", default="entity", help="Type of model to analyze (entity, repository, service, all)")


def handle_command(args):
    """Handle the modeler command."""
    if args.subcommand == "start":
        from uno.devtools.modeler.server import start_server
        
        # Set project directory if provided
        if hasattr(args, "project") and args.project:
            if not args.project.exists():
                print(f"Error: Project directory {args.project} does not exist")
                sys.exit(1)
            os.environ["UNO_PROJECT_DIR"] = str(args.project)
        
        print(f"Starting Uno Data Modeler at http://{args.host}:{args.port}")
        print("Press Ctrl+C to exit")
        
        start_server(host=args.host, port=args.port, open_browser=not args.no_browser)
    elif args.subcommand == "analyze":
        from uno.devtools.modeler.analyzer import AnalyzeCodebase, ModelType
        import json
        
        print(f"Analyzing project at {args.project_dir}...")
        
        analyzer = AnalyzeCodebase(args.project_dir)
        result = analyzer.analyze(ModelType(args.type))
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
            print(f"Model saved to {args.output}")
        else:
            print("Extracted Model:")
            print(f"Entities: {len(result['entities'])}")
            print(f"Relationships: {len(result['relationships'])}")
            
            for entity in result["entities"]:
                print(f"\n{entity.name}")
                for field in entity.fields:
                    print(f"  - {field.name}: {field.type}")
    else:
        print("Unknown subcommand. Use 'modeler start' or 'modeler analyze'.")


if __name__ == "__main__":
    if TYPER_AVAILABLE:
        modeler_app()
    else:
        print("Typer not available. Please install it with: pip install typer rich")
        sys.exit(1)