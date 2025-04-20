from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from uno.core.errors.dashboard import router as api_router

# Create templates instance
templates = Jinja2Templates(directory="uno/core/errors/templates")

# Create main router
router = APIRouter(prefix="/errors", tags=["Error Dashboard"])

# Include API routes
router.include_router(api_router)

@router.get("/")
async def get_dashboard(request: Request):
    """Serve the error dashboard page."""
    return templates.TemplateResponse("error_dashboard.html", {"request": request})
