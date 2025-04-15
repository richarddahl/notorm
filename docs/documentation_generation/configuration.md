# Documentation Generator Configuration

The Uno documentation generator provides extensive configuration options to customize how documentation is generated and rendered.

## Configuration Options

The `DocGeneratorConfig` class provides the following configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | str | "API Documentation" | Title for the documentation |
| `description` | str | "Generated API documentation" | Description for the documentation |
| `version` | str | "1.0.0" | Version for the documentation |
| `formats` | List[DocFormat] | [MARKDOWN, OPENAPI] | Output formats for the documentation |
| `output_dir` | str | "docs/api" | Output directory for the documentation |
| `include_source_links` | bool | True | Include links to source code |
| `include_examples` | bool | True | Include examples in the documentation |
| `example_depth` | int | 2 | Depth of examples to include |
| `include_internal` | bool | False | Include internal components |
| `include_deprecated` | bool | True | Include deprecated components |
| `include_beta` | bool | True | Include beta components |
| `include_alpha` | bool | True | Include alpha components |
| `include_experimental` | bool | True | Include experimental components |
| `modules_to_document` | List[str] | [] | Modules to document |
| `url_base` | Optional[str] | None | Base URL for the documentation |
| `logo_url` | Optional[str] | None | URL for the logo to use |
| `css_urls` | List[str] | [] | CSS URLs for HTML documentation |
| `js_urls` | List[str] | [] | JavaScript URLs for HTML documentation |
| `extra_templates` | Dict[str, str] | {} | Extra templates for custom rendering |
| `metadata` | Dict[str, Any] | {} | Additional metadata for the documentation |

## Basic Configuration

Here's a basic configuration example:

```python
from uno.core.docs.generator import DocGeneratorConfig, DocFormat

config = DocGeneratorConfig(```

title="My API Documentation",
description="Documentation for my API",
version="1.0.0",
formats=[DocFormat.MARKDOWN, DocFormat.OPENAPI],
output_dir="docs/api",
modules_to_document=["my_app.api", "my_app.models"]
```
)
```

## Output Formats

The documentation generator supports multiple output formats:

```python
from uno.core.docs.generator import DocFormat

# Generate all supported formats
formats = [```

DocFormat.MARKDOWN,  # Markdown documentation
DocFormat.OPENAPI,   # OpenAPI (Swagger) specification
DocFormat.HTML,      # HTML documentation
DocFormat.ASCIIDOC   # AsciiDoc documentation
```
]
```

## Filtering Components

You can control which components are included in the documentation:

```python
config = DocGeneratorConfig(```

# Include internal components (prefixed with underscore)
include_internal=True,
``````

```
```

# Skip deprecated components
include_deprecated=False,
``````

```
```

# Only include stable components
include_beta=False,
include_alpha=False,
include_experimental=False
```
)
```

## Examples Configuration

Control how examples are included in the documentation:

```python
config = DocGeneratorConfig(```

# Include examples
include_examples=True,
``````

```
```

# Set the depth for nested examples
example_depth=3
```
)
```

## HTML Customization

For HTML documentation, you can customize the appearance:

```python
config = DocGeneratorConfig(```

# Set base URL for documentation
url_base="https://docs.example.com/api",
``````

```
```

# Add logo
logo_url="https://example.com/logo.png",
``````

```
```

# Add custom CSS and JavaScript
css_urls=[```

"https://cdn.example.com/styles.css",
"/custom/styles.css"
```
],
js_urls=[```

"https://cdn.example.com/scripts.js",
"/custom/scripts.js"
```
]
```
)
```

## Custom Templates

You can provide custom templates for rendering:

```python
config = DocGeneratorConfig(```

extra_templates={```

"markdown/model.md": "path/to/custom/model_template.md",
"html/index.html": "path/to/custom/index_template.html"
```
}
```
)
```

## Metadata

Add additional metadata to the documentation:

```python
config = DocGeneratorConfig(```

metadata={```

"organization": "Example Corp",
"contact_email": "api@example.com",
"license": "MIT",
"repository": "https://github.com/example/myapi"
```
}
```
)
```

## Command Line Configuration

When using the command-line interface, the same configuration options are available as command-line arguments:

```bash
python -m uno.core.docs.cli \```

--title "My API Documentation" \
--description "Documentation for my API" \
--version "1.0.0" \
--formats markdown openapi \
--output-dir docs/api \
--include-source-links \
--include-examples \
--example-depth 2 \
--modules my_app.api my_app.models \
--url-base https://docs.example.com/api \
--logo-url https://example.com/logo.png
```
```

## Environment Variables

You can also configure the documentation generator using environment variables:

```bash
export UNO_DOCS_TITLE="My API Documentation"
export UNO_DOCS_DESCRIPTION="Documentation for my API"
export UNO_DOCS_VERSION="1.0.0"
export UNO_DOCS_FORMATS="markdown,openapi"
export UNO_DOCS_OUTPUT_DIR="docs/api"
export UNO_DOCS_MODULES="my_app.api,my_app.models"
```

Then in your Python code:

```python
from uno.core.docs.generator import load_config_from_env, generate_docs

config = load_config_from_env()
generate_docs(config)
```

## Full Configuration Example

Here's a complete configuration example:

```python
from uno.core.docs.generator import DocGeneratorConfig, DocFormat, generate_docs

config = DocGeneratorConfig(```

# Basic information
title="My API Documentation",
description="Comprehensive documentation for my API",
version="1.0.0",
``````

```
```

# Output configuration
formats=[DocFormat.MARKDOWN, DocFormat.OPENAPI, DocFormat.HTML],
output_dir="docs/api",
``````

```
```

# Component filtering
include_internal=False,
include_deprecated=True,
include_beta=True,
include_alpha=False,
include_experimental=False,
``````

```
```

# Source and examples configuration
include_source_links=True,
include_examples=True,
example_depth=2,
``````

```
```

# Modules to document
modules_to_document=[```

"my_app.api.v1",
"my_app.api.v2",
"my_app.models"
```
],
``````

```
```

# HTML customization
url_base="https://docs.example.com/api",
logo_url="https://example.com/logo.png",
css_urls=["https://cdn.example.com/styles.css"],
js_urls=["https://cdn.example.com/scripts.js"],
``````

```
```

# Additional metadata
metadata={```

"organization": "Example Corp",
"contact_email": "api@example.com",
"license": "MIT"
```
}
```
)

# Generate documentation
generate_docs(config)
```