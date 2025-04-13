#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example script demonstrating how to integrate and use the attributes and values APIs.

This example shows:
1. Setting up the necessary services and repositories
2. Registering API endpoints
3. Starting a FastAPI application with the integrated endpoints

Run this script with:
    python attributes_values_api_example.py
"""

import logging
import uvicorn
from fastapi import FastAPI, APIRouter
from typing import List

from uno.database.db_manager import DBManager
from uno.attributes import (
    AttributeRepository,
    AttributeTypeRepository,
    AttributeService,
    AttributeTypeService,
    register_attribute_endpoints,
)
from uno.values import (
    AttachmentRepository,
    BooleanValueRepository,
    DateTimeValueRepository,
    DateValueRepository,
    DecimalValueRepository,
    IntegerValueRepository,
    TextValueRepository,
    TimeValueRepository,
    ValueService,
    register_value_endpoints,
)


def create_app():
    """Create and configure the FastAPI application with attribute and value endpoints."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    
    # Create FastAPI app
    app = FastAPI(
        title="Attributes and Values API Example",
        description="Example API for managing attributes and values",
        version="0.1.0"
    )
    
    # Create router
    api_router = APIRouter()
    
    # Create database manager
    db_manager = DBManager()
    
    # Create attribute repositories and services
    logger.info("Setting up attribute repositories and services...")
    attribute_repository = AttributeRepository(db_manager)
    attribute_type_repository = AttributeTypeRepository(db_manager)
    attribute_service = AttributeService(
        attribute_repository=attribute_repository,
        attribute_type_repository=attribute_type_repository,
        db_manager=db_manager,
        logger=logger
    )
    attribute_type_service = AttributeTypeService(
        attribute_type_repository=attribute_type_repository,
        db_manager=db_manager,
        logger=logger
    )
    
    # Create value repositories and service
    logger.info("Setting up value repositories and services...")
    boolean_repository = BooleanValueRepository(db_manager)
    text_repository = TextValueRepository(db_manager)
    integer_repository = IntegerValueRepository(db_manager)
    decimal_repository = DecimalValueRepository(db_manager)
    date_repository = DateValueRepository(db_manager)
    datetime_repository = DateTimeValueRepository(db_manager)
    time_repository = TimeValueRepository(db_manager)
    attachment_repository = AttachmentRepository(db_manager)
    
    value_service = ValueService(
        boolean_repository=boolean_repository,
        text_repository=text_repository,
        integer_repository=integer_repository,
        decimal_repository=decimal_repository,
        date_repository=date_repository,
        datetime_repository=datetime_repository,
        time_repository=time_repository,
        attachment_repository=attachment_repository,
        db_manager=db_manager,
        logger=logger
    )
    
    # Register attribute and attribute type endpoints
    logger.info("Registering attribute endpoints...")
    register_attribute_endpoints(
        router=api_router,
        attribute_service=attribute_service,
        attribute_type_service=attribute_type_service,
        attribute_prefix="/attributes",
        attribute_type_prefix="/attribute-types",
        attribute_tags=["Attributes"],
        attribute_type_tags=["Attribute Types"]
    )
    
    # Register value endpoints
    logger.info("Registering value endpoints...")
    register_value_endpoints(
        router=api_router,
        value_service=value_service,
        prefix="/values",
        tags=["Values"]
    )
    
    # Include router in app
    app.include_router(api_router, prefix="/api/v1")
    
    # Add basic welcome route
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to the Attributes and Values API Example",
            "documentation": "/docs",
            "attribute_endpoints": "/api/v1/attributes",
            "attribute_type_endpoints": "/api/v1/attribute-types",
            "value_endpoints": "/api/v1/values"
        }
    
    logger.info("FastAPI app configuration complete")
    return app


def main():
    """Run the FastAPI application."""
    app = create_app()
    
    # Start the server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()