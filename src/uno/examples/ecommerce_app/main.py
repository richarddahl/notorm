"""
E-Commerce Application Example.

This module serves as the entry point for the e-commerce application example,
demonstrating the unified Domain-Driven Design approach in the Uno framework.
"""

import uvicorn
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from uno.core.errors.base import UnoError
from uno.core.events import initialize_events
from uno.domain.unified_services import DomainServiceFactory, initialize_service_factory

# Import context modules
from uno.examples.ecommerce_app.catalog import setup_catalog
from uno.examples.ecommerce_app.order import setup_order
from uno.examples.ecommerce_app.customer import setup_customer
from uno.examples.ecommerce_app.cart import setup_cart
from uno.examples.ecommerce_app.shipping import setup_shipping
from uno.examples.ecommerce_app.payment import setup_payment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecommerce_app")

# Create FastAPI application
app = FastAPI(
    title="E-Commerce API",
    description="Example e-commerce application using domain-driven design",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for UnoError
@app.exception_handler(UnoError)
async def uno_error_handler(request: Request, exc: UnoError):
    """Handle UnoError exceptions and convert to appropriate HTTP responses."""
    status_code = 400

    # Map specific error codes to status codes
    if hasattr(exc, "error_code"):
        if exc.error_code in ["NOT_FOUND", "ENTITY_NOT_FOUND", "RESOURCE_NOT_FOUND"]:
            status_code = 404
        elif exc.error_code in ["UNAUTHORIZED", "UNAUTHENTICATED"]:
            status_code = 401
        elif exc.error_code in ["FORBIDDEN", "ACCESS_DENIED", "PERMISSION_DENIED"]:
            status_code = 403
        elif exc.error_code in ["VALIDATION_ERROR", "INVALID_INPUT"]:
            status_code = 400
        elif exc.error_code in ["INTERNAL_ERROR", "SYSTEM_ERROR"]:
            status_code = 500
        elif exc.error_code in ["CONFLICT", "ALREADY_EXISTS", "DUPLICATE"]:
            status_code = 409

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.error_code if hasattr(exc, "error_code") else "ERROR",
            "message": str(exc),
            "detail": exc.context if hasattr(exc, "context") else None,
        },
    )


# Setup contexts
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    # Initialize event system
    initialize_events()

    # Setup all contexts
    setup_catalog(app)
    setup_order(app)
    setup_customer(app)
    setup_cart(app)
    setup_shipping(app)
    setup_payment(app)

    logger.info("E-commerce application initialized")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning welcome message."""
    return {
        "message": "Welcome to the E-Commerce API",
        "version": "1.0.0",
        "documentation": "/docs",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "uno.examples.ecommerce_app.main:app", host="0.0.0.0", port=8000, reload=True
    )
