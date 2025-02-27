# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from fastapi import FastAPI

from uno.db.obj import UnoObj

tags_metadata = [
    {
        "name": "0KUI",
        "description": "Zero Knowledge User Interface.",
        "externalDocs": {
            "description": "0kui Documentation",
            "url": "http://localhost:8001/okui/",
        },
    }
]
tags_metadata.extend(
    [
        {
            "name": uno_obj.display_name,
            "description": uno_obj.__doc__,
            "externalDocs": {
                "description": f"{uno_obj.display_name} Documentation",
                "url": f"http://localhost:8001/{uno_obj.display_name}",
            },
        }
        for uno_obj in UnoObj.registry.values()
        if getattr(uno_obj, "include_in_api_docs", True)
    ]
)

app = FastAPI(
    openapi_tags=tags_metadata,
    title="Uno is not an ORM",
)
