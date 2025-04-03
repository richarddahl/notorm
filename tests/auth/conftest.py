# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import sqlalchemy
import pytest
import factory

from sqlalchemy.orm import sessionmaker
from tests.conftest import sync_engine as engine
from uno.auth.bases import UserBase

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


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserBase
        sqlalchemy_session = SessionLocal()
        sqlalchemy_session_persistence = "commit"

    full_name = factory.Faker("name")
    email = factory.lazy_attribute(
        lambda o: f"{o.full_name.replace(' ', '.').lower()}@example.com"
    )
    handle = factory.lazy_attribute(
        lambda o: f"@{o.full_name.replace(' ', '_').lower()}"
    )


@pytest.fixture(scope="function")
def user_factory(db_session):
    """Fixture to provide a UserFactory with a session."""
    UserFactory._meta.sqlalchemy_session = db_session
    return UserFactory


with db_session().begin():
    # Create the database tables if they don't exist
    engine.execute(sqlalchemy.text("SET ROLE uno_test_writer"))
user = UserFactory.create()

print(user.full_name)
print(user.email)
print(user.handle)
