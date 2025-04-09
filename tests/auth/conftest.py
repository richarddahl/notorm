# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import sqlalchemy
import pytest
import factory

from sqlalchemy.orm import sessionmaker
from uno.auth.models import UserModel

'''
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
        model = UserModel
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


@pytest.fixture(scope="function", autouse=True)
def setup_database(db_session):
    """Fixture to set up the database before each test."""
    try:
        with db_session.begin():
            db_session.execute(sqlalchemy.text("SET ROLE uno_test_writer;"))
            # Add any additional setup logic here
    except sqlalchemy.exc.OperationalError as e:
        print("OperationalError during setup_database:", e)
        raise


@pytest.fixture(scope="function")
def create_user(user_factory, db_session):
    """Fixture to create a user."""
    with db_session.begin():
        user = user_factory.create()
        print(user.full_name)
        print(user.email)
        print(user.handle)
        return user

'''
