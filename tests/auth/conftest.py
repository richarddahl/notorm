# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import pytest

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from uno.db.base import UnoBase
from uno.db.db import engine, sync_engine


AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="function")
async def session(db):
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
