"""
Server for the visual data modeling tool.

This module provides a FastAPI server for the visual data modeling tool,
allowing data modeling and code generation.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from uuid import UUID

import uvicorn
import webbrowser
import threading
import time
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from uno.devtools.modeler.analyzer import AnalyzeCodebase, ModelType
from uno.devtools.modeler.generator import CodeGenerator

# Set up logging
logger = logging.getLogger(__name__)

# Templates directory - relative to this file
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "webapp"
STATIC_DIR = TEMPLATE_DIR / "static"

# Create directories if they don't exist
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(title="Uno Data Modeler", description="Visual data modeling tool for Uno")

# Set up templates
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Models
class EntityField(BaseModel):
    """
    Model for an entity field.
    """
    
    name: str
    type: str
    primaryKey: Optional[bool] = False


class Entity(BaseModel):
    """
    Model for an entity.
    """
    
    id: str
    name: str
    fields: List[EntityField]
    x: Optional[float] = None
    y: Optional[float] = None


class Relationship(BaseModel):
    """
    Model for a relationship between entities.
    """
    
    source: str
    target: str
    type: str
    name: Optional[str] = None


class DataModel(BaseModel):
    """
    Complete data model with entities and relationships.
    """
    
    projectName: str
    entities: List[Entity]
    relationships: List[Relationship]


class GeneratedCode(BaseModel):
    """
    Generated code for entities, repositories, and services.
    """
    
    entities: Dict[str, str]
    repositories: Dict[str, str]
    services: Dict[str, str]


class ModelAnalysisResult(BaseModel):
    """
    Result of analyzing a model.
    """
    
    entities: List[Entity]
    relationships: List[Relationship]


# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serve the main application page.
    """
    return templates.TemplateResponse(
        "modeler.html", {"request": request, "title": "Uno Data Modeler"}
    )


@app.post("/api/devtools/model/generate", response_model=GeneratedCode)
async def generate_code(model: DataModel):
    """
    Generate code from a data model.
    
    Args:
        model: Data model with entities and relationships
        
    Returns:
        Generated code for entities, repositories, and services
    """
    try:
        generator = CodeGenerator(model.projectName)
        code = generator.generate(model.entities, model.relationships)
        return code
    except Exception as e:
        logger.exception("Error generating code")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/devtools/model/analyze", response_model=ModelAnalysisResult)
async def analyze_codebase(
    project_path: str,
    model_type: ModelType = ModelType.ENTITY,
):
    """
    Analyze a codebase and extract a data model.
    
    Args:
        project_path: Path to the project to analyze
        model_type: Type of model to analyze
        
    Returns:
        Extracted data model with entities and relationships
    """
    try:
        analyzer = AnalyzeCodebase(project_path)
        result = analyzer.analyze(model_type)
        return result
    except Exception as e:
        logger.exception("Error analyzing codebase")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/devtools/model/projects")
async def list_projects():
    """
    List available Uno projects in the workspace.
    
    Returns:
        List of Uno projects with their paths
    """
    # This is a simplified implementation
    # In a real implementation, we would search for Uno projects
    return {"projects": []}


def start_server(host: str = "localhost", port: int = 8765, open_browser: bool = True):
    """
    Start the data modeler server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        open_browser: Whether to open a browser window
    """
    if open_browser:
        # Use the modules imported at the top level
        def open_browser_after_delay():
            time.sleep(1.5)  # Wait for server to start
            webbrowser.open(f"http://{host}:{port}")
        
        threading.Thread(target=open_browser_after_delay).start()
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()