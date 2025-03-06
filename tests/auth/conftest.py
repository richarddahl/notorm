# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import pytest

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from uno.record.record import UnoRecordBase
from uno.storage.session import engine


AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="module")
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(UnoRecordBase.metadata.create_all)
    yield engine
    # async with engine.begin() as conn:
    #    await conn.run_sync(UnoRecordBase.metadata.drop_all)


@pytest.fixture(scope="function")
async def session(db):
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
