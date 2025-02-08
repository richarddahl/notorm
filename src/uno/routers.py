# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from enum import Enum

from typing import Annotated, List, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, ConfigDict
from pydantic.dataclasses import dataclass

from fastapi import APIRouter, FastAPI, HTTPException, Request, Header, Depends

# from uno.database.base import get_db
get_db = None


class TestModel(BaseModel):
    value: str


@dataclass
class RouterDef:
    path_suffix: str = ""
    path_objs: str = ""
    method: str = "GET"
    router: str = "get"
    multiple: bool = False
    include_in_schema: bool = True
    summary: str = ""
    description: str = ""


@dataclass
class Router:
    model: Any
    path_module: str
    mask: str = ""
    path_objs: str = ""
    path_prefix: str = "/api"
    path_suffix: str = ""
    method: str = "GET"
    router: str = "get"
    multiple: bool = False
    include_in_schema: bool = True
    summary: str = ""
    description: str = ""
    tags: list[str | Enum] | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_to_app(self, app: FastAPI):
        router = APIRouter()
        router.add_api_route(
            f"{self.path_prefix}/{self.path_module}/{self.path_objs}{self.path_suffix}",
            endpoint=getattr(self, self.router),
            methods=[self.method],
            response_model=List[TestModel],
            # response_model=TestModel if not self.multiple else List[TestModel],
            # response_model=self.model if not self.multiple else List[self.model],
            include_in_schema=self.include_in_schema,
            tags=self.tags,
            summary=self.summary,
            description=self.description,
        )
        app.include_router(router)

    async def get_by_id(
        self,
        id: str,
        authorization: Annotated[str, Header()],
        db: AsyncSession = Depends(get_db),
    ):
        await db.execute(func.uno.authorize_user(authorization))
        result = await db.execute(select(self.table).filter_by(id=id))
        obj = result.scalar()
        if obj is None:
            raise HTTPException(status_code=404, detail="Object not found")
        return obj

    async def get(
        self,
        authorization: Annotated[str, Header()],
        db: AsyncSession = Depends(get_db),
    ):
        await db.execute(func.uno.authorize_user(authorization))
        result = await db.execute(select(self.table))
        return result.scalars()

    async def post(
        self,
        request: Request,
        authorization: Annotated[str, Header()],
        db: AsyncSession = Depends(get_db),
    ):
        await db.execute(func.uno.authorize_user(authorization))
        data = await request.json()
        await db.execute(self.table.insert().values(data))
        return {"message": "post"}

    def put(self):
        return {"message": "put"}

    def delete(self):
        return {"message": "delete"}
