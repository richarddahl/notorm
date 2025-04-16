# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    {
        "name": "Domain",
        "description": "Domain-driven API endpoints",
        "externalDocs": {
            "description": "Domain Documentation",
            "url": "http://localhost:8001/domain/",
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
