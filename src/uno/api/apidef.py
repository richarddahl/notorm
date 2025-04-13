# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from uno.registry import get_registry

tags_metadata = [
    {
        "name": "0KUI",
        "description": "Zero Knowledge User Interface.",
        "externalDocs": {
            "description": "0kui Documentation",
            "url": "http://localhost:8001/okui/",
        },
    },
    {
        "name": "Schemas",
        "description": "API Schemas",
        "externalDocs": {
            "description": "Documentation",
            "url": "http://localhost:8001/schema/",
        },
    },
]
# Create the FastAPI app first
app = FastAPI(
    openapi_tags=tags_metadata,
    title="Uno is not an ORM",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get registry instance - model configuration will happen in main.py startup event
registry = get_registry()

# Extend tags metadata for documentation
# This will run during import but won't configure the models yet
tags_metadata.extend(
    [
        {
            "name": uno_object.display_name_plural,
            "description": uno_object.__doc__,
            "externalDocs": {
                "description": f"{uno_object.display_name} Documentation",
                "url": f"http://localhost:8001/{uno_object.display_name}",
            },
        }
        for uno_object in registry.get_all().values()
        if getattr(uno_object, "include_in_schema_docs", True)
    ]
)
