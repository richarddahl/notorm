# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio

from uno.storage.management.db_manager import DBManager
from uno.apps.auth.objs import User, Group, Tenant, Role


if __name__ == "__main__":
    User.configure()
    Group.configure()
    Tenant.configure()
    Role.configure()
    db = DBManager()
    asyncio.run(db.create_superuser())
