"""
Scaffolding tools for creating Uno projects and features.

This module provides CLI commands for scaffolding entire projects and features:
- Project creation
- Feature scaffolding
- Module creation
"""

import os
import sys
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import re

try:
    import typer
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Get root directory of the Uno framework
UNO_ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent

# Templates directory
TEMPLATES_DIR = UNO_ROOT_DIR / "src" / "uno" / "devtools" / "templates"

# Logger
logger = logging.getLogger(__name__)

# Console for rich output
console = Console() if RICH_AVAILABLE else None


def get_template_env() -> Environment:
    """
    Get a configured Jinja2 template environment.

    Returns:
        Jinja2 Environment configured with template loaders
    """
    if not TEMPLATES_DIR.exists():
        # Create templates directory if it doesn't exist
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

        # Copy default templates if available
        default_templates = UNO_ROOT_DIR / "templates"
        if default_templates.exists():
            for template_file in default_templates.glob("**/*"):
                if template_file.is_file():
                    relative_path = template_file.relative_to(default_templates)
                    target_path = TEMPLATES_DIR / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(template_file, target_path)

    # Create Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add custom filters
    env.filters["snake_case"] = lambda s: re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()
    env.filters["camel_case"] = lambda s: "".join(
        word.capitalize() for word in s.split("_")
    )
    env.filters["pascal_case"] = lambda s: "".join(
        word.capitalize() for word in s.split("_")
    )
    env.filters["kebab_case"] = lambda s: s.replace("_", "-").lower()

    return env


