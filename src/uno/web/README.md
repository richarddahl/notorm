# Uno Web Module

This module contains the web assets for Uno applications, including static files and templates.

## Structure

- `static/`: Contains static assets like images, CSS, and JavaScript
  - `assets/`: Core assets like images, scripts, and stylesheets
  - `components/`: Web components used in the UI
- `templates/`: Contains HTML templates used by the application
  - `base.html`: Base template with common layout
  - `index.html`: Main index template
  - `app.html`: Application template

## Usage

To use these web assets in your Uno application:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "templates")
templates = Jinja2Templates(directory=templates_dir)
```

## Customization

You can customize the templates and static files by overriding them in your application. Create a `web` directory in your application root with `static` and `templates` subdirectories, and Uno will use those files instead of the default ones.