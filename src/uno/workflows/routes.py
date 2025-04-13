"""
FastAPI route handlers for the workflow admin UI.

This module contains route handlers for the workflow admin UI,
which renders the workflow administration interface.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pathlib import Path
import os

# Define templates directory relative to project base
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Create router for workflow UI routes
router = APIRouter(tags=["workflows_ui"])


@router.get("/workflows", response_class=HTMLResponse)
async def workflow_admin(request: Request):
    """
    Render the workflow administration interface.
    
    Args:
        request: The FastAPI request object
    
    Returns:
        The rendered HTML response
    """
    return templates.TemplateResponse(
        "workflow_admin.html",
        {"request": request}
    )


@router.get("/workflows/new", response_class=HTMLResponse)
async def new_workflow(request: Request):
    """
    Render the workflow designer interface for creating a new workflow.
    
    Args:
        request: The FastAPI request object
    
    Returns:
        The rendered HTML response
    """
    return templates.TemplateResponse(
        "workflow_admin.html",
        {"request": request, "mode": "designer"}
    )


@router.get("/workflows/{workflow_id}", response_class=HTMLResponse)
async def edit_workflow(workflow_id: str, request: Request):
    """
    Render the workflow designer interface for editing an existing workflow.
    
    Args:
        workflow_id: The ID of the workflow to edit
        request: The FastAPI request object
    
    Returns:
        The rendered HTML response
    """
    return templates.TemplateResponse(
        "workflow_admin.html",
        {"request": request, "mode": "designer", "workflow_id": workflow_id}
    )


@router.get("/workflows/{workflow_id}/executions/{execution_id}", response_class=HTMLResponse)
async def workflow_execution(workflow_id: str, execution_id: str, request: Request):
    """
    Render the workflow execution detail interface.
    
    Args:
        workflow_id: The ID of the workflow
        execution_id: The ID of the execution to view
        request: The FastAPI request object
    
    Returns:
        The rendered HTML response
    """
    return templates.TemplateResponse(
        "workflow_admin.html",
        {
            "request": request,
            "mode": "execution",
            "workflow_id": workflow_id,
            "execution_id": execution_id
        }
    )


@router.get("/workflows/{workflow_id}/simulate", response_class=HTMLResponse)
async def simulate_workflow(workflow_id: str, request: Request):
    """
    Render the workflow simulator interface.
    
    Args:
        workflow_id: The ID of the workflow to simulate
        request: The FastAPI request object
    
    Returns:
        The rendered HTML response
    """
    return templates.TemplateResponse(
        "workflow_admin.html",
        {"request": request, "mode": "simulator", "workflow_id": workflow_id}
    )