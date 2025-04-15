"""
HTML renderer for documentation.

This module provides a renderer that transforms documentation schemas into HTML
format for use in documentation sites, providing a rich and interactive
experience.
"""

import os
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape

from uno.core.docs.schema import (
    DocSchema, EndpointDoc, ModelDoc, TagDoc, SecuritySchemeDoc,
    ParameterDoc, FieldDoc, ExampleDoc, DocStatus, ParameterLocation
)
from uno.core.docs.renderers.base import DocRenderer


class HtmlRenderer(DocRenderer):
    """Renderer for HTML documentation."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the HTML renderer.
        
        Args:
            template_dir: Directory containing HTML templates. If None, default templates are used.
        """
        # Find templates directory
        if template_dir is None:
            # Use default templates
            template_dir = os.path.join(os.path.dirname(__file__), "templates", "html")
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self.env.filters['slugify'] = self._slugify
        self.env.filters['status_class'] = self._status_to_css_class
        self.env.filters['method_class'] = self._method_to_css_class
        self.env.filters['json_pretty'] = self._json_pretty
        self.env.filters['md_to_html'] = self._md_to_html
        self.env.filters['param_location_icon'] = self._param_location_icon
        
        # Register custom tests
        self.env.tests['list_type'] = self._is_list_type
        self.env.tests['dict_type'] = self._is_dict_type
        self.env.tests['optional_type'] = self._is_optional_type
    
    def render(self, schema: DocSchema, config: Any) -> Dict[str, str]:
        """
        Render documentation schema as HTML.
        
        Args:
            schema: Documentation schema to render
            config: Configuration for rendering
            
        Returns:
            Dictionary of filenames to rendered content
        """
        result = {}
        
        # Set up common template variables
        template_vars = {
            "schema": schema,
            "config": config,
            "endpoints_by_tag": self._group_endpoints_by_tag(schema.endpoints),
            "models_by_letter": self._group_models_by_letter(schema.models),
            "models_by_name": {model.name: model for model in schema.models},
            "tags_by_name": {tag.name: tag for tag in schema.tags},
            "static_prefix": "../static" if config.include_source_links else "static"
        }
        
        # Render index page
        template = self.env.get_template("index.html")
        result["index.html"] = template.render(**template_vars)
        
        # Render endpoints by tag
        endpoints_dir = "endpoints"
        for tag, endpoints in template_vars["endpoints_by_tag"].items():
            tag_slug = self._slugify(tag)
            tag_path = f"{endpoints_dir}/{tag_slug}.html"
            
            template = self.env.get_template("endpoints_tag.html")
            result[tag_path] = template.render(
                tag=tag,
                endpoints=endpoints,
                **template_vars
            )
        
        # Render models by letter
        models_dir = "models"
        for letter, models in template_vars["models_by_letter"].items():
            letter_path = f"{models_dir}/{letter.lower()}.html"
            
            template = self.env.get_template("models_letter.html")
            result[letter_path] = template.render(
                letter=letter,
                models=models,
                **template_vars
            )
        
        # Render search page
        template = self.env.get_template("search.html")
        result["search.html"] = template.render(**template_vars)
        
        # Render static resources (CSS, JS, etc.)
        static_dir = "static"
        
        # CSS files
        css_files = ["styles.css", "normalize.css", "prism.css"]
        for css_file in css_files:
            css_template = self.env.get_template(f"static/{css_file}")
            result[f"{static_dir}/{css_file}"] = css_template.render()
        
        # JavaScript files
        js_files = ["main.js", "search.js", "prism.js", "api.js"]
        for js_file in js_files:
            js_template = self.env.get_template(f"static/{js_file}")
            result[f"{static_dir}/{js_file}"] = js_template.render()
        
        # Add documentation data as JSON for search
        result[f"{static_dir}/docs-data.js"] = self._generate_docs_data_js(schema)
        
        return result
    
    def _generate_docs_data_js(self, schema: DocSchema) -> str:
        """Generate JavaScript file with documentation data for searching."""
        # Create search index
        search_data = {
            "endpoints": [],
            "models": [],
            "version": schema.version
        }
        
        # Add endpoints to search index
        for endpoint in schema.endpoints:
            search_data["endpoints"].append({
                "path": endpoint.path,
                "method": endpoint.method,
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "url": f"endpoints/{self._slugify(endpoint.tags[0] if endpoint.tags else 'Default')}.html#{self._slugify(endpoint.method + '_' + endpoint.path)}"
            })
        
        # Add models to search index
        for model in schema.models:
            search_data["models"].append({
                "name": model.name,
                "description": model.description,
                "fields": [field.name for field in model.fields],
                "tags": model.tags,
                "url": f"models/{model.name[0].lower()}.html#{self._slugify(model.name)}"
            })
        
        # Generate JavaScript
        return f"window.docsData = {json.dumps(search_data, indent=2)};"
    
    def _group_endpoints_by_tag(self, endpoints: List[EndpointDoc]) -> Dict[str, List[EndpointDoc]]:
        """Group endpoints by tag."""
        result = {}
        
        for endpoint in endpoints:
            # Use first tag, or "Default" if no tags
            tag = endpoint.tags[0] if endpoint.tags else "Default"
            
            if tag not in result:
                result[tag] = []
                
            result[tag].append(endpoint)
        
        # Sort endpoints within each tag by path
        for tag in result:
            result[tag] = sorted(result[tag], key=lambda e: e.path)
        
        return result
    
    def _group_models_by_letter(self, models: List[ModelDoc]) -> Dict[str, List[ModelDoc]]:
        """Group models by first letter."""
        result = {}
        
        for model in models:
            letter = model.name[0].upper()
            
            if letter not in result:
                result[letter] = []
                
            result[letter].append(model)
        
        # Sort models within each letter by name
        for letter in result:
            result[letter] = sorted(result[letter], key=lambda m: m.name)
        
        return result
    
    def _slugify(self, text: str) -> str:
        """Convert text to slug format."""
        # Replace non-alphanumeric characters with hyphens
        text = re.sub(r'[^a-zA-Z0-9]+', '-', text)
        # Remove leading/trailing hyphens
        text = text.strip('-')
        # Convert to lowercase
        return text.lower()
    
    def _status_to_css_class(self, status: DocStatus) -> str:
        """Convert status to CSS class name."""
        status_map = {
            DocStatus.STABLE: "status-stable",
            DocStatus.BETA: "status-beta",
            DocStatus.ALPHA: "status-alpha",
            DocStatus.DEPRECATED: "status-deprecated",
            DocStatus.EXPERIMENTAL: "status-experimental"
        }
        return status_map.get(status, "status-unknown")
    
    def _method_to_css_class(self, method: str) -> str:
        """Convert HTTP method to CSS class name."""
        method_map = {
            "GET": "method-get",
            "POST": "method-post",
            "PUT": "method-put",
            "DELETE": "method-delete",
            "PATCH": "method-patch",
            "OPTIONS": "method-options",
            "HEAD": "method-head"
        }
        return method_map.get(method.upper(), "method-unknown")
    
    def _param_location_icon(self, location: ParameterLocation) -> str:
        """Get an icon for parameter location."""
        icon_map = {
            ParameterLocation.PATH: '<i class="bi bi-link"></i>',
            ParameterLocation.QUERY: '<i class="bi bi-question-circle"></i>',
            ParameterLocation.HEADER: '<i class="bi bi-list"></i>',
            ParameterLocation.COOKIE: '<i class="bi bi-cookie"></i>',
            ParameterLocation.BODY: '<i class="bi bi-body-text"></i>'
        }
        return icon_map.get(location, '<i class="bi bi-question"></i>')
    
    def _json_pretty(self, value: Any) -> str:
        """Format value as pretty-printed JSON."""
        return json.dumps(value, indent=2, sort_keys=False)
    
    def _md_to_html(self, markdown: str) -> str:
        """Convert Markdown to HTML."""
        try:
            import markdown
            return markdown.markdown(markdown)
        except ImportError:
            # Fallback to simple conversion if markdown module is not available
            html = markdown
            # Convert headers
            html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            # Convert bold and italic
            html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
            html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
            # Convert code blocks
            html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
            # Convert inline code
            html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
            # Convert paragraphs
            html = re.sub(r'\n\n(.*?)\n\n', r'<p>\1</p>\n\n', html, flags=re.DOTALL)
            return html
    
    def _is_list_type(self, type_str: str) -> bool:
        """Check if a type string represents a list type."""
        return type_str.startswith('List[') or type_str.startswith('list[')
    
    def _is_dict_type(self, type_str: str) -> bool:
        """Check if a type string represents a dictionary type."""
        return type_str.startswith('Dict[') or type_str.startswith('dict[')
    
    def _is_optional_type(self, type_str: str) -> bool:
        """Check if a type string represents an optional type."""
        return type_str.startswith('Optional[') or type_str.startswith('Union[') and 'None' in type_str