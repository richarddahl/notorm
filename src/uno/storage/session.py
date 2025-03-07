# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import AsyncIterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from uno.config import settings


DB_ROLE = f"{settings.DB_NAME}_login"
DB_SYNC_DRIVER = settings.DB_SYNC_DRIVER
DB_ASYNC_DRIVER = settings.DB_ASYNC_DRIVER
DB_USER_PW = settings.DB_USER_PW
DB_HOST = settings.DB_HOST
DB_NAME = settings.DB_NAME
DB_SCHEMA = settings.DB_SCHEMA

sync_engine = create_engine(
    # f"{DB_SYNC_DRIVER}://{DB_ROLE}:{DB_USER_PW}@{DB_HOST}/{DB_NAME}",
    f"{DB_SYNC_DRIVER}://postgres:{DB_USER_PW}@{DB_HOST}/{DB_NAME}",
)

engine = create_async_engine(
    # f"{DB_ASYNC_DRIVER}://{DB_ROLE}:{DB_USER_PW}@{DB_HOST}/{DB_NAME}",
    f"{DB_ASYNC_DRIVER}://postgres:{DB_USER_PW}@{DB_HOST}/{DB_NAME}",
    poolclass=NullPool,
    # echo=True,
)

SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


async def get_session() -> AsyncIterator:
    async with SessionLocal() as session:
        yield session


"""
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


async def get_session() -> AsyncIterator:
    async with SessionLocal() as session:
        yield session
"""
