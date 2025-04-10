# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from uno.registry import UnoRegistry

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
# Get registry instance
registry = UnoRegistry.get_instance()

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

# Configure all registered UnoObj classes
for uno_object in registry.get_all().values():
    if hasattr(uno_object, "configure"):
        uno_object.configure(app)
