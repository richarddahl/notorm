# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from enum import Enum

from typing import Annotated

from sqlalchemy import select, func, Table
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, ConfigDict
from dataclasses import dataclass

from fastapi import APIRouter, FastAPI, HTTPException, Request, Header, Depends


get_db = None


@dataclass
class Router:
    path_prefix: str = "/api"
    path_module: str = ""
    path_suffix: str = ""
    path_objs: str = ""
    method: str = "GET"
    endpoint: str = "get"
    multiple: bool = False
    include_in_schema: bool = True
    summary: str = ""
    description: str = ""
    tags: list[str | Enum] | None = None
    table: Table | None = None
    response_model: BaseModel | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_to_app(self, schema: BaseModel, table: Table, app: FastAPI):
        router = APIRouter()
        router.add_api_route(
            f"{self.path_prefix}{self.path_module}{self.path_objs}{self.path_suffix}",
            response_model=schema,
            endpoint=getattr(self, self.endpoint),
            methods=[self.method],
            include_in_schema=self.include_in_schema,
            tags=self.tags,
            summary=self.summary,
            description=self.description,
        )
        app.include_router(router)

    async def get_by_id(
        self,
        id: str,
    ):
        result = await db.execute(select(self.table).filter_by(id=id))
        obj = result.scalar()
        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")
        return self.response_model

    async def get(
        self,
    ):
        await db.execute(func.uno.authorize_user(authorization))
        result = await db.execute(select(self.table))
        return result.scalars()

    async def post(
        self,
        request: Request,
    ) -> dict:
        data = await request.json()
        return self.response_model

    def patch(self):
        return self.response_model

    def put(self):
        return self.response_model

    def delete(self):
        return {"message": "delete"}
