# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import FastAPI

from uno.object import UnoObj

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
        for uno_object in UnoObj.registry.values()
        if getattr(uno_object, "include_in_schema_docs", True)
    ]
)

app = FastAPI(
    openapi_tags=tags_metadata,
    title="Uno is not an ORM",
)
