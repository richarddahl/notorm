# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import asyncio

from uno.record.db_manager import DBManager


if __name__ == "__main__":
    db = DBManager()
    asyncio.run(db.create_superuser())
