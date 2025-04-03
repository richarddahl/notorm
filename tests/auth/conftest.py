# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import sqlalchemy
import pytest
import factory

from sqlalchemy.orm import sessionmaker
from tests.conftest import session

# Assuming `engine` is defined in your main application code
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Fixture to provide a SQLAlchemy session for the tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from uno.auth.bases import UserBase
from uno.auth.models import User


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserBase
        sqlalchemy_session_factory = lambda: session

    full_name = factory.Faker("name")
    email = factory.lazy_attribute(
        lambda o: f"{o.full_name.replace(' ', '.').lower()}@example.com"
    )
    handle = factory.lazy_attribute(
        lambda o: f"@{o.full_name.replace(' ', '_').lower()}"
    )


user = UserFactory.create()
print("Creating user with email:", user.email)
print("Creating user with handle:", user.handle)
print("Creating user with full name:", user.full_name)
