"""
FastAPI application for the e-commerce API.

This module sets up the FastAPI application with all the routes
and middleware for the e-commerce API.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from uno.dependencies import initialize_services

from examples.ecommerce.api.dto.common import ErrorResponse
from examples.ecommerce.api.user import router as user_router
from examples.ecommerce.api.product import router as product_router
from examples.ecommerce.api.order import router as order_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ecommerce_api")


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for service initialization and cleanup."""
    # Startup: initialize services
    logger.info("Initializing services...")
    initialize_services()
    logger.info("Services initialized")
    
    yield
    
    # Shutdown: cleanup operations would go here
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="E-commerce API",
    description="API for e-commerce application using domain-driven design",
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(user_router)
app.include_router(product_router)
app.include_router(order_router)


# Exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "code": "INTERNAL_ERROR"}
    )


# Health check endpoint
@app.get("/health", tags=["system"])
async def health_check():
    """Check the health of the API."""
    return {"status": "ok"}