"""
Documentation generator for Uno applications.

This module provides a documentation generator for Uno applications, which can
extract API documentation, generate diagrams, and more.
"""

import inspect
import importlib
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, Callable
import re

try:
    import docstring_parser

    DOCSTRING_PARSER_AVAILABLE = True
except ImportError:
    DOCSTRING_PARSER_AVAILABLE = False

try:
    import markdown
    import pygments

    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False


logger = logging.getLogger("uno.docs")


class DocGenerator:
    """Generator for Uno application documentation."""

    def __init__(
        self,
        module_name: str,
        output_dir: Optional[Union[str, Path]] = None,
        include_private: bool = False,
        include_source: bool = True,
        include_modules: list[str] | None = None,
        exclude_modules: list[str] | None = None,
        template_dir: Optional[Union[str, Path]] = None,
    ):
        """Initialize the documentation generator.

        Args:
            module_name: Name of the root module
            output_dir: Output directory for documentation
            include_private: Whether to include private members
            include_source: Whether to include source code
            include_modules: Optional list of modules to include
            exclude_modules: Optional list of modules to exclude
            template_dir: Optional directory with templates
        """
        self.module_name = module_name
        self.output_dir = Path(output_dir) if output_dir else Path("docs")
        self.include_private = include_private
        self.include_source = include_source
        self.include_modules = include_modules or []
        self.exclude_modules = exclude_modules or []
        self.template_dir = Path(template_dir) if template_dir else None

        # Initialize module cache
        self.modules = {}
        self.classes = {}
        self.functions = {}

        # Load module
        try:
            self.root_module = importlib.import_module(module_name)
            self.modules[module_name] = self.root_module
        except ImportError as e:
            logger.error(f"Error loading module {module_name}: {str(e)}")
            raise

    def generate_docs(self) -> None:
        """Generate documentation for the module."""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Discover modules
        self._discover_modules()

        # Generate module documentation
        for module_name, module in self.modules.items():
            self._generate_module_docs(module_name, module)

        # Generate index
        self._generate_index()

        # Generate search index
        self._generate_search_index()

        # Copy assets
        self._copy_assets()

        logger.info(f"Documentation generated in {self.output_dir}")

    def _discover_modules(self) -> None:
        """Discover all modules in the package."""
        # Find all submodules
        for finder, name, is_pkg in pkgutil.iter_modules(
            self.root_module.__path__, f"{self.module_name}."
        ):
            # Check if module should be included
            if self.include_modules and not any(
                name.startswith(m) for m in self.include_modules
            ):
                continue

            # Check if module should be excluded
            if self.exclude_modules and any(
                name.startswith(m) for m in self.exclude_modules
            ):
                continue

            try:
                module = importlib.import_module(name)
                self.modules[name] = module

                # Find classes and functions
                for obj_name, obj in inspect.getmembers(module):
                    # Skip private members if not included
                    if not self.include_private and obj_name.startswith("_"):
                        continue

                    # Handle classes
                    if inspect.isclass(obj) and obj.__module__ == name:
                        self.classes[f"{name}.{obj_name}"] = obj

                    # Handle functions
                    elif inspect.isfunction(obj) and obj.__module__ == name:
                        self.functions[f"{name}.{obj_name}"] = obj
            except ImportError as e:
                logger.warning(f"Error importing module {name}: {str(e)}")

    def _generate_module_docs(self, module_name: str, module: Any) -> None:
        """Generate documentation for a module.

        Args:
            module_name: Name of the module
            module: Module object
        """
        # Create module directory
        module_dir = self.output_dir / module_name.replace(".", "/")
        module_dir.mkdir(parents=True, exist_ok=True)

        # Create module index file
        index_path = module_dir / "index.md"

        with open(index_path, "w") as f:
            # Title
            f.write(f"# {module_name}\n\n")

            # Module docstring
            if module.__doc__:
                f.write(f"{module.__doc__.strip()}\n\n")

            # Classes
            classes = [
                cls
                for name, cls in self.classes.items()
                if name.startswith(f"{module_name}.")
            ]

            if classes:
                f.write("## Classes\n\n")
                for cls in classes:
                    cls_name = cls.__name__
                    cls_doc = cls.__doc__.strip() if cls.__doc__ else ""
                    f.write(f"- [{cls_name}]({cls_name}.md): {cls_doc.split('.')[0]}\n")
                f.write("\n")

            # Functions
            functions = [
                func
                for name, func in self.functions.items()
                if name.startswith(f"{module_name}.")
            ]

            if functions:
                f.write("## Functions\n\n")
                for func in functions:
                    func_name = func.__name__
                    func_doc = func.__doc__.strip() if func.__doc__ else ""
                    f.write(
                        f"- [{func_name}]({func_name}.md): {func_doc.split('.')[0]}\n"
                    )
                f.write("\n")

        # Generate class documentation
        for cls_name, cls in self.classes.items():
            if cls_name.startswith(f"{module_name}."):
                self._generate_class_docs(cls, module_dir)

        # Generate function documentation
        for func_name, func in self.functions.items():
            if func_name.startswith(f"{module_name}."):
                self._generate_function_docs(func, module_dir)

    def _generate_class_docs(self, cls: Any, module_dir: Path) -> None:
        """Generate documentation for a class.

        Args:
            cls: Class object
            module_dir: Module directory
        """
        # Create class file
        cls_path = module_dir / f"{cls.__name__}.md"

        with open(cls_path, "w") as f:
            # Title
            f.write(f"# {cls.__name__}\n\n")

            # Class docstring
            if cls.__doc__:
                f.write(f"{cls.__doc__.strip()}\n\n")

            # Inheritance
            if cls.__bases__ and cls.__bases__[0] != object:
                base_classes = ", ".join(
                    b.__name__ for b in cls.__bases__ if b != object
                )
                f.write(f"Inherits from: {base_classes}\n\n")

            # Methods
            methods = []
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                # Skip private methods if not included
                if (
                    not self.include_private
                    and name.startswith("_")
                    and name != "__init__"
                ):
                    continue

                methods.append((name, method))

            if methods:
                f.write("## Methods\n\n")
                for method_name, method in methods:
                    f.write(f"### {method_name}\n\n")

                    # Method signature
                    sig = inspect.signature(method)
                    f.write(f"```python\n{method_name}{sig}\n```\n\n")

                    # Method docstring
                    if method.__doc__:
                        f.write(f"{method.__doc__.strip()}\n\n")

                    # Include source code
                    if self.include_source:
                        try:
                            source = inspect.getsource(method)
                            f.write("**Source:**\n\n")
                            f.write(f"```python\n{source}\n```\n\n")
                        except (IOError, TypeError):
                            pass

            # Class source code
            if self.include_source:
                try:
                    source = inspect.getsource(cls)
                    f.write("## Source\n\n")
                    f.write(f"```python\n{source}\n```\n")
                except (IOError, TypeError):
                    pass

    def _generate_function_docs(self, func: Any, module_dir: Path) -> None:
        """Generate documentation for a function.

        Args:
            func: Function object
            module_dir: Module directory
        """
        # Create function file
        func_path = module_dir / f"{func.__name__}.md"

        with open(func_path, "w") as f:
            # Title
            f.write(f"# {func.__name__}\n\n")

            # Function signature
            sig = inspect.signature(func)
            f.write(f"```python\n{func.__name__}{sig}\n```\n\n")

            # Function docstring
            if func.__doc__:
                # Parse docstring
                if DOCSTRING_PARSER_AVAILABLE:
                    try:
                        doc = docstring_parser.parse(func.__doc__)

                        # Description
                        if doc.short_description:
                            f.write(f"{doc.short_description}\n\n")

                        if doc.long_description:
                            f.write(f"{doc.long_description}\n\n")

                        # Parameters
                        if doc.params:
                            f.write("### Parameters\n\n")
                            for param in doc.params:
                                param_type = (
                                    f": `{param.type_name}`" if param.type_name else ""
                                )
                                f.write(f"- `{param.arg_name}`{param_type}")
                                if param.description:
                                    f.write(f" - {param.description}")
                                f.write("\n")
                            f.write("\n")

                        # Returns
                        if doc.returns:
                            f.write("### Returns\n\n")
                            return_type = (
                                f": `{doc.returns.type_name}`"
                                if doc.returns.type_name
                                else ""
                            )
                            f.write(f"{return_type} {doc.returns.description}\n\n")

                        # Raises
                        if doc.raises:
                            f.write("### Raises\n\n")
                            for raised in doc.raises:
                                f.write(
                                    f"- `{raised.type_name}`: {raised.description}\n"
                                )
                            f.write("\n")
                    except Exception as e:
                        # Fallback to raw docstring
                        f.write(f"{func.__doc__.strip()}\n\n")
                else:
                    # Raw docstring
                    f.write(f"{func.__doc__.strip()}\n\n")

            # Function source code
            if self.include_source:
                try:
                    source = inspect.getsource(func)
                    f.write("## Source\n\n")
                    f.write(f"```python\n{source}\n```\n")
                except (IOError, TypeError):
                    pass

    def _generate_index(self) -> None:
        """Generate documentation index."""
        index_path = self.output_dir / "index.md"

        with open(index_path, "w") as f:
            # Title
            f.write(f"# {self.module_name} Documentation\n\n")

            # Root module docstring
            if self.root_module.__doc__:
                f.write(f"{self.root_module.__doc__.strip()}\n\n")

            # Modules
            f.write("## Modules\n\n")
            for module_name in sorted(self.modules.keys()):
                if module_name == self.module_name:
                    continue

                relative_name = (
                    module_name[len(self.module_name) + 1 :]
                    if module_name.startswith(f"{self.module_name}.")
                    else module_name
                )
                module_doc = self.modules[module_name].__doc__
                doc_summary = module_doc.strip().split(".")[0] if module_doc else ""

                f.write(
                    f"- [{relative_name}]({module_name.replace('.', '/')}/index.md): {doc_summary}\n"
                )

    def _generate_search_index(self) -> None:
        """Generate search index for documentation."""
        import json

        search_index = []

        # Index modules
        for module_name, module in self.modules.items():
            module_doc = module.__doc__ or ""
            search_index.append(
                {
                    "type": "module",
                    "name": module_name,
                    "path": f"{module_name.replace('.', '/')}/index.md",
                    "summary": module_doc.strip().split(".")[0] if module_doc else "",
                    "content": module_doc.strip(),
                }
            )

        # Index classes
        for cls_name, cls in self.classes.items():
            module_name = cls.__module__
            cls_doc = cls.__doc__ or ""
            search_index.append(
                {
                    "type": "class",
                    "name": cls.__name__,
                    "path": f"{module_name.replace('.', '/')}/{cls.__name__}.md",
                    "module": module_name,
                    "summary": cls_doc.strip().split(".")[0] if cls_doc else "",
                    "content": cls_doc.strip(),
                }
            )

        # Index functions
        for func_name, func in self.functions.items():
            module_name = func.__module__
            func_doc = func.__doc__ or ""
            search_index.append(
                {
                    "type": "function",
                    "name": func.__name__,
                    "path": f"{module_name.replace('.', '/')}/{func.__name__}.md",
                    "module": module_name,
                    "summary": func_doc.strip().split(".")[0] if func_doc else "",
                    "content": func_doc.strip(),
                }
            )

        # Write search index
        search_index_path = self.output_dir / "search_index.json"
        with open(search_index_path, "w") as f:
            json.dump(search_index, f, indent=2)

    def _copy_assets(self) -> None:
        """Copy assets to the output directory."""
        assets_dir = self.output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        # Copy standard assets if templates are available
        if self.template_dir:
            import shutil

            assets_src = self.template_dir / "assets"
            if assets_src.exists():
                for asset in assets_src.glob("**/*"):
                    if asset.is_file():
                        rel_path = asset.relative_to(assets_src)
                        dst_path = assets_dir / rel_path
                        dst_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(asset, dst_path)

        # Create CSS file
        css_path = assets_dir / "styles.css"
        with open(css_path, "w") as f:
            f.write(
                """
/* Base styles */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 1rem;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 {
    font-size: 2rem;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
}

h2 {
    font-size: 1.5rem;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
}

/* Code blocks */
pre {
    background-color: #f6f8fa;
    border-radius: 3px;
    padding: 16px;
    overflow: auto;
}

code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
    background-color: #f6f8fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
}

/* Navigation */
nav {
    background-color: #f6f8fa;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 3px;
}

nav ul {
    list-style-type: none;
    padding: 0;
    margin: 0;
}

nav li {
    display: inline-block;
    margin-right: 1rem;
}

/* Search */
.search {
    margin-bottom: 1rem;
}

.search input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 3px;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
    body {
        background-color: #0d1117;
        color: #c9d1d9;
    }

    h1, h2 {
        border-bottom-color: #30363d;
    }

    pre, code {
        background-color: #161b22;
    }

    nav {
        background-color: #161b22;
    }
}
            """
            )

        # Create JavaScript file
        js_path = assets_dir / "script.js"
        with open(js_path, "w") as f:
            f.write(
                """
document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            
            // Load search index
            fetch('/assets/search_index.json')
                .then(response => response.json())
                .then(searchIndex => {
                    // Filter results
                    const results = searchIndex.filter(item => {
                        return item.name.toLowerCase().includes(query) || 
                               item.summary.toLowerCase().includes(query) ||
                               item.content.toLowerCase().includes(query);
                    });
                    
                    // Display results
                    const resultsContainer = document.getElementById('search-results');
                    if (resultsContainer) {
                        if (query.length < 2) {
                            resultsContainer.innerHTML = '';
                            return;
                        }
                        
                        if (results.length === 0) {
                            resultsContainer.innerHTML = '<p>No results found</p>';
                            return;
                        }
                        
                        let html = '<ul>';
                        for (const result of results) {
                            html += `<li><a href="/${result.path}">${result.name}</a> (${result.type})`;
                            if (result.summary) {
                                html += `: ${result.summary}`;
                            }
                            html += '</li>';
                        }
                        html += '</ul>';
                        
                        resultsContainer.innerHTML = html;
                    }
                });
        });
    }
});
            """
            )


# Helper function for module discovery
try:
    import pkgutil
except ImportError:

    class _PkgutilHelper:
        def iter_modules(self, path, prefix):
            return []

    pkgutil = _PkgutilHelper()


def generate_module_docs(
    module_name: str,
    output_dir: Optional[Union[str, Path]] = None,
    include_private: bool = False,
    include_source: bool = True,
    include_modules: list[str] | None = None,
    exclude_modules: list[str] | None = None,
    template_dir: Optional[Union[str, Path]] = None,
) -> None:
    """Generate documentation for a module.

    Args:
        module_name: Name of the root module
        output_dir: Output directory for documentation
        include_private: Whether to include private members
        include_source: Whether to include source code
        include_modules: Optional list of modules to include
        exclude_modules: Optional list of modules to exclude
        template_dir: Optional directory with templates
    """
    generator = DocGenerator(
        module_name=module_name,
        output_dir=output_dir,
        include_private=include_private,
        include_source=include_source,
        include_modules=include_modules,
        exclude_modules=exclude_modules,
        template_dir=template_dir,
    )

    generator.generate_docs()
