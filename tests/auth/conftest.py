# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio
import pytest
import factory

from tests.conftest import session

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