def scaffold_project(
    name: str,
    template: str = "standard",
    database: str = "postgresql",
    api: bool = True,
    domain_driven: bool = True,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Scaffold a new Uno project.

    Args:
        name: Project name
        template: Project template to use
        database: Database backend
        api: Include API setup
        domain_driven: Use domain-driven design
        output_dir: Directory to create the project in (default: current directory)

    Returns:
        Path to the created project
    """
    if RICH_AVAILABLE:
        console.print(Panel(f"Creating new Uno project: [bold]{name}[/bold]"))

    # Validate project name
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
        raise ValueError(
            f"Invalid project name: {name}. "
            "Project name must start with a letter and contain only "
            "letters, numbers, and underscores."
        )

    # Set up output directory
    if output_dir is None:
        output_dir = Path.cwd()

    project_dir = output_dir / name

    # Check if directory already exists
    if project_dir.exists():
        raise FileExistsError(f"Directory '{project_dir}' already exists")

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=False)

    # Get template environment
    env = get_template_env()

    # Check if template exists
    template_dir = TEMPLATES_DIR / "project" / template
    if not template_dir.exists():
        available_templates = [
            d.name for d in (TEMPLATES_DIR / "project").glob("*") if d.is_dir()
        ]

        if not available_templates:
            raise ValueError(
                f"No project templates found in {TEMPLATES_DIR / 'project'}. "
                "Please create a template directory first."
            )

        raise ValueError(
            f"Template '{template}' not found. Available templates: "
            f"{', '.join(available_templates)}"
        )

    # Set up context for templates
    context = {
        "project_name": name,
        "database": database,
        "include_api": api,
        "domain_driven": domain_driven,
    }

    # Create directory structure based on template
    if RICH_AVAILABLE:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating project structure...", total=None)

            # Create directories first
            _create_project_directories(project_dir, template_dir, context)

            # Then create files
            _create_project_files(project_dir, template_dir, env, context)

            progress.update(task, completed=True)
    else:
        print("Creating project structure...")
        _create_project_directories(project_dir, template_dir, context)
        _create_project_files(project_dir, template_dir, env, context)
        print("Project structure created.")

    # Success message and next steps
    if RICH_AVAILABLE:
        console.print(
            f"[bold green]✓[/bold green] Project created successfully at {project_dir}"
        )

        table = Table(title="Next Steps")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")

        table.add_row(f"cd {name}", "Change to project directory")
        table.add_row("python -m venv venv", "Create virtual environment")
        table.add_row(
            "source venv/bin/activate", "Activate virtual environment (Linux/Mac)"
        )
        table.add_row(
            "venv\\Scripts\\activate", "Activate virtual environment (Windows)"
        )
        table.add_row("pip install -r requirements.txt", "Install dependencies")
        table.add_row("uno dev start", "Start development server")

        console.print(table)
    else:
        print(f"Project created successfully at {project_dir}")
        print("\nNext steps:")
        print(f"  cd {name}")
        print(f"  python -m venv venv")
        print(f"  source venv/bin/activate  # On Linux/Mac")
        print(f"  venv\\Scripts\\activate    # On Windows")
        print(f"  pip install -r requirements.txt")
        print(f"  uno dev start")

    return project_dir


def _create_model(
    name: str, project_dir: Path, env: Environment, context: Dict[str, Any]
) -> Path:
    """Create a database model file."""
    models_dir = (
        project_dir
        / "src"
        / context["project_name"]
        / "infrastructure"
        / "database"
        / "models"
    )
    models_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py if it doesn't exist
    init_file = models_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, "w") as f:
            f.write('"""Database models for the application."""\n\n')
            f.write("from sqlalchemy.ext.declarative import declarative_base\n\n")
            f.write("Base = declarative_base()\n\n")
            f.write("# Import all models here\n")

    output_file = models_dir / f"{name.lower()}_model.py"

    try:
        # Try to use the domain model template first
        template_path = "feature/domain_model.py.j2"
        if not (TEMPLATES_DIR / template_path).exists():
            # If the template doesn't exist, create a simple model file
            logger.warning(
                f"Template {template_path} not found, creating simple model file"
            )
            with open(output_file, "w") as f:
                f.write(f'"""\n{name.title()} database model.\n"""\n\n')
                f.write(
                    "from sqlalchemy import Column, String, Text, Boolean, DateTime\n"
                )
                f.write("from sqlalchemy.dialects.postgresql import UUID\n")
                f.write("from datetime import datetime, UTC\n")
                f.write("import uuid\n\n")
                f.write(
                    f'from {context["project_name"]}.infrastructure.database.base import Base\n\n\n'
                )
                f.write(f"class {name.title()}Model(Base):\n")
                f.write(f'    """SQLAlchemy model for {name.title()}."""\n\n')
                f.write(f'    __tablename__ = "{name.lower()}s"\n\n')
                f.write(
                    "    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))\n"
                )
                f.write("    name = Column(String(255), nullable=False)\n")
                f.write("    description = Column(Text, nullable=True)\n")
                f.write(
                    "    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(datetime.UTC))\n"
                )
                f.write(
                    "    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(datetime.UTC))\n"
                )
                f.write(
                    "    is_active = Column(Boolean, nullable=False, default=True)\n"
                )
            return output_file

        # Render the template
        template = env.get_template(template_path)
        content = template.render(**context)

        with open(output_file, "w") as f:
            f.write(content)

        # Update the __init__.py file to import the model
        with open(init_file, "r") as f:
            content = f.read()

        if f"from .{name.lower()}_model import {name.title()}Model" not in content:
            with open(init_file, "a") as f:
                f.write(f"from .{name.lower()}_model import {name.title()}Model\n")

        return output_file
    except Exception as e:
        logger.error(f"Error creating model: {e}")
        raise


def scaffold_feature(
    name: str,
    domain: str | None = None,
    create_entity: bool = True,
    create_repository: bool = True,
    create_service: bool = True,
    create_endpoint: bool = True,
    create_model: bool = True,
    create_tests: bool = True,
    project_dir: Optional[Path] = None,
) -> list[Path]:
    """
    Scaffold a complete feature with all required components.

    Args:
        name: Feature name
        domain: Domain name for the feature
        create_entity: Create entity model
        create_repository: Create repository
        create_service: Create service
        create_endpoint: Create API endpoint
        create_model: Create database model
        create_tests: Create tests
        project_dir: Project directory (default: detect from current directory)

    Returns:
        List of created file paths
    """
    if RICH_AVAILABLE:
        console.print(Panel(f"Scaffolding feature: [bold]{name}[/bold]"))

    # Validate feature name
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
        raise ValueError(
            f"Invalid feature name: {name}. "
            "Feature name must start with a letter and contain only "
            "letters, numbers, and underscores."
        )

    # Find project directory if not specified
    if project_dir is None:
        project_dir = _find_project_root()
        if project_dir is None:
            raise ValueError(
                "Not in a Uno project directory. Please specify the project directory "
                "or run this command from within a Uno project."
            )

    # Determine domain directory
    if domain:
        domain_dir = (
            project_dir / "src" / _get_project_name(project_dir) / "domain" / domain
        )
    else:
        # Use the feature name as subdirectory in domain
        domain_dir = project_dir / "src" / _get_project_name(project_dir) / "domain"

    # Create domain directory if it doesn't exist
    domain_dir.mkdir(parents=True, exist_ok=True)

    # Get template environment
    env = get_template_env()

    # Set up context for templates
    context = {
        "feature_name": name,
        "domain": domain,
        "project_name": _get_project_name(project_dir),
    }

    created_files = []

    if RICH_AVAILABLE:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Scaffolding feature components...", total=None)

            # Create components
            if create_entity:
                entity_file = _create_entity(name, domain_dir, env, context)
                created_files.append(entity_file)

            if create_model:
                model_file = _create_model(name, project_dir, env, context)
                created_files.append(model_file)

            if create_repository:
                repo_file = _create_repository(name, domain_dir, env, context)
                created_files.append(repo_file)

            if create_service:
                service_file = _create_service(name, domain_dir, env, context)
                created_files.append(service_file)

            if create_endpoint:
                endpoint_file = _create_endpoint(name, project_dir, env, context)
                created_files.append(endpoint_file)

            if create_tests:
                test_files = _create_tests(name, domain, project_dir, env, context)
                created_files.extend(test_files)

            progress.update(task, completed=True)
    else:
        print("Scaffolding feature components...")

        if create_entity:
            entity_file = _create_entity(name, domain_dir, env, context)
            created_files.append(entity_file)

        if create_model:
            model_file = _create_model(name, project_dir, env, context)
            created_files.append(model_file)

        if create_repository:
            repo_file = _create_repository(name, domain_dir, env, context)
            created_files.append(repo_file)

        if create_service:
            service_file = _create_service(name, domain_dir, env, context)
            created_files.append(service_file)

        if create_endpoint:
            endpoint_file = _create_endpoint(name, project_dir, env, context)
            created_files.append(endpoint_file)

        if create_tests:
            test_files = _create_tests(name, domain, project_dir, env, context)
            created_files.extend(test_files)

        print("Feature components created.")

    # Success message
    if RICH_AVAILABLE:
        console.print(
            f"[bold green]✓[/bold green] Feature '{name}' scaffolded successfully!"
        )

        table = Table(title="Created Files")
        table.add_column("Component", style="cyan")
        table.add_column("Path", style="green")

        for file_path in created_files:
            component_type = (
                file_path.stem.split("_")[-1]
                if "_" in file_path.stem
                else file_path.stem
            )
            relative_path = file_path.relative_to(project_dir)
            table.add_row(component_type, str(relative_path))

        console.print(table)
    else:
        print(f"Feature '{name}' scaffolded successfully!")
        print("\nCreated files:")
        for file_path in created_files:
            relative_path = file_path.relative_to(project_dir)
            print(f"  {relative_path}")

    return created_files


# Helper functions
def _create_project_directories(
    project_dir: Path, template_dir: Path, context: Dict[str, Any]
) -> None:
    """Create project directories based on the template."""
    # Get directories from template
    template_structure_file = template_dir / "structure.json"
    if template_structure_file.exists():
        with open(template_structure_file, "r") as f:
            structure = json.load(f)

        # Create directories from structure
        for directory in structure.get("directories", []):
            # Replace template variables in directory path
            dir_path = directory
            for key, value in context.items():
                dir_path = dir_path.replace(f"{{{key}}}", str(value))

            # Create directory
            (project_dir / dir_path).mkdir(parents=True, exist_ok=True)
    else:
        # Default directory structure
        default_dirs = [
            "src",
            f"src/{context['project_name']}",
            f"src/{context['project_name']}/api",
            f"src/{context['project_name']}/core",
            f"src/{context['project_name']}/domain",
            f"src/{context['project_name']}/infrastructure",
            "tests",
            "tests/unit",
            "tests/integration",
            "docs",
        ]

        for directory in default_dirs:
            (project_dir / directory).mkdir(parents=True, exist_ok=True)


def _create_project_files(
    project_dir: Path, template_dir: Path, env: Environment, context: Dict[str, Any]
) -> None:
    """Create project files based on the template."""
    # Get files from template
    template_structure_file = template_dir / "structure.json"
    if template_structure_file.exists():
        with open(template_structure_file, "r") as f:
            structure = json.load(f)

        # Create files from structure
        for file_info in structure.get("files", []):
            template_path = file_info["template"]
            output_path = file_info["output"]

            # Check conditions if any
            if "condition" in file_info:
                condition = file_info["condition"]
                key, value = condition.split("=")
                if str(context.get(key.strip())) != value.strip():
                    continue

            # Replace template variables in output path
            for key, value in context.items():
                output_path = output_path.replace(f"{{{key}}}", str(value))

            # Create parent directories if needed
            output_file = project_dir / output_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Render template
            try:
                template = env.get_template(
                    f"project/{template_dir.name}/{template_path}"
                )
                content = template.render(**context)

                with open(output_file, "w") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error rendering template {template_path}: {e}")
                # Continue with other files
                continue
    else:
        # Default files
        default_files = [
            ("project/standard/pyproject.toml.j2", "pyproject.toml"),
            ("project/standard/README.md.j2", "README.md"),
            ("project/standard/main.py.j2", f"src/{context['project_name']}/main.py"),
            (
                "project/standard/config.py.j2",
                f"src/{context['project_name']}/core/config.py",
            ),
            (
                "project/standard/dependencies.py.j2",
                f"src/{context['project_name']}/core/dependencies.py",
            ),
        ]

        for template_path, output_path in default_files:
            # Create parent directories if needed
            output_file = project_dir / output_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Render template
            try:
                template = env.get_template(template_path)
                content = template.render(**context)

                with open(output_file, "w") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error rendering template {template_path}: {e}")
                # Continue with other files
                continue


def _find_project_root() -> Optional[Path]:
    """Find the root directory of a Uno project from the current directory."""
    current_dir = Path.cwd()

    # Check current directory and all parents
    while current_dir != current_dir.parent:
        # Check for markers of a Uno project
        if (current_dir / "pyproject.toml").exists() and (current_dir / "src").exists():
            # Try to find a src/project_name directory
            src_dir = current_dir / "src"
            if src_dir.exists() and src_dir.is_dir():
                # Look for a subdirectory with a main.py file
                for subdir in src_dir.glob("*"):
                    if subdir.is_dir() and (subdir / "main.py").exists():
                        return current_dir

            # Fallback: just return the directory with pyproject.toml
            return current_dir

        # Move up to parent directory
        current_dir = current_dir.parent

    # Not found
    return None


def _get_project_name(project_dir: Path) -> str:
    """Get the project name from a project directory."""
    # Try to find it from src directory
    src_dir = project_dir / "src"
    if src_dir.exists() and src_dir.is_dir():
        # Look for a subdirectory with a main.py file
        for subdir in src_dir.glob("*"):
            if subdir.is_dir() and (subdir / "main.py").exists():
                return subdir.name

    # Fallback: use the directory name
    return project_dir.name


def _create_entity(
    name: str, domain_dir: Path, env: Environment, context: Dict[str, Any]
) -> Path:
    """Create an entity model file."""
    output_file = domain_dir / f"{name.lower()}_entity.py"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try to use the domain entity template first
        template_path = "feature/domain_entity.py.j2"
        if not (TEMPLATES_DIR / template_path).exists():
            # Fall back to the basic template
            template_path = "feature/entity.py.j2"

        template = env.get_template(template_path)
        content = template.render(**context)

        with open(output_file, "w") as f:
            f.write(content)

        return output_file
    except Exception as e:
        logger.error(f"Error creating entity: {e}")
        raise


def _create_repository(
    name: str, domain_dir: Path, env: Environment, context: Dict[str, Any]
) -> Path:
    """Create a repository file."""
    output_file = domain_dir / f"{name.lower()}_repository.py"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try to use the domain repository template first
        template_path = "feature/domain_repository.py.j2"
        if not (TEMPLATES_DIR / template_path).exists():
            # Fall back to the basic template
            template_path = "feature/repository.py.j2"

        template = env.get_template(template_path)
        content = template.render(**context)

        with open(output_file, "w") as f:
            f.write(content)

        return output_file
    except Exception as e:
        logger.error(f"Error creating repository: {e}")
        raise


def _create_service(
    name: str, domain_dir: Path, env: Environment, context: Dict[str, Any]
) -> Path:
    """Create a service file."""
    output_file = domain_dir / f"{name.lower()}_service.py"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try to use the domain service template first
        template_path = "feature/domain_service.py.j2"
        if not (TEMPLATES_DIR / template_path).exists():
            # Fall back to the basic template
            template_path = "feature/service.py.j2"

        template = env.get_template(template_path)
        content = template.render(**context)

        with open(output_file, "w") as f:
            f.write(content)

        return output_file
    except Exception as e:
        logger.error(f"Error creating service: {e}")
        raise


def _create_endpoint(
    name: str, project_dir: Path, env: Environment, context: Dict[str, Any]
) -> Path:
    """Create an API endpoint file."""
    api_dir = project_dir / "src" / context["project_name"] / "api"
    output_file = api_dir / f"{name.lower()}_endpoints.py"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try to use the domain endpoints template first
        template_path = "feature/domain_endpoints.py.j2"
        if not (TEMPLATES_DIR / template_path).exists():
            # Fall back to the basic template
            template_path = "feature/endpoint.py.j2"

        template = env.get_template(template_path)
        content = template.render(**context)

        with open(output_file, "w") as f:
            f.write(content)

        return output_file
    except Exception as e:
        logger.error(f"Error creating endpoint: {e}")
        raise


def _create_tests(
    name: str,
    domain: Optional[str],
    project_dir: Path,
    env: Environment,
    context: Dict[str, Any],
) -> list[Path]:
    """Create test files."""
    test_files = []

    # Unit tests
    unit_test_dir = project_dir / "tests" / "unit"
    if domain:
        unit_test_dir = unit_test_dir / domain

    unit_test_file = unit_test_dir / f"test_{name.lower()}.py"
    unit_test_dir.mkdir(parents=True, exist_ok=True)

    try:
        template = env.get_template("feature/unit_test.py.j2")
        content = template.render(**context)

        with open(unit_test_file, "w") as f:
            f.write(content)

        test_files.append(unit_test_file)
    except Exception as e:
        logger.error(f"Error creating unit test: {e}")
        # Continue with other test files

    # Integration tests
    integration_test_dir = project_dir / "tests" / "integration"
    integration_test_file = integration_test_dir / f"test_{name.lower()}_api.py"
    integration_test_dir.mkdir(parents=True, exist_ok=True)

    try:
        template = env.get_template("feature/integration_test.py.j2")
        content = template.render(**context)

        with open(integration_test_file, "w") as f:
            f.write(content)

        test_files.append(integration_test_file)
    except Exception as e:
        logger.error(f"Error creating integration test: {e}")
        # Continue

    return test_files


# Command-line interface
try:
    import typer

    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

if TYPER_AVAILABLE:
    scaffold_app = typer.Typer(help="Scaffold Uno projects and features")

    @scaffold_app.command("new")
    def new_project_command(
        name: str = typer.Argument(..., help="Project name"),
        template: str = typer.Option(
            "standard", "--template", "-t", help="Project template to use"
        ),
        database: str = typer.Option(
            "postgresql", "--database", "-d", help="Database backend"
        ),
        api: bool = typer.Option(True, "--api/--no-api", help="Include API setup"),
        domain_driven: bool = typer.Option(
            True, "--ddd/--no-ddd", help="Use domain-driven design"
        ),
        output_dir: Optional[Path] = typer.Option(
            None, "--output", "-o", help="Output directory"
        ),
    ):
        """Create a new Uno project."""
        try:
            scaffold_project(
                name=name,
                template=template,
                database=database,
                api=api,
                domain_driven=domain_driven,
                output_dir=output_dir,
            )
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
            else:
                print(f"Error: {str(e)}")
            sys.exit(1)

    @scaffold_app.command("feature")
    def feature_command(
        name: str = typer.Argument(..., help="Feature name"),
        domain: Optional[str] = typer.Option(
            None, "--domain", "-d", help="Domain name"
        ),
        no_entity: bool = typer.Option(
            False, "--no-entity", help="Skip entity creation"
        ),
        no_model: bool = typer.Option(
            False, "--no-model", help="Skip database model creation"
        ),
        no_repository: bool = typer.Option(
            False, "--no-repository", help="Skip repository creation"
        ),
        no_service: bool = typer.Option(
            False, "--no-service", help="Skip service creation"
        ),
        no_endpoint: bool = typer.Option(
            False, "--no-endpoint", help="Skip endpoint creation"
        ),
        no_tests: bool = typer.Option(False, "--no-tests", help="Skip test creation"),
        project_dir: Optional[Path] = typer.Option(
            None, "--project", "-p", help="Project directory"
        ),
    ):
        """Scaffold a complete feature with all required components."""
        try:
            scaffold_feature(
                name=name,
                domain=domain,
                create_entity=not no_entity,
                create_model=not no_model,
                create_repository=not no_repository,
                create_service=not no_service,
                create_endpoint=not no_endpoint,
                create_tests=not no_tests,
                project_dir=project_dir,
            )
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
            else:
                print(f"Error: {str(e)}")
            sys.exit(1)


def setup_parser(subparsers):
    """Set up the argument parser for the scaffold command."""
    scaffold_parser = subparsers.add_parser(
        "scaffold", help="Scaffold projects and features"
    )
    scaffold_subparsers = scaffold_parser.add_subparsers(dest="subcommand")

    # New project command
    new_parser = scaffold_subparsers.add_parser("new", help="Create a new Uno project")
    new_parser.add_argument("name", help="Project name")
    new_parser.add_argument(
        "--template", "-t", default="standard", help="Project template to use"
    )
    new_parser.add_argument(
        "--database", "-d", default="postgresql", help="Database backend"
    )
    new_parser.add_argument("--no-api", action="store_true", help="Skip API setup")
    new_parser.add_argument(
        "--no-ddd", action="store_true", help="Skip domain-driven design"
    )
    new_parser.add_argument("--output", "-o", type=Path, help="Output directory")

    # Feature command
    feature_parser = scaffold_subparsers.add_parser(
        "feature", help="Scaffold a feature"
    )
    feature_parser.add_argument("name", help="Feature name")
    feature_parser.add_argument("--domain", "-d", help="Domain name")
    feature_parser.add_argument(
        "--no-entity", action="store_true", help="Skip entity creation"
    )
    feature_parser.add_argument(
        "--no-model", action="store_true", help="Skip database model creation"
    )
    feature_parser.add_argument(
        "--no-repository", action="store_true", help="Skip repository creation"
    )
    feature_parser.add_argument(
        "--no-service", action="store_true", help="Skip service creation"
    )
    feature_parser.add_argument(
        "--no-endpoint", action="store_true", help="Skip endpoint creation"
    )
    feature_parser.add_argument(
        "--no-tests", action="store_true", help="Skip test creation"
    )
    feature_parser.add_argument("--project", "-p", type=Path, help="Project directory")


def handle_command(args):
    """Handle the scaffold command."""
    if args.subcommand == "new":
        scaffold_project(
            name=args.name,
            template=args.template,
            database=args.database,
            api=not args.no_api,
            domain_driven=not args.no_ddd,
            output_dir=args.output,
        )
    elif args.subcommand == "feature":
        scaffold_feature(
            name=args.name,
            domain=args.domain,
            create_entity=not args.no_entity,
            create_model=not args.no_model if hasattr(args, "no_model") else True,
            create_repository=not args.no_repository,
            create_service=not args.no_service,
            create_endpoint=not args.no_endpoint,
            create_tests=not args.no_tests,
            project_dir=args.project,
        )
    else:
        print("Unknown subcommand. Use 'scaffold new' or 'scaffold feature'.")


if __name__ == "__main__":
    if TYPER_AVAILABLE:
        scaffold_app()
    else:
        print("Typer not available. Please install it with: pip install typer rich")
        sys.exit(1)
